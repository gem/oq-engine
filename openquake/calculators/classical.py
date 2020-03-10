# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
import time
import logging
import operator
from datetime import datetime
import numpy

from openquake.baselib import parallel, hdf5
from openquake.baselib.general import AccumDict, block_splitter
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib.calc.filters import split_sources
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.commonlib import calc, util, logs
from openquake.commonlib.source_reader import random_filtered_sources
from openquake.calculators import getters
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
MINWEIGHT = 1000
weight = operator.attrgetter('weight')
grp_extreme_dt = numpy.dtype([('grp_id', U16), ('grp_trt', hdf5.vstr),
                             ('extreme_poe', F32)])


def get_extreme_poe(array, imtls):
    """
    :param array: array of shape (L, G) with L=num_levels, G=num_gsims
    :param imtls: DictArray imt -> levels
    :returns:
        the maximum PoE corresponding to the maximum level for IMTs and GSIMs
    """
    return max(array[imtls(imt).stop - 1].max() for imt in imtls)


def classical_split_filter(srcs, srcfilter, gsims, params, monitor):
    """
    Split the given sources, filter the subsources and the compute the
    PoEs. Yield back subtasks if the split sources contain more than
    maxweight ruptures.
    """
    # first check if we are sampling the sources
    ss = int(os.environ.get('OQ_SAMPLE_SOURCES', 0))
    if ss:
        splits, stime = split_sources(srcs)
        srcs = random_filtered_sources(splits, srcfilter, ss)
        yield classical(srcs, srcfilter, gsims, params, monitor)
        return
    # NB: splitting all the sources improves the distribution significantly,
    # compared to splitting only the big sources
    with monitor("splitting/filtering sources"):
        splits, _stime = split_sources(srcs)
        sources = list(srcfilter.filter(splits))
    if not sources:
        yield {'pmap': {}}
        return
    maxw = min(sum(src.weight for src in sources)/5, params['max_weight'])
    if maxw < MINWEIGHT*5:  # task too small to be resubmitted
        yield classical(sources, srcfilter, gsims, params, monitor)
        return
    blocks = list(block_splitter(sources, maxw, weight))
    subtasks = len(blocks) - 1
    for block in blocks[:-1]:
        yield classical, block, srcfilter, gsims, params
    if monitor.calc_id and subtasks:
        msg = 'produced %d subtask(s) with max weight=%d' % (
            subtasks, max(b.weight for b in blocks))
        try:
            logs.dbcmd('log', monitor.calc_id, datetime.utcnow(), 'DEBUG',
                       'classical_split_filter#%d' % monitor.task_no, msg)
        except Exception:
            # a foreign key error in case of `oq run` is expected
            print(msg)
    yield classical(blocks[-1], srcfilter, gsims, params, monitor)


def preclassical(srcs, srcfilter, gsims, params, monitor):
    """
    Split and prefilter the sources
    """
    calc_times = AccumDict(accum=numpy.zeros(3, F32))  # nrups, nsites, time
    pmap = AccumDict(accum=0)
    with monitor("splitting/filtering sources"):
        splits, _stime = split_sources(srcs)
    for src in splits:
        t0 = time.time()
        if srcfilter.get_close_sites(src) is None:
            continue
        dt = time.time() - t0
        calc_times[src.id] += F32([src.num_ruptures, src.nsites, dt])
        for grp_id in src.grp_ids:
            pmap[grp_id] += 0
    return dict(pmap=pmap, calc_times=calc_times, rup_data={'grp_id': []},
                extra=dict(task_no=monitor.task_no, totrups=src.num_ruptures,
                           trt=src.tectonic_region_type))


