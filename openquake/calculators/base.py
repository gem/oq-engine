# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
import os
import sys
import abc
import pdb
import logging
import operator
import itertools
import traceback
from datetime import datetime
from shapely import wkt
import numpy

from openquake.baselib import (
    config, general, hdf5, datastore, __version__ as engine_version)
from openquake.baselib.performance import perf_dt, Monitor
from openquake.hazardlib.calc.filters import SourceFilter, RtreeFilter
from openquake.risklib import riskinput, riskmodels
from openquake.commonlib import readinput, source, calc, writers
from openquake.baselib.parallel import Starmap
from openquake.hazardlib.shakemap import get_sitecol_shakemap, to_gmfs
from openquake.calculators.export import export as exp
from openquake.calculators.getters import GmfDataGetter, PmapGetter

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_trt = operator.attrgetter('src_group_id')
get_imt = operator.attrgetter('imt')

calculators = general.CallableDict(operator.attrgetter('calculation_mode'))
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
TWO16 = 2 ** 16


class InvalidCalculationID(Exception):
    """
    Raised when running a post-calculation on top of an incompatible
    pre-calculation
    """


PRECALC_MAP = dict(
    classical=['psha'],
    disaggregation=['psha'],
    scenario_risk=['scenario'],
    scenario_damage=['scenario'],
    classical_risk=['classical'],
    classical_bcr=['classical'],
    classical_damage=['classical'],
    event_based=['event_based', 'event_based_risk', 'ucerf_hazard'],
    event_based_risk=['event_based', 'event_based_risk', 'ucerf_hazard'],
    ucerf_classical=['ucerf_psha'],
    ucerf_hazard=['ucerf_hazard'])


def fix_ones(pmap):
    """
    Physically, an extremely small intensity measure level can have an
    extremely large probability of exceedence, however that probability
    cannot be exactly 1 unless the level is exactly 0. Numerically, the
    PoE can be 1 and this give issues when calculating the damage (there
    is a log(0) in
    :class:`openquake.risklib.scientific.annual_frequency_of_exceedence`).
    Here we solve the issue by replacing the unphysical probabilities 1
    with .9999999999999999 (the float64 closest to 1).
    """
    for sid in pmap:
        array = pmap[sid].array
        array[array == 1.] = .9999999999999999
    return pmap


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


