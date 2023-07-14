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

import operator
import numpy

from openquake.baselib import general, hdf5
from openquake.hazardlib import probability_map, stats
from openquake.hazardlib.calc.disagg import to_rates, to_probs
from openquake.hazardlib.source.rupture import (
    BaseRupture, RuptureProxy, EBRupture, get_ebr)
from openquake.commonlib import datastore

U16 = numpy.uint16
U32 = numpy.uint32
I64 = numpy.int64
F32 = numpy.float32
TWO24 = 2 ** 24
by_taxonomy = operator.attrgetter('taxonomy')
code2cls = BaseRupture.init()
weight = operator.itemgetter('n_occ')


class NotFound(Exception):
    pass


def build_stat_curve(pcurve, imtls, stat, weights, use_rates=False):
    """
    Build statistics by taking into account IMT-dependent weights
    """
    poes = pcurve.array.T  # shape R, L
    assert len(poes) == len(weights), (len(poes), len(weights))
    L = imtls.size
    array = numpy.zeros((L, 1))
    if isinstance(weights, list):  # IMT-dependent weights
        # this is slower since the arrays are shorter
        for imt in imtls:
            slc = imtls(imt)
            ws = [w[imt] for w in weights]
            if sum(ws) == 0:  # expect no data for this IMT
                continue
            if use_rates:
                array[slc, 0] = to_probs(stat(to_rates(poes[:, slc]), ws))
            else:
                array[slc, 0] = stat(poes[:, slc], ws)
    else:
        if use_rates:
            array[:, 0] = to_probs(stat(to_rates(poes), weights))
        else:
            array[:, 0] = stat(poes, weights)
    return probability_map.ProbabilityCurve(array)


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
        dset = self.dstore['_poes']
        if gsim_idx is None:
            curves = dset[start:start + len(gsims), site_id, imt_slc]
            return weights @ curves
        return dset[start + gsim_idx, site_id, imt_slc]

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


class PmapGetter(object):
    """
    Read hazard curves from the datastore for all realizations or for a
    specific realization.

    :param dstore: a DataStore instance or file system path to it
    :param sids: the subset of sites to consider (if None, all sites)
    """
    def __init__(self, dstore, full_lt, slices, imtls=(), poes=(), use_rates=0):
        self.filename = dstore if isinstance(dstore, str) else dstore.filename
        if len(full_lt.weights[0].dic) == 1:  # no weights by IMT
            self.weights = numpy.array([w['weight'] for w in full_lt.weights])
        else:
            self.weights = full_lt.weights
        self.imtls = imtls
        self.poes = poes
        self.use_rates = use_rates
        self.num_rlzs = len(full_lt.weights)
        self.eids = None
        if 'trt_smrs' not in dstore:  # starting from hazard_curves.csv
            self.trt_rlzs = full_lt.get_trt_rlzs([[0]])
        else:
            self.trt_rlzs = full_lt.get_trt_rlzs(dstore['trt_smrs'][:])
        self.slices = slices
        self._pmap = {}

    @property
    def sids(self):
        self.init()
        return list(self._pmap)

    @property
    def imts(self):
        return list(self.imtls)

    @property
    def L(self):
        return self.imtls.size

    @property
    def N(self):
        self.init()
        return len(self._pmap)

    @property
    def M(self):
        return len(self.imtls)

    @property
    def R(self):
        return len(self.weights)

    def init(self):
        """
        Build the probability curves from the underlying dataframes
        """
        if self._pmap:
            return self._pmap
        G = len(self.trt_rlzs)
        with hdf5.File(self.filename) as dstore:
            for start, stop in self.slices:
                poes_df = dstore.read_df('_poes', slc=slice(start, stop))
                for sid, df in poes_df.groupby('sid'):
                    try:
                        array = self._pmap[sid].array
                    except KeyError:
                        array = numpy.zeros((self.L, G))
                        self._pmap[sid] = probability_map.ProbabilityCurve(
                            array)
                    array[df.lid, df.gid] = df.poe
        return self._pmap

    # used in risk calculations where there is a single site per getter
    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: a probability curve of shape (L, R) for the given site
        """
        self.init()
        if not self.sids:
            # this happens when the poes are all zeros, as in
            # classical_risk/case_3 for the first site
            return probability_map.ProbabilityCurve(
                numpy.zeros((self.L, self.num_rlzs)))
        return self.get_pcurve(self.sids[0])

    def get_pcurve(self, sid):  # used in classical
        """
        :returns: a ProbabilityCurve of shape L, R
        """
        pmap = self.init()
        pc0 = probability_map.ProbabilityCurve(
            numpy.zeros((self.L, self.num_rlzs)))
        if sid not in pmap:  # no hazard for sid
            return pc0
        for g, trs in enumerate(self.trt_rlzs):
            probability_map.combine_probs(
                pc0.array, pmap[sid].array[:, g], trs % TWO24)
        return pc0

    def get_mean(self):
        """
        Compute the mean curve as a ProbabilityMap

        :param grp:
            if not None must be a string of the form "grp-XX"; in that case
            returns the mean considering only the contribution for group XX
        """
        self.init()
        if len(self.weights) == 1:  # one realization
            # the standard deviation is zero
            pmap = self.get(0)
            for sid, pcurve in pmap.items():
                array = numpy.zeros(pcurve.array.shape)
                array[:, 0] = pcurve.array[:, 0]
                pcurve.array = array
            return pmap
        L = self.imtls.size
        pmap = probability_map.ProbabilityMap(self.sids, L, 1)
        for sid in self.sids:
            pmap[sid] = build_stat_curve(
                self.get_pcurve(sid),
                self.imtls, stats.mean_curve, self.weights)
        return pmap


def get_rupture_getters(dstore, ct=0, srcfilter=None):
    """
    :param dstore: a :class:`openquake.commonlib.datastore.DataStore`
    :param ct: number of concurrent tasks
    :returns: a list of RuptureGetters
    """
    full_lt = dstore['full_lt'].init()
    rup_array = dstore['ruptures'][:]
    if len(rup_array) == 0:
        raise NotFound('There are no ruptures in %s' % dstore)
    proxies = [RuptureProxy(rec) for rec in rup_array]
    rup_array['e0'][1:] = rup_array['n_occ'].cumsum()[:-1]
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
    D, R, C = array3RC.shape
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
    idx = numpy.searchsorted(rups['id'], rup_id)
    if idx == len(rups):
        raise ValueError(f"Missing {rup_id=}")
    rec = rups[idx]
    if rec['id'] != rup_id:
        raise ValueError(f"Missing {rup_id=}")
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
