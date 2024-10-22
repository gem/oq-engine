# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2023 GEM Foundation
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
import operator
import collections
import numpy

from openquake.baselib import general, hdf5
from openquake.hazardlib.map_array import MapArray
from openquake.hazardlib.calc.disagg import to_rates, to_probs
from openquake.hazardlib.source.rupture import (
    BaseRupture, RuptureProxy, get_ebr)
from openquake.commonlib import datastore

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


def build_stat_curve(hcurve, imtls, stat, weights, wget, use_rates=False):
    """
    Build statistics by taking into account IMT-dependent weights
    """
    poes = hcurve.T  # shape R, L
    assert len(poes) == len(weights), (len(poes), len(weights))
    L = imtls.size
    array = numpy.zeros((L, 1))
    
    if weights.shape[1] > 1:  # IMT-dependent weights
        # this is slower since the arrays are shorter
        for imt in imtls:
            slc = imtls(imt)
            ws = wget(weights, imt)
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
def get_pmaps_gb(dstore, full_lt=None):
    """
    :returns: memory required on the master node to keep the pmaps
    """
    N = len(dstore['sitecol/sids'])
    L = dstore['oqparam'].imtls.size
    full_lt = full_lt or dstore['full_lt'].init()
    if 'trt_smrs' not in dstore:  # starting from hazard_curves.csv
        trt_smrs = [[0]]
    else:
        trt_smrs = dstore['trt_smrs'][:]
    trt_rlzs = full_lt.get_trt_rlzs(trt_smrs)
    gids = full_lt.get_gids(trt_smrs)
    max_gb = len(trt_rlzs) * N * L * 4 / 1024**3
    return max_gb, trt_rlzs, gids


def get_num_chunks(dstore):
    """
    :returns: the number of postclassical tasks to generate.

    It is 5 times the number of GB required to store the rates.
    """
    msd = dstore['oqparam'].max_sites_disagg
    try:
        req_gb = dstore['source_groups'].attrs['req_gb']
    except KeyError:
        return msd
    chunks = max(int(5 * req_gb), msd)
    return chunks

    
def map_getters(dstore, full_lt=None, disagg=False):
    """
    :returns: a list of pairs (MapGetter, weights)
    """
    oq = dstore['oqparam']
    # disaggregation is meant for few sites, i.e. no tiling
    N = len(dstore['sitecol/sids'])
    chunks = get_num_chunks(dstore)
    if disagg and N > chunks:
        raise ValueError('There are %d sites but only %d chunks' % (N, chunks))

    full_lt = full_lt or dstore['full_lt'].init()
    R = full_lt.get_num_paths()
    _req_gb, trt_rlzs, _gids = get_pmaps_gb(dstore, full_lt)
    if oq.fastmean and not disagg:
        weights = dstore['gweights'][:]
        trt_rlzs = numpy.zeros(len(weights))  # reduces the data transfer
    else:
       weights = full_lt.weights
    fnames = [dstore.filename]
    try:
        scratch_dir = dstore.hdf5.attrs['scratch_dir']
    except KeyError:  # no tiling
        pass
    else:
        for f in os.listdir(scratch_dir):
            if f.endswith('.hdf5'):
                fnames.append(os.path.join(scratch_dir, f))
    out = []
    for chunk in range(chunks):
        getter = MapGetter(fnames, chunk, trt_rlzs, R, oq)
        getter.weights = weights
        out.append(getter)
    return out


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
            pmap = mgetter.init()
            for sid in pmap:
                rates[sid] = pmap[sid]  # shape (L, G)
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

    
class MapGetter(object):
    """
    Read hazard curves from the datastore for all realizations or for a
    specific realization.
    """
    def __init__(self, filenames, idx, trt_rlzs, R, oq):
        self.filenames = filenames
        self.idx = idx
        self.trt_rlzs = trt_rlzs
        self.R = R
        self.imtls = oq.imtls
        self.poes = oq.poes
        self.use_rates = oq.use_rates
        self.eids = None
        self._map = {}

    @property
    def sids(self):
        self.init()
        return list(self._map)

    @property
    def imts(self):
        return list(self.imtls)

    @property
    def G(self):
        return len(self.trt_rlzs)

    @property
    def L(self):
        return self.imtls.size

    @property
    def N(self):
        self.init()
        return len(self._map)

    @property
    def M(self):
        return len(self.imtls)

    def init(self):
        """
        Build the _map from the underlying dataframes
        """
        if self._map:
            return self._map
        for fname in self.filenames:
            with hdf5.File(fname) as dstore:
                slices = dstore['_rates/slice_by_idx'][:]
                slices = slices[slices['idx'] == self.idx]
                for start, stop in zip(slices['start'], slices['stop']):
                    rates_df = dstore.read_df('_rates', slc=slice(start, stop))
                    # not using groupby to save memory
                    for sid in rates_df.sid.unique():
                        df = rates_df[rates_df.sid == sid]
                        try:
                            array = self._map[sid]
                        except KeyError:
                            array = numpy.zeros((self.L, self.G))
                            self._map[sid] = array
                        array[df.lid, df.gid] = df.rate
        return self._map

    def get_hcurve(self, sid):  # used in classical
        """
        :param sid: a site ID
        :returns: an array of shape (L, R) for the given site ID
        """
        pmap = self.init()
        r0 = numpy.zeros((self.L, self.R))
        if sid not in pmap:  # no hazard for sid
            return r0
        for g, t_rlzs in enumerate(self.trt_rlzs):
            rlzs = t_rlzs % TWO24
            rates = pmap[sid][:, g]
            for rlz in rlzs:
                r0[:, rlz] += rates
        return to_probs(r0)

    def get_fast_mean(self, gweights):
        """
        :returns: a MapArray of shape (N, M, L1) with the mean hcurves
        """
        M = self.M
        L1 = self.L // M
        means = MapArray(U32(self.sids), M, L1).fill(0)
        for sid in self.sids:
            idx = means.sidx[sid]
            rates = self._map[sid]  # shape (L, G)
            means.array[idx] = (rates @ gweights).reshape((M, L1))
        means.array[:] = to_probs(means.array)
        return means


