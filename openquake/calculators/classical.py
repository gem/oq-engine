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
import gzip
import time
import pickle
import psutil
import logging
import operator
import functools
import h5py
import numpy
import pandas
try:
    from PIL import Image
except ImportError:
    Image = None
from openquake.baselib import performance, parallel, hdf5, config, python3compat
from openquake.baselib.general import (
    AccumDict, DictArray, block_splitter, groupby, humansize,
    get_nbytes_msg, agg_probs, pprod)
from openquake.hazardlib.contexts import ContextMaker, read_cmakers, basename
from openquake.hazardlib.calc.hazard_curve import classical as hazclassical
from openquake.hazardlib.probability_map import ProbabilityMap, poes_dt
from openquake.commonlib import calc, datastore
from openquake.calculators import base, getters, extract

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
slice_dt = numpy.dtype([('sid', U32), ('start', int), ('stop', int)])


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


def _concat(acc, slc2):
    if len(acc) == 0:
        return [slc2]
    slc1 = acc[-1]  # last slice
    if slc2[0] == slc1[1]:
        new = numpy.array([slc1[0], slc2[1]])
        return acc[:-1] + [new]
    return acc + [slc2]


def compactify(arrayN2):
    """
    :param arrayN2: an array with columns (start, stop)
    :returns: a shorter array with the same structure

    Here is how it works in an example where the first three slices
    are compactified into one while the last slice stays as it is:

    >>> arr = numpy.array([[84384702, 84385520],
    ...                    [84385520, 84385770],
    ...                    [84385770, 84386062],
    ...                    [84387636, 84388028]])
    >>> compactify(arr)
    array([[84384702, 84386062],
           [84387636, 84388028]])
    """
    if len(arrayN2) == 1:
        # nothing to compactify
        return arrayN2
    out = numpy.array(functools.reduce(_concat, arrayN2, []))
    return out


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


def semicolon_aggregate(probs, source_ids):
    """
    :param probs: array of shape (..., Ns)
    :param source_ids: list of source IDs (some with semicolons) of length Ns
    :returns: array of shape (..., Ns) and list of length N with N < Ns

    This is used to aggregate array of probabilities in the case of sources
    which are variations of a base source. Here is an example with Ns=7
    sources reducible to N=4 base sources:

    >>> source_ids = ['A;0', 'A;1', 'A;2', 'B', 'C', 'D;0', 'D;1']
    >>> probs = numpy.array([[.01, .02, .03, .04, .05, .06, .07],
    ...                      [.00, .01, .02, .03, .04, .05, .06]])

    `semicolon_aggregate` effectively reduces the array of probabilities
    from 7 to 4 components, however for storage convenience it does not
    change the shape, so the missing components are zeros:

    >>> semicolon_aggregate(probs, source_ids)  # (2, 7) => (2, 4)
    (array([[0.058906, 0.04    , 0.05    , 0.1258  , 0.      , 0.      ,
            0.      ],
           [0.0298  , 0.03    , 0.04    , 0.107   , 0.      , 0.      ,
            0.      ]]), array(['A', 'B', 'C', 'D'], dtype='<U1'))

    It is assumed that the semicolon sources are independent, i.e. not mutex.
    """
    srcids = [srcid.split(';')[0] for srcid in source_ids]
    unique, indices = numpy.unique(srcids, return_inverse=True)
    new = numpy.zeros_like(probs)
    for i, s1, s2 in performance.idx_start_stop(indices):
        new[..., i] = pprod(probs[..., s1:s2], axis=-1)
    return new, unique


def check_disagg_by_src(dstore):
    """
    Make sure that by composing disagg_by_src one gets the hazard curves
    """
    info = dstore['source_info'][:]
    mutex = info['mutex_weight'] > 0
    mean = dstore.sel('hcurves-stats', stat='mean')[:, 0]  # N, M, L
    dbs = dstore.sel('disagg_by_src')  # N, R, M, L, Ns
    if mutex.sum():
        dbs_indep = dbs[:, :, :, :, ~mutex]
        dbs_mutex = dbs[:, :, :, :, mutex]
        poes_indep = pprod(dbs_indep, axis=4)  # N, R, M, L
        poes_mutex = dbs_mutex.sum(axis=4)  # N, R, M, L
        poes = poes_indep + poes_mutex - poes_indep * poes_mutex
    else:
        poes = pprod(dbs, axis=4)  # N, R, M, L
    rlz_weights = dstore['weights'][:]
    mean2 = numpy.einsum('sr...,r->s...', poes, rlz_weights)  # N, M, L
    if not numpy.allclose(mean, mean2, atol=1E-6):
        logging.error('check_disagg_src fails: %s =! %s',
                      mean[0], mean2[0])

    # check the extract call is not broken
    aw = extract.extract(dstore, 'disagg_by_src?lvl_id=-1')
    assert aw.array.dtype.names == ('src_id', 'poe')

