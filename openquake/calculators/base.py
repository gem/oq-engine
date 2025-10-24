# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
import io
import os
import sys
import abc
import pdb
import json
import time
import inspect
import logging
import operator
import traceback
import tempfile
import getpass
from datetime import datetime
from shapely import wkt
import psutil
import numpy
import pandas
from PIL import Image
import configparser
import collections

from openquake.commands.plot_assets import main as plot_assets
from openquake.baselib import general, hdf5, config
from openquake.baselib import parallel
from openquake.baselib.performance import Monitor, idx_start_stop
from openquake.hazardlib import (
    InvalidFile, geo, site, stats, logictree, source_reader)
from openquake.hazardlib.gsim_lt import GsimLogicTree
from openquake.hazardlib.site_amplification import Amplifier
from openquake.hazardlib.site_amplification import AmplFunction
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.calc.filters import SourceFilter, getdefault
from openquake.hazardlib.source import rupture
from openquake.hazardlib.shakemap.gmfs import to_gmfs
from openquake.risklib import riskinput, riskmodels, reinsurance
from openquake.commonlib import readinput, datastore, logs
from openquake.calculators.export import export as exp
from openquake.calculators import getters, postproc

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
EBDOC = ('https://docs.openquake.org/oq-engine/master/manual/user-guide/'
         'advanced/advanced-calculations.html#understanding-the-hazard')

stats_dt = numpy.dtype([('mean', F32), ('std', F32),
                        ('min', F32), ('max', F32),
                        ('len', U16)])

USER = getpass.getuser()
MB = 1024 ** 2


def get_aelo_changelog():
    dic = collections.defaultdict(list)
    c = configparser.ConfigParser()
    changelog_path = os.path.join(
        config.directory.mosaic_dir, 'aelo_changelog.ini')
    c.read(changelog_path)
    for sec in c.sections():
        dic['AELO_VERSION'].append(sec)
        for k, v in c.items(sec):
            dic[k].append(v)
    df = pandas.DataFrame(dic)
    df = df.drop(columns=['private'])
    df = df.applymap(
        lambda x: (x.replace('\n', '<br>').lstrip('<br>')
                   if isinstance(x, str) else x))
    df.columns = df.columns.str.upper()
    return df


def get_aelo_version():
    aelo_changelog = get_aelo_changelog()
    aelo_version = aelo_changelog['AELO_VERSION'][0]
    return aelo_version


def check_imtls(this, parent):
    """
    Fix the hazard_imtls of two calculations if possible
    """
    for imt, imls in this.items():
        if len(imls) != len(parent[imt]) or (
                F32(imls) != F32(parent[imt])).any():
            raise ValueError('The intensity measure levels %s are different '
                             'from the parent levels %s for %s' % (
                                 imls, parent[imt], imt))


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
    test_mode = False  # set in the tests
    is_stochastic = False  # True for scenario and event based calculators

    def __init__(self, oqparam, calc_id):
        self.oqparam = oqparam
        self.datastore = datastore.new(calc_id, oqparam)
        self.engine_version = logs.dbcmd('engine_version')
        if os.environ.get('OQ_APPLICATION_MODE') == 'AELO':
            self.aelo_version = get_aelo_version()
        # save the version in the monitor, to be used in the version
        # check in the workers
        self._monitor = Monitor(
            '%s.run' % self.__class__.__name__, measuremem=True,
            h5=self.datastore, version=self.engine_version
            if parallel.oq_distribute() == 'zmq' else None)
        self._monitor.filename = self.datastore.filename
        # NB: using h5=self.datastore.hdf5 would mean losing the performance
        # info about Calculator.run since the file will be closed later on

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
        if isinstance(self.oqparam.risk_imtls, dict):
            # always except in case_shakemap
            self.datastore['oqparam'] = self.oqparam
        attrs = self.datastore['/'].attrs
        attrs['engine_version'] = self.engine_version
        if hasattr(self, 'aelo_version'):
            attrs['aelo_version'] = self.aelo_version
        attrs['date'] = datetime.now().isoformat()[:19]
        if 'checksum32' not in attrs:
            attrs['input_size'] = size = self.oqparam.get_input_size()
            attrs['checksum32'] = check = readinput.get_checksum32(
                self.oqparam, self.datastore.hdf5)
            logging.info(f'Checksum of the inputs: {check} '
                         f'(total size {general.humansize(size)})')
            return logs.dbcmd('add_checksum', self.datastore.calc_id, check)

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

    def run(self, pre_execute=True, concurrent_tasks=None, remove=False,
            shutdown=False, **kw):
        """
        Run the calculation and return the exported outputs.

        :param pre_execute: set it to False to avoid running pre_execute
        :param concurrent_tasks: set it to 0 to disable parallelization
        :param remove: set it to False to remove the hdf5cache file (if any)
        :param shutdown: set it to True to shutdown the ProcessPool
        """
        oq = self.oqparam
        with self._monitor:
            self._monitor.username = kw.get('username', '')
            if concurrent_tasks is None:  # use the job.ini parameter
                ct = oq.concurrent_tasks
            else:  # used the parameter passed in the command-line
                ct = concurrent_tasks
            if ct == 0:  # disable distribution temporarily
                oq_distribute = os.environ.get('OQ_DISTRIBUTE')
                os.environ['OQ_DISTRIBUTE'] = 'no'
            if ct != oq.concurrent_tasks:
                # save the used concurrent_tasks
                oq.concurrent_tasks = ct
            if self.precalc is None:
                logging.info('Running %s with concurrent_tasks = %d',
                             self.__class__.__name__, ct)
            old_job_id = self.save_params(**kw)
            assert config.dbserver.cache in ('on', 'off')
            if (old_job_id and config.dbserver.cache == 'on' and
                    not self.test_mode):
                logging.info(f"Already calculated, {old_job_id=}")
                calc_id = self.datastore.calc_id
                self.datastore = datastore.read(old_job_id)
                logs.dbcmd("UPDATE job SET ds_calc_dir = ?x WHERE id=?x",
                           self.datastore.filename[:-5], calc_id)  # strip .hdf5
                expose_outputs(self.datastore, owner=USER, calc_id=calc_id)
                self.export(kw.get('exports', ''))
                return self.exported
            try:
                if pre_execute:
                    self.pre_execute()
                self.result = self.execute()
                if self.result is not None:
                    self.post_execute(self.result)
                # FIXME: this part can be called multiple times, i.e. by
                # EventBasedCalculator,EventBasedRiskCalculator
                self.post_process()
                self.export(kw.get('exports', ''))
            except Exception:
                if kw.get('pdb'):  # post-mortem debug
                    tb = sys.exc_info()[2]
                    traceback.print_tb(tb)
                    pdb.post_mortem(tb)
                else:
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

                # remove temporary hdf5 file, if any
                if os.path.exists(self.datastore.tempname):
                    if remove and oq.calculation_mode != 'preclassical':
                        # removing in preclassical with multiFaultSources
                        # would break --hc which is reading the temp file
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
        elif isinstance(self.oqparam.exports, (tuple, list)):
            fmts = self.oqparam.exports
        else:  # is a string
            fmts = self.oqparam.exports.split(',')
        keys = set(self.datastore) | {'fullreport'}
        has_hcurves = ('hcurves-stats' in self.datastore or
                       'hcurves-rlzs' in self.datastore)
        if has_hcurves:
            keys.add('hcurves')
        if 'ruptures' in self.datastore and len(self.datastore['ruptures']):
            keys.add('event_based_mfd')
        elif 'ruptures' in keys:
            keys.remove('ruptures')
        for fmt in fmts:
            if not fmt:
                continue
            if fmt == 'csv':
                self._export(('realizations', fmt))
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
    if time_event != 'avg' and time_event not in occupancy_periods:
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


