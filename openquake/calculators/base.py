# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
import h5py
import numpy
import pandas

from openquake.baselib import (
    general, hdf5, __version__ as engine_version)
from openquake.baselib import parallel, python3compat
from openquake.baselib.performance import Monitor
from openquake.hazardlib import InvalidFile, site, stats
from openquake.hazardlib.site_amplification import Amplifier
from openquake.hazardlib.site_amplification import AmplFunction
from openquake.hazardlib.calc.filters import SourceFilter, getdefault
from openquake.hazardlib.source import rupture
from openquake.hazardlib.shakemap.maps import get_sitecol_shakemap
from openquake.hazardlib.shakemap.gmfs import to_gmfs
from openquake.risklib import riskinput, riskmodels
from openquake.commonlib import readinput, logictree, datastore
from openquake.calculators.export import export as exp
from openquake.calculators import getters

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_imt = operator.attrgetter('imt')

calculators = general.CallableDict(operator.attrgetter('calculation_mode'))
U8 = numpy.uint8
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


def build_weights(realizations):
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

    def __init__(self, oqparam, calc_id):
        self.datastore = datastore.new(calc_id, oqparam)
        self._monitor = Monitor(
            '%s.run' % self.__class__.__name__, measuremem=True,
            h5=self.datastore)
        # NB: using h5=self.datastore.hdf5 would mean losing the performance
        # info about Calculator.run since the file will be closed later on
        self.oqparam = oqparam

    def pre_checks(self):
        """
        Checks to run after the pre_execute but before the execute
        """

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
        self.datastore['oqparam'] = self.oqparam
        attrs = self.datastore['/'].attrs
        attrs['engine_version'] = engine_version
        attrs['date'] = datetime.now().isoformat()[:19]
        if 'checksum32' not in attrs:
            attrs['checksum32'] = readinput.get_checksum32(
                self.oqparam, self.datastore.hdf5)
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

    def run(self, pre_execute=True, concurrent_tasks=None, remove=True,
            shutdown=False, **kw):
        """
        Run the calculation and return the exported outputs.

        :param pre_execute: set it to False to avoid running pre_execute
        :param concurrent_tasks: set it to 0 to disable parallelization
        :param remove: set it to False to remove the hdf5cache file (if any)
        :param shutdown: set it to True to shutdown the ProcessPool
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
                if shutdown:
                    parallel.Starmap.shutdown()
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
                readinput.smlt_cache.clear()
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
        self.exported = getattr(self, 'exported', {})
        if isinstance(exports, tuple):
            fmts = exports
        elif exports:  # is a string
            fmts = exports.split(',')
        elif isinstance(self.oqparam.exports, tuple):
            fmts = self.oqparam.exports
        else:  # is a string
            fmts = self.oqparam.exports.split(',')
        keys = set(self.datastore) | {'fullreport'}
        has_hcurves = ('hcurves-stats' in self.datastore or
                       'hcurves-rlzs' in self.datastore)
        if has_hcurves:
            keys.add('hcurves')
        for fmt in fmts:
            if not fmt:
                continue
            for key in sorted(keys):  # top level keys
                if 'rlzs' in key and self.R > 1:
                    if (key[:-4] + 'stats') in self.datastore:
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

    def __repr__(self):
        return '<%s#%d>' % (self.__class__.__name__, self.datastore.calc_id)


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


def check_amplification(ampl_df, sitecol):
    """
    Make sure the amplification codes in the site collection match the
    ones in the amplification table.

    :param ampl_df: the amplification table as a pandas DataFrame
    :param sitecol: the site collection
    """
    codeset = set(ampl_df.index)
    if len(codeset) == 1:
        # there is a single amplification function, there is no need to
        # extend the sitecol with an ampcode field
        return
    codes = set(sitecol.ampcode)
    missing = codes - codeset
    if missing:
        raise ValueError('The site collection contains references to missing '
                         'amplification functions: %s' % b' '.join(missing).
                         decode('utf8'))


class HazardCalculator(BaseCalculator):
    """
    Base class for hazard calculators based on source models
    """

    def src_filter(self):
        """
        :returns: a SourceFilter
        """
        oq = self.oqparam
        if getattr(self, 'sitecol', None):
            sitecol = self.sitecol.complete
        else:  # can happen to the ruptures-only calculator
            sitecol = None
        return SourceFilter(sitecol, oq.maximum_distance)

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
        return len(self.datastore['sitecol'])

    @property
    def few_sites(self):
        """
        :returns: True if there are less than max_sites_disagg
        """
        return len(self.sitecol.complete) <= self.oqparam.max_sites_disagg

    def check_overflow(self):
        """Overridden in event based"""

    def check_floating_spinning(self):
        f, s = self.csm.get_floating_spinning_factors()
        if f != 1:
            logging.info('Rupture floating factor = %s', f)
        if s != 1:
            logging.info('Rupture spinning factor = %s', s)
        if (f * s >= 1.5 and self.oqparam.pointsource_distance is None
                and 'classical' in self.oqparam.calculation_mode):
            logging.info(
                'You are not using the pointsource_distance approximation:\n'
                'https://docs.openquake.org/oq-engine/advanced/common-mistakes.html#pointsource-distance')

    def read_inputs(self):
        """
        Read risk data and sources if any
        """
        oq = self.oqparam
        self._read_risk_data()
        self.check_overflow()  # check if self.sitecol is too large

        if ('amplification' in oq.inputs and
                oq.amplification_method == 'kernel'):
            logging.info('Reading %s', oq.inputs['amplification'])
            df = AmplFunction.read_df(oq.inputs['amplification'])
            check_amplification(df, self.sitecol)
            self.af = AmplFunction.from_dframe(df)

        if (oq.calculation_mode == 'disaggregation' and
                oq.max_sites_disagg < len(self.sitecol)):
            raise ValueError(
                'Please set max_sites_disagg=%d in %s' % (
                    len(self.sitecol), oq.inputs['job_ini']))
        if ('source_model_logic_tree' in oq.inputs and
                oq.hazard_calculation_id is None):
            with self.monitor('composite source model', measuremem=True):
                self.csm = csm = readinput.get_composite_source_model(
                    oq, self.datastore.hdf5)
                mags_by_trt = csm.get_mags_by_trt()
                oq.maximum_distance.interp(mags_by_trt)
                for trt in mags_by_trt:
                    self.datastore['source_mags/' + trt] = numpy.array(
                        mags_by_trt[trt])
                    it = list(oq.maximum_distance.ddic[trt].items())
                    if len(it) > 2:
                        md = '%s->%d, ... %s->%d, %s->%d' % (
                            it[0] + it[-2] + it[-1])
                        logging.info('max_dist %s: %s', trt, md)
                self.full_lt = csm.full_lt
        self.init()  # do this at the end of pre-execute
        self.pre_checks()

        if (not oq.hazard_calculation_id
                and oq.calculation_mode != 'preclassical'
                and not oq.save_disk_space):
            self.gzip_inputs()

        # check DEFINED_FOR_REFERENCE_VELOCITY
        if self.amplifier:
            gsim_lt = readinput.get_gsim_lt(oq)
            self.amplifier.check(self.sitecol.vs30, oq.vs30_tolerance,
                                 gsim_lt.values)

    def import_perils(self):
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
            with self.monitor('importing inputs', measuremem=True):
                self.read_inputs()
            if 'gmfs' in oq.inputs:
                self.datastore['full_lt'] = logictree.FullLogicTree.fake()
                if oq.inputs['gmfs'].endswith('.csv'):
                    eids = import_gmfs_csv(self.datastore, oq,
                                           self.sitecol.complete.sids)
                elif oq.inputs['gmfs'].endswith('.hdf5'):
                    eids = import_gmfs_hdf5(self.datastore, oq)
                else:
                    raise NotImplementedError(
                        'Importer for %s' % oq.inputs['gmfs'])
                E = len(eids)
                if hasattr(oq, 'number_of_ground_motion_fields'):
                    if oq.number_of_ground_motion_fields != E:
                        raise RuntimeError(
                            'Expected %d ground motion fields, found %d' %
                            (oq.number_of_ground_motion_fields, E))
                else:  # set the number of GMFs from the file
                    oq.number_of_ground_motion_fields = E
            else:
                self.import_perils()
            self.save_crmodel()
        elif 'hazard_curves' in oq.inputs:  # read hazard from file
            assert not oq.hazard_calculation_id, (
                'You cannot use --hc together with hazard_curves')
            haz_sitecol = readinput.get_site_collection(oq)
            self.load_crmodel()  # must be after get_site_collection
            self.read_exposure(haz_sitecol)  # define .assets_by_site
            poes = fix_ones(readinput.pmap).array(len(haz_sitecol))
            self.datastore['_poes'] = poes.transpose(2, 0, 1)  # shape GNL
            self.datastore['assetcol'] = self.assetcol
            self.datastore['full_lt'] = fake = logictree.FullLogicTree.fake()
            self.datastore['rlzs_by_g'] = sum(
                fake.get_rlzs_by_grp().values(), [])
            with hdf5.File(self.datastore.tempname, 'a') as t:
                t['oqparam'] = oq
            self.realizations = fake.get_realizations()
            self.save_crmodel()
            self.datastore.swmr_on()
        elif oq.hazard_calculation_id:
            parent = datastore.read(oq.hazard_calculation_id)
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
            with self.monitor('importing inputs', measuremem=True):
                self.read_inputs()
            oqp = parent['oqparam']
            if oqp.investigation_time != oq.investigation_time:
                raise ValueError(
                    'The parent calculation was using investigation_time=%s'
                    ' != %s' % (oqp.investigation_time, oq.investigation_time))
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
            calc.from_engine = self.from_engine
            calc.pre_checks = lambda: self.__class__.pre_checks(calc)
            calc.run(remove=False)
            calc.datastore.close()
            for name in ('csm param sitecol assetcol crmodel realizations '
                         'policy_name policy_dict full_lt exported').split():
                if hasattr(calc, name):
                    setattr(self, name, getattr(calc, name))
        else:
            with self.monitor('importing inputs', measuremem=True):
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
        if 'full_lt' in self.datastore:
            full_lt = self.datastore['full_lt']
            self.realizations = full_lt.get_realizations()
            if oq.hazard_calculation_id and 'gsim_logic_tree' in oq.inputs:
                # redefine the realizations by reading the weights from the
                # gsim_logic_tree_file that could be different from the parent
                full_lt.gsim_lt = logictree.GsimLogicTree(
                    oq.inputs['gsim_logic_tree'], set(full_lt.trts))
        elif hasattr(self, 'csm'):
            self.check_floating_spinning()
            self.realizations = self.csm.full_lt.get_realizations()
        else:  # build a fake; used by risk-from-file calculators
            self.datastore['full_lt'] = fake = logictree.FullLogicTree.fake()
            self.realizations = fake.get_realizations()

    @general.cached_property
    def R(self):
        """
        :returns: the number of realizations
        """
        if self.oqparam.collect_rlzs:
            return 1
        elif 'weights' in self.datastore:
            return len(self.datastore['weights'])
        try:
            return self.csm.full_lt.get_num_rlzs()
        except AttributeError:  # no self.csm
            return self.datastore['full_lt'].get_num_rlzs()

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
            self.datastore['sitecol'] = self.sitecol
            if len(discarded):
                self.datastore['discarded'] = discarded
                if 'scenario' in oq.calculation_mode:
                    # this is normal for the case of scenario from rupture
                    logging.info('%d assets were discarded because too far '
                                 'from the rupture; use `oq show discarded` '
                                 'to show them and `oq plot_assets` to plot '
                                 'them' % len(discarded))
                elif not oq.discard_assets:  # raise an error
                    self.datastore['assetcol'] = self.assetcol
                    raise RuntimeError(
                        '%d assets were discarded; use `oq show discarded` to'
                        ' show them and `oq plot_assets` to plot them' %
                        len(discarded))
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
        oq = self.oqparam
        logging.info('Reading the risk model if present')
        self.crmodel = readinput.get_crmodel(oq)
        if not self.crmodel:
            parent = self.datastore.parent
            if 'crm' in parent:
                self.crmodel = riskmodels.CompositeRiskModel.read(parent, oq)
            return
        if oq.ground_motion_fields and not oq.imtls:
            raise InvalidFile('No intensity_measure_types specified in %s' %
                              self.oqparam.inputs['job_ini'])
        self.save_params()  # re-save oqparam

    def save_crmodel(self):
        """
        Save the risk models in the datastore
        """
        if len(self.crmodel):
            logging.info('Storing risk model')
            attrs = self.crmodel.get_attrs()
            self.datastore.create_df('crm', self.crmodel.to_dframe(),
                                     'gzip', **attrs)

    def _read_risk_data(self):
        # read the risk model (if any), the exposure (if any) and then the
        # site collection, possibly extracted from the exposure.
        oq = self.oqparam
        self.load_crmodel()  # must be called first
        if (not oq.imtls and 'shakemap' not in oq.inputs
                and oq.ground_motion_fields):
            raise InvalidFile('There are no intensity measure types in %s' %
                              oq.inputs['job_ini'])
        if oq.hazard_calculation_id:
            with datastore.read(oq.hazard_calculation_id) as dstore:
                haz_sitecol = dstore['sitecol'].complete
                if ('amplification' in oq.inputs and
                        'ampcode' not in haz_sitecol.array.dtype.names):
                    haz_sitecol.add_col('ampcode', site.ampcode_dt)
        else:
            if 'gmfs' in oq.inputs and oq.inputs['gmfs'].endswith('.hdf5'):
                with hdf5.File(oq.inputs['gmfs']) as f:
                    haz_sitecol = f['sitecol']
            else:
                haz_sitecol = readinput.get_site_collection(oq, self.datastore)
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
        self.policy_name = ''
        self.policy_dict = {}
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
            if oq.shakemap_id or 'shakemap' in oq.inputs or oq.shakemap_uri:
                self.sitecol, self.assetcol = read_shakemap(
                    self, haz_sitecol, assetcol)
                self.datastore['sitecol'] = self.sitecol
                self.datastore['assetcol'] = self.assetcol
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
            if self.sitecol and oq.imtls:
                logging.info('Read N=%d hazard sites and L=%d hazard levels',
                             len(self.sitecol), oq.imtls.size)

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
            tmap = readinput.taxonomy_mapping(
                self.oqparam, self.assetcol.tagcol.taxonomy)
            self.crmodel.tmap = tmap
            taxonomies = set()
            for ln in oq.loss_names:
                for items in self.crmodel.tmap[ln]:
                    for taxo, weight in items:
                        if taxo != '?':
                            taxonomies.add(taxo)
            # check that we are covering all the taxonomies in the exposure
            missing = taxonomies - set(self.crmodel.taxonomies)
            if self.crmodel and missing:
                raise RuntimeError('The exposure contains the taxonomies %s '
                                   'which are not in the risk model' % missing)
            if len(self.crmodel.taxonomies) > len(taxonomies):
                logging.info('Reducing risk model from %d to %d taxonomies',
                             len(self.crmodel.taxonomies), len(taxonomies))
                self.crmodel = self.crmodel.reduce(taxonomies)
                self.crmodel.tmap = tmap

        if hasattr(self, 'sitecol') and self.sitecol:
            if 'site_model' in oq.inputs:
                assoc_dist = (oq.region_grid_spacing * 1.414
                              if oq.region_grid_spacing else 5)  # Graeme's 5km
                sm = readinput.get_site_model(oq)
                self.sitecol.complete.assoc(sm, assoc_dist)
                self.datastore['sitecol'] = self.sitecol

        # store amplification functions if any
        self.af = None
        if 'amplification' in oq.inputs:
            logging.info('Reading %s', oq.inputs['amplification'])
            df = AmplFunction.read_df(oq.inputs['amplification'])
            check_amplification(df, self.sitecol)
            if oq.amplification_method == 'kernel':
                # TODO: need to add additional checks on the main calculation
                # methodology since the kernel method is currently tested only
                # for classical PSHA
                self.af = AmplFunction.from_dframe(df)
                self.amplifier = None
            else:
                self.amplifier = Amplifier(oq.imtls, df, oq.soil_intensities)
        else:
            self.amplifier = None

        # manage secondary perils
        sec_perils = oq.get_sec_perils()
        for sp in sec_perils:
            sp.prepare(self.sitecol)  # add columns as needed

        mal = {lt: getdefault(oq.minimum_asset_loss, lt)
               for lt in oq.loss_names}
        if mal:
            logging.info('minimum_asset_loss=%s', mal)
        self.param = dict(individual_curves=oq.individual_curves,
                          ps_grid_spacing=oq.ps_grid_spacing,
                          minimum_distance=oq.minimum_distance,
                          collapse_level=int(oq.collapse_level),
                          split_sources=oq.split_sources,
                          avg_losses=oq.avg_losses,
                          amplifier=self.amplifier,
                          sec_perils=sec_perils,
                          ses_seed=oq.ses_seed)
        # compute exposure stats
        if hasattr(self, 'assetcol'):
            save_agg_values(
                self.datastore, self.assetcol, oq.loss_names, oq.aggregate_by)

    def store_rlz_info(self, rel_ruptures):
        """
        Save info about the composite source model inside the full_lt dataset

        :param rel_ruptures: dictionary TRT -> number of relevant ruptures
        """
        oq = self.oqparam
        if hasattr(self, 'full_lt'):  # no scenario
            self.realizations = self.full_lt.get_realizations()
            if not self.realizations:
                raise RuntimeError('Empty logic tree: too much filtering?')
            self.datastore['full_lt'] = self.full_lt
        else:  # scenario
            self.full_lt = self.datastore['full_lt']

        R = self.R
        logging.info('There are %d realization(s)', R)

        self.datastore['weights'] = arr = build_weights(self.realizations)
        self.datastore.set_attrs('weights', nbytes=arr.nbytes)

        if ('event_based' in oq.calculation_mode and R >= TWO16
                or R >= TWO32):
            raise ValueError(
                'The logic tree has too many realizations (%d), use sampling '
                'instead' % R)
        elif R > 10000:
            logging.warning(
                'The logic tree has %d realizations(!), please consider '
                'sampling it', R)
        if rel_ruptures:
            self.check_discardable(rel_ruptures)

    def check_discardable(self, rel_ruptures):
        """
        Check if logic tree reduction is possible
        """
        n = len(self.full_lt.sm_rlzs)
        keep_trts = set()
        nrups = []
        for grp_id, trt_smrs in enumerate(self.datastore['trt_smrs']):
            trti, smrs = numpy.divmod(trt_smrs, n)
            trt = self.full_lt.trts[trti[0]]
            nr = rel_ruptures.get(grp_id, 0)
            nrups.append(nr)
            if nr:
                keep_trts.add(trt)
        self.datastore['est_rups_by_grp'] = U32(nrups)
        discard_trts = set(self.full_lt.trts) - keep_trts
        if discard_trts:
            msg = ('No sources for some TRTs: you should set\n'
                   'discard_trts = %s\nin %s') % (
                       ', '.join(discard_trts), self.oqparam.inputs['job_ini'])
            logging.warning(msg)

    def store_source_info(self, calc_times, nsites=False):
        """
        Save (eff_ruptures, num_sites, calc_time) inside the source_info
        """
        self.csm.update_source_info(calc_times, nsites)
        recs = [tuple(row) for row in self.csm.source_info.values()]
        hdf5.extend(self.datastore['source_info'],
                    numpy.array(recs, readinput.source_info_dt))
        return [rec[0] for rec in recs]  # return source_ids

    def post_process(self):
        """For compatibility with the engine"""


class RiskCalculator(HazardCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .crmodel, .sitecol, .assetcol, .riskinputs in the
    pre_execute phase.
    """

    def build_riskinputs(self, kind):
        """
        :param kind:
            kind of hazard getter, can be 'poe' or 'gmf'
        :returns:
            a list of RiskInputs objects, sorted by IMT.
        """
        logging.info('Building risk inputs from %d realization(s)', self.R)
        imtset = set(self.oqparam.imtls) | set(self.oqparam.get_sec_imts())
        if not set(self.oqparam.risk_imtls) & imtset:
            rsk = ', '.join(self.oqparam.risk_imtls)
            haz = ', '.join(imtset)
            raise ValueError('The IMTs in the risk models (%s) are disjoint '
                             "from the IMTs in the hazard (%s)" % (rsk, haz))
        if not hasattr(self.crmodel, 'tmap'):
            self.crmodel.tmap = readinput.taxonomy_mapping(
                self.oqparam, self.assetcol.tagcol.taxonomy)
        with self.monitor('building riskinputs'):
            if self.oqparam.hazard_calculation_id:
                dstore = self.datastore.parent
            else:
                dstore = self.datastore
            riskinputs = getattr(self, '_gen_riskinputs_' + kind)(dstore)
        assert riskinputs
        if all(isinstance(ri.hazard_getter, getters.ZeroGetter)
               for ri in riskinputs):
            raise RuntimeError(f'the {kind}s are all zeros on the assets')
        logging.info('Built %d risk inputs', len(riskinputs))
        self.acc = None
        return riskinputs

    def _gen_riskinputs_gmf(self, dstore):
        out = []
        if 'gmf_data' not in dstore:  # needed for case_shakemap
            dstore.close()
            dstore = self.datastore
        if 'gmf_data' not in dstore:
            raise InvalidFile('No gmf_data: did you forget gmfs_csv in %s?'
                              % self.oqparam.inputs['job_ini'])
        rlzs = dstore['events']['rlz_id']
        gmf_df = dstore.read_df('gmf_data', 'sid')
        logging.info('Events per site: ~%d', len(gmf_df) / self.N)
        logging.info('Grouping the GMFs by site ID')
        by_sid = dict(list(gmf_df.groupby(gmf_df.index)))
        asset_df = self.assetcol.to_dframe('site_id')
        for sid, assets in asset_df.groupby(asset_df.index):
            try:
                df = by_sid[sid]
            except KeyError:
                getter = getters.ZeroGetter(
                    sid, rlzs, self.R, gmf_df.columns[1:])  # strip eid
            else:
                df['rlz'] = rlzs[df.eid.to_numpy()]
                getter = getters.GmfDataGetter(sid, df, len(rlzs), self.R)
            if len(dstore['gmf_data/eid']) == 0:
                raise RuntimeError(
                    'There are no GMFs available: perhaps you did set '
                    'ground_motion_fields=False or a large minimum_intensity')
            out.append(riskinput.RiskInput(getter, assets))
        return out

    def _gen_riskinputs_poe(self, dstore):
        out = []
        asset_df = self.assetcol.to_dframe('site_id')
        for sid, assets in asset_df.groupby(asset_df.index):
            # hcurves, shape (R, N)
            ws = [rlz.weight for rlz in self.realizations]
            getter = getters.PmapGetter(dstore, ws, [sid], self.oqparam.imtls)
            for slc in general.split_in_slices(
                    len(assets), self.oqparam.assets_per_site_limit):
                out.append(riskinput.RiskInput(getter, assets[slc]))
            if slc.stop - slc.start >= TWO16:
                logging.error('There are %d assets on site #%d!',
                              slc.stop - slc.start, sid)
        return out

    def execute(self):
        """
        Parallelize on the riskinputs and returns a dictionary of results.
        Require a `.core_task` to be defined with signature
        (riskinputs, crmodel, param, monitor).
        """
        if not hasattr(self, 'riskinputs'):  # in the reportwriter
            return
        ct = self.oqparam.concurrent_tasks or 1
        maxw = sum(ri.weight for ri in self.riskinputs) / ct
        self.datastore.swmr_on()
        smap = parallel.Starmap(
            self.core_task.__func__, h5=self.datastore.hdf5)
        smap.monitor.save('crmodel', self.crmodel)
        for block in general.block_splitter(
                self.riskinputs, maxw, get_weight, sort=True):
            for ri in block:
                # we must use eager reading for performance reasons:
                # concurrent reading on the workers would be extra-slow;
                # also, I could not get lazy reading to work with
                # the SWMR mode for event_based_risk
                if not isinstance(ri.hazard_getter, getters.PmapGetter):
                    ri.hazard_getter.init()
            smap.submit((block, self.param))
        return smap.reduce(self.combine, self.acc)

    def combine(self, acc, res):
        """
        Combine the outputs assuming acc and res are dictionaries
        """
        if res is None:
            raise MemoryError('You ran out of memory!')
        return acc + res


