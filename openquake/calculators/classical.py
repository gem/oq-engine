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
import zlib
import pickle
import psutil
import logging
import operator
import numpy
import pandas
from PIL import Image
from openquake.baselib import (
    performance, parallel, hdf5, config, python3compat)
from openquake.baselib.general import (
    AccumDict, DictArray, block_splitter, groupby, humansize)
from openquake.hazardlib import valid, InvalidFile
from openquake.hazardlib.contexts import read_cmakers, get_maxsize
from openquake.hazardlib.calc.hazard_curve import classical as hazclassical
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.map_array import MapArray, rates_dt
from openquake.commonlib import calc
from openquake.calculators import base, getters

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
I64 = numpy.int64
TWO24 = 2 ** 24
TWO32 = 2 ** 32
BUFFER = 1.5  # enlarge the pointsource_distance sphere to fix the weight;
# with BUFFER = 1 we would have lots of apparently light sources
# collected together in an extra-slow task, as it happens in SHARE
# with ps_grid_spacing=50
get_weight = operator.attrgetter('weight')


def _store(rates, h5):
    chunks = rates['sid'] % getters.CHUNKS
    for chunk in numpy.unique(chunks):
        ch_rates = rates[chunks == chunk]
        name = '_rates%03d' % chunk
        try:
            h5.create_df(name, [(n, rates_dt[n]) for n in rates_dt.names])
        except ValueError:  # already created
            pass
        hdf5.extend(h5[f'{name}/sid'], ch_rates['sid'])
        hdf5.extend(h5[f'{name}/gid'], ch_rates['gid'])
        hdf5.extend(h5[f'{name}/lid'], ch_rates['lid'])
        hdf5.extend(h5[f'{name}/rate'], ch_rates['rate'])


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


def to_rates(pnemap, gid, tiling, disagg_by_src):
    """
    :returns: dictionary if tiling is True, else MapArray with rates
    """
    rates = pnemap.to_rates()
    if tiling:
        return rates.to_array(gid)
    if disagg_by_src:
        return rates
    return rates.remove_zeros()


def get_tile_size(oq, N, csm, maxw=0):
    """
    :returns: the number of sites in the smallest tile
    """
    maxw = maxw or csm.get_max_weight(oq)
    sizes = [maxw / sg.weight * N for sg in csm.src_groups]
    return int(min(sizes))


#  ########################### task functions ############################ #

