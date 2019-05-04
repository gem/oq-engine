# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
import traceback
from datetime import datetime
from shapely import wkt
import numpy

from openquake.baselib import (
    general, hdf5, datastore, __version__ as engine_version)
from openquake.baselib.parallel import Starmap
from openquake.baselib.performance import perf_dt, Monitor
from openquake.hazardlib import InvalidFile
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.source import rupture
from openquake.hazardlib.shakemap import get_sitecol_shakemap, to_gmfs
from openquake.risklib import riskinput
from openquake.commonlib import (
    readinput, logictree, source, calc, writers, util)
from openquake.calculators.ucerf_base import UcerfFilter
from openquake.calculators.export import export as exp
from openquake.calculators import getters

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
RUPTURES_PER_BLOCK = 100000  # used in classical_split_filter


class InvalidCalculationID(Exception):
    """
    Raised when running a post-calculation on top of an incompatible
    pre-calculation
    """


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


def build_weights(realizations, imt_dt):
    """
    :returns: an array with the realization weights of shape R
    """
    arr = numpy.array([rlz.weight['default'] for rlz in realizations])
    return arr


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


MAXSITES = 1000
CORRELATION_MATRIX_TOO_LARGE = '''\
You have a correlation matrix which is too large: %%d sites > %d.
To avoid that, set a proper `region_grid_spacing` so that your exposure
takes less sites.''' % MAXSITES


