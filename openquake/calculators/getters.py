# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2020 GEM Foundation
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
import unittest.mock as mock
import numpy
from openquake.baselib import hdf5, datastore, general, performance
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.hazardlib import calc, probability_map, stats
from openquake.hazardlib.source.rupture import (
    EBRupture, BaseRupture, events_dt, RuptureProxy)
from openquake.risklib.riskinput import rsi2str
from openquake.commonlib.calc import gmvs_to_poes

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
by_taxonomy = operator.attrgetter('taxonomy')
code2cls = BaseRupture.init()
weight = operator.attrgetter('weight')


def build_stat_curve(poes, imtls, stat, weights):
    """
    Build statistics by taking into account IMT-dependent weights
    """
    assert len(poes) == len(weights), (len(poes), len(weights))
    L = len(imtls.array)
    array = numpy.zeros((L, 1))
    if isinstance(weights, list):  # IMT-dependent weights
        # this is slower since the arrays are shorter
        for imt in imtls:
            slc = imtls(imt)
            ws = [w[imt] for w in weights]
            if sum(ws) == 0:  # expect no data for this IMT
                continue
            array[slc] = stat(poes[:, slc], ws)
    else:
        array = stat(poes, weights)
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


def get_slice_by_g(rlzs_by_gsim_list):
    """
    :returns: a list of slices
    """
    slices = []
    start = 0
    for rlzs_by_gsim in rlzs_by_gsim_list:
        ngsims = len(rlzs_by_gsim)
        slices.append(slice(start, start + ngsims))
        start += ngsims
    return slices


class PmapGetter(object):
    """
    Read hazard curves from the datastore for all realizations or for a
    specific realization.

    :param dstore: a DataStore instance or file system path to it
    :param sids: the subset of sites to consider (if None, all sites)
    """
    def __init__(self, dstore, weights, sids, imtls=(), poes=()):
        self.filename = dstore if isinstance(dstore, str) else dstore.filename
        if len(weights[0].dic) == 1:  # no weights by IMT
            self.weights = numpy.array([w['weight'] for w in weights])
        else:
            self.weights = weights
        self.sids = sids
        self.imtls = imtls
        self.poes = poes
        self.num_rlzs = len(weights)
        self.eids = None
        self.sids = sids

    @property
    def imts(self):
        return list(self.imtls)

    @property
    def L(self):
        return len(self.imtls.array)

    @property
    def N(self):
        return len(self.sids)

    @property
    def M(self):
        return len(self.imtls)

    @property
    def R(self):
        return len(self.weights)

    def init(self):
        """
        Read the poes and set the .data attribute with the hazard curves
        """
        if hasattr(self, '_pmap'):  # already initialized
            return self._pmap
        dstore = hdf5.File(self.filename, 'r')
        self.rlzs_by_g = dstore['rlzs_by_g'][()]

        # populate _pmap
        dset = dstore['_poes']  # NLG_
        L, G = dset.shape[1:]
        self._pmap = probability_map.ProbabilityMap.build(L, G, self.sids)
        for sid, array in zip(self.sids, dset[list(self.sids)]):
            self._pmap[sid].array = array
        self.nbytes = self._pmap.nbytes
        dstore.close()
        return self._pmap

    # used in risk calculation where there is a single site per getter
    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: R probability curves for the given site
        """
        return self.get_pcurves(self.sids[0])

    def get_pcurves(self, sid):  # used in classical
        """
        :returns: a list of R probability curves with shape L
        """
        pmap = self.init()
        pcurves = [probability_map.ProbabilityCurve(numpy.zeros((self.L, 1)))
                   for _ in range(self.num_rlzs)]
        try:
            pc = pmap[sid]
        except KeyError:  # no hazard for sid
            return pcurves
        for g, rlzis in enumerate(self.rlzs_by_g):
            c = probability_map.ProbabilityCurve(pc.array[:, [g]])
            for rlzi in rlzis:
                pcurves[rlzi] |= c
        return pcurves

    def get_hcurves(self, pmap, rlzs_by_gsim):  # in disagg_by_src
        """
        :param pmap_by_et_id: a dictionary of ProbabilityMaps by group ID
        :returns: an array of PoEs of shape (N, R, M, L)
        """
        self.init()
        res = numpy.zeros((self.N, self.R, self.L))
        for sid, pc in pmap.items():
            for gsim_idx, rlzis in enumerate(rlzs_by_gsim.values()):
                poes = pc.array[:, gsim_idx]
                for rlz in rlzis:
                    res[sid, rlz] = general.agg_probs(res[sid, rlz], poes)
        return res.reshape(self.N, self.R, self.M, -1)

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
        L = len(self.imtls.array)
        pmap = probability_map.ProbabilityMap.build(L, 1, self.sids)
        for sid in self.sids:
            pmap[sid] = build_stat_curve(
                numpy.array([pc.array for pc in self.get_pcurves(sid)]),
                self.imtls, stats.mean_curve, self.weights)
        return pmap


class GmfDataGetter(object):
    """
    An object with an .init() and .get_hazard() method
    """
    def __init__(self, sid, df, num_events, num_rlzs):
        self.sids = [sid]
        self.df = df
        self.num_rlzs = num_rlzs  # used in event_based_risk
        # now some attributes set for API compatibility with the GmfGetter
        # number of ground motion fields
        # dictionary rlzi -> array(imts, events, nbytes)
        self.E = num_events

    def init(self):
        pass

    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: an dict rlzi -> datadict
        """
        return dict(list(self.df.groupby('rlzs')))