def delta(vs30, vs30ref):
    """
    >>> print(round(delta(760, 800), 3))
    0.051
    """
    return 2 * (numpy.abs(vs30 - vs30ref) / (vs30 + vs30ref)).max()


class HazardCalculator(BaseCalculator):
    """
    Base class for hazard calculators based on source models
    """
    af = None
    amplifier = None

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
        :returns: the number of sites
        """
        if hasattr(self, 'sitecol'):
            return len(self.sitecol) if self.sitecol else 0
        if 'sitecol' not in self.datastore:
            return 0
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
        oq = self.oqparam
        f, s = self.csm.get_floating_spinning_factors()
        if f != 1:
            logging.info('Rupture floating factor = %s', f)
        if s != 1:
            logging.info('Rupture spinning factor = %s', s)
        if (f * s >= 1.5 and oq.no_pointsource_distance
                and ('classical' in oq.calculation_mode or
                     'disaggregation' in oq.calculation_mode)):
            logging.info(
                'You are not using the pointsource_distance approximation:\n'
                'https://docs.openquake.org/oq-engine/advanced/general.html#'
                'pointsource-distance')
        elif 'classical' in oq.calculation_mode:
            if oq.ps_grid_spacing:
                logging.info('Using pointsource_distance=%s + %d',
                             oq.pointsource_distance, int(oq.ps_grid_spacing))
            else:
                logging.info('Using pointsource_distance=%s',
                             oq.pointsource_distance)

    def check_consequences(self):
        oq = self.oqparam
        names = self.assetcol.array.dtype.names
        for consequence in self.crmodel.get_consequences():
            if consequence == 'homeless':
                if 'value-residents' not in names:
                    msg = '<field oq="residents" input="OCCUPANTS_PER_ASSET"/>'
                    fnames = '\n'.join(oq.inputs['exposure'])
                    raise InvalidFile(
                        "%s: Missing %s in the exposureFields node"
                        % (fnames, msg))

    def read_inputs(self):
        """
        Read risk data and sources if any
        """
        oq = self.oqparam
        dist = parallel.oq_distribute()
        avail = psutil.virtual_memory().available / 1024**3
        required = .25 * (1 if dist == 'no' else parallel.num_cores)
        if (dist == 'processpool' and avail < required and
                sys.platform != 'darwin'):
            # macos tells that there is no memory when there is, so we
            # must not enter in SLOW MODE there
            msg = ('Entering SLOW MODE. You have %.1f GB available, '
                   'but the engine would like at least 0.25 GB per core, '
                   'i.e. %.1f GB: '
                   'https://github.com/gem/oq-engine/blob/master/doc/faq.md'
                   ) % (avail, required)
            if oq.concurrent_tasks:
                oq.concurrent_tasks = 0
                logging.warning(msg)
            else:
                raise MemoryError('You have only %.1f GB available' % avail)
        self._read_risk1()
        self._read_risk2()
        self._read_risk3()

        if (oq.calculation_mode == 'event_based' and
                oq.ground_motion_correlation_model and
                len(self.sitecol) > oq.max_sites_correl):
            raise ValueError('You cannot use a correlation model with '
                             f'{self.N} sites [{oq.max_sites_correl=}]')
        if hasattr(self, 'assetcol'):
            self.check_consequences()
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
        if ('source_model_logic_tree' in oq.inputs or
            'source_model' in oq.inputs) and oq.hazard_calculation_id is None:
            with self.monitor('composite source model', measuremem=True):
                self.csm = csm = readinput.get_composite_source_model(
                    oq, self.datastore)
                self.datastore['full_lt'] = self.full_lt = csm.full_lt
                if oq.site_labels:
                    trts = {sg.trt for sg in csm.src_groups}
                    dic = GsimLogicTree.read_dict(
                        oq.inputs['gsim_logic_tree'], trts)
                    assert list(dic)[0] == 'Default', list(dic)
                    for label in list(dic)[1:]:
                        self.datastore['gsim_lt' + label] = dic[label]
                assert oq.mags_by_trt, 'Filtered out all magnitudes!'
                for trt in oq.mags_by_trt:
                    mags = numpy.array(oq.mags_by_trt[trt])
                    self.datastore['source_mags/' + trt] = mags
                    interp = oq.maximum_distance(trt)
                    if len(interp.x) > 2:
                        md = '%s->%d, ... %s->%d, %s->%d' % (
                            interp.x[0], interp.y[0],
                            interp.x[-2], interp.y[-2],
                            interp.x[-1], interp.y[-1])
                        logging.info('max_dist %s: %s', trt, md)
        self.init()  # do this at the end of pre-execute
        self.pre_checks()
        if 'multi_peril' in oq.inputs:
            self.gzip_inputs()

        # check DEFINED_FOR_REFERENCE_VELOCITY
        if hasattr(self, 'full_lt'):
            gsim_lt = self.full_lt.gsim_lt
        else:
            gsim_lt = readinput.get_gsim_lt(oq)
        if self.amplifier:
            self.amplifier.check(self.sitecol.vs30, oq.vs30_tolerance,
                                 gsim_lt.values)

    def import_perils(self):  # called in pre_execute
        """
        Read the hazard fields as csv files, associate them to the sites
        and create suitable `gmf_data` and `events`.
        """
        oq = self.oqparam
        [sp] = oq.get_sec_perils()
        sp.prepare(self.sitecol)
        self.datastore['events'] = numpy.zeros(1, rupture.events_dt)
        cols = [col for col in sp.data if col not in ('sid', 'eid')]
        create_gmf_data(self.datastore, [],
                        cols, sp.data, len(self.sitecol))

    def pre_execute(self):
        """
        Check if there is a previous calculation ID.
        If yes, read the inputs by retrieving the previous calculation;
        if not, read the inputs directly.
        """
        oq = self.oqparam
        self.t0 = time.time()
        if 'gmfs' in oq.inputs or 'multi_peril' in oq.inputs:
            # read hazard from files
            assert not oq.hazard_calculation_id, (
                'You cannot use --hc together with gmfs_file')
            with self.monitor('importing inputs', measuremem=True):
                self.read_inputs()
            if 'gmfs' in oq.inputs:
                self.datastore['full_lt'] = logictree.FullLogicTree.fake()
                if oq.inputs['gmfs'][0].endswith('.csv'):
                    eids = import_gmfs_csv(self.datastore, oq, self.sitecol)
                elif oq.inputs['gmfs'][0].endswith('.hdf5'):
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
            haz_sitecol = readinput.get_site_collection(
                oq, self.datastore.hdf5)
            self.load_crmodel()  # must be after get_site_collection
            self.read_exposure(haz_sitecol)  # define .assets_by_site
            _mesh, pmap = readinput.get_pmap_from_csv(
                oq, oq.inputs['hazard_curves'])
            df = (~pmap).to_dframe()
            self.datastore.create_df('_rates', df)
            slices = numpy.array([(0, 0, len(df))], getters.slice_dt)
            self.datastore['_rates/slice_by_idx'] = slices
            self.datastore['assetcol'] = self.assetcol
            self.datastore['full_lt'] = logictree.FullLogicTree.fake()
            self.datastore['trt_rlzs'] = U32([[0]])
            self.save_crmodel()
            self.datastore.swmr_on()
        elif oq.hazard_calculation_id:
            self.pre_execute_from_parent()
        elif self.__class__.precalc:
            calc = calculators[self.__class__.precalc](
                self.oqparam, self.datastore.calc_id)
            calc.from_engine = self.from_engine
            calc.run(remove=False)
            calc.datastore.close()
            for name in (
                'csm param sitecol assetcol crmodel realizations max_gb '
                'max_weight amplifier policy_df treaty_df full_lt exported '
                'trt_rlzs gids'
            ).split():
                if hasattr(calc, name):
                    setattr(self, name, getattr(calc, name))
        else:
            with self.monitor('importing inputs', measuremem=True):
                self.read_inputs()
                self.save_crmodel()
            if oq.impact and 'mmi' in oq.inputs:
                logging.info('Computing MMI-aggregated values')
                mmi_df = self.assetcol.get_mmi_values(
                    oq.aggregate_by, oq.inputs['mmi'], oq.inputs['exposure'][0])
                if len(mmi_df):
                    self.datastore.hdf5.create_df('mmi_tags', mmi_df)
                else:
                    logging.info('Missing mmi_tags, there are no assets in '
                                 'the MMI geometries provided by the ShakeMap')

    def pre_execute_from_parent(self):
        """
        Read data from the parent calculation and perform some checks
        """
        oq = self.oqparam
        parent = datastore.read(oq.hazard_calculation_id)
        oqparent = parent['oqparam']
        if 'weights' in parent:
            weights = numpy.unique(parent['weights'][:])
            if (oq.job_type == 'risk' and oq.collect_rlzs and
                    len(weights) > 1):
                raise ValueError(
                    'collect_rlzs=true can be specified only if '
                    'the realizations have identical weights')
        if oqparent.imtls and oq.calculation_mode in ('classical', 'disagg'):
            check_imtls(oq.imtls, oqparent.imtls)
        self.check_precalc(oqparent.calculation_mode)
        self.datastore.parent = parent
        # copy missing parameters from the parent
        if 'concurrent_tasks' not in vars(self.oqparam):
            self.oqparam.concurrent_tasks = (
                self.oqparam.__class__.concurrent_tasks.default)
        params = {name: value for name, value in
                  vars(parent['oqparam']).items()
                  if name not in vars(self.oqparam)
                  and name != 'ground_motion_fields'}
        if params:
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
        sec_imts = {sec_imt.split('_')[1] for sec_imt in oq.sec_imts}
        missing_imts = set(oq.risk_imtls) - sec_imts - set(oqp.imtls)
        if oqp.imtls and missing_imts:
            raise ValueError(
                'The parent calculation is missing the IMT(s) %s' %
                ', '.join(missing_imts))
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
        if hasattr(self, 'csm'):
            self.check_floating_spinning()
        elif 'full_lt' in self.datastore:
            # for instance in classical damage case_8a
            pass
        else:  # build a fake; used by risk-from-file calculators
            self.datastore['full_lt'] = logictree.FullLogicTree.fake()

    @general.cached_property
    def R(self):
        """
        :returns: the number of realizations
        """
        if self.oqparam.collect_rlzs and self.oqparam.job_type == 'risk':
            return 1
        elif 'weights' in self.datastore:
            return len(self.datastore['weights'])
        try:
            return self.csm.full_lt.get_num_paths()
        except AttributeError:  # no self.csm
            return self.datastore['full_lt'].get_num_paths()

    def read_exposure(self, haz_sitecol):  # after load_risk_model
        """
        Read the exposure, the risk models and update the attributes
        .sitecol, .assetcol
        """
        oq = self.oqparam
        inp_types = set(self.crmodel.loss_types) - {'injured', 'affectedpop'}
        self.sitecol, self.assetcol, discarded, exposure = \
            readinput.get_sitecol_assetcol(
                oq, haz_sitecol, inp_types, self.datastore)

        # this is overriding the sitecol in test_case_miriam
        self.datastore['sitecol'] = self.sitecol
        if len(discarded):
            self.datastore['discarded'] = discarded
            if 'scenario' in oq.calculation_mode:
                # this is normal for the case of scenario from rupture
                if not oq.calculation_mode.startswith('scenario'):
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
        if 'insurance' in oq.inputs:
            self.load_insurance_data(oq.inputs['insurance'].items())
        elif 'reinsurance' in oq.inputs:
            self.load_insurance_data(oq.inputs['reinsurance'].items())
        return exposure

    def load_insurance_data(self, lt_fnames):
        """
        Read the insurance files and populate the policy_df
        """
        oq = self.oqparam
        policy_acc = general.AccumDict(accum=[])
        # here is an example of policy_idx: {'?': 0, 'B': 1, 'A': 2}
        if 'reinsurance' in oq.inputs:
            loss_type = list(lt_fnames)[0][0]
            policy_df, treaty_df, fieldmap = readinput.get_reinsurance(
                oq, self.assetcol)
            treaties = set(treaty_df.id)
            assert len(treaties) == len(treaty_df), 'Not unique treaties'
            self.datastore.create_df('treaty_df', treaty_df,
                                     field_map=json.dumps(fieldmap))
            self.treaty_df = treaty_df
            # add policy_grp column
            for _, pol in policy_df.iterrows():
                grp = reinsurance.build_policy_grp(pol, treaty_df)
                policy_acc['policy_grp'].append(grp)
            for col in policy_df.columns:
                policy_acc[col].extend(policy_df[col])
            policy_acc['loss_type'].extend([loss_type] * len(policy_df))
        else:  # insurance
            policy_idx = self.assetcol.tagcol.policy_idx
            for loss_type, fname in lt_fnames:
                #  `deductible` and `insurance_limit` as fractions
                policy_df = pandas.read_csv(fname, keep_default_na=False)
                policy_df['policy'] = [
                    policy_idx[pol] for pol in policy_df.policy]
                for col in ['deductible', 'insurance_limit']:
                    reinsurance.check_fractions(
                        [col], [policy_df[col].to_numpy()], fname)
                for col in policy_df.columns:
                    policy_acc[col].extend(policy_df[col])
                policy_acc['loss_type'].extend([loss_type] * len(policy_df))
        assert policy_acc
        self.policy_df = pandas.DataFrame(policy_acc)
        self.datastore.create_df('policy', self.policy_df)

    def load_crmodel(self):
        # to be called before read_exposure
        # NB: this is called even if there is no risk model
        """
        Read the risk models and set the attribute .crmodel.
        The crmodel can be empty for hazard calculations.
        Save the loss ratios (if any) in the datastore.
        """
        oq = self.oqparam
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
            if len(self.crmodel.tmap_df):
                self.datastore.create_df('taxmap', self.crmodel.tmap_df, 'gzip')

    def _plot_assets(self):
        # called by post_risk in ARISTOTLE mode
        plt = plot_assets(self.datastore.calc_id, show=False,
                          assets_only=True)
        bio = io.BytesIO()
        plt.savefig(bio, format='png', bbox_inches='tight')
        fig_path = 'png/assets.png'
        logging.info(f'Saving {fig_path} into the datastore')
        self.datastore[fig_path] = Image.open(bio)

    def _read_no_exposure(self, haz_sitecol):
        oq = self.oqparam
        if oq.hazard_calculation_id:
            # NB: this is tested in event_based case_27 and case_31
            child = readinput.get_site_collection(oq, self.datastore.hdf5)
            assoc_dist = (oq.region_grid_spacing * 1.414
                          if oq.region_grid_spacing else 5)  # Graeme's 5km
            # keep the sites of the parent close to the sites of the child
            self.sitecol, _array, _discarded = geo.utils.assoc(
                child, haz_sitecol, assoc_dist, 'filter')
            self.datastore['sitecol'] = self.sitecol
        else:  # base case
            self.sitecol = haz_sitecol
        if self.sitecol and oq.imtls:
            logging.info('Read N=%d hazard sites and L=%d hazard levels',
                         len(self.sitecol), oq.imtls.size)
        manysites = (oq.calculation_mode=='event_based'
                     and oq.ground_motion_fields
                     and len(self.sitecol) > oq.max_sites_disagg)
        if manysites and not oq.minimum_magnitude:
            oq.raise_invalid('missing minimum_magnitude, suggested 5')
        if manysites and not oq.minimum_intensity:
            oq.raise_invalid('missing minimum_intensity, suggested .05')

    def _read_risk1(self):
        # read the risk model (if any) and then the site collection,
        # possibly extracted from the exposure
        oq = self.oqparam
        self.load_crmodel()  # must be called first
        if (not oq.imtls and 'shakemap' not in oq.inputs and 'ins_loss'
                not in oq.inputs and oq.ground_motion_fields):
            raise InvalidFile('There are no intensity measure types in %s' %
                              oq.inputs['job_ini'])
        elif oq.hazard_calculation_id:
            haz_sitecol = read_parent_sitecol(oq, self.datastore)
        else:
            if 'gmfs' in oq.inputs and oq.inputs['gmfs'][0].endswith('.hdf5'):
                haz_sitecol, _ = site.merge_sitecols(
                    oq.inputs['gmfs'], oq.mosaic_model, check_gmfs=True)
            else:
                haz_sitecol = readinput.get_site_collection(
                    oq, self.datastore.hdf5)
            if hasattr(self, 'rup'):
                # for scenario we reduce the site collection to the sites
                # within the maximum distance from the rupture
                haz_sitecol, _dctx = self.cmaker.filter(haz_sitecol, self.rup)
                haz_sitecol.make_complete()

        oq_hazard = (self.datastore.parent['oqparam']
                     if self.datastore.parent else None)
        if 'exposure' in oq.inputs and 'assetcol' not in self.datastore.parent:
            exposure = self.read_exposure(haz_sitecol)
            self.datastore['assetcol'] = self.assetcol
            self.datastore['exposure'] = exposure
            if hasattr(exposure, 'exposures'):
                self.datastore.getitem('assetcol')['exposures'] = numpy.array(
                    exposure.exposures, hdf5.vstr)
        elif 'assetcol' in self.datastore.parent:
            logging.info('Reusing hazard exposure')
            haz_sitecol = read_parent_sitecol(oq, self.datastore)
            assetcol = self.datastore.parent['assetcol']
            assetcol.update_tagcol(oq.aggregate_by)
            if oq.region:
                region = wkt.loads(oq.region)
                self.sitecol = haz_sitecol.within(region)
            if oq.shakemap_id or 'shakemap' in oq.inputs or oq.shakemap_uri:
                self.sitecol, self.assetcol = store_gmfs_from_shakemap(
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
                self.sitecol = haz_sitecol
                if ('site_id' in oq.aggregate_by and 'site_id' not
                        in assetcol.tagcol.tagnames):
                    assetcol.tagcol.add_tagname('site_id')
                    assetcol.tagcol.site_id.extend(range(self.N))
        else:  # no exposure
            self._read_no_exposure(haz_sitecol)
        if (oq.calculation_mode.startswith(('event_based', 'ebrisk')) and
                oq.ground_motion_fields and self.N > 1000 and
                len(oq.min_iml) == 0):
            oq.raise_invalid(f'minimum_intensity must be set, see {EBDOC}')

        if oq_hazard:
            parent = self.datastore.parent
            if 'assetcol' in parent:
                check_time_event(oq, parent['assetcol'].occupancy_periods)
            elif oq.job_type == 'risk' and 'exposure' not in oq.inputs:
                raise ValueError('Missing exposure both in hazard and risk!')
            if (oq_hazard.time_event != 'avg' and
                    oq_hazard.time_event != oq.time_event):
                raise ValueError(
                    'The risk configuration file has time_event=%s but the '
                    'hazard was computed with time_event=%s' % (
                        oq.time_event, oq_hazard.time_event))

    def _read_risk2(self):
        oq = self.oqparam
        if oq.job_type == 'risk':
            if not hasattr(self, 'assetcol'):
                oq.raise_invalid('missing exposure')

            taxidx = self.assetcol.get_taxidx()
            # i.e. {'Concrete1': 1, 'Wood1': 2}
            tmap_df = readinput.taxonomy_mapping(oq, taxidx)
            self.crmodel.set_tmap(tmap_df, taxidx)
            risk_ids = set(tmap_df.risk_id)

            # check that we are covering all the taxonomies in the exposure
            # (exercised in EventBasedRiskTestCase::test_missing_taxonomy)
            missing = risk_ids - set(self.crmodel.riskids)
            msg = f'tmap.risk_id {missing} not in the CompositeRiskModel'
            if self.crmodel and missing:
                # in scenario_damage/case_14 the fragility model contains
                # 'CR+PC/LDUAL/HBET:8.19/m ' with a trailing space while
                # tmap.risk_id is extracted from the exposure and has no space
                raise RuntimeError(msg)

            self.crmodel.check_risk_ids(oq.inputs)

            if len(self.crmodel.riskids) > len(risk_ids):
                logging.info(
                    'Reducing risk model from %d to %d risk functions',
                    len(self.crmodel.riskids), len(risk_ids))
                self.crmodel = self.crmodel.reduce(risk_ids)
                self.crmodel.tmap_df = tmap_df

    def _read_risk3(self):
        oq = self.oqparam
        if 'station_data' in oq.inputs:
            logging.info('Reading station data from %s',
                         oq.inputs['station_data'])
            # NB: get_station_data is extending the complete sitecol
            # which then is associated to the site parameters below
            self.station_data, self.observed_imts = \
                readinput.get_station_data(oq, self.sitecol,
                                           duplicates_strategy='avg')
            self.datastore.create_df('station_data', self.station_data)
            oq.observed_imts = self.observed_imts

        if hasattr(self, 'sitecol') and self.sitecol and not oq.ruptures_hdf5:
            if 'site_model' in oq.inputs or oq.impact:
                assoc_dist = (oq.region_grid_spacing * 1.414
                              if oq.region_grid_spacing else 5)  # Graeme's 5km
                sm = readinput.get_site_model(oq, self.datastore.hdf5)
                if oq.prefer_global_site_params and not numpy.isnan(
                        oq.reference_vs30_value):
                    self.sitecol.set_global_params(oq)
                else:
                    # use the site model parameters
                    self.sitecol.assoc(sm, assoc_dist)

            if oq.override_vs30:
                # override vs30, z1pt0 and z2pt5
                if len(self.sitecol) == 1:
                    # tested in classical/case_08
                    self.sitecol.array['vs30'] = -999
                self.sitecol = self.sitecol.multiply(oq.override_vs30)
                names = self.sitecol.array.dtype.names
                if 'z1pt0' in names:
                    self.sitecol.calculate_z1pt0()
                if 'z2pt5' in names:
                    self.sitecol.calculate_z2pt5()

            self.datastore['sitecol'] = self.sitecol
            if self.sitecol is not self.sitecol.complete:
                self.datastore['complete'] = self.sitecol.complete
            elif 'complete' in self.datastore.parent:
                # fix: the sitecol is not complete
                self.sitecol.complete = self.datastore.parent['complete']

        # store amplification functions if any
        if 'amplification' in oq.inputs:
            logging.info('Reading %s', oq.inputs['amplification'])
            df = AmplFunction.read_df(oq.inputs['amplification'])
            check_amplification(df, self.sitecol)
            if oq.amplification_method == 'kernel':
                # TODO: need to add additional checks on the main calculation
                # methodology since the kernel method is currently tested only
                # for classical PSHA
                self.af = AmplFunction.from_dframe(df)
            else:
                self.amplifier = Amplifier(oq.imtls, df, oq.soil_intensities)

        # manage secondary perils
        sec_perils = oq.get_sec_perils()
        for sp in sec_perils:
            sp.prepare(self.sitecol)  # add columns as needed
        if sec_perils:
            self.datastore['sitecol'] = self.sitecol

        mal = {lt: getdefault(oq.minimum_asset_loss, lt)
               for lt in oq.loss_types}
        if mal:
            logging.info('minimum_asset_loss=%s', mal)
        oq._amplifier = self.amplifier
        oq._sec_perils = sec_perils
        # compute exposure stats
        if hasattr(self, 'assetcol'):
            save_agg_values(
                self.datastore, self.assetcol, oq.loss_types, oq.aggregate_by)

        if 'post_loss_amplification' in oq.inputs:
            df = pandas.read_csv(oq.inputs['post_loss_amplification']
                                 ).sort_values('return_period')
            self.datastore.create_df('post_loss_amplification', df)

    def store_rlz_info(self, rel_ruptures):
        """
        Save info about the composite source model inside the full_lt dataset

        :param rel_ruptures: dictionary TRT -> number of relevant ruptures
        """
        if hasattr(self, 'full_lt'):  # no scenario
            if self.full_lt.get_num_paths() == 0:
                raise RuntimeError('Empty logic tree: too much filtering?')
        else:  # scenario
            self.full_lt = self.datastore['full_lt']
        if 'weights' not in self.datastore:
            self.datastore['weights'] = F32(
                [rlz.weight[-1] for rlz in self.full_lt.get_realizations()])
        if rel_ruptures:
            self.check_discardable(rel_ruptures)

    def check_discardable(self, rel_ruptures):
        """
        Check if logic tree reduction is possible
        """
        keep_trts = set()
        nrups = []
        for grp_id, trt_smrs in enumerate(self.csm.get_trt_smrs()):
            trti, _smrs = numpy.divmod(trt_smrs, 2**24)
            trt = self.full_lt.trts[trti[0]]
            nr = rel_ruptures.get(grp_id, 0)
            nrups.append(nr)
            if nr:
                keep_trts.add(trt)
        self.datastore['est_rups_by_grp'] = U32(nrups)
        discard_trts = set(self.full_lt.trts) - keep_trts
        if discard_trts and self.oqparam.calculation_mode == 'disaggregation':
            self.oqparam.discard_trts = discard_trts
        elif discard_trts:
            msg = ('No sources for some TRTs: you should set\n'
                   'discard_trts = %s\nin %s') % (
                       ', '.join(discard_trts), self.oqparam.inputs['job_ini'])
            logging.warning(msg)

    # to be called after csm.fix_src_offset()
    def store_source_info(self, source_data):
        """
        Save (eff_ruptures, num_sites, calc_time) inside the source_info
        """
        # called first in preclassical, then called again in classical
        first_time = 'source_info' not in self.datastore
        if first_time:
            source_reader.create_source_info(self.csm, self.datastore.hdf5)
        self.csm.update_source_info(source_data)
        recs = [tuple(row) for row in self.csm.source_info.values()]
        self.datastore['source_info'][:] = numpy.array(
            recs, source_reader.source_info_dt)

        # sanity check on the total weight
        totw = sum(src.weight for src in self.csm.get_sources())
        saved = sum(row[source_reader.WEIGHT]
                    for row in self.csm.source_info.values())
        numpy.testing.assert_allclose(totw, saved, atol=1E-3)

    def post_process(self):
        """
        Run postprocessing function, if any
        """
        oq = self.oqparam
        if oq.postproc_func:
            modname, funcname = oq.postproc_func.rsplit('.', 1)
            mod = getattr(postproc, modname)
            func = getattr(mod, funcname)
            if 'csm' in inspect.getfullargspec(func).args:
                if hasattr(self, 'csm'):  # already there
                    csm = self.csm
                else:  # read the csm from the parent calculation
                    csm = self.datastore.parent['_csm']
                    csm.full_lt = self.datastore.parent['full_lt'].init()
                oq.postproc_args['csm'] = csm
            with self._monitor(oq.postproc_func, measuremem=True):
                func(self.datastore, **oq.postproc_args)


class RiskCalculator(HazardCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .crmodel, .sitecol, .assetcol, .riskinputs in the
    pre_execute phase.
    """

    def build_riskinputs(self):
        """
        :returns:
            a list of RiskInputs objects, sorted by IMT.
        """
        logging.info('Building risk inputs from %d realization(s)', self.R)
        imtset = set(self.oqparam.imtls) | set(self.oqparam.sec_imts)
        if not set(self.oqparam.risk_imtls) & imtset:
            rsk = ', '.join(self.oqparam.risk_imtls)
            haz = ', '.join(imtset)
            raise ValueError('The IMTs in the risk models (%s) are disjoint '
                             "from the IMTs in the hazard (%s)" % (rsk, haz))
        if len(self.crmodel.tmap_df) == 0:
            taxonomies = self.assetcol.tagcol.taxonomy[1:]
            taxidx = {taxo: i for i, taxo in enumerate(taxonomies, 1)}
            self.crmodel.tmap_df = readinput.taxonomy_mapping(
                self.oqparam, taxidx)
        with self.monitor('building riskinputs'):
            if self.oqparam.hazard_calculation_id:
                dstore = self.datastore.parent
            else:
                dstore = self.datastore
            riskinputs = self._gen_riskinputs(dstore)
        assert riskinputs
        logging.info('Built %d risk inputs', len(riskinputs))
        self.acc = None
        return riskinputs

    # used only for classical_risk and classical_damage
    def _gen_riskinputs(self, dstore):
        out = []
        asset_df = self.assetcol.to_dframe('site_id')
        getterdict = getters.CurveGetter.build(dstore)
        for sid, assets in asset_df.groupby(asset_df.index):
            getter = getterdict[sid]
            # hcurves, shape (R, N)
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
            smap.submit((block, self.oqparam))
        return smap.reduce(self.combine, self.acc)

    def combine(self, acc, res):
        """
        Combine the outputs assuming acc and res are dictionaries
        """
        if res is None:
            raise MemoryError('You ran out of memory!')
        return acc + res