class BaseCalculator(metaclass=abc.ABCMeta):
    """
    Abstract base class for all calculators.

    :param oqparam: OqParam object
    :param monitor: monitor object
    :param calc_id: numeric calculation ID
    """
    from_engine = False  # set by engine.run_calc
    is_stochastic = False  # True for scenario and event based calculators

    def __init__(self, oqparam, calc_id=None):
        self.datastore = datastore.DataStore(calc_id)
        self._monitor = Monitor(
            '%s.run' % self.__class__.__name__, measuremem=True)
        self.oqparam = oqparam
        if 'performance_data' not in self.datastore:
            self.datastore.create_dset('performance_data', perf_dt)

    def monitor(self, operation='', **kw):
        """
        :returns: a new Monitor instance
        """
        mon = self._monitor(operation, hdf5=self.datastore.hdf5)
        self._monitor.calc_id = mon.calc_id = self.datastore.calc_id
        vars(mon).update(kw)
        return mon

    def save_params(self, **kw):
        """
        Update the current calculation parameters and save engine_version
        """
        if ('hazard_calculation_id' in kw and
                kw['hazard_calculation_id'] is None):
            del kw['hazard_calculation_id']
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
        with self._monitor:
            self._monitor.username = kw.get('username', '')
            self._monitor.hdf5 = self.datastore.hdf5
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
            try:
                if pre_execute:
                    self.pre_execute()
                self.result = self.execute()
                if self.result is not None:
                    self.post_execute(self.result)
                self.before_export()
                self.export(kw.get('exports', ''))
            except Exception:
                if kw.get('pdb'):  # post-mortem debug
                    tb = sys.exc_info()[2]
                    traceback.print_tb(tb)
                    pdb.post_mortem(tb)
                else:
                    logging.critical('', exc_info=True)
                    raise
            finally:
                # cleanup globals
                if ct == 0:  # restore OQ_DISTRIBUTE
                    if oq_distribute is None:  # was not set
                        del os.environ['OQ_DISTRIBUTE']
                    else:
                        os.environ['OQ_DISTRIBUTE'] = oq_distribute
                readinput.pmap = None
                readinput.exposure = None
                readinput.gmfs = None
                readinput.eids = None
                self._monitor.flush()

                if close:  # in the engine we close later
                    self.result = None
                    try:
                        self.datastore.close()
                    except (RuntimeError, ValueError):
                        # sometimes produces errors but they are difficult to
                        # reproduce
                        logging.warn('', exc_info=True)

        return getattr(self, 'exported', {})

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
        """
        self.exported = getattr(self.precalc, 'exported', {})
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
                if 'rlzs' in key and self.R > 1:
                    continue  # skip individual curves
                self._export((key, fmt))
            if has_hcurves and self.oqparam.hazard_maps:
                self._export(('hmaps', fmt))
            if has_hcurves and self.oqparam.uniform_hazard_spectra:
                self._export(('uhs', fmt))

    def _export(self, ekey):
        if ekey not in exp or self.exported.get(ekey):  # already exported
            return
        with self.monitor('export'):
            self.exported[ekey] = fnames = exp(ekey, self.datastore)
            if fnames:
                logging.info('exported %s: %s', ekey[0], fnames)

    def before_export(self):
        """
        Set the attributes nbytes
        """
        # sanity check that eff_ruptures have been set, i.e. are not -1
        try:
            csm_info = self.datastore['csm_info']
        except KeyError:
            csm_info = self.datastore['csm_info'] = self.csm.info
        for sm in csm_info.source_models:
            for sg in sm.src_groups:
                assert sg.eff_ruptures != -1, sg

        for key in self.datastore:
            self.datastore.set_nbytes(key)
        self.datastore.flush()


def check_time_event(oqparam, occupancy_periods):
    """
    Check the `time_event` parameter in the datastore, by comparing
    with the periods found in the exposure.
    """
    time_event = oqparam.time_event
    if time_event and time_event not in occupancy_periods:
        raise ValueError(
            'time_event is %s in %s, but the exposure contains %s' %
            (time_event, oqparam.inputs['job_ini'],
             ', '.join(occupancy_periods)))


class HazardCalculator(BaseCalculator):
    """
    Base class for hazard calculators based on source models
    """
    precalc = None

    def get_filter(self):
        """
        :returns: a SourceFilter/RtreeFilter or None
        """
        oq = self.oqparam
        self.hdf5cache = self.datastore.hdf5cache()
        self.src_filter = SourceFilter(
            self.sitecol.complete, oq.maximum_distance, self.hdf5cache)
        if 'ucerf' in oq.calculation_mode:
            # do not preprocess
            return
        elif (oq.prefilter_sources == 'rtree' and 'event_based' not in
                oq.calculation_mode):
            # rtree can be used only with processpool, otherwise one gets an
            # RTreeError: Error in "Index_Create": Spatial Index Error:
            # IllegalArgumentException: SpatialIndex::DiskStorageManager:
            # Index/Data file cannot be read/writen.
            logging.info('Preprocessing the sources with rtree')
            src_filter = RtreeFilter(self.sitecol.complete,
                                     oq.maximum_distance, self.hdf5cache)
        else:
            src_filter = self.src_filter
        return src_filter

    def can_read_parent(self):
        """
        :returns:
            the parent datastore if it is present and can be read from the
            workers, None otherwise
        """
        read_access = (
            config.distribution.oq_distribute in ('no', 'processpool') or
            config.directory.shared_dir)
        hdf5cache = getattr(self, 'hdf5cache', None)
        if hdf5cache and read_access:
            return hdf5cache
        elif (self.oqparam.hazard_calculation_id and read_access and
                'gmf_data' not in self.datastore.hdf5):
            self.datastore.parent.close()  # make sure it is closed
            return self.datastore.parent
        logging.warn('With a parent calculation reading the hazard '
                     'would be faster')

    def check_overflow(self):
        """Overridden in event based"""

    def check_floating_spinning(self):
        op = '=' if self.oqparam.pointsource_distance == {} else '<'
        f, s = self.csm.get_floating_spinning_factors()
        if f != 1:
            logging.info('Rupture floating factor %s %s', op, f)
        if s != 1:
            logging.info('Rupture spinning factor %s %s', op, s)

    def read_inputs(self):
        """
        Read risk data and sources if any
        """
        oq = self.oqparam
        self._read_risk_data()
        self.check_overflow()  # check if self.sitecol is too large
        if 'source' in oq.inputs and oq.hazard_calculation_id is None:
            self.csm = readinput.get_composite_source_model(
                oq, self.monitor(), srcfilter=self.get_filter())
        self.init()  # do this at the end of pre-execute

    def pre_execute(self, pre_calculator=None):
        """
        Check if there is a previous calculation ID.
        If yes, read the inputs by retrieving the previous calculation;
        if not, read the inputs directly.
        """
        oq = self.oqparam
        if 'gmfs' in oq.inputs:  # read hazard from file
            assert not oq.hazard_calculation_id, (
                'You cannot use --hc together with gmfs_file')
            self.read_inputs()
            save_gmfs(self)
        elif 'hazard_curves' in oq.inputs:  # read hazard from file
            assert not oq.hazard_calculation_id, (
                'You cannot use --hc together with hazard_curves')
            haz_sitecol = readinput.get_site_collection(oq)
            # NB: horrible: get_site_collection calls get_pmap_from_nrml
            # that sets oq.investigation_time, so it must be called first
            self.load_riskmodel()  # must be after get_site_collection
            self.read_exposure(haz_sitecol)  # define .assets_by_site
            self.datastore['poes/grp-00'] = fix_ones(readinput.pmap)
            self.datastore['sitecol'] = self.sitecol
            self.datastore['assetcol'] = self.assetcol
            self.datastore['csm_info'] = fake = source.CompositionInfo.fake()
            self.rlzs_assoc = fake.get_rlzs_assoc()
        elif oq.hazard_calculation_id:
            parent = datastore.read(oq.hazard_calculation_id)
            check_precalc_consistency(
                oq.calculation_mode,
                parent['oqparam'].calculation_mode)
            self.datastore.parent = parent
            # copy missing parameters from the parent
            params = {name: value for name, value in
                      vars(parent['oqparam']).items()
                      if name not in vars(self.oqparam)}
            self.save_params(**params)
            self.read_inputs()
            oqp = parent['oqparam']
            if oqp.investigation_time != oq.investigation_time:
                raise ValueError(
                    'The parent calculation was using investigation_time=%s'
                    ' != %s' % (oqp.investigation_time, oq.investigation_time))
            if oqp.minimum_intensity != oq.minimum_intensity:
                raise ValueError(
                    'The parent calculation was using minimum_intensity=%s'
                    ' != %s' % (oqp.minimum_intensity, oq.minimum_intensity))
            missing_imts = set(oq.imtls) - set(oqp.imtls)
            if missing_imts:
                raise ValueError(
                    'The parent calculation is missing the IMT(s) %s' %
                    ', '.join(missing_imts))
        elif pre_calculator:
            calc = calculators[pre_calculator](
                self.oqparam, self.datastore.calc_id)
            calc.run()
            self.param = calc.param
            self.sitecol = calc.sitecol
            self.assetcol = calc.assetcol
            self.riskmodel = calc.riskmodel
            self.rlzs_assoc = calc.rlzs_assoc
        else:
            self.read_inputs()
        if self.riskmodel:
            self.save_riskmodel()

    def init(self):
        """
        To be overridden to initialize the datasets needed by the calculation
        """
        if not self.oqparam.risk_imtls:
            if self.datastore.parent:
                self.oqparam.risk_imtls = (
                    self.datastore.parent['oqparam'].risk_imtls)
            elif not self.oqparam.imtls:
                raise ValueError('Missing intensity_measure_types!')
        if self.precalc:
            self.rlzs_assoc = self.precalc.rlzs_assoc
        elif 'csm_info' in self.datastore:
            self.rlzs_assoc = self.datastore['csm_info'].get_rlzs_assoc()
        elif hasattr(self, 'csm'):
            self.check_floating_spinning()
            self.rlzs_assoc = self.csm.info.get_rlzs_assoc()
            self.datastore['csm_info'] = self.csm.info
        else:  # build a fake; used by risk-from-file calculators
            self.datastore['csm_info'] = fake = source.CompositionInfo.fake()
            self.rlzs_assoc = fake.get_rlzs_assoc()

    def read_exposure(self, haz_sitecol=None):
        """
        Read the exposure, the riskmodel and update the attributes
        .sitecol, .assetcol
        """
        with self.monitor('reading exposure', autoflush=True):
            self.sitecol, self.assetcol, discarded = (
                readinput.get_sitecol_assetcol(
                    self.oqparam, haz_sitecol, self.riskmodel.loss_types))
            if len(discarded):
                self.datastore['discarded'] = discarded
                msg = ('%d sites with assets were discarded; use '
                       '`oq plot_assets` to see them' % len(discarded))
                if hasattr(self, 'rup') or self.oqparam.discard_assets:
                    # just log a warning in case of scenario from rupture
                    # or when discard_assets is set to True
                    logging.warn(msg)
                else:  # raise an error
                    self.datastore['sitecol'] = self.sitecol
                    self.datastore['assetcol'] = self.assetcol
                    raise RuntimeError(msg)
            readinput.exposure = None  # reset the global
        # reduce the riskmodel to the relevant taxonomies
        taxonomies = set(taxo for taxo in self.assetcol.tagcol.taxonomy
                         if taxo != '?')
        if len(self.riskmodel.taxonomies) > len(taxonomies):
            logging.info('Reducing risk model from %d to %d taxonomies',
                         len(self.riskmodel.taxonomies), len(taxonomies))
            self.riskmodel = self.riskmodel.reduce(taxonomies)

    def get_min_iml(self, oq):
        # set the minimum_intensity
        if hasattr(self, 'riskmodel') and not oq.minimum_intensity:
            # infer it from the risk models if not directly set in job.ini
            oq.minimum_intensity = self.riskmodel.min_iml
        min_iml = calc.fix_minimum_intensity(oq.minimum_intensity, oq.imtls)
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
        logging.info('Reading the risk model if present')
        self.riskmodel = readinput.get_risk_model(self.oqparam)
        if not self.riskmodel:
            parent = self.datastore.parent
            if 'fragility' in parent or 'vulnerability' in parent:
                self.riskmodel = riskinput.read_composite_risk_model(parent)
            return
        self.save_params()  # re-save oqparam

    def save_riskmodel(self):
        """
        Save the risk models in the datastore
        """
        oq = self.oqparam
        self.datastore[oq.risk_model] = rm = self.riskmodel
        attrs = self.datastore.getitem(oq.risk_model).attrs
        attrs['min_iml'] = hdf5.array_of_vstr(sorted(rm.min_iml.items()))
        self.datastore.set_nbytes(oq.risk_model)

    def _read_risk_data(self):
        # read the exposure (if any), the risk model (if any) and then the
        # site collection, possibly extracted from the exposure.
        oq = self.oqparam
        self.load_riskmodel()  # must be called first

        if oq.hazard_calculation_id:
            with datastore.read(oq.hazard_calculation_id) as dstore:
                haz_sitecol = dstore['sitecol'].complete
        else:
            haz_sitecol = readinput.get_site_collection(oq)
            if hasattr(self, 'rup'):
                # for scenario we reduce the site collection to the sites
                # within the maximum distance from the rupture
                haz_sitecol, _dctx = self.cmaker.filter(
                    haz_sitecol, self.rup)
                haz_sitecol.make_complete()

        oq_hazard = (self.datastore.parent['oqparam']
                     if self.datastore.parent else None)
        if 'exposure' in oq.inputs:
            self.read_exposure(haz_sitecol)
            self.datastore['assetcol'] = self.assetcol
        elif 'assetcol' in self.datastore.parent:
            assetcol = self.datastore.parent['assetcol']
            if oq.region:
                region = wkt.loads(self.oqparam.region)
                self.sitecol = haz_sitecol.within(region)
            if oq.shakemap_id or 'shakemap' in oq.inputs:
                self.sitecol, self.assetcol = self.read_shakemap(
                    haz_sitecol, assetcol)
                self.datastore['assetcol'] = self.assetcol
                logging.info('Extracted %d/%d assets',
                             len(self.assetcol), len(assetcol))
            elif hasattr(self, 'sitecol') and general.not_equal(
                    self.sitecol.sids, haz_sitecol.sids):
                self.assetcol = assetcol.reduce(self.sitecol)
                self.datastore['assetcol'] = self.assetcol
                logging.info('Extracted %d/%d assets',
                             len(self.assetcol), len(assetcol))
            else:
                self.assetcol = assetcol
        else:  # no exposure
            self.sitecol = haz_sitecol
            logging.info('Read %d hazard sites', len(self.sitecol))

        if oq_hazard:
            parent = self.datastore.parent
            if 'assetcol' in parent:
                check_time_event(oq, parent['assetcol'].occupancy_periods)
            elif oq.job_type == 'risk' and 'exposure' not in oq.inputs:
                raise ValueError('Missing exposure both in hazard and risk!')
            if oq_hazard.time_event and oq_hazard.time_event != oq.time_event:
                raise ValueError(
                    'The risk configuration file has time_event=%s but the '
                    'hazard was computed with time_event=%s' % (
                        oq.time_event, oq_hazard.time_event))

        if self.oqparam.job_type == 'risk':
            taxonomies = set(taxo for taxo in self.assetcol.tagcol.taxonomy
                             if taxo != '?')

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

        if hasattr(self, 'sitecol'):
            self.datastore['sitecol'] = self.sitecol.complete
        # used in the risk calculators
        self.param = dict(individual_curves=oq.individual_curves)

    def store_csm_info(self, eff_ruptures):
        """
        Save info about the composite source model inside the csm_info dataset
        """
        self.csm.info.update_eff_ruptures(eff_ruptures)
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc(self.oqparam.sm_lt_path)
        if not self.rlzs_assoc:
            raise RuntimeError('Empty logic tree: too much filtering?')
        self.datastore['csm_info'] = self.csm.info
        R = len(self.rlzs_assoc.realizations)
        if 'event_based' in self.oqparam.calculation_mode and R >= TWO16:
            # rlzi is 16 bit integer in the GMFs, so there is hard limit or R
            raise ValueError(
                'The logic tree has %d realizations, the maximum '
                'is %d' % (R, TWO16))
        elif R > 10000:
            logging.warn(
                'The logic tree has %d realizations(!), please consider '
                'sampling it', R)
        self.datastore.flush()

    def store_source_info(self, calc_times):
        """
        Save (weight, num_sites, calc_time) inside the source_info dataset
        """
        if calc_times:
            source_info = self.datastore['source_info']
            ids, vals = zip(*sorted(calc_times.items()))
            vals = numpy.array(vals)  # shape (n, 3)
            source_info[ids, 'weight'] += vals[:, 0]
            source_info[ids, 'num_sites'] += vals[:, 1]
            source_info[ids, 'calc_time'] += vals[:, 2]

    def post_process(self):
        """For compatibility with the engine"""


def build_hmaps(hcurves_by_kind, slice_, imtls, poes, monitor):
    """
    Build hazard maps from a slice of hazard curves.
    :returns: a pair ({kind: hmaps}, slice)
    """
    dic = {}
    for kind, hcurves in hcurves_by_kind.items():
        dic[kind] = calc.make_hmap_array(hcurves, imtls, poes, len(hcurves))
    return dic, slice_


class RiskCalculator(HazardCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .riskmodel, .sitecol, .assetcol, .riskinputs in the
    pre_execute phase.
    """
    @property
    def R(self):
        """
        :returns: the number of realizations as read from `csm_info`
        """
        try:
            return self._R
        except AttributeError:
            self._R = self.datastore['csm_info'].get_num_rlzs()
            return self._R

    def read_shakemap(self, haz_sitecol, assetcol):
        """
        Enabled only if there is a shakemap_id parameter in the job.ini.
        Download, unzip, parse USGS shakemap files and build a corresponding
        set of GMFs which are then filtered with the hazard site collection
        and stored in the datastore.
        """
        oq = self.oqparam
        E = oq.number_of_ground_motion_fields
        oq.risk_imtls = oq.imtls or self.datastore.parent['oqparam'].imtls
        extra = self.riskmodel.get_extra_imts(oq.risk_imtls)
        if extra:
            logging.warn('There are risk functions for not available IMTs '
                         'which will be ignored: %s' % extra)

        logging.info('Getting/reducing shakemap')
        with self.monitor('getting/reducing shakemap'):
            smap = oq.shakemap_id if oq.shakemap_id else numpy.load(
                oq.inputs['shakemap'])
            sitecol, shakemap, discarded = get_sitecol_shakemap(
                smap, oq.imtls, haz_sitecol, oq.asset_hazard_distance,
                oq.discard_assets)
            if len(discarded):
                self.datastore['discarded'] = discarded
            assetcol = assetcol.reduce_also(sitecol)

        logging.info('Building GMFs')
        with self.monitor('building/saving GMFs'):
            imts, gmfs = to_gmfs(
                shakemap, oq.cross_correlation, oq.site_effects,
                oq.truncation_level, E, oq.random_seed, oq.imtls)
            save_gmf_data(self.datastore, sitecol, gmfs, imts)
            events = numpy.zeros(E, readinput.stored_event_dt)
            events['eid'] = numpy.arange(E, dtype=U64)
            self.datastore['events'] = events
        return sitecol, assetcol

    def build_riskinputs(self, kind, eps=None, num_events=0):
        """
        :param kind:
            kind of hazard getter, can be 'poe' or 'gmf'
        :param eps:
            a matrix of epsilons (or None)
        :param num_events:
            how many events there are
        :returns:
            a list of RiskInputs objects, sorted by IMT.
        """
        logging.info('Building risk inputs from %d realization(s)', self.R)
        imtls = self.oqparam.imtls
        if not set(self.oqparam.risk_imtls) & set(imtls):
            rsk = ', '.join(self.oqparam.risk_imtls)
            haz = ', '.join(imtls)
            raise ValueError('The IMTs in the risk models (%s) are disjoint '
                             "from the IMTs in the hazard (%s)" % (rsk, haz))
        if not hasattr(self, 'assetcol'):
            self.assetcol = self.datastore['assetcol']
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy
        with self.monitor('building riskinputs', autoflush=True):
            riskinputs = list(self._gen_riskinputs(kind, eps, num_events))
        assert riskinputs
        logging.info('Built %d risk inputs', len(riskinputs))
        return riskinputs

    def _gen_riskinputs(self, kind, eps, num_events):
        assets_by_site = self.assetcol.assets_by_site()
        dstore = self.can_read_parent() or self.datastore
        for sid, assets in enumerate(assets_by_site):
            if len(assets) == 0:
                continue
            # build the riskinputs
            if kind == 'poe':  # hcurves, shape (R, N)
                getter = PmapGetter(dstore, self.rlzs_assoc, [sid])
                getter.num_rlzs = self.R
            else:  # gmf
                getter = GmfDataGetter(dstore, [sid], self.R)
            if dstore is self.datastore:
                # read the hazard data in the controller node
                getter.init()
            else:
                # the datastore must be closed to avoid the HDF5 fork bug
                assert dstore.hdf5 == (), '%s is not closed!' % dstore
            for block in general.block_splitter(assets, 1000):
                # dictionary of epsilons for the reduced assets
                reduced_eps = {ass.ordinal: eps[ass.ordinal]
                               for ass in block
                               if eps is not None and len(eps)}
                yield riskinput.RiskInput(getter, [block], reduced_eps)

    def execute(self):
        """
        Parallelize on the riskinputs and returns a dictionary of results.
        Require a `.core_task` to be defined with signature
        (riskinputs, riskmodel, rlzs_assoc, monitor).
        """
        if not hasattr(self, 'riskinputs'):  # in the reportwriter
            return
        res = Starmap.apply(
            self.core_task.__func__,
            (self.riskinputs, self.riskmodel, self.param, self.monitor()),
            concurrent_tasks=self.oqparam.concurrent_tasks or 1,
            weight=get_weight
        ).reduce(self.combine)
        return res

    def combine(self, acc, res):
        return acc + res


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


