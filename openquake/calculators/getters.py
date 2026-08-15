# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2026 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import os
import copy
import operator
import collections
import numpy

from openquake.baselib import general, hdf5
from openquake.hazardlib.map_array import MapArray
from openquake.hazardlib.contexts import get_unique_inverse
from openquake.hazardlib.calc.disagg import to_rates, to_probs
from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.source.rupture import get_ebrupture  # noqa: F401
from openquake.commonlib.calc import get_proxies

U16 = numpy.uint16
U32 = numpy.uint32
I64 = numpy.int64
F32 = numpy.float32
TWO24 = 2 ** 24
by_taxonomy = operator.attrgetter('taxonomy')
code2cls = BaseRupture.init()
weight = operator.itemgetter('n_occ')
slice_dt = numpy.dtype([('idx', U32), ('start', int), ('stop', int)])


class NotFound(Exception):
    pass


def build_stat_curve(hcurve, imtls, stat, wget, use_rates=False):
    """
    Build statistics by taking into account IMT-dependent weights
    """
    weights = wget.weights
    poes = hcurve.T  # shape R, L
    assert len(poes) == len(weights), (len(poes), len(weights))
    L = imtls.size
    array = numpy.zeros((L, 1))

    if weights.shape[1] > 1:  # IMT-dependent weights
        # this is slower since the arrays are shorter
        for imt in imtls:
            slc = imtls(imt)
            ws = wget(None, imt)
            if not ws.sum():  # expect no data for this IMT
                continue
            if use_rates:
                array[slc, 0] = to_probs(stat(to_rates(poes[:, slc]), ws))
            else:
                array[slc, 0] = stat(poes[:, slc], ws)
    else:
        if use_rates:
            array[:, 0] = to_probs(stat(to_rates(poes), weights[:, -1]))
        else:
            array[:, 0] = stat(poes, weights[:, -1])
    return array


def sig_eps_dt(imts):
    """
    :returns: a composite data type for the sig_eps output
    """
    lst = [('eid', U32), ('rlz_id', U16)]
    for imt in imts:
        lst.append(('sig_inter_' + imt, F32))
    for imt in imts:
        lst.append(('eps_inter_' + imt, F32))
    return numpy.dtype(lst)


class HcurvesGetter(object):
    """
    Read the contribution to the hazard curves coming from each source
    in a calculation with a source specific logic tree
    """
    def __init__(self, dstore):
        self.dstore = dstore
        self.imtls = dstore['oqparam'].imtls
        self.full_lt = dstore['full_lt'].init()
        self.sslt = self.full_lt.source_model_lt.decompose()
        self.source_info = dstore['source_info'][:]

    def get_hcurve(self, src_id, imt=None, site_id=0, gsim_idx=None):
        """
        Return the curve associated to the given src_id, imt and gsim_idx
        as an array of length L
        """
        assert ';' in src_id, src_id  # must be a realization specific src_id
        imt_slc = self.imtls(imt) if imt else slice(None)
        start, gsims, weights = self.bysrc[src_id]
        # Source-specific LT + site LT is unsupported: _rates is split
        # across _rates_site_i groups so there is no unambiguous curve
        if '_rates' not in self.dstore:
            raise NotImplementedError(
                'HcurvesGetter is not supported when a site-model logic '
                'tree is present')
        dset = self.dstore['_rates']
        if gsim_idx is None:
            curves = dset[start:start + len(gsims), site_id, imt_slc]
            return weights @ curves
        return to_probs(dset[start + gsim_idx, site_id, imt_slc])

    # NB: not used right now
    def get_hcurves(self, src, imt=None, site_id=0, gsim_idx=None):
        """
        Return the curves associated to the given src, imt and gsim_idx
        as an array of shape (R, L)
        """
        assert ';' not in src, src  # not a rlz specific source ID
        curves = []
        for i in range(self.sslt[src].num_paths):
            src_id = '%s;%d' % (src, i)
            curves.append(self.get_hcurve(src_id, imt, site_id, gsim_idx))
        return numpy.array(curves)

    def get_mean_hcurve(self, src=None, imt=None, site_id=0, gsim_idx=None):
        """
        Return the mean curve associated to the given src, imt and gsim_idx
        as an array of shape L
        """
        if src is None:
            hcurves = [self.get_mean_hcurve(src) for src in self.sslt]
            return general.agg_probs(*hcurves)
        weights = [rlz.weight for rlz in self.sslt[src]]
        curves = self.get_hcurves(src, imt, site_id, gsim_idx)
        return weights @ curves