def longname(name, columns):
    """Add the secondary peril prefix to the name"""
    for col in columns:
        if col.endswith(name):
            return col
            break
    else:
        return name


# NB: changes oq.imtls by side effect!
def import_gmfs_csv(dstore, oqparam, sitecol):
    """
    Import in the datastore a ground motion field CSV file.

    :param dstore: the datastore
    :param oqparam: an OqParam instance
    :param sitecol: the site collection
    :returns: event_ids
    """
    [fname] = oqparam.inputs['gmfs']
    dtdict = {'sid': U32,
              'eid': U32,
              'custom_site_id': (numpy.bytes_, 8),
              None: F32}
    array = hdf5.read_csv(
        fname, dtdict,
        renamedict=dict(site_id='sid', event_id='eid', rlz_id='rlzi')
    ).array
    names = array.dtype.names  # rlz_id, sid, ...
    if names[0] == 'rlzi':  # backward compatibility
        names = names[1:]  # discard the field rlzi
    names = [n for n in names if n != 'custom_site_id']
    # strip prefix `gmv_` from the column name
    imts = [name[4:] if name.startswith('gmv_') else name
            for name in names if name not in ('sid', 'eid')]
    oqparam.hazard_imtls = {imt: [0] for imt in imts}
    missing = set(oqparam.imtls) - set(imts)
    if missing:
        raise ValueError('The calculation needs %s which is missing from %s' %
                         (', '.join(missing), fname))
    arr = numpy.zeros(len(array), oqparam.gmf_data_dt())
    for name in names:
        lname = longname(name, arr.dtype.names)
        arr[name[4:] if name.startswith('gmv_') else lname] = array[name]

    if 'sid' not in names:
        # there is a custom_site_id instead
        customs = sitecol.complete.custom_site_id
        to_sid = {csi: sid for sid, csi in enumerate(customs)}
        for csi in numpy.unique(array['custom_site_id']):
            ok = array['custom_site_id'] == csi
            arr['sid'][ok] = to_sid[csi]

    n = len(numpy.unique(arr[['sid', 'eid']]))
    if n != len(array):
        raise ValueError('Duplicated site_id, event_id in %s' % fname)
    # store the events
    eids = numpy.unique(array['eid'])
    eids.sort()
    if eids[0] != 0:
        raise ValueError('The event_id must start from zero in %s' % fname)
    store_events(dstore, eids)
    logging.info('Storing %d events, all relevant', len(eids))
    # store the GMFs
    dic = general.group_array(arr, 'sid')
    offset = 0
    gmvlst = []
    for sid in sitecol.complete.sids:
        n = len(dic.get(sid, []))
        if n:
            offset += n
            gmvs = dic[sid]
            gmvlst.append(gmvs)
    data = numpy.concatenate(gmvlst)
    data.sort(order='eid')
    create_gmf_data(dstore, oqparam.get_primary_imtls(),
                    oqparam.sec_imts, data=data, N=len(sitecol.complete))
    dstore['weights'] = numpy.ones(1)
    return eids