def import_gmfs_csv(dstore, oqparam, sids):
    """
    Import in the datastore a ground motion field CSV file.

    :param dstore: the datastore
    :param oqparam: an OqParam instance
    :param sids: the complete site IDs
    :returns: event_ids
    """
    fname = oqparam.inputs['gmfs']
    array = hdf5.read_csv(fname, {'sid': U32, 'eid': U32, None: F32},
                          renamedict=dict(site_id='sid', event_id='eid',
                                          rlz_id='rlzi')).array
    names = array.dtype.names  # rlz_id, sid, ...
    if names[0] == 'rlzi':  # backward compatibility
        names = names[1:]  # discard the field rlzi
    imts = [name.lstrip('gmv_') for name in names[2:]]
    oqparam.hazard_imtls = {imt: [0] for imt in imts}
    missing = set(oqparam.imtls) - set(imts)
    if missing:
        raise ValueError('The calculation needs %s which is missing from %s' %
                         (', '.join(missing), fname))
    imt2idx = {imt: i for i, imt in enumerate(oqparam.imtls)}
    arr = numpy.zeros(len(array), oqparam.gmf_data_dt())
    for name in names:
        if name.startswith('gmv_'):
            try:
                m = imt2idx[name[4:]]
            except KeyError:  # the file contains more than enough IMTs
                pass
            else:
                arr[f'gmv_{m}'][:] = array[name]
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
    logging.info('Storing %d events, all relevant', E)
    dstore['events'] = events
    # store the GMFs
    dic = general.group_array(arr, 'sid')
    offset = 0
    gmvlst = []
    for sid in sids:
        n = len(dic.get(sid, []))
        if n:
            offset += n
            gmvs = dic[sid]
            gmvlst.append(gmvs)
    data = numpy.concatenate(gmvlst)
    data.sort(order='eid')
    create_gmf_data(dstore, oqparam.get_primary_imtls(),
                    oqparam.get_sec_imts(), data=data)
    dstore['weights'] = numpy.ones(1)
    return eids