@base.calculators.add('classical', 'ucerf_classical')
class ClassicalCalculator(base.HazardCalculator):
    """
    Classical PSHA calculator
    """
    core_task = classical_split_filter
    accept_precalc = ['classical']

    def agg_dicts(self, acc, dic):
        """
        Aggregate dictionaries of hazard curves by updating the accumulator.

        :param acc: accumulator dictionary
        :param dic: dict with keys pmap, calc_times, rup_data
        """
        # NB: dic should be a dictionary, but when the calculation dies
        # for an OOM it can become None, thus giving a very confusing error
        if dic is None:
            raise MemoryError('You ran out of memory!')
        if not dic['pmap']:
            return acc
        trt = dic['extra'].pop('trt')
        with self.monitor('aggregate curves'):
            extra = dic['extra']
            self.totrups += extra['totrups']
            d = dic['calc_times']  # srcid -> eff_rups, eff_sites, dt
            self.calc_times += d
            srcids = []
            eff_rups = 0
            eff_sites = 0
            for srcid, rec in d.items():
                srcids.append(srcid)
                eff_rups += rec[0]
                if rec[0]:
                    eff_sites += rec[1] / rec[0]
            self.by_task[extra['task_no']] = (
                eff_rups, eff_sites, U32(srcids))
            for grp_id, pmap in dic['pmap'].items():
                if pmap:
                    acc[grp_id] |= pmap
                acc.eff_ruptures[trt] += eff_rups

            rup_data = dic['rup_data']
            nr = len(rup_data['grp_id'])
            if nr:
                default = (numpy.ones(nr, F32) * numpy.nan,
                           [numpy.zeros(0, F32)] * nr)
                for k in self.rparams:
                    # variable lenght arrays
                    vlen = k.endswith('_') or k == 'probs_occur'
                    try:
                        v = rup_data[k]
                    except KeyError:
                        v = default[vlen]
                    if vlen:
                        self.datastore.hdf5.save_vlen('rup/' + k, v)
                    else:
                        dset = self.datastore['rup/' + k]
                        hdf5.extend(dset, v)
        return acc

    def acc0(self):
        """
        Initial accumulator, a dict grp_id -> ProbabilityMap(L, G)
        """
        zd = AccumDict()
        num_levels = len(self.oqparam.imtls.array)
        rparams = {'grp_id', 'occurrence_rate',
                   'weight', 'probs_occur', 'sid_', 'lon_', 'lat_', 'rrup_'}
        gsims_by_trt = self.csm_info.get_gsims_by_trt()
        n = len(self.csm_info.sm_rlzs)
        trts = list(self.csm_info.gsim_lt.values)
        for sm in self.csm_info.sm_rlzs:
            for grp_id in self.csm_info.grp_ids(sm.ordinal):
                trt = trts[grp_id // n]
                gsims = gsims_by_trt[trt]
                cm = ContextMaker(trt, gsims)
                rparams.update(cm.REQUIRES_RUPTURE_PARAMETERS)
                for dparam in cm.REQUIRES_DISTANCES:
                    rparams.add(dparam + '_')
                zd[grp_id] = ProbabilityMap(num_levels, len(gsims))
        zd.eff_ruptures = AccumDict(accum=0)  # trt -> eff_ruptures
        self.rparams = sorted(rparams)
        for k in self.rparams:
            # variable length arrays
            vlen = k.endswith('_') or k == 'probs_occur'
            if k == 'grp_id':
                dt = U16
            elif k == 'sid_':
                dt = hdf5.vuint16
            elif vlen:
                dt = hdf5.vfloat32
            else:
                dt = F32
            self.datastore.create_dset('rup/' + k, dt)
        self.by_task = {}  # task_no => src_ids
        self.totrups = 0  # total number of ruptures before collapsing
        return zd

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        oq = self.oqparam
        if oq.hazard_calculation_id and not oq.compare_with_classical:
            with util.read(self.oqparam.hazard_calculation_id) as parent:
                self.csm_info = parent['csm_info']
            self.calc_stats()  # post-processing
            return {}

        mags = self.datastore['source_mags'][()]
        if len(mags) == 0:  # everything was discarded
            raise RuntimeError('All sources were discarded!?')
        gsims_by_trt = self.csm_info.get_gsims_by_trt()
        if 'source_mags' in self.datastore and oq.imtls:
            mags = self.datastore['source_mags'][()]
            self.datastore['effect_by_mag_dst_trt'] = calc.get_effect(
                mags, self.sitecol, gsims_by_trt, oq)
        smap = parallel.Starmap(
            self.core_task.__func__, h5=self.datastore.hdf5,
            num_cores=oq.num_cores)
        smap.task_queue = list(self.gen_task_queue())  # really fast
        acc0 = self.acc0()  # create the rup/ datasets BEFORE swmr_on()
        self.datastore.swmr_on()
        smap.h5 = self.datastore.hdf5
        self.calc_times = AccumDict(accum=numpy.zeros(3, F32))
        try:
            acc = smap.get_results().reduce(self.agg_dicts, acc0)
            self.store_rlz_info(acc.eff_ruptures)
        finally:
            with self.monitor('store source_info'):
                self.store_source_info(self.calc_times)
            if self.by_task:
                logging.info('Storing by_task information')
                num_tasks = max(self.by_task) + 1,
                er = self.datastore.create_dset('by_task/eff_ruptures',
                                                U32, num_tasks)
                es = self.datastore.create_dset('by_task/eff_sites',
                                                U32, num_tasks)
                si = self.datastore.create_dset('by_task/srcids',
                                                hdf5.vuint32, num_tasks,
                                                fillvalue=None)
                for task_no, rec in self.by_task.items():
                    effrups, effsites, srcids = rec
                    er[task_no] = effrups
                    es[task_no] = effsites
                    si[task_no] = srcids
                self.by_task.clear()
        self.numrups = sum(arr[0] for arr in self.calc_times.values())
        numsites = sum(arr[1] for arr in self.calc_times.values())
        logging.info('Effective number of ruptures: %d/%d',
                     self.numrups, self.totrups)
        logging.info('Effective number of sites per rupture: %d',
                     numsites / self.numrups)
        self.calc_times.clear()  # save a bit of memory
        return acc

    def gen_task_queue(self):
        """
        Build a task queue to be attached to the Starmap instance
        """
        oq = self.oqparam
        gsims_by_trt = self.csm_info.get_gsims_by_trt()
        src_groups = self.csm.src_groups

        def srcweight(src):
            trt = src.tectonic_region_type
            g = len(gsims_by_trt[trt])
            m = (oq.maximum_distance(trt) / 300) ** 2
            return src.weight * g * m

        totweight = sum(sum(srcweight(src) for src in sg) for sg in src_groups)
        param = dict(
            truncation_level=oq.truncation_level, imtls=oq.imtls,
            filter_distance=oq.filter_distance, reqv=oq.get_reqv(),
            maximum_distance=oq.maximum_distance,
            pointsource_distance=oq.pointsource_distance,
            shift_hypo=oq.shift_hypo, max_weight=oq.max_weight,
            max_sites_disagg=oq.max_sites_disagg)
        srcfilter = self.src_filter(self.datastore.tempname)
        if oq.calculation_mode == 'preclassical':
            f1 = f2 = preclassical
        else:
            f1, f2 = classical, classical_split_filter
        C = oq.concurrent_tasks or 1
        for sg in src_groups:
            gsims = gsims_by_trt[sg.trt]
            if sg.atomic:
                # do not split atomic groups
                nb = 1
                yield f1, (sg, srcfilter, gsims, param)
            else:  # regroup the sources in blocks
                blocks = list(block_splitter(sg, totweight/C, srcweight))
                nb = len(blocks)
                for block in blocks:
                    logging.debug('Sending %d source(s) with weight %d',
                                  len(block), block.weight)
                    yield f2, (block, srcfilter, gsims, param)

            nr = sum(src.weight for src in sg)
            logging.info('TRT = %s', sg.trt)
            if oq.maximum_distance.magdist:
                md = ', '.join('%s->%d' % item for item in sorted(
                    oq.maximum_distance.magdist[sg.trt].items()))
            else:
                md = oq.maximum_distance(sg.trt)
            logging.info('max_dist=%s, gsims=%d, ruptures=%d, blocks=%d',
                         md, len(gsims), nr, nb)
            if oq.pointsource_distance['default']:
                pd = ', '.join('%s->%d' % item for item in sorted(
                    oq.pointsource_distance[sg.trt].items()))
                logging.info('ps_dist=%s', pd)

    def save_hazard(self, acc, pmap_by_kind):
        """
        Works by side effect by saving hcurves and hmaps on the datastore

        :param acc: ignored
        :param pmap_by_kind: a dictionary of ProbabilityMaps

        kind can be ('hcurves', 'mean'), ('hmaps', 'mean'),  ...
        """
        with self.monitor('saving statistics'):
            for kind in pmap_by_kind:  # i.e. kind == 'hcurves-stats'
                pmaps = pmap_by_kind[kind]
                if kind in ('hmaps-rlzs', 'hmaps-stats'):
                    # pmaps is a list of R pmaps
                    dset = self.datastore.getitem(kind)
                    for r, pmap in enumerate(pmaps):
                        for s in pmap:
                            dset[s, r] = pmap[s].array  # shape (M, P)
                elif kind in ('hcurves-rlzs', 'hcurves-stats'):
                    dset = self.datastore.getitem(kind)
                    for r, pmap in enumerate(pmaps):
                        for s in pmap:
                            dset[s, r] = pmap[s].array[:, 0]  # shape L
            self.datastore.flush()

    def post_execute(self, pmap_by_grp_id):
        """
        Collect the hazard curves by realization and export them.

        :param pmap_by_grp_id:
            a dictionary grp_id -> hazard curves
        """
        oq = self.oqparam
        trt_by_grp = self.csm_info.trt_by_grp
        data = []
        with self.monitor('saving probability maps'):
            for grp_id, pmap in pmap_by_grp_id.items():
                if pmap:  # pmap can be missing if the group is filtered away
                    base.fix_ones(pmap)  # avoid saving PoEs == 1
                    trt = trt_by_grp[grp_id]
                    key = 'poes/grp-%02d' % grp_id
                    self.datastore[key] = pmap
                    self.datastore.set_attrs(key, trt=trt)
                    extreme = max(
                        get_extreme_poe(pmap[sid].array, oq.imtls)
                        for sid in pmap)
                    data.append((grp_id, trt_by_grp[grp_id], extreme))
        if oq.hazard_calculation_id is None and 'poes' in self.datastore:
            self.datastore['disagg_by_grp'] = numpy.array(
                sorted(data), grp_extreme_dt)
            self.calc_stats()

    def calc_stats(self):
        oq = self.oqparam
        hstats = oq.hazard_stats()
        # initialize datasets
        N = len(self.sitecol.complete)
        P = len(oq.poes)
        M = len(oq.imtls)
        if oq.soil_intensities is not None:
            L = M * len(oq.soil_intensities)
        else:
            L = len(oq.imtls.array)
        R = len(self.realizations)
        S = len(hstats)
        if R > 1 and oq.individual_curves or not hstats:
            self.datastore.create_dset('hcurves-rlzs', F32, (N, R, L))
            if oq.poes:
                self.datastore.create_dset('hmaps-rlzs', F32, (N, R, M, P))
        if hstats:
            self.datastore.create_dset('hcurves-stats', F32, (N, S, L))
            if oq.poes:
                self.datastore.create_dset('hmaps-stats', F32, (N, S, M, P))
        ct = oq.concurrent_tasks
        logging.info('Building hazard statistics with %d concurrent_tasks', ct)
        weights = [rlz.weight for rlz in self.realizations]
        allargs = [  # this list is very fast to generate
            (getters.PmapGetter(self.datastore, weights, t.sids, oq.poes),
             N, hstats, oq.individual_curves, oq.max_sites_disagg,
             self.amplifier)
            for t in self.sitecol.split_in_tiles(ct)]
        if N <= oq.max_sites_disagg:  # few sites
            dist = 'no'
        else:
            dist = None  # parallelize as usual
            self.datastore.swmr_on()
        parallel.Starmap(
            build_hazard, allargs, distribute=dist, h5=self.datastore.hdf5
        ).reduce(self.save_hazard)


@base.calculators.add('preclassical')
class PreCalculator(ClassicalCalculator):
    """
    Calculator to filter the sources and compute the number of effective
    ruptures
    """
    core_task = preclassical


def build_hazard(pgetter, N, hstats, individual_curves,
                 max_sites_disagg, amplifier, monitor):
    """
    :param pgetter: an :class:`openquake.commonlib.getters.PmapGetter`
    :param N: the total number of sites
    :param hstats: a list of pairs (statname, statfunc)
    :param individual_curves: if True, also build the individual curves
    :param max_sites_disagg: if there are less sites than this, store rup info
    :param amplifier: instance of Amplifier or None
    :param monitor: instance of Monitor
    :returns: a dictionary kind -> ProbabilityMap

    The "kind" is a string of the form 'rlz-XXX' or 'mean' of 'quantile-XXX'
    used to specify the kind of output.
    """
    with monitor('read PoEs'):
        pgetter.init()
        if amplifier:
            ampcode = pgetter.dstore['sitecol'].ampcode
    imtls, poes, weights = pgetter.imtls, pgetter.poes, pgetter.weights
    M = len(imtls)
    L = len(imtls.array) if amplifier is None else len(amplifier.amplevels) * M
    R = len(weights)
    S = len(hstats)
    pmap_by_kind = {}
    if R > 1 and individual_curves or not hstats:
        pmap_by_kind['hcurves-rlzs'] = [ProbabilityMap(L) for r in range(R)]
    if hstats:
        pmap_by_kind['hcurves-stats'] = [ProbabilityMap(L) for r in range(S)]
        if poes:
            pmap_by_kind['hmaps-stats'] = [ProbabilityMap(L) for r in range(S)]
    combine_mon = monitor('combine pmaps', measuremem=False)
    compute_mon = monitor('compute stats', measuremem=False)
    for sid in pgetter.sids:
        with combine_mon:
            pcurves = pgetter.get_pcurves(sid)
            if amplifier:
                pcurves = amplifier.amplify(ampcode[sid], pcurves)
        if sum(pc.array.sum() for pc in pcurves) == 0:  # no data
            continue
        with compute_mon:
            if hstats:
                arr = numpy.array([pc.array for pc in pcurves])
                for s, (statname, stat) in enumerate(hstats.items()):
                    pc = getters.build_stat_curve(arr, imtls, stat, weights)
                    pmap_by_kind['hcurves-stats'][s][sid] = pc
                    if poes:
                        hmap = calc.make_hmap(pc, pgetter.imtls, poes, sid)
                        pmap_by_kind['hmaps-stats'][s].update(hmap)
            if R > 1 and individual_curves or not hstats:
                for pmap, pc in zip(pmap_by_kind['hcurves-rlzs'], pcurves):
                    pmap[sid] = pc
                if poes:
                    pmap_by_kind['hmaps-rlzs'] = [
                        calc.make_hmap(pc, imtls, poes, sid) for pc in pcurves]
    return pmap_by_kind
