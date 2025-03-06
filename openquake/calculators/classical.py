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
import time
import zlib
import pickle
import psutil
import logging
import operator
import numpy
import pandas
from PIL import Image
from openquake.baselib import parallel, hdf5, config, python3compat
from openquake.baselib.general import (
    AccumDict, DictArray, groupby, humansize, block_splitter)
from openquake.hazardlib import valid, InvalidFile
from openquake.hazardlib.contexts import read_cmakers
from openquake.hazardlib.calc.hazard_curve import classical as hazclassical
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.map_array import RateMap, MapArray, rates_dt, check_hmaps
from openquake.commonlib import calc
from openquake.calculators import base, getters, preclassical, views

get_weight = operator.attrgetter('weight')
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
I64 = numpy.int64
TWO24 = 2 ** 24
TWO30 = 2 ** 30
TWO32 = 2 ** 32
GZIP = 'gzip'
BUFFER = 1.5  # enlarge the pointsource_distance sphere to fix the weight;
# with BUFFER = 1 we would have lots of apparently light sources
# collected together in an extra-slow task, as it happens in SHARE
# with ps_grid_spacing=50


def _store(rates, num_chunks, h5, mon=None, gzip=GZIP):
    if len(rates) == 0:
        return
    newh5 = h5 is None
    if newh5:
        scratch = parallel.scratch_dir(mon.calc_id)
        h5 = hdf5.File(f'{scratch}/{mon.task_no}.hdf5', 'a')
    chunks = rates['sid'] % num_chunks
    idx_start_stop = []
    for chunk in numpy.unique(chunks):
        ch_rates = rates[chunks == chunk]
        try:
            h5.create_df(
                '_rates', [(n, rates_dt[n]) for n in rates_dt.names], gzip)
            hdf5.create(
                h5, '_rates/slice_by_idx', getters.slice_dt, fillvalue=None)
        except ValueError:  # already created
            offset = len(h5['_rates/sid'])
        else:
            offset = 0
        idx_start_stop.append((chunk, offset, offset + len(ch_rates)))
        hdf5.extend(h5['_rates/sid'], ch_rates['sid'])
        hdf5.extend(h5['_rates/gid'], ch_rates['gid'])
        hdf5.extend(h5['_rates/lid'], ch_rates['lid'])
        hdf5.extend(h5['_rates/rate'], ch_rates['rate'])
    iss = numpy.array(idx_start_stop, getters.slice_dt)
    hdf5.extend(h5['_rates/slice_by_idx'], iss)
    if newh5:
        fname = h5.filename
        h5.flush()
        h5.close()
        return fname


class Set(set):
    __iadd__ = set.__ior__


def get_heavy_gids(source_groups, cmakers):
    """
    :returns: the g-indices associated to the heavy groups
    """
    if source_groups.attrs['tiling']:
        return []
    elif cmakers[0].oq.disagg_by_src:
        grp_ids = source_groups['grp_id']  # all groups
    else:
        grp_ids = source_groups['grp_id'][source_groups['blocks'] > 1]
    gids = []
    for grp_id in grp_ids:
        gids.extend(cmakers[grp_id].gid)
    return gids


def store_ctxs(dstore, rupdata_list, grp_id):
    """
    Store contexts in the datastore
    """
    for rupdata in rupdata_list:
        nr = len(rupdata)
        known = set(rupdata.dtype.names)
        for par in dstore['rup']:
            if par == 'rup_id':
                rup_id = I64(rupdata['src_id']) * TWO30 + rupdata['rup_id']
                hdf5.extend(dstore['rup/rup_id'], rup_id)
            elif par == 'grp_id':
                hdf5.extend(dstore['rup/grp_id'], numpy.full(nr, grp_id))
            elif par == 'probs_occur':
                dstore.hdf5.save_vlen('rup/probs_occur', rupdata[par])
            elif par in known:
                hdf5.extend(dstore['rup/' + par], rupdata[par])
            else:
                hdf5.extend(dstore['rup/' + par], numpy.full(nr, numpy.nan))


#  ########################### task functions ############################ #
    