def _getset_attrs(oq):
    # read effective_time, num_events and imts from oq.inputs['gmfs']
    # if the format of the file is old (v3.11) also sets the attributes
    # investigation_time and ses_per_logic_tree_path on `oq`
    num_sites = []
    num_events = []
    for fname in oq.inputs['gmfs']:
        with hdf5.File(fname, 'r') as f:
            try:
                attrs = dict(f['gmf_data'].attrs)
                num_events.append(attrs['num_events'])
            except KeyError:
                attrs = {}
                num_events.append(len(f['events']))
            num_sites.append(len(f['sitecol']))
    return dict(effective_time=attrs.get('effective_time'),
                num_events=num_events, num_sites=num_sites, imts=list(oq.imtls))


def import_sites_hdf5(dstore, fnames):
    """
    Import site collections by merging them.

    :returns: a list of dictionaries local_sid->global_sid for each sitecol
    """
    if len(fnames) == 1:
        with hdf5.File(fnames[0], 'r') as f:
            dstore['sitecol'] = f['sitecol']
        convs = []
    else:  # merge the sites
        dstore['sitecol'], convs = site.merge_sitecols(fnames)
    return convs


# tested in scenario_test/case_33
def import_ruptures_hdf5(h5, fnames):
    """
    Importing the ruptures and the events
    """
    size = sum(os.path.getsize(f) for f in fnames)
    logging.warning('Importing %d files, %s',
                    len(fnames), general.humansize(size))
    rups = []
    h5.create_dataset(
        'events', (0,), rupture.events_dt, maxshape=(None,), chunks=True,
        compression='gzip')
    h5.create_dataset(
        'rupgeoms', (0,), hdf5.vfloat32, maxshape=(None,), chunks=True)
    E = 0
    offset = 0
    for fileno, fname in enumerate(fnames):
        with hdf5.File(fname, 'r') as f:
            oq = f['oqparam']
            events = f['events'][:]
            events['id'] += E
            events['rup_id'] += offset
            E += len(events)
            hdf5.extend(h5['events'], events)
            arr = f['rupgeoms'][:]
            h5.save_vlen('rupgeoms', list(arr))
            rup = f['ruptures'][:]
            rup['id'] += offset
            rup['geom_id'] += offset
            offset += len(rup)
            rups.extend(rup)
            if oq.mosaic_model and 'full_lt' in f:
                h5[f'full_lt/{oq.mosaic_model}'] = f['full_lt']

    ruptures = numpy.array(rups, dtype=rups[0].dtype)
    ruptures['e0'][1:] = ruptures['n_occ'].cumsum()[:-1]
    h5.create_dataset('ruptures', data=ruptures, compression='gzip')
    h5.create_dataset(
        'trt_smr_start_stop', data=idx_start_stop(ruptures['trt_smr']))


