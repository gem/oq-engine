# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
from __future__ import division
import os
import sys
import abc
import pdb
import logging
import operator
import itertools
import traceback
import collections
from functools import partial
from datetime import datetime
import numpy

from openquake.baselib import (
    general, hdf5, datastore, __version__ as engine_version)
from openquake.baselib.performance import Monitor
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib import geo
from openquake.risklib import riskinput, asset
from openquake.commonlib import readinput, source, calc, riskmodels
from openquake.baselib.parallel import Starmap, wakeup_pool
from openquake.baselib.python3compat import with_metaclass
from openquake.calculators.export import export as exp

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_trt = operator.attrgetter('src_group_id')
get_imt = operator.attrgetter('imt')

calculators = general.CallableDict(operator.attrgetter('calculation_mode'))

Site = collections.namedtuple('Site', 'sid lon lat')

F32 = numpy.float32


class InvalidCalculationID(Exception):
    """
    Raised when running a post-calculation on top of an incompatible
    pre-calculation
    """


class AssetSiteAssociationError(Exception):
    """Raised when there are no hazard sites close enough to any asset"""

rlz_dt = numpy.dtype([('uid', 'S200'), ('model', 'S200'),
                      ('gsims', 'S100'), ('weight', F32)])

logversion = True


PRECALC_MAP = dict(
    classical=['psha'],
    disaggregation=['psha'],
    scenario_risk=['scenario'],
    scenario_damage=['scenario'],
    classical_risk=['classical'],
    classical_bcr=['classical'],
    classical_damage=['classical'],
    event_based=['event_based', 'event_based_rupture', 'ebrisk',
                 'event_based_risk', 'ucerf_rupture'],
    event_based_risk=['event_based', 'event_based_rupture', 'ucerf_rupture',
                      'event_based_risk'],
    ucerf_classical=['ucerf_psha'],
    ucerf_hazard=['ucerf_rupture'])


def set_array(longarray, shortarray):
    """
    :param longarray: a numpy array of floats of length L >= l
    :param shortarray: a numpy array of floats of length l

    Fill `longarray` with the values of `shortarray`, starting from the left.
    If `shortarry` is shorter than `longarray`, then the remaining elements on
    the right are filled with `numpy.nan` values.
    """
    longarray[:len(shortarray)] = shortarray
    longarray[len(shortarray):] = numpy.nan


def gsim_names(rlz):
    """
    Names of the underlying GSIMs separated by spaces
    """
    return ' '.join(str(v) for v in rlz.gsim_rlz.value)


def check_precalc_consistency(calc_mode, precalc_mode):
    """
    Defensive programming against users providing an incorrect pre-calculation
    ID (with ``--hazard-calculation-id``)

    :param calc_mode:
        calculation_mode of the current calculation
    :param precalc_mode:
        calculation_mode of the previous calculation
    """
    ok_mode = PRECALC_MAP[calc_mode]
    if calc_mode != precalc_mode and precalc_mode not in ok_mode:
        raise InvalidCalculationID(
            'In order to run a risk calculation of kind %r, '
            'you need to provide a calculation of kind %r, '
            'but you provided a %r instead' %
            (calc_mode, ok_mode, precalc_mode))


