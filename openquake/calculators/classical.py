# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
import logging
import operator
import numpy
import pandas
from PIL import Image
from openquake.baselib import parallel, hdf5, config, python3compat
from openquake.baselib.general import (
    AccumDict, DictArray, groupby, humansize)
from openquake.hazardlib import valid, InvalidFile
from openquake.hazardlib.source_group import (
    read_csm, read_src_group, get_allargs)
from openquake.hazardlib.contexts import get_cmakers, read_full_lt_by_label
from openquake.hazardlib.calc import hazard_curve
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.map_array import (
    RateMap, MapArray, rates_dt, check_hmaps, gen_chunks)
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
    # NB: this is faster if num_chunks is not too large
    logging.debug(f'Storing {humansize(rates.nbytes)}')
    newh5 = h5 is None
    if newh5:
        scratch = parallel.scratch_dir(mon.calc_id)
        h5 = hdf5.File(f'{scratch}/{mon.task_no}.hdf5', 'a')
    data = AccumDict(accum=[])
    try:
        h5.create_df(
            '_rates', [(n, rates_dt[n]) for n in rates_dt.names], gzip)
        hdf5.create(h5, '_rates/slice_by_idx', getters.slice_dt)
    except ValueError:  # already created
        offset = len(h5['_rates/sid'])
    else:
        offset = 0
    idx_start_stop = []
    if isinstance(mon, U32):  # chunk number
        pairs = [(mon, slice(None))]  # single chunk
    else:
        pairs = gen_chunks(rates['sid'], num_chunks)
    for chunk, mask in pairs:
        ch_rates = rates[mask]
        n = len(ch_rates)
        data['sid'].append(ch_rates['sid'])
        data['gid'].append(ch_rates['gid'])
        data['lid'].append(ch_rates['lid'])
        data['rate'].append(ch_rates['rate'])
        idx_start_stop.append((chunk, offset, offset + n))
        offset += n
    iss = numpy.array(idx_start_stop, getters.slice_dt)
    for key in data:
        dt = data[key][0].dtype
        data[key] = numpy.concatenate(data[key], dtype=dt)
    hdf5.extend(h5['_rates/sid'], data['sid'])
    hdf5.extend(h5['_rates/gid'], data['gid'])
    hdf5.extend(h5['_rates/lid'], data['lid'])
    hdf5.extend(h5['_rates/rate'], data['rate'])
    hdf5.extend(h5['_rates/slice_by_idx'], iss)
    if newh5:
        fname = h5.filename
        h5.flush()
        h5.close()
        return fname


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
        for chunk, mask in gen_chunks(sids, num_chunks):
            rmap = MapArray(sids[mask], rates.shape[1], 1)
            rmap.array = rates_g[mask, :, None]
            rats = rmap.to_array([g])
            _store(rats, num_chunks, None, mon)


def read_groups_sitecol(dstore, grp_keys):
    """
    :returns: source groups associated to the keys and site collection
    """
    with dstore:
        grp = [read_src_group(dstore, grp_id) for grp_id in grp_keys]
        sitecol = dstore['sitecol'].complete  # super-fast
    return grp, sitecol


def baseclassical(grp, tgetter, cmaker, remove_zeros, dstore=None, monitor=None):
    """
    Wrapper over hazard_curve.classical
    """
    if monitor:
        cmaker.init_monitoring(monitor)
    if dstore:
        with dstore:
            sites = tgetter(dstore['sitecol'], cmaker.ilabel)
    else:
        sites = tgetter
    result = hazard_curve.classical(grp, sites, cmaker)
    if remove_zeros:
        result['rmap'] = result['rmap'].remove_zeros()
    result['rmap'].gid = cmaker.gid
    result['rmap'].wei = cmaker.wei
    return result


# NB: the tilegetter here is trivial unless there are ilabels
def classical_disagg(grp_keys, tilegetter, cmaker, dstore, monitor):
    """
    Call the classical calculator in hazardlib with few sites.
    `grp_keys` contains always a single element except in the case
    of multiple atomic groups.
    """
    cmaker.init_monitoring(monitor)
    grps, sitecol = read_groups_sitecol(dstore, grp_keys)
    sites = tilegetter(sitecol, cmaker.ilabel)
    if grps[0].atomic:
        # case_27 (Japan)
        # disagg_by_src works since the atomic group contains a single
        # source 'case' (mutex combination of case:01, case:02)
        result = baseclassical(grps, sites, cmaker, remove_zeros=False)
        # do not remove zeros, otherwise AELO for JPN will break
        yield result
    else:
        # yield a result for each base source
        for grp in grps:
            for srcs in groupby(grp, valid.basename).values():
                result = baseclassical(srcs, sites, cmaker, remove_zeros=False)
                yield result


