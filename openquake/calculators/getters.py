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
import collections
import itertools
import operator
import logging
import unittest.mock as mock
import numpy
from openquake.baselib import hdf5, datastore, general
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


class PmapGetter(object):
    """
    Read hazard curves from the datastore for all realizations or for a
    specific realization.

    :param dstore: a DataStore instance or file system path to it
    :param sids: the subset of sites to consider (if None, all sites)
    """
    def __init__(self, dstore, weights, sids=None, poes=()):
        self.filename = dstore if isinstance(dstore, str) else dstore.filename
        self.sids = sids
        if len(weights[0].dic) == 1:  # no weights by IMT
            self.weights = numpy.array([w['weight'] for w in weights])
        else:
            self.weights = weights
        self.poes = poes
        self.num_rlzs = len(weights)
        self.eids = None
        self.nbytes = 0
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
        if hasattr(self, '_pmap_by_grp'):  # already initialized
            return self._pmap_by_grp
        dstore = hdf5.File(self.filename, 'r')
        if self.sids is None:
            self.sids = dstore['sitecol'].sids
        oq = dstore['oqparam']
        self.imtls = oq.imtls
        self.poes = self.poes or oq.poes
        if 'rlzs_by_grp' in dstore:
            self.rlzs_by_grp = {grp: dset[()] for grp, dset in
                                dstore['rlzs_by_grp'].items()}
        else:
            self.rlzs_by_grp = dstore['full_lt'].get_rlzs_by_grp()

        # populate _pmap_by_grp
        self._pmap_by_grp = {}
        if 'poes' in dstore:
            # build probability maps restricted to the given sids
            ok_sids = set(self.sids)
            for grp, dset in dstore['poes'].items():
                ds = dset['array']
                L, G = ds.shape[1:]
                pmap = probability_map.ProbabilityMap(L, G)
                for idx, sid in enumerate(dset['sids'][()]):
                    if sid in ok_sids:
                        pmap[sid] = probability_map.ProbabilityCurve(ds[idx])
                self._pmap_by_grp[grp] = pmap
                self.nbytes += pmap.nbytes
        dstore.close()
        return self._pmap_by_grp

    # used in risk calculation where there is a single site per getter
    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: R probability curves for the given site
        """
        return self.get_pcurves(self.sids[0])

    def get(self, rlzi, grp=None):
        """
        :param rlzi: a realization index
        :param grp: None (all groups) or a string of the form "grp-XX"
        :returns: the hazard curves for the given realization
        """
        self.init()
        assert self.sids is not None
        pmap = probability_map.ProbabilityMap(len(self.imtls.array), 1)
        grps = [grp] if grp is not None else sorted(self._pmap_by_grp)
        for grp in grps:
            for gsim_idx, rlzis in enumerate(self.rlzs_by_grp[grp]):
                for r in rlzis:
                    if r == rlzi:
                        pmap |= self._pmap_by_grp[grp].extract(gsim_idx)
                        break
        return pmap

    def get_pcurves(self, sid, pmap_by_grp=()):  # used in classical
        """
        :returns: a list of R probability curves with shape L
        """
        if not pmap_by_grp:
            pmap_by_grp = self.init()
        pcurves = [probability_map.ProbabilityCurve(numpy.zeros((self.L, 1)))
                   for _ in range(self.num_rlzs)]
        for grp, pmap in pmap_by_grp.items():
            try:
                pc = pmap[sid]
            except KeyError:  # no hazard for sid
                continue
            for gsim_idx, rlzis in enumerate(self.rlzs_by_grp[grp]):
                c = probability_map.ProbabilityCurve(pc.array[:, [gsim_idx]])
                for rlzi in rlzis:
                    pcurves[rlzi] |= c
        return pcurves

    def get_hcurves(self, pmap_by_grp):
        """
        :param pmap_by_grp: a dictionary of ProbabilityMaps by group
        :returns: an array of PoEs of shape (N, R, M, L)
        """
        self.init()
        res = numpy.zeros((self.N, self.R, self.L))
        for grp, pmap in pmap_by_grp.items():
            for sid, pc in pmap.items():
                for gsim_idx, rlzis in enumerate(self.rlzs_by_grp[grp]):
                    poes = pc.array[:, gsim_idx]
                    for rlz in rlzis:
                        res[sid, rlz] = general.agg_probs(res[sid, rlz], poes)
        return res.reshape(self.N, self.R, self.M, -1)

    def items(self, kind=''):
        """
        Extract probability maps from the datastore, possibly generating
        on the fly the ones corresponding to the individual realizations.
        Yields pairs (tag, pmap).

        :param kind:
            the kind of PoEs to extract; if not given, returns the realization
            if there is only one or the statistics otherwise.
        """
        num_rlzs = len(self.weights)
        if not kind or kind == 'all':  # use default
            if 'hcurves' in self.dstore:
                for k in sorted(self.dstore['hcurves']):
                    yield k, self.dstore['hcurves/' + k][()]
            elif num_rlzs == 1:
                yield 'mean', self.get(0)
            return
        if 'poes' in self.dstore and kind in ('rlzs', 'all'):
            for rlzi in range(num_rlzs):
                hcurves = self.get(rlzi)
                yield 'rlz-%03d' % rlzi, hcurves
        elif 'poes' in self.dstore and kind.startswith('rlz-'):
            yield kind, self.get(int(kind[4:]))
        if 'hcurves' in self.dstore and kind == 'stats':
            for k in sorted(self.dstore['hcurves']):
                if not k.startswith('rlz'):
                    yield k, self.dstore['hcurves/' + k][()]

    def get_mean(self, grp=None):
        """
        Compute the mean curve as a ProbabilityMap

        :param grp:
            if not None must be a string of the form "grp-XX"; in that case
            returns the mean considering only the contribution for group XX
        """
        self.init()
        if len(self.weights) == 1:  # one realization
            # the standard deviation is zero
            pmap = self.get(0, grp)
            for sid, pcurve in pmap.items():
                array = numpy.zeros(pcurve.array.shape)
                array[:, 0] = pcurve.array[:, 0]
                pcurve.array = array
            return pmap
        elif grp:
            raise NotImplementedError('multiple realizations')
        L = len(self.imtls.array)
        pmap = probability_map.ProbabilityMap.build(L, 1, self.sids)
        for sid in self.sids:
            pmap[sid] = build_stat_curve(
                numpy.array([pc.array for pc in self.get_pcurves(sid)]),
                self.imtls, stats.mean_curve, self.weights)
        return pmap


class GmfDataGetter(collections.abc.Mapping):
    """
    A dictionary-like object {sid: dictionary by realization index}
    """
    def __init__(self, dstore, sids, rlzs, num_rlzs):
        self.dstore = dstore
        self.sids = sids
        self.rlzs = rlzs
        self.num_rlzs = num_rlzs
        assert len(sids) == 1, sids

    def init(self):
        if hasattr(self, 'data'):  # already initialized
            return
        self.dstore.open('r')  # if not already open
        self.data = self[self.sids[0]]
        if not self.data:  # no GMVs, return 0, counted in no_damage
            self.data = {rlzi: 0 for rlzi in range(self.num_rlzs)}
        # now some attributes set for API compatibility with the GmfGetter
        # number of ground motion fields
        # dictionary rlzi -> array(imts, events, nbytes)
        self.E = len(self.rlzs)
        del self.rlzs

    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: an dict rlzi -> datadict
        """
        return self.data

    def __getitem__(self, sid):
        dset = self.dstore['gmf_data/data']
        idxs = self.dstore['gmf_data/indices'][sid]
        if idxs.dtype.name == 'uint32':  # scenario
            idxs = [idxs]
        elif not idxs.dtype.names:  # engine >= 3.2
            idxs = zip(*idxs)
        data = [dset[start:stop] for start, stop in idxs]
        if len(data) == 0:  # site ID with no data
            return {}
        return group_by_rlz(numpy.concatenate(data), self.rlzs)

    def __iter__(self):
        return iter(self.sids)

    def __len__(self):
        return len(self.sids)


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
        trt, samples = self.rupgetter.trt, self.rupgetter.samples
        with mon:
            proxies = self.rupgetter.get_proxies()
        for proxy in proxies:
            with mon:
                ebr = proxy.to_ebr(trt, samples)
                sids = self.srcfilter.close_sids(proxy, trt)
                sitecol = self.sitecol.filtered(sids)
                try:
                    computer = calc.gmf.GmfComputer(
                        ebr, sitecol, self.oqparam.imtls, self.cmaker,
                        self.oqparam.truncation_level, self.correl_model,
                        self.amplifier, self.sec_perils)
                    computer.offset = self.rupgetter.offset
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

    def get_gmfdata(self, mon):
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

    def compute_gmfs_curves(self, rlzs, monitor):
        """
        :param rlzs: an array of shapeE
        :returns: a dict with keys gmfdata, indices, hcurves
        """
        oq = self.oqparam
        mon = monitor('getting ruptures', measuremem=True)
        hcurves = {}  # key -> poes
        if oq.hazard_curves_from_gmfs:
            hc_mon = monitor('building hazard curves', measuremem=False)
            gmfdata = self.get_gmfdata(mon)  # returned later
            hazard = self.get_hazard_by_sid(data=gmfdata)
            for sid, hazardr in hazard.items():
                dic = group_by_rlz(hazardr, rlzs)
                for rlzi, array in dic.items():
                    with hc_mon:
                        poes = gmvs_to_poes(
                            array['gmv'].T, oq.imtls,
                            oq.ses_per_logic_tree_path)
                        for m, imt in enumerate(oq.imtls):
                            hcurves[rsi2str(rlzi, sid, imt)] = poes[m]
        if not oq.ground_motion_fields:
            return dict(gmfdata=(), hcurves=hcurves)
        gmfdata = self.get_gmfdata(mon)
        if len(gmfdata) == 0:
            return dict(gmfdata=[])
        indices = []
        gmfdata.sort(order=('sid', 'eid'))
        start = stop = 0
        for sid, rows in itertools.groupby(gmfdata['sid']):
            for row in rows:
                stop += 1
            indices.append((sid, start, stop))
            start = stop
        times = numpy.array([tup + (monitor.task_no,) for tup in self.times],
                            time_dt)
        times.sort(order='rup_id')
        res = dict(gmfdata=gmfdata, hcurves=hcurves, times=times,
                   sig_eps=numpy.array(self.sig_eps, self.sig_eps_dt),
                   indices=numpy.array(indices, (U32, 3)))
        return res