def _getset_attrs(oq):
    # read effective_time, num_events and imts from oq.inputs['gmfs']
    # if the format of the file is old (v3.11) also sets the attributes
    # investigation_time and ses_per_logic_tree_path on `oq`
    with hdf5.File(oq.inputs['gmfs'], 'r') as f:
        attrs = f['gmf_data'].attrs
        etime = attrs.get('effective_time')
        num_events = attrs.get('num_events')
        if etime is None:   # engine == 3.11
            R = len(f['weights'])
            num_events = len(f['events'])
            arr = f.getitem('oqparam')
            it = arr['par_name'] == b'investigation_time'
            it = float(arr[it]['par_value'][0])
            oq.investigation_time = it
            ses = arr['par_name'] == b'ses_per_logic_tree_path'
            ses = int(arr[ses]['par_value'][0])
            oq.ses_per_logic_tree_path = ses
            etime = it * ses * R
            imts = []
            for name in arr['par_name']:
                if name.startswith(b'hazard_imtls.'):
                    imts.append(name[13:].decode('utf8'))
        else:  # engine >= 3.12
            imts = attrs['imts'].split()
    return dict(effective_time=etime, num_events=num_events, imts=imts)


def import_gmfs_hdf5(dstore, oqparam):
    """
    Import in the datastore a ground motion field HDF5 file.

    :param dstore: the datastore
    :param oqparam: an OqParam instance
    :returns: event_ids
    """
    dstore['gmf_data'] = h5py.ExternalLink(oqparam.inputs['gmfs'], "gmf_data")
    attrs = _getset_attrs(oqparam)
    oqparam.hazard_imtls = {imt: [0] for imt in attrs['imts']}

    # store the events
    E = attrs['num_events']
    events = numpy.zeros(E, rupture.events_dt)
    events['id'] = numpy.arange(E)
    rel = numpy.unique(dstore['gmf_data/eid'])
    logging.info('Storing %d events, %d relevant', E, len(rel))
    dstore['events'] = events
    dstore['weights'] = numpy.ones(1)
    return events['id']


