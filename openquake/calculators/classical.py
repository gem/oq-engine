# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2022 GEM Foundation
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
import time
import psutil
import logging
import operator
import numpy
import pandas
try:
    from PIL import Image
except ImportError:
    Image = None
from openquake.baselib import performance, parallel, hdf5, config
from openquake.baselib.general import (
    AccumDict, DictArray, block_splitter, groupby, humansize,
    get_nbytes_msg, agg_probs)
from openquake.hazardlib.contexts import ContextMaker, read_cmakers
from openquake.hazardlib.calc.hazard_curve import classical as hazclassical
from openquake.hazardlib.probability_map import ProbabilityMap, poes_dt
from openquake.commonlib import calc
from openquake.calculators import base, getters

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
I64 = numpy.int64
TWO32 = 2 ** 32
BUFFER = 1.5  # enlarge the pointsource_distance sphere to fix the weight;
# with BUFFER = 1 we would have lots of apparently light sources
# collected together in an extra-slow task, as it happens in SHARE
# with ps_grid_spacing=50
get_weight = operator.attrgetter('weight')
disagg_grp_dt = numpy.dtype([
    ('grp_start', U16), ('grp_trt', hdf5.vstr), ('avg_poe', F32),
    ('nsites', U32)])


class Set(set):
    __iadd__ = set.__ior__


def get_source_id(src):  # used in submit_tasks
    return src.source_id.split(':')[0]


def store_ctxs(dstore, rupdata, grp_id):
    """
    Store contexts with the same magnitude in the datastore
    """
    nr = len(rupdata['mag'])
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


def classical(srcs, sids, cmaker, monitor):
    """
    Read the sitecol and call the classical calculator in hazardlib
    """
    cmaker.init_monitoring(monitor)
    sitecol = monitor.read('sitecol')
    if sids is not None:
        sitecol = sitecol.filter(numpy.isin(sitecol.sids, sids))
    result = hazclassical(srcs, sitecol, cmaker)
    # print(srcs, sum(src.weight for src in srcs))
    return result


def postclassical(pgetter, N, hstats, individual_rlzs,
                  max_sites_disagg, amplifier, monitor):
    """
    :param pgetter: an :class:`openquake.commonlib.getters.PmapGetter`
    :param N: the total number of sites
    :param hstats: a list of pairs (statname, statfunc)
    :param individual_rlzs: if True, also build the individual curves
    :param max_sites_disagg: if there are less sites than this, store rup info
    :param amplifier: instance of Amplifier or None
    :param monitor: instance of Monitor
    :returns: a dictionary kind -> ProbabilityMap

    The "kind" is a string of the form 'rlz-XXX' or 'mean' of 'quantile-XXX'
    used to specify the kind of output.
    """
    with monitor('read PoEs', measuremem=True):
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
    if R > 1 and individual_rlzs or not hstats:
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
            pc = pgetter.get_pcurve(sid)  # shape (L, R)
            if amplifier:
                pc = amplifier.amplify(ampcode[sid], pc)
                # NB: the pcurve have soil levels != IMT levels
        if pc.array.sum() == 0:  # no data
            continue
        with compute_mon:
            if hstats:
                for s, (statname, stat) in enumerate(hstats.items()):
                    sc = getters.build_stat_curve(pc, imtls, stat, weights)
                    pmap_by_kind['hcurves-stats'][s][sid] = sc
                    if poes:
                        hmap = calc.make_hmap(sc, imtls, poes, sid)
                        pmap_by_kind['hmaps-stats'][s].update(hmap)
            if R > 1 and individual_rlzs or not hstats:
                for r, pmap in enumerate(pmap_by_kind['hcurves-rlzs']):
                    pmap[sid] = pc.extract(r)
                if poes:
                    for r in range(R):
                        hmap = calc.make_hmap(pc.extract(r), imtls, poes, sid)
                        pmap_by_kind['hmaps-rlzs'][r].update(hmap)
    return pmap_by_kind


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


