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
import itertools
import traceback
from datetime import datetime
from shapely import wkt
import numpy

from openquake.baselib import (
    general, hdf5, datastore, __version__ as engine_version)
from openquake.baselib import parallel
from openquake.baselib.performance import Monitor, init_performance
from openquake.hazardlib import InvalidFile
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.source import rupture
from openquake.hazardlib.shakemap import get_sitecol_shakemap, to_gmfs
from openquake.risklib import riskinput, riskmodels
from openquake.commonlib import readinput, logictree, source, calc, util
from openquake.calculators.ucerf_base import UcerfFilter
from openquake.calculators.export import export as exp
from openquake.calculators import getters, views

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_trt = operator.attrgetter('src_group_id')
get_imt = operator.attrgetter('imt')

calculators = general.CallableDict(operator.attrgetter('calculation_mode'))
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
TWO16 = 2 ** 16
TWO32 = 2 ** 32

stats_dt = numpy.dtype([('mean', F32), ('std', F32),
                        ('min', F32), ('max', F32), ('len', U16)])


# this is used for the minimum_intensity dictionaries
def consistent(dic1, dic2):
    """
    Check if two dictionaries with default are consistent:

    >>> consistent({'PGA': 0.05, 'SA(0.3)': 0.05}, {'default': 0.05})
    True
    >>> consistent({'SA(0.3)': 0.1, 'SA(0.6)': 0.05},
    ... {'default': 0.1, 'SA(0.3)': 0.1, 'SA(0.6)': 0.05})
    True
    """
    if dic1 == dic2:
        return True
    v1 = set(dic1.values())
    v2 = set(dic2.values())
    missing = set(dic2) - set(dic1) - {'default'}
    if len(v1) == 1 and len(v2) == 1 and v1 == v2:
        # {'PGA': 0.05, 'SA(0.3)': 0.05} is consistent with {'default': 0.05}
        return True
    return not missing


def get_stats(seq):
    std = numpy.nan if len(seq) == 1 else numpy.std(seq, ddof=1)
    tup = (numpy.mean(seq), std, numpy.min(seq), numpy.max(seq), len(seq))
    return numpy.array(tup, stats_dt)


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
        init_performance(self.datastore.hdf5)
        self._monitor = Monitor(
            '%s.run' % self.__class__.__name__, measuremem=True,
            h5=self.datastore)
        # NB: using h5=self.datastore.hdf5 would mean losing the performance
        # info about Calculator.run since the file will be closed later on
        self.oqparam = oqparam
        if oqparam.num_cores:
            parallel.CT = oqparam.num_cores * 2

    def monitor(self, operation='', **kw):
        """
        :returns: a new Monitor instance
        """
        mon = self._monitor(operation, h5=self.datastore.hdf5)
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
            logging.info('Checksum of the input files: %(checksum32)s', attrs)
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

    def run(self, pre_execute=True, concurrent_tasks=None, remove=True, **kw):
        """
        Run the calculation and return the exported outputs.
        """
        with self._monitor:
            self._monitor.username = kw.get('username', '')
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
                readinput.gsim_lt_cache.clear()

                # remove temporary hdf5 file, if any
                if os.path.exists(self.datastore.tempname) and remove:
                    os.remove(self.datastore.tempname)
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

    def gzip_inputs(self):
        """
        Gzipping the inputs and saving them in the datastore
        """
        logging.info('gzipping the input files')
        fnames = readinput.get_input_files(self.oqparam)
        self.datastore.store_files(fnames)

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


def check_amplification(dstore):
    """
    Make sure the amplification codes in the site collection match the
    ones in the amplification table
    """
    codeset = set(dstore['amplification']['ampcode'])
    if len(codeset) == 1:
        # there is a single amplification function, there is no need to
        # extend the sitecol with an ampcode field
        return
    codes = set(dstore['sitecol'].ampcode)
    missing = codes - codeset
    if missing:
        raise ValueError('The site collection contains references to missing '
                         'amplification functions:' + ' '.join(missing))