def create_gmf_data(dstore, prim_imts, sec_imts=(), data=None):
    """
    Create and possibly populate the datasets in the gmf_data group
    """
    oq = dstore['oqparam']
    R = dstore['full_lt'].get_num_rlzs()
    M = len(prim_imts)
    n = 0 if data is None else len(data['sid'])
    items = [('sid', U32 if n == 0 else data['sid']),
             ('eid', U32 if n == 0 else data['eid'])]
    for m in range(M):
        col = f'gmv_{m}'
        items.append((col, F32 if data is None else data[col]))
    for imt in sec_imts:
        items.append((str(imt), F32 if n == 0 else data[imt]))
    if oq.investigation_time:
        eff_time = oq.investigation_time * oq.ses_per_logic_tree_path * R
    else:
        eff_time = 0
    dstore.create_df('gmf_data', items, 'gzip')
    dstore.set_attrs('gmf_data', num_events=len(dstore['events']),
                     imts=' '.join(map(str, prim_imts)),
                     effective_time=eff_time)
    if data is not None:
        df = pandas.DataFrame(dict(items))
        avg_gmf = numpy.zeros((2, n, M + len(sec_imts)), F32)
        for sid, df in df.groupby(df.sid):
            df.pop('eid')
            df.pop('sid')
            avg_gmf[:, sid] = stats.avg_std(df.to_numpy())
        dstore['avg_gmf'] = avg_gmf


