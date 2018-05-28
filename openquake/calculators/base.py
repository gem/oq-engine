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
from functools import partial
from datetime import datetime
from shapely import wkt
import numpy

from openquake.baselib import (
    config, general, hdf5, datastore, __version__ as engine_version)
from openquake.baselib.performance import Monitor
from openquake.hazardlib.calc.filters import SourceFilter, RtreeFilter, rtree
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
logversion = True


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
    event_based=['event_based', 'event_based_rupture', 'ebrisk',
                 'event_based_risk', 'ucerf_rupture'],
    event_based_risk=['event_based', 'event_based_rupture', 'ucerf_rupture',
                      'event_based_risk', 'ucerf_hazard'],
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
    pre_calculator = None  # to be overridden
    is_stochastic = False  # True for scenario and event based calculators

    def __init__(self, oqparam, calc_id=None):
        self.datastore = datastore.DataStore(calc_id)
        self._monitor = Monitor(
            '%s.run' % self.__class__.__name__, measuremem=True)
        self._monitor.hdf5path = self.datastore.hdf5path
        self.oqparam = oqparam

    def monitor(self, operation, **kw):
        """
        :returns: a new Monitor instance
        """
        mon = self._monitor(operation, hdf5path=self.datastore.hdf5path)
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
        global logversion
        with self._monitor:
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
            Starmap.init()
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
                Starmap.shutdown()
        self._monitor.flush()
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

        if self.close:  # in the engine we close later
            self.result = None
            try:
                self.datastore.close()
            except (RuntimeError, ValueError):
                # sometimes produces errors but they are difficult to
                # reproduce
                logging.warn('', exc_info=True)

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
        csm_info = self.datastore['csm_info']
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

    def filter_csm(self):
        """
        :returns: (filtered CompositeSourceModel, SourceFilter)
        """
        oq = self.oqparam
        mon = self.monitor('prefilter')
        self.hdf5cache = self.datastore.hdf5cache()
        src_filter = SourceFilter(self.sitecol.complete, oq.maximum_distance,
                                  self.hdf5cache)
        if (oq.prefilter_sources == 'numpy' or rtree is None):
            csm = self.csm.filter(src_filter, mon)
        elif oq.prefilter_sources == 'rtree':
            prefilter = RtreeFilter(self.sitecol.complete, oq.maximum_distance,
                                    self.hdf5cache)
            csm = self.csm.filter(prefilter, mon)
        else:  # prefilter_sources='no'
            csm = self.csm.filter(SourceFilter(None, {}), mon)
        return csm, src_filter

    def can_read_parent(self):
        """
        :returns:
            the parent datastore if it is present and can be read from the
            workers, None otherwise
        """
        read_access = (
            config.distribution.oq_distribute in ('no', 'processpool') or
            config.directory.shared_dir)
        hdf5cache = getattr(self.precalc, 'hdf5cache', None)
        if hdf5cache and read_access:
            return hdf5cache
        elif (self.oqparam.hazard_calculation_id and read_access and
              'gmf_data' not in self.datastore.hdf5):
            self.datastore.parent.close()  # make sure it is closed
            return self.datastore.parent

    def compute_previous(self):
        precalc = calculators[self.pre_calculator](
            self.oqparam, self.datastore.calc_id)
        precalc.run(close=False)
        if 'scenario' not in self.oqparam.calculation_mode:
            self.csm = precalc.csm
        pre_attrs = vars(precalc)
        if 'riskmodel' in pre_attrs:
            self.riskmodel = precalc.riskmodel
        return precalc

    def read_previous(self, precalc_id):
        """
        Read the previous calculation datastore by checking the consistency
        of the calculation_mode, then read the risk data.
        """
        parent = datastore.read(precalc_id)
        check_precalc_consistency(
            self.oqparam.calculation_mode, parent['oqparam'].calculation_mode)
        self.datastore.parent = parent
        # copy missing parameters from the parent
        params = {name: value for name, value in
                  vars(parent['oqparam']).items()
                  if name not in vars(self.oqparam)}
        self.save_params(**params)
        return parent

    def read_inputs(self):
        """
        Read risk data and sources if any
        """
        oq = self.oqparam
        self.read_risk_data()
        if 'source' in oq.inputs and oq.hazard_calculation_id is None:
            with self.monitor('reading composite source model', autoflush=1):
                self.csm = readinput.get_composite_source_model(oq)
                if oq.disagg_by_src:
                    self.csm = self.csm.grp_by_src()
            with self.monitor('splitting sources', measuremem=1, autoflush=1):
                logging.info('Splitting sources')
                self.csm.split_all()
            if self.is_stochastic:
                # initialize the rupture serial numbers before filtering; in
                # this way the serials are independent from the site collection
                # this is ultra-fast
                self.csm.init_serials()
            f, s = self.csm.get_floating_spinning_factors()
            if f != 1:
                logging.info('Rupture floating factor=%s', f)
            if s != 1:
                logging.info('Rupture spinning factor=%s', s)
            self.csm.info.gsim_lt.check_imts(oq.imtls)
            self.csm.info.gsim_lt.store_gmpe_tables(self.datastore)
            self.rup_data = {}
        self.init()

    def pre_execute(self):
        """
        Check if there is a pre_calculator or a previous calculation ID.
        If yes, read the inputs by invoking the precalculator or by retrieving
        the previous calculation; if not, read the inputs directly.
        """
        precalc_id = self.oqparam.hazard_calculation_id
        if self.pre_calculator is not None:
            # the parameter hazard_calculation_id is only meaningful if
            # there is a precalculator
            if precalc_id is None:
                self.precalc = self.compute_previous()
                self.sitecol = self.precalc.sitecol
            else:
                self.read_previous(precalc_id)
                self.read_risk_data()
            self.init()
        else:  # we are in a basic calculator
            self.read_inputs()
        if hasattr(self, 'sitecol'):
            if 'scenario' in self.oqparam.calculation_mode:
                self.datastore['sitecol'] = self.sitecol
            else:
                self.datastore['sitecol'] = self.sitecol.complete
        self.param = {}  # used in the risk calculators
        if 'gmfs' in self.oqparam.inputs:
            save_gmfs(self)

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
            self.sitecol, self.assetcol = readinput.get_sitecol_assetcol(
                self.oqparam, haz_sitecol)
            readinput.exposure = None  # reset the global

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
        logging.info('Reading the risk model if present')
        self.riskmodel = rm = readinput.get_risk_model(self.oqparam)
        if not self.riskmodel:
            parent = self.datastore.parent
            if 'composite_risk_model' in parent:
                self.riskmodel = riskinput.read_composite_risk_model(parent)
            return
        self.save_params()  # re-save oqparam
        # save the risk models and loss_ratios in the datastore
        self.datastore['composite_risk_model'] = rm
        attrs = self.datastore.getitem('composite_risk_model').attrs
        attrs['min_iml'] = hdf5.array_of_vstr(sorted(rm.get_min_iml().items()))
        self.datastore.set_nbytes('composite_risk_model')
        self.datastore.hdf5.flush()

    def read_risk_data(self):
        """
        Read the exposure (if any), the risk model (if any) and then the
        site collection, possibly extracted from the exposure.
        """
        oq = self.oqparam
        self.load_riskmodel()  # must be called first
        with self.monitor('reading site collection', autoflush=True):
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
                    if name == 'num_sites':
                        value /= (row.num_split or 1)
                    elif name == 'grp_id' and isinstance(value, list):
                        # same ID sources; store only the first
                        value = value[0]
                    array[i][name] = value
            self.datastore['source_info'] = array
            infos.clear()
        self.csm.info.update_eff_ruptures(
            partial(self.count_eff_ruptures, acc))
        self.rlzs_assoc = self.csm.info.get_rlzs_assoc(self.oqparam.sm_lt_path)
        if not self.rlzs_assoc:
            raise RuntimeError('Empty logic tree: too much filtering?')

        self.datastore['csm_info'] = self.csm.info
        R = len(self.rlzs_assoc.realizations)
        if self.is_stochastic and R >= TWO16:
            # rlzi is 16 bit integer in the GMFs, so there is hard limit or R
            raise ValueError(
                'The logic tree has %d realizations, the maximum '
                'is %d' % (R, TWO16))
        elif R > 10000:
            logging.warn(
                'The logic tree has %d realizations(!), please consider '
                'sampling it', R)
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

        logging.info('Getting/reducing shakemap')
        with self.monitor('getting/reducing shakemap'):
            smap = oq.shakemap_id if oq.shakemap_id else numpy.load(
                oq.inputs['shakemap'])
            sitecol, shakemap = get_sitecol_shakemap(
                smap, haz_sitecol, oq.asset_hazard_distance or
                oq.region_grid_spacing)
            assetcol = assetcol.reduce_also(sitecol)

        logging.info('Building GMFs')
        with self.monitor('building/saving GMFs'):
            gmfs = to_gmfs(shakemap, oq.cross_correlation, oq.site_effects,
                           oq.truncation_level, E, oq.random_seed, oq.imtls)
            save_gmf_data(self.datastore, sitecol, gmfs)
            events = numpy.zeros(E, readinput.stored_event_dt)
            events['eid'] = numpy.arange(E, dtype=U64)
            self.datastore['events'] = events
        return sitecol, assetcol

    def make_eps(self, num_ruptures):
        """
        :param num_ruptures: the size of the epsilon array for each asset
        """
        oq = self.oqparam
        with self.monitor('building epsilons', autoflush=True):
            return riskinput.make_eps(
                self.assetcol, num_ruptures,
                oq.master_seed, oq.asset_correlation)

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
        logging.info('Found %d realization(s)', self.R)
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
        num_tasks = self.oqparam.concurrent_tasks or 1
        assets_by_site = self.assetcol.assets_by_site()
        if kind == 'poe':
            indices = None
        else:
            indices = self.datastore['gmf_data/indices'].value
        dstore = self.can_read_parent() or self.datastore
        sid_weight = []
        for sid, assets in enumerate(assets_by_site):
            if len(assets) == 0:
                continue
            elif indices is None:
                weight = len(assets)
            else:
                num_gmfs = sum(stop - start for start, stop in indices[sid])
                weight = len(assets) * (num_gmfs or 1)
            sid_weight.append((sid, weight))
        for block in general.split_in_blocks(
                sid_weight, num_tasks, weight=operator.itemgetter(1)):
            sids = numpy.array([sid for sid, _weight in block])
            reduced_assets = assets_by_site[sids]
            # dictionary of epsilons for the reduced assets
            reduced_eps = {}
            for assets in reduced_assets:
                for ass in assets:
                    if eps is not None and len(eps):
                        reduced_eps[ass.ordinal] = eps[ass.ordinal]
            # build the riskinputs
            if kind == 'poe':  # hcurves, shape (R, N)
                getter = PmapGetter(dstore, self.rlzs_assoc, sids)
                getter.num_rlzs = self.R
            else:  # gmf
                getter = GmfDataGetter(dstore, sids, self.R, num_events)
            if dstore is self.datastore:
                # read the hazard data in the controller node
                logging.info('Reading hazard')
                getter.init()
            else:
                # the datastore must be closed to avoid the HDF5 fork bug
                assert dstore.hdf5 == (), '%s is not closed!' % dstore
            ri = riskinput.RiskInput(getter, reduced_assets, reduced_eps)
            ri.weight = block.weight
            yield ri

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
        save_gmf_data(dstore, haz_sitecol, gmfs[:, haz_sitecol.sids], eids)


def save_gmf_data(dstore, sitecol, gmfs, eids=()):
    """
    :param dstore: a :class:`openquake.baselib.datastore.DataStore` instance
    :param sitecol: a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param gmfs: an array of shape (R, N, E, M)
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
        lst.append(numpy.array([(offset, offset + n)], riskinput.indices_dt))
        offset += n
    dstore.save_vlen('gmf_data/indices', lst)
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
    n_imts = len(array.dtype.names[3:])  # rlzi, sid, eid, gmv_PGA, ...
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
        lst.append(numpy.array([(offset, offset + n)], riskinput.indices_dt))
        if n:
            offset += n
            dstore.extend('gmf_data/data', dic[sid])
    dstore.save_vlen('gmf_data/indices', lst)

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
