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
from openquake.baselib.python3compat import decode
from openquake.hazardlib import probability_map, stats
from openquake.hazardlib.source.rupture import (
    BaseRupture, RuptureProxy, to_arrays)
from openquake.commonlib import datastore

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
by_taxonomy = operator.attrgetter('taxonomy')
code2cls = BaseRupture.init()
weight = operator.itemgetter('n_occ')


class NotFound(Exception):
    pass


def build_stat_curve(pcurve, imtls, stat, weights):
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
            array[slc, 0] = stat(poes[:, slc], ws)
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
        self.full_lt = dstore['full_lt']
        self.sslt = self.full_lt.source_model_lt.decompose()
        self.source_info = dstore['source_info'][:]
        self.disagg_by_grp = dstore['disagg_by_grp'][:]
        gsim_lt = self.full_lt.gsim_lt
        self.bysrc = {}  # src_id -> (start, gsims, weights)
        for row in self.source_info:
            dis = self.disagg_by_grp[row['grp_id']]
            trt = decode(dis['grp_trt'])
            weights = gsim_lt.get_weights(trt)
            self.bysrc[decode(row['source_id'])] = (
                dis['grp_start'], gsim_lt.values[trt], weights)

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
    def __init__(self, dstore, weights, slices, imtls=(), poes=(), ntasks=1):
        self.filename = dstore if isinstance(dstore, str) else dstore.filename
        if len(weights[0].dic) == 1:  # no weights by IMT
            self.weights = numpy.array([w['weight'] for w in weights])
        else:
            self.weights = weights
        self.imtls = imtls
        self.poes = poes
        self.ntasks = ntasks
        self.num_rlzs = len(weights)
        self.eids = None
        self.rlzs_by_g = dstore['rlzs_by_g'][()]
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
        G = len(self.rlzs_by_g)
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
        for g, rlzs in enumerate(self.rlzs_by_g):
            probability_map.combine_probs(
                pc0.array, pmap[sid].array[:, g], rlzs)
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


time_dt = numpy.dtype(
    [('rup_id', U32), ('nsites', U16), ('time', F32), ('task_no', U16)])


def get_rupture_getters(dstore, ct=0, slc=slice(None), srcfilter=None):
    """
    :param dstore: a :class:`openquake.commonlib.datastore.DataStore`
    :param ct: number of concurrent tasks
    :returns: a list of RuptureGetters
    """
    full_lt = dstore['full_lt']
    rup_array = dstore['ruptures'][slc]
    if len(rup_array) == 0:
        raise NotFound('There are no ruptures in %s' % dstore)
    rup_array.sort(order=['trt_smr', 'n_occ'])
    scenario = 'scenario' in dstore['oqparam'].calculation_mode
    proxies = [RuptureProxy(rec, scenario) for rec in rup_array]
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

    def get_rupdict(self):  # used in extract_event_info and show rupture
        """
        :returns: a dictionary with the parameters of the rupture
        """
        assert len(self.proxies) == 1, 'Please specify a slice of length 1'
        dic = {'trt': self.trt}
        with datastore.read(self.filename) as dstore:
            rupgeoms = dstore['rupgeoms']
            rec = self.proxies[0].rec
            geom = rupgeoms[rec['id']]
            arrays = to_arrays(geom)  # one array per surface
            for a, array in enumerate(arrays):
                dic['surface_%d' % a] = multiline(array)
            rupclass, surclass = code2cls[rec['code']]
            dic['rupture_class'] = rupclass.__name__
            dic['surface_class'] = surclass.__name__
            dic['hypo'] = rec['hypo']
            dic['occurrence_rate'] = rec['occurrence_rate']
            dic['trt_smr'] = rec['trt_smr']
            dic['n_occ'] = rec['n_occ']
            dic['seed'] = rec['seed']
            dic['mag'] = rec['mag']
            dic['srcid'] = rec['source_id']
        return dic

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