def _split_src(sources, n):
    sources.sort(key=get_weight)
    for srcs in numpy.array_split(sources, n):
        if len(srcs):
            yield list(srcs)


def _split_blk(blocks, n):
    for i in range(n):
        out = sum(blocks[i::n], [])
        if out:
            yield out


def classical(grp_keys, tilegetter, cmaker, dstore, monitor):
    """
    Call the classical calculator in hazardlib with many sites.
    `grp_keys` contains always a single element except in the case
    of multiple atomic groups.
    """
    cmaker.init_monitoring(monitor)
    # grp_keys is multiple only for JPN and New Madrid groups
    grps, sitecol = read_groups_sitecol(dstore, grp_keys)
    fulltask = all('-' not in grp_key for grp_key in grp_keys)
    sites = tilegetter(sitecol, cmaker.ilabel)
    if fulltask:
        # return raw array that will be stored immediately
        result = baseclassical(grps, sites, cmaker, remove_zeros=True)
        result['rmap'] = result['rmap'].to_array(cmaker.gid)
        yield result
    elif len(grps) == 1 and len(grps[0]) >= 3:
        # tested in case_66
        b0, *blks = _split_src(list(grps[0]), 8)
        t0 = time.time()
        res = baseclassical(b0, sites, cmaker, True)
        dt = time.time() - t0
        yield res
        if dt > cmaker.oq.time_per_task:
            for srcs in _split_blk(blks, 7):
                yield baseclassical, srcs, tilegetter, cmaker, True, dstore
        else:
            odd, even = _split_blk(blks, 2)
            yield baseclassical, odd, tilegetter, cmaker, True, dstore
            yield baseclassical(even, sites, cmaker, True)
    else:
        yield baseclassical(grps, sites, cmaker, True)

# for instance for New Zealand G~1000 while R[full_enum]~1_000_000
# i.e. passing the gweights reduces the data transfer by 1000 times
# NB: fast_mean is used only if there are no site_labels
def fast_mean(pgetter, monitor):
    """
    :param pgetter: a :class:`openquake.commonlib.getters.MapGetter`
    :param gweights: an array of Gt weights
    :returns: a dictionary kind -> MapArray
    """
    with monitor('reading rates', measuremem=True):
        pgetter.init()

    with monitor('compute stats', measuremem=True):
        hcurves = pgetter.get_fast_mean()

    pmap_by_kind = {'hcurves-stats': [hcurves]}
    if pgetter.poes:
        with monitor('make_hmaps', measuremem=False):
            pmap_by_kind['hmaps-stats'] = calc.make_hmaps(
                pmap_by_kind['hcurves-stats'], pgetter.imtls, pgetter.poes)
    return pmap_by_kind


def postclassical(pgetter, hstats, individual_rlzs, amplifier, monitor):
    """
    :param pgetter: a :class:`openquake.commonlib.getters.MapGetter`
    :param hstats: a list of pairs (statname, statfunc)
    :param individual_rlzs: if True, also build the individual curves
    :param amplifier: instance of Amplifier or None
    :param monitor: instance of Monitor
    :returns: a dictionary kind -> MapArray

    The "kind" is a string of the form 'rlz-XXX' or 'mean' of 'quantile-XXX'
    used to specify the kind of output.
    """
    with monitor('reading rates', measuremem=True):
        pgetter.init()

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
                if len(pgetter.ilabels):
                    wget = pgetter.wgets[pgetter.ilabels[sid]]
                else:
                    wget = pgetter.wgets[0]
                for s, (statname, stat) in enumerate(hstats.items()):
                    sc = getters.build_stat_curve(
                        pc, imtls, stat, wget, pgetter.use_rates)
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


# used in in disagg_by_src
def get_rates(rmap, M, itime):
    """
    :param rmap: a MapArray
    :returns: an array of rates of shape (N, M, L1)
    """
    rates = rmap.array @ rmap.wei / itime
    return rates.reshape((len(rates), M, -1))


def store_mean_rates_by_src(dstore, srcidx, dic):
    """
    Store data inside mean_rates_by_src with shape (N, M, L1, Ns)
    """
    mean_rates_by_src = dstore['mean_rates_by_src/array'][()]
    for key, rates in dic.items():
        if isinstance(key, str):
            # in case of mean_rates_by_src key is a source ID
            idx = srcidx[valid.corename(key)]
            mean_rates_by_src[..., idx] += rates
    dstore['mean_rates_by_src/array'][:] = mean_rates_by_src
    return mean_rates_by_src