def save_gmdata(calc, n_rlzs):
    """
    Save a composite array `gmdata` in the datastore.

    :param calc: a calculator with a dictionary .gmdata {rlz: data}
    :param n_rlzs: the total number of realizations
    """
    n_sites = len(calc.sitecol)
    dtlist = ([(imt, F32) for imt in calc.oqparam.imtls] + [('events', U32)])
    array = numpy.zeros(n_rlzs, dtlist)
    for rlzi in sorted(calc.gmdata):
        data = calc.gmdata[rlzi]  # (imts, events)
        events = data[-1]
        gmv = data[:-1] / events / n_sites
        array[rlzi] = tuple(gmv) + (events,)
    calc.datastore['gmdata'] = array


def save_gmfs(calculator):
    """
    :param calculator: a scenario_risk/damage or event_based_risk calculator
    :returns: a pair (eids, R) where R is the number of realizations
    """
    dstore = calculator.datastore
    oq = calculator.oqparam
    logging.info('Reading gmfs from file')
    if oq.inputs['gmfs'].endswith('.csv'):
        # TODO: check if import_gmfs can be removed
        eids, num_rlzs, calculator.gmdata = import_gmfs(
            dstore, oq.inputs['gmfs'], calculator.sitecol.complete.sids)
        save_gmdata(calculator, calculator.R)
    else:  # XML
        eids, gmfs = readinput.eids, readinput.gmfs
    E = len(eids)
    calculator.eids = eids
    if hasattr(oq, 'number_of_ground_motion_fields'):
        if oq.number_of_ground_motion_fields != E:
            raise RuntimeError(
                'Expected %d ground motion fields, found %d' %
                (oq.number_of_ground_motion_fields, E))
    else:  # set the number of GMFs from the file
        oq.number_of_ground_motion_fields = E
    # NB: save_gmfs redefine oq.sites in case of GMFs from XML or CSV
    if oq.inputs['gmfs'].endswith('.xml'):
        haz_sitecol = readinput.get_site_collection(oq)
        R, N, E, I = gmfs.shape
        save_gmf_data(dstore, haz_sitecol, gmfs[:, haz_sitecol.sids],
                      oq.imtls, eids)