class ZeroGetter(object):
    """
    An object with an .init() and .get_hazard() method
    """
    def __init__(self, sid, num_rlzs):
        self.sids = [sid]
        self.num_rlzs = num_rlzs

    def init(self):
        pass

    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: an dict rlzi -> 0
        """
        return {rlzi: 0 for rlzi in range(self.num_rlzs)}


time_dt = numpy.dtype(
    [('rup_id', U32), ('nsites', U16), ('time', F32), ('task_no', U16)])


class GmfGetter(object):
    """
    An hazard getter with methods .get_gmfdata and .get_hazard returning
    ground motion values.
    """
    def __init__(self, rupgetter, srcfilter, oqparam, amplifier=None,
                 sec_perils=()):
        self.rlzs_by_gsim = rupgetter.rlzs_by_gsim
        self.rupgetter = rupgetter
        self.srcfilter = srcfilter
        self.sitecol = srcfilter.sitecol.complete
        self.oqparam = oqparam
        self.amplifier = amplifier
        self.sec_perils = sec_perils
        self.min_iml = oqparam.min_iml
        self.N = len(self.sitecol)
        self.num_rlzs = sum(len(rlzs) for rlzs in self.rlzs_by_gsim.values())
        self.sig_eps_dt = sig_eps_dt(oqparam.imtls)
        md = (calc.filters.MagDepDistance(oqparam.maximum_distance)
              if isinstance(oqparam.maximum_distance, dict)
              else oqparam.maximum_distance)
        param = {'filter_distance': oqparam.filter_distance,
                 'imtls': oqparam.imtls, 'maximum_distance': md}
        self.cmaker = ContextMaker(
            rupgetter.trt, rupgetter.rlzs_by_gsim, param)
        self.correl_model = oqparam.correl_model

    def gen_computers(self, mon):
        """
        Yield a GmfComputer instance for each non-discarded rupture
        """
        trt = self.rupgetter.trt
        with mon:
            proxies = self.rupgetter.get_proxies()
        for proxy in proxies:
            with mon:
                ebr = proxy.to_ebr(trt)
                sids = self.srcfilter.close_sids(proxy, trt)
                if len(sids) == 0:  # filtered away
                    continue
                sitecol = self.sitecol.filtered(sids)
                try:
                    computer = calc.gmf.GmfComputer(
                        ebr, sitecol, self.cmaker,
                        self.oqparam.truncation_level, self.correl_model,
                        self.amplifier, self.sec_perils)
                except FarAwayRupture:
                    continue
                # due to numeric errors ruptures within the maximum_distance
                # when written, can be outside when read; I found a case with
                # a distance of 99.9996936 km over a maximum distance of 100 km
            yield computer

    @property
    def sids(self):
        return self.sitecol.sids

    @property
    def imtls(self):
        return self.oqparam.imtls

    @property
    def imts(self):
        return list(self.oqparam.imtls)

    def get_gmfdata(self, mon=performance.Monitor()):
        """
        :returns: an array of the dtype (sid, eid, gmv)
        """
        alldata = []
        self.sig_eps = []
        self.times = []  # rup_id, nsites, dt
        for computer in self.gen_computers(mon):
            data, dt = computer.compute_all(
                self.min_iml, self.rlzs_by_gsim, self.sig_eps)
            self.times.append((computer.ebrupture.id, len(computer.sids), dt))
            alldata.append(data)
        if not alldata:
            return []
        return numpy.concatenate(alldata)

    # not called by the engine
    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: a dictionary rlzi -> array
        """
        data = self.get_gmfdata()
        return general.group_array(data, 'rlz')

    def get_hazard_by_sid(self, data=None):
        """
        :param data: if given, an iterator of records of dtype gmf_dt
        :returns: sid -> records
        """
        if data is None:
            data = self.get_gmfdata()
        if len(data) == 0:
            return {}
        return general.group_array(data, 'sid')

    def compute_gmfs_curves(self, monitor):
        """
        :returns: a dict with keys gmfdata, hcurves
        """
        oq = self.oqparam
        mon = monitor('getting ruptures', measuremem=True)
        hcurves = {}  # key -> poes
        if oq.hazard_curves_from_gmfs:
            hc_mon = monitor('building hazard curves', measuremem=False)
            gmfdata = self.get_gmfdata(mon)  # returned later
            hazard = self.get_hazard_by_sid(data=gmfdata)
            for sid, hazardr in hazard.items():
                dic = general.group_array(hazardr, 'rlz')
                for rlzi, array in dic.items():
                    with hc_mon:
                        poes = gmvs_to_poes(
                            array['gmv'].T, oq.imtls,
                            oq.ses_per_logic_tree_path)
                        for m, imt in enumerate(oq.imtls):
                            hcurves[rsi2str(rlzi, sid, imt)] = poes[m]
        if not oq.ground_motion_fields:
            return dict(gmfdata=(), hcurves=hcurves)
        if not oq.hazard_curves_from_gmfs:
            gmfdata = self.get_gmfdata(mon)
        if len(gmfdata) == 0:
            return dict(gmfdata=[])
        times = numpy.array([tup + (monitor.task_no,) for tup in self.times],
                            time_dt)
        times.sort(order='rup_id')
        res = dict(gmfdata=gmfdata, hcurves=hcurves, times=times,
                   sig_eps=numpy.array(self.sig_eps, self.sig_eps_dt))
        return res


