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

from openquake.baselib import general, hdf5, config
from openquake.hazardlib.map_array import MapArray
from openquake.hazardlib.contexts import get_unique_inverse
from openquake.hazardlib.calc.disagg import to_rates, to_probs
from openquake.hazardlib.source.rupture import BaseRupture, get_ebr
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
        trt_smrs, _ = get_unique_inverse(dstore['trt_smrs'][:])
    trt_rlzs = full_lt.get_trt_rlzs(trt_smrs)
    max_gb = len(trt_rlzs) * N * L * 4 / 1024**3
    return max_gb, trt_rlzs, trt_smrs


def get_num_chunks(dstore):
    """
    :returns: number of chunks to generate (determine postclassical tasks)

    For performance, it is important to generate few chunks.
    There are three regimes:

    - few sites, num_chunks=N
    - regular, num_chunks=concurrent_tasks/2
    - lots of data, num_chunks=req_gb
    """
    oq = dstore['oqparam']
    N = len(dstore['sitecol/sids'])
    ct2 = oq.concurrent_tasks // 2 or 1
    if N < ct2 or oq.calculation_mode == 'disaggregation':
        return N  # one chunk per site
    try:
        req_gb = int(dstore['source_groups'].attrs['req_gb'])
    except KeyError: # in classical_bcr
        req_gb = .1
    max_gb = int(config.memory.pmap_max_mb) / 1024
    ntiles = int(numpy.ceil(req_gb / max_gb))
    return ntiles if ntiles > ct2 else ct2
    # for EUR on cole concurrent_tasks=256
    # req_gb=202, N=260,000


def map_getters(dstore, full_lt=None, oq=None, disagg=False):
    """
    :returns: a list of pairs (MapGetter, weights)
    """
    oq = oq or dstore['oqparam']
    n = get_num_chunks(dstore)

    # full_lt is None in classical_risk, classical_damage
    full_lt = full_lt or dstore['full_lt'].init()
    R = full_lt.get_num_paths()
    _req_gb, trt_rlzs, trt_smrs = get_pmaps_gb(dstore, full_lt)
    attrs = vars(full_lt)
    full_lt.init()
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
    try:
        scratch_dir = dstore.hdf5.attrs['scratch_dir']
    except KeyError:  # no tiling
        pass
    else:
        for f in os.listdir(scratch_dir):
            if f.endswith('.hdf5'):
                fnames.append(os.path.join(scratch_dir, f))
    out = []
    sids = dstore['sitecol/sids'][:]
    for chunk in range(n):
        tile = sids[sids % n == chunk]
        getter = MapGetter(fnames, chunk, trt_rlzs, tile, R, oq)
        if oq.fastmean:
            getter.gweights = gweights
        else:
            getter.wgets = wgets
        if oq.site_labels:
            getter.ilabels = dstore['sitecol'].ilabel
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
    def __init__(self, filenames, chunk, trt_rlzs, sids, R, oq):
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
        for fname in self.filenames:
            with hdf5.File(fname) as dstore:
                slices = dstore['_rates/slice_by_idx'][:]
                slices = slices[slices['idx'] == self.chunk]
                for start, stop in zip(slices['start'], slices['stop']):
                    df = dstore.read_df('_rates', slc=slice(start, stop))
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
                r0[:, rlz] += rates
        return to_probs(r0)

    def get_fast_mean(self):
        """
        :returns: a MapArray of shape (N, M, L1) with the mean hcurves
        """
        M = self.M
        L1 = self.L // M
        means = MapArray(U32(self.sids), M, L1).fill(0)
        for sid in self.sids:
            rates = self.array[self.sid2idx[sid]]  # shape (L, G)
            if len(self.ilabels):
                gweights = self.gweights[self.ilabels[sid]]
            else:
                gweights = self.gweights[0]
            sidx = means.sidx[sid]
            means.array[sidx] = (rates @ gweights).reshape((M, L1))
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


def get_ebrupture(dstore, rup_id):  # used in show rupture
    """
    This is EXTREMELY inefficient, since it reads all ruptures.
    NB: it assumes rup_is is unique
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