# NB: using 32 bit ratemaps
def get_rmap_gb(dstore, full_lt=None):
    """
    :returns: (size_of_the_global_RateMap_in_GB, trt_rlzs, trt_smrs)
    """
    N = len(dstore['sitecol/sids'])
    L = dstore['oqparam'].imtls.size
    full_lt = full_lt or dstore['full_lt'].init()
    if 'trt_smrs' not in dstore:  # starting from hazard_curves.csv
        trt_smrs = [[0]]
    else:
        trt_smrs, _ = get_unique_inverse(dstore['trt_smrs'][:])
    trt_rlzs = full_lt.get_trt_rlzs(trt_smrs)
    max_gb = len(trt_rlzs) * N * L * 4 / 1024**3
    return max_gb, trt_rlzs, trt_smrs


def get_num_chunks(dstore, full_lt=None):
    """
    :returns: number of chunks to generate (determine postclassical tasks)

    For performance, it is important to generate few chunks.
    There are three regimes:

    - classical_risk from hazard_curves.csv, num_chunks=1
    - few sites, num_chunks=N
    - regular, num_chunks=concurrent_tasks/2
    - lots of data, num_chunks=req_gb
    """
    oq = dstore['oqparam']
    if 'hazard_curves' in oq.inputs:
        return 1
    N = len(dstore['sitecol/sids'])
    ct2 = oq.concurrent_tasks // 2 or 1
    if N < ct2 or oq.calculation_mode == 'disaggregation':
        return N  # one chunk per site
    req_gb, _, _ = get_rmap_gb(dstore, full_lt)
    ntiles = int(numpy.ceil(req_gb))
    return ntiles if ntiles > ct2 else ct2
    # for EUR on cole concurrent_tasks=256
    # req_gb=202, N=260,000 => 202


def map_getters(dstore, full_lt=None, oq=None, disagg=False):
    """
    :returns: a list of pairs (MapGetter, weights)
    """
    oq = oq or dstore['oqparam']
    n = get_num_chunks(dstore, full_lt)

    # full_lt is None in classical_risk, classical_damage
    full_lt = full_lt or dstore['full_lt'].init()
    R = full_lt.get_num_paths()
    _req_gb, trt_rlzs, trt_smrs = get_rmap_gb(dstore, full_lt)
    attrs = vars(full_lt)
    full_lt.init()
    gweights, wgets = None, None
    if oq.fastmean:
        gweights = [full_lt.g_weights(trt_smrs)]
    else:
        wgets = [full_lt.gsim_lt.wget]
    for label in oq.site_labels:
        flt = copy.copy(full_lt)
        flt.__dict__.update(attrs)
        flt.gsim_lt = dstore['gsim_lt' + label]
        flt.init()
        if oq.fastmean:
            gweights.append(flt.g_weights(trt_smrs))
        else:
            wgets.append(flt.gsim_lt.wget)
    fnames = [dstore.filename]
    calc_dir = dstore.filename[:-5]
    if os.path.exists(calc_dir):
        for f in os.listdir(calc_dir):
            if f.endswith('.hdf5'):
                fnames.append(os.path.join(calc_dir, f))

    sids = dstore['sitecol/sids'][:]

    # Under a site-model LT there are Rsite variants
    # (rates_dset, rlz_mask); otherwise a single ('_rates', None) variant
    variants, gws_by_site = _site_lt_variants(full_lt, trt_smrs, oq.fastmean)
    site_lt_on = getattr(full_lt, 'site_model_lt', None) is not None
    out = []
    for chunk in range(n):
        tile = sids[sids % n == chunk]
        sub_getters = []
        for j, (rates_dset, rlz_mask) in enumerate(variants):
            getter = MapGetter(fnames, chunk, trt_rlzs, tile, R, oq,
                               rates_dset=rates_dset, rlz_mask=rlz_mask)
            if oq.fastmean:
                getter.gweights = [gws_by_site[j]] if site_lt_on else gweights
            else:
                getter.wgets = wgets
            if oq.site_labels:
                getter.ilabels = dstore['sitecol'].ilabel
            sub_getters.append(getter)
        if site_lt_on and (disagg or oq.fastmean):
            out.append(MergedMapGetter(sub_getters))
        else:
            out.extend(sub_getters)
    return out