class HazardCalculator(BaseCalculator):
    """
    Base class for hazard calculators based on source models
    """
    def src_filter(self, filename=None):
        """
        :returns: a SourceFilter/UcerfFilter
        """
        oq = self.oqparam
        if getattr(self, 'sitecol', None):
            sitecol = self.sitecol.complete
        else:  # can happen to the ruptures-only calculator
            sitecol = None
            filename = None
        if 'ucerf' in oq.calculation_mode:
            return UcerfFilter(sitecol, oq.maximum_distance, filename)
        return SourceFilter(sitecol, oq.maximum_distance, filename)

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
        return len(self.sitecol.complete) if self.sitecol else None

    def check_overflow(self):
        """Overridden in event based"""

    def check_floating_spinning(self):
        f, s = self.csm.get_floating_spinning_factors()
        if f != 1:
            logging.info('Rupture floating factor = %s', f)
        if s != 1:
            logging.info('Rupture spinning factor = %s', s)

    def read_inputs(self):
        """
        Read risk data and sources if any
        """
        oq = self.oqparam
        self._read_risk_data()
        self.check_overflow()  # check if self.sitecol is too large
        if getattr(self, 'sitecol', None):
            # can be None for the ruptures-only calculator
            with hdf5.File(self.datastore.tempname, 'w') as tmp:
                tmp['sitecol'] = self.sitecol
        if ('source_model_logic_tree' in oq.inputs and
                oq.hazard_calculation_id is None):
            with self.monitor('composite source model', measuremem=True):
                self.csm = csm = readinput.get_composite_source_model(
                    oq, self.datastore.hdf5)
                self.csm_info = csm.info
                self.datastore['source_model_lt'] = csm.source_model_lt
                res = views.view('dupl_sources', self.datastore)
                logging.info(f'The composite source model has {res.val:_d} '
                             'ruptures')
            if res:
                logging.info(res)
        self.init()  # do this at the end of pre-execute

        if not oq.hazard_calculation_id:
            self.gzip_inputs()

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
                if not oq.inputs['gmfs'].endswith('.csv'):
                    raise NotImplementedError(
                        'Importer for %s' % oq.inputs['gmfs'])
                E = len(import_gmfs(self.datastore, oq.inputs['gmfs'],
                                    self.sitecol.complete.sids))
                if hasattr(oq, 'number_of_ground_motion_fields'):
                    if oq.number_of_ground_motion_fields != E:
                        raise RuntimeError(
                            'Expected %d ground motion fields, found %d' %
                            (oq.number_of_ground_motion_fields, E))
                else:  # set the number of GMFs from the file
                    oq.number_of_ground_motion_fields = E
            else:
                self.save_multi_peril()
            self.save_crmodel()
        elif 'hazard_curves' in oq.inputs:  # read hazard from file
            assert not oq.hazard_calculation_id, (
                'You cannot use --hc together with hazard_curves')
            haz_sitecol = readinput.get_site_collection(oq)
            self.load_crmodel()  # must be after get_site_collection
            self.read_exposure(haz_sitecol)  # define .assets_by_site
            self.datastore['poes/grp-00'] = fix_ones(readinput.pmap)
            self.datastore['sitecol'] = self.sitecol
            self.datastore['assetcol'] = self.assetcol
            self.datastore['csm_info'] = fake = source.CompositionInfo.fake()
            self.rlzs_assoc = fake.get_rlzs_assoc()
            self.datastore['rlzs_by_grp'] = self.rlzs_assoc.by_grp()
            self.save_crmodel()
        elif oq.hazard_calculation_id:
            parent = util.read(oq.hazard_calculation_id)
            self.check_precalc(parent['oqparam'].calculation_mode)
            self.datastore.parent = parent
            # copy missing parameters from the parent
            if 'concurrent_tasks' not in vars(self.oqparam):
                self.oqparam.concurrent_tasks = (
                    self.oqparam.__class__.concurrent_tasks.default)
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
            if not consistent(oqp.minimum_intensity, oq.minimum_intensity):
                raise ValueError(
                    'The parent calculation was using minimum_intensity=%s'
                    ' != %s' % (oqp.minimum_intensity, oq.minimum_intensity))
            hstats, rstats = list(oqp.hazard_stats()), list(oq.hazard_stats())
            if hstats != rstats:
                raise ValueError(
                    'The parent calculation had stats %s != %s' %
                    (hstats, rstats))
            missing_imts = set(oq.risk_imtls) - set(oqp.imtls)
            if missing_imts:
                raise ValueError(
                    'The parent calculation is missing the IMT(s) %s' %
                    ', '.join(missing_imts))
            self.save_crmodel()
        elif self.__class__.precalc:
            calc = calculators[self.__class__.precalc](
                self.oqparam, self.datastore.calc_id)
            calc.run(remove=False)
            for name in ('csm param sitecol assetcol crmodel rlzs_assoc '
                         'policy_name policy_dict csm_info').split():
                if hasattr(calc, name):
                    setattr(self, name, getattr(calc, name))
        else:
            self.read_inputs()
            self.save_crmodel()

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

    def read_exposure(self, haz_sitecol):  # after load_risk_model
        """
        Read the exposure, the risk models and update the attributes
        .sitecol, .assetcol
        """
        oq = self.oqparam
        with self.monitor('reading exposure'):
            self.sitecol, self.assetcol, discarded = (
                readinput.get_sitecol_assetcol(
                    oq, haz_sitecol, self.crmodel.loss_types))
            if len(discarded):
                self.datastore['discarded'] = discarded
                if hasattr(self, 'rup'):
                    # this is normal for the case of scenario from rupture
                    logging.info('%d assets were discarded because too far '
                                 'from the rupture; use `oq show discarded` '
                                 'to show them and `oq plot_assets` to plot '
                                 'them' % len(discarded))
                elif not oq.discard_assets:  # raise an error
                    self.datastore['sitecol'] = self.sitecol
                    self.datastore['assetcol'] = self.assetcol
                    raise RuntimeError(
                        '%d assets were discarded; use `oq show discarded` to'
                        ' show them and `oq plot_assets` to plot them' %
                        len(discarded))
        self.policy_name = ''
        self.policy_dict = {}
        if oq.inputs.get('insurance'):
            k, v = zip(*oq.inputs['insurance'].items())
            self.load_insurance_data(k, v)
        return readinput.exposure

    def load_insurance_data(self, ins_types, ins_files):
        """
        Read the insurance files and populate the policy_dict
        """
        for loss_type, fname in zip(ins_types, ins_files):
            array = hdf5.read_csv(
                fname, {'insurance_limit': float, 'deductible': float,
                        None: object}).array
            policy_name = array.dtype.names[0]
            policy_idx = getattr(self.assetcol.tagcol, policy_name + '_idx')
            insurance = numpy.zeros((len(policy_idx), 2))
            for pol, ded, lim in array[
                    [policy_name, 'deductible', 'insurance_limit']]:
                insurance[policy_idx[pol]] = ded, lim
            self.policy_dict[loss_type] = insurance
            if self.policy_name and policy_name != self.policy_name:
                raise ValueError(
                    'The file %s contains %s as policy field, but we were '
                    'expecting %s' % (fname, policy_name, self.policy_name))
            else:
                self.policy_name = policy_name

    def load_crmodel(self):
        # to be called before read_exposure
        # NB: this is called even if there is no risk model
        """
        Read the risk models and set the attribute .crmodel.
        The crmodel can be empty for hazard calculations.
        Save the loss ratios (if any) in the datastore.
        """
        logging.info('Reading the risk model if present')
        self.crmodel = readinput.get_crmodel(self.oqparam)
        if not self.crmodel:
            parent = self.datastore.parent
            if 'risk_model' in parent:
                self.crmodel = riskmodels.CompositeRiskModel.read(parent)
            return
        if self.oqparam.ground_motion_fields and not self.oqparam.imtls:
            raise InvalidFile('No intensity_measure_types specified in %s' %
                              self.oqparam.inputs['job_ini'])
        self.save_params()  # re-save oqparam

    def save_crmodel(self):
        """
        Save the risk models in the datastore
        """
        if len(self.crmodel):
            self.datastore['risk_model'] = rm = self.crmodel
            attrs = self.datastore.getitem('risk_model').attrs
            attrs['min_iml'] = hdf5.array_of_vstr(sorted(rm.min_iml.items()))

    def _read_risk_data(self):
        # read the exposure (if any), the risk model (if any) and then the
        # site collection, possibly extracted from the exposure.
        oq = self.oqparam
        self.load_crmodel()  # must be called first

        if oq.hazard_calculation_id:
            with util.read(oq.hazard_calculation_id) as dstore:
                haz_sitecol = dstore['sitecol'].complete
                if ('amplification' in oq.inputs and
                        'ampcode' not in haz_sitecol.array.dtype.names):
                    haz_sitecol.add_col('ampcode', (numpy.string_, 2))
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
            self.datastore['cost_calculator'] = exposure.cost_calculator
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
                logging.info('Extracted %d/%d assets',
                             len(self.assetcol), len(assetcol))
            else:
                self.assetcol = assetcol
        else:  # no exposure
            self.sitecol = haz_sitecol
            if self.sitecol:
                logging.info('Read N=%d hazard sites and L=%d hazard levels',
                             len(self.sitecol), len(oq.imtls.array))

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
            tmap_arr, tmap_lst = logictree.taxonomy_mapping(
                self.oqparam.inputs.get('taxonomy_mapping'),
                self.assetcol.tagcol.taxonomy)
            self.crmodel.tmap = tmap_lst
            if len(tmap_arr):
                self.datastore['taxonomy_mapping'] = tmap_arr
            taxonomies = set(taxo for items in self.crmodel.tmap
                             for taxo, weight in items if taxo != '?')
            # check that we are covering all the taxonomies in the exposure
            missing = taxonomies - set(self.crmodel.taxonomies)
            if self.crmodel and missing:
                raise RuntimeError('The exposure contains the taxonomies %s '
                                   'which are not in the risk model' % missing)
            if len(self.crmodel.taxonomies) > len(taxonomies):
                logging.info('Reducing risk model from %d to %d taxonomies',
                             len(self.crmodel.taxonomies), len(taxonomies))
                self.crmodel = self.crmodel.reduce(taxonomies)
                self.crmodel.tmap = tmap_lst
            self.crmodel.vectorize_cons_model(self.assetcol.tagcol)

        if hasattr(self, 'sitecol') and self.sitecol:
            if 'site_model' in oq.inputs:
                assoc_dist = (oq.region_grid_spacing * 1.414
                              if oq.region_grid_spacing else 5)  # Graeme's 5km
                sm = readinput.get_site_model(oq)
                self.sitecol.complete.assoc(sm, assoc_dist)
            self.datastore['sitecol'] = self.sitecol.complete

        # store amplification functions if any
        if 'amplification' in oq.inputs:
            logging.info('Reading %s', oq.inputs['amplification'])
            self.datastore['amplification'] = readinput.get_amplification(oq)
            check_amplification(self.datastore)

        # used in the risk calculators
        self.param = dict(individual_curves=oq.individual_curves,
                          avg_losses=oq.avg_losses)

        # compute exposure stats
        if hasattr(self, 'assetcol'):
            save_exposed_values(
                self.datastore, self.assetcol, oq.loss_names, oq.aggregate_by)

    def store_rlz_info(self, eff_ruptures=None):
        """
        Save info about the composite source model inside the csm_info dataset
        """
        if hasattr(self, 'csm_info'):  # no scenario
            self.csm_info.update_eff_ruptures(eff_ruptures)
            self.rlzs_assoc = self.csm_info.get_rlzs_assoc(
                self.oqparam.sm_lt_path)
            if not self.rlzs_assoc.realizations:
                raise RuntimeError('Empty logic tree: too much filtering?')

            # sanity check that eff_ruptures have been set, i.e. are not -1
            for sm in self.csm_info.source_models:
                for sg in sm.src_groups:
                    assert sg.eff_ruptures != -1, sg
            self.datastore['csm_info'] = self.csm_info

        R = len(self.rlzs_assoc.realizations)
        logging.info('There are %d realization(s)', R)
        rlzs_by_grp = self.rlzs_assoc.by_grp()

        if self.oqparam.imtls:
            self.datastore['weights'] = arr = build_weights(
                self.rlzs_assoc.realizations, self.oqparam.imt_dt())
            self.datastore.set_attrs('weights', nbytes=arr.nbytes)

        if ('event_based' in self.oqparam.calculation_mode and R >= TWO16
                or R >= TWO32):
            # rlzi is 16 bit integer in the GMFs and 32 bit in rlzs_by_grp
            raise ValueError(
                'The logic tree has too many realizations (%d), use sampling '
                'instead' % R)
        elif R > 10000:
            logging.warning(
                'The logic tree has %d realizations(!), please consider '
                'sampling it', R)

        # save a composite array with fields (grp_id, gsim_id, rlzs)
        if rlzs_by_grp:
            self.datastore['rlzs_by_grp'] = rlzs_by_grp

    def store_source_info(self, calc_times):
        """
        Save (weight, num_sites, calc_time) inside the source_info dataset
        """
        if calc_times:
            source_info = self.datastore['source_info']
            arr = numpy.zeros((len(source_info), 3), F32)
            # NB: the zip magic is needed for performance,
            # looping would be too slow
            ids, vals = zip(*calc_times.items())
            arr[numpy.array(ids)] = vals
            source_info['eff_ruptures'] += arr[:, 0]
            source_info['num_sites'] += arr[:, 1]
            source_info['calc_time'] += arr[:, 2]

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
    attributes .crmodel, .sitecol, .assetcol, .riskinputs in the
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
        logging.info('Getting/reducing shakemap')
        with self.monitor('getting/reducing shakemap'):
            # for instance for the test case_shakemap the haz_sitecol
            # has sids in range(0, 26) while sitecol.sids is
            # [8, 9, 10, 11, 13, 15, 16, 17, 18];
            # the total assetcol has 26 assets on the total sites
            # and the reduced assetcol has 9 assets on the reduced sites
            smap = oq.shakemap_id if oq.shakemap_id else numpy.load(
                oq.inputs['shakemap'])
            sitecol, shakemap, discarded = get_sitecol_shakemap(
                smap, oq.imtls, haz_sitecol,
                oq.asset_hazard_distance['default'],
                oq.discard_assets)
            if len(discarded):
                self.datastore['discarded'] = discarded
            assetcol.reduce_also(sitecol)

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
        if not hasattr(self.crmodel, 'tmap'):
            _, self.crmodel.tmap = logictree.taxonomy_mapping(
                self.oqparam.inputs.get('taxonomy_mapping'),
                self.assetcol.tagcol.taxonomy)
        with self.monitor('building riskinputs'):
            riskinputs = list(self._gen_riskinputs(kind))
        assert riskinputs
        logging.info('Built %d risk inputs', len(riskinputs))
        if self.oqparam.calculation_mode in (
                'event_based_damage', 'scenario_damage', 'scenario_risk'):
            self.datastore.swmr_on()
        return riskinputs

    def get_getter(self, kind, sid):
        """
        :param kind: 'poe' or 'gmf'
        :param sid: a site ID
        :returns: a PmapGetter or GmfDataGetter
        """
        if (self.oqparam.hazard_calculation_id and
                'gmf_data' not in self.datastore):
            # 'gmf_data' in self.datastore happens for ShakeMap calculations
            self.datastore.parent.close()  # make sure it is closed
            dstore = self.datastore.parent
        else:
            dstore = self.datastore
        if kind == 'poe':  # hcurves, shape (R, N)
            ws = [rlz.weight for rlz in self.rlzs_assoc.realizations]
            getter = getters.PmapGetter(dstore, ws, [sid])
        else:  # gmf
            getter = getters.GmfDataGetter(dstore, [sid], self.R)
            if len(dstore['gmf_data/data']) == 0:
                raise RuntimeError(
                    'There are no GMFs available: perhaps you set '
                    'ground_motion_fields=False or a large minimum_intensity')
        if (self.oqparam.calculation_mode not in
                'event_based_damage scenario_damage scenario_risk'
                and dstore is self.datastore):
            # hack to make h5py happy; I could not get this to work with
            # the SWMR mode
            getter.init()
        return getter

    def _gen_riskinputs(self, kind):
        hazard = ('gmf_data' in self.datastore or 'poes' in self.datastore or
                  'multi_peril' in self.datastore)
        if not hazard:
            raise InvalidFile('Did you forget gmfs_csv|hazard_curves_csv|'
                              'multi_peril_csv in %s?'
                              % self.oqparam.inputs['job_ini'])
        rinfo_dt = numpy.dtype([('sid', U16), ('num_assets', U16)])
        rinfo = []
        assets_by_site = self.assetcol.assets_by_site()
        for sid, assets in enumerate(assets_by_site):
            if len(assets) == 0:
                continue
            getter = self.get_getter(kind, sid)
            for block in general.block_splitter(
                    assets, self.oqparam.assets_per_site_limit):
                yield riskinput.RiskInput(sid, getter, numpy.array(block))
            rinfo.append((sid, len(block)))
            if len(block) >= TWO16:
                logging.error('There are %d assets on site #%d!',
                              len(block), sid)
        self.datastore['riskinput_info'] = numpy.array(rinfo, rinfo_dt)

    def execute(self):
        """
        Parallelize on the riskinputs and returns a dictionary of results.
        Require a `.core_task` to be defined with signature
        (riskinputs, crmodel, rlzs_assoc, monitor).
        """
        if not hasattr(self, 'riskinputs'):  # in the reportwriter
            return
        res = parallel.Starmap.apply(
            self.core_task.__func__,
            (self.riskinputs, self.crmodel, self.param, self.monitor()),
            concurrent_tasks=self.oqparam.concurrent_tasks or 1,
            weight=get_weight, h5=self.datastore.hdf5
        ).reduce(self.combine)
        return res

    def combine(self, acc, res):
        return acc + res


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
        events['id'] = numpy.arange(E, dtype=U32)
    dstore['events'] = events
    offset = 0
    # convert an array of shape (N, E, M) into an array of type gmv_data_dt
    N, E, M = gmfs.shape
    lst = [(sitecol.sids[s], ei, gmfs[s, ei])
           for s in numpy.arange(N, dtype=U32)
           for ei, event in enumerate(events)]
    gmfa = numpy.array(lst, dstore['oqparam'].gmf_data_dt())
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