class BaseCalculator(with_metaclass(abc.ABCMeta)):
    """
    Abstract base class for all calculators.

    :param oqparam: OqParam object
    :param monitor: monitor object
    :param calc_id: numeric calculation ID
    """
    from_engine = False  # set by engine.run_calc
    sitecol = datastore.persistent_attribute('sitecol')
    assetcol = datastore.persistent_attribute('assetcol')
    performance = datastore.persistent_attribute('performance')
    pre_calculator = None  # to be overridden
    is_stochastic = False  # True for scenario and event based calculators

    @property
    def taxonomies(self):
        L = len('taxonomy=')
        return [tag[L:]
                for tag in self.datastore['assetcol/tags']
                if tag.startswith('taxonomy=')]

    def __init__(self, oqparam, monitor=Monitor(), calc_id=None):
        self._monitor = monitor
        self.datastore = datastore.DataStore(calc_id)
        self.oqparam = oqparam

    def monitor(self, operation, **kw):
        """
        Return a new Monitor instance
        """
        mon = self._monitor(operation, hdf5path=self.datastore.hdf5path)
        self._monitor.calc_id = mon.calc_id = self.datastore.calc_id
        vars(mon).update(kw)
        return mon

    def save_params(self, **kw):
        """
        Update the current calculation parameters and save engine_version
        """
        vars(self.oqparam).update(**kw)
        self.datastore['oqparam'] = self.oqparam  # save the updated oqparam
        attrs = self.datastore['/'].attrs
        attrs['engine_version'] = engine_version
        attrs['date'] = datetime.now().isoformat()[:19]
        if 'checksum32' not in attrs:
            attrs['checksum32'] = readinput.get_checksum32(self.oqparam)
        self.datastore.flush()

    def set_log_format(self):
        """Set the format of the root logger"""
        fmt = '[%(asctime)s #{} %(levelname)s] %(message)s'.format(
            self.datastore.calc_id)
        for handler in logging.root.handlers:
            handler.setFormatter(logging.Formatter(fmt))

    def run(self, pre_execute=True, concurrent_tasks=None, close=True, **kw):
        """
        Run the calculation and return the exported outputs.
        """
        global logversion
        self.close = close
        self.set_log_format()
        if logversion:  # make sure this is logged only once
            logging.info('Running %s', self.oqparam.inputs['job_ini'])
            logging.info('Using engine version %s', engine_version)
            logversion = False
        if concurrent_tasks is None:  # use the job.ini parameter
            ct = self.oqparam.concurrent_tasks
        else:  # used the parameter passed in the command-line
            ct = concurrent_tasks
        if ct == 0:  # disable distribution temporarily
            oq_distribute = os.environ.get('OQ_DISTRIBUTE')
            os.environ['OQ_DISTRIBUTE'] = 'no'
        if ct != self.oqparam.concurrent_tasks:
            # save the used concurrent_tasks
            self.oqparam.concurrent_tasks = ct
        self.save_params(**kw)
        exported = {}
        try:
            if pre_execute:
                self.pre_execute()
            self.result = self.execute()
            if self.result is not None:
                self.post_execute(self.result)
            self.before_export()
            exported = self.export(kw.get('exports', ''))
        except:
            if kw.get('pdb'):  # post-mortem debug
                tb = sys.exc_info()[2]
                traceback.print_tb(tb)
                pdb.post_mortem(tb)
            else:
                logging.critical('', exc_info=True)
                raise
        finally:
            if ct == 0:  # restore OQ_DISTRIBUTE
                if oq_distribute is None:  # was not set
                    del os.environ['OQ_DISTRIBUTE']
                else:
                    os.environ['OQ_DISTRIBUTE'] = oq_distribute
        return exported

    def core_task(*args):
        """
        Core routine running on the workers.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def pre_execute(self):
        """
        Initialization phase.
        """

    @abc.abstractmethod
    def execute(self):
        """
        Execution phase. Usually will run in parallel the core
        function and return a dictionary with the results.
        """

    @abc.abstractmethod
    def post_execute(self, result):
        """
        Post-processing phase of the aggregated output. It must be
        overridden with the export code. It will return a dictionary
        of output files.
        """

    def export(self, exports=None):
        """
        Export all the outputs in the datastore in the given export formats.
        Individual outputs are not exported if there are multiple realizations.

        :returns: dictionary output_key -> sorted list of exported paths
        """
        num_rlzs = len(self.datastore['realizations'])
        exported = {}
        if isinstance(exports, tuple):
            fmts = exports
        elif exports:  # is a string
            fmts = exports.split(',')
        elif isinstance(self.oqparam.exports, tuple):
            fmts = self.oqparam.exports
        else:  # is a string
            fmts = self.oqparam.exports.split(',')
        keys = set(self.datastore)
        has_hcurves = 'hcurves' in self.datastore or 'poes' in self.datastore
        if has_hcurves:
            keys.add('hcurves')
        for fmt in fmts:
            if not fmt:
                continue
            for key in sorted(keys):  # top level keys
                if 'rlzs' in key and num_rlzs > 1:
                    continue  # skip individual curves
                self._export((key, fmt), exported)
            if has_hcurves and self.oqparam.hazard_maps:
                self._export(('hmaps', fmt), exported)
            if has_hcurves and self.oqparam.uniform_hazard_spectra:
                self._export(('uhs', fmt), exported)

        if self.close:  # in the engine we close later
            self.result = None
            try:
                self.datastore.close()
            except (RuntimeError, ValueError):
                # sometimes produces errors but they are difficult to
                # reproduce
                logging.warn('', exc_info=True)
        return exported

    def _export(self, ekey, exported):
        if ekey in exp:
            with self.monitor('export'):
                exported[ekey] = exp(ekey, self.datastore)
                logging.info('exported %s: %s', ekey[0], exported[ekey])

    def before_export(self):
        """
        Collect the realizations and set the attributes nbytes
        """
        if hasattr(self, 'rlzs_assoc'):
            sm_by_rlz = self.datastore['csm_info'].get_sm_by_rlz(
                self.rlzs_assoc.realizations) or collections.defaultdict(
                    lambda: 'NA')
            self.datastore['realizations'] = numpy.array(
                [(r.uid, sm_by_rlz[r], gsim_names(r), r.weight)
                 for r in self.rlzs_assoc.realizations], rlz_dt)
        for key in self.datastore:
            self.datastore.set_nbytes(key)
        self.datastore.flush()


def check_time_event(oqparam, time_events):
    """
    Check the `time_event` parameter in the datastore, by comparing
    with the periods found in the exposure.
    """
    time_event = oqparam.time_event
    if time_event and time_event not in time_events:
        raise ValueError(
            'time_event is %s in %s, but the exposure contains %s' %
            (time_event, oqparam.inputs['job_ini'], ', '.join(time_events)))


class HazardCalculator(BaseCalculator):
    """
    Base class for hazard calculators based on source models
    """
    def get_num_tiles(self):
        """
        :returns: the number of tiles in which the SiteCollection can be split
        """
        return 1  # overridden in the PSHA calculator

    def assoc_assets_sites(self, sitecol):
        """
        :param sitecol: a sequence of sites
        :returns: a pair (filtered sites, asset collection)

        The new site collection is different from the original one
        if some assets were discarded or if there were missing assets
        for some sites.
        """
        asset_hazard_distance = self.oqparam.asset_hazard_distance
        siteobjects = geo.utils.GeographicObjects(
            Site(sid, lon, lat) for sid, lon, lat in
            zip(sitecol.sids, sitecol.lons, sitecol.lats))
        assets_by_sid = general.AccumDict()
        for assets in self.assetcol.assets_by_site():
            if len(assets):
                lon, lat = assets[0].location
                site, distance = siteobjects.get_closest(lon, lat)
                if distance <= asset_hazard_distance:
                    # keep the assets, otherwise discard them
                    assets_by_sid += {site.sid: list(assets)}
        if not assets_by_sid:
            raise AssetSiteAssociationError(
                'Could not associate any site to any assets within the '
                'asset_hazard_distance of %s km' % asset_hazard_distance)
        mask = numpy.array([sid in assets_by_sid for sid in sitecol.sids])
        assets_by_site = [assets_by_sid.get(sid, []) for sid in sitecol.sids]
        return sitecol.filter(mask), asset.AssetCollection(
            assets_by_site,
            self.exposure.assets_by_tag,
            self.exposure.cost_calculator,
            self.oqparam.time_event,
            time_events=hdf5.array_of_vstr(sorted(self.exposure.time_events)))

    def count_assets(self):
        """
        Count how many assets are taken into consideration by the calculator
        """
        return len(self.assetcol)

    def compute_previous(self):
        precalc = calculators[self.pre_calculator](
            self.oqparam, self.monitor('precalculator'),
            self.datastore.calc_id)
        precalc.run(close=False)
        if 'scenario' not in self.oqparam.calculation_mode:
            self.csm = precalc.csm
        pre_attrs = vars(precalc)
        for name in ('riskmodel', 'assets_by_site'):
            if name in pre_attrs:
                setattr(self, name, getattr(precalc, name))
        return precalc

    def read_previous(self, precalc_id):
        parent = datastore.read(precalc_id)
        check_precalc_consistency(
            self.oqparam.calculation_mode, parent['oqparam'].calculation_mode)
        self.datastore.parent = parent
        # copy missing parameters from the parent
        params = {name: value for name, value in
                  vars(parent['oqparam']).items()
                  if name not in vars(self.oqparam)}
        self.save_params(**params)
        self.read_risk_data()

    def basic_pre_execute(self):
        oq = self.oqparam
        self.read_risk_data()
        if 'source' in oq.inputs:
            wakeup_pool()  # fork before reading the source model
            if oq.hazard_calculation_id:  # already stored csm
                logging.info('Reusing composite source model of calc #%d',
                             oq.hazard_calculation_id)
                with datastore.read(oq.hazard_calculation_id) as dstore:
                    csm = dstore['composite_source_model']
            else:
                csm = self.read_csm()
            logging.info('Prefiltering the CompositeSourceModel')
            with self.monitor('prefiltering source model',
                              autoflush=True, measuremem=True):
                if self.get_num_tiles() == 1:
                    srcfilter = SourceFilter(self.sitecol, oq.maximum_distance)
                else:  # do not filter
                    srcfilter = SourceFilter(None, {})
                self.csm = csm.filter(srcfilter)
            info = self.csm.info
            info.gsim_lt.check_imts(oq.imtls)
            info.tot_weight = self.csm.weight
            self.datastore['csm_info'] = self.csm.info
            self.rup_data = {}
        self.init()

    def read_csm(self):
        if 'source' not in self.oqparam.inputs:
            raise ValueError('Missing source_model_logic_tree in %(job_ini)s '
                             'or missing --hc option' % self.oqparam.inputs)
        with self.monitor('reading composite source model', autoflush=True):
                csm = readinput.get_composite_source_model(self.oqparam)
        if self.is_stochastic:
            # initialize the rupture serial numbers before the
            # filtering; in this way the serials are independent
            # from the site collection; this is ultra-fast
            csm.init_serials()
        return csm

    def pre_execute(self):
        """
        Check if there is a pre_calculator or a previous calculation ID.
        If yes, read the inputs by invoking the precalculator or by retrieving
        the previous calculation; if not, read the inputs directly.
        """
        precalc_id = self.oqparam.hazard_calculation_id
        job_info = {}
        if self.pre_calculator is not None:
            # the parameter hazard_calculation_id is only meaningful if
            # there is a precalculator
            self.precalc = (self.compute_previous() if precalc_id is None
                            else self.read_previous(precalc_id))
            self.init()
        else:  # we are in a basic calculator
            self.precalc = None
            self.basic_pre_execute()
            if 'source' in self.oqparam.inputs:
                job_info.update(readinput.get_job_info(
                    self.oqparam, self.csm, self.sitecol))
        if hasattr(self, 'riskmodel'):
            job_info['require_epsilons'] = bool(self.riskmodel.covs)
        self._monitor.save_info(job_info)
        self.param = {}  # used in the risk calculators

    def init(self):
        """
        To be overridden to initialize the datasets needed by the calculation
        """
        if not self.oqparam.imtls:
            raise ValueError('Missing intensity_measure_types!')
        if self.precalc:
            self.rlzs_assoc = self.precalc.rlzs_assoc
        elif 'csm_info' in self.datastore:
            self.rlzs_assoc = self.datastore['csm_info'].get_rlzs_assoc()
        else:  # build a fake; used by risk-from-file calculators
            self.datastore['csm_info'] = fake = source.CompositionInfo.fake()
            self.rlzs_assoc = fake.get_rlzs_assoc()

    def read_exposure(self):
        """
        Read the exposure, the riskmodel and update the attributes .exposure,
        .sitecol, .assets_by_site, .taxonomies.
        """
        logging.info('Reading the exposure')
        with self.monitor('reading exposure', autoflush=True):
            self.exposure = readinput.get_exposure(self.oqparam)
            self.sitecol, self.assetcol = (
                readinput.get_sitecol_assetcol(self.oqparam, self.exposure))
            # NB: using hdf5.vstr would fail for large exposures;
            # the datastore could become corrupt, and also ultra-strange
            # may happen (i.e. having the sitecol saved inside asset_refs!!)
            arefs = numpy.array(self.exposure.asset_refs)
            self.datastore['asset_refs'] = arefs
            self.datastore.set_attrs('asset_refs', nbytes=arefs.nbytes)
            logging.info('Read %d assets on %d sites',
                         len(self.assetcol), len(self.sitecol))

    def get_min_iml(self, oq):
        # set the minimum_intensity
        if hasattr(self, 'riskmodel') and not oq.minimum_intensity:
            # infer it from the risk models if not directly set in job.ini
            oq.minimum_intensity = self.riskmodel.get_min_iml()
        min_iml = calc.fix_minimum_intensity(
            oq.minimum_intensity, oq.imtls)
        if min_iml.sum() == 0:
            logging.warn('The GMFs are not filtered: '
                         'you may want to set a minimum_intensity')
        else:
            logging.info('minimum_intensity=%s', oq.minimum_intensity)
        return min_iml

    def load_riskmodel(self):
        """
        Read the risk model and set the attribute .riskmodel.
        The riskmodel can be empty for hazard calculations.
        Save the loss ratios (if any) in the datastore.
        """
        self.riskmodel = rm = readinput.get_risk_model(self.oqparam)
        if not self.riskmodel:  # can happen only in a hazard calculation
            return
        self.save_params()  # re-save oqparam
        # save the risk models and loss_ratios in the datastore
        self.datastore['composite_risk_model'] = rm
        attrs = self.datastore.getitem('composite_risk_model').attrs
        attrs['min_iml'] = hdf5.array_of_vstr(sorted(rm.get_min_iml().items()))
        if rm.damage_states:
            # best not to save them as bytes, they are used as headers
            attrs['damage_states'] = hdf5.array_of_vstr(rm.damage_states)
        self.datastore.set_nbytes('composite_risk_model')
        self.datastore.hdf5.flush()

    def assoc_assets(self, haz_sitecol):
        """
        Associate the exposure assets to the hazard sites and redefine
        the .sitecol and .assetcol attributes.
        """
        if haz_sitecol is not None and haz_sitecol != self.sitecol:
            num_assets = self.count_assets()
            with self.monitor('assoc_assets_sites', autoflush=True):
                self.sitecol, self.assetcol = \
                    self.assoc_assets_sites(haz_sitecol.complete)
            ok_assets = self.count_assets()
            num_sites = len(self.sitecol)
            logging.warn('Associated %d assets to %d sites, %d discarded',
                         ok_assets, num_sites, num_assets - ok_assets)

    def read_risk_data(self):
        """
        Read the exposure (if any), the risk model (if any) and then the
        site collection, possibly extracted from the exposure.
        """
        oq = self.oqparam
        with self.monitor('reading site collection', autoflush=True):
            haz_sitecol = readinput.get_site_collection(oq)
        if haz_sitecol is not None:
            logging.info('Read %d hazard site(s)', len(haz_sitecol))
        oq_hazard = (self.datastore.parent['oqparam']
                     if self.datastore.parent else None)
        if 'exposure' in oq.inputs:
            self.read_exposure()
            self.load_riskmodel()  # must be called *after* read_exposure
            if self.datastore.parent:
                haz_sitecol = self.datastore.parent['sitecol']
            self.assoc_assets(haz_sitecol)
        elif oq.job_type == 'risk':
            raise RuntimeError(
                'Missing exposure_file in %(job_ini)s' % oq.inputs)
        else:  # no exposure
            self.load_riskmodel()
            self.sitecol = haz_sitecol

        if oq_hazard:
            parent = self.datastore.parent
            if 'assetcol' in parent:
                check_time_event(oq, parent['assetcol'].time_events)
            if oq_hazard.time_event and oq_hazard.time_event != oq.time_event:
                raise ValueError(
                    'The risk configuration file has time_event=%s but the '
                    'hazard was computed with time_event=%s' % (
                        oq.time_event, oq_hazard.time_event))

        if self.oqparam.job_type == 'risk':
            taxonomies = set(self.taxonomies)

            # check that we are covering all the taxonomies in the exposure
            missing = taxonomies - set(self.riskmodel.taxonomies)
            if self.riskmodel and missing:
                raise RuntimeError('The exposure contains the taxonomies %s '
                                   'which are not in the risk model' % missing)

            # same check for the consequence models, if any
            consequence_models = riskmodels.get_risk_models(
                self.oqparam, 'consequence')
            for lt, cm in consequence_models.items():
                missing = taxonomies - set(cm)
                if missing:
                    raise ValueError(
                        'Missing consequenceFunctions for %s' %
                        ' '.join(missing))

    def count_eff_ruptures(self, result_dict, src_group_id):
        """
        Returns the number of ruptures in the src_group (after filtering)
        or 0 if the src_group has been filtered away.

        :param result_dict: a dictionary with keys (grp_id, gsim)
        :param src_group_id: the source group ID
        """
        return result_dict.eff_ruptures.get(src_group_id, 0)

    def store_source_info(self, infos, acc):
        # save the calculation times per each source
        if infos:
            rows = sorted(
                infos.values(),
                key=operator.attrgetter('calc_time'),
                reverse=True)
            array = numpy.zeros(len(rows), source.SourceInfo.dt)
            for i, row in enumerate(rows):
                for name in array.dtype.names:
                    value = getattr(row, name)
                    if name == 'grp_id' and isinstance(value, list):
                        # same ID sources; store only the first
                        value = value[0]
                    array[i][name] = value
            self.datastore['source_info'] = array
            infos.clear()
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc(
            partial(self.count_eff_ruptures, acc), self.oqparam.sm_lt_path)
        self.datastore['csm_info'] = self.csm.info
        if 'source_info' in self.datastore:
            # the table is missing for UCERF, we should fix that
            self.datastore.set_attrs(
                'source_info', nbytes=array.nbytes,
                has_dupl_sources=self.csm.has_dupl_sources)
        self.datastore.flush()

    def post_process(self):
        """For compatibility with the engine"""


class RiskCalculator(HazardCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .riskmodel, .sitecol, .assets_by_site, .exposure
    .riskinputs in the pre_execute phase.
    """
    def make_eps(self, num_ruptures):
        """
        :param num_ruptures: the size of the epsilon array for each asset
        """
        oq = self.oqparam
        with self.monitor('building epsilons', autoflush=True):
            return riskinput.make_eps(
                self.assetcol, num_ruptures,
                oq.master_seed, oq.asset_correlation)

    def build_riskinputs(self, kind, eps=numpy.zeros(0), eids=None):
        """
        :param kind:
            kind of hazard getter, can be 'poe' or 'gmf'
        :param eps:
            a matrix of epsilons (possibly empty)
        :param eids:
            an array of event IDs (or None)
        :returns:
            a list of RiskInputs objects, sorted by IMT.
        """
        imtls = self.oqparam.imtls
        if not set(self.oqparam.risk_imtls) & set(imtls):
            rsk = ', '.join(self.oqparam.risk_imtls)
            haz = ', '.join(imtls)
            raise ValueError('The IMTs in the risk models (%s) are disjoint '
                             "from the IMTs in the hazard (%s)" % (rsk, haz))
        num_tasks = self.oqparam.concurrent_tasks or 1
        assets_by_site = self.assetcol.assets_by_site()
        self.tagmask = self.assetcol.tagmask()
        with self.monitor('building riskinputs', autoflush=True):
            riskinputs = []
            sid_weight_pairs = [
                (sid, len(assets))
                for sid, assets in enumerate(assets_by_site)]
            blocks = general.split_in_blocks(
                sid_weight_pairs, num_tasks, weight=operator.itemgetter(1))
            for block in blocks:
                sids = numpy.array([sid for sid, _weight in block])
                reduced_assets = assets_by_site[sids]
                # dictionary of epsilons for the reduced assets
                reduced_eps = collections.defaultdict(F32)
                for assets in reduced_assets:
                    for ass in assets:
                        ass.tagmask = self.tagmask[ass.ordinal]
                        if len(eps):
                            reduced_eps[ass.ordinal] = eps[ass.ordinal]
                # build the riskinputs
                if kind == 'poe':  # hcurves, shape (R, N)
                    getter = calc.PmapGetter(self.datastore, sids)
                else:  # gmf
                    getter = riskinput.GmfDataGetter(self.datastore, sids)
                hgetter = riskinput.HazardGetter(
                    self.datastore, kind, getter, imtls, eids)
                hgetter.init()  # read the hazard data
                ri = riskinput.RiskInput(hgetter, reduced_assets, reduced_eps)
                if ri.weight > 0:
                    riskinputs.append(ri)
            assert riskinputs
            logging.info('Built %d risk inputs', len(riskinputs))
            return riskinputs

    def execute(self):
        """
        Parallelize on the riskinputs and returns a dictionary of results.
        Require a `.core_task` to be defined with signature
        (riskinputs, riskmodel, rlzs_assoc, monitor).
        """
        mon = self.monitor('risk')
        all_args = [(riskinput, self.riskmodel, self.param, mon)
                    for riskinput in self.riskinputs]
        res = Starmap(self.core_task.__func__, all_args).reduce(self.combine)
        return res

    def combine(self, acc, res):
        return acc + res