def group_by_rlz(data, rlzs):
    """
    :param data: a composite array of D elements with a field `eid`
    :param rlzs: an array of E >= D elements
    :returns: a dictionary rlzi -> data for each realization
    """
    acc = general.AccumDict(accum=[])
    for rec in data:
        acc[rlzs[rec['eid']]].append(rec)
    return {rlzi: numpy.array(recs) for rlzi, recs in acc.items()}


def gen_rgetters(dstore, slc=slice(None)):
    """
    :yields: unfiltered RuptureGetters
    """
    full_lt = dstore['full_lt']
    trt_by_grp = full_lt.trt_by_grp
    samples = full_lt.get_samples_by_grp()
    rlzs_by_gsim = full_lt.get_rlzs_by_gsim_grp()
    rup_array = dstore['ruptures'][slc]
    nr = len(dstore['ruptures'])
    for grp_id, arr in general.group_array(rup_array, 'grp_id').items():
        if not rlzs_by_gsim.get(grp_id, []):  # the model has no sources
            continue
        for block in general.split_in_blocks(arr, len(arr) / nr):
            rgetter = RuptureGetter(
                [RuptureProxy(rec) for rec in block], dstore.filename, grp_id,
                trt_by_grp[grp_id], samples[grp_id], rlzs_by_gsim[grp_id])
            yield rgetter