def import_gmfs(dstore, fname, sids):
    """
    Import in the datastore a ground motion field CSV file.

    :param dstore: the datastore
    :param fname: the CSV file
    :param sids: the site IDs (complete)
    :returns: event_ids, num_rlzs
    """
    array = hdf5.read_csv(fname, {'sid': U32, 'eid': U32, None: F32},
                          renamedict=dict(site_id='sid', event_id='eid',
                                          rlz_id='rlzi')).array
    names = array.dtype.names
    if names[0] == 'rlzi':  # backward compatbility
        names = names[1:]  # discard the field rlzi
    imts = [name[4:] for name in names[2:]]
    oq = dstore['oqparam']
    missing = set(oq.imtls) - set(imts)
    if missing:
        raise ValueError('The calculation needs %s which is missing from %s' %
                         (', '.join(missing), fname))
    imt2idx = {imt: i for i, imt in enumerate(oq.imtls)}
    arr = numpy.zeros(len(array), oq.gmf_data_dt())
    for name in names:
        if name.startswith('gmv_'):
            try:
                m = imt2idx[name[4:]]
            except KeyError:  # the file contains more than enough IMTs
                pass
            else:
                arr['gmv'][:, m] = array[name]
        else:
            arr[name] = array[name]

    n = len(numpy.unique(array[['sid', 'eid']]))
    if n != len(array):
        raise ValueError('Duplicated site_id, event_id in %s' % fname)
    # store the events
    eids = numpy.unique(array['eid'])
    eids.sort()
    if eids[0] != 0:
        raise ValueError('The event_id must start from zero in %s' % fname)
    E = len(eids)
    events = numpy.zeros(E, rupture.events_dt)
    events['id'] = eids
    dstore['events'] = events
    # store the GMFs
    dic = general.group_array(arr, 'sid')
    lst = []
    offset = 0
    gmvlst = []
    for sid in sids:
        n = len(dic.get(sid, []))
        lst.append((offset, offset + n))
        if n:
            offset += n
            gmvs = dic[sid]
            gmvlst.append(gmvs)
    dstore['gmf_data/data'] = numpy.concatenate(gmvlst)
    dstore['gmf_data/indices'] = numpy.array(lst, U32)
    dstore['gmf_data/imts'] = ' '.join(imts)
    dstore['weights'] = numpy.ones(1)
    return eids