def save_agg_values(dstore, assetcol, lossnames, aggby):
    """
    Store agg_keys, agg_values.
    :returns: the aggkey dictionary key -> tags
    """
    lst = []
    aggkey = assetcol.tagcol.get_aggkey(aggby)
    K = len(aggkey)
    agg_number = numpy.zeros(K + 1, U32)
    if aggby:
        logging.info('Storing %d aggregation keys', len(aggkey))
        dt = [(name + '_', U16) for name in aggby] + [
            (name, hdf5.vstr) for name in aggby]
        kvs = []
        for key, val in aggkey.items():
            val = tuple(python3compat.decode(val))
            kvs.append(key + val)
            lst.append(' '.join(val))
        dstore['agg_keys'] = numpy.array(kvs, dt)
        if aggby == ['id']:
            kids = assetcol['ordinal']
        elif aggby == ['site_id']:
            kids = assetcol['site_id']
        else:
            key2i = {key: i for i, key in enumerate(aggkey)}
            kids = [key2i[tuple(t)] for t in assetcol[aggby]]
        dstore['assetcol/kids'] = U16(kids)
        agg_number[:K] = general.fast_agg(kids, assetcol['number'], M=K)
    agg_number[K] = assetcol['number'].sum()
    dstore['agg_number'] = agg_number
    lst.append('*total*')
    if assetcol.get_value_fields():
        dstore['agg_values'] = assetcol.get_agg_values(lossnames, aggby)
        dstore.set_shape_descr(
            'agg_values', aggregation=lst, loss_type=lossnames)
    return aggkey if aggby else {}