def _site_lt_variants(full_lt, trt_smrs, fastmean):
    """
    :returns: (variants, gweights_by_site)
        variants is a list of (rates_dset, rlz_mask); for the
        no-site-LT case that's a single ('_rates', None) entry.
        gweights_by_site is None unless fastmean is on
        together with a site LT
    """
    site_lt = getattr(full_lt, 'site_model_lt', None)
    if site_lt is None:
        return [('_rates', None)], None
    site_ords = numpy.array([r.site_rlz.ordinal
                             for r in full_lt.get_realizations()])
    used_i = [i for i in range(site_lt.Rsite) if (site_ords == i).any()]
    variants = [('_rates_site_%d' % i, site_ords == i) for i in used_i]
    if not fastmean:
        return variants, None
    # Per-site-rlz gweights: for each gid, sum weights of rlzs owned by
    # this branch only, so fastmean's sum over sub-getters reproduces
    # sum_r w_r * rate_r
    gws_by_site = []
    for i in used_i:
        mask = site_ords == i
        gwi = []
        for _trt_smrs in trt_smrs:
            for grlzs in full_lt.get_rlzs_by_gsim(_trt_smrs).values():
                mrlzs = numpy.array([r for r in grlzs if mask[r]], dtype=int)
                if len(mrlzs):
                    gwi.append(full_lt.weights[mrlzs].sum(axis=0))
                else:
                    gwi.append(numpy.zeros_like(full_lt.weights[0]))
        gws_by_site.append(numpy.array(gwi))
    return variants, gws_by_site


class ZeroGetter(object):
    """
    Return an array of zeros of shape (L, R)
    """
    def __init__(self, L, R):
        self.L = L
        self.R = R

    def get_hazard(self):
        return numpy.zeros((self.L, self.R))


class CurveGetter(object):
    """
    Hazard curve builder used in classical_risk/classical_damage.

    :param sid: site index
    :param rates: array of shape (L, G) for the given site
    """
    @classmethod
    def build(cls, dstore):
        """
        :returns: a dictionary sid -> CurveGetter
        """
        rates = {}
        for mgetter in map_getters(dstore):
            array = mgetter.init()
            for sid, idx in mgetter.sid2idx.items():
                rates[sid] = array[idx]  # shape (L, G)
        dic = collections.defaultdict(lambda: ZeroGetter(mgetter.L, mgetter.R))
        for sid in rates:
            dic[sid] = cls(sid, rates[sid], mgetter.trt_rlzs, mgetter.R)
        return dic

    def __init__(self, sid, rates, trt_rlzs, R):
        self.sid = sid
        self.rates = rates
        self.trt_rlzs = trt_rlzs
        self.R = R

    def get_hazard(self):
        r0 = numpy.zeros((len(self.rates), self.R))
        for g, t_rlzs in enumerate(self.trt_rlzs):
            rlzs = t_rlzs % TWO24
            rates = self.rates[:, g]
            for rlz in rlzs:
                r0[:, rlz] += rates
        return to_probs(r0)


class DeltaRatesGetter(object):
    """
    Read the delta rates from an aftershock datastore
    """
    def __init__(self, dstore):
        self.dstore = dstore

    def __call__(self, src_id):
        with self.dstore.open('r') as dstore:
            return dstore['delta_rates'][src_id]


class MapGetter(object):
    """
    Read hazard curves from the datastore for all realizations or for a
    specific realization.
    """
    def __init__(self, filenames, chunk, trt_rlzs, sids, R, oq,
                 rates_dset='_rates', rlz_mask=None):
        self.filenames = filenames
        self.chunk = chunk
        self.trt_rlzs = trt_rlzs
        self.sids = sids
        self.R = R
        self.imtls = oq.imtls
        self.poes = oq.poes
        self.use_rates = oq.use_rates
        self.eids = None
        self.ilabels = ()  # overridden in case of ilabels
        self.array = None
        # Under site-model LT, rates are split into _rates_site_i groups
        # and rlz_mask picks the rlzs owned by that site branch
        self.rates_dset = rates_dset
        self.rlz_mask = rlz_mask

    @property
    def imts(self):
        return list(self.imtls)

    @property
    def Gt(self):
        return len(self.trt_rlzs)

    @property
    def L(self):
        return self.imtls.size

    @property
    def N(self):
        return len(self.sids)

    @property
    def M(self):
        return len(self.imtls)

    def init(self):
        """
        Build the array from the underlying dataframes
        """
        if self.array is not None:
            return self.array
        sid2idx = {sid: idx for idx, sid in enumerate(self.sids)}
        self.array = numpy.zeros((self.N, self.L, self.Gt))  # move to 32 bit
        slice_key = '%s/slice_by_idx' % self.rates_dset
        for fname in self.filenames:
            with hdf5.File(fname) as dstore:
                if self.rates_dset not in dstore:
                    continue
                slices = dstore[slice_key][:]
                slices = slices[slices['idx'] == self.chunk]
                for start, stop in zip(slices['start'], slices['stop']):
                    df = dstore.read_df(
                        self.rates_dset, slc=slice(start, stop))
                    idxs = U32([sid2idx[sid] for sid in df.sid])
                    lid = df.lid.to_numpy()
                    gid = df.gid.to_numpy()
                    self.array[idxs, lid, gid] += df.rate
        self.sid2idx = sid2idx
        return self.array

    def get_hcurve(self, sid):  # used in classical
        """
        :param sid: a site ID
        :returns: an array of shape (L, R) for the given site ID
        """
        array = self.init()
        r0 = numpy.zeros((self.L, self.R))
        idx = self.sid2idx[sid]
        for g, t_rlzs in enumerate(self.trt_rlzs):
            rlzs = t_rlzs % TWO24
            rates = array[idx, :, g]
            for rlz in rlzs:
                if self.rlz_mask is not None and not self.rlz_mask[rlz]:
                    continue
                r0[:, rlz] += rates
        return to_probs(r0)

    def get_fast_mean(self):
        """
        :returns: a MapArray of shape (N, M, L1) with the mean hcurves
        """
        M = self.M
        L1 = self.L // M
        means = MapArray(U32(self.sids), M, L1).fill(0)
        gweights = self.gweights[0]
        imt_dep_weights = gweights.shape[1] > 1
        for sid in self.sids:
            if len(self.ilabels):
                gweights = self.gweights[self.ilabels[sid]]
            rates = self.array[self.sid2idx[sid]]  # shape (L, G)
            sidx = means.sidx[sid]
            for m in range(M):
                means.array[sidx, m] = rates[m*L1: m*L1+L1] @ gweights[
                    :, m if imt_dep_weights else -1]
        means.array[:] = to_probs(means.array)
        return means