class Hazard:
    """
    Helper class for storing the PoEs
    """
    def __init__(self, dstore, full_lt, srcidx):
        self.datastore = dstore
        self.full_lt = full_lt
        self.cmakers = read_cmakers(dstore, full_lt)
        self.imtls = imtls = dstore['oqparam'].imtls
        self.level_weights = imtls.array.flatten() / imtls.array.sum()
        self.sids = dstore['sitecol/sids'][:]
        self.srcidx = srcidx
        self.N = len(dstore['sitecol/sids'])
        self.R = full_lt.get_num_paths()
        self.acc = AccumDict(accum={})

    def get_hcurves(self, pmap, rlzs_by_gsim):  # used in in disagg_by_src
        """
        :param pmap: a ProbabilityMap
        :param rlzs_by_gsim: a dictionary gsim -> rlz IDs
        :returns: an array of PoEs of shape (N, R, M, L)
        """
        res = numpy.zeros((self.N, self.R, self.imtls.size))
        for sid, pc in pmap.items():
            for gsim_idx, rlzis in enumerate(rlzs_by_gsim.values()):
                poes = pc.array[:, gsim_idx]
                for rlz in rlzis:
                    res[sid, rlz] = agg_probs(res[sid, rlz], poes)
        return res.reshape(self.N, self.R, len(self.imtls), -1)

    def store_poes(self, grp_id, pmap):
        """
        Store the pmap of the given group inside the _poes dataset
        """
        cmaker = self.cmakers[grp_id]
        arr = pmap.array(self.N)
        # arr[arr < 1E-5] = 0.  # minimum_poe
        sids, lids, gids = arr.nonzero()
        hdf5.extend(self.datastore['_poes/sid'], sids)
        hdf5.extend(self.datastore['_poes/gid'], gids + cmaker.start)
        hdf5.extend(self.datastore['_poes/lid'], lids)
        hdf5.extend(self.datastore['_poes/poe'], arr[sids, lids, gids])
        self.acc[grp_id]['grp_start'] = cmaker.start
        self.acc[grp_id]['avg_poe'] = arr.mean(axis=(0, 2))@self.level_weights
        self.acc[grp_id]['nsites'] = len(pmap)

    def store_disagg(self, pmaps=None):
        """
        Store data inside disagg_by_grp (optionally disagg_by_src)
        """
        n = len(self.full_lt.sm_rlzs)
        lst = []
        for grp_id, indices in enumerate(self.datastore['trt_smrs']):
            dic = self.acc[grp_id]
            if dic:
                trti, smrs = numpy.divmod(indices, n)
                trt = self.full_lt.trts[trti[0]]
                lst.append((dic['grp_start'], trt, dic['avg_poe'],
                            dic['nsites']))
        self.datastore['disagg_by_grp'] = numpy.array(lst, disagg_grp_dt)

        if pmaps:  # called inside a loop
            for key, pmap in pmaps.items():
                if isinstance(key, str):
                    # contains only string keys in case of disaggregation
                    rlzs_by_gsim = self.cmakers[pmap.grp_id].gsims
                    # works because disagg_by_src disables submit_split
                    self.datastore['disagg_by_src'][..., self.srcidx[key]] = (
                        self.get_hcurves(pmap, rlzs_by_gsim))


