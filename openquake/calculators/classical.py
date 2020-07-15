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
import re
import time
import copy
import pprint
import logging
import operator
from datetime import datetime
import numpy

from openquake.baselib import parallel, hdf5
from openquake.baselib.python3compat import encode
from openquake.baselib.general import (
    AccumDict, DictArray, block_splitter, groupby, humansize,
    get_array_nbytes, decompress)
from openquake.hazardlib.contexts import ContextMaker, get_effect
from openquake.hazardlib.calc.filters import split_sources, getdefault
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.commonlib import calc, util, logs, readinput
from openquake.commonlib.source_reader import random_filtered_sources
from openquake.calculators import getters
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO32 = 2 ** 32
grp_extreme_dt = numpy.dtype([('grp_id', U16), ('grp_trt', hdf5.vstr),
                             ('extreme_poe', F32)])

MAXMEMORY = '''Estimated upper memory limit per core:
%d sites x %d levels x %d gsims x %d src_multiplicity * 8 bytes = %s'''

TOOBIG = '''\
The calculation is too big and will likely fail:
num_sites = %d
num_levels = %d
num_gsims = %d
src_multiplicity = %d
The estimated memory per core is %s > 4 GB.
You should reduce one or more of the listed parameters.'''


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
    maxw = params['max_weight']
    N = len(srcfilter.sitecol.complete)

    def weight(src):
        n = 10 * numpy.sqrt(len(src.indices) / N)
        return src.weight * params['rescale_weight'] * n
    blocks = list(block_splitter(sources, maxw, weight))
    subtasks = len(blocks) - 1
    for block in blocks[:-1]:
        yield classical, block, srcfilter, gsims, params
    if monitor.calc_id and subtasks:
        msg = 'produced %d subtask(s) with mean weight %d' % (
            subtasks, numpy.mean([b.weight for b in blocks[:-1]]))
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
    totrups = 0
    maxradius = 0
    for src in splits:
        t0 = time.time()
        totrups += src.num_ruptures
        if srcfilter.get_close_sites(src) is None:
            continue
        if hasattr(src, 'radius'):  # for point sources
            maxradius = max(maxradius, src.radius)
        dt = time.time() - t0
        calc_times[src.source_id] += F32(
            [src.num_ruptures, src.nsites, dt])
        for grp_id in src.grp_ids:
            pmap[grp_id] += 0
    return dict(pmap=pmap, calc_times=calc_times, rup_data={},
                extra=dict(task_no=monitor.task_no, totrups=totrups,
                           trt=src.tectonic_region_type, maxradius=maxradius))


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
        if self.oqparam.disagg_by_src:
            # store the poes for the given source
            acc[dic['extra']['source_id']] = dic['pmap']

        trt = dic['extra'].pop('trt')
        self.maxradius = max(self.maxradius, dic['extra'].pop('maxradius'))
        with self.monitor('aggregate curves'):
            extra = dic['extra']
            self.totrups += extra['totrups']
            d = dic['calc_times']  # srcid -> eff_rups, eff_sites, dt
            self.calc_times += d
            srcids = set()
            eff_rups = 0
            eff_sites = 0
            for srcid, rec in d.items():
                srcids.add(re.sub(r':\d+$', '', srcid))
                eff_rups += rec[0]
                if rec[0]:
                    eff_sites += rec[1] / rec[0]
            self.by_task[extra['task_no']] = (
                eff_rups, eff_sites, sorted(srcids))
            for grp_id, pmap in dic['pmap'].items():
                if pmap and grp_id in acc:
                    acc[grp_id] |= pmap
                else:
                    acc[grp_id] = copy.copy(pmap)
                acc.eff_ruptures[trt] += eff_rups

            # store rup_data if there are few sites
            for mag, d in dic['rup_data'].items():
                d = decompress(d)
                for k in self.rparams:
                    nr = len(d['gidx'])
                    name = 'rup_%s/%s' % (mag, k)
                    if k.endswith('_'):  # distance parameter
                        try:
                            v = d[k.rstrip('_')]
                        except KeyError:
                            v = numpy.ones((nr, self.N)) * numpy.nan
                    else:
                        try:
                            v = d[k]
                        except KeyError:
                            if k == 'probs_occur':
                                v = [numpy.zeros(0)] * nr
                            else:
                                v = numpy.ones(nr) * numpy.nan
                    if k == 'probs_occur':  # variable lenght arrays
                        self.datastore.hdf5.save_vlen(name, v)
                        continue
                    hdf5.extend(self.datastore[name], v)
        return acc

    def acc0(self):
        """
        Initial accumulator, a dict grp_id -> ProbabilityMap(L, G)
        """
        zd = AccumDict()
        num_levels = len(self.oqparam.imtls.array)
        rparams = {'gidx', 'occurrence_rate',
                   'probs_occur', 'clon_', 'clat_', 'rrup_'}
        gsims_by_trt = self.full_lt.get_gsims_by_trt()
        n = len(self.full_lt.sm_rlzs)
        trts = list(self.full_lt.gsim_lt.values)
        for sm in self.full_lt.sm_rlzs:
            for grp_id in self.full_lt.grp_ids(sm.ordinal):
                trt = trts[grp_id // n]
                gsims = gsims_by_trt[trt]
                cm = ContextMaker(trt, gsims)
                rparams.update(cm.REQUIRES_RUPTURE_PARAMETERS)
                for dparam in cm.REQUIRES_DISTANCES:
                    rparams.add(dparam + '_')
        zd.eff_ruptures = AccumDict(accum=0)  # trt -> eff_ruptures
        mags = set()
        for trt, dset in self.datastore['source_mags'].items():
            mags.update(dset[:])
        mags = sorted(mags)
        if self.few_sites:
            self.rparams = sorted(rparams)
            for k in self.rparams:
                for mag in mags:
                    name = 'rup_%s/%s' % (mag, k)
                    # variable length arrays
                    if k == 'gidx':
                        self.datastore.create_dset(
                            name, U16, compression='gzip')
                    elif k == 'probs_occur':  # vlen
                        self.datastore.create_dset(
                            name, hdf5.vfloat64, compression='gzip')
                    elif k.endswith('_'):  # array of shape (U, N)
                        self.datastore.create_dset(
                            name, F32, shape=(None, self.N),
                            compression='gzip')
                    else:
                        self.datastore.create_dset(name, F32)
        else:
            self.rparams = {}
        self.by_task = {}  # task_no => src_ids
        self.totrups = 0  # total number of ruptures before collapsing
        self.maxradius = 0

        # estimate max memory per core
        max_num_gsims = max(len(gsims) for gsims in gsims_by_trt.values())
        max_num_grp_ids = max(
            len(grp_ids) for grp_ids in self.datastore['grp_ids'])
        pmapbytes = self.N * num_levels * max_num_gsims * max_num_grp_ids * 8
        if pmapbytes > TWO32:
            logging.warning(
                TOOBIG % (self.N, num_levels, max_num_gsims, max_num_grp_ids,
                          humansize(pmapbytes)))
        logging.info(MAXMEMORY % (self.N, num_levels, max_num_gsims,
                                  max_num_grp_ids, humansize(pmapbytes)))

        self.Ns = len(self.csm.source_info)
        if self.oqparam.disagg_by_src:
            sources = self.get_source_ids()
            self.datastore.create_dset(
                'disagg_by_src', F32,
                (self.N, self.R, self.M, self.L1, self.Ns))
            self.datastore.set_shape_attrs(
                'disagg_by_src', site_id=self.N, rlz_id=self.R,
                imt=list(self.oqparam.imtls), lvl=self.L1, src_id=sources)
        return zd

    def get_source_ids(self):
        """
        :returns: the unique source IDs contained in the composite model
        """
        oq = self.oqparam
        self.M = len(oq.imtls)
        self.L1 = len(oq.imtls.array) // self.M
        sources = encode([src_id for src_id in self.csm.source_info])
        size, msg = get_array_nbytes(
            dict(N=self.N, R=self.R, M=self.M, L1=self.L1, Ns=self.Ns))
        ps = 'pointSource' in self.full_lt.source_model_lt.source_types
        if size > TWO32 and not ps:
            raise RuntimeError('The matrix disagg_by_src is too large: %s'
                               % msg)
        elif size > TWO32:
            msg = ('The source model contains point sources: you cannot set '
                   'disagg_by_src=true unless you convert them to multipoint '
                   'sources with the command oq upgrade_nrml --multipoint %s'
                   ) % oq.base_path
            raise RuntimeError(msg)
        return sources

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        oq = self.oqparam
        if oq.hazard_calculation_id and not oq.compare_with_classical:
            with util.read(self.oqparam.hazard_calculation_id) as parent:
                self.full_lt = parent['full_lt']
            self.calc_stats()  # post-processing
            return {}

        mags = self.datastore['source_mags']  # by TRT
        if len(mags) == 0:  # everything was discarded
            raise RuntimeError('All sources were discarded!?')
        gsims_by_trt = self.full_lt.get_gsims_by_trt()
        if oq.pointsource_distance is not None:
            for trt in gsims_by_trt:
                oq.pointsource_distance[trt] = getdefault(
                    oq.pointsource_distance, trt)
        mags_by_trt = {}
        for trt in mags:
            mags_by_trt[trt] = mags[trt][()]
        imts_with_period = [imt for imt in oq.imtls
                            if imt == 'PGA' or imt.startswith('SA')]
        imts_ok = len(imts_with_period) == len(oq.imtls)
        if (imts_ok and oq.pointsource_distance and
                oq.pointsource_distance.suggested()) or (
                    imts_ok and oq.minimum_intensity):
            aw, self.psd = get_effect(
                mags_by_trt, self.sitecol.one(), gsims_by_trt, oq)
            dic = {trt: [(float(mag), int(dst))
                         for mag, dst in self.psd[trt].items()]
                   for trt in self.psd if trt != 'default'}
            logging.info('Using pointsource_distance=\n%s', pprint.pformat(dic))
            if len(vars(aw)) > 1:  # more than _extra
                self.datastore['effect_by_mag_dst'] = aw
        elif oq.pointsource_distance:
            self.psd = oq.pointsource_distance.interp(mags_by_trt)
            for trt, dic in self.psd.items():
                it = list(dic.items())
                md = '%s->%d ... %s->%d' % (it[0] + it[-1])
                logging.info('ps_dist %s: %s', trt, md)
        else:
            self.psd = {}
        smap = parallel.Starmap(classical, h5=self.datastore.hdf5,
                                num_cores=oq.num_cores)
        self.submit_tasks(smap)
        acc0 = self.acc0()  # create the rup/ datasets BEFORE swmr_on()
        self.datastore.swmr_on()
        smap.h5 = self.datastore.hdf5
        self.calc_times = AccumDict(accum=numpy.zeros(3, F32))
        try:
            acc = smap.reduce(self.agg_dicts, acc0)
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
                                                hdf5.vstr, num_tasks,
                                                fillvalue=None)
                for task_no, rec in self.by_task.items():
                    effrups, effsites, srcids = rec
                    er[task_no] = effrups
                    es[task_no] = effsites
                    si[task_no] = ' '.join(srcids)
                self.by_task.clear()
        self.numrups = sum(arr[0] for arr in self.calc_times.values())
        numsites = sum(arr[1] for arr in self.calc_times.values())
        logging.info('Effective number of ruptures: {:_d}/{:_d}'.format(
            int(self.numrups), self.totrups))
        logging.info('Effective number of sites per rupture: %d',
                     numsites / self.numrups)
        if self.psd:
            psdist = max(max(self.psd[trt].values()) for trt in self.psd)
            if psdist != -1 and self.maxradius >= psdist / 2:
                logging.warning('The pointsource_distance of %d km is too '
                                'small compared to a maxradius of %d km',
                                psdist, self.maxradius)
        self.calc_times.clear()  # save a bit of memory
        return acc

    def submit_tasks(self, smap):
        """
        Submit tasks to the passed Starmap
        """
        oq = self.oqparam
        gsims_by_trt = self.full_lt.get_gsims_by_trt()
        src_groups = self.csm.src_groups

        def srcweight(src):
            trt = src.tectonic_region_type
            g = len(gsims_by_trt[trt])
            return src.weight * g

        logging.info('Weighting the sources')
        totweight = 0
        for sg in src_groups:
            for src in sg:
                totweight += srcweight(src)
                if src.code == b'C' and src.num_ruptures > 10_000:
                    msg = ('{} is suspiciously large, containing {:_d} '
                           'ruptures with complex_fault_mesh_spacing={} km')
                    spc = oq.complex_fault_mesh_spacing
                    logging.warning(msg.format(src, src.num_ruptures, spc))
        C = oq.concurrent_tasks or 1
        if oq.calculation_mode == 'preclassical':
            f1 = f2 = preclassical
            C *= 50  # use more tasks because there will be slow tasks
        elif oq.disagg_by_src or oq.is_ucerf() or oq.split_sources is False:
            # do not split the sources
            C *= 5  # use more tasks, especially in UCERF
            f1, f2 = classical, classical
        else:
            f1, f2 = classical, classical_split_filter
        max_weight = max(min(totweight / C, oq.max_weight), oq.min_weight)
        logging.info('tot_weight={:_d}, max_weight={:_d}'.format(
            int(totweight), int(max_weight)))
        param = dict(
            truncation_level=oq.truncation_level, imtls=oq.imtls,
            filter_distance=oq.filter_distance, reqv=oq.get_reqv(),
            maximum_distance=oq.maximum_distance,
            pointsource_distance=self.psd,
            point_rupture_bins=oq.point_rupture_bins,
            shift_hypo=oq.shift_hypo, max_weight=max_weight,
            collapse_level=oq.collapse_level,
            max_sites_disagg=oq.max_sites_disagg,
            af=self.af)
        srcfilter = self.src_filter(self.datastore.tempname)
        for sg in src_groups:
            gsims = gsims_by_trt[sg.trt]
            param['rescale_weight'] = len(gsims)
            if sg.atomic:
                # do not split atomic groups
                nb = 1
                smap.submit((sg, srcfilter, gsims, param), f1)
            else:  # regroup the sources in blocks
                blks = (groupby(sg, operator.attrgetter('source_id')).values()
                        if oq.disagg_by_src
                        else block_splitter(sg, totweight/C, srcweight,
                                            sort=True))
                blocks = list(blks)
                nb = len(blocks)
                for block in blocks:
                    logging.debug('Sending %d source(s) with weight %d',
                                  len(block),
                                  sum(srcweight(src) for src in block))
                    smap.submit((block, srcfilter, gsims, param), f2)

            w = sum(srcweight(src) for src in sg)
            logging.info('TRT = %s', sg.trt)
            if oq.maximum_distance.magdist:
                it = sorted(oq.maximum_distance.magdist[sg.trt].items())
                md = '%s->%d ... %s->%d' % (it[0] + it[-1])
            else:
                md = oq.maximum_distance(sg.trt)
            logging.info('max_dist={}, gsims={}, weight={:_d}, blocks={}'.
                         format(md, len(gsims), int(w), nb))

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
                            dset[s, r] = pmap[s].array.reshape(self.M, self.L1)
            self.datastore.flush()

    def post_execute(self, pmap_by_key):
        """
        Collect the hazard curves by realization and export them.

        :param pmap_by_key:
            a dictionary key -> hazard curves
        """
        nr = {name: len(dset['mag']) for name, dset in self.datastore.items()
              if name.startswith('rup_')}
        if nr:  # few sites, log the number of ruptures per magnitude
            logging.info('%s', nr)
        oq = self.oqparam
        data = []
        weights = [rlz.weight for rlz in self.realizations]
        pgetter = getters.PmapGetter(self.datastore, weights)
        with self.monitor('saving probability maps'):
            for key, pmap in pmap_by_key.items():
                if isinstance(key, str):  # disagg_by_src
                    serial = self.csm.source_info[key][readinput.SERIAL]
                    self.datastore['disagg_by_src'][..., serial] = (
                        pgetter.get_hcurves(
                            {'grp-%02d' % gid: pmap[gid] for gid in pmap}))
                elif pmap:  # pmap can be missing if the group is filtered away
                    # key is the group ID
                    base.fix_ones(pmap)  # avoid saving PoEs == 1
                    trt = self.full_lt.trt_by_grp[key]
                    name = 'poes/grp-%02d' % key
                    self.datastore[name] = pmap
                    extreme = max(
                        get_extreme_poe(pmap[sid].array, oq.imtls)
                        for sid in pmap)
                    data.append((key, trt, extreme))
        if oq.hazard_calculation_id is None and 'poes' in self.datastore:
            self.datastore['disagg_by_grp'] = numpy.array(
                sorted(data), grp_extreme_dt)
            self.calc_stats()

    def calc_stats(self):
        oq = self.oqparam
        hstats = oq.hazard_stats()
        # initialize datasets
        imls = oq.imtls.array
        N = len(self.sitecol.complete)
        P = len(oq.poes)
        M = self.M = len(oq.imtls)
        imts = list(oq.imtls)
        if oq.soil_intensities is not None:
            L = M * len(oq.soil_intensities)
        else:
            L = len(imls)
        L1 = self.L1 = L // M
        R = len(self.realizations)
        S = len(hstats)
        if R > 1 and oq.individual_curves or not hstats:
            self.datastore.create_dset('hcurves-rlzs', F32, (N, R, M, L1))
            self.datastore.set_shape_attrs(
                'hcurves-rlzs', site_id=N, rlz_id=R, imt=imts, lvl=L1)
            if oq.poes:
                self.datastore.create_dset('hmaps-rlzs', F32, (N, R, M, P))
                self.datastore.set_shape_attrs(
                    'hmaps-rlzs', site_id=N, rlz_id=R,
                    imt=list(oq.imtls), poe=oq.poes)
        if hstats:
            self.datastore.create_dset('hcurves-stats', F32, (N, S, M, L1))
            self.datastore.set_shape_attrs(
                'hcurves-stats', site_id=N, stat=list(hstats),
                imt=imts, lvl=numpy.arange(L1))
            if oq.poes:
                self.datastore.create_dset('hmaps-stats', F32, (N, S, M, P))
                self.datastore.set_shape_attrs(
                    'hmaps-stats', site_id=N, stat=list(hstats),
                    imt=list(oq.imtls), poe=oq.poes)
        ct = oq.concurrent_tasks or 1
        logging.info('Building hazard statistics')
        self.weights = [rlz.weight for rlz in self.realizations]
        allargs = [  # this list is very fast to generate
            (getters.PmapGetter(self.datastore, self.weights, t.sids, oq.poes),
             N, hstats, oq.individual_curves, oq.max_sites_disagg,
             self.amplifier)
            for t in self.sitecol.split_in_tiles(ct)]
        if self.few_sites:
            dist = 'no'
        else:
            dist = None  # parallelize as usual
            self.datastore.swmr_on()
        parallel.Starmap(
            build_hazard, allargs, distribute=dist, h5=self.datastore.hdf5
        ).reduce(self.save_hazard)
        if 'hmaps-stats' in self.datastore:
            hmaps = self.datastore.sel('hmaps-stats', stat='mean')  # NSMP
            maxhaz = hmaps.max(axis=(0, 1, 3))
            mh = dict(zip(self.oqparam.imtls, maxhaz))
            logging.info('The maximum hazard map values are %s', mh)


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
            imtls = DictArray({imt: amplifier.amplevels
                               for imt in pgetter.imtls})
        else:
            imtls = pgetter.imtls
    poes, weights = pgetter.poes, pgetter.weights
    M = len(imtls)
    P = len(poes)
    L = len(imtls.array)
    R = len(weights)
    S = len(hstats)
    pmap_by_kind = {}
    if R > 1 and individual_curves or not hstats:
        pmap_by_kind['hcurves-rlzs'] = [ProbabilityMap(L) for r in range(R)]
    if hstats:
        pmap_by_kind['hcurves-stats'] = [ProbabilityMap(L) for r in range(S)]
        if poes:
            pmap_by_kind['hmaps-stats'] = [
                ProbabilityMap(M, P) for r in range(S)]
    combine_mon = monitor('combine pmaps', measuremem=False)
    compute_mon = monitor('compute stats', measuremem=False)
    for sid in pgetter.sids:
        with combine_mon:
            pcurves = pgetter.get_pcurves(sid)
            if amplifier:
                pcurves = amplifier.amplify(ampcode[sid], pcurves)
                # NB: the pcurves have soil levels != IMT levels
        if sum(pc.array.sum() for pc in pcurves) == 0:  # no data
            continue
        with compute_mon:
            if hstats:
                arr = numpy.array([pc.array for pc in pcurves])
                for s, (statname, stat) in enumerate(hstats.items()):
                    pc = getters.build_stat_curve(arr, imtls, stat, weights)
                    pmap_by_kind['hcurves-stats'][s][sid] = pc
                    if poes:
                        hmap = calc.make_hmap(pc, imtls, poes, sid)
                        pmap_by_kind['hmaps-stats'][s].update(hmap)
            if R > 1 and individual_curves or not hstats:
                for pmap, pc in zip(pmap_by_kind['hcurves-rlzs'], pcurves):
                    pmap[sid] = pc
                if poes:
                    pmap_by_kind['hmaps-rlzs'] = [
                        calc.make_hmap(pc, imtls, poes, sid) for pc in pcurves]
    return pmap_by_kind
