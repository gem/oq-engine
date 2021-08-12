# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2021 GEM Foundation
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

import logging
import operator
import numpy
import pandas
from openquake.baselib import hdf5, general, performance, parallel
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.hazardlib import probability_map, stats
from openquake.hazardlib.calc import filters, gmf
from openquake.hazardlib.source.rupture import (
    BaseRupture, RuptureProxy, to_arrays)
from openquake.risklib.riskinput import rsi2str
from openquake.commonlib import calc, datastore

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
by_taxonomy = operator.attrgetter('taxonomy')
code2cls = BaseRupture.init()
weight = operator.attrgetter('weight')


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

    @property
    def imts(self):
        return list(self.imtls)

    @property
    def L(self):
        return self.imtls.size

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
        dset = dstore['_poes']  # GNL
        G, N, L = dset.shape
        self._pmap = probability_map.ProbabilityMap.build(L, G, self.sids)
        data = dset[:, self.sids, :]  # shape (G, N, L)
        for i, sid in enumerate(self.sids):
            self._pmap[sid].array = data[:, i, :].T  # shape (L, G)
        self.nbytes = self._pmap.nbytes
        dstore.close()
        return self._pmap

    # used in risk calculation where there is a single site per getter
    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: a probability curve of shape (L, R) for the given site
        """
        return self.get_pcurve(self.sids[0])

    def get_pcurve(self, sid):  # used in classical
        """
        :returns: a ProbabilityCurve of shape L, R
        """
        pmap = self.init()
        pc0 = probability_map.ProbabilityCurve(
            numpy.zeros((self.L, self.num_rlzs)))
        try:
            pc0.combine(pmap[sid], self.rlzs_by_g)
        except KeyError:  # no hazard for sid
            pass
        return pc0

    def get_hcurves(self, pmap, rlzs_by_gsim):  # used in in disagg_by_src
        """
        :param pmap: a ProbabilityMap
        :param rlzs_by_gsim: a dictionary gsim -> rlz IDs
        :returns: an array of PoEs of shape (N, R, M, L)
        """
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
        L = self.imtls.size
        pmap = probability_map.ProbabilityMap.build(L, 1, self.sids)
        for sid in self.sids:
            pmap[sid] = build_stat_curve(
                self.get_pcurve(sid),
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
        :returns: the underlying DataFrame
        """
        # the order in which the gmfs are stored is random since it depends
        # on which hazard task ends first; here we reorder
        # the gmfs by event ID for reproducibility
        return self.df.sort_values('eid')