@base.calculators.add('classical')
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
        :param dic: dict with keys rmap, source_data, rup_data
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
        self.dparam_mb = max(dic.pop('dparam_mb'), self.dparam_mb)
        self.source_mb = max(dic.pop('source_mb'), self.source_mb)

        # store rup_data if there are few sites
        if self.few_sites and len(dic['rup_data']):
            with self.monitor('saving rup_data'):
                store_ctxs(self.datastore, dic['rup_data'], grp_id)

        rmap = dic.pop('rmap', None)
        source_id = dic.pop('basename', '')  # non-empty for disagg_by_src
        if source_id:
            # accumulate the rates for the given source
            oq = self.oqparam
            M = len(oq.imtls)
            acc[source_id] += get_rates(rmap, M, oq.investigation_time)
        if rmap is None:
            # already stored in the workers, case_22
            pass
        elif isinstance(rmap, numpy.ndarray):
            # store the rates
            with self.monitor('storing rates', measuremem=True):
                chunkno = dic.get('chunkno')  # None with the current impl.
                _store(rmap, self.num_chunks, self.datastore, chunkno)
        else:
            # aggregating rates is ultra-fast compared to storing
            self.rmap[grp_id] += rmap
        return acc

    def create_rup(self):
        """
        Create the rup datasets *before* starting the calculation
        """
        params = {'grp_id', 'occurrence_rate', 'clon', 'clat', 'rrup',
                  'probs_occur', 'sids', 'src_id', 'rup_id', 'weight'}
        for label, cmakers in self.cmdict.items():
            for cm in cmakers:
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
        full_lt_by_label = read_full_lt_by_label(self.datastore, self.full_lt)
        trt_smrs = self.datastore['trt_smrs'][:]
        self.cmdict = {label: get_cmakers(trt_smrs, full_lt, oq)
                       for label, full_lt in full_lt_by_label.items()}
        if 'delta_rates' in self.datastore:  # aftershock
            drgetter = getters.DeltaRatesGetter(self.datastore)
            for cmakers in self.cmdict.values():
                for cmaker in cmakers:
                    cmaker.deltagetter = drgetter

        parent = self.datastore.parent
        if parent:
            # tested in case_43
            self.req_gb, self.max_weight = preclassical.store_tiles(
                self.datastore, self.csm, self.sitecol,
                self.cmdict['Default'])

        self.cfactor = numpy.zeros(2)
        self.dparam_mb = 0
        self.source_mb = 0
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

        self.num_chunks = getters.get_num_chunks(self.datastore)
        logging.info('Using num_chunks=%d', self.num_chunks)

        # create empty dataframes
        self.datastore.create_df(
            '_rates', [(n, rates_dt[n]) for n in rates_dt.names], GZIP)
        self.datastore.create_dset('_rates/slice_by_idx', getters.slice_dt)

    def check_memory(self, N, L, maxw):
        """
        Log the memory required to receive the largest MapArray,
        assuming all sites are affected (upper limit)
        """
        num_gs = [len(cm.gsims) for cm in self.cmdict['Default']]
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
            self.csm = read_csm(parent, self.full_lt)
            self.datastore['source_info'] = parent['source_info'][:]
            oq.mags_by_trt = {
                trt: python3compat.decode(dset[:])
                for trt, dset in parent['source_mags'].items()}
            if 'source_data' in parent:
                # execute finished correctly, repeat post-processing only
                self.build_curves_maps()
                return {}

        self.init_poes()
        if oq.fastmean:
            logging.info('Will use the fast_mean algorithm')
        if not hasattr(self, 'trt_rlzs'):
            self.max_gb, self.trt_rlzs, trt_smrs = getters.get_rmap_gb(
                self.datastore, self.full_lt)
        self.srcidx = {
            name: i for i, name in enumerate(self.csm.get_basenames())}
        rlzs = self.R == 1 or oq.individual_rlzs
        if not rlzs and not oq.hazard_stats():
            raise InvalidFile('%(job_ini)s: you disabled all statistics',
                              oq.inputs)
        self.source_data = AccumDict(accum=[])
        sgs, ds = self._pre_execute()
        self._execute(sgs, ds)
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
        if self.dparam_mb:
            logging.info('maximum size of the dparam cache=%.1f MB',
                         self.dparam_mb)
            logging.info('maximum size of the multifaults=%.1f MB',
                         self.source_mb)
        self.build_curves_maps()
        return True

    def _pre_execute(self):
        oq = self.oqparam
        if 'ilabel' in self.sitecol.array.dtype.names and not oq.site_labels:
            logging.warning('The site model has a field `ilabel` but it will '
                            'be ignored since site_labels is missing in %s',
                            oq.inputs['job_ini'])
        if oq.disagg_by_src and oq.site_labels:
            assert len(numpy.unique(self.sitecol.ilabel)) == 1, \
                'disagg_by_src not supported on splittable site collection'
        sgs = self.datastore['source_groups']
        self.tiling = sgs.attrs['tiling']
        if 'sitecol' in self.datastore.parent:
            ds = self.datastore.parent
        else:
            ds = self.datastore
        if self.tiling:
            assert not oq.disagg_by_src
            assert self.N > self.oqparam.max_sites_disagg, self.N
        else:  # regular calculator
            self.create_rup()  # create the rup/ datasets BEFORE swmr_on()
        return sgs, ds

    def _execute(self, sgs, ds):
        oq = self.oqparam
        allargs = []
        L = self.oqparam.imtls.size
        self.rmap = {}
        # in the case of many sites produce half the tasks
        data = get_allargs(self.csm, self.cmdict, self.sitecol,
                           self.max_weight, self.num_chunks, tiling=self.tiling)
        maxtiles = 1
        for cmaker, tilegetters, grp_keys, atomic in data:
            cmaker.tiling = self.tiling
            if self.few_sites or oq.disagg_by_src or len(grp_keys) > 1:
                grp_id = int(grp_keys[0].split('-')[0])
                self.rmap[grp_id] = RateMap(self.sitecol.sids, L, cmaker.gid)
            if self.few_sites or oq.disagg_by_src and cmaker.ilabel is None:
                assert len(tilegetters) == 1, "disagg_by_src has no tiles"
            for tgetter in tilegetters:
                if atomic:
                    # JPN, send the grp_keys together, they will all send
                    # rates to the RateMap associated to the first grp_id
                    allargs.append((grp_keys, tgetter, cmaker, ds))
                else:
                    # send a grp_key at the time
                    for grp_key in grp_keys:
                        allargs.append(([grp_key], tgetter, cmaker, ds))
            maxtiles = max(maxtiles, len(tilegetters))
        kind = 'tiling' if oq.tiling else 'regular'
        logging.warning('This is a %s calculation with '
                        '%d tasks, maxtiles=%d', kind,
                        len(allargs), maxtiles)

        # save grp_keys by task
        keys = numpy.array([' '.join(args[0]).encode('ascii')
                            for args in allargs])
        self.datastore.create_dset('grp_keys', keys)

        # log info about the heavy sources
        srcs = [src for src in self.csm.get_sources() if src.weight]
        maxsrc = max(srcs, key=lambda s: s.weight)
        logging.info('Heaviest: %s', maxsrc)

        self.datastore.swmr_on()  # must come before the Starmap
        if self.few_sites or oq.disagg_by_src:
            smap = parallel.Starmap(
                classical_disagg, allargs, h5=self.datastore.hdf5)
        else:
            smap = parallel.Starmap(classical, allargs, h5=self.datastore.hdf5)
        acc = smap.reduce(self.agg_dicts, AccumDict(accum=0.))
        self._post_execute(acc)

    def _post_execute(self, acc):
        # save the rates and performs some checks
        oq = self.oqparam
        logging.info('Saving RateMaps')

        def genargs():
            # produce Gt arguments
            for grp_id, rmap in self.rmap.items():
                for g, j in rmap.jid.items():
                    yield grp_id, g, self.N, rmap.jid, self.num_chunks

        mon = self.monitor('storing rates', measuremem=True)
        for grp_id, g, N, jid, num_chunks in genargs():
            with mon:
                rates = self.rmap[grp_id].to_array(g)
                _store(rates, self.num_chunks, self.datastore)

        if oq.disagg_by_src:
            mrs = store_mean_rates_by_src(self.datastore, self.srcidx, acc)
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
        df['impact'] = df.nctxs / self.N
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
            slow_tasks = (len(dur[dur > 4 * dur.mean()]) and
                          dur.max() > 5 * oq.time_per_task)
            msg = 'There were %d slow task(s)' % slow_tasks
            if slow_tasks and self.SLOW_TASK_ERROR and not oq.disagg_by_src:
                raise RuntimeError('%s in #%d' % (msg, self.datastore.calc_id))
            elif slow_tasks:
                logging.info(msg)

    def _create_hcurves_maps(self):
        oq = self.oqparam
        N = len(self.sitecol)
        R = len(self.datastore['weights'])
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
        if R == 1 or oq.individual_rlzs:
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
        return N, S, M, P, L1

    # called by execute before post_execute
    def build_curves_maps(self):
        """
        Compute and store hcurves-rlzs, hcurves-stats, hmaps-rlzs, hmaps-stats
        """
        oq = self.oqparam
        hstats = oq.hazard_stats()
        N, S, M, P, L1 = self._create_hcurves_maps()
        if '_rates' in set(self.datastore) or not self.datastore.parent:
            dstore = self.datastore
        else:
            dstore = self.datastore.parent
        allargs = [(getter, hstats, oq.individual_rlzs, self.amplifier)
                   for getter in getters.map_getters(dstore, self.full_lt, oq)]
        if not allargs:  # case_60
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
                mean_hcurves = self.datastore.sel(
                    'hcurves-stats', stat='mean')[:, 0]
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