class BaseCalculator(metaclass=abc.ABCMeta):
    """
    Abstract base class for all calculators.

    :param oqparam: OqParam object
    :param monitor: monitor object
    :param calc_id: numeric calculation ID
    """
    precalc = None
    accept_precalc = []
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

    def check_precalc(self, precalc_mode):
        """
        Defensive programming against users providing an incorrect
        pre-calculation ID (with ``--hazard-calculation-id``).

        :param precalc_mode:
            calculation_mode of the previous calculation
        """
        calc_mode = self.oqparam.calculation_mode
        ok_mode = self.accept_precalc
        if calc_mode != precalc_mode and precalc_mode not in ok_mode:
            raise InvalidCalculationID(
                'In order to run a calculation of kind %r, '
                'you need to provide a calculation of kind %r, '
                'but you provided a %r instead' %
                (calc_mode, ok_mode, precalc_mode))

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
                        logging.warning('', exc_info=True)

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
        has_hcurves = ('hcurves-stats' in self.datastore or
                       'hcurves-rlzs' in self.datastore)
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
            try:
                self.exported[ekey] = fnames = exp(ekey, self.datastore)
            except Exception as exc:
                fnames = []
                logging.error('Could not export %s: %s', ekey, exc)
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
    def block_splitter(self, sources, weight=get_weight, key=lambda src: 1):
        """
        :param sources: a list of sources
        :param weight: a weight function (default .weight)
        :param key: None or 'src_group_id'
        :returns: an iterator over blocks of sources
        """
        ct = self.oqparam.concurrent_tasks or 1
        maxweight = self.csm.get_maxweight(weight, ct, source.MINWEIGHT)
        if not hasattr(self, 'logged'):
            if maxweight == source.MINWEIGHT:
                logging.info('Using minweight=%d', source.MINWEIGHT)
            else:
                logging.info('Using maxweight=%d', maxweight)
            self.logged = True
        return general.block_splitter(sources, maxweight, weight, key)

    @general.cached_property
    def src_filter(self):
        """
        :returns: a SourceFilter/UcerfFilter
        """
        oq = self.oqparam
        self.hdf5cache = self.datastore.hdf5cache()
        sitecol = self.sitecol.complete if self.sitecol else None
        if 'ucerf' in oq.calculation_mode:
            return UcerfFilter(sitecol, oq.maximum_distance, self.hdf5cache)
        return SourceFilter(sitecol, oq.maximum_distance, self.hdf5cache)

    @property
    def E(self):
        """
        :returns: the number of stored events
        """
        try:
            return len(self.datastore['events'])
        except KeyError:
            return 0

    @property
    def N(self):
        """
        :returns: the total number of sites
        """
        if hasattr(self, 'sitecol'):
            return len(self.sitecol.complete) if self.sitecol else None
        return len(self.datastore['sitecol/array'])

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
        if ('source_model_logic_tree' in oq.inputs and
                oq.hazard_calculation_id is None):
            self.csm = readinput.get_composite_source_model(
                oq, self.monitor(), srcfilter=self.src_filter)
        self.init()  # do this at the end of pre-execute

    def save_multi_peril(self):
        """Defined in MultiRiskCalculator"""

    def pre_execute(self):
        """
        Check if there is a previous calculation ID.
        If yes, read the inputs by retrieving the previous calculation;
        if not, read the inputs directly.
        """
        oq = self.oqparam
        if 'gmfs' in oq.inputs or 'multi_peril' in oq.inputs:
            # read hazard from files
            assert not oq.hazard_calculation_id, (
                'You cannot use --hc together with gmfs_file')
            self.read_inputs()
            if 'gmfs' in oq.inputs:
                save_gmfs(self)
            else:
                self.save_multi_peril()
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
            parent = util.read(oq.hazard_calculation_id)
            self.check_precalc(parent['oqparam'].calculation_mode)
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
            missing_imts = set(oq.risk_imtls) - set(oqp.imtls)
            if missing_imts:
                raise ValueError(
                    'The parent calculation is missing the IMT(s) %s' %
                    ', '.join(missing_imts))
        elif self.__class__.precalc:
            calc = calculators[self.__class__.precalc](
                self.oqparam, self.datastore.calc_id)
            calc.run()
            self.param = calc.param
            self.sitecol = calc.sitecol
            self.assetcol = calc.assetcol
            self.riskmodel = calc.riskmodel
            if hasattr(calc, 'rlzs_assoc'):
                self.rlzs_assoc = calc.rlzs_assoc
            else:
                # this happens for instance for a scenario_damage without
                # rupture, gmfs, multi_peril
                raise InvalidFile(
                    '%(job_ini)s: missing gmfs_csv, multi_peril_csv' %
                    oq.inputs)
            if hasattr(calc, 'csm'):  # no scenario
                self.csm = calc.csm
        else:
            self.read_inputs()
        if self.riskmodel:
            self.save_riskmodel()

    def init(self):
        """
        To be overridden to initialize the datasets needed by the calculation
        """
        oq = self.oqparam
        if not oq.risk_imtls:
            if self.datastore.parent:
                oq.risk_imtls = (
                    self.datastore.parent['oqparam'].risk_imtls)
        if 'precalc' in vars(self):
            self.rlzs_assoc = self.precalc.rlzs_assoc
        elif 'csm_info' in self.datastore:
            csm_info = self.datastore['csm_info']
            if oq.hazard_calculation_id and 'gsim_logic_tree' in oq.inputs:
                # redefine the realizations by reading the weights from the
                # gsim_logic_tree_file that could be different from the parent
                csm_info.gsim_lt = logictree.GsimLogicTree(
                    oq.inputs['gsim_logic_tree'], set(csm_info.trts))
            self.rlzs_assoc = csm_info.get_rlzs_assoc()
        elif hasattr(self, 'csm'):
            self.check_floating_spinning()
            self.rlzs_assoc = self.csm.info.get_rlzs_assoc()
        else:  # build a fake; used by risk-from-file calculators
            self.datastore['csm_info'] = fake = source.CompositionInfo.fake()
            self.rlzs_assoc = fake.get_rlzs_assoc()

    @general.cached_property
    def R(self):
        """
        :returns: the number of realizations
        """
        try:
            return self.csm.info.get_num_rlzs()
        except AttributeError:  # no self.csm
            return self.datastore['csm_info'].get_num_rlzs()

    def read_exposure(self, haz_sitecol=None):  # after load_risk_model
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
                if hasattr(self, 'rup'):
                    # this is normal for the case of scenario from rupture
                    logging.info('%d assets were discarded because too far '
                                 'from the rupture; use `oq show discarded` '
                                 'to show them and `oq plot_assets` to plot '
                                 'them' % len(discarded))
                elif not self.oqparam.discard_assets:  # raise an error
                    self.datastore['sitecol'] = self.sitecol
                    self.datastore['assetcol'] = self.assetcol
                    raise RuntimeError(
                        '%d assets were discarded; use `oq show discarded` to'
                        ' show them and `oq plot_assets` to plot them' %
                        len(discarded))

        # reduce the riskmodel to the relevant taxonomies
        taxonomies = set(taxo for taxo in self.assetcol.tagcol.taxonomy
                         if taxo != '?')
        if len(self.riskmodel.taxonomies) > len(taxonomies):
            logging.info('Reducing risk model from %d to %d taxonomies',
                         len(self.riskmodel.taxonomies), len(taxonomies))
            self.riskmodel = self.riskmodel.reduce(taxonomies)
        return readinput.exposure

    def load_riskmodel(self):
        # to be called before read_exposure
        # NB: this is called even if there is no risk model
        """
        Read the risk model and set the attribute .riskmodel.
        The riskmodel can be empty for hazard calculations.
        Save the loss ratios (if any) in the datastore.
        """
        logging.info('Reading the risk model if present')
        self.riskmodel = readinput.get_risk_model(self.oqparam)
        if not self.riskmodel:
            parent = self.datastore.parent
            if 'risk_model' in parent:
                self.riskmodel = riskinput.CompositeRiskModel.read(parent)
            return
        if self.oqparam.ground_motion_fields and not self.oqparam.imtls:
            raise InvalidFile('No intensity_measure_types specified in %s' %
                              self.oqparam.inputs['job_ini'])
        self.save_params()  # re-save oqparam

    def save_riskmodel(self):
        """
        Save the risk models in the datastore
        """
        self.datastore['risk_model'] = rm = self.riskmodel
        self.datastore['taxonomy_mapping'] = self.riskmodel.tmap
        attrs = self.datastore.getitem('risk_model').attrs
        attrs['min_iml'] = hdf5.array_of_vstr(sorted(rm.min_iml.items()))
        self.datastore.set_nbytes('risk_model')

    def _read_risk_data(self):
        # read the exposure (if any), the risk model (if any) and then the
        # site collection, possibly extracted from the exposure.
        oq = self.oqparam
        self.load_riskmodel()  # must be called first

        if oq.hazard_calculation_id:
            with util.read(oq.hazard_calculation_id) as dstore:
                haz_sitecol = dstore['sitecol'].complete
        else:
            haz_sitecol = readinput.get_site_collection(oq)
            if hasattr(self, 'rup'):
                # for scenario we reduce the site collection to the sites
                # within the maximum distance from the rupture
                haz_sitecol, _dctx = self.cmaker.filter(
                    haz_sitecol, self.rup)
                haz_sitecol.make_complete()

            if 'site_model' in oq.inputs:
                self.datastore['site_model'] = readinput.get_site_model(oq)

        oq_hazard = (self.datastore.parent['oqparam']
                     if self.datastore.parent else None)
        if 'exposure' in oq.inputs:
            exposure = self.read_exposure(haz_sitecol)
            self.datastore['assetcol'] = self.assetcol
            self.datastore['assetcol/num_taxonomies'] = (
                self.assetcol.num_taxonomies_by_site())
            if hasattr(readinput.exposure, 'exposures'):
                self.datastore['assetcol/exposures'] = (
                    numpy.array(exposure.exposures, hdf5.vstr))
        elif 'assetcol' in self.datastore.parent:
            assetcol = self.datastore.parent['assetcol']
            if oq.region:
                region = wkt.loads(oq.region)
                self.sitecol = haz_sitecol.within(region)
            if oq.shakemap_id or 'shakemap' in oq.inputs:
                self.sitecol, self.assetcol = self.read_shakemap(
                    haz_sitecol, assetcol)
                self.datastore['assetcol'] = self.assetcol
                logging.info('Extracted %d/%d assets',
                             len(self.assetcol), len(assetcol))
                nsites = len(self.sitecol)
                if (oq.spatial_correlation != 'no' and
                        nsites > MAXSITES):  # hard-coded, heuristic
                    raise ValueError(CORRELATION_MATRIX_TOO_LARGE % nsites)
            elif hasattr(self, 'sitecol') and general.not_equal(
                    self.sitecol.sids, haz_sitecol.sids):
                self.assetcol = assetcol.reduce(self.sitecol)
                self.datastore['assetcol'] = self.assetcol
                self.datastore['assetcol/num_taxonomies'] = (
                    self.assetcol.num_taxonomies_by_site())
                logging.info('Extracted %d/%d assets',
                             len(self.assetcol), len(assetcol))
            else:
                self.assetcol = assetcol
        else:  # no exposure
            self.sitecol = haz_sitecol
            if self.sitecol:
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

        if oq.job_type == 'risk':
            taxonomies = set(taxo for taxo in self.assetcol.tagcol.taxonomy
                             if taxo != '?')

            # check that we are covering all the taxonomies in the exposure
            missing = taxonomies - set(self.riskmodel.taxonomies)
            if self.riskmodel and missing:
                raise RuntimeError('The exposure contains the taxonomies %s '
                                   'which are not in the risk model' % missing)

            # same check for the consequence models, if any
            if any(key.endswith('_consequence') for key in oq.inputs):
                for taxonomy in taxonomies:
                    cfs = self.riskmodel[taxonomy].consequence_functions
                    if not cfs:
                        raise ValueError(
                            'Missing consequenceFunctions for %s' % taxonomy)

        if hasattr(self, 'sitecol') and self.sitecol:
            self.datastore['sitecol'] = self.sitecol.complete
        # used in the risk calculators
        self.param = dict(individual_curves=oq.individual_curves,
                          avg_losses=oq.avg_losses)

        # store the `exposed_value` if there is an exposure
        if 'exposed_value' not in set(self.datastore) and hasattr(
                self, 'assetcol'):
            self.datastore['exposed_value'] = self.assetcol.agg_value(
                *oq.aggregate_by)

    def store_rlz_info(self, eff_ruptures=None):
        """
        Save info about the composite source model inside the csm_info dataset
        """
        if hasattr(self, 'csm'):  # no scenario
            self.csm.info.update_eff_ruptures(eff_ruptures)
            self.rlzs_assoc = self.csm.info.get_rlzs_assoc(
                self.oqparam.sm_lt_path)
            if not self.rlzs_assoc:
                raise RuntimeError('Empty logic tree: too much filtering?')
            self.datastore['csm_info'] = self.csm.info
        R = len(self.rlzs_assoc.realizations)
        logging.info('There are %d realization(s)', R)
        if self.oqparam.imtls:
            self.datastore['weights'] = arr = build_weights(
                self.rlzs_assoc.realizations, self.oqparam.imt_dt())
            self.datastore.set_attrs('weights', nbytes=arr.nbytes)
            if hasattr(self, 'hdf5cache'):  # no scenario
                with hdf5.File(self.hdf5cache, 'r+') as cache:
                    cache['weights'] = arr
        if 'event_based' in self.oqparam.calculation_mode and R >= TWO16:
            # rlzi is 16 bit integer in the GMFs, so there is hard limit or R
            raise ValueError(
                'The logic tree has %d realizations, the maximum '
                'is %d' % (R, TWO16))
        elif R > 10000:
            logging.warning(
                'The logic tree has %d realizations(!), please consider '
                'sampling it', R)
        self.datastore.flush()

    def store_source_info(self, calc_times):
        """
        Save (weight, num_sites, calc_time) inside the source_info dataset
        """
        if calc_times:
            source_info = self.datastore['source_info']
            arr = numpy.zeros((len(source_info), 2), F32)
            ids, vals = zip(*sorted(calc_times.items()))
            arr[numpy.array(ids)] = vals
            source_info['weight'] += arr[:, 0]
            source_info['calc_time'] += arr[:, 1]

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
            logging.warning('There are risk functions for not available IMTs '
                            'which will be ignored: %s' % extra)

        logging.info('Getting/reducing shakemap')
        with self.monitor('getting/reducing shakemap'):
            smap = oq.shakemap_id if oq.shakemap_id else numpy.load(
                oq.inputs['shakemap'])
            sitecol, shakemap, discarded = get_sitecol_shakemap(
                smap, oq.imtls, haz_sitecol,
                oq.asset_hazard_distance['default'],
                oq.discard_assets)
            if len(discarded):
                self.datastore['discarded'] = discarded
            assetcol = assetcol.reduce_also(sitecol)

        logging.info('Building GMFs')
        with self.monitor('building/saving GMFs'):
            imts, gmfs = to_gmfs(
                shakemap, oq.spatial_correlation, oq.cross_correlation,
                oq.site_effects, oq.truncation_level, E, oq.random_seed,
                oq.imtls)
            save_gmf_data(self.datastore, sitecol, gmfs, imts)
        return sitecol, assetcol

    def build_riskinputs(self, kind):
        """
        :param kind:
            kind of hazard getter, can be 'poe' or 'gmf'
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
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy
        with self.monitor('building riskinputs', autoflush=True):
            riskinputs = list(self._gen_riskinputs(kind))
        assert riskinputs
        logging.info('Built %d risk inputs', len(riskinputs))
        return riskinputs

    def get_getter(self, kind, sid):
        """
        :param kind: 'poe' or 'gmf'
        :param sid: a site ID
        :returns: a PmapGetter or GmfDataGetter
        """
        hdf5cache = getattr(self, 'hdf5cache', None)
        if hdf5cache:
            dstore = hdf5cache
        elif (self.oqparam.hazard_calculation_id and
              'gmf_data' not in self.datastore):
            # 'gmf_data' in self.datastore happens for ShakeMap calculations
            self.datastore.parent.close()  # make sure it is closed
            dstore = self.datastore.parent
        else:
            dstore = self.datastore
        if kind == 'poe':  # hcurves, shape (R, N)
            getter = getters.PmapGetter(dstore, self.rlzs_assoc, [sid])
        else:  # gmf
            getter = getters.GmfDataGetter(dstore, [sid], self.R)
        if dstore is self.datastore:
            getter.init()
        return getter

    def _gen_riskinputs(self, kind):
        rinfo_dt = numpy.dtype([('sid', U16), ('num_assets', U16)])
        rinfo = []
        assets_by_site = self.assetcol.assets_by_site()
        for sid, assets in enumerate(assets_by_site):
            if len(assets) == 0:
                continue
            getter = self.get_getter(kind, sid)
            for block in general.block_splitter(
                    assets, self.oqparam.assets_per_site_limit):
                yield riskinput.RiskInput(getter, numpy.array(block))
            rinfo.append((sid, len(block)))
            if len(block) >= TWO16:
                logging.error('There are %d assets on site #%d!',
                              len(block), sid)
        self.datastore['riskinput_info'] = numpy.array(rinfo, rinfo_dt)

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


def get_gmv_data(sids, gmfs, events):
    """
    Convert an array of shape (N, E, M) into an array of type gmv_data_dt
    """
    N, E, M = gmfs.shape
    gmv_data_dt = numpy.dtype(
        [('rlzi', U16), ('sid', U32), ('eid', U64), ('gmv', (F32, (M,)))])
    # NB: ordering of the loops: first site, then event
    lst = [(event['rlz'], sids[s], ei, gmfs[s, ei])
           for s in numpy.arange(N, dtype=U32)
           for ei, event in enumerate(events)]
    return numpy.array(lst, gmv_data_dt)


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
        eids = import_gmfs(
            dstore, oq.inputs['gmfs'], calculator.sitecol.complete.sids)
    else:  # XML
        eids, gmfs = readinput.eids, readinput.gmfs
    E = len(eids)
    events = numpy.zeros(E, rupture.events_dt)
    events['id'] = eids
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
        N, E, M = gmfs.shape
        save_gmf_data(dstore, haz_sitecol, gmfs[haz_sitecol.sids],
                      oq.imtls, events)


def save_gmf_data(dstore, sitecol, gmfs, imts, events=()):
    """
    :param dstore: a :class:`openquake.baselib.datastore.DataStore` instance
    :param sitecol: a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param gmfs: an array of shape (N, E, M)
    :param imts: a list of IMT strings
    :param events: E event IDs or the empty tuple
    """
    if len(events) == 0:
        E = gmfs.shape[1]
        events = numpy.zeros(E, rupture.events_dt)
        events['id'] = numpy.arange(E, dtype=U64)
    dstore['events'] = events
    offset = 0
    gmfa = get_gmv_data(sitecol.sids, gmfs, events)
    dstore['gmf_data/data'] = gmfa
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


def get_idxs(data, eid2idx):
    """
    Convert from event IDs to event indices.

    :param data: an array with a field eid
    :param eid2idx: a dictionary eid -> idx
    :returns: the array of event indices
    """
    uniq, inv = numpy.unique(data['eid'], return_inverse=True)
    idxs = numpy.array([eid2idx[eid] for eid in uniq])[inv]
    return idxs


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
    E = len(eids)
    eid2idx = dict(zip(eids, range(E)))
    events = numpy.zeros(E, rupture.events_dt)
    events['id'] = eids
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
            gmvs = dic[sid]
            gmvs['eid'] = get_idxs(gmvs, eid2idx)
            gmvs['rlzi'] = 0   # effectively there is only 1 realization
            dstore.extend('gmf_data/data', gmvs)
    dstore['gmf_data/indices'] = numpy.array(lst, U32)
    dstore['gmf_data/imts'] = ' '.join(imts)
    sig_eps_dt = [('eid', U64), ('sig', (F32, n_imts)), ('eps', (F32, n_imts))]
    dstore['gmf_data/sigma_epsilon'] = numpy.zeros(0, sig_eps_dt)
    dstore['weights'] = numpy.ones(1)
    return eids
