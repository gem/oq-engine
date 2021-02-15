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
import io
import time
import psutil
import pprint
import logging
import operator
import numpy
try:
    from PIL import Image
except ImportError:
    Image = None
from openquake.baselib import parallel, hdf5, config
from openquake.baselib.python3compat import encode
from openquake.baselib.general import (
    AccumDict, DictArray, block_splitter, groupby, humansize,
    get_nbytes_msg)
from openquake.hazardlib.source.point import (
    PointSource, grid_point_sources, msr_name)
from openquake.hazardlib.source.base import EPS
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.contexts import ContextMaker, get_effect
from openquake.hazardlib.calc.filters import split_source, SourceFilter
from openquake.hazardlib.calc.hazard_curve import classical as hazclassical
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.commonlib import calc, util, readinput
from openquake.calculators import getters
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO32 = 2 ** 32
BUFFER = 1.5  # enlarge the pointsource_distance sphere to fix the weight
# with BUFFER = 1 we would have lots of apparently light sources
# collected together in an extra-slow task, as it happens in SHARE
# with ps_grid_spacing=50
get_weight = operator.attrgetter('weight')
grp_extreme_dt = numpy.dtype([('et_id', U16), ('grp_trt', hdf5.vstr),
                             ('extreme_poe', F32)])


def get_source_id(src):  # used in submit_tasks
    return src.source_id.split(':')[0]


def get_extreme_poe(array, imtls):
    """
    :param array: array of shape (L, G) with L=num_levels, G=num_gsims
    :param imtls: DictArray imt -> levels
    :returns:
        the maximum PoE corresponding to the maximum level for IMTs and GSIMs
    """
    return max(array[imtls(imt).stop - 1].max() for imt in imtls)


def run_preclassical(csm, oqparam, h5):
    """
    :param csm: a CompositeSourceModel with attribute .srcfilter
    :param oqparam: the parameters in job.ini file
    :param h5: a DataStore instance
    """
    logging.info('Sending %s', csm.sitecol)

    # do nothing for atomic sources except counting the ruptures
    for src in csm.get_sources(atomic=True):
        src.num_ruptures = src.count_ruptures()
        src.nsites = len(csm.sitecol)

    # run preclassical for non-atomic sources
    sources_by_grp = groupby(
        csm.get_sources(atomic=False),
        lambda src: (src.grp_id, msr_name(src)))
    param = dict(maximum_distance=oqparam.maximum_distance,
                 pointsource_distance=oqparam.pointsource_distance,
                 ps_grid_spacing=oqparam.ps_grid_spacing,
                 split_sources=oqparam.split_sources)
    srcfilter = SourceFilter(
        csm.sitecol.reduce(10000) if csm.sitecol else None,
        oqparam.maximum_distance)
    res = parallel.Starmap(
        preclassical,
        ((srcs, srcfilter, param) for srcs in sources_by_grp.values()),
        h5=h5, distribute=None if len(sources_by_grp) > 1 else 'no').reduce()

    if res and res['before'] != res['after']:
        logging.info('Reduced the number of sources from {:_d} -> {:_d}'.
                     format(res['before'], res['after']))

    if res and h5:
        csm.update_source_info(res['calc_times'], nsites=True)

    for grp_id, srcs in res.items():
        # srcs can be empty if the minimum_magnitude filter is on
        if srcs and not isinstance(grp_id, str):
            newsg = SourceGroup(srcs[0].tectonic_region_type)
            newsg.sources = srcs
            csm.src_groups[grp_id] = newsg

    # sanity check
    for sg in csm.src_groups:
        for src in sg:
            assert src.num_ruptures
            assert src.nsites

    # store ps_grid data, if any
    for key, sources in res.items():
        if isinstance(key, str) and key.startswith('ps_grid/'):
            arrays = []
            for ps in sources:
                if hasattr(ps, 'location'):
                    lonlats = [ps.location.x, ps.location.y]
                    for src in getattr(ps, 'pointsources', []):
                        lonlats.extend([src.location.x, src.location.y])
                    arrays.append(F32(lonlats))
            h5[key] = arrays