def import_gmfs_hdf5(dstore, oq):
    """
    Import in the datastore a ground motion field HDF5 file.

    :param dstore: the datastore
    :param oq: an OqParam instance
    :returns: event_ids
    """
    # NB: once we tried to use ExternalLinks to avoid copying the GMFs,
    # but you cannot access an external link if the file it points to is
    # already open, therefore you cannot run in parallel two calculations
    # starting from the same GMFs; moreover a calc_XXX.hdf5 downloaded
    # from the webui would be small but orphan of the GMFs; moreover
    # users changing the name of the external file or changing the
    # ownership would break calc_XXX.hdf5; therefore we copy everything
    # even if bloated (also because of SURA issues having the external
    # file under NFS and calc_XXX.hdf5 in the local filesystem)
    if 'oqparam' not in dstore:
        dstore['oqparam'] = oq
    fnames = oq.inputs['gmfs']
    size = sum(os.path.getsize(f) for f in fnames)
    logging.warning('Importing %d files, %s',
                    len(fnames), general.humansize(size))
    attrs = _getset_attrs(oq)
    E = sum(attrs['num_events'])
    rups = []
    if len(fnames) == 1:
        with hdf5.File(fnames[0], 'r') as f:
            dstore['sitecol'] = f['sitecol']  # complete by construction
            if 'gmv_0' in f['gmf_data']:  # old format <= v3.23
                imts = f['gmf_data'].attrs['imts']
                imtlist = imts.split()
                grp = dstore.hdf5.create_group('gmf_data')
                for nam, val in f['gmf_data'].attrs.items():
                    if nam == '__pdcolumns__':
                        grp.attrs['__pdcolumns__'] = 'eid sid ' + imts
                    else:
                        grp.attrs[nam] = val
                for col in f['gmf_data']:
                    if col.startswith('gmv_'):  # before v3.24
                        name = imtlist[int(col[4:])]
                    else:
                        name = col
                    f.copy(f'gmf_data/{col}', grp, name)
            else:
                f.copy('gmf_data', dstore.hdf5)
    else:  # merge the sites and the gmfs, tested in scenario/case_33
        convs = import_sites_hdf5(dstore, fnames)
        create_gmf_data(dstore, oq.all_imts(), E=E,
                        R=oq.number_of_logic_tree_samples)
        num_ev_rup_site = []
        fileno = 0
        nE = 0
        for fname, conv, ne in zip(fnames, convs, attrs['num_events']):
            logging.warning('Importing %s', fname)
            with hdf5.File(fname, 'r') as f:
                fileno += 1
                imtlist = f['gmf_data'].attrs['imts'].split()
                size = len(f['gmf_data/sid'])
                logging.info('Reading {:_d} rows from {}'.format(size, fname))
                sids = numpy.array(list(conv))
                for slc in general.gen_slices(0, size, 10_000_000):
                    df = f.read_df('gmf_data', slc=slc)
                    df = df[numpy.isin(df.sid, sids)]
                    for sid, idx in conv.items():
                        df.loc[df.sid == sid, 'sid'] = idx
                    df['eid'] += nE  # add an offset to the event IDs
                    for col in df.columns:
                        if col.startswith('gmv_'):  # before v3.24
                            name = imtlist[int(col[4:])]
                        else:
                            name = col
                        hdf5.extend(dstore[f'gmf_data/{name}'], df[col])
            nE += ne
            num_ev_rup_site.append((nE, len(rups), len(conv)))
        oq.hazard_imtls = {imt: [0] for imt in attrs['imts']}

    # store the events
    events = numpy.zeros(E, rupture.events_dt)
    rel = numpy.unique(dstore['gmf_data/eid'][:])
    e = len(rel)
    assert E >= e, (E, e)
    events['id'] = numpy.concatenate([rel, numpy.arange(E-e) + rel.max() + 1])
    logging.info('Storing %d events, %d relevant', E, e)
    dstore['events'] = events
    n = oq.number_of_logic_tree_samples
    if n:
        dstore['weights'] = numpy.full(n, 1/n)
    else:
        dstore['weights'] = numpy.ones(1)
    return events['id']


