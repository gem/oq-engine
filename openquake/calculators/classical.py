# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
from openquake.baselib import (
    performance, parallel, hdf5, config, python3compat, workerpool as w)
from openquake.baselib.general import (
    AccumDict, DictArray, block_splitter, groupby, humansize)
from openquake.hazardlib import InvalidFile
from openquake.hazardlib.contexts import read_cmakers, basename, get_maxsize
from openquake.hazardlib.calc.hazard_curve import classical as hazclassical
from openquake.hazardlib.calc import disagg
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
slice_dt = numpy.dtype([('sid', U32), ('start', int), ('stop', int)])


def get_pmaps_gb(dstore):
    """
    :returns: memory required on the master node to keep the pmaps
    """
    N = len(dstore['sitecol'])
    L = dstore['oqparam'].imtls.size
    full_lt = dstore['full_lt'].init()
    all_trt_smrs = dstore['trt_smrs'][:]
    trt_rlzs = full_lt.get_trt_rlzs(all_trt_smrs)
    gids = full_lt.get_gids(all_trt_smrs)
    return len(trt_rlzs) * N * L * 8 / 1024**3, trt_rlzs, gids


def build_slice_by_sid(sids, offset=0):
    """
    Convert an array of site IDs (with repetitions) into an array slice_dt
    """
    arr = performance.idx_start_stop(sids)
    sbs = numpy.zeros(len(arr), slice_dt)
    sbs['sid'] = arr[:, 0]
    sbs['start'] = arr[:, 1] + offset
    sbs['stop'] = arr[:, 2] + offset
    return sbs


class Set(set):
    __iadd__ = set.__ior__


def store_ctxs(dstore, rupdata_list, grp_id):
    """
    Store contexts in the datastore
    """
    for rupdata in rupdata_list:
        nr = len(rupdata)
        known = set(rupdata.dtype.names)
        for par in dstore['rup']:
            if par == 'grp_id':
                hdf5.extend(dstore['rup/grp_id'], numpy.full(nr, grp_id))
            elif par == 'probs_occur':
                dstore.hdf5.save_vlen('rup/probs_occur', rupdata[par])
            elif par in known:
                hdf5.extend(dstore['rup/' + par], rupdata[par])
            else:
                hdf5.extend(dstore['rup/' + par], numpy.full(nr, numpy.nan))

#  ########################### task functions ############################ #


