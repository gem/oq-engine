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
import time
import logging
import operator
import numpy

from openquake.baselib import parallel, hdf5
from openquake.baselib.general import AccumDict, block_splitter
from openquake.hazardlib.contexts import FEWSITES
from openquake.hazardlib.calc.filters import split_sources
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.hazardlib.probability_map import (
    ProbabilityMap, ProbabilityCurve)
from openquake.commonlib import calc, util
from openquake.commonlib.source_model_factory import random_filtered_sources
from openquake.calculators import getters
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
weight = operator.attrgetter('weight')
grp_extreme_dt = numpy.dtype([('grp_id', U16), ('grp_name', hdf5.vstr),
                             ('extreme_poe', F32)])
source_data_dt = numpy.dtype(
    [('taskno', U16), ('src_id', U32), ('nsites', U32), ('nruptures', U32),
     ('weight', F32)])


def get_src_ids(sources):
    """
    :returns:
       a string with the source IDs of the given sources, stripping the
       extension after the colon, if any
    """
    src_ids = []
    for src in sources:
        long_src_id = src.source_id
        try:
            src_id, ext = long_src_id.rsplit(':', 1)
        except ValueError:
            src_id = long_src_id
        src_ids.append(src_id)
    return ' '.join(set(src_ids))


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
    # compared to splitting only the big source
    sources = []
    with monitor("filtering/splitting sources"):
        for src, _sites in srcfilter(srcs):
            splits, _stime = split_sources([src])
            sources.extend(srcfilter.filter(splits))
    if sources:
        tot = 0
        sd = AccumDict(accum=numpy.zeros(3))  # nsites, nrupts, weight
        for src in sources:
            arr = numpy.array([src.nsites, src.num_ruptures, src.weight])
            sd[src.id] += arr
            tot += 1
        source_data = numpy.array([(monitor.task_no, src_id, s/tot, r, w)
                                   for src_id, (s, r, w) in sd.items()],
                                  source_data_dt)
        first = True
        for out in parallel.split_task(
                classical, sources, srcfilter, gsims, params, monitor,
                duration=params['task_duration']):
            if first:
                out['source_data'] = source_data
                first = False
            yield out


def preclassical(srcs, srcfilter, gsims, params, monitor):
    """
    Prefilter the sources
    """
    eff_ruptures = AccumDict(accum=0)   # grp_id -> num_ruptures
    calc_times = AccumDict(accum=numpy.zeros(2, F32))  # weight, time
    nsites = {}
    for src in srcs:
        t0 = time.time()
        if srcfilter.get_close_sites(src) is None:
            continue
        for grp_id in src.src_group_ids:
            eff_ruptures[grp_id] += src.num_ruptures
        dt = time.time() - t0
        calc_times[src.id] += numpy.array([src.weight, dt], F32)
        nsites[src.id] = src.nsites
    return dict(pmap={}, calc_times=calc_times, eff_ruptures=eff_ruptures,
                rup_data={}, nsites=nsites)