def save_exposed_values(dstore, assetcol, lossnames, tagnames):
    """
    Store 2^n arrays where n is the number of tagNames. For instance with
    the tags country, occupancy it stores 2^2 = 4 arrays:

    exposed_values/agg_country_occupancy  # shape (T1, T2, L)
    exposed_values/agg_country            # shape (T1, L)
    exposed_values/agg_occupancy          # shape (T2, L)
    exposed_values/agg                    # shape (L,)
    """
    aval = numpy.zeros((len(assetcol), len(lossnames)), F32)  # (A, L)
    array = assetcol.array
    for lti, lt in enumerate(lossnames):
        if lt == 'occupants':
            aval[array['ordinal'], lti] = array[lt + '_None']
        elif lt.endswith('_ins'):
            aval[array['ordinal'], lti] = array['value-' + lt[:-4]]
        elif lt in assetcol.fields:
            aval[array['ordinal'], lti] = array['value-' + lt]
    for n in range(len(tagnames) + 1, -1, -1):
        for names in itertools.combinations(tagnames, n):
            name = 'exposed_values/' + '_'.join(('agg',) + names)
            logging.info('Storing %s', name)
            dstore[name] = assetcol.aggregate_by(list(names), aval)
            attrs = dict(shape_descr=names + ('loss_name',),
                         loss_name=lossnames)
            for tagname in tagnames:
                attrs[tagname] = getattr(assetcol.tagcol, tagname)[1:]
            dstore.set_attrs(name, **attrs)
