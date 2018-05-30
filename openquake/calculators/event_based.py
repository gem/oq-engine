# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
import math
import os.path
import itertools
import logging
import collections
import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import zip
from openquake.baselib.general import (
    AccumDict, block_splitter, split_in_slices)
from openquake.hazardlib.calc.stochastic import sample_ruptures
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.risklib.riskinput import str2rsi, rsi2str, indices_dt
from openquake.baselib import parallel
from openquake.commonlib import calc, util, readinput
from openquake.calculators import base
from openquake.calculators.getters import GmfGetter, RuptureGetter
from openquake.calculators.classical import (
    ClassicalCalculator, saving_sources_by_task)

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64


def compute_ruptures(sources, src_filter, gsims, param, monitor):
    """
    :param sources:
        a sequence of sources of the same group
    :param src_filter:
        a source site filter
    :param gsims:
        a list of GSIMs for the current tectonic region model
    :param param:
        a dictionary of additional parameters
    :param monitor:
        monitor instance
    :returns:
        a dictionary src_group_id -> [Rupture instances]
    """
    # NB: by construction each block is a non-empty list with
    # sources of the same src_group_id
    grp_id = sources[0].src_group_id
    dic = sample_ruptures(sources, src_filter, gsims, param, monitor)
    res = AccumDict({grp_id: dic['eb_ruptures']})
    res.num_events = dic['num_events']
    res.calc_times = dic['calc_times']
    res.eff_ruptures = {grp_id: dic['num_ruptures']}
    return res


def get_events(ebruptures):
    """
    Extract an array of dtype stored_event_dt from a list of EBRuptures
    """
    events = []
    year = 0  # to be set later
    for ebr in ebruptures:
        for event in ebr.events:
            rec = (event['eid'], ebr.serial, ebr.grp_id, year, event['ses'],
                   event['sample'])
            events.append(rec)
    return numpy.array(events, readinput.stored_event_dt)