U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32


def get_gmv_data(sids, gmfs):
    """
    Convert an array of shape (R, N, E, I) into an array of type gmv_data_dt
    """
    R, N, E, I = gmfs.shape
    gmv_data_dt = numpy.dtype(
        [('rlzi', U16), ('sid', U32), ('eid', U64), ('gmv', (F32, (I,)))])
    # NB: ordering of the loops: first site, then event, then realization
    # it is such that save_gmf_data saves the indices correctly for each sid
    it = ((r, sids[s], eid, gmfa[s, eid])
          for s, eid in itertools.product(
                  numpy.arange(N, dtype=U32), numpy.arange(E, dtype=U64))
          for r, gmfa in enumerate(gmfs))
    return numpy.fromiter(it, gmv_data_dt)


def get_gmfs(calculator):
    """
    :param calculator: a scenario_risk/damage or gmf_ebrisk calculator
    :returns: a pair (eids, gmfs) where gmfs is a matrix of shape (R, N, E, I)
    """
    dstore = calculator.datastore
    oq = calculator.oqparam
    sitecol = calculator.sitecol
    if dstore.parent:
        haz_sitecol = dstore.parent['sitecol']  # S sites
    else:
        haz_sitecol = sitecol  # N sites
    N = len(haz_sitecol.complete)
    I = len(oq.imtls)
    if 'gmfs' in oq.inputs:  # from file
        logging.info('Reading gmfs from file')
        eids, gmfs = readinput.get_gmfs(oq)
        E = len(eids)
        if hasattr(oq, 'number_of_ground_motion_fields'):
            if oq.number_of_ground_motion_fields != E:
                raise RuntimeError(
                    'Expected %d ground motion fields, found %d' %
                    (oq.number_of_ground_motion_fields, E))
        else:  # set the number of GMFs from the file
            oq.number_of_ground_motion_fields = E
        # NB: get_gmfs redefine oq.sites in case of GMFs from XML or CSV
        haz_sitecol = readinput.get_site_collection(oq) or haz_sitecol
        calculator.assoc_assets(haz_sitecol)
        R, N, E, I = gmfs.shape
        save_gmf_data(dstore, haz_sitecol,
                      gmfs[:, haz_sitecol.indices])

        # store the events, useful when read the GMFs from a file
        events = numpy.zeros(E, readinput.stored_event_dt)
        events['eid'] = eids
        dstore['events'] = events
        return eids, gmfs

    elif calculator.precalc:  # from previous step
        num_assocs = dstore['csm_info'].get_num_rlzs()
        E = oq.number_of_ground_motion_fields
        eids = numpy.arange(E)
        gmfs = numpy.zeros((num_assocs, N, E, I))
        for g, gsim in enumerate(calculator.precalc.gsims):
            gmfs[g, sitecol.sids] = calculator.precalc.gmfa[gsim]
        return eids, gmfs


def save_gmf_data(dstore, sitecol, gmfs):
    """
    :param dstore: a :class:`openquake.baselib.datastore.DataStore` instance
    :param sitecol: a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param gmfs: an array of shape (R, N, E, I)
    """
    offset = 0
    dstore['gmf_data/data'] = gmfa = get_gmv_data(sitecol.sids, gmfs)
    dic = general.group_array(gmfa, 'sid')
    lst = []
    for sid in sitecol.complete.sids:
        rows = dic.get(sid, ())
        n = len(rows)
        lst.append(numpy.array([(offset, offset + n)], riskinput.indices_dt))
        offset += n
    dstore.save_vlen('gmf_data/indices', lst)
    dstore.set_attrs('gmf_data', num_gmfs=len(gmfs))