@base.calculators.add('classical', 'ucerf_classical')
class ClassicalCalculator(base.HazardCalculator):
    """
    Classical PSHA calculator
    """
    core_task = classical
    precalc = 'preclassical'
    accept_precalc = ['preclassical', 'classical']
    SLOW_TASK_ERROR = False

    def agg_dicts(self, acc, dic):
        """
        Aggregate dictionaries of hazard curves by updating the accumulator.

        :param acc: accumulator dictionary
        :param dic: dict with keys pmap, source_data, rup_data
        """
        # NB: dic should be a dictionary, but when the calculation dies
        # for an OOM it can become None, thus giving a very confusing error
        if dic is None:
            raise MemoryError('You ran out of memory!')

        sdata = dic['source_data']
        self.source_data += sdata
        grp_id = dic.pop('grp_id')
        self.rel_ruptures[grp_id] += sum(sdata['nrupts'])
        self.cfactor += dic.pop('cfactor')

        # store rup_data if there are few sites
        if self.few_sites and len(dic['rup_data']['src_id']):
            with self.monitor('saving rup_data'):
                store_ctxs(self.datastore, dic['rup_data'], grp_id)

        pmap = dic['pmap']
        pmap.grp_id = grp_id
        source_id = dic.pop('source_id', None)
        if source_id:
            # store the poes for the given source
            acc[source_id.split(':')[0]] = pmap
        if pmap:
            acc[grp_id] |= pmap
        self.n_outs[grp_id] -= 1
        if self.n_outs[grp_id] == 0:  # no other tasks for this grp_id
            with self.monitor('storing PoEs', measuremem=True):
                self.haz.store_poes(grp_id, acc.pop(grp_id))
        return acc

    def create_dsets(self):
        """
        Store some empty datasets in the datastore
        """
        self.init_poes()
        params = {'grp_id', 'occurrence_rate', 'clon_', 'clat_', 'rrup_',
                  'probs_occur_', 'sids_', 'src_id'}
        gsims_by_trt = self.full_lt.get_gsims_by_trt()

        for trt, gsims in gsims_by_trt.items():
            cm = ContextMaker(trt, gsims, self.oqparam)
            params.update(cm.REQUIRES_RUPTURE_PARAMETERS)
            for dparam in cm.REQUIRES_DISTANCES:
                params.add(dparam + '_')
        if self.few_sites:
            # self.oqparam.time_per_task = 1_000_000  # disable task splitting
            descr = [('id', I64)]  # (param, dt)
            for param in params:
                if param == 'sids_':
                    dt = hdf5.vuint16
                elif param == 'probs_occur_':
                    dt = hdf5.vfloat64
                elif param.endswith('_'):
                    dt = hdf5.vfloat32
                elif param == 'src_id':
                    dt = U32
                elif param == 'grp_id':
                    dt = U16
                else:
                    dt = F32
                descr.append((param, dt))
            self.datastore.create_df('rup', descr, 'gzip')
        self.Ns = len(self.csm.source_info)
        self.cfactor = numpy.zeros(2)
        self.rel_ruptures = AccumDict(accum=0)  # grp_id -> rel_ruptures
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
        sources = list(self.csm.source_info)
        size, msg = get_nbytes_msg(
            dict(N=self.N, R=self.R, M=self.M, L1=self.L1, Ns=self.Ns))
        ps = any(src.code == b'P' for src in self.csm.get_sources())
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

    def init_poes(self):
        if self.oqparam.hazard_calculation_id:
            full_lt = self.datastore.parent['full_lt']
            trt_smrs = self.datastore.parent['trt_smrs'][:]
        else:
            full_lt = self.csm.full_lt
            trt_smrs = self.csm.get_trt_smrs()
        self.grp_ids = numpy.arange(len(trt_smrs))
        rlzs_by_gsim_list = full_lt.get_rlzs_by_gsim_list(trt_smrs)
        rlzs_by_g = []
        for rlzs_by_gsim in rlzs_by_gsim_list:
            for rlzs in rlzs_by_gsim.values():
                rlzs_by_g.append(rlzs)
        self.datastore.create_df('_poes', poes_dt.items())
        # NB: compressing the dataset causes a big slowdown in writing :-(
        if not self.oqparam.hazard_calculation_id:
            self.datastore.swmr_on()

    def check_memory(self, N, L, num_gs):
        """
        Log the memory required to receive the largest ProbabilityMap,
        assuming all sites are affected (upper limit)
        """
        G = max(num_gs)
        size = G * N * L * 8
        # for ESHM20 there are 95,000 sites and up to 72,000 can be affected
        logging.info('Requiring %s for full ProbabilityMap of shape %s',
                     humansize(size), (G, N, L))
        avail = min(psutil.virtual_memory().available, config.memory.limit)
        if avail < size:
            raise MemoryError(
                'You have only %s of free RAM' % humansize(avail))

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the sources according to their weight and
        tectonic region type.
        """
        oq = self.oqparam
        if oq.hazard_calculation_id:
            parent = self.datastore.parent
            if '_poes' in parent:
                self.post_classical()  # repeat post-processing
                return {}
            else:  # after preclassical, like in case_36
                self.csm = parent['_csm']
                self.full_lt = parent['full_lt']
                self.datastore['source_info'] = parent['source_info'][:]
                max_weight = self.csm.get_max_weight(oq)
        else:
            max_weight = self.max_weight
        self.create_dsets()  # create the rup/ datasets BEFORE swmr_on()
        srcidx = {
            rec[0]: i for i, rec in enumerate(self.csm.source_info.values())}
        self.haz = Hazard(self.datastore, self.full_lt, srcidx)
        # only groups generating more than 1 task preallocate memory
        num_gs = [len(cm.gsims) for grp, cm in enumerate(self.haz.cmakers)]
        L = oq.imtls.size
        tiles = self.sitecol.split_max(oq.max_sites_per_tile)
        if len(tiles) > 1:
            sizes = [len(tile) for tile in tiles]
            logging.info('There are %d tiles of sizes %s', len(tiles), sizes)
            for size in sizes:
                assert size > oq.max_sites_disagg, (size, oq.max_sites_disagg)
        self.source_data = AccumDict(accum=[])
        self.n_outs = AccumDict(accum=0)
        acc = {}
        t0 = time.time()
        for t, tile in enumerate(tiles, 1):
            self.check_memory(len(tile), L, num_gs)
            sids = tile.sids if len(tiles) > 1 else None
            smap = self.submit(sids, self.haz.cmakers, max_weight)
            for cm in self.haz.cmakers:
                acc[cm.grp_id] = ProbabilityMap.build(L, len(cm.gsims))
            smap.reduce(self.agg_dicts, acc)
            if len(tiles) > 1:
                logging.info('Finished tile %d of %d', t, len(tiles))
        self.store_info()
        self.haz.store_disagg(acc)
        logging.info('cfactor = {:_d}/{:_d} = {:.1f}'.format(
            int(self.cfactor[1]), int(self.cfactor[0]),
            self.cfactor[1] / self.cfactor[0]))
        if not oq.hazard_calculation_id:
            self.classical_time = time.time() - t0
        return True

    def store_info(self):
        """
        Store full_lt, source_info and source_data
        """
        self.store_rlz_info(self.rel_ruptures)
        self.store_source_info(self.source_data)
        df = pandas.DataFrame(self.source_data)
        # NB: the impact factor is the number of effective ruptures;
        # consider for instance a point source producing 200 ruptures
        # for points within the pointsource_distance (n points) and
        # producing 20 effective ruptures for the N-n points outside;
        # then impact = (200 * n + 20 * (N-n)) / N; for n=1 and N=10
        # it gives impact = 38, i.e. there are 38 effective ruptures
        df['impact'] = df.nsites / self.N
        self.datastore.create_df('source_data', df)
        self.source_data.clear()  # save a bit of memory

    def submit(self, sids, cmakers, max_weight):
        """
        :returns: a Starmap instance for the current tile
        """
        oq = self.oqparam
        self.datastore.swmr_on()  # must come before the Starmap
        smap = parallel.Starmap(classical, h5=self.datastore.hdf5)
        smap.monitor.save('sitecol', self.sitecol)
        triples = []
        for grp_id in self.grp_ids:
            sg = self.csm.src_groups[grp_id]
            if sg.atomic:
                # do not split atomic groups
                trip = (sg, sids, cmakers[grp_id])
                triples.append(trip)
                smap.submit(trip)
                self.n_outs[grp_id] += 1
            else:  # regroup the sources in blocks
                blks = (groupby(sg, get_source_id).values()
                        if oq.disagg_by_src else
                        block_splitter(
                            sg, max_weight, get_weight, sort=True))
                blocks = list(blks)
                for block in blocks:
                    logging.debug(
                        'Sending %d source(s) with weight %d',
                        len(block), sum(src.weight for src in block))
                    trip = (block, sids, cmakers[grp_id])
                    triples.append(trip)
                    # outs = (oq.outs_per_task if len(block) >= oq.outs_per_task
                    #         else len(block))
                    # if outs > 1 and not oq.disagg_by_src:
                    #     smap.submit_split(trip, oq.time_per_task, outs)
                    #     self.n_outs[grp_id] += outs
                    # else:
                    smap.submit(trip)
                    self.n_outs[grp_id] += 1
        logging.info('grp_id->n_outs: %s', list(self.n_outs.values()))
        return smap

    def collect_hazard(self, acc, pmap_by_kind):
        """
        Populate hcurves and hmaps in the .hazard dictionary

        :param acc: ignored
        :param pmap_by_kind: a dictionary of ProbabilityMaps
        """
        # this is practically instantaneous
        if pmap_by_kind is None:  # instead of a dict
            raise MemoryError('You ran out of memory!')
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
                    else:  # hcurves
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
            slow_tasks = len(dur[dur > 3 * dur.mean()]) and dur.max() > 180
            msg = 'There were %d slow task(s)' % slow_tasks
            if (slow_tasks and self.SLOW_TASK_ERROR and
                    not self.oqparam.disagg_by_src):
                raise RuntimeError('%s in #%d' % (msg, self.datastore.calc_id))
            elif slow_tasks:
                logging.info(msg)

        # sanity check on the rupture IDs
        if 'rup' in self.datastore:
            rup_id = self.datastore['rup/id']
            tot = len(rup_id)
            logging.info('Stored {:_d} ruptures'.format(tot))
            if 0 < tot < 1_000_000:
                uniq = len(numpy.unique(rup_id[:]))
                assert tot == uniq, (tot, uniq)

        if '_poes' in self.datastore:
            self.post_classical()

    def _create_hcurves_maps(self):
        oq = self.oqparam
        N = len(self.sitecol)
        R = len(self.realizations)
        if oq.individual_rlzs is None:  # not specified in the job.ini
            individual_rlzs = (N == 1) * (R > 1)
        else:
            individual_rlzs = oq.individual_rlzs
        hstats = oq.hazard_stats()
        # initialize datasets
        P = len(oq.poes)
        M = self.M = len(oq.imtls)
        imts = list(oq.imtls)
        if oq.soil_intensities is not None:
            L = M * len(oq.soil_intensities)
        else:
            L = oq.imtls.size
        L1 = self.L1 = L // M
        S = len(hstats)
        if R > 1 and individual_rlzs or not hstats:
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
        return N, S, M, P, L1, individual_rlzs

    def post_classical(self):
        """
        Store hcurves-rlzs, hcurves-stats, hmaps-rlzs, hmaps-stats
        """
        oq = self.oqparam
        hstats = oq.hazard_stats()
        if not oq.hazard_curves:  # do nothing
            return
        N, S, M, P, L1, individual = self._create_hcurves_maps()
        ct = oq.concurrent_tasks or 1
        if 1 < ct <= 20:  # saving memory on small machines
            ct = 60
        self.weights = ws = [rlz.weight for rlz in self.realizations]
        if '_poes' in set(self.datastore):
            dstore = self.datastore
        else:
            dstore = self.datastore.parent
        sites_per_task = int(numpy.ceil(self.N / ct))
        nbytes = len(dstore['_poes/sid']) * 4
        logging.info('Reading %s of _poes/sid', humansize(nbytes))
        # NB: there is a genious idea here, to split in tasks by using
        # the formula ``taskno = sites_ids // sites_per_task`` and then
        # extracting a dictionary of slices for each taskno. This works
        # since by construction the site_ids are sequential and there are
        # at most G slices per task. For instance if there are 6 sites
        # disposed in 2 groups and we want to produce 2 tasks we can use
        # 012345012345 // 3 = 000111000111 and the slices are
        # {0: [(0, 3), (6, 9)], 1: [(3, 6), (9, 12)]}
        slicedic = performance.get_slices(
            dstore['_poes/sid'][:] // sites_per_task)
        if not slicedic:
            # no hazard, nothing to do, happens in case_60
            return
        nslices = sum(len(slices) for slices in slicedic.values())
        logging.info('There are %d slices of poes [%.1f per task]',
                     nslices, nslices / len(slicedic))
        allargs = [
            (getters.PmapGetter(dstore, ws, slices, oq.imtls, oq.poes),
             N, hstats, individual, oq.max_sites_disagg, self.amplifier)
            for slices in slicedic.values()]
        self.hazard = {}  # kind -> array
        hcbytes = 8 * N * S * M * L1
        hmbytes = 8 * N * S * M * P if oq.poes else 0
        logging.info('Producing %s of hazard curves and %s of hazard maps',
                     humansize(hcbytes), humansize(hmbytes))
        if not performance.numba:
            logging.info('numba is not installed: using the slow algorithm')
        self.datastore.swmr_on()  # essential before Starmap
        parallel.Starmap(
            postclassical, allargs,
            distribute='no' if self.few_sites else None,
            h5=self.datastore.hdf5,
        ).reduce(self.collect_hazard)
        for kind in sorted(self.hazard):
            logging.info('Saving %s', kind)  # very fast
            self.datastore[kind][:] = self.hazard.pop(kind)

        fraction = os.environ.get('OQ_SAMPLE_SOURCES')
        if fraction and hasattr(self, 'classical_time'):
            total_time = time.time() - self.t0
            delta = total_time - self.classical_time
            est_time = self.classical_time / float(fraction) + delta
            logging.info('Estimated time: %.1f hours', est_time / 3600)

        # generate plots
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
