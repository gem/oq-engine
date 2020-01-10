# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
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
from openquake.commonlib.calc import _gmvs_to_haz_curve

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
        lst.append(('sig_' + imt, F32))
    for imt in imts:
        lst.append(('eps_' + imt, F32))
    return numpy.dtype(lst)


class PmapGetter(object):
    """
    Read hazard curves from the datastore for all realizations or for a
    specific realization.

    :param dstore: a DataStore instance or file system path to it
    :param sids: the subset of sites to consider (if None, all sites)
    :param rlzs_assoc: a RlzsAssoc instance (if None, infers it)
    """
    def __init__(self, dstore, weights, sids=None, poes=()):
        self.dstore = dstore
        self.sids = dstore['sitecol'].sids if sids is None else sids
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

    def init(self):
        """
        Read the poes and set the .data attribute with the hazard curves
        """
        if hasattr(self, '_pmap_by_grp'):  # already initialized
            return self._pmap_by_grp
        if isinstance(self.dstore, str):
            self.dstore = hdf5.File(self.dstore, 'r')
        else:
            self.dstore.open('r')  # if not
        if self.sids is None:
            self.sids = self.dstore['sitecol'].sids
        oq = self.dstore['oqparam']
        self.imtls = oq.imtls
        self.poes = self.poes or oq.poes
        rlzs_by_grp = self.dstore['rlzs_by_grp']
        self.rlzs_by_grp = {k: dset[()] for k, dset in rlzs_by_grp.items()}

        # populate _pmap_by_grp
        self._pmap_by_grp = {}
        if 'poes' in self.dstore:
            # build probability maps restricted to the given sids
            ok_sids = set(self.sids)
            for grp, dset in self.dstore['poes'].items():
                ds = dset['array']
                L, G = ds.shape[1:]
                pmap = probability_map.ProbabilityMap(L, G)
                for idx, sid in enumerate(dset['sids'][()]):
                    if sid in ok_sids:
                        pmap[sid] = probability_map.ProbabilityCurve(ds[idx])
                self._pmap_by_grp[grp] = pmap
                self.nbytes += pmap.nbytes
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

    def get_pcurves(self, sid):  # used in classical
        """
        :returns: a list of R probability curves with shape L
        """
        pmap_by_grp = self.init()
        L = len(self.imtls.array)
        pcurves = [probability_map.ProbabilityCurve(numpy.zeros((L, 1)))
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

    def get_pcurve(self, s, r, g):  # used in disaggregation
        """
        :param s: site ID
        :param r: realization ID
        :param g: group ID
        :returns: a probability curves with shape L (or None, if missing)
        """
        grp = 'grp-%02d' % g
        pmap = self.init()[grp]
        try:
            pc = pmap[s]
        except KeyError:
            return
        L = len(self.imtls.array)
        pcurve = probability_map.ProbabilityCurve(numpy.zeros((L, 1)))
        for gsim_idx, rlzis in enumerate(self.rlzs_by_grp[grp]):
            for rlzi in rlzis:
                if rlzi == r:
                    pcurve |= probability_map.ProbabilityCurve(
                        pc.array[:, [gsim_idx]])
        return pcurve

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
    def __init__(self, dstore, sids, num_rlzs):
        self.dstore = dstore
        self.sids = sids
        self.num_rlzs = num_rlzs
        assert len(sids) == 1, sids

    def init(self):
        if hasattr(self, 'data'):  # already initialized
            return
        self.dstore.open('r')  # if not already open
        if 'amplification' in self.dstore:
            sitecol = self.dstore['sitecol']
            arr = self.dstore['amplification']
            dic = general.group_array(arr, 'ampcode')
            imts = self.dstore['gmf_data/imts'][()].split()
            self.amplification = numpy.zeros((len(sitecol), len(imts)))
            for m, imt in enumerate(imts):
                for sid, ampl in enumerate(sitecol.ampcode):
                    [f] = dic[ampl][imt]
                    self.amplification[sid, m] = f
        else:
            self.amplification = ()
        try:
            self.imts = self.dstore['gmf_data/imts'][()].split()
        except KeyError:  # engine < 3.3
            self.imts = list(self.dstore['oqparam'].imtls)
        self.rlzs = self.dstore['events']['rlz_id']
        self.data = self[self.sids[0]]
        if not self.data:  # no GMVs, return 0, counted in no_damage
            self.data = {rlzi: 0 for rlzi in range(self.num_rlzs)}
        # now some attributes set for API compatibility with the GmfGetter
        # number of ground motion fields
        # dictionary rlzi -> array(imts, events, nbytes)
        self.E = len(self.rlzs)

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
        arr = numpy.concatenate(data)
        if len(self.amplification):
            for m, ampl in enumerate(self.amplification[sid]):
                arr['gmv'][:, m] *= ampl
        return group_by_rlz(arr, self.rlzs)

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
    def __init__(self, rupgetter, srcfilter, oqparam):
        self.rlzs_by_gsim = rupgetter.rlzs_by_gsim
        self.rupgetter = rupgetter
        self.srcfilter = srcfilter
        self.sitecol = srcfilter.sitecol.complete
        self.oqparam = oqparam
        self.min_iml = oqparam.min_iml
        self.N = len(self.sitecol)
        self.num_rlzs = sum(len(rlzs) for rlzs in self.rlzs_by_gsim.values())
        self.sig_eps_dt = sig_eps_dt(oqparam.imtls)
        M32 = (F32, len(oqparam.imtls))
        self.gmv_eid_dt = numpy.dtype([('gmv', M32), ('eid', U32)])
        md = (calc.filters.IntegrationDistance(oqparam.maximum_distance)
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
        for ebr in self.rupgetter.get_ruptures():
            with mon:
                sitecol = self.sitecol.filtered(ebr.sids)
                try:
                    computer = calc.gmf.GmfComputer(
                        ebr, sitecol, self.oqparam.imtls, self.cmaker,
                        self.oqparam.truncation_level, self.correl_model)
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
            self.times.append((computer.rupture.id, len(computer.sids), dt))
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
                        gmvs = array['gmv']
                        for imti, imt in enumerate(oq.imtls):
                            poes = _gmvs_to_haz_curve(
                                gmvs[:, imti], oq.imtls[imt],
                                oq.ses_per_logic_tree_path)
                            hcurves[rsi2str(rlzi, sid, imt)] = poes
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


def gen_rupture_getters(dstore, slc=slice(None), srcfilter=None):
    """
    :yields: RuptureGetters
    """
    try:
        e0s = dstore['eslices'][:, 0]
    except KeyError:
        e0s = None
    csm_info = dstore['csm_info']
    trt_by_grp = csm_info.grp_by("trt")
    samples = csm_info.get_samples_by_grp()
    rlzs_by_gsim = csm_info.get_rlzs_by_gsim_grp()
    rup_array = dstore['ruptures'][slc]
    ct = dstore['oqparam'].concurrent_tasks
    maxweight = len(dstore['ruptures']) / (ct or 1)

    def gen(arr):
        if srcfilter:
            for rec in arr:
                sids = srcfilter.close_sids(rec, trt)
                if len(sids):
                    yield RuptureProxy(rec, sids)
        else:
            yield from map(RuptureProxy, arr)

    light_rgetters = []
    ntasks = 0
    nr = 0
    for grp_id, arr in general.group_array(rup_array, 'grp_id').items():
        if not rlzs_by_gsim[grp_id]:
            # this may happen if a source model has no sources, like
            # in event_based_risk/case_3
            continue
        trt = trt_by_grp[grp_id]
        for proxies in general.block_splitter(
                gen(arr), maxweight, operator.attrgetter('weight')):
            if e0s is None:
                e0 = numpy.zeros(len(proxies), U32)
            else:
                e0 = e0s[nr: nr + len(proxies)]
            rgetter = RuptureGetter(
                proxies, dstore.filename, grp_id,
                trt_by_grp[grp_id], samples[grp_id], rlzs_by_gsim[grp_id], e0)
            if rgetter.weight < maxweight / 2:
                light_rgetters.append(rgetter)
            else:
                yield rgetter
            nr += len(proxies)
            ntasks += 1
    nheavy = ntasks - len(light_rgetters)
    logging.info('There are %d/%d heavy tasks', nheavy, ntasks)
    yield from light_rgetters  # IMPORTANT: send the small tasks later


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
                 rlzs_by_gsim, e0=None):
        self.proxies = proxies
        self.weight = sum(proxy.weight for proxy in proxies)
        self.filename = filename
        self.grp_id = grp_id
        self.trt = trt
        self.samples = samples
        self.rlzs_by_gsim = rlzs_by_gsim
        self.e0 = e0
        n_occ = sum(int(proxy['n_occ']) for proxy in proxies)
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
        for e0, rup in zip(self.e0, self.proxies):
            ebr = EBRupture(mock.Mock(rup_id=rup['serial']), rup['srcidx'],
                            self.grp_id, rup['n_occ'], self.samples)
            for rlz_id, eids in ebr.get_eids_by_rlz(self.rlzs_by_gsim).items():
                for eid in eids:
                    eid_rlz.append((eid + e0, rup['id'], rlz_id))
        return numpy.array(eid_rlz, events_dt)

    def get_rupdict(self):
        """
        :returns: a dictionary with the parameters of the rupture
        """
        assert len(self.proxies) == 1, 'Please specify a slice of length 1'
        dic = {'trt': self.trt, 'samples': self.samples}
        with datastore.read(self.filename) as dstore:
            rupgeoms = dstore['rupgeoms']
            source_ids = dstore['source_info']['source_id']
            rec = self.proxies[0].rec
            geom = rupgeoms[rec['gidx1']:rec['gidx2']].reshape(
                rec['sx'], rec['sy'])
            dic['lons'] = geom['lon']
            dic['lats'] = geom['lat']
            dic['deps'] = geom['depth']
            rupclass, surclass = code2cls[rec['code']]
            dic['rupture_class'] = rupclass.__name__
            dic['surface_class'] = surclass.__name__
            dic['hypo'] = rec['hypo']
            dic['occurrence_rate'] = rec['occurrence_rate']
            dic['grp_id'] = rec['grp_id']
            dic['n_occ'] = rec['n_occ']
            dic['serial'] = rec['serial']
            dic['mag'] = rec['mag']
            dic['srcid'] = source_ids[rec['srcidx']]
        return dic

    def get_ruptures(self, min_mag=0):
        """
        :returns: a list of EBRuptures filtered by bounding box
        """
        ebrs = []
        with datastore.read(self.filename) as dstore:
            rupgeoms = dstore['rupgeoms']
            for e0, proxy in zip(self.e0, self.proxies):
                if proxy['mag'] < min_mag:
                    continue
                geom = rupgeoms[proxy['gidx1']:proxy['gidx2']].reshape(
                    proxy['sx'], proxy['sy'])
                ebr = proxy.to_ebr(geom, self.trt, self.samples)
                ebr.e0 = 0 if self.e0 is None else e0
                ebrs.append(ebr)
        return ebrs

    def __len__(self):
        return len(self.proxies)

    def __repr__(self):
        wei = ' [w=%d]' % self.weight if hasattr(self, 'weight') else ''
        return '<%s grp_id=%d, %d rupture(s)%s>' % (
            self.__class__.__name__, self.grp_id, len(self), wei)