def save_rates(g, N, jid, num_chunks, mon):
    """
    Store the rates for the given g on a file scratch/calc_id/task_no.hdf5
    """
    with mon.shared['rates'] as rates:
        rates_g = rates[:, :, jid[g]]
        sids = numpy.arange(N)
        for chunk in range(num_chunks):
            ch = sids % num_chunks == chunk
            rmap = MapArray(sids[ch], rates.shape[1], 1)
            rmap.array = rates_g[ch, :, None]
            rats = rmap.to_array([g])
            _store(rats, num_chunks, None, mon)


def classical(sources, tilegetters, cmaker, dstore, monitor):
    """
    Call the classical calculator in hazardlib
    """
    # NB: removing the yield would cause terrible slow tasks
    cmaker.init_monitoring(monitor)
    with dstore:
        if sources is None:  # read the full group from the datastore
            arr = dstore.getitem('_csm')[cmaker.grp_id]
            sources = pickle.loads(zlib.decompress(arr.tobytes()))
        sitecol = dstore['sitecol'].complete  # super-fast

    if cmaker.disagg_by_src and not cmaker.atomic:
        # in case_27 (Japan) we do NOT enter here;
        # disagg_by_src still works since the atomic group contains a single
        # source 'case' (mutex combination of case:01, case:02)
        for srcs in groupby(sources, valid.basename).values():
            result = hazclassical(srcs, sitecol, cmaker)
            result['rmap'].gid = cmaker.gid
            yield result
        return

    for tileno, tileget in enumerate(tilegetters):
        result = hazclassical(sources, tileget(sitecol), cmaker)
        if tileno:
            # source_data has keys src_id, grp_id, nsites, esites, nrupts,
            # weight, ctimes, taskno
            for key, lst in result['source_data'].items():
                if key in ('weight', 'nrupts'):
                    # avoid bogus weights in `oq show task:classical`
                    lst[:] = [0. for _ in range(len(lst))]
        if cmaker.disagg_by_src:
            # do not remove zeros, otherwise AELO for JPN will break
            # since there are 4 sites out of 18 with zeros
            rmap = result.pop('rmap')
        else:
            rmap = result.pop('rmap').remove_zeros()
        # print(f"{monitor.task_no=} {rmap=}")

        if rmap.size_mb and cmaker.blocks == 1 and not cmaker.disagg_by_src:
            if config.directory.custom_tmp:
                rates = rmap.to_array(cmaker.gid)
                _store(rates, cmaker.num_chunks, None, monitor)
            else:
                result['rmap'] = rmap.to_array(cmaker.gid)
        elif rmap.size_mb:
            result['rmap'] = rmap
            result['rmap'].gid = cmaker.gid
        yield result


def tiling(tilegetter, cmaker, dstore, monitor):
    """
    Tiling calculator
    """
    cmaker.init_monitoring(monitor)
    with dstore:
        arr = dstore.getitem('_csm')[cmaker.grp_id]
        sources = pickle.loads(zlib.decompress(arr.tobytes()))
        sitecol = dstore['sitecol'].complete  # super-fast
    result = hazclassical(sources, tilegetter(sitecol), cmaker)
    rmap = result.pop('rmap').remove_zeros()
    if config.directory.custom_tmp:
        rates = rmap.to_array(cmaker.gid)
        _store(rates, cmaker.num_chunks, None, monitor)
    else:
        result['rmap'] = rmap.to_array(cmaker.gid)
    return result


# for instance for New Zealand G~1000 while R[full_enum]~1_000_000
# i.e. passing the gweights reduces the data transfer by 1000 times
def fast_mean(pgetter, monitor):
    """
    :param pgetter: a :class:`openquake.commonlib.getters.MapGetter`
    :param gweights: an array of G weights
    :returns: a dictionary kind -> MapArray
    """
    with monitor('reading rates', measuremem=True):
        pgetter.init()
    if not pgetter.sids:  # can happen with tiling
        return {}

    with monitor('compute stats', measuremem=True):
        hcurves = pgetter.get_fast_mean(pgetter.weights)

    pmap_by_kind = {'hcurves-stats': [hcurves]}
    if pgetter.poes:
        with monitor('make_hmaps', measuremem=False):
            pmap_by_kind['hmaps-stats'] = calc.make_hmaps(
                pmap_by_kind['hcurves-stats'], pgetter.imtls, pgetter.poes)
    return pmap_by_kind