# used in scenario_damage
class ZeroGetter(GmfDataGetter):
    """
    An object with an .init() and .get_hazard() method
    """
    def __init__(self, sid, rlzs, R, gmvcolumns):
        nr = len(rlzs)
        self.sids = [sid]
        self.df = pandas.DataFrame({
            'sid': [sid] * nr, 'rlz': rlzs, 'eid': numpy.arange(nr)})
        for col in gmvcolumns:
            self.df[col] = numpy.zeros(nr, dtype=F32)
        self.num_rlzs = R


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
        md = (filters.MagDepDistance(oqparam.maximum_distance)
              if isinstance(oqparam.maximum_distance, dict)
              else oqparam.maximum_distance)
        param = {'imtls': oqparam.imtls, 'maximum_distance': md,
                 'minimum_distance': oqparam.minimum_distance,
                 'truncation_level': oqparam.truncation_level}
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
                    computer = gmf.GmfComputer(
                        ebr, sitecol, self.cmaker, self.correl_model,
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
        :returns: a DataFrame with fields eid, sid, gmv_...
        """
        alldata = general.AccumDict(accum=[])
        self.sig_eps = []
        self.times = []  # rup_id, nsites, dt
        for computer in self.gen_computers(mon):
            data, dt = computer.compute_all(
                self.min_iml, self.rlzs_by_gsim, self.sig_eps)
            self.times.append((computer.ebrupture.id, len(computer.sids), dt))
            for key in data:
                alldata[key].extend(data[key])
        for key, val in sorted(alldata.items()):
            if key in 'eid sid rlz':
                alldata[key] = U32(alldata[key])
            else:
                alldata[key] = F32(alldata[key])
        return pandas.DataFrame(alldata)

    # not called by the engine
    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: DataFrame
        """
        return self.get_gmfdata()

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
            if len(gmfdata) == 0:
                return dict(gmfdata=(), hcurves=hcurves)
            for (sid, rlz), df in gmfdata.groupby(['sid', 'rlz']):
                with hc_mon:
                    poes = calc.gmvs_to_poes(
                        df, oq.imtls, oq.ses_per_logic_tree_path)
                    for m, imt in enumerate(oq.imtls):
                        hcurves[rsi2str(rlz, sid, imt)] = poes[m]
        if not oq.ground_motion_fields:
            return dict(gmfdata=(), hcurves=hcurves)
        if not oq.hazard_curves_from_gmfs:
            gmfdata = self.get_gmfdata(mon)
        if len(gmfdata) == 0:
            return dict(gmfdata=[])
        times = numpy.array([tup + (monitor.task_no,) for tup in self.times],
                            time_dt)
        times.sort(order='rup_id')
        res = dict(gmfdata=strip_zeros(gmfdata), hcurves=hcurves, times=times,
                   sig_eps=numpy.array(self.sig_eps, self.sig_eps_dt))
        return res


def strip_zeros(gmf_df):
    # remove the rows with all zero values
    df = gmf_df[gmf_df.columns[3:]]  # strip eid, sid, rlz
    ok = df.to_numpy().sum(axis=1) > 0
    return gmf_df[ok]


def weight_ruptures(rup_array, srcfilter, trt_by, scenario):
    """
    :param rup_array: an array of ruptures
    :param srcfilter: a SourceFilter
    :param trt_by: a function trt_smr -> TRT
    :param scenario: True for ruptures of kind scenario
    :returns: list of RuptureProxies
    """
    proxies = []
    for rec in rup_array:
        proxy = RuptureProxy(rec, scenario=scenario)
        sids = srcfilter.close_sids(proxy.rec, trt_by(rec['trt_smr']))
        proxy.nsites = len(sids)
        proxies.append(proxy)
    return proxies


def get_rupture_getters(dstore, ct=0, slc=slice(None), srcfilter=None):
    """
    :param dstore: a :class:`openquake.commonlib.datastore.DataStore`
    :param ct: number of concurrent tasks
    :returns: a list of RuptureGetters
    """
    full_lt = dstore['full_lt']
    rlzs_by_gsim = full_lt.get_rlzs_by_gsim()
    rup_array = dstore['ruptures'][slc]
    if len(rup_array) == 0:
        raise NotFound('There are no ruptures in %s' % dstore)
    rup_array.sort(order='trt_smr')  # avoid generating too many tasks
    scenario = 'scenario' in dstore['oqparam'].calculation_mode
    if srcfilter is None:
        proxies = [RuptureProxy(rec, None, scenario) for rec in rup_array]
    elif len(rup_array) <= 1000:  # do not parallelize
        proxies = weight_ruptures(
            rup_array, srcfilter, full_lt.trt_by, scenario)
    else:  # parallelize the weighting of the ruptures
        proxies = parallel.Starmap.apply(
            weight_ruptures, (rup_array, srcfilter, full_lt.trt_by, scenario),
            concurrent_tasks=ct, progress=logging.debug
        ).reduce(acc=[])
    maxweight = sum(proxy.weight for proxy in proxies) / (ct or 1)
    rgetters = []
    for block in general.block_splitter(
            proxies, maxweight, operator.attrgetter('weight'),
            key=operator.itemgetter('trt_smr')):
        trt_smr = block[0]['trt_smr']
        if len(rlzs_by_gsim) == 1:
            [rbg] = rlzs_by_gsim.values()
        else:
            rbg = rlzs_by_gsim[trt_smr]
        rg = RuptureGetter(block, dstore.filename, trt_smr,
                           full_lt.trt_by(trt_smr), rbg)
        rgetters.append(rg)
    return rgetters


# NB: amplification is missing
def get_gmfgetter(dstore, rup_id):
    """
    :returns: GmfGetter associated to the given rupture
    """
    oq = dstore['oqparam']
    srcfilter = filters.SourceFilter(
        dstore['sitecol'], oq.maximum_distance)
    for rgetter in get_rupture_getters(dstore, slc=slice(rup_id, rup_id+1)):
        gg = GmfGetter(rgetter, srcfilter, oq)
        break
    return gg


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
        self.weight = sum(proxy.weight for proxy in proxies)
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
                proxy.nsites = len(sids)
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