def create_gmf_data(dstore, prim_imts, sec_imts=(), data=None,
                    N=None, E=None, R=None):
    """
    Create and possibly populate the datasets in the gmf_data group
    """
    oq = dstore['oqparam']
    if not R and 'full_lt' not in dstore:  # from shakemap
        dstore['full_lt'] = logictree.FullLogicTree.fake()
        store_events(dstore, E)
    R = R or dstore['full_lt'].get_num_paths()
    M = len(prim_imts)
    if data is None:
        N = 0
    else:
        assert N is not None  # pass len(complete) here
    items = [('sid', U32 if N == 0 else data['sid']),
             ('eid', U32 if N == 0 else data['eid'])]
    for col in map(str, prim_imts):
        items.append((col, F32 if data is None else data[col]))
    for imt in sec_imts:
        items.append((str(imt), F32 if N == 0 else data[imt]))
    if oq.investigation_time:
        eff_time = oq.investigation_time * oq.ses_per_logic_tree_path * R
    else:
        eff_time = 0
    dstore.create_df('gmf_data', items,
                     num_events=E or len(dstore['events']),
                     imts=' '.join(map(str, prim_imts)),
                     investigation_time=oq.investigation_time or 0,
                     effective_time=eff_time)
    if oq.mea_tau_phi:
        dstore.create_df(
            'mea_tau_phi', GmfComputer.mtp_dt.descr, compression='gzip')

    if data is not None:
        _df = pandas.DataFrame(dict(items))
        avg_gmf = numpy.zeros((2, N, M + len(sec_imts)), F32)
        for sid, df in _df.groupby(_df.sid):
            df.pop('eid')
            df.pop('sid')
            avg_gmf[:, sid] = stats.avg_std(df.to_numpy())
        dstore['avg_gmf'] = avg_gmf