@base.calculators.add('classical')
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
        :param dic: dict with keys pmap, calc_times, eff_ruptures, rup_data
        """
        with self.monitor('aggregate curves', autoflush=True):
            acc.nsites.update(dic['nsites'])
            acc.eff_ruptures += dic['eff_ruptures']
            self.calc_times += dic['calc_times']
            for grp_id, pmap in dic['pmap'].items():
                if pmap:
                    acc[grp_id] |= pmap
            for grp_id, data in dic['rup_data'].items():
                if len(data):
                    self.datastore.extend('rup/grp-%02d' % grp_id, data)
            if 'source_data' in dic:
                self.datastore.extend('source_data', dic['source_data'])
        return acc

    def acc0(self):
        """
        Initial accumulator, a dict grp_id -> ProbabilityMap(L, G)
        """
        csm_info = self.csm.info
        zd = AccumDict()
        num_levels = len(self.oqparam.imtls.array)
        for grp in self.csm.src_groups:
            num_gsims = len(csm_info.gsim_lt.get_gsims(grp.trt))
            zd[grp.id] = ProbabilityMap(num_levels, num_gsims)
        zd.eff_ruptures = AccumDict()  # grp_id -> eff_ruptures
        zd.nsites = AccumDict()  # src.id -> nsites
        return zd

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        oq = self.oqparam
        if oq.hazard_calculation_id and not oq.compare_with_classical:
            parent = util.read(self.oqparam.hazard_calculation_id)
            self.csm_info = parent['csm_info']
            parent.close()
            self.calc_stats(parent)  # post-processing
            return {}
        # TODO: enable integration_distance when implemented correctly
        # try:
        #     self.src_filter.integration_distance = self.datastore[
        #        'integration_distance']
        # except KeyError:
        #     logging.warn('No integration_distance')
        with self.monitor('managing sources', autoflush=True):
            smap = parallel.Starmap(
                self.core_task.__func__, monitor=self.monitor())
            self.submit_sources(smap)
        self.calc_times = AccumDict(accum=numpy.zeros(2, F32))
        try:
            acc = smap.reduce(self.agg_dicts, self.acc0())
            self.store_rlz_info(acc.eff_ruptures)
        finally:
            with self.monitor('store source_info', autoflush=True):
                self.store_source_info(self.calc_times)
        if acc.nsites:
            if len(acc.nsites) > 100000:
                # not saving source_info.num_sites since it would be slow:
                # we do not want to wait hours for unused information
                logging.warn(
                    'There are %d contributing sources', len(acc.nsites))
            else:
                logging.info('Saving source_info.num_sites for %d sources',
                             len(acc.nsites))
                src_ids = sorted(acc.nsites)
                nsites = [acc.nsites[i] for i in src_ids]
                self.datastore['source_info'][src_ids, 'num_sites'] = nsites
        if not self.calc_times:
            raise RuntimeError('All sources were filtered away!')
        self.calc_times.clear()  # save a bit of memory
        return acc

    def submit_sources(self, smap):
        """
        Send the sources split in tasks
        """
        oq = self.oqparam
        N, L = len(self.sitecol), len(oq.imtls.array)
        trt_sources = self.csm.get_trt_sources(optimize_dupl=True)
        maxweight = min(self.csm.get_maxweight(
            trt_sources, weight, oq.concurrent_tasks), 1E6)
        if oq.task_duration is None:  # inferred
            # from 1 minute up to 6 hours
            td = max((maxweight * N * L) ** numpy.log10(4) / 3000, 60)
        else:  # user given
            td = oq.task_duration
        param = dict(
            truncation_level=oq.truncation_level, imtls=oq.imtls,
            filter_distance=oq.filter_distance, reqv=oq.get_reqv(),
            pointsource_distance=oq.pointsource_distance,
            task_duration=td, maxweight=maxweight)
        logging.info('ruptures_per_task = %(maxweight)d, '
                     'task_duration = %(task_duration)ds', param)

        for trt, sources in trt_sources:
            heavy_sources = []
            gsims = self.csm.info.gsim_lt.get_gsims(trt)
            if hasattr(sources, 'atomic') and sources.atomic:
                smap.submit(sources, self.src_filter, gsims, param,
                            func=classical)
            else:  # regroup the sources in blocks
                for block in block_splitter(sources, maxweight, weight):
                    if block.weight > maxweight:
                        heavy_sources.extend(block)
                    smap.submit(block, self.src_filter, gsims, param)

            # heavy source are split on the master node
            if heavy_sources:
                logging.info('Found %d heavy sources %s, ...',
                             len(heavy_sources), heavy_sources[0])

    def save_hazard_stats(self, acc, pmap_by_kind):
        """
        Works by side effect by saving statistical hcurves and hmaps on the
        datastore.

        :param acc: ignored
        :param pmap_by_kind: a dictionary of ProbabilityMaps

        kind can be ('hcurves', 'mean'), ('hmaps', 'mean'),  ...
        """
        with self.monitor('saving statistics', autoflush=True):
            for kind in pmap_by_kind:  # i.e. kind == 'hcurves-stats'
                pmaps = pmap_by_kind[kind]
                if kind == 'rlz_by_sid':  # pmaps is actually a rlz_by_sid
                    for sid, rlz in pmaps.items():
                        self.datastore['best_rlz'][sid] = rlz
                elif kind in ('hmaps-rlzs', 'hmaps-stats'):
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
        try:
            csm_info = self.csm.info
        except AttributeError:
            csm_info = self.datastore['csm_info']
        trt_by_grp = csm_info.grp_by("trt")
        grp_name = {grp.id: grp.name for sm in csm_info.source_models
                    for grp in sm.src_groups}
        data = []
        with self.monitor('saving probability maps', autoflush=True):
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
                    data.append((grp_id, grp_name[grp_id], extreme))
                    if 'rup' in set(self.datastore):
                        self.datastore.set_nbytes('rup/grp-%02d' % grp_id)
                        tot_ruptures = sum(
                            len(r) for r in self.datastore['rup'].values())
                        self.datastore.set_attrs(
                            'rup', tot_ruptures=tot_ruptures)
        if oq.hazard_calculation_id is None and 'poes' in self.datastore:
            self.datastore.set_nbytes('poes')
            self.datastore['disagg_by_grp'] = numpy.array(
                sorted(data), grp_extreme_dt)

            # save a copy of the poes in hdf5cache
            with hdf5.File(self.hdf5cache) as cache:
                cache['oqparam'] = oq
                self.datastore.hdf5.copy('poes', cache)
            self.calc_stats(self.hdf5cache)

    def calc_stats(self, parent):
        oq = self.oqparam
        hstats = oq.hazard_stats()
        # initialize datasets
        N = len(self.sitecol.complete)
        L = len(oq.imtls.array)
        P = len(oq.poes)
        M = len(oq.imtls)
        R = len(self.rlzs_assoc.realizations)
        S = len(hstats)
        if R > 1 and oq.individual_curves or not hstats:
            self.datastore.create_dset('hcurves-rlzs', F32, (N, R, L))
            if oq.poes:
                self.datastore.create_dset('hmaps-rlzs', F32, (N, R, M, P))
        if hstats:
            self.datastore.create_dset('hcurves-stats', F32, (N, S, L))
            if oq.poes:
                self.datastore.create_dset('hmaps-stats', F32, (N, S, M, P))
        if 'mean' in dict(hstats) and R > 1 and N <= FEWSITES:
            self.datastore.create_dset('best_rlz', U32, (N,))
        ct = oq.concurrent_tasks
        logging.info('Building hazard statistics with %d concurrent_tasks', ct)
        weights = [rlz.weight for rlz in self.rlzs_assoc.realizations]
        allargs = [  # this list is very fast to generate
            (getters.PmapGetter(parent, weights, t.sids, oq.poes),
             N, hstats, oq.individual_curves)
            for t in self.sitecol.split_in_tiles(ct)]
        parallel.Starmap(build_hazard_stats, allargs, self.monitor()).reduce(
            self.save_hazard_stats)


@base.calculators.add('preclassical')
class PreCalculator(ClassicalCalculator):
    """
    Calculator to filter the sources and compute the number of effective
    ruptures
    """
    core_task = preclassical


def _build_stat_curve(poes, imtls, stat, weights):
    L = len(imtls.array)
    array = numpy.zeros((L, 1))
    if isinstance(weights, list):  # IMT-dependent weights
        # this is slower since the arrays are shorter
        for imt in imtls:
            slc = imtls(imt)
            ws = [w[imt] for w in weights]
            if sum(ws) == 0:  # expect no data for this IMT
                continue
            array[slc] = stat(poes[:, slc], ws)
    else:
        array = stat(poes, weights)
    return ProbabilityCurve(array)


def build_hazard_stats(pgetter, N, hstats, individual_curves, monitor):
    """
    :param pgetter: an :class:`openquake.commonlib.getters.PmapGetter`
    :param N: the total number of sites
    :param hstats: a list of pairs (statname, statfunc)
    :param individual_curves: if True, also build the individual curves
    :param monitor: instance of Monitor
    :returns: a dictionary kind -> ProbabilityMap

    The "kind" is a string of the form 'rlz-XXX' or 'mean' of 'quantile-XXX'
    used to specify the kind of output.
    """
    with monitor('read PoEs'):
        pgetter.init()
    imtls, poes, weights = pgetter.imtls, pgetter.poes, pgetter.weights
    L = len(imtls.array)
    R = len(weights)
    S = len(hstats)
    pmap_by_kind = {'rlz_by_sid': {}}
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
        if sum(pc.array.sum() for pc in pcurves) == 0:  # no data
            continue
        with compute_mon:
            if hstats:
                arr = numpy.array([pc.array for pc in pcurves])
                for s, (statname, stat) in enumerate(hstats.items()):
                    pc = _build_stat_curve(arr, imtls, stat, weights)
                    pmap_by_kind['hcurves-stats'][s][sid] = pc
                    if poes:
                        hmap = calc.make_hmap(pc, pgetter.imtls, poes, sid)
                        pmap_by_kind['hmaps-stats'][s].update(hmap)
                    if statname == 'mean' and R > 1 and N <= FEWSITES:
                        rlz = pmap_by_kind['rlz_by_sid']
                        rlz[sid] = util.closest_to_ref(
                            [p.array for p in pcurves], pc.array)['rlz']
            if R > 1 and individual_curves or not hstats:
                for pmap, pc in zip(pmap_by_kind['hcurves-rlzs'], pcurves):
                    pmap[sid] = pc
                if poes:
                    pmap_by_kind['hmaps-rlzs'] = [
                        calc.make_hmap(pc, imtls, poes, sid) for pc in pcurves]
    return pmap_by_kind