def classical(srcs, sitecol, cmaker, monitor):
    """
    Call the classical calculator in hazardlib
    """
    # NB: removing the yield would cause terrible slow tasks
    cmaker.init_monitoring(monitor)
    rup_indep = getattr(srcs, 'rup_interdep', None) != 'mutex'
    
    # maximum size of the pmap array in GB
    size_mb = len(cmaker.gsims) * cmaker.imtls.size * len(sitecol) * 8 / 1024**2
    itiles = int(numpy.ceil(size_mb / cmaker.pmap_max_mb))

    # NB: disagg_by_src is disabled in case of tiling
    assert not (itiles > 1 and cmaker.disagg_by_src)
    for sites in sitecol.split_in_tiles(itiles):
        pmap = ProbabilityMap(
            sites.sids, cmaker.imtls.size, len(cmaker.gsims)).fill(rup_indep)
        result = hazclassical(srcs, sites, cmaker, pmap)
        result['pnemap'] = ~pmap.remove_zeros()
        result['pnemap'].trt_smrs = cmaker.trt_smrs
        yield result


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
    poes, weights, sids = pgetter.poes, pgetter.weights, U32(pgetter.sids)
    M = len(imtls)
    L = imtls.size
    L1 = L // M
    R = len(weights)
    S = len(hstats)
    pmap_by_kind = {}
    if R == 1 or individual_rlzs:
        pmap_by_kind['hcurves-rlzs'] = [
            ProbabilityMap(sids, M, L1).fill(0) for r in range(R)]
    if hstats:
        pmap_by_kind['hcurves-stats'] = [
            ProbabilityMap(sids, M, L1).fill(0) for r in range(S)]
    combine_mon = monitor('combine pmaps', measuremem=False)
    compute_mon = monitor('compute stats', measuremem=False)
    hmaps_mon = monitor('make_hmaps', measuremem=False)
    sidx = ProbabilityMap(sids, 1, 1).fill(0).sidx
    for sid in sids:
        idx = sidx[sid]
        with combine_mon:
            pc = pgetter.get_pcurve(sid)  # shape (L, R)
            if amplifier:
                pc = amplifier.amplify(ampcode[sid], pc)
                # NB: the pcurve have soil levels != IMT levels
        if pc.array.sum() == 0:  # no data
            continue
        with compute_mon:
            if R == 1 or individual_rlzs:
                for r in range(R):
                    pmap_by_kind['hcurves-rlzs'][r].array[idx] = (
                        pc.array[:, r].reshape(M, L1))
            if hstats:
                for s, (statname, stat) in enumerate(hstats.items()):
                    sc = getters.build_stat_curve(
                        pc, imtls, stat, weights, pgetter.use_rates)
                    arr = sc.array.reshape(M, L1)
                    pmap_by_kind['hcurves-stats'][s].array[idx] = arr

    if poes and (R == 1 or individual_rlzs):
        with hmaps_mon:
            pmap_by_kind['hmaps-rlzs'] = calc.make_hmaps(
                pmap_by_kind['hcurves-rlzs'], imtls, poes)
    if poes and hstats:
        with hmaps_mon:
            pmap_by_kind['hmaps-stats'] = calc.make_hmaps(
                pmap_by_kind['hcurves-stats'], imtls, poes)
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
        oq = dstore['oqparam']
        self.full_lt = full_lt
        self.weights = full_lt.rlzs['weight']
        self.imtls = oq.imtls
        self.level_weights = oq.imtls.array.flatten() / oq.imtls.array.sum()
        self.sids = dstore['sitecol/sids'][:]
        self.srcidx = srcidx
        self.N = len(dstore['sitecol/sids'])
        self.M = len(oq.imtls)
        self.L = oq.imtls.size
        self.L1 = self.L // self.M
        self.R = full_lt.get_num_paths()
        self.acc = AccumDict(accum={})
        self.offset = 0

    # used in in disagg_by_src
    def get_rates(self, pmap):
        """
        :param pmap: a ProbabilityMap
        :returns: an array of rates of shape (N, M, L1)
        """
        out = numpy.zeros((self.N, self.L))
        rates = disagg.to_rates(pmap.array)  # shape (N, L, G)
        for trt_smr in pmap.trt_smrs:
            allrlzs = self.full_lt.get_rlzs_by_gsim(trt_smr).values()
            for i, rlzs in enumerate(allrlzs):
                out[:, :] += rates[:, :, i] * self.weights[rlzs].sum()
        return out.reshape((self.N, self.M, self.L1))

    def store_poes(self, pnes, the_sids):
        """
        Store 1-pnes inside the _poes dataset
        """
        avg_poe = 0
        # store by IMT to save memory
        for imt in self.imtls:
            slc = self.imtls(imt)
            poes = 1. - pnes[:, slc]
            # Physically, an extremely small intensity measure level can have an
            # extremely large probability of exceedence,however that probability
            # cannot be exactly 1 unless the level is exactly 0. Numerically,
            # the PoE can be 1 and this give issues when calculating the damage:
            # there is a log(0) in scientific.annual_frequency_of_exceedence.
            # Here we solve the issue by replacing the unphysical probabilities
            # 1 with .9999999999999999 (the float64 closest to 1).
            poes[poes == 1.] = .9999999999999999
            # the nonzero below uses a lot of memory, however it is useful
            # to reduce the storage a lot (~3 times for EUR)
            idxs, lids, gids = poes.nonzero()
            if len(idxs) == 0:  # happens in case_60
                return 0
            sids = the_sids[idxs]
            hdf5.extend(self.datastore['_poes/sid'], sids)
            hdf5.extend(self.datastore['_poes/gid'], gids)
            hdf5.extend(self.datastore['_poes/lid'], lids + slc.start)
            hdf5.extend(self.datastore['_poes/poe'], poes[idxs, lids, gids])

            # slice_by_sid contains 3x6=18 slices in classical/case_22
            # which has 6 IMTs each one with 20 levels
            sbs = build_slice_by_sid(sids, self.offset)
            hdf5.extend(self.datastore['_poes/slice_by_sid'], sbs)
            self.offset += len(sids)
            avg_poe += poes.mean(axis=(0, 2)) @ self.level_weights[slc]
        self.acc['avg_poe'] = avg_poe
        self.acc['nsites'] = self.offset
        return self.offset * 16  # 4 + 2 + 2 + 8 bytes

    def store_disagg(self, pmaps):
        """
        Store data inside mean_rates_by_src
        """
        mean_rates_by_src = self.datastore['mean_rates_by_src/array'][()]
        for key, pmap in pmaps.items():
            if isinstance(key, str):
                # in case of mean_rates_by_src key is a source ID
                idx = self.srcidx[basename(key, '!;:')]
                mean_rates_by_src[..., idx] += self.get_rates(pmap)
        self.datastore['mean_rates_by_src/array'][:] = mean_rates_by_src