def save_agg_values(dstore, assetcol, lossnames, aggby):
    """
    Store agg_keys, agg_values.
    :returns: the aggkey dictionary key -> tags
    """
    if aggby:
        aggids, aggtags = assetcol.build_aggids(aggby)
        logging.info('Storing %d aggregation keys', len(aggids))
        agg_keys = ['\t'.join(tags) for tags in aggtags]
        dstore['agg_keys'] = numpy.array(agg_keys, hdf5.vstr)
        if 'assetcol' not in set(dstore):
            dstore['assetcol'] = assetcol
    if assetcol.get_value_fields():
        dstore['agg_values'] = assetcol.get_agg_values(aggby)


def store_events(dstore, eids):
    """
    Store E events associated to a single realization
    """
    if isinstance(eids, numpy.ndarray):
        E = len(eids)
        events = numpy.zeros(E, rupture.events_dt)
        events['id'] = eids
    else:  # scalar
        E = eids
        events = numpy.zeros(E, rupture.events_dt)
        events['id'] = numpy.arange(E, dtype=U32)
    dstore['events'] = events
    dstore['weights'] = [1.]
    return events


def store_gmfs(calc, sitecol, shakemap, gmf_dict):
    """
    Store a ShakeMap array as a gmf_data dataset.
    """
    logging.info('Building GMFs')
    oq = calc.oqparam
    with calc.monitor('building/saving GMFs'):
        vs30 = None  # do not amplify, the ShakeMap takes care of that already
        imts, gmfs = to_gmfs(shakemap, gmf_dict, vs30,
                             oq.truncation_level,
                             oq.number_of_ground_motion_fields,
                             oq.random_seed, oq.imtls)
        N, E, _M = gmfs.shape
        events = store_events(calc.datastore, E)
        # convert into an array of dtype gmv_data_dt
        lst = [(sitecol.sids[s], ei) + tuple(gmfs[s, ei])
               for ei, event in enumerate(events)
               for s in numpy.arange(N, dtype=U32)]
        oq.hazard_imtls = {str(imt): [0] for imt in imts}
        data = numpy.array(lst, oq.gmf_data_dt())
        create_gmf_data(
            calc.datastore, imts, data=data, N=len(sitecol.complete), R=1)
        calc.datastore['full_lt'] = logictree.FullLogicTree.fake()
        calc.datastore['weights'] = numpy.ones(1)