def store_ctxs(dstore, rupdata, grp_id):
    """
    Store contexts with the same magnitude in the datastore
    """
    nr = len(rupdata['mag'])
    rupdata['nsites'] = numpy.array([len(s) for s in rupdata['sids_']])
    rupdata['grp_id'] = numpy.repeat(grp_id, nr)
    nans = numpy.repeat(numpy.nan, nr)
    for par in dstore['rup']:
        n = 'rup/' + par
        if par.endswith('_'):
            if par in rupdata:
                dstore.hdf5.save_vlen(n, rupdata[par])
            else:  # add nr empty rows
                dstore[n].resize((len(dstore[n]) + nr,))
        else:
            hdf5.extend(dstore[n], rupdata.get(par, nans))


#  ########################### task functions ############################ #

def preclassical(srcs, srcfilter, params, monitor):
    """
    Weight the sources. Also split them if split_sources is true. If
    ps_grid_spacing is set, grid the point sources before weighting them.

    NB: srcfilter can be on a reduced site collection for performance reasons
    """
    # src.id -> nrups, nsites, time, task_no
    calc_times = AccumDict(accum=numpy.zeros(4, F32))
    sources = []
    grp_id = srcs[0].grp_id
    trt = srcs[0].tectonic_region_type
    md = params['maximum_distance'](trt)
    pd = (params['pointsource_distance'](trt)
          if params['pointsource_distance'] else 0)
    with monitor('splitting sources'):
        # this can be slow
        for src in srcs:
            t0 = time.time()
            src.nsites = len(srcfilter.close_sids(src))
            # NB: it is crucial to split only the close sources, for
            # performance reasons (think of Ecuador in SAM)
            splits = split_source(src) if (
                params['split_sources'] and src.nsites) else [src]
            sources.extend(splits)
            nrups = src.count_ruptures() if src.nsites else 0
            dt = time.time() - t0
            calc_times[src.id] += F32([nrups, src.nsites, dt, 0])
        for arr in calc_times.values():
            arr[3] = monitor.task_no
    dic = grid_point_sources(sources, params['ps_grid_spacing'], monitor)
    with monitor('weighting sources'):
        # this is normally fast
        for src in dic[grp_id]:
            if not src.nsites:  # filtered out
                src.nsites = EPS
            is_ps = isinstance(src, PointSource)
            if is_ps:
                # NB: using cKDTree would not help, performance-wise
                cdist = srcfilter.sitecol.get_cdist(src.location)
                src.nsites = (cdist <= md + pd).sum() or EPS
            src.num_ruptures = src.count_ruptures()
            if pd and is_ps:
                nphc = src.count_nphc()
                if nphc > 1:
                    close = (cdist <= pd * BUFFER).sum()
                    far = src.nsites - close
                    factor = (close + (far + EPS) / nphc) / (close + far + EPS)
                    src.num_ruptures *= factor
    dic['calc_times'] = calc_times
    dic['before'] = len(sources)
    dic['after'] = len(dic[grp_id])
    if params['ps_grid_spacing']:
        dic['ps_grid/%02d' % monitor.task_no] = [
            src for src in dic[grp_id] if src.nsites > EPS]
    return dic


def classical(srcs, rlzs_by_gsim, params, monitor):
    """
    Read the SourceFilter and call the classical calculator in hazardlib
    """
    srcfilter = monitor.read('srcfilter')
    return hazclassical(srcs, srcfilter, rlzs_by_gsim, params, monitor)


class Hazard:
    """
    Helper class for storing the PoEs
    """
    def __init__(self, dstore, full_lt, pgetter, srcidx):
        self.datastore = dstore
        self.full_lt = full_lt
        self.et_ids = dstore['et_ids'][:]
        self.rlzs_by_gsim_list = full_lt.get_rlzs_by_gsim_list(self.et_ids)
        self.slice_by_g = getters.get_slice_by_g(self.rlzs_by_gsim_list)
        self.get_hcurves = pgetter.get_hcurves
        self.imtls = pgetter.imtls
        self.sids = pgetter.sids
        self.srcidx = srcidx
        self.data = []

    def init(self, pmaps, grp_id):
        """
        Initialize the pmaps dictionary with zeros, if needed
        """
        if grp_id not in pmaps:
            L, G = self.imtls.size, len(self.rlzs_by_gsim_list[grp_id])
            pmaps[grp_id] = ProbabilityMap.build(L, G, self.sids)

    def store_poes(self, grp_id, pmap):
        """
        Store the pmap of the given group inside the _poes dataset
        """
        trt = self.full_lt.trt_by_et[self.et_ids[grp_id][0]]
        base.fix_ones(pmap)  # avoid saving PoEs == 1, fast
        arr = numpy.array([pmap[sid].array for sid in pmap]).transpose(2, 0, 1)
        self.datastore['_poes'][self.slice_by_g[grp_id]] = arr  # shape GNL
        extreme = max(
            get_extreme_poe(pmap[sid].array, self.imtls)
            for sid in pmap)
        self.data.append((grp_id, trt, extreme))

    def store_disagg(self, pmaps=None):
        """
        Store data inside disagg_by_src/disagg_by_grp
        """
        if pmaps:  # called inside a loop
            for key, pmap in pmaps.items():
                # contains only string keys in case of disaggregation
                rlzs_by_gsim = self.rlzs_by_gsim_list[pmap.grp_id]
                self.datastore['disagg_by_src'][..., self.srcidx[key]] = (
                    self.get_hcurves(pmap, rlzs_by_gsim))
        else:  # called at the end of the loop
            self.datastore['disagg_by_grp'] = numpy.array(
                sorted(self.data), grp_extreme_dt)