@base.calculators.add('event_based_rupture')
class EventBasedRuptureCalculator(base.HazardCalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_task = compute_ruptures
    is_stochastic = True

    def init(self):
        """
        Set the random seed passed to the SourceManager and the
        minimum_intensity dictionary.
        """
        oq = self.oqparam
        self.min_iml = self.get_min_iml(oq)
        self.rupser = calc.RuptureSerializer(self.datastore)

    def zerodict(self):
        """
        Initial accumulator, a dictionary (grp_id, gsim) -> curves
        """
        zd = AccumDict()
        zd.eff_ruptures = AccumDict()
        self.grp_trt = self.csm.info.grp_by("trt")
        return zd

    def agg_dicts(self, acc, ruptures_by_grp_id):
        """
        Accumulate dictionaries of ruptures and populate the `events`
        dataset in the datastore.

        :param acc: accumulator dictionary
        :param ruptures_by_grp_id: a nested dictionary grp_id -> ruptures
        """
        if hasattr(ruptures_by_grp_id, 'calc_times'):
            for srcid, nsites, eids, dt in ruptures_by_grp_id.calc_times:
                info = self.csm.infos[srcid]
                info.num_sites += nsites
                info.calc_time += dt
                info.num_split += 1
                info.events += len(eids)
        if hasattr(ruptures_by_grp_id, 'eff_ruptures'):
            acc.eff_ruptures += ruptures_by_grp_id.eff_ruptures
        acc += ruptures_by_grp_id
        self.save_ruptures(ruptures_by_grp_id)
        return acc

    def save_ruptures(self, ruptures_by_grp_id):
        """
        Extend the 'events' dataset with the events from the given ruptures;
        also, save the ruptures if the flag `save_ruptures` is on.

        :param ruptures_by_grp_id: a dictionary grp_id -> list of EBRuptures
        """
        with self.monitor('saving ruptures', autoflush=True):
            for grp_id, ebrs in ruptures_by_grp_id.items():
                if len(ebrs):
                    events = get_events(ebrs)
                    dset = self.datastore.extend('events', events)
                    if self.oqparam.save_ruptures:
                        self.rupser.save(ebrs, eidx=len(dset)-len(events))

    def gen_args(self, csm, monitor):
        """
        Used in the case of large source model logic trees.

        :param monitor: a :class:`openquake.baselib.performance.Monitor`
        :param csm: a reduced CompositeSourceModel
        :yields: (sources, sites, gsims, monitor) tuples
        """
        oq = self.oqparam

        def weight(src):
            return src.num_ruptures * src.RUPTURE_WEIGHT
        csm, src_filter = self.filter_csm()
        maxweight = csm.get_maxweight(weight, oq.concurrent_tasks or 1)
        logging.info('Using maxweight=%d', maxweight)
        param = dict(
            truncation_level=oq.truncation_level,
            imtls=oq.imtls, filter_distance=oq.filter_distance,
            seed=oq.ses_seed, maximum_distance=oq.maximum_distance,
            ses_per_logic_tree_path=oq.ses_per_logic_tree_path)

        num_tasks = 0
        num_sources = 0
        for sm in csm.source_models:
            for sg in sm.src_groups:
                gsims = csm.info.gsim_lt.get_gsims(sg.trt)
                csm.add_infos(sg.sources)
                if sg.src_interdep == 'mutex':  # do not split
                    sg.samples = sm.samples
                    yield sg, src_filter, gsims, param, monitor
                    num_tasks += 1
                    num_sources += len(sg.sources)
                    continue
                for block in block_splitter(sg.sources, maxweight, weight):
                    block.samples = sm.samples
                    yield block, src_filter, gsims, param, monitor
                    num_tasks += 1
                    num_sources += len(block)
        logging.info('Sent %d sources in %d tasks', num_sources, num_tasks)

    def execute(self):
        with self.monitor('managing sources', autoflush=True):
            allargs = self.gen_args(self.csm, self.monitor('classical'))
            iterargs = saving_sources_by_task(allargs, self.datastore)
            if isinstance(allargs, list):
                # there is a trick here: if the arguments are known
                # (a list, not an iterator), keep them as a list
                # then the Starmap will understand the case of a single
                # argument tuple and it will run in core the task
                iterargs = list(iterargs)
            acc = parallel.Starmap(self.core_task.__func__, iterargs).reduce(
                self.agg_dicts, self.zerodict())
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(self.csm.infos, acc)
        return acc

    def post_execute(self, result):
        """
        Save the SES collection
        """
        self.rupser.close()
        num_events = sum(set_counts(self.datastore, 'events').values())
        if num_events == 0:
            raise RuntimeError(
                'No seismic events! Perhaps the investigation time is too '
                'small or the maximum_distance is too small')
        num_ruptures = sum(len(ruptures) for ruptures in result.values())
        logging.info('Setting %d event years on %d ruptures',
                     num_events, num_ruptures)
        with self.monitor('setting event years', measuremem=True,
                          autoflush=True):
            numpy.random.seed(self.oqparam.ses_seed)
            set_random_years(self.datastore, 'events',
                             int(self.oqparam.investigation_time))


def set_counts(dstore, dsetname):
    """
    :param dstore: a DataStore instance
    :param dsetname: name of dataset with a field `grp_id`
    :returns: a dictionary grp_id > counts
    """
    groups = dstore[dsetname]['grp_id']
    unique, counts = numpy.unique(groups, return_counts=True)
    dic = dict(zip(unique, counts))
    dstore.set_attrs(dsetname, by_grp=sorted(dic.items()))
    return dic


def set_random_years(dstore, name, investigation_time):
    """
    Set on the `events` dataset year labels sensitive to the
    SES ordinal and the investigation time.

    :param dstore: a DataStore instance
    :param name: name of the dataset ('events')
    :param investigation_time: investigation time
    """
    events = dstore[name].value
    years = numpy.random.choice(investigation_time, len(events)) + 1
    year_of = dict(zip(numpy.sort(events['eid']), years))  # eid -> year
    for event in events:
        event['year'] = year_of[event['eid']]
    dstore[name] = events


# ######################## GMF calculator ############################ #


def compute_gmfs_and_curves(getters, oq, monitor):
    """
    :param getters:
        a list of GmfGetter instances
    :param oq:
        an OqParam instance
    :param monitor:
        a Monitor instance
    :returns:
        a list of dictionaries with keys gmfcoll and hcurves
    """
    results = []
    for getter in getters:
        with monitor('GmfGetter.init', measuremem=True):
            getter.init()
        hcurves = {}  # key -> poes
        if oq.hazard_curves_from_gmfs:
            hc_mon = monitor('building hazard curves', measuremem=False)
            duration = oq.investigation_time * oq.ses_per_logic_tree_path
            with monitor('building hazard', measuremem=True):
                gmfdata = numpy.fromiter(getter.gen_gmv(), getter.gmf_data_dt)
                hazard = getter.get_hazard(data=gmfdata)
            for sid, hazardr in zip(getter.sids, hazard):
                for rlzi, array in hazardr.items():
                    if len(array) == 0:  # no data
                        continue
                    with hc_mon:
                        gmvs = array['gmv']
                        for imti, imt in enumerate(getter.imtls):
                            poes = calc._gmvs_to_haz_curve(
                                gmvs[:, imti], oq.imtls[imt],
                                oq.investigation_time, duration)
                            hcurves[rsi2str(rlzi, sid, imt)] = poes
        else:  # fast lane
            with monitor('building hazard', measuremem=True):
                gmfdata = numpy.fromiter(getter.gen_gmv(), getter.gmf_data_dt)
        indices = []
        if oq.ground_motion_fields:
            gmfdata.sort(order=('sid', 'rlzi', 'eid'))
            start = stop = 0
            for sid, rows in itertools.groupby(gmfdata['sid']):
                for row in rows:
                    stop += 1
                indices.append((sid, start, stop))
                start = stop
        else:
            gmfdata = None
        res = dict(gmfdata=gmfdata, hcurves=hcurves, gmdata=getter.gmdata,
                   indices=numpy.array(indices, (U32, 3)))
        if len(getter.gmdata):
            results.append(res)
    return results


def update_nbytes(dstore, key, array):
    nbytes = dstore.get_attr(key, 'nbytes', 0)
    dstore.set_attrs(key, nbytes=nbytes + array.nbytes)


@base.calculators.add('event_based')
class EventBasedCalculator(base.HazardCalculator):
    """
    Event based PSHA calculator generating the ground motion fields and
    the hazard curves from the ruptures, depending on the configuration
    parameters.
    """
    pre_calculator = 'event_based_rupture'
    core_task = compute_gmfs_and_curves
    is_stochastic = True

    def combine_pmaps_and_save_gmfs(self, acc, results):
        """
        Combine the hazard curves (if any) and save the gmfs (if any)
        sequentially; notice that the gmfs may come from
        different tasks in any order.

        :param acc: an accumulator for the hazard curves
        :param results: dictionaries rlzi, imt -> [gmf_array, curves_by_imt]
        :returns: a new accumulator
        """
        sav_mon = self.monitor('saving gmfs')
        agg_mon = self.monitor('aggregating hcurves')
        hdf5path = self.datastore.hdf5path
        for res in results:
            self.gmdata += res['gmdata']
            data = res['gmfdata']
            if data is not None:
                with sav_mon:
                    hdf5.extend3(hdf5path, 'gmf_data/data', data)
                    # it is important to save the number of bytes while the
                    # computation is going, to see the progress
                    update_nbytes(self.datastore, 'gmf_data/data', data)
                    for sid, start, stop in res['indices']:
                        self.indices[sid].append(
                            (start + self.offset, stop + self.offset))
                    self.offset += len(data)
            slicedic = self.oqparam.imtls.slicedic
            with agg_mon:
                for key, poes in res['hcurves'].items():
                    r, sid, imt = str2rsi(key)
                    array = acc[r].setdefault(sid, 0).array[slicedic[imt], 0]
                    array[:] = 1. - (1. - array) * (1. - poes)
            sav_mon.flush()
            agg_mon.flush()
            self.datastore.flush()
            if 'ruptures' in res:
                vars(EventBasedRuptureCalculator)['save_ruptures'](
                    self, res['ruptures'])
        return acc

    def gen_args(self):
        """
        :yields: the arguments for compute_gmfs_and_curves
        """
        oq = self.oqparam
        sitecol = self.sitecol.complete
        monitor = self.monitor(self.core_task.__name__)
        imts = list(oq.imtls)
        min_iml = self.get_min_iml(oq)
        correl_model = oq.get_correl_model()
        try:
            csm_info = self.csm.info
        except AttributeError:  # no csm
            csm_info = self.datastore['csm_info']
        samples_by_grp = csm_info.get_samples_by_grp()
        rlzs_by_gsim = {grp_id: self.rlzs_assoc.get_rlzs_by_gsim(grp_id)
                        for grp_id in samples_by_grp}
        if self.precalc:
            num_ruptures = sum(len(rs) for rs in self.precalc.result.values())
            block_size = math.ceil(num_ruptures / (oq.concurrent_tasks or 1))
            for grp_id, ruptures in self.precalc.result.items():
                if not ruptures:
                    continue
                for block in block_splitter(ruptures, block_size):
                    getter = GmfGetter(
                        rlzs_by_gsim[grp_id], block, sitecol,
                        imts, min_iml, oq.maximum_distance,
                        oq.truncation_level, correl_model,
                        oq.filter_distance, samples_by_grp[grp_id])
                    yield [getter], oq, monitor
            return
        U = len(self.datastore['ruptures'])
        logging.info('Found %d ruptures', U)
        parent = self.can_read_parent() or self.datastore
        for slc in split_in_slices(U, oq.concurrent_tasks or 1):
            getters = []
            for grp_id in rlzs_by_gsim:
                ruptures = RuptureGetter(parent, slc, grp_id)
                if parent is self.datastore:  # not accessible parent
                    ruptures = list(ruptures)
                    if not ruptures:
                        continue
                getters.append(GmfGetter(
                    rlzs_by_gsim[grp_id], ruptures, sitecol,
                    imts, min_iml, oq.maximum_distance, oq.truncation_level,
                    correl_model, oq.filter_distance, samples_by_grp[grp_id]))
            yield getters, oq, monitor

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the ruptures according to their weight and
        tectonic region type.
        """
        oq = self.oqparam
        if not oq.hazard_curves_from_gmfs and not oq.ground_motion_fields:
            return
        if self.oqparam.ground_motion_fields:
            calc.check_overflow(self)

        self.csm_info = self.datastore['csm_info']
        self.sm_id = {tuple(sm.path): sm.ordinal
                      for sm in self.csm_info.source_models}
        L = len(oq.imtls.array)
        R = self.datastore['csm_info'].get_num_rlzs()
        self.gmdata = {}
        self.offset = 0
        self.indices = collections.defaultdict(list)  # sid -> indices
        ires = parallel.Starmap(
            self.core_task.__func__, self.gen_args()).submit_all()
        if self.precalc and self.precalc.result:
            # remove the ruptures in memory to save memory
            self.precalc.result.clear()
        acc = ires.reduce(self.combine_pmaps_and_save_gmfs, {
            r: ProbabilityMap(L) for r in range(R)})
        base.save_gmdata(self, R)
        if self.indices:
            logging.info('Saving gmf_data/indices')
            with self.monitor('saving gmf_data/indices', measuremem=True,
                              autoflush=True):
                self.datastore.save_vlen(
                    'gmf_data/indices',
                    [numpy.array(self.indices[sid], indices_dt)
                     for sid in self.sitecol.complete.sids])
        return acc

    def save_gmf_bytes(self):
        """Save the attribute nbytes in the gmf_data datasets"""
        ds = self.datastore
        for sm_id in ds['gmf_data']:
            ds.set_nbytes('gmf_data/' + sm_id)
        ds.set_nbytes('gmf_data')

    def post_execute(self, result):
        """
        :param result:
            a dictionary (src_group_id, gsim) -> haz_curves or an empty
            dictionary if hazard_curves_from_gmfs is false
        """
        oq = self.oqparam
        if not oq.hazard_curves_from_gmfs and not oq.ground_motion_fields:
            return
        elif oq.hazard_curves_from_gmfs:
            rlzs = self.rlzs_assoc.realizations
            # save individual curves
            for i in sorted(result):
                key = 'hcurves/rlz-%03d' % i
                if result[i]:
                    self.datastore[key] = result[i]
                else:
                    self.datastore[key] = ProbabilityMap(oq.imtls.array.size)
                    logging.info('Zero curves for %s', key)
            # compute and save statistics; this is done in process and can
            # be very slow if there are thousands of realizations
            weights = [rlz.weight for rlz in rlzs]
            hstats = self.oqparam.hazard_stats()
            if len(hstats) and len(rlzs) > 1:
                logging.info('Computing statistical hazard curves')
                for kind, stat in hstats:
                    pmap = compute_pmap_stats(result.values(), [stat], weights)
                    self.datastore['hcurves/' + kind] = pmap
        if self.datastore.parent:
            self.datastore.parent.open()
        if 'gmf_data' in self.datastore:
            self.save_gmf_bytes()
        if oq.compare_with_classical:  # compute classical curves
            export_dir = os.path.join(oq.export_dir, 'cl')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            oq.export_dir = export_dir
            # one could also set oq.number_of_logic_tree_samples = 0
            self.cl = ClassicalCalculator(oq)
            # TODO: perhaps it is possible to avoid reprocessing the source
            # model, however usually this is quite fast and do not dominate
            # the computation
            self.cl.run(close=False)
            cl_mean_curves = get_mean_curves(self.cl.datastore)
            eb_mean_curves = get_mean_curves(self.datastore)
            for imt in eb_mean_curves.dtype.names:
                rdiff, index = util.max_rel_diff_index(
                    cl_mean_curves[imt], eb_mean_curves[imt])
                logging.warn('Relative difference with the classical '
                             'mean curves for IMT=%s: %d%% at site index %d',
                             imt, rdiff * 100, index)


def get_mean_curves(dstore):
    """
    Extract the mean hazard curves from the datastore, as a composite
    array of length nsites.
    """
    imtls = dstore['oqparam'].imtls
    nsites = len(dstore['sitecol'])
    hcurves = dstore['hcurves']
    if 'mean' in hcurves:
        mean = dstore['hcurves/mean']
    elif len(hcurves) == 1:  # there is a single realization
        mean = dstore['hcurves/rlz-0000']
    return mean.convert(imtls, nsites)