#  ########################### task functions ############################ #


def classical(srcs, sitecol, cmaker, monitor):
    """
    Call the classical calculator in hazardlib
    """
    cmaker.init_monitoring(monitor)
    if isinstance(srcs, datastore.DataStore):  # keep_source_groups=true
        with srcs:
            if sitecol is None:
                sitecol = srcs['sitecol']
            f = srcs.parent.hdf5 if srcs.parent else srcs.hdf5
            arr = h5py.File.__getitem__(f, '_csm')[cmaker.grp_id]
            srcs =  pickle.loads(gzip.decompress(arr.tobytes()))
    rup_indep = getattr(srcs, 'rup_interdep', None) != 'mutex'
    pmap = ProbabilityMap(
        sitecol.sids, cmaker.imtls.size, len(cmaker.gsims)).fill(rup_indep)
    result = hazclassical(srcs, sitecol, cmaker, pmap)
    result['pnemap'] = ~pmap.remove_zeros()
    result['pnemap'].start = cmaker.start
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
    poes, weights, sids = pgetter.poes, pgetter.weights, U32(pgetter.sids)
    M = len(imtls)
    L = imtls.size
    L1 = L // M
    R = len(weights)
    S = len(hstats)
    pmap_by_kind = {}
    if R > 1 and individual_rlzs or not hstats:
        pmap_by_kind['hcurves-rlzs'] = [
            ProbabilityMap(sids, M, L1).fill(0) for r in range(R)]
    if hstats:
        pmap_by_kind['hcurves-stats'] = [
            ProbabilityMap(sids, M, L1).fill(0) for r in range(S)]
    combine_mon = monitor('combine pmaps', measuremem=False)
    compute_mon = monitor('compute stats', measuremem=False)
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
            if R > 1 and individual_rlzs or not hstats:
                for r in range(R):
                    pmap_by_kind['hcurves-rlzs'][r].array[idx] = (
                        pc.array[:, r].reshape(M, L1))
            if hstats:
                for s, (statname, stat) in enumerate(hstats.items()):
                    sc = getters.build_stat_curve(pc, imtls, stat, weights)
                    arr = sc.array.reshape(M, L1)
                    pmap_by_kind['hcurves-stats'][s].array[idx] = arr

    if poes and (R > 1 and individual_rlzs or not hstats):
        pmap_by_kind['hmaps-rlzs'] = calc.make_hmaps(
            pmap_by_kind['hcurves-rlzs'], imtls, poes)
    if poes and hstats:
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
        self.full_lt = full_lt
        self.cmakers = read_cmakers(dstore, full_lt)
        self.totgsims = sum(len(cm.gsims) for cm in self.cmakers)
        self.imtls = imtls = dstore['oqparam'].imtls
        self.level_weights = imtls.array.flatten() / imtls.array.sum()
        self.sids = dstore['sitecol/sids'][:]
        self.srcidx = srcidx
        self.N = len(dstore['sitecol/sids'])
        self.R = full_lt.get_num_paths()
        self.acc = AccumDict(accum={})
        self.offset = 0

    def get_hcurves(self, pmap, rlzs_by_gsim):  # used in in disagg_by_src
        """
        :param pmap: a ProbabilityMap
        :param rlzs_by_gsim: a dictionary gsim -> rlz IDs
        :returns: an array of PoEs of shape (N, R, M, L)
        """
        res = numpy.zeros((self.N, self.R, self.imtls.size))
        for sid, arr in zip(pmap.sids, pmap.array):
            for gsim_idx, rlzis in enumerate(rlzs_by_gsim.values()):
                for rlz in rlzis:
                    res[sid, rlz] = agg_probs(res[sid, rlz], arr[:, gsim_idx])
        return res.reshape(self.N, self.R, len(self.imtls), -1)

    def store_poes(self, grp_id, pmap):
        """
        Store the pmap of the given group inside the _poes dataset
        """
        start = pmap.start
        arr = 1. - pmap.array
        # Physically, an extremely small intensity measure level can have an
        # extremely large probability of exceedence, however that probability
        # cannot be exactly 1 unless the level is exactly 0. Numerically, the
        # PoE can be 1 and this give issues when calculating the damage (there
        # is a log(0) in
        # :class:`openquake.risklib.scientific.annual_frequency_of_exceedence`).
        # Here we solve the issue by replacing the unphysical probabilities 1
        # with .9999999999999999 (the float64 closest to 1).
        arr[arr == 1.] = .9999999999999999
        # arr[arr < 1E-5] = 0.  # minimum_poe
        idxs, lids, gids = arr.nonzero()
        if len(idxs):
            sids = pmap.sids[idxs]
            hdf5.extend(self.datastore['_poes/sid'], sids)
            hdf5.extend(self.datastore['_poes/gid'], gids + start)
            hdf5.extend(self.datastore['_poes/lid'], lids)
            hdf5.extend(self.datastore['_poes/poe'], arr[idxs, lids, gids])
            sbs = build_slice_by_sid(sids, self.offset)
            hdf5.extend(self.datastore['_poes/slice_by_sid'], sbs)
            self.offset += len(sids)
        self.acc[grp_id]['grp_start'] = start
        self.acc[grp_id]['avg_poe'] = arr.mean(axis=(0, 2))@self.level_weights
        self.acc[grp_id]['nsites'] = len(pmap.sids)

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
            disagg_by_src = self.datastore['disagg_by_src'][()]
            for key, pmap in pmaps.items():
                if isinstance(key, str):
                    # in case of disagg_by_src key is a source ID
                    rlzs_by_gsim = self.cmakers[pmap.grp_id].gsims
                    disagg_by_src[..., self.srcidx[key]] = (
                        self.get_hcurves(pmap, rlzs_by_gsim))
            self.datastore['disagg_by_src'][:] = disagg_by_src