@base.calculators.add('classical', 'preclassical', 'ucerf_classical')
class ClassicalCalculator(base.HazardCalculator):
    """
    Classical PSHA calculator
    """
    core_task = classical
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
        pmap = dic['pmap']
        extra = dic['extra']
        ctimes = dic['calc_times']  # srcid -> eff_rups, eff_sites, dt
        self.calc_times += ctimes
        srcids = set()
        eff_rups = 0
        eff_sites = 0
        for srcid, rec in ctimes.items():
            srcids.add(srcid)
            eff_rups += rec[0]
            if rec[0]:
                eff_sites += rec[1] / rec[0]
        self.by_task[extra['task_no']] = (
            eff_rups, eff_sites, sorted(srcids))
        self.rel_ruptures[extra.pop('trt')] += eff_rups
        grp_id = extra['grp_id']
        self.counts[grp_id] -= 1
        if self.oqparam.disagg_by_src:
            # store the poes for the given source
            pmap.grp_id = grp_id
            acc[extra['source_id'].split(':')[0]] = pmap

        self.maxradius = max(self.maxradius, extra.pop('maxradius'))
        with self.monitor('aggregate curves'):
            if pmap:
                self.haz.init(acc, grp_id)
                acc[grp_id] |= pmap

        # store rup_data if there are few sites
        if self.few_sites and len(dic['rup_data']['src_id']):
            with self.monitor('saving rup_data'):
                store_ctxs(self.datastore, dic['rup_data'], grp_id)

        if self.counts[grp_id] == 0:
            with self.monitor('saving probability maps'):
                if grp_id in acc:
                    self.haz.store_poes(grp_id, acc.pop(grp_id))
        return acc

    def create_dsets(self):
        """
        Store some empty datasets in the datastore
        """
        params = {'grp_id', 'occurrence_rate', 'clon_', 'clat_', 'rrup_',
                  'nsites', 'probs_occur_', 'sids_', 'src_id'}
        gsims_by_trt = self.full_lt.get_gsims_by_trt()
        for trt, gsims in gsims_by_trt.items():
            cm = ContextMaker(trt, gsims, dict(imtls=self.oqparam.imtls))
            params.update(cm.REQUIRES_RUPTURE_PARAMETERS)
            for dparam in cm.REQUIRES_DISTANCES:
                params.add(dparam + '_')
        mags = set()
        for trt, dset in self.datastore['source_mags'].items():
            mags.update(dset[:])
        mags = sorted(mags)
        if self.few_sites:
            descr = []  # (param, dt)
            for param in params:
                if param == 'sids_':
                    dt = hdf5.vuint16
                elif param == 'probs_occur_':
                    dt = hdf5.vfloat64
                elif param.endswith('_'):
                    dt = hdf5.vfloat32
                elif param == 'src_id':
                    dt = U32
                elif param in {'nsites', 'grp_id'}:
                    dt = U16
                else:
                    dt = F32
                descr.append((param, dt))
            self.datastore.create_dframe('rup', descr, 'gzip')
        self.by_task = {}  # task_no => src_ids
        self.maxradius = 0
        self.Ns = len(self.csm.source_info)
        self.rel_ruptures = AccumDict(accum=0)  # trt -> rel_ruptures
        # NB: the relevant ruptures are less than the effective ruptures,
        # which are a preclassical concept
        if self.oqparam.disagg_by_src:
            sources = self.get_source_ids()
            self.datastore.create_dset(
                'disagg_by_src', F32,
                (self.N, self.R, self.M, self.L1, self.Ns))
            self.datastore.set_shape_descr(
                'disagg_by_src', site_id=self.N, rlz_id=self.R,
                imt=list(self.oqparam.imtls), lvl=self.L1, src_id=sources)

    def get_source_ids(self):
        """
        :returns: the unique source IDs contained in the composite model
        """
        oq = self.oqparam
        self.M = len(oq.imtls)
        self.L1 = oq.imtls.size // self.M
        sources = encode([src_id for src_id in self.csm.source_info])
        size, msg = get_nbytes_msg(
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

    def init(self):
        super().init()
        if self.oqparam.hazard_calculation_id:
            full_lt = self.datastore.parent['full_lt']
            et_ids = self.datastore.parent['et_ids'][:]
        else:
            full_lt = self.csm.full_lt
            et_ids = self.csm.get_et_ids()
        self.grp_ids = numpy.arange(len(et_ids))
        rlzs_by_gsim_list = full_lt.get_rlzs_by_gsim_list(et_ids)
        rlzs_by_g = []
        for rlzs_by_gsim in rlzs_by_gsim_list:
            for rlzs in rlzs_by_gsim.values():
                rlzs_by_g.append(rlzs)
        self.datastore.hdf5.save_vlen(
            'rlzs_by_g', [U32(rlzs) for rlzs in rlzs_by_g])
        nlevels = self.oqparam.imtls.size
        poes_shape = (len(rlzs_by_g), self.N, nlevels)  # GNL
        size = numpy.prod(poes_shape) * 8
        bytes_per_grp = size / len(self.grp_ids)
        avail = min(psutil.virtual_memory().available, config.memory.limit)
        logging.info('Requiring %s for full ProbabilityMap of shape %s',
                     humansize(size), poes_shape)
        maxlen = max(len(rbs) for rbs in rlzs_by_gsim_list)
        maxsize = maxlen * self.N * self.oqparam.imtls.size * 8
        logging.info('Requiring %s for max ProbabilityMap of shape %s',
                     humansize(maxsize), (maxlen, self.N, nlevels))
        if avail < bytes_per_grp:
            raise MemoryError(
                'You have only %s of free RAM' % humansize(avail))
        elif avail < size:
            logging.warning('You have only %s of free RAM' % humansize(avail))
        self.ct = (self.oqparam.concurrent_tasks or 1) * 2.5
        # NB: it is CRITICAL for performance to have shape GNL and not NLG
        # dset[g, :, :] = XXX is fast, dset[:, :, g] = XXX is ultra-slow
        self.datastore.create_dset('_poes', F64, poes_shape)
        if not self.oqparam.hazard_calculation_id:
            self.datastore.swmr_on()

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

        assert oq.max_sites_per_tile > oq.max_sites_disagg, (
            oq.max_sites_per_tile, oq.max_sites_disagg)
        psd = self.set_psd()  # must go before to set the pointsource_distance
        run_preclassical(self.csm, oq, self.datastore)

        # exit early if we want to perform only a preclassical
        if oq.calculation_mode == 'preclassical':
            recs = [tuple(row) for row in self.csm.source_info.values()]
            self.datastore['source_info'] = numpy.array(
                recs, readinput.source_info_dt)
            self.datastore['full_lt'] = self.csm.full_lt
            self.datastore.swmr_on()  # fixes HDF5 error in build_hazard
            return

        self.create_dsets()  # create the rup/ datasets BEFORE swmr_on()
        grp_ids = numpy.arange(len(self.csm.src_groups))
        self.calc_times = AccumDict(accum=numpy.zeros(3, F32))
        weights = [rlz.weight for rlz in self.realizations]
        pgetter = getters.PmapGetter(
            self.datastore, weights, self.sitecol.sids, oq.imtls)
        srcidx = {rec[0]: i for i, rec in enumerate(
            self.csm.source_info.values())}
        self.haz = Hazard(self.datastore, self.full_lt, pgetter, srcidx)
        blocks = list(block_splitter(grp_ids, len(self.grp_ids)))
        for b, block in enumerate(blocks, 1):
            args = self.get_args(block, self.haz)
            logging.info('Sending %d tasks', len(args))
            smap = parallel.Starmap(classical, args, h5=self.datastore.hdf5)
            smap.monitor.save('srcfilter', self.src_filter())
            self.datastore.swmr_on()
            smap.h5 = self.datastore.hdf5
            pmaps = smap.reduce(self.agg_dicts)
            logging.debug("busy time: %s", smap.busytime)
            self.haz.store_disagg(pmaps)
        if not oq.hazard_calculation_id:
            self.haz.store_disagg()
        self.store_info(psd)
        return True

    def store_info(self, psd):
        self.store_rlz_info(self.rel_ruptures)
        source_ids = self.store_source_info(self.calc_times)
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
                si[task_no] = ' '.join(source_ids[s] for s in srcids)
            self.by_task.clear()
        if self.calc_times:  # can be empty in case of errors
            self.numctxs = sum(arr[0] for arr in self.calc_times.values())
            numsites = sum(arr[1] for arr in self.calc_times.values())
            logging.info('Total number of contexts: {:_d}'.
                         format(int(self.numctxs)))
            logging.info('Average number of sites per context: %d',
                         numsites / self.numctxs)
        if psd:
            psdist = max(max(psd.ddic[trt].values()) for trt in psd.ddic)
            if psdist and self.maxradius >= psdist / 2:
                logging.warning('The pointsource_distance of %d km is too '
                                'small compared to a maxradius of %d km',
                                psdist, self.maxradius)
        self.calc_times.clear()  # save a bit of memory

    def set_psd(self):
        """
        Set the pointsource_distance
        """
        oq = self.oqparam
        mags = self.datastore['source_mags']  # by TRT
        if len(mags) == 0:  # everything was discarded
            raise RuntimeError('All sources were discarded!?')
        gsims_by_trt = self.full_lt.get_gsims_by_trt()
        mags_by_trt = {}
        for trt in mags:
            mags_by_trt[trt] = mags[trt][()]
        psd = oq.pointsource_distance
        if psd is not None:
            psd.interp(mags_by_trt)
            for trt, dic in psd.ddic.items():
                # the sum is zero for {'default': [(1, 0), (10, 0)]}
                if sum(dic.values()):
                    it = list(dic.items())
                    md = '%s->%d ... %s->%d' % (it[0] + it[-1])
                    logging.info('ps_dist %s: %s', trt, md)
        imts_with_period = [imt for imt in oq.imtls
                            if imt == 'PGA' or imt.startswith('SA')]
        imts_ok = len(imts_with_period) == len(oq.imtls)
        if (imts_ok and psd and psd.suggested()) or (
                imts_ok and oq.minimum_intensity):
            aw = get_effect(mags_by_trt, self.sitecol.one(), gsims_by_trt, oq)
            if psd:
                dic = {trt: [(float(mag), int(dst))
                             for mag, dst in psd.ddic[trt].items()]
                       for trt in psd.ddic if trt != 'default'}
                logging.info('pointsource_distance=\n%s', pprint.pformat(dic))
            if len(vars(aw)) > 1:  # more than _extra
                self.datastore['effect_by_mag_dst'] = aw
        hint = 1 if self.N <= oq.max_sites_disagg else numpy.ceil(
            self.N / oq.max_sites_per_tile)
        self.params = dict(
            truncation_level=oq.truncation_level,
            imtls=oq.imtls, reqv=oq.get_reqv(),
            pointsource_distance=oq.pointsource_distance,
            shift_hypo=oq.shift_hypo,
            min_weight=oq.min_weight,
            collapse_level=oq.collapse_level, hint=hint,
            max_sites_disagg=oq.max_sites_disagg,
            split_sources=oq.split_sources, af=self.af)
        return psd

    def get_args(self, grp_ids, hazard):
        """
        :returns: a list of Starmap arguments
        """
        oq = self.oqparam
        allargs = []
        src_groups = self.csm.src_groups
        tot_weight = 0
        for grp_id in grp_ids:
            rlzs_by_gsim = hazard.rlzs_by_gsim_list[grp_id]
            sg = src_groups[grp_id]
            for src in sg:
                src.ngsims = len(rlzs_by_gsim)
                tot_weight += src.weight
                if src.code == b'C' and src.num_ruptures > 20_000:
                    msg = ('{} is suspiciously large, containing {:_d} '
                           'ruptures with complex_fault_mesh_spacing={} km')
                    spc = oq.complex_fault_mesh_spacing
                    logging.info(msg.format(src, src.num_ruptures, spc))
        assert tot_weight
        max_weight = max(tot_weight / self.ct, oq.min_weight)
        self.params['max_weight'] = max_weight
        logging.info('tot_weight={:_d}, max_weight={:_d}'.format(
            int(tot_weight), int(max_weight)))
        self.counts = AccumDict(accum=0)
        for grp_id in grp_ids:
            rlzs_by_gsim = hazard.rlzs_by_gsim_list[grp_id]
            sg = src_groups[grp_id]
            if sg.atomic:
                # do not split atomic groups
                self.counts[grp_id] += 1
                allargs.append((sg, rlzs_by_gsim, self.params))
            else:  # regroup the sources in blocks
                blks = (groupby(sg, get_source_id).values() if oq.disagg_by_src
                        else block_splitter(
                                sg, max_weight, get_weight, sort=True))
                blocks = list(blks)
                self.counts[grp_id] += len(blocks)
                for block in blocks:
                    logging.debug('Sending %d source(s) with weight %d',
                                  len(block), sum(src.weight for src in block))
                    allargs.append((block, rlzs_by_gsim, self.params))
        return allargs

    def save_hazard(self, acc, pmap_by_kind):
        """
        Works by side effect by saving hcurves and hmaps on the datastore

        :param acc: ignored
        :param pmap_by_kind: a dictionary of ProbabilityMaps
        """
        with self.monitor('collecting hazard'):
            for kind in pmap_by_kind:  # hmaps-XXX, hcurves-XXX
                pmaps = pmap_by_kind[kind]
                if kind in self.hazard:
                    array = self.hazard[kind]
                else:
                    dset = self.datastore.getitem(kind)
                    array = self.hazard[kind] = numpy.zeros(
                        dset.shape, dset.dtype)
                for r, pmap in enumerate(pmaps):
                    for s in pmap:
                        if kind.startswith('hmaps'):
                            array[s, r] = pmap[s].array  # shape (M, P)
                        else:
                            array[s, r] = pmap[s].array.reshape(-1, self.L1)

    def post_execute(self, dummy):
        """
        Compute the statistical hazard curves
        """
        task_info = self.datastore.read_df('task_info', 'taskname')
        try:
            dur = task_info.loc[b'classical'].duration
        except KeyError:  # no data
            pass
        else:
            slow_tasks = len(dur[dur > 3 * dur.mean()])
            if slow_tasks:
                logging.info('There were %d slow tasks', slow_tasks)
        nr = {name: len(dset['mag']) for name, dset in self.datastore.items()
              if name.startswith('rup_')}
        if nr:  # few sites, log the number of ruptures per magnitude
            logging.info('%s', nr)
        if (self.oqparam.hazard_calculation_id is None
                and '_poes' in self.datastore):
            self.datastore.swmr_on()  # needed
            self.calc_stats()

    def calc_stats(self):
        oq = self.oqparam
        hstats = oq.hazard_stats()
        # initialize datasets
        N = len(self.sitecol.complete)
        P = len(oq.poes)
        M = self.M = len(oq.imtls)
        imts = list(oq.imtls)
        if oq.soil_intensities is not None:
            L = M * len(oq.soil_intensities)
        else:
            L = oq.imtls.size
        L1 = self.L1 = L // M
        R = len(self.realizations)
        S = len(hstats)
        if R > 1 and oq.individual_curves or not hstats:
            self.datastore.create_dset('hcurves-rlzs', F32, (N, R, M, L1))
            self.datastore.set_shape_descr(
                'hcurves-rlzs', site_id=N, rlz_id=R, imt=imts, lvl=L1)
            if oq.poes:
                self.datastore.create_dset('hmaps-rlzs', F32, (N, R, M, P))
                self.datastore.set_shape_descr(
                    'hmaps-rlzs', site_id=N, rlz_id=R,
                    imt=list(oq.imtls), poe=oq.poes)
        if hstats:
            self.datastore.create_dset('hcurves-stats', F32, (N, S, M, L1))
            self.datastore.set_shape_descr(
                'hcurves-stats', site_id=N, stat=list(hstats),
                imt=imts, lvl=numpy.arange(L1))
            if oq.poes:
                self.datastore.create_dset('hmaps-stats', F32, (N, S, M, P))
                self.datastore.set_shape_descr(
                    'hmaps-stats', site_id=N, stat=list(hstats),
                    imt=list(oq.imtls), poe=oq.poes)
        ct = oq.concurrent_tasks or 1
        logging.info('Building hazard statistics')
        self.weights = [rlz.weight for rlz in self.realizations]
        dstore = (self.datastore.parent if oq.hazard_calculation_id
                  else self.datastore)
        allargs = [  # this list is very fast to generate
            (getters.PmapGetter(
                dstore, self.weights, t.sids, oq.imtls, oq.poes),
             N, hstats, oq.individual_curves, oq.max_sites_disagg,
             self.amplifier)
            for t in self.sitecol.split_in_tiles(ct)]
        if self.few_sites:
            dist = 'no'
        else:
            dist = None  # parallelize as usual
        if oq.hazard_calculation_id is None:  # essential before Starmap
            self.datastore.swmr_on()
        self.hazard = {}  # kind -> array
        parallel.Starmap(
            build_hazard, allargs, distribute=dist, h5=self.datastore.hdf5
        ).reduce(self.save_hazard)
        for kind in sorted(self.hazard):
            logging.info('Saving %s', kind)
            self.datastore[kind][:] = self.hazard.pop(kind)
        if 'hmaps-stats' in self.datastore:
            hmaps = self.datastore.sel('hmaps-stats', stat='mean')  # NSMP
            maxhaz = hmaps.max(axis=(0, 1, 3))
            mh = dict(zip(self.oqparam.imtls, maxhaz))
            logging.info('The maximum hazard map values are %s', mh)
            if Image is None or not self.from_engine:  # missing PIL
                return
            M, P = hmaps.shape[2:]
            logging.info('Saving %dx%d mean hazard maps', M, P)
            inv_time = oq.investigation_time
            allargs = []
            for m, imt in enumerate(self.oqparam.imtls):
                for p, poe in enumerate(self.oqparam.poes):
                    dic = dict(m=m, p=p, imt=imt, poe=poe, inv_time=inv_time,
                               calc_id=self.datastore.calc_id,
                               array=hmaps[:, 0, m, p])
                    allargs.append((dic, self.sitecol.lons, self.sitecol.lats))
            smap = parallel.Starmap(make_hmap_png, allargs)
            for dic in smap:
                self.datastore['png/hmap_%(m)d_%(p)d' % dic] = dic['img']


def make_hmap_png(hmap, lons, lats):
    """
    :param hmap:
        a dictionary with keys calc_id, m, p, imt, poe, inv_time, array
    :param lons: an array of longitudes
    :param lats: an array of latitudes
    :returns: an Image object containing the hazard map
    """
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.grid(True)
    ax.set_title('hmap for IMT=%(imt)s, poe=%(poe)s\ncalculation %(calc_id)d,'
                 'inv_time=%(inv_time)dy' % hmap)
    ax.set_ylabel('Longitude')
    coll = ax.scatter(lons, lats, c=hmap['array'], cmap='jet')
    plt.colorbar(coll)
    bio = io.BytesIO()
    plt.savefig(bio, format='png')
    return dict(img=Image.open(bio), m=hmap['m'], p=hmap['p'])


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
            with hdf5.File(pgetter.filename, 'r') as f:
                ampcode = f['sitecol'].ampcode
            imtls = DictArray({imt: amplifier.amplevels
                               for imt in pgetter.imtls})
        else:
            imtls = pgetter.imtls
    poes, weights = pgetter.poes, pgetter.weights
    M = len(imtls)
    P = len(poes)
    L = imtls.size
    R = len(weights)
    S = len(hstats)
    pmap_by_kind = {}
    if R > 1 and individual_curves or not hstats:
        pmap_by_kind['hcurves-rlzs'] = [ProbabilityMap(L) for r in range(R)]
        if poes:
            pmap_by_kind['hmaps-rlzs'] = [
                ProbabilityMap(M, P) for r in range(R)]
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
                    for r, pc in enumerate(pcurves):
                        hmap = calc.make_hmap(pc, imtls, poes, sid)
                        pmap_by_kind['hmaps-rlzs'][r].update(hmap)
    return pmap_by_kind