def _gen(arr, srcfilter, trt, samples):
    for rec in arr:
        sids = srcfilter.close_sids(rec, trt)
        if len(sids):
            yield RuptureProxy(rec, len(sids), samples)


def gen_rupture_getters(dstore, srcfilter, ct):
    """
    :param dstore: a :class:`openquake.baselib.datastore.DataStore`
    :param srcfilter: a :class:`openquake.hazardlib.calc.filters.SourceFilter`
    :param ct: number of concurrent tasks
    :yields: filtered RuptureGetters
    """
    full_lt = dstore['full_lt']
    trt_by_grp = full_lt.trt_by_grp
    samples = full_lt.get_samples_by_grp()
    rlzs_by_gsim = full_lt.get_rlzs_by_gsim_grp()
    rup_array = dstore['ruptures'][()]
    items = list(general.group_array(rup_array, 'grp_id').items())
    items.sort(key=lambda item: len(item[1]))  # other weights were much worse
    maxweight = None
    while items:
        grp_id, rups = items.pop()  # from the largest group
        if not rlzs_by_gsim[grp_id]:
            # this may happen if a source model has no sources, like
            # in event_based_risk/case_3
            continue
        trt = trt_by_grp[grp_id]
        proxies = list(_gen(rups, srcfilter, trt, samples[grp_id]))
        if len(proxies) == 1:  # split by gsim
            offset = 0
            for gsim, rlzs in rlzs_by_gsim[grp_id].items():
                rgetter = RuptureGetter(
                    proxies, dstore.filename, grp_id,
                    trt, samples[grp_id], {gsim: rlzs})
                rgetter.offset = offset
                offset += rgetter.num_events
                yield rgetter
        else:  # split by block
            if not maxweight:
                maxweight = sum(p.weight for p in proxies) / (ct // 2 or 1)
            nblocks = 0
            for block in general.block_splitter(
                    proxies, maxweight, operator.attrgetter('weight')):
                nblocks += 1
                rgetter = RuptureGetter(
                    block, dstore.filename, grp_id,
                    trt, samples[grp_id], rlzs_by_gsim[grp_id])
                yield rgetter
            logging.info('Sent group %d: %d ruptures -> %d task(s)',
                         grp_id, len(rups), nblocks)


def get_ebruptures(dstore):
    """
    Extract EBRuptures from the datastore
    """
    ebrs = []
    for rgetter in gen_rgetters(dstore):
        for proxy in rgetter.get_proxies():
            ebrs.append(proxy.to_ebr(rgetter.trt, rgetter.samples))
    return ebrs


# this is never called directly; gen_rupture_getters is used instead
class RuptureGetter(object):
    """
    :param proxies:
        a list of RuptureProxies
    :param filename:
        path to the HDF5 file containing a 'rupgeoms' dataset
    :param grp_id:
        source group index
    :param trt:
        tectonic region type string
    :param samples:
        number of samples of the group
    :param rlzs_by_gsim:
        dictionary gsim -> rlzs for the group
    """
    def __init__(self, proxies, filename, grp_id, trt, samples,
                 rlzs_by_gsim):
        self.proxies = proxies
        self.weight = sum(proxy.weight for proxy in proxies)
        self.filename = filename
        self.grp_id = grp_id
        self.trt = trt
        self.samples = samples
        self.rlzs_by_gsim = rlzs_by_gsim
        n_occ = sum(int(proxy['n_occ']) for proxy in proxies)
        self.offset = 0  # can be overridden
        self.num_events = n_occ if samples > 1 else n_occ * sum(
            len(rlzs) for rlzs in rlzs_by_gsim.values())

    @property
    def num_ruptures(self):
        return len(self.proxies)

    def get_eid_rlz(self):
        """
        :returns: a composite array with the associations eid->rlz
        """
        eid_rlz = []
        for rup in self.proxies:
            ebr = EBRupture(mock.Mock(rup_id=rup['serial']), rup['source_id'],
                            self.grp_id, rup['n_occ'], self.samples)
            for rlz_id, eids in ebr.get_eids_by_rlz(self.rlzs_by_gsim,
                                                    self.offset).items():
                for eid in eids:
                    eid_rlz.append((eid + rup['e0'], rup['id'], rlz_id))
        return numpy.array(eid_rlz, events_dt)

    def get_rupdict(self):
        """
        :returns: a dictionary with the parameters of the rupture
        """
        assert len(self.proxies) == 1, 'Please specify a slice of length 1'
        dic = {'trt': self.trt, 'samples': self.samples}
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
            dic['grp_id'] = rec['grp_id']
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

    def __len__(self):
        return len(self.proxies)

    def __repr__(self):
        wei = ' [w=%d]' % self.weight if hasattr(self, 'weight') else ''
        return '<%s grp_id=%d, %d rupture(s)%s>' % (
            self.__class__.__name__, self.grp_id, len(self), wei)