def classical(sources, sitecol, cmaker, dstore, monitor):
    """
    Call the classical calculator in hazardlib
    """
    # NB: removing the yield would cause terrible slow tasks
    cmaker.init_monitoring(monitor)
    tiling = not hasattr(sources, '__iter__')  # passed gid
    disagg_by_src = cmaker.disagg_by_src
    with dstore:
        if tiling:  # tiling calculator, read the sources from the datastore
            gid = sources
            with monitor('reading sources'):  # fast, but uses a lot of RAM
                arr = dstore.getitem('_csm')[cmaker.grp_id]
                sources = pickle.loads(zlib.decompress(arr.tobytes()))
        else:  # regular calculator
            gid = 0
            sitecol = dstore['sitecol']  # super-fast

    if disagg_by_src and not getattr(sources, 'atomic', False):
        # in case_27 (Japan) we do NOT enter here;
        # disagg_by_src still works since the atomic group contains a single
        # source 'case' (mutex combination of case:01, case:02)
        for srcs in groupby(sources, valid.basename).values():
            pmap = MapArray(
                sitecol.sids, cmaker.imtls.size, len(cmaker.gsims)).fill(
                cmaker.rup_indep)
            result = hazclassical(srcs, sitecol, cmaker, pmap)
            result['pnemap'] = to_rates(~pmap, gid, tiling, disagg_by_src)
            yield result
    else:
        pmap = MapArray(
            sitecol.sids, cmaker.imtls.size, len(cmaker.gsims)).fill(
                cmaker.rup_indep)
        result = hazclassical(sources, sitecol, cmaker, pmap)
        rates = to_rates(~pmap, gid, tiling, disagg_by_src)
        if monitor.config.distribution.save_on_tmp and tiling:
            # tested in case_22
            try:
                os.mkdir(monitor.calc_dir)
            except FileExistsError:  # somebody else wrote it
                pass
            fname = f'{monitor.calc_dir}/{monitor.task_no}.hdf5'
            # print('Saving rates on %s' % fname)
            with hdf5.File(fname, 'a') as h5:
                _store(rates, h5)
            yield dict(cfactor=result['cfactor'])
            return
        else:
            result['pnemap'] = rates
        yield result


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
        self.offset = 0

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
        source_id = dic.pop('basename', '')  # non-empty for disagg_by_src
        if source_id:
            # accumulate the rates for the given source
            acc[source_id] += self.haz.get_rates(pnemap, grp_id)
        G = pnemap.array.shape[2]
        rates = self.pmap.array
        sidx = self.pmap.sidx[pnemap.sids]
        for i, gid in enumerate(self.gids[grp_id]):
            rates[sidx, :, gid] += pnemap.array[:, :, i % G]
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
        Log the memory required to receive the largest MapArray,
        assuming all sites are affected (upper limit)
        """
        num_gs = [len(cm.gsims) for cm in self.cmakers]
        max_gs = max(num_gs)
        maxsize = get_maxsize(len(self.oqparam.imtls), max_gs)
        logging.info('Considering {:_d} contexts at once'.format(maxsize))
        size = max_gs * N * L * 4
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
            if any(name.startswith('_rates') for name in parent):
                self.build_curves_maps()  # repeat post-processing
                return {}
        else:
            maxw = self.max_weight
        self.init_poes()
        if oq.fastmean:
            logging.info('Will use the fast_mean algorithm')
        req_gb, self.trt_rlzs, self.gids = getters.get_pmaps_gb(
            self.datastore, self.full_lt)
        srcidx = {name: i for i, name in enumerate(self.csm.get_basenames())}
        self.haz = Hazard(self.datastore, srcidx, self.gids)
        rlzs = self.R == 1 or oq.individual_rlzs
        if not rlzs and not oq.hazard_stats():
            raise InvalidFile('%(job_ini)s: you disabled all statistics',
                              oq.inputs)
        self.source_data = AccumDict(accum=[])
        if not performance.numba:
            logging.warning('numba is not installed: using the slow algorithm')

        t0 = time.time()
        max_gb = float(config.memory.pmap_max_gb)
        if (oq.disagg_by_src or self.N < oq.max_sites_disagg or req_gb < max_gb
            or oq.tile_spec):
            self.check_memory(len(self.sitecol), oq.imtls.size, maxw)
            self.execute_reg(maxw)
        else:
            self.execute_big(maxw)
        self.store_info()
        if self.cfactor[0] == 0:
            if self.N == 1:
                logging.warning('The site is far from all seismic sources'
                                ' included in the hazard model')
            else:
                raise RuntimeError('The sites are far from all seismic sources'
                                   ' included in the hazard model')
        else:
            logging.info('cfactor = {:_d}/{:_d} = {:.1f}'.format(
                int(self.cfactor[1]), int(self.cfactor[0]),
                self.cfactor[1] / self.cfactor[0]))
        self.build_curves_maps()
        if not oq.hazard_calculation_id:
            self.classical_time = time.time() - t0
        return True

    def execute_reg(self, maxw):
        """
        Regular case
        """
        self.create_rup()  # create the rup/ datasets BEFORE swmr_on()
        acc = AccumDict(accum=0.)  # src_id -> pmap
        oq = self.oqparam
        L = oq.imtls.size
        Gt = len(self.trt_rlzs)
        self.pmap = MapArray(self.sitecol.sids, L, Gt).fill(0, F32)
        allargs = []
        if 'sitecol' in self.datastore.parent:
            ds = self.datastore.parent
        else:
            ds = self.datastore
        for cm in self.cmakers:
            cm.gsims = list(cm.gsims)  # save data transfer
            sg = self.csm.src_groups[cm.grp_id]
            cm.rup_indep = getattr(sg, 'rup_interdep', None) != 'mutex'
            cm.save_on_tmp = config.distribution.save_on_tmp
            if sg.atomic or sg.weight <= maxw:
                blks = [sg]
            else:
                blks = block_splitter(sg, maxw, get_weight, sort=True)
            for block in blks:
                logging.debug('Sending %d source(s) with weight %d',
                              len(block), sg.weight)
                allargs.append((block, None, cm, ds))

        self.datastore.swmr_on()  # must come before the Starmap
        smap = parallel.Starmap(classical, allargs, h5=self.datastore.hdf5)
        acc = smap.reduce(self.agg_dicts, acc)
        with self.monitor('storing rates', measuremem=True):
            _store(self.pmap.to_array(), self.datastore)
        del self.pmap
        if oq.disagg_by_src:
            mrs = self.haz.store_mean_rates_by_src(acc)
            if oq.use_rates and self.N == 1:  # sanity check
                self.check_mean_rates(mrs)

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
            ok = got[m] < 10.
            numpy.testing.assert_allclose(got[m, ok], exp[m, ok], atol=1E-5)

    def fix_maxw_tsize(self, maxw, tsize):
        if tsize < 100:  # less than 100 sites per tile
            logging.info(
                'concurrent_tasks=%d is too large, producing less tiles',
                self.oqparam.concurrent_tasks)
            maxw = maxw * 100/ tsize
            tsize = get_tile_size(self.oqparam, self.N, self.csm, maxw)
        return maxw, tsize

    def execute_big(self, maxw):
        """
        Use parallel tiling
        """
        oq = self.oqparam
        assert not oq.disagg_by_src
        assert self.N > self.oqparam.max_sites_disagg, self.N
        tsize = get_tile_size(oq, self.N, self.csm, maxw)
        maxw, tsize = self.fix_maxw_tsize(maxw, tsize)
        logging.info('min_tile_size = {:_d}'.format(tsize))
        allargs = []
        self.ntiles = []
        if config.distribution.save_on_tmp:
            self._monitor.config = config
            logging.info('Storing the rates in %s', self._monitor.calc_dir)
            self.datastore.hdf5.attrs['scratch_dir'] = self._monitor.calc_dir
        if '_csm' in self.datastore.parent:
            ds = self.datastore.parent
        else:
            ds = self.datastore
        sizes = []
        max_gb = float(config.memory.pmap_max_gb)
        for cm in self.cmakers:
            cm.gsims = list(cm.gsims)  # save data transfer
            sg = self.csm.src_groups[cm.grp_id]
            cm.rup_indep = getattr(sg, 'rup_interdep', None) != 'mutex'
            cm.save_on_tmp = config.distribution.save_on_tmp
            gid = self.gids[cm.grp_id][0]
            size_gb = len(cm.gsims) * oq.imtls.size * self.N * 8 / 1024**3
            ntiles = numpy.ceil(sg.weight / maxw)
            if size_gb / ntiles > max_gb:
                ntiles = numpy.ceil(size_gb / max_gb)
            tiles = self.sitecol.split(ntiles, minsize=oq.max_sites_disagg)
            logging.info('Group #%d, %d tiles', cm.grp_id, len(tiles))
            for tile in tiles:
                allargs.append((gid, tile, cm, ds))
                sizes.append(size_gb * len(tile) / self.N)
                self.ntiles.append(len(tiles))
        logging.warning('Generated at most %d tiles, maxsize=%.1f G',
                        max(self.ntiles), max(sizes))
        self.datastore.swmr_on()  # must come before the Starmap
        for dic in parallel.Starmap(classical, allargs, h5=self.datastore.hdf5):
            self.cfactor += dic['cfactor']
            if 'pnemap' in dic:
                _store(dic['pnemap'], self.datastore)
        return {}

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
        if '_rates000' in set(self.datastore) or not self.datastore.parent:
            dstore = self.datastore
        else:
            dstore = self.datastore.parent
        wget = self.full_lt.wget
        allargs = [(getter, wget, hstats, individual, oq.max_sites_disagg,
                    self.amplifier) for getter in getters.map_getters(
                        dstore, self.full_lt)]
        if not config.distribution.save_on_tmp and not allargs:  # case_60
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

        fraction = os.environ.get('OQ_SAMPLE_SOURCES')
        if fraction and hasattr(self, 'classical_time'):
            total_time = time.time() - self.t0
            delta = total_time - self.classical_time
            est_time = self.classical_time / float(fraction) + delta
            logging.info('Estimated time: %.1f hours', est_time / 3600)

        if 'hmaps-stats' in self.datastore and not oq.tile_spec:
            self.plot_hmaps()

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
        smap = parallel.Starmap(make_hmap_png, allargs, distribute='processpool')
        for dic in smap:
            self.datastore['png/hmap_%(m)d_%(p)d' % dic] = dic['img']