@base.calculators.add('classical', 'ucerf_classical')
class ClassicalCalculator(base.HazardCalculator):
    """
    Classical PSHA calculator
    """
    core_task = classical
    precalc = 'preclassical'
    accept_precalc = ['preclassical', 'classical', 'aftershock']
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
        cfactor = dic.pop('cfactor')
        if cfactor[1] != cfactor[0]:
            print('ctxs_per_mag = {:.0f}, cfactor_per_task = {:.1f}'.format(
                cfactor[1] / cfactor[2], cfactor[1] / cfactor[0]))
        self.cfactor += cfactor

        # store rup_data if there are few sites
        if self.few_sites and len(dic['rup_data']):
            with self.monitor('saving rup_data'):
                store_ctxs(self.datastore, dic['rup_data'], grp_id)

        pnemap = dic['pnemap']  # probabilities of no exceedence
        pmap_by_src = dic.pop('pmap_by_src', {})  # non-empty for disagg_by_src
        # len(pmap_by_src) > 1 only for mutex sources, see contexts.py
        for source_id, pm in pmap_by_src.items():
            # store the poes for the given source
            acc[source_id] = pm
            pm.grp_id = grp_id
            pm.trt_smrs = pnemap.trt_smrs
        G = pnemap.array.shape[2]
        for i, gid in enumerate(self.gids[grp_id]):
            self.pmap.multiply_pnes(pnemap, gid, i % G)
        return acc

    def create_rup(self):
        """
        Create the rup datasets *before* starting the calculation
        """
        params = {'grp_id', 'occurrence_rate', 'clon', 'clat', 'rrup',
                  'probs_occur', 'sids', 'src_id', 'rup_id', 'weight'}
        for cm in self.cmakers:
            params.update(cm.REQUIRES_RUPTURE_PARAMETERS)
            params.update(cm.REQUIRES_DISTANCES)
        if self.few_sites:
            descr = []  # (param, dt)
            for param in sorted(params):
                if param == 'sids':
                    dt = U16  # storing only for few sites
                elif param == 'probs_occur':
                    dt = hdf5.vfloat64
                elif param in ('src_id', 'rup_id'):
                    dt = U32
                elif param == 'grp_id':
                    dt = U16
                else:
                    dt = F32
                descr.append((param, dt))
            self.datastore.create_df('rup', descr, 'gzip')
        # NB: the relevant ruptures are less than the effective ruptures,
        # which are a preclassical concept

    def init_poes(self):
        self.cmakers = read_cmakers(self.datastore, self.csm)
        self.cfactor = numpy.zeros(3)
        self.rel_ruptures = AccumDict(accum=0)  # grp_id -> rel_ruptures
        self.datastore.create_df('_poes', poes_dt.items())
        self.datastore.create_dset('_poes/slice_by_sid', slice_dt)
        # NB: compressing the dataset causes a big slowdown in writing :-(

        oq = self.oqparam
        if oq.disagg_by_src:
            M = len(oq.imtls)
            L1 = oq.imtls.size // M
            sources = self.csm.get_basenames()
            mean_rates_by_src = numpy.zeros((self.N, M, L1, len(sources)))
            dic = dict(shape_descr=['site_id', 'imt', 'lvl', 'src_id'],
                       site_id=self.N, imt=list(oq.imtls),
                       lvl=L1, src_id=numpy.array(sources))
            self.datastore['mean_rates_by_src'] = hdf5.ArrayWrapper(
                mean_rates_by_src, dic)

    def check_memory(self, N, L, maxw):
        """
        Log the memory required to receive the largest ProbabilityMap,
        assuming all sites are affected (upper limit)
        """
        num_gs = [len(cm.gsims) for cm in self.cmakers]
        max_gs = max(num_gs)
        maxsize = get_maxsize(len(self.oqparam.imtls), max_gs)
        logging.info('Considering {:_d} contexts at once'.format(maxsize))
        size = max_gs * N * L * 8
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
            logging.info('Reading from parent calculation')
            parent = self.datastore.parent
            self.full_lt = parent['full_lt'].init()
            self.csm = parent['_csm']
            self.csm.init(self.full_lt)
            self.datastore['source_info'] = parent['source_info'][:]
            maxw = self.csm.get_max_weight(oq)
            oq.mags_by_trt = {
                trt: python3compat.decode(dset[:])
                for trt, dset in parent['source_mags'].items()}
            if '_poes' in parent:
                self.build_curves_maps()  # repeat post-processing
                return {}
        else:
            maxw = self.max_weight
        self.init_poes()
        srcidx = {name: i for i, name in enumerate(self.csm.get_basenames())}
        self.haz = Hazard(self.datastore, self.full_lt, srcidx)
        rlzs = self.haz.R == 1 or oq.individual_rlzs
        if not rlzs and not oq.hazard_stats():
            raise InvalidFile('%(job_ini)s: you disabled all statistics',
                              oq.inputs)
        self.source_data = AccumDict(accum=[])
        if not performance.numba:
            logging.warning('numba is not installed: using the slow algorithm')

        t0 = time.time()
        req_gb, self.trt_rlzs, self.gids = get_pmaps_gb(self.datastore)
        self.ntiles = 1 + int(req_gb / oq.pmap_max_mb)  # 50 GB
        if self.ntiles > 1:
            self.execute_seq(maxw)
        else:  # regular case
            self.check_memory(len(self.sitecol), oq.imtls.size, maxw)
            self.execute_par(maxw)
        self.store_info()
        if self.cfactor[0] == 0:
            raise RuntimeError('There are no ruptures close to the site(s)')
        logging.info('cfactor = {:_d}/{:_d} = {:.1f}'.format(
            int(self.cfactor[1]), int(self.cfactor[0]),
            self.cfactor[1] / self.cfactor[0]))
        if '_poes' in self.datastore:
            self.build_curves_maps()
        if not oq.hazard_calculation_id:
            self.classical_time = time.time() - t0
        return True

    def execute_par(self, maxw):
        """
        Regular case
        """
        self.create_rup()  # create the rup/ datasets BEFORE swmr_on()
        acc = self.run_one(self.sitecol, maxw)
        if self.oqparam.disagg_by_src:
            self.haz.store_disagg(acc)

    def execute_seq(self, maxw):
        """
        Use sequential tiling
        """
        assert self.N > self.oqparam.max_sites_disagg, self.N
        logging.info('Running %d tiles', self.ntiles)
        for n, tile in enumerate(self.sitecol.split(self.ntiles)):
            if n == 0:
                self.check_memory(len(tile), self.oqparam.imtls.size, maxw)
            self.run_one(tile, maxw)
            logging.info('Finished tile %d of %d', n+1, self.ntiles)
            if parallel.oq_distribute() == 'zmq':
                w.WorkerMaster(config.zworkers).restart()
            else:
                parallel.Starmap.shutdown()

    def run_one(self, sitecol, maxw):
        """
        Run a subset of sites and update the accumulator
        """
        acc = {}  # src_id -> pmap
        oq = self.oqparam
        L = oq.imtls.size
        Gt = len(self.trt_rlzs)
        nbytes = 8 * len(sitecol) * L * Gt
        logging.info(f'Allocating %s for the global pmap ({Gt=})',
                     humansize(nbytes))
        self.pmap = ProbabilityMap(sitecol.sids, L, Gt).fill(1)
        allargs = []
        for cm in self.cmakers:
            cm.pmap_max_mb = oq.pmap_max_mb
            sg = self.csm.src_groups[cm.grp_id]
            if oq.disagg_by_src:  # possible only with a single tile
                blks = groupby(sg, basename).values()
            elif sg.atomic or sg.weight <= maxw:
                blks = [sg]
            else:
                blks = block_splitter(sg, maxw, get_weight, sort=True)
            for block in blks:
                logging.debug('Sending %d source(s) with weight %d',
                              len(block), sg.weight)
                allargs.append((block, sitecol, cm))

        self.datastore.swmr_on()  # must come before the Starmap
        smap = parallel.Starmap(classical, allargs, h5=self.datastore.hdf5)
        acc = smap.reduce(self.agg_dicts, acc)
        with self.monitor('storing PoEs', measuremem=True):
            nbytes = self.haz.store_poes(self.pmap.array, self.pmap.sids)
        logging.info('Stored %s of PoEs', humansize(nbytes))
        del self.pmap
        return acc

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
                array = self.hazard[kind] = numpy.zeros(dset.shape, dset.dtype)
            for r, pmap in enumerate(pmaps):
                for idx, sid in enumerate(pmap.sids):
                    array[sid, r] = pmap.array[idx]  # shape (M, P)

    def post_execute(self, dummy):
        """
        Check for slow tasks
        """
        oq = self.oqparam
        task_info = self.datastore.read_df('task_info', 'taskname')
        try:
            dur = task_info.loc[b'classical'].duration
        except KeyError:  # no data
            pass
        else:
            slow_tasks = len(dur[dur > 3 * dur.mean()]) and dur.max() > 180
            msg = 'There were %d slow task(s)' % slow_tasks
            if slow_tasks and self.SLOW_TASK_ERROR and not oq.disagg_by_src:
                raise RuntimeError('%s in #%d' % (msg, self.datastore.calc_id))
            elif slow_tasks:
                logging.info(msg)

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
        if R == 1 or individual_rlzs:
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

    # called by execute before post_execute
    def build_curves_maps(self):
        """
        Compute and store hcurves-rlzs, hcurves-stats, hmaps-rlzs, hmaps-stats
        """
        oq = self.oqparam
        hstats = oq.hazard_stats()
        if not oq.hazard_curves:  # do nothing
            return
        N, S, M, P, L1, individual = self._create_hcurves_maps()
        poes_gb = self.datastore.getsize('_poes') / 1024**3
        if poes_gb < .1:
            ct = 1
        elif poes_gb < 2:
            ct = int(poes_gb * 10)
        else:
            ct = int(poes_gb) + 18  # number of tasks > number of GB
        if ct > 1:
            logging.info('Producing %d postclassical tasks', ct)
        if '_poes' in set(self.datastore):
            dstore = self.datastore
        else:
            dstore = self.datastore.parent
        sites_per_task = int(numpy.ceil(self.N / ct))
        sbs = dstore['_poes/slice_by_sid'][:]
        sbs['sid'] //= sites_per_task
        # NB: there is a genious idea here, to split in tasks by using
        # the formula ``taskno = sites_ids // sites_per_task`` and then
        # extracting a dictionary of slices for each taskno. This works
        # since by construction the site_ids are sequential and there are
        # at most G slices per task. For instance if there are 6 sites
        # disposed in 2 groups and we want to produce 2 tasks we can use
        # 012345012345 // 3 = 000111000111 and the slices are
        # {0: [(0, 3), (6, 9)], 1: [(3, 6), (9, 12)]}
        slicedic = AccumDict(accum=[])
        for idx, start, stop in sbs:
            slicedic[idx].append((start, stop))
        if not slicedic:
            # no hazard, nothing to do, happens in case_60
            return

        # using compactify improves the performance of `read PoEs`;
        # I have measured a 3.5x in the AUS model with 1 rlz
        allslices = [calc.compactify(slices) for slices in slicedic.values()]
        nslices = sum(len(slices) for slices in allslices)
        logging.info('There are %d slices of poes [%.1f per task]',
                     nslices, nslices / len(slicedic))
        allargs = [
            (getters.PmapGetter(dstore, self.full_lt, slices,
                                oq.imtls, oq.poes, oq.use_rates),
             N, hstats, individual, oq.max_sites_disagg, self.amplifier)
            for slices in allslices]
        self.hazard = {}  # kind -> array
        hcbytes = 8 * N * S * M * L1
        hmbytes = 8 * N * S * M * P if oq.poes else 0
        if hcbytes:
            logging.info('Producing %s of hazard curves', humansize(hcbytes))
        if hmbytes:
            logging.info('Producing %s of hazard maps', humansize(hmbytes))
        if not performance.numba:
            logging.warning('numba is not installed: using the slow algorithm')
        if 'delta_rates' in self.datastore.parent:
            pass  # do nothing for the aftershock calculator, avoids an error
        else:  # in all the other cases
            self.datastore.swmr_on()
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

        # generate hazard map plots
        if 'hmaps-stats' in self.datastore and self.N > 1000:
            hmaps = self.datastore.sel('hmaps-stats', stat='mean')  # NSMP
            maxhaz = hmaps.max(axis=(0, 1, 3))
            mh = dict(zip(self.oqparam.imtls, maxhaz))
            logging.info('The maximum hazard map values are %s', mh)
            if Image is None or not self.from_engine:  # missing PIL
                return
            if self.N < 1000:  # few sites, don't plot
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