def get_pmaps_size(dstore, ct):
    """
    :returns: memory required on the master node to keep the pmaps
    """
    N = len(dstore['sitecol'])
    L = dstore['oqparam'].imtls.size
    cmakers = read_cmakers(dstore)
    maxw = sum(cm.weight for cm in cmakers) / (ct or 1)
    num_gs = [len(cm.gsims) for cm in cmakers if cm.weight > maxw]
    return sum(num_gs) * N * L * 8


def decide_num_tasks(dstore, concurrent_tasks):
    """
    :param dstore: DataStore
    :param concurrent_tasks: hint for the number of tasks to generate
    """
    cmakers = read_cmakers(dstore)
    weights = [cm.weight for cm in cmakers]
    maxw = 2*sum(weights) / concurrent_tasks
    dtlist = [('grp_id', U16), ('cmakers', U16), ('tiles', U16)]
    ntasks = []
    for cm in sorted(cmakers, key=lambda cm: weights[cm.grp_id], reverse=True):
        w = weights[cm.grp_id]
        nt = int(numpy.ceil(w / maxw / len(cm.gsims)))
        assert nt
        ntasks.append((cm.grp_id, len(cm.gsims), nt))
    return numpy.array(ntasks, dtlist)


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
        self.cfactor += dic.pop('cfactor')

        # store rup_data if there are few sites
        if self.few_sites and len(dic['rup_data']):
            with self.monitor('saving rup_data'):
                store_ctxs(self.datastore, dic['rup_data'], grp_id)

        pnemap = dic['pnemap']  # probabilities of no exceedence
        pnemap.grp_id = grp_id
        pmap_by_src = dic.pop('pmap_by_src', {})
        # len(pmap_by_src) > 1 only for mutex sources, see contexts.py
        for source_id, pm in pmap_by_src.items():
            # store the poes for the given source
            acc[source_id] = pm
            pm.grp_id = grp_id
        if pnemap and grp_id in acc:
            acc[grp_id].update(pnemap)
        elif pnemap:
            with self.monitor('storing PoEs', measuremem=True):
                self.haz.store_poes(grp_id, pnemap)
            return acc
        self.n_outs[grp_id] -= 1
        if self.n_outs[grp_id] == 0:  # no other tasks for this grp_id
            with self.monitor('storing PoEs', measuremem=True):
                self.haz.store_poes(grp_id, acc.pop(grp_id))
        return acc

    def create_dsets(self):
        """
        Store some empty datasets in the datastore
        """
        params = {'grp_id', 'occurrence_rate', 'clon', 'clat', 'rrup',
                  'probs_occur', 'sids', 'src_id', 'rup_id', 'weight'}
        gsims_by_trt = self.full_lt.get_gsims_by_trt()

        for trt, gsims in gsims_by_trt.items():
            cm = ContextMaker(trt, gsims, self.oqparam)
            params.update(cm.REQUIRES_RUPTURE_PARAMETERS)
            params.update(cm.REQUIRES_DISTANCES)
        if self.few_sites:
            # self.oqparam.time_per_task = 1_000_000  # disable task splitting
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
        if self.oqparam.disagg_by_src:
            self.create_disagg_by_src()

    def create_disagg_by_src(self):
        """
        :returns: the unique source IDs contained in the composite model
        """
        oq = self.oqparam
        self.M = len(oq.imtls)
        self.L1 = oq.imtls.size // self.M
        sources = list(self.csm.source_info)
        size, msg = get_nbytes_msg(
            dict(N=self.N, R=self.R, M=self.M, L1=self.L1, Ns=len(sources)))
        if size > TWO32:
            raise RuntimeError('The matrix disagg_by_src is too large: %s'
                               % msg)
        self.datastore.create_dset(
            'disagg_by_src', F32,
            (self.N, self.R, self.M, self.L1, len(sources)))
        self.datastore.set_shape_descr(
            'disagg_by_src', site_id=self.N, rlz_id=self.R,
            imt=list(self.oqparam.imtls), lvl=self.L1, src_id=sources)
        return sources

    def init_poes(self):
        self.cfactor = numpy.zeros(2)
        self.rel_ruptures = AccumDict(accum=0)  # grp_id -> rel_ruptures
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
        self.datastore.create_dset('_poes/slice_by_sid', slice_dt)
        # NB: compressing the dataset causes a big slowdown in writing :-(

    def check_memory(self, N, L, max_gs, maxw):
        """
        Log the memory required to receive the largest ProbabilityMap,
        assuming all sites are affected (upper limit)
        """
        num_gs = []
        for cm in self.haz.cmakers:
            sg = self.csm.src_groups[cm.grp_id]
            if sg.atomic or sg.weight <= maxw:
                pass  # no need to keep the group in memory
            else:
                num_gs.append(len(cm.gsims))
        size = max_gs * N * L * 8
        tot = sum(num_gs) * N * L * 8
        logging.info('ProbabilityMap(G=%d,N=%d,L=%d): %s per core + %s',
                     max_gs, N, L, humansize(size), humansize(tot))
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
                self.build_curves_maps()  # repeat post-processing
                return {}
            else:  # after preclassical, like in case_36
                logging.info('Reading from parent calculation')
                self.csm = parent['_csm']
                oq.mags_by_trt = {
                    trt: python3compat.decode(dset[:])
                    for trt, dset in parent['source_mags'].items()}
                self.full_lt = parent['full_lt']
                self.datastore['source_info'] = parent['source_info'][:]
                maxw = self.csm.get_max_weight(oq)
        else:
            maxw = self.max_weight
        self.init_poes()
        srcidx = {
            rec[0]: i for i, rec in enumerate(self.csm.source_info.values())}
        self.haz = Hazard(self.datastore, self.full_lt, srcidx)
        self.source_data = AccumDict(accum=[])
        t0 = time.time()
        if oq.keep_source_groups is None:
            # enable keep_source_groups if the pmaps would take 30+ GB
            oq.keep_source_groups = get_pmaps_size(
		self.datastore, oq.concurrent_tasks) > 30 * 1024**3
        if oq.keep_source_groups:
            self.execute_keep_groups()
        else:
            self.execute_split_groups(maxw)
        self.store_info()
        if self.cfactor[0] == 0:
            raise RuntimeError('Filtered away all ruptures??')
        logging.info('cfactor = {:_d}/{:_d} = {:.1f}'.format(
            int(self.cfactor[1]), int(self.cfactor[0]),
            self.cfactor[1] / self.cfactor[0]))
        if '_poes' in self.datastore:
            self.build_curves_maps()
        if not oq.hazard_calculation_id:
            self.classical_time = time.time() - t0
        return True

    def execute_split_groups(self, maxw):
        """
        Method called when keep_source_groups=False
        """
        oq = self.oqparam
        self.create_dsets()  # create the rup/ datasets BEFORE swmr_on()
        max_gs = max(len(cm.gsims) for cm in self.haz.cmakers)
        self.check_memory(len(self.sitecol), oq.imtls.size, max_gs, maxw)
        self.n_outs = AccumDict(accum=0)
        acc = self.run_tiles(maxw)
        self.haz.store_disagg(acc)

    def execute_keep_groups(self):
        """
        Method called when keep_source_groups=True
        """
        assert self.N > self.oqparam.max_sites_disagg, self.N
        decide = decide_num_tasks(
            self.datastore, self.oqparam.concurrent_tasks or 1)
        self.datastore.swmr_on()  # must come before the Starmap
        smap = parallel.Starmap(classical, h5=self.datastore.hdf5)
        for grp_id, ngsims, ntiles in decide:
            cmaker = self.haz.cmakers[grp_id]
            grp = self.csm.src_groups[grp_id]
            logging.info('Sending %s, %d gsims * %d tiles',
                         grp, len(cmaker.gsims), ntiles)
            for tile in self.sitecol.split(ntiles):
                for cm in cmaker.split_by_gsim():
                    smap.submit(
                        (self.datastore, None if ntiles == 1 else tile, cm))
        smap.reduce(self.agg_dicts)

    def run_tiles(self, maxw):
        """
        Run a subset of sites and update the accumulator
        """
        acc = {}
        oq = self.oqparam
        L = oq.imtls.size
        allargs = []
        for cm in self.haz.cmakers:
            G = len(cm.gsims)
            sg = self.csm.src_groups[cm.grp_id]

            # maximum size of the pmap array in GB
            size_gb = G * L * self.N * 8 / 1024**3
            ntiles = numpy.ceil(size_gb / oq.pmap_max_gb)
            # NB: disagg_by_src is disabled in case of tiling
            assert not (ntiles > 1 and oq.disagg_by_src)
            # NB: tiling only works with many sites
            assert ntiles == 1 or self.N > oq.max_sites_disagg * ntiles
            tiles = self.sitecol.split(ntiles)

            if sg.atomic or sg.weight <= maxw:
                for tile in tiles:
                    allargs.append((sg, tile, cm))
            else:
                # only heavy groups preallocate memory
                acc[cm.grp_id] = ProbabilityMap(
                    self.sitecol.sids, oq.imtls.size, len(cm.gsims)).fill(1)
                acc[cm.grp_id].start = cm.start
                if oq.disagg_by_src:  # possible only with a single tile
                    blks = groupby(sg, basename).values()
                else:
                    blks = block_splitter(sg, maxw, get_weight)
                for block in blks:
                    logging.debug('Sending %d source(s) with weight %d',
                                  len(block), sg.weight)
                    for tile in tiles:
                        self.n_outs[cm.grp_id] += 1
                        allargs.append((block, tile, cm))
        allargs.sort(key=lambda tup: sum(src.weight for src in tup[0]),
                     reverse=True)
        if not performance.numba:
            logging.warning('numba is not installed: using the slow algorithm')
        self.datastore.swmr_on()  # must come before the Starmap
        smap = parallel.Starmap(classical, allargs, h5=self.datastore.hdf5)
        return smap.reduce(self.agg_dicts, acc)

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
        Check for slow tasks and fix disagg_by_src if needed
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
        if 'disagg_by_src' in list(self.datastore):
            srcids = python3compat.decode(
                self.datastore['source_info']['source_id'])
            if any(';' in srcid for srcid in srcids):
                # enable reduction of the array disagg_by_src
                arr = self.datastore['disagg_by_src'][:]
                arr, srcids = semicolon_aggregate(arr, srcids)
                self.datastore['disagg_by_src'][:] = arr
                self.datastore.set_shape_descr(
                    'disagg_by_src', site_id=self.N, rlz_id=self.R,
                    imt=list(self.oqparam.imtls), lvl=self.L1, src_id=srcids)
        if 'disagg_by_src' in self.datastore:
            logging.info('Comparing disagg_by_src vs mean curves')
            check_disagg_by_src(self.datastore)

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
        ct = oq.concurrent_tasks or 1
        if 1 < ct < 80:  # saving memory on small machines
            ct = 80
        self.weights = ws = [rlz.weight for rlz in self.realizations]
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
        allslices = [compactify(slices) for slices in slicedic.values()]
        nslices = sum(len(slices) for slices in allslices)
        logging.info('There are %d slices of poes [%.1f per task]',
                     nslices, nslices / len(slicedic))
        allargs = [
            (getters.PmapGetter(dstore, ws, slices, oq.imtls, oq.poes),
             N, hstats, individual, oq.max_sites_disagg, self.amplifier)
            for slices in allslices]
        self.hazard = {}  # kind -> array
        hcbytes = 8 * N * S * M * L1
        hmbytes = 8 * N * S * M * P if oq.poes else 0
        logging.info('Producing %s of hazard curves and %s of hazard maps',
                     humansize(hcbytes), humansize(hmbytes))
        if not performance.numba:
            logging.warning('numba is not installed: using the slow algorithm')
        if not oq.hazard_calculation_id:
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
