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

from openquake.baselib import parallel, hdf5, datastore
from openquake.baselib.python3compat import encode
from openquake.baselib.general import AccumDict, block_splitter
from openquake.hazardlib.contexts import FEWSITES
from openquake.hazardlib.calc.filters import split_sources
from openquake.hazardlib.calc.hazard_curve import classical, ProbabilityMap
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.commonlib import calc, util, readinput
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
    [('taskno', U16), ('nsites', U32), ('nruptures', U32), ('weight', F32)])


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
        srcs = readinput.random_filtered_sources(splits, srcfilter, ss)
        yield classical(srcs, srcfilter, gsims, params, monitor)
        return
    sources = []
    with monitor("filtering/splitting sources"):
        for src, _sites in srcfilter(srcs):
            if src.num_ruptures >= params['maxweight']:
                splits, stime = split_sources([src])
                sources.extend(srcfilter.filter(splits))
            else:
                sources.append(src)
        blocks = list(block_splitter(sources, params['maxweight'],
                                     operator.attrgetter('num_ruptures')))
    if blocks:
        # yield the first blocks (if any) and compute the last block in core
        # NB: the last block is usually the smallest one
        for block in blocks[:-1]:
            yield classical, block, srcfilter, gsims, params
        yield classical(blocks[-1], srcfilter, gsims, params, monitor)


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
    accept_precalc = ['psha']

    def agg_dicts(self, acc, dic):
        """
        Aggregate dictionaries of hazard curves by updating the accumulator.

        :param acc: accumulator dictionary
        :param dic: dictionary with keys pmap, calc_times, eff_ruptures
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
            parent = datastore.read(self.oqparam.hazard_calculation_id)
            self.csm_info = parent['csm_info']
            parent.close()
            self.calc_stats(parent)  # post-processing
            return {}
        with self.monitor('managing sources', autoflush=True):
            smap = parallel.Starmap(
                self.core_task.__func__, monitor=self.monitor())
            source_ids = []
            data = []
            for i, sources in enumerate(self._send_sources(smap)):
                source_ids.append(get_src_ids(sources))
                for src in sources:  # collect source data
                    data.append((i, src.nsites, src.num_ruptures, src.weight))
            if source_ids:
                self.datastore['task_sources'] = encode(source_ids)
            self.datastore.extend(
                'source_data', numpy.array(data, source_data_dt))
        self.calc_times = AccumDict(accum=numpy.zeros(2, F32))
        try:
            acc = smap.reduce(self.agg_dicts, self.acc0())
            self.store_rlz_info(acc.eff_ruptures)
        finally:
            with self.monitor('store source_info', autoflush=True):
                self.store_source_info(self.calc_times)
        if acc.nsites:
            src_ids = sorted(acc.nsites)
            nsites = [acc.nsites[i] for i in src_ids]
            self.datastore['source_info'][src_ids, 'num_sites'] = nsites
        if not self.calc_times:
            raise RuntimeError('All sources were filtered away!')
        self.calc_times.clear()  # save a bit of memory
        return acc

    def _send_sources(self, smap):
        oq = self.oqparam
        opt = self.oqparam.optimize_same_id_sources
        nrup = operator.attrgetter('num_ruptures')
        param = dict(
            truncation_level=oq.truncation_level, imtls=oq.imtls,
            filter_distance=oq.filter_distance, reqv=oq.get_reqv(),
            pointsource_distance=oq.pointsource_distance,
            maxweight=min(self.csm.get_maxweight(nrup, oq.concurrent_tasks),
                          base.RUPTURES_PER_BLOCK))
        logging.info('Max ruptures per task = %(maxweight)d', param)

        num_tasks = 0
        num_sources = 0

        if self.csm.has_dupl_sources and not opt:
            logging.warning('Found %d duplicated sources',
                            self.csm.has_dupl_sources)

        for trt, sources in self.csm.get_trt_sources():
            gsims = self.csm.info.gsim_lt.get_gsims(trt)
            num_sources += len(sources)
            if hasattr(sources, 'atomic') and sources.atomic:
                smap.submit(sources, self.src_filter, gsims, param,
                            func=classical)
                yield sources
                num_tasks += 1
            else:  # regroup the sources in blocks
                for block in block_splitter(sources, param['maxweight'], nrup):
                    smap.submit(block, self.src_filter, gsims, param)
                    yield block
                    num_tasks += 1
        logging.info('Sent %d sources in %d tasks', num_sources, num_tasks)

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
        logging.info('Building hazard statistics')
        ct = oq.concurrent_tasks
        allargs = [  # this list is very fast to generate
            (getters.PmapGetter(parent, self.rlzs_assoc, t.sids, oq.poes),
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
    with monitor('combine pmaps'):
        pgetter.init()  # if not already initialized
        try:
            pmaps = pgetter.get_pmaps()
        except IndexError:  # no data
            return {}
        if sum(len(pmap) for pmap in pmaps) == 0:  # no data
            return {}
    R = len(pmaps)
    imtls, poes, weights = pgetter.imtls, pgetter.poes, pgetter.weights
    pmap_by_kind = {}
    hmaps_stats = []
    hcurves_stats = []
    with monitor('compute stats'):
        for statname, stat in hstats.items():
            pmap = compute_pmap_stats(pmaps, [stat], weights, imtls)
            hcurves_stats.append(pmap)
            if pgetter.poes:
                hmaps_stats.append(
                    calc.make_hmap(pmap, pgetter.imtls, pgetter.poes))
            if statname == 'mean' and R > 1 and N <= FEWSITES:
                pmap_by_kind['rlz_by_sid'] = rlz = {}
                for sid, pcurve in pmap.items():
                    rlz[sid] = util.closest_to_ref(
                        [pm.setdefault(sid, 0).array for pm in pmaps],
                        pcurve.array)['rlz']
    if hcurves_stats:
        pmap_by_kind['hcurves-stats'] = hcurves_stats
    if hmaps_stats:
        pmap_by_kind['hmaps-stats'] = hmaps_stats
    if R > 1 and individual_curves or not hstats:
        pmap_by_kind['hcurves-rlzs'] = pmaps
        if pgetter.poes:
            with monitor('build individual hmaps'):
                pmap_by_kind['hmaps-rlzs'] = [
                    calc.make_hmap(pmap, imtls, poes) for pmap in pmaps]
    return pmap_by_kind