def postclassical(pgetter, wget, hstats, individual_rlzs,
                  max_sites_disagg, amplifier, monitor):
    """
    :param pgetter: a :class:`openquake.commonlib.getters.MapGetter`
    :param wget: function (weights[:, :], imt) -> weights[:]
    :param hstats: a list of pairs (statname, statfunc)
    :param individual_rlzs: if True, also build the individual curves
    :param max_sites_disagg: if there are less sites than this, store rup info
    :param amplifier: instance of Amplifier or None
    :param monitor: instance of Monitor
    :returns: a dictionary kind -> MapArray

    The "kind" is a string of the form 'rlz-XXX' or 'mean' of 'quantile-XXX'
    used to specify the kind of output.
    """
    with monitor('reading rates', measuremem=True):
        pgetter.init()
    if not pgetter.sids:  # can happen with tiling
        return {}

    if amplifier:
        # amplification is meant for few sites, i.e. no tiling
        with hdf5.File(pgetter.filenames[0], 'r') as f:
            ampcode = f['sitecol'].ampcode
        imtls = DictArray({imt: amplifier.amplevels
                           for imt in pgetter.imtls})
    else:
        imtls = pgetter.imtls
    poes, sids = pgetter.poes, U32(pgetter.sids)
    M = len(imtls)
    L = imtls.size
    L1 = L // M
    R = pgetter.R
    S = len(hstats)
    pmap_by_kind = {}
    if R == 1 or individual_rlzs:
        pmap_by_kind['hcurves-rlzs'] = [
            MapArray(sids, M, L1).fill(0) for r in range(R)]
    if hstats:
        pmap_by_kind['hcurves-stats'] = [
            MapArray(sids, M, L1).fill(0) for r in range(S)]
    combine_mon = monitor('combine pmaps', measuremem=False)
    compute_mon = monitor('compute stats', measuremem=False)
    hmaps_mon = monitor('make_hmaps', measuremem=False)
    sidx = MapArray(sids, 1, 1).fill(0).sidx
    for sid in sids:
        idx = sidx[sid]
        with combine_mon:
            pc = pgetter.get_hcurve(sid)  # shape (L, R)
            if amplifier:
                pc = amplifier.amplify(ampcode[sid], pc)
                # NB: the hcurve have soil levels != IMT levels
        if pc.sum() == 0:  # no data
            continue
        with compute_mon:
            if R == 1 or individual_rlzs:
                for r in range(R):
                    pmap_by_kind['hcurves-rlzs'][r].array[idx] = (
                        pc[:, r].reshape(M, L1))
            if hstats:
                for s, (statname, stat) in enumerate(hstats.items()):
                    sc = getters.build_stat_curve(
                        pc, imtls, stat, pgetter.weights, wget,
                        pgetter.use_rates)
                    arr = sc.reshape(M, L1)
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
    Helper class for storing the rates
    """
    def __init__(self, dstore, srcidx, gids):
        self.datastore = dstore
        oq = dstore['oqparam']
        self.itime = oq.investigation_time
        self.weig = dstore['gweights'][:]
        self.imtls = oq.imtls
        self.sids = dstore['sitecol/sids'][:]
        self.srcidx = srcidx
        self.gids = gids
        self.N = len(dstore['sitecol/sids'])
        self.M = len(oq.imtls)
        self.L = oq.imtls.size
        self.L1 = self.L // self.M
        self.acc = AccumDict(accum={})

    # used in in disagg_by_src
    def get_rates(self, pmap, grp_id):
        """
        :param pmap: a MapArray
        :returns: an array of rates of shape (N, M, L1)
        """
        gids = self.gids[grp_id]
        rates = pmap.array @ self.weig[gids] / self.itime
        return rates.reshape((self.N, self.M, self.L1))

    def store_mean_rates_by_src(self, dic):
        """
        Store data inside mean_rates_by_src with shape (N, M, L1, Ns)
        """
        mean_rates_by_src = self.datastore['mean_rates_by_src/array'][()]
        for key, rates in dic.items():
            if isinstance(key, str):
                # in case of mean_rates_by_src key is a source ID
                idx = self.srcidx[valid.corename(key)]
                mean_rates_by_src[..., idx] += rates
        self.datastore['mean_rates_by_src/array'][:] = mean_rates_by_src
        return mean_rates_by_src


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

        grp_id = dic.pop('grp_id')
        sdata = dic.pop('source_data', None)
        if sdata is not None:
            self.source_data += sdata
            self.rel_ruptures[grp_id] += sum(sdata['nrupts'])
        self.cfactor += dic.pop('cfactor')

        # store rup_data if there are few sites
        if self.few_sites and len(dic['rup_data']):
            with self.monitor('saving rup_data'):
                store_ctxs(self.datastore, dic['rup_data'], grp_id)

        rmap = dic.pop('rmap', None)
        source_id = dic.pop('basename', '')  # non-empty for disagg_by_src
        if source_id:
            # accumulate the rates for the given source
            acc[source_id] += self.haz.get_rates(rmap, grp_id)
        if rmap is None:
            # already stored in the workers, case_22
            pass
        elif isinstance(rmap, numpy.ndarray):
            # store the rates directly, case_03 or tiling without custom_tmp
            with self.monitor('storing rates', measuremem=True):
                _store(rmap, self.num_chunks, self.datastore)
        else:
            # aggregating rates is ultra-fast compared to storing
            self.rmap += rmap
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
                elif param == 'src_id':
                    dt = U32
                elif param == 'rup_id':
                    dt = I64
                elif param == 'grp_id':
                    dt = U16
                else:
                    dt = F32
                descr.append((param, dt))
            self.datastore.create_df('rup', descr, 'gzip')
        # NB: the relevant ruptures are less than the effective ruptures,
        # which are a preclassical concept

    def init_poes(self):
        oq = self.oqparam
        self.cmakers = read_cmakers(self.datastore, self.csm)
        parent = self.datastore.parent
        if parent:
            # tested in case_43
            self.req_gb, self.max_weight, self.trt_rlzs, self.gids = (
                preclassical.store_tiles(
                    self.datastore, self.csm, self.sitecol, self.cmakers))

        self.cfactor = numpy.zeros(2)
        self.rel_ruptures = AccumDict(accum=0)  # grp_id -> rel_ruptures
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

        # create empty dataframes
        self.num_chunks = getters.get_num_chunks(self.datastore)
        # create empty dataframes
        self.datastore.create_df(
            '_rates', [(n, rates_dt[n]) for n in rates_dt.names])
        self.datastore.create_dset('_rates/slice_by_idx', getters.slice_dt)

    def check_memory(self, N, L, maxw):
        """
        Log the memory required to receive the largest MapArray,
        assuming all sites are affected (upper limit)
        """
        num_gs = [len(cm.gsims) for cm in self.cmakers]
        size = max(num_gs) * N * L * 4
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
            oq.mags_by_trt = {
                trt: python3compat.decode(dset[:])
                for trt, dset in parent['source_mags'].items()}
            if '_rates' in parent:
                self.build_curves_maps()  # repeat post-processing
                return {}

        self.init_poes()
        if oq.fastmean:
            logging.info('Will use the fast_mean algorithm')
        if not hasattr(self, 'trt_rlzs'):
            self.max_gb, self.trt_rlzs, self.gids = getters.get_pmaps_gb(
                self.datastore, self.full_lt)
        srcidx = {name: i for i, name in enumerate(self.csm.get_basenames())}
        self.haz = Hazard(self.datastore, srcidx, self.gids)
        rlzs = self.R == 1 or oq.individual_rlzs
        if not rlzs and not oq.hazard_stats():
            raise InvalidFile('%(job_ini)s: you disabled all statistics',
                              oq.inputs)
        self.source_data = AccumDict(accum=[])
        sgs, ds = self._pre_execute()
        if self.tiling:
            self._execute_tiling(sgs, ds)
        else:
            self._execute_regular(sgs, ds)
        if self.cfactor[0] == 0:
            if self.N == 1:
                logging.error('The site is far from all seismic sources'
                              ' included in the hazard model')
            else:
                raise RuntimeError('The sites are far from all seismic sources'
                                   ' included in the hazard model')
        else:
            logging.info('cfactor = {:_d}'.format(int(self.cfactor[0])))
        self.store_info()
        self.build_curves_maps()
        return True

    def _pre_execute(self):
        oq = self.oqparam
        sgs = self.datastore['source_groups']
        self.tiling = sgs.attrs['tiling']
        if 'sitecol' in self.datastore.parent:
            ds = self.datastore.parent
        else:
            ds = self.datastore
        if config.directory.custom_tmp:
            scratch = parallel.scratch_dir(self.datastore.calc_id)
            logging.info('Storing the rates in %s', scratch)
            self.datastore.hdf5.attrs['scratch_dir'] = scratch
        if self.tiling:
            assert not oq.disagg_by_src
            assert self.N > self.oqparam.max_sites_disagg, self.N
        else:  # regular calculator
            self.create_rup()  # create the rup/ datasets BEFORE swmr_on()
        return sgs, ds

    def _execute_regular(self, sgs, ds):
        allargs = []
        n_out = []
        splits = []
        for cmaker, tilegetters, blocks, nsplits in self.csm.split(
                self.cmakers, self.sitecol, self.max_weight, self.num_chunks):
            for block in blocks:
                for tgetters in block_splitter(tilegetters, nsplits):
                    allargs.append((block, tgetters, cmaker, ds))
                    n_out.append(len(tgetters))
            splits.append(nsplits)
        logging.warning('This is a regular calculation with %d outputs, '
                        '%d tasks, min_tiles=%d, max_tiles=%d',
                        sum(n_out), len(allargs), min(n_out), max(n_out))

        # log info about the heavy sources
        srcs = self.csm.get_sources()
        maxsrc = max(srcs, key=lambda s: s.weight / splits[s.grp_id])
        logging.info('Heaviest: %s', maxsrc)

        L = self.oqparam.imtls.size
        gids = get_heavy_gids(sgs, self.cmakers)
        self.rmap = RateMap(self.sitecol.sids, L, gids)

        self.datastore.swmr_on()  # must come before the Starmap
        smap = parallel.Starmap(classical, allargs, h5=self.datastore.hdf5)
        if not self.oqparam.disagg_by_src:
            smap.expected_outputs = sum(n_out)
        acc = smap.reduce(self.agg_dicts, AccumDict(accum=0.))
        self._post_regular(acc)

    def _execute_tiling(self, sgs, ds):
        allargs = []
        n_out = []
        for cmaker, tilegetters, blocks, splits in self.csm.split(
                self.cmakers, self.sitecol, self.max_weight, self.num_chunks, True):
            for block in blocks:
                for tgetter in tilegetters:
                    allargs.append((tgetter, cmaker, ds))
                n_out.append(len(tilegetters))
        logging.warning('This is a tiling calculation with '
                        '%d tasks, min_tiles=%d, max_tiles=%d',
                        len(allargs), min(n_out), max(n_out))

        t0 = time.time()
        self.datastore.swmr_on()  # must come before the Starmap
        smap = parallel.Starmap(tiling, allargs, h5=self.datastore.hdf5)
        smap.reduce(self.agg_dicts, AccumDict(accum=0.))

        fraction = os.environ.get('OQ_SAMPLE_SOURCES')
        if fraction:
            est_time = time.time() - t0 / float(fraction)
            logging.info('Estimated time for the classical part: %.1f hours '
                         '(upper limit)', est_time / 3600)

    def _post_regular(self, acc):
        # save the rates and performs some checks
        oq = self.oqparam
        if self.rmap.size_mb:
            logging.info('Processing %s', self.rmap)

        def genargs():
            for g, j in self.rmap.jid.items():
                yield g, self.N, self.rmap.jid, self.num_chunks

        if (self.rmap.size_mb > 200 and config.directory.custom_tmp and
            parallel.oq_distribute() != 'no'):
            # tested in the oq-risk-tests
            self.datastore.swmr_on()  # must come before the Starmap
            savemap = parallel.Starmap(save_rates, genargs(),
                                       h5=self.datastore,
                                       distribute='processpool')
            savemap.share(rates=self.rmap.array)
            savemap.reduce()
        elif self.rmap.size_mb:
            for g, N, jid, num_chunks in genargs():
                rates = self.rmap.to_array(g)
                _store(rates, self.num_chunks, self.datastore)
        del self.rmap
        if oq.disagg_by_src:
            mrs = self.haz.store_mean_rates_by_src(acc)
            if oq.use_rates and self.N == 1:  # sanity check
                self.check_mean_rates(mrs)

    # NB: the largest mean_rates_by_src is SUPER-SENSITIVE to numerics!
    # in particular disaggregation/case_15 is sensitive to num_cores
    # with very different values between 2 and 16 cores(!)
    def check_mean_rates(self, mean_rates_by_src):
        """
        The sum of the mean_rates_by_src must correspond to the mean_rates
        """
        try:
            exp = disagg.to_rates(self.datastore['hcurves-stats'][0, 0])
        except KeyError:  # if there are no ruptures close to the site
            return
        got = mean_rates_by_src[0].sum(axis=2)  # sum over the sources
        for m in range(len(got)):
            # skipping large rates which can be wrong due to numerics
            # (it happens in logictree/case_05 and in Japan)
            ok = got[m] < 2.
            numpy.testing.assert_allclose(got[m, ok], exp[m, ok], atol=1E-5)

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
        :param pmap_by_kind: a dictionary of MapArrays
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
            dur = views.discard_small(task_info.loc[b'classical'].duration)
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
        R = len(self.datastore['weights'])
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
        N, S, M, P, L1, individual = self._create_hcurves_maps()
        if '_rates' in set(self.datastore) or not self.datastore.parent:
            dstore = self.datastore
        else:
            dstore = self.datastore.parent
        wget = self.full_lt.wget
        allargs = [(getter, wget, hstats, individual, oq.max_sites_disagg,
                    self.amplifier) for getter in getters.map_getters(
                        dstore, self.full_lt)]
        if not config.directory.custom_tmp and not allargs:  # case_60
            logging.warning('No rates were generated')
            return
        self.hazard = {}  # kind -> array
        hcbytes = 8 * N * S * M * L1
        hmbytes = 8 * N * S * M * P if oq.poes else 0
        if hcbytes:
            logging.info('Producing %s of hazard curves', humansize(hcbytes))
        if hmbytes:
            logging.info('Producing %s of hazard maps', humansize(hmbytes))
        if 'delta_rates' in oq.inputs:
            pass  # avoid an HDF5 error
        else:  # in all the other cases
            self.datastore.swmr_on()
        if oq.fastmean:
            parallel.Starmap(
                fast_mean, [args[0:1] for args in allargs],
                distribute='no' if self.few_sites else None,
                h5=self.datastore.hdf5,
            ).reduce(self.collect_hazard)
        else:
            parallel.Starmap(
                postclassical, allargs,
                distribute='no' if self.few_sites else None,
                h5=self.datastore.hdf5,
            ).reduce(self.collect_hazard)
        for kind in sorted(self.hazard):
            logging.info('Saving %s', kind)  # very fast
            self.datastore[kind][:] = self.hazard.pop(kind)

        if 'hmaps-stats' in self.datastore and not oq.tile_spec:
            self.plot_hmaps()

            # check numerical stability of the hmaps around the poes
            if self.N <= oq.max_sites_disagg and not self.amplifier:
                mean_hcurves = self.datastore.sel('hcurves-stats', stat='mean')[:, 0]
                check_hmaps(mean_hcurves, oq.imtls, oq.poes)

    def plot_hmaps(self):
        """
        Generate hazard map plots if there are more than 1000 sites
        """
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
        inv_time = self.oqparam.investigation_time
        allargs = []
        for m, imt in enumerate(self.oqparam.imtls):
            for p, poe in enumerate(self.oqparam.poes):
                dic = dict(m=m, p=p, imt=imt, poe=poe, inv_time=inv_time,
                           calc_id=self.datastore.calc_id,
                           array=hmaps[:, 0, m, p])
                allargs.append((dic, self.sitecol.lons, self.sitecol.lats))
        smap = parallel.Starmap(make_hmap_png, allargs, h5=self.datastore)
        for dic in smap:
            self.datastore['png/hmap_%(m)d_%(p)d' % dic] = dic['img']