class MergedMapGetter(object):
    """
    Wraps a list of per-site-rlz :class:`MapGetter` instances (all sharing
    chunk, sids, trt_rlzs, R) into one getter with a single
    hcurve per sid; used by disagg and fastmean under a site-model LT
    """
    def __init__(self, sub_getters):
        first = sub_getters[0]
        self.sub_getters = sub_getters
        self.filenames = first.filenames
        self.chunk = first.chunk
        self.trt_rlzs = first.trt_rlzs
        self.sids = first.sids
        self.R = first.R
        self.imtls = first.imtls
        self.poes = first.poes
        self.use_rates = first.use_rates
        self.eids = None
        self.ilabels = first.ilabels
        self.wgets = getattr(first, 'wgets', None)
        self.gweights = getattr(first, 'gweights', None)
        self.array = None

    @property
    def imts(self):
        return list(self.imtls)

    @property
    def L(self):
        return self.imtls.size

    @property
    def M(self):
        return len(self.imtls)

    def init(self):
        for sub in self.sub_getters:
            sub.init()
        self.sid2idx = self.sub_getters[0].sid2idx

    def get_hcurve(self, sid):
        """
        :returns: an array of shape (L, R); each column r is taken
            from the sub-getter whose rlz_mask includes r
        """
        r0 = numpy.zeros((self.L, self.R))
        for sub in self.sub_getters:
            r0[:, sub.rlz_mask] = sub.get_hcurve(sid)[:, sub.rlz_mask]
        return r0

    def get_fast_mean(self):
        """
        :returns: a :class:`MapArray` of shape (N, M, L1) with the mean
            hcurves, aggregated across sub-getter rates before to_probs
        """
        M = self.M
        L1 = self.L // M
        means = MapArray(U32(self.sids), M, L1).fill(0)
        for sub in self.sub_getters:
            sub.init()
            gweights = sub.gweights[0]
            imt_dep = gweights.shape[1] > 1
            for sid in self.sids:
                gw = (sub.gweights[sub.ilabels[sid]]
                      if len(sub.ilabels) else gweights)
                rates = sub.array[sub.sid2idx[sid]]  # shape (L, G)
                sidx = means.sidx[sid]
                for m in range(M):
                    means.array[sidx, m] += rates[m*L1:m*L1+L1] @ gw[
                        :, m if imt_dep else -1]
        means.array[:] = to_probs(means.array)
        return means


def get_ebruptures(dstore):
    """
    Extract EBRuptures from the datastore
    """
    ebrs = []
    trts = list(dstore['full_lt/gsim_lt'].values)
    for proxy in get_proxies(dstore.filename):
        ebrs.append(proxy.to_ebr(trts[0]))
    return ebrs


def line(points):
    return '(%s)' % ', '.join('%.5f %.5f %.5f' % tuple(p) for p in points)


def multiline(array3RC):
    """
    :param array3RC: array of shape (3, R, C)
    :returns: a MULTILINESTRING
    """
    D, R, _C = array3RC.shape
    assert D == 3, D
    lines = 'MULTILINESTRING(%s)' % ', '.join(
        line(array3RC[:, r, :].T) for r in range(R))
    return lines