def gen_rupture_getters(dstore, ct=0, slc=slice(None)):
    """
    :param dstore: a :class:`openquake.baselib.datastore.DataStore`
    :param ct: number of concurrent tasks
    :yields: RuptureGetters
    """
    full_lt = dstore['full_lt']
    trt_by_et = full_lt.trt_by_et
    rlzs_by_gsim = full_lt.get_rlzs_by_gsim_grp()
    rup_array = dstore['ruptures'][slc]
    rup_array.sort(order='et_id')  # avoid generating too many tasks
    maxweight = rup_array['n_occ'].sum() / (ct or 1)
    for block in general.block_splitter(
            rup_array, maxweight, operator.itemgetter('n_occ'),
            key=operator.itemgetter('et_id')):
        et_id = block[0]['et_id']
        trt = trt_by_et[et_id]
        proxies = [RuptureProxy(rec) for rec in block]
        yield RuptureGetter(proxies, dstore.filename, et_id,
                            trt, rlzs_by_gsim[et_id])


# NB: amplification is missing
def get_gmfgetter(dstore, rup_id):
    """
    :returns: GmfGetter associated to the given rupture
    """
    oq = dstore['oqparam']
    srcfilter = calc.filters.SourceFilter(
        dstore['sitecol'], oq.maximum_distance)
    for rgetter in gen_rupture_getters(dstore, slc=slice(rup_id, rup_id+1)):
        gg = GmfGetter(rgetter, srcfilter, oq)
        break
    return gg


