# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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
import sys
import abc
import pdb
import math
import socket
import logging
import operator
import traceback
import collections

import numpy

from openquake.hazardlib.geo import geodetic
from openquake.baselib import general, hdf5
from openquake.baselib.performance import Monitor
from openquake.risklib import riskinput, __version__, __codename__
from openquake.commonlib import readinput, riskmodels, datastore, source
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib.parallel import starmap, executor
from openquake.commonlib.views import view, rst_table, stats
from openquake.baselib.python3compat import with_metaclass

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_trt = operator.attrgetter('trt_model_id')
get_imt = operator.attrgetter('imt')

calculators = general.CallableDict(operator.attrgetter('calculation_mode'))

Site = collections.namedtuple('Site', 'sid lon lat')

F32 = numpy.float32


class AssetSiteAssociationError(Exception):
    """Raised when there are no hazard sites close enough to any asset"""

rlz_dt = numpy.dtype([('uid', (bytes, 200)), ('weight', F32)])

logversion = {True}


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


class BaseCalculator(with_metaclass(abc.ABCMeta)):
    """
    Abstract base class for all calculators.

    :param oqparam: OqParam object
    :param monitor: monitor object
    :param calc_id: numeric calculation ID
    """
    sitecol = datastore.persistent_attribute('sitecol')
    etags = datastore.persistent_attribute('etags')
    assetcol = datastore.persistent_attribute('assetcol')
    cost_types = datastore.persistent_attribute('cost_types')
    job_info = datastore.persistent_attribute('job_info')
    performance = datastore.persistent_attribute('performance')
    csm = datastore.persistent_attribute('composite_source_model')
    pre_calculator = None  # to be overridden
    is_stochastic = False  # True for scenario and event based calculators

    @property
    def taxonomies(self):
        return self.datastore['assetcol/taxonomies'].value

    def __init__(self, oqparam, monitor=Monitor(), calc_id=None):
        self.monitor = monitor
        self.datastore = datastore.DataStore(calc_id)
        self.monitor.calc_id = self.datastore.calc_id
        self.monitor.hdf5path = self.datastore.hdf5path
        self.datastore.export_dir = oqparam.export_dir
        self.oqparam = oqparam

    def save_params(self, **kw):
        """
        Update the current calculation parameters and save engine_version
        """
        vars(self.oqparam).update(engine_version=__version__, **kw)
        self.datastore['oqparam'] = self.oqparam  # save the updated oqparam
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
        self.close = close
        self.set_log_format()
        if logversion:  # make sure this is logged only once
            logging.info(
                'Using engine version %s "%s"', __version__, __codename__)
            logversion.pop()
        if (concurrent_tasks is not None and concurrent_tasks !=
                OqParam.concurrent_tasks.default):
            self.oqparam.concurrent_tasks = concurrent_tasks
        self.save_params(**kw)
        exported = {}
        try:
            if pre_execute:
                self.pre_execute()
            result = self.execute()
            self.post_execute(result)
            exported = self.export(kw.get('exports', ''))
        except KeyboardInterrupt:
            pids = ' '.join(str(p.pid) for p in executor._processes)
            sys.stderr.write(
                'You can manually kill the workers with kill %s\n' % pids)
            raise
        except:
            if kw.get('pdb'):  # post-mortem debug
                tb = sys.exc_info()[2]
                traceback.print_exc(tb)
                pdb.post_mortem(tb)
            else:
                logging.critical('', exc_info=True)
                raise
        self.clean_up()
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

        :returns: dictionary output_key -> sorted list of exported paths
        """
        # avoid circular imports
        from openquake.commonlib.export import export as exp
        exported = {}
        individual_curves = self.oqparam.individual_curves
        if exports and isinstance(exports, tuple):
            fmts = exports
        elif exports:  # is a string
            fmts = exports.split(',')
        else:  # use passed values
            fmts = self.oqparam.exports
        for fmt in fmts:
            if not fmt:
                continue
            keys = set(self.datastore)
            if (self.oqparam.uniform_hazard_spectra and not
                    self.oqparam.hazard_maps):
                # do not export the hazard maps, even if they are there
                keys.remove('hmaps')
            for key in sorted(keys):  # top level keys
                if 'rlzs' in key and not individual_curves:
                    continue  # skip individual curves
                ekey = (key, fmt)
                if ekey not in exp:  # non-exportable output
                    continue
                with self.monitor('export'):
                    exported[ekey] = exp(ekey, self.datastore)
                logging.info('exported %s: %s', key, exported[ekey])
            # special case for uhs which is a view
            if (self.oqparam.uniform_hazard_spectra and
                    'hmaps' in self.datastore):
                ekey = ('uhs', fmt)
                exported[ekey] = exp(ekey, self.datastore)
                logging.info('exported %s: %s', key, exported[ekey])
        return exported

    def clean_up(self):
        """
        Collect the realizations and the monitoring information,
        then close the datastore.
        """
        if 'hcurves' in self.datastore:
            self.datastore.set_nbytes('hcurves')
        if 'hmaps' in self.datastore:
            self.datastore.set_nbytes('hmaps')
        self.datastore.flush()
        if self.close:  # in the engine we close later
            try:
                self.datastore.close()
            except RuntimeError:  # there could be a mysterious HDF5 error
                logging.warn('', exc_info=True)


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
    SourceManager = source.SourceManager
    mean_curves = None  # to be overridden

    def assoc_assets_sites(self, sitecol):
        """
        :param sitecol: a sequence of sites
        :returns: a pair (filtered_sites, assets_by_site)

        The new site collection is different from the original one
        if some assets were discarded or if there were missing assets
        for some sites.
        """
        maximum_distance = self.oqparam.asset_hazard_distance
        siteobjects = geodetic.GeographicObjects(
            Site(sid, lon, lat) for sid, lon, lat in
            zip(sitecol.sids, sitecol.lons, sitecol.lats))
        assets_by_sid = general.AccumDict()
        for assets in self.assets_by_site:
            if len(assets):
                lon, lat = assets[0].location
                site, _ = siteobjects.get_closest(lon, lat, maximum_distance)
                if site:
                    assets_by_sid += {site.sid: list(assets)}
        if not assets_by_sid:
            raise AssetSiteAssociationError(
                'Could not associate any site to any assets within the '
                'maximum distance of %s km' % maximum_distance)
        mask = numpy.array([sid in assets_by_sid for sid in sitecol.sids])
        assets_by_site = [assets_by_sid.get(sid, []) for sid in sitecol.sids]
        return sitecol.filter(mask), numpy.array(assets_by_site)

    def count_assets(self):
        """
        Count how many assets are taken into consideration by the calculator
        """
        return sum(len(assets) for assets in self.assets_by_site)

    def compute_previous(self):
        precalc = calculators[self.pre_calculator](
            self.oqparam, self.monitor('precalculator'),
            self.datastore.calc_id)
        precalc.run()
        if 'scenario' not in self.oqparam.calculation_mode:
            self.csm = precalc.csm
        pre_attrs = vars(precalc)
        for name in ('riskmodel', 'assets_by_site'):
            if name in pre_attrs:
                setattr(self, name, getattr(precalc, name))

    def read_previous(self, precalc_id):
        parent = datastore.read(precalc_id)
        self.datastore.set_parent(parent)
        # copy missing parameters from the parent
        params = {name: value for name, value in
                  vars(parent['oqparam']).items()
                  if name not in vars(self.oqparam)}
        self.save_params(**params)
        self.read_risk_data()

    def basic_pre_execute(self):
        self.read_risk_data()
        if 'source' in self.oqparam.inputs:
            with self.monitor(
                    'reading composite source model', autoflush=True):
                self.csm = readinput.get_composite_source_model(self.oqparam)
                self.datastore['csm_info'] = self.csm.info
                self.rup_data = {}
        self.init()
        if 'source' in self.oqparam.inputs:
            with self.monitor('managing sources', autoflush=True):
                self.taskman = self.send_sources()
            attrs = self.datastore.hdf5['composite_source_model'].attrs
            attrs['weight'] = self.csm.weight
            attrs['filtered_weight'] = self.csm.filtered_weight
            attrs['maxweight'] = self.csm.maxweight

    def pre_execute(self):
        """
        Check if there is a pre_calculator or a previous calculation ID.
        If yes, read the inputs by invoking the precalculator or by retrieving
        the previous calculation; if not, read the inputs directly.
        """
        job_info = hdf5.LiteralAttrs()
        if self.pre_calculator is not None:
            # the parameter hazard_calculation_id is only meaningful if
            # there is a precalculator
            precalc_id = self.oqparam.hazard_calculation_id
            if precalc_id is None:  # recompute everything
                self.compute_previous()
            else:  # read previously computed data
                self.read_previous(precalc_id)
            self.init()
        else:  # we are in a basic calculator
            self.basic_pre_execute()
            if 'source' in self.oqparam.inputs:
                vars(job_info).update(readinput.get_job_info(
                    self.oqparam, self.csm, self.sitecol))

        job_info.hostname = socket.gethostname()
        if hasattr(self, 'riskmodel'):
            job_info.require_epsilons = bool(self.riskmodel.covs)
        self.job_info = job_info
        self.datastore.flush()
        try:
            csm_info = self.datastore['csm_info']
        except KeyError:
            pass
        else:
            csm_info.gsim_lt.check_imts(self.oqparam.imtls)

    def init(self):
        """
        To be overridden to initialize the datasets needed by the calculation
        """
        self.random_seed = None
        if 'csm_info' in self.datastore or 'csm_info' in self.datastore.parent:
            self.rlzs_assoc = self.datastore['csm_info'].get_rlzs_assoc()
        else:  # build a fake; used by risk-from-file calculators
            self.datastore['csm_info'] = fake = source.CompositionInfo.fake()
            self.rlzs_assoc = fake.get_rlzs_assoc()
        self.datastore['realizations'] = numpy.array(
            [(r.uid, r.weight) for r in self.rlzs_assoc.realizations], rlz_dt)

    def read_exposure(self):
        """
        Read the exposure, the riskmodel and update the attributes .exposure,
        .sitecol, .assets_by_site, .cost_types, .taxonomies.
        """
        logging.info('Reading the exposure')
        with self.monitor('reading exposure', autoflush=True):
            self.exposure = readinput.get_exposure(self.oqparam)
            arefs = numpy.array(self.exposure.asset_refs)
            self.datastore['asset_refs'] = arefs
            self.datastore.set_attrs('asset_refs', nbytes=arefs.nbytes)
            all_cost_types = set(self.oqparam.all_cost_types)
            fname = self.oqparam.inputs['exposure']
            self.cost_calculator = readinput.get_exposure_lazy(
                fname, all_cost_types)[-1]
            self.sitecol, self.assets_by_site = (
                readinput.get_sitecol_assets(self.oqparam, self.exposure))
            if len(self.exposure.cost_types):
                self.cost_types = self.exposure.cost_types

    def load_riskmodel(self):
        """
        Read the risk model and set the attribute .riskmodel.
        The riskmodel can be empty for hazard calculations.
        Save the loss ratios (if any) in the datastore.
        """
        rmdict = riskmodels.get_risk_models(self.oqparam)
        if not rmdict:  # can happen only in a hazard calculation
            return
        self.oqparam.set_risk_imtls(rmdict)
        self.save_params()  # re-save oqparam
        self.riskmodel = rm = readinput.get_risk_model(self.oqparam, rmdict)
        if 'taxonomies' in self.datastore:
            # check that we are covering all the taxonomies in the exposure
            missing = set(self.taxonomies) - set(rm.taxonomies)
            if rm and missing:
                raise RuntimeError('The exposure contains the taxonomies %s '
                                   'which are not in the risk model' % missing)

        # save the risk models and loss_ratios in the datastore
        for taxonomy, rmodel in rm.items():
            self.datastore['composite_risk_model/' + taxonomy] = (
                rmodel.risk_functions)
            if hasattr(rmodel, 'retro_functions'):
                self.datastore[
                    'composite_risk_model/%s-retrofitted' % taxonomy] = (
                        rmodel.retro_functions)
        attrs = self.datastore['composite_risk_model'].attrs
        attrs['loss_types'] = rm.loss_types
        attrs['min_iml'] = sorted(rm.get_min_iml().items())
        if rm.damage_states:
            attrs['damage_states'] = rm.damage_states
        self.datastore['loss_ratios'] = rm.get_loss_ratios()
        self.datastore.set_nbytes('composite_risk_model')
        self.datastore.set_nbytes('loss_ratios')
        self.datastore.hdf5.flush()

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
            num_assets = self.count_assets()
            if self.datastore.parent:
                haz_sitecol = self.datastore.parent['sitecol']
            if haz_sitecol is not None and haz_sitecol != self.sitecol:
                with self.monitor('assoc_assets_sites'):
                    self.sitecol, self.assets_by_site = \
                        self.assoc_assets_sites(haz_sitecol.complete)
                ok_assets = self.count_assets()
                num_sites = len(self.sitecol)
                logging.warn('Associated %d assets to %d sites, %d discarded',
                             ok_assets, num_sites, num_assets - ok_assets)
        elif oq_hazard and 'exposure' in oq_hazard.inputs:
            logging.info('Re-using the already imported exposure')
            self.load_riskmodel()
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

        # asset collection
        if hasattr(self, 'assets_by_site'):
            self.assetcol = riskinput.AssetCollection(
                self.assets_by_site, self.cost_calculator, oq.time_event,
                time_events=sorted(self.exposure.time_events) or '')
        elif hasattr(self, 'assetcol'):
            self.assets_by_site = self.assetcol.assets_by_site()

    def is_tiling(self):
        """
        :returns:
            True if the calculator produces more than one tile, False otherwise
        """
        return (self.oqparam.calculation_mode == 'classical' and
                len(self.sitecol) > self.oqparam.sites_per_tile)

    def send_sources(self):
        """
        Filter/split and send the sources to the workers.
        :returns: a :class:`openquake.commonlib.parallel.TaskManager`
        """
        oq = self.oqparam
        tiles = [self.sitecol]
        self.num_tiles = 1
        if self.is_tiling():
            hint = math.ceil(len(self.sitecol) / oq.sites_per_tile)
            tiles = self.sitecol.split_in_tiles(hint)
            self.num_tiles = len(tiles)
            logging.info('Generating %d tiles of %d sites each',
                         self.num_tiles, len(tiles[0]))
        manager = source.SourceManager(
            self.csm, oq.maximum_distance, self.datastore,
            self.monitor.new(oqparam=oq), self.random_seed,
            oq.filter_sources, num_tiles=self.num_tiles)
        tm = starmap(self.core_task.__func__, manager.gen_args(tiles))
        manager.store_source_info(self.datastore)
        return tm

    def save_data_transfer(self, taskmanager):
        """
        Save information about the data transfer in the risk calculation
        as attributes of agg_loss_table
        """
        if taskmanager.received:  # nothing is received when OQ_DISTRIBUTE=no
            tname = taskmanager.name
            self.datastore.save('job_info', {
                tname + '_sent': taskmanager.sent,
                tname + '_max_received_per_task': max(taskmanager.received),
                tname + '_tot_received': sum(taskmanager.received),
                tname + '_num_tasks': len(taskmanager.received)})

    def post_process(self):
        """For compatibility with the engine"""


class RiskCalculator(HazardCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .riskmodel, .sitecol, .assets_by_site, .exposure
    .riskinputs in the pre_execute phase.
    """
    extra_args = ()  # to be overridden in subclasses

    def check_poes(self, curves_by_trt_gsim):
        """Overridden in ClassicalDamage"""

    def make_eps(self, num_ruptures):
        """
        :param num_ruptures: the size of the epsilon array for each asset
        """
        oq = self.oqparam
        with self.monitor('building epsilons', autoflush=True):
            return riskinput.make_eps(
                self.assets_by_site, num_ruptures,
                oq.master_seed, oq.asset_correlation)

    def build_riskinputs(self, hazards_by_key, eps=numpy.zeros(0)):
        """
        :param hazards_by_key:
            a dictionary key -> IMT -> array of length num_sites
        :param eps:
            a matrix of epsilons (possibly empty)
        :returns:
            a list of RiskInputs objects, sorted by IMT.
        """
        self.check_poes(hazards_by_key)
        imtls = self.oqparam.imtls
        if not set(self.oqparam.risk_imtls) & set(imtls):
            rsk = ', '.join(self.oqparam.risk_imtls)
            haz = ', '.join(imtls)
            raise ValueError('The IMTs in the risk models (%s) are disjoint '
                             "from the IMTs in the hazard (%s)" % (rsk, haz))
        num_tasks = math.ceil((self.oqparam.concurrent_tasks or 1) /
                              len(imtls))
        with self.monitor('building riskinputs', autoflush=True):
            riskinputs = []
            idx_weight_pairs = [
                (i, len(assets))
                for i, assets in enumerate(self.assets_by_site)]
            blocks = general.split_in_blocks(
                idx_weight_pairs, num_tasks, weight=operator.itemgetter(1))
            for block in blocks:
                indices = numpy.array([idx for idx, _weight in block])
                reduced_assets = self.assets_by_site[indices]
                # dictionary of epsilons for the reduced assets
                reduced_eps = collections.defaultdict(F32)
                if len(eps):
                    for assets in reduced_assets:
                        for asset in assets:
                            reduced_eps[asset.ordinal] = eps[asset.ordinal]

                # collect the hazards by key into hazards by imt
                hdata = collections.defaultdict(lambda: [{} for _ in indices])
                for key, hazards_by_imt in hazards_by_key.items():
                    for imt in imtls:
                        hazards_by_site = hazards_by_imt[imt]
                        for i, haz in enumerate(hazards_by_site[indices]):
                            hdata[imt][i][key] = haz
                # build the riskinputs
                for imt in hdata:
                    ri = self.riskmodel.build_input(
                        imt, hdata[imt], reduced_assets, reduced_eps)
                    if ri.weight > 0:
                        riskinputs.append(ri)
            assert riskinputs
            logging.info('Built %d risk inputs', len(riskinputs))
            return sorted(riskinputs, key=self.riskinput_key)

    def riskinput_key(self, ri):
        """
        :param ri: riskinput object
        :returns: the IMT associated to it
        """
        return ri.imt

    def execute(self):
        """
        Parallelize on the riskinputs and returns a dictionary of results.
        Require a `.core_task` to be defined with signature
        (riskinputs, riskmodel, rlzs_assoc, monitor).
        """
        self.monitor.oqparam = self.oqparam
        rlz_ids = getattr(self.oqparam, 'rlz_ids', ())
        if rlz_ids:
            self.rlzs_assoc = self.rlzs_assoc.extract(rlz_ids)
        all_args = ((riskinput, self.riskmodel, self.rlzs_assoc) +
                    self.extra_args + (self.monitor,)
                    for riskinput in self.riskinputs)
        res = starmap(self.core_task.__func__, all_args).reduce()
        return res


@view.add('task_info')
def view_task_info(token, dstore):
    """
    Display statistical information about the tasks performance
    """
    pdata = dstore['performance_data'].value
    tasks = [calc.core_task.__name__ for calc in calculators.values()]
    data = ['measurement mean stddev min max num_tasks'.split()]
    for task in set(tasks):  # strip duplicates
        records = pdata[pdata['operation'] == 'total ' + task]
        if len(records):
            for stat in ('time_sec', 'memory_mb'):
                val = records[stat]
                data.append(stats(task + '.' + stat, val))
    if len(data) == 1:
        return 'Not available'
    return rst_table(data)