def save_gmf_data(dstore, sitecol, gmfs, imts, eids=()):
    """
    :param dstore: a :class:`openquake.baselib.datastore.DataStore` instance
    :param sitecol: a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param gmfs: an array of shape (R, N, E, M)
    :param imts: a list of IMT strings
    :param eids: E event IDs or the empty tuple
    """
    offset = 0
    dstore['gmf_data/data'] = gmfa = get_gmv_data(sitecol.sids, gmfs)
    dic = general.group_array(gmfa, 'sid')
    lst = []
    all_sids = sitecol.complete.sids
    for sid in all_sids:
        rows = dic.get(sid, ())
        n = len(rows)
        lst.append((offset, offset + n))
        offset += n
    dstore['gmf_data/imts'] = ' '.join(imts)
    dstore['gmf_data/indices'] = numpy.array(lst, U32)
    dstore.set_attrs('gmf_data', num_gmfs=len(gmfs))
    if len(eids):  # store the events
        events = numpy.zeros(len(eids), readinput.stored_event_dt)
        events['eid'] = eids
        dstore['events'] = events


def import_gmfs(dstore, fname, sids):
    """
    Import in the datastore a ground motion field CSV file.

    :param dstore: the datastore
    :param fname: the CSV file
    :param sids: the site IDs (complete)
    :returns: event_ids, num_rlzs
    """
    array = writers.read_composite_array(fname).array
    # has header rlzi, sid, eid, gmv_PGA, ...
    imts = [name[4:] for name in array.dtype.names[3:]]
    n_imts = len(imts)
    gmf_data_dt = numpy.dtype(
        [('rlzi', U16), ('sid', U32), ('eid', U64), ('gmv', (F32, (n_imts,)))])
    # store the events
    eids = numpy.unique(array['eid'])
    eids.sort()
    events = numpy.zeros(len(eids), readinput.stored_event_dt)
    events['eid'] = eids
    dstore['events'] = events
    # store the GMFs
    dic = general.group_array(array.view(gmf_data_dt), 'sid')
    lst = []
    offset = 0
    for sid in sids:
        n = len(dic.get(sid, []))
        lst.append((offset, offset + n))
        if n:
            offset += n
            dstore.extend('gmf_data/data', dic[sid])
    dstore['gmf_data/indices'] = numpy.array(lst, U32)
    dstore['gmf_data/imts'] = ' '.join(imts)

    # FIXME: if there is no data for the maximum realization
    # the inferred number of realizations will be wrong
    num_rlzs = array['rlzi'].max() + 1

    # compute gmdata
    dic = general.group_array(array.view(gmf_data_dt), 'rlzi')
    gmdata = {r: numpy.zeros(n_imts + 1, F32) for r in range(num_rlzs)}
    for r in dic:
        gmv = dic[r]['gmv']
        rec = gmdata[r]  # (imt1, ..., imtM, nevents)
        rec[:-1] += gmv.sum(axis=0)
        rec[-1] += len(gmv)
    return eids, num_rlzs, gmdata