def store_gmfs_from_shakemap(calc, haz_sitecol, assetcol):
    """
    Enabled only if there is a shakemap parameter in the job.ini.
    Download, unzip, parse USGS shakemap files and build a corresponding
    set of GMFs which are then filtered with the hazard site collection
    and stored in the datastore.
    """
    oq = calc.oqparam
    with calc.monitor('getting/reducing shakemap'):
        sitecol, shakemap = readinput.assoc_to_shakemap(
            oq, haz_sitecol, assetcol)  # also reducing assetcol
        calc.datastore['assetcol'] = assetcol
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
                % ', '.join(oq.imtls))
    else:
        # no MMI intensities, calculation with or without correlation
        if oq.impact:
            gmf_dict = {'kind': 'basic'}  # possibly add correlation
        elif oq.spatial_correlation != 'no' or oq.cross_correlation != 'no':
            # cross correlation and/or spatial correlation after S&H
            gmf_dict = {'kind': 'Silva&Horspool',
                        'spatialcorr': oq.spatial_correlation,
                        'crosscorr': oq.cross_correlation,
                        'cholesky_limit': oq.cholesky_limit}
        else:
            # no correlation required, basic calculation is faster
            gmf_dict = {'kind': 'basic'}
    store_gmfs(calc, sitecol, shakemap, gmf_dict)
    return sitecol, assetcol


def read_parent_sitecol(oq, dstore):
    """
    :returns: the hazard site collection in the parent calculation
    """
    with datastore.read(oq.hazard_calculation_id) as parent:
        if 'sitecol' in parent:
            haz_sitecol = parent['sitecol'].complete
        else:
            haz_sitecol = readinput.get_site_collection(oq, dstore.hdf5)
        if ('amplification' in oq.inputs and
                'ampcode' not in haz_sitecol.array.dtype.names):
            haz_sitecol.add_col('ampcode', site.ampcode_dt)
    return haz_sitecol


def create_risk_by_event(calc):
    """
    Created an empty risk_by_event with keys event_id, agg_id, loss_id
    and fields for damages, losses and consequences
    """
    oq = calc.oqparam
    dstore = calc.datastore
    try:
        K = len(dstore['agg_keys'])
    except KeyError:
        K = 0
    crmodel = calc.crmodel
    if 'risk' in oq.calculation_mode:
        fields = [('loss', F32)]
        descr = [('event_id', U32), ('agg_id', U32), ('loss_id', U8),
                 ('variance', F32)] + fields
        dstore.create_df('risk_by_event', descr, K=K, L=len(oq.loss_types))
    else:  # damage + consequences
        dmgs = ' '.join(crmodel.damage_states[1:])
        descr = ([('event_id', U32), ('agg_id', U32), ('loss_id', U8)] +
                 [(dc, F32) for dc in crmodel.get_dmg_csq()])
        dstore.create_df('risk_by_event', descr, K=K,
                         L=len(oq.loss_types), limit_states=dmgs)


class DstoreCache:
    """
    Datastore cache based on a file called 'ini_hdf5.csv'
    containing associations job.ini -> calc_XXX.hdf5
    """
    def __init__(self, dirpath):
        self.ini_hdf5_csv = os.path.join(dirpath or tempfile.gettempdir(),
                                         'ini_hdf5.csv')

    def read(self):
        cache = {}
        if not os.path.exists(self.ini_hdf5_csv):
            return cache
        with open(self.ini_hdf5_csv, 'rt') as f:
            for line in f:
                ini, hdf5 = line.split(',')
                cache[ini] = hdf5[:-1]  # strip trailing \n
        return cache

    def get(self, ini):
        assert ',' not in ini, ini
        cache = self.read()
        if ini in cache:
            return datastore.read(cache[ini])
        dstore = run_calc(ini).datastore
        cache[ini] = dstore.filename
        assert ',' not in cache[ini], cache[ini]
        with open(self.ini_hdf5_csv, 'w') as f:
            for ini, h5 in sorted(cache.items()):
                print(f'{ini},{h5}', file=f)
        return dstore

    def clear(self):
        os.remove(self.ini_hdf5_csv)

dcache = DstoreCache(config.directory.custom_tmp)


def run_calc(job_ini, **kw):
    """
    Helper to run calculations programmatically.

    :param job_ini: path to a job.ini file or dictionary of parameters
    :param kw: parameters to override
    :returns: a Calculator instance
    """
    with logs.init(job_ini) as log:
        log.params.update(kw)
        calc = calculators(log.get_oqparam(), log.calc_id)
        calc.run()
        return calc


def expose_outputs(dstore, owner=USER, status='complete', calc_id=None):
    """
    Build a correspondence between the outputs in the datastore and the
    ones in the database.

    :param dstore: datastore
    """
    oq = dstore['oqparam']
    exportable = set(ekey[0] for ekey in exp)
    calcmode = oq.calculation_mode
    dskeys = set(dstore) & exportable  # exportable datastore keys
    dskeys.add('fullreport')
    rlzs = dstore['full_lt'].rlzs
    if len(rlzs) > 1:
        dskeys.add('realizations')
    hdf5 = dstore.hdf5
    if 'mmi_tags' in hdf5:
        dskeys.add('mmi_tags')
    if 'hcurves-stats' in hdf5 or 'hcurves-rlzs' in hdf5:
        if oq.hazard_stats() or oq.individual_rlzs or len(rlzs) == 1:
            dskeys.add('hcurves')
        if oq.uniform_hazard_spectra:
            dskeys.add('uhs')  # export them
        if oq.hazard_maps:
            dskeys.add('hmaps')  # export them
    if len(rlzs) > 1 and not oq.collect_rlzs:
        if 'aggrisk' in dstore:
            dskeys.add('aggrisk-stats')
        if 'aggcurves' in dstore:
            dskeys.add('aggcurves-stats')
        if not oq.individual_rlzs:
            for out in ['avg_losses-rlzs', 'aggrisk', 'aggcurves']:
                if out in dskeys:
                    dskeys.remove(out)
    if 'curves-rlzs' in dstore and len(rlzs) == 1:
        dskeys.add('loss_curves-rlzs')
    if 'curves-stats' in dstore and len(rlzs) > 1:
        dskeys.add('loss_curves-stats')
    if oq.conditional_loss_poes:  # expose loss_maps outputs
        if 'loss_curves-stats' in dstore:
            dskeys.add('loss_maps-stats')
    if 'ruptures' in dskeys:
        if 'scenario' in calcmode or len(dstore['ruptures']) == 0:
            # do not export, as requested by Vitor
            exportable.remove('ruptures')
        else:
            dskeys.add('event_based_mfd')
    if 'hmaps' in dskeys and not oq.hazard_maps:
        dskeys.remove('hmaps')  # do not export the hazard maps
    if logs.dbcmd('get_job', dstore.calc_id) is None:
        # the calculation has not been imported in the db yet
        logs.dbcmd('import_job', dstore.calc_id, oq.calculation_mode,
                   oq.description + ' [parent]', owner, status,
                   oq.hazard_calculation_id, dstore.datadir)
    keysize = []
    for key in sorted(dskeys & exportable):
        try:
            size_mb = dstore.getsize(key) / MB
        except (KeyError, AttributeError):
            size_mb = -1
        if size_mb:
            keysize.append((key, size_mb))
    ds_size = dstore.getsize() / MB
    logs.dbcmd('create_outputs', calc_id or dstore.calc_id, keysize, ds_size)