def read_shakemap(calc, haz_sitecol, assetcol):
    """
    Enabled only if there is a shakemap_id parameter in the job.ini.
    Download, unzip, parse USGS shakemap files and build a corresponding
    set of GMFs which are then filtered with the hazard site collection
    and stored in the datastore.
    """
    oq = calc.oqparam
    E = oq.number_of_ground_motion_fields
    oq.risk_imtls = oq.imtls or calc.datastore.parent['oqparam'].imtls
    logging.info('Getting/reducing shakemap')
    with calc.monitor('getting/reducing shakemap'):
        # for instance for the test case_shakemap the haz_sitecol
        # has sids in range(0, 26) while sitecol.sids is
        # [8, 9, 10, 11, 13, 15, 16, 17, 18];
        # the total assetcol has 26 assets on the total sites
        # and the reduced assetcol has 9 assets on the reduced sites
        if oq.shakemap_id:
            uridict = {'kind': 'usgs_id', 'id': oq.shakemap_id}
        elif 'shakemap' in oq.inputs:
            uridict = {'kind': 'file_npy', 'fname': oq.inputs['shakemap']}
        else:
            uridict = oq.shakemap_uri
        sitecol, shakemap, discarded = get_sitecol_shakemap(
            uridict.pop('kind'), uridict, oq.imtls, haz_sitecol,
            oq.asset_hazard_distance['default'])
        if len(discarded):
            calc.datastore['discarded'] = discarded
        assetcol.reduce_also(sitecol)
        logging.info('Extracted %d assets', len(assetcol))

    # assemble dictionary to decide on the calculation method for the gmfs
    if 'MMI' in oq.imtls:
        # calculations with MMI should be executed
        if len(oq.imtls) == 1:
            # only MMI intensities
            if oq.spatial_correlation != 'no' or oq.cross_correlation != 'no':
                logging.warning('Calculations with MMI intensities do not '
                                'support correlation. No correlations '
                                'are applied.')

            gmf_dict = {'kind': 'mmi'}
        else:
            # there are also other intensities than MMI
            raise RuntimeError(
                'There are the following intensities in your model: %s '
                'Models mixing MMI and other intensities are not supported. '
                % ', '.join(oq.imtls.keys()))
    else:
        # no MMI intensities, calculation with or without correlation
        if oq.spatial_correlation != 'no' or oq.cross_correlation != 'no':
            # cross correlation and/or spatial correlation after S&H
            gmf_dict = {'kind': 'Silva&Horspool',
                        'spatialcorr': oq.spatial_correlation,
                        'crosscorr': oq.cross_correlation,
                        'cholesky_limit': oq.cholesky_limit}
        else:
            # no correlation required, basic calculation is faster
            gmf_dict = {'kind': 'basic'}

    logging.info('Building GMFs')
    with calc.monitor('building/saving GMFs'):
        imts, gmfs = to_gmfs(shakemap, gmf_dict, oq.site_effects,
                             oq.truncation_level, E, oq.random_seed, oq.imtls)
        N, E, M = gmfs.shape
        events = numpy.zeros(E, rupture.events_dt)
        events['id'] = numpy.arange(E, dtype=U32)
        calc.datastore['events'] = events
        # convert into an array of dtype gmv_data_dt
        lst = [(sitecol.sids[s], ei) + tuple(gmfs[s, ei])
               for ei, event in enumerate(events)
               for s in numpy.arange(N, dtype=U32)]
        oq.hazard_imtls = {str(imt): [0] for imt in imts}
        data = numpy.array(lst, oq.gmf_data_dt())
        create_gmf_data(calc.datastore, imts, data=data)
    return sitecol, assetcol


def create_risk_by_event(calc):
    """
    Created an empty risk_by_event with keys event_id, agg_id, loss_id
    and fields for damages, losses and consequences
    """
    oq = calc.oqparam
    dstore = calc.datastore
    aggkey = getattr(calc, 'aggkey', {})  # empty if not aggregate_by
    crmodel = calc.crmodel
    if 'risk' in oq.calculation_mode:
        descr = [('event_id', U32), ('agg_id', U32), ('loss_id', U8),
                 ('loss', F32), ('variance', F32)]
        dstore.create_df('risk_by_event', descr, K=len(aggkey),
                         L=len(oq.loss_names))
    else:  # damage + consequences
        dmgs = ' '.join(crmodel.damage_states[1:])
        descr = ([('event_id', U32), ('agg_id', U32), ('loss_id', U8)] +
                 [(dc, F32) for dc in crmodel.get_dmg_csq()])
        dstore.create_df('risk_by_event', descr, K=len(aggkey),
                         L=len(oq.loss_names), limit_states=dmgs)