def get_rupture_getters(dstore, ct=0, srcfilter=None, rupids=None):
    """
    :param dstore: a :class:`openquake.commonlib.datastore.DataStore`
    :param ct: number of concurrent tasks
    :returns: a list of RuptureGetters
    """
    full_lt = dstore['full_lt'].init()
    rup_array = dstore['ruptures'][:]
    if rupids is not None:
        rup_array = rup_array[numpy.isin(rup_array['id'], rupids)]
    if len(rup_array) == 0:
        raise NotFound('There are no ruptures in %s' % dstore)
    proxies = [RuptureProxy(rec) for rec in rup_array]
    maxweight = rup_array['n_occ'].sum() / (ct / 2 or 1)
    rgetters = []
    for block in general.block_splitter(
            proxies, maxweight, operator.itemgetter('n_occ'),
            key=operator.itemgetter('trt_smr')):
        trt_smr = block[0]['trt_smr']
        rbg = full_lt.get_rlzs_by_gsim(trt_smr)
        rg = RuptureGetter(block, dstore.filename, trt_smr,
                           full_lt.trt_by(trt_smr), rbg)
        rgetters.append(rg)
    return rgetters


def get_ebruptures(dstore):
    """
    Extract EBRuptures from the datastore
    """
    ebrs = []
    for rgetter in get_rupture_getters(dstore):
        for proxy in rgetter.get_proxies():
            ebrs.append(proxy.to_ebr(rgetter.trt))
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


def get_ebrupture(dstore, rup_id):  # used in show rupture
    """
    This is EXTREMELY inefficient, so it must be used only when you are
    interested in a single rupture.
    """
    rups = dstore['ruptures'][:]  # read everything in memory
    rupgeoms = dstore['rupgeoms']  # do not read everything in memory
    idxs, = numpy.where(rups['id'] == rup_id)
    if len(idxs) == 0:
        raise ValueError(f"Missing {rup_id=}")
    [rec] = rups[idxs]
    trts = dstore.getitem('full_lt').attrs['trts']
    trt = trts[rec['trt_smr'] // TWO24]
    geom = rupgeoms[rec['geom_id']]
    return get_ebr(rec, geom, trt)


# this is never called directly; get_rupture_getters is used instead
class RuptureGetter(object):
    """
    :param proxies:
        a list of RuptureProxies
    :param filename:
        path to the HDF5 file containing a 'rupgeoms' dataset
    :param trt_smr:
        source group index
    :param trt:
        tectonic region type string
    :param rlzs_by_gsim:
        dictionary gsim -> rlzs for the group
    """
    def __init__(self, proxies, filename, trt_smr, trt, rlzs_by_gsim):
        self.proxies = proxies
        self.weight = sum(proxy['n_occ'] for proxy in proxies)
        self.filename = filename
        self.trt_smr = trt_smr
        self.trt = trt
        self.rlzs_by_gsim = rlzs_by_gsim
        self.num_events = sum(int(proxy['n_occ']) for proxy in proxies)

    @property
    def num_ruptures(self):
        return len(self.proxies)

    @property
    def seeds(self):
        return [p['seed'] for p in self.proxies]

    def get_proxies(self, min_mag=0):
        """
        :returns: a list of RuptureProxies
        """
        proxies = []
        with datastore.read(self.filename) as dstore:
            rupgeoms = dstore['rupgeoms']
            for proxy in self.proxies:
                if proxy['mag'] < min_mag:
                    # discard small magnitudes
                    continue
                proxy.geom = rupgeoms[proxy['geom_id']]
                proxies.append(proxy)
        return proxies

    # called in ebrisk calculations
    def split(self, srcfilter, maxw):
        """
        :returns: RuptureProxies with weight < maxw
        """
        proxies = []
        for proxy in self.proxies:
            sids = srcfilter.close_sids(proxy.rec, self.trt)
            if len(sids):
                proxies.append(proxy)
        rgetters = []
        for block in general.block_splitter(proxies, maxw, weight):
            rg = RuptureGetter(block, self.filename, self.trt_smr, self.trt,
                               self.rlzs_by_gsim)
            rgetters.append(rg)
        return rgetters

    def __len__(self):
        return len(self.proxies)

    def __repr__(self):
        wei = ' [w=%d]' % self.weight if hasattr(self, 'weight') else ''
        return '<%s trt_smr=%d, %d rupture(s)%s>' % (
            self.__class__.__name__, self.trt_smr, len(self), wei)