def get_ebruptures(dstore):
    """
    Extract EBRuptures from the datastore
    """
    ebrs = []
    for rgetter in gen_rupture_getters(dstore):
        for proxy in rgetter.get_proxies():
            ebrs.append(proxy.to_ebr(rgetter.trt))
    return ebrs


def get_eid_rlz(proxies, rlzs_by_gsim):
    """
    :returns: a composite array with the associations eid->rlz
    """
    eid_rlz = []
    for rup in proxies:
        ebr = EBRupture(mock.Mock(rup_id=rup['serial']), rup['source_id'],
                        rup['et_id'], rup['n_occ'])
        for rlz_id, eids in ebr.get_eids_by_rlz(rlzs_by_gsim).items():
            for eid in eids:
                eid_rlz.append((eid + rup['e0'], rup['id'], rlz_id))
    return numpy.array(eid_rlz, events_dt)


# this is never called directly; gen_rupture_getters is used instead
class RuptureGetter(object):
    """
    :param proxies:
        a list of RuptureProxies
    :param filename:
        path to the HDF5 file containing a 'rupgeoms' dataset
    :param et_id:
        source group index
    :param trt:
        tectonic region type string
    :param rlzs_by_gsim:
        dictionary gsim -> rlzs for the group
    """
    def __init__(self, proxies, filename, et_id, trt, rlzs_by_gsim):
        self.proxies = proxies
        self.weight = sum(proxy.weight for proxy in proxies)
        self.filename = filename
        self.et_id = et_id
        self.trt = trt
        self.rlzs_by_gsim = rlzs_by_gsim
        self.num_events = sum(int(proxy['n_occ']) for proxy in proxies)

    @property
    def num_ruptures(self):
        return len(self.proxies)

    def get_rupdict(self):
        """
        :returns: a dictionary with the parameters of the rupture
        """
        assert len(self.proxies) == 1, 'Please specify a slice of length 1'
        dic = {'trt': self.trt}
        with datastore.read(self.filename) as dstore:
            rupgeoms = dstore['rupgeoms']
            rec = self.proxies[0].rec
            geom = rupgeoms[rec['id']].reshape(
                rec['s1'], rec['s2'], 3).transpose(2, 0, 1)
            dic['lons'] = geom[0]
            dic['lats'] = geom[1]
            dic['deps'] = geom[2]
            rupclass, surclass = code2cls[rec['code']]
            dic['rupture_class'] = rupclass.__name__
            dic['surface_class'] = surclass.__name__
            dic['hypo'] = rec['hypo']
            dic['occurrence_rate'] = rec['occurrence_rate']
            dic['et_id'] = rec['et_id']
            dic['n_occ'] = rec['n_occ']
            dic['serial'] = rec['serial']
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

    def split(self, srcfilter, maxw):
        """
        :yields: RuptureProxies with weight < maxw
        """
        proxies = []
        for proxy in self.proxies:
            sids = srcfilter.close_sids(proxy.rec, self.trt)
            if len(sids):
                proxies.append(RuptureProxy(proxy.rec, len(sids)))
        for block in general.block_splitter(proxies, maxw, weight):
            yield RuptureGetter(block, self.filename, self.et_id, self.trt,
                                self.rlzs_by_gsim)

    def __len__(self):
        return len(self.proxies)

    def __repr__(self):
        wei = ' [w=%d]' % self.weight if hasattr(self, 'weight') else ''
        return '<%s et_id=%d, %d rupture(s)%s>' % (
            self.__class__.__name__, self.et_id, len(self), wei)
