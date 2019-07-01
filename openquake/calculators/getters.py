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
from openquake.hazardlib import calc, geo, probability_map
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.source.rupture import EBRupture, BaseRupture
from openquake.risklib.riskinput import rsi2str
from openquake.commonlib.calc import _gmvs_to_haz_curve

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64
by_taxonomy = operator.attrgetter('taxonomy')
code2cls = BaseRupture.init()


def sig_eps_dt(imts):
    """
    :returns: a composite data type for the sig_eps output
    """
    lst = [('eid', U64), ('rlzi', U16)]
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
        else:
            raise NotImplementedError('multiple realizations')


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
        try:
            self.imts = self.dstore['gmf_data/imts'][()].split()
        except KeyError:  # engine < 3.3
            self.imts = list(self.dstore['oqparam'].imtls)
        self.rlzs = self.dstore['events']['rlz']
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
        return group_by_rlz(numpy.concatenate(data), self.rlzs)

    def __iter__(self):
        return iter(self.sids)

    def __len__(self):
        return len(self.sids)


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
        self.gmv_dt = oqparam.gmf_data_dt()
        self.sig_eps_dt = sig_eps_dt(oqparam.imtls)
        M32 = (F32, len(oqparam.imtls))
        self.gmv_eid_dt = numpy.dtype([('gmv', M32), ('eid', U64)])
        self.cmaker = ContextMaker(
            rupgetter.trt, rupgetter.rlzs_by_gsim,
            calc.filters.IntegrationDistance(oqparam.maximum_distance)
            if isinstance(oqparam.maximum_distance, dict)
            else oqparam.maximum_distance,
            {'filter_distance': oqparam.filter_distance})
        self.correl_model = oqparam.correl_model

    @property
    def sids(self):
        return self.sitecol.sids

    @property
    def imtls(self):
        return self.oqparam.imtls

    @property
    def imts(self):
        return list(self.oqparam.imtls)

    def init(self):
        """
        Initialize the computers. Should be called on the workers
        """
        if hasattr(self, 'computers'):  # init already called
            return
        with hdf5.File(self.rupgetter.filename, 'r') as parent:
            self.weights = parent['weights'][()]
        self.computers = []
        for ebr in self.rupgetter.get_ruptures(self.srcfilter):
            sitecol = self.sitecol.filtered(ebr.sids)
            try:
                computer = calc.gmf.GmfComputer(
                    ebr, sitecol, self.oqparam.imtls, self.cmaker,
                    self.oqparam.truncation_level, self.correl_model)
            except FarAwayRupture:
                # due to numeric errors, ruptures within the maximum_distance
                # when written, can be outside when read; I found a case with
                # a distance of 99.9996936 km over a maximum distance of 100 km
                continue
            self.computers.append(computer)

    def gen_gmfs(self):
        """
        Compute the GMFs for the given realization and
        yields arrays of the dtype (sid, eid, imti, gmv), one for rupture
        """
        self.sig_eps = []
        self.eid2rlz = {}
        for computer in self.computers:
            rup = computer.rupture
            sids = computer.sids
            eids_by_rlz = rup.get_eids_by_rlz(self.rlzs_by_gsim)
            data = []
            for gs, rlzs in self.rlzs_by_gsim.items():
                num_events = sum(len(eids_by_rlz[rlzi]) for rlzi in rlzs)
                if num_events == 0:
                    continue
                # NB: the trick for performance is to keep the call to
                # compute.compute outside of the loop over the realizations
                # it is better to have few calls producing big arrays
                array, sig, eps = computer.compute(gs, num_events)
                array = array.transpose(1, 0, 2)  # from M, N, E to N, M, E
                for i, miniml in enumerate(self.min_iml):  # gmv < minimum
                    arr = array[:, i, :]
                    arr[arr < miniml] = 0
                n = 0
                for rlzi in rlzs:
                    eids = eids_by_rlz[rlzi]
                    e = len(eids)
                    if not e:
                        continue
                    for ei, eid in enumerate(eids):
                        gmf = array[:, :, n + ei]  # shape (N, M)
                        tot = gmf.sum(axis=0)  # shape (M,)
                        if not tot.sum():
                            continue
                        tup = tuple([eid, rlzi] + list(sig[:, n + ei]) +
                                    list(eps[:, n + ei]))
                        self.sig_eps.append(tup)
                        self.eid2rlz[eid] = rlzi
                        for sid, gmv in zip(sids, gmf):
                            if gmv.sum():
                                data.append((sid, eid, gmv))
                    n += e
            yield numpy.array(data, self.gmv_dt)

    def get_gmfdata(self):
        """
        :returns: an array of the dtype (sid, eid, imti, gmv)
        """
        alldata = list(self.gen_gmfs())
        if not alldata:
            return numpy.zeros(0, self.gmv_dt)
        return numpy.concatenate(alldata)

    def get_hazard_by_sid(self, data=None):
        """
        :param data: if given, an iterator of records of dtype gmf_dt
        :returns: sid -> records
        """
        if data is None:
            data = self.get_gmfdata()
        return general.group_array(data, 'sid')

    def compute_gmfs_curves(self, monitor):
        """
        :returns: a dict with keys gmfdata, indices, hcurves
        """
        oq = self.oqparam
        with monitor('GmfGetter.init', measuremem=True):
            self.init()
        hcurves = {}  # key -> poes
        if oq.hazard_curves_from_gmfs:
            hc_mon = monitor('building hazard curves', measuremem=False)
            with monitor('building hazard', measuremem=True):
                gmfdata = self.get_gmfdata()  # returned later
                hazard = self.get_hazard_by_sid(data=gmfdata)
            for sid, hazardr in hazard.items():
                dic = group_by_rlz(hazardr, self.eid2rlz)
                for rlzi, array in dic.items():
                    with hc_mon:
                        gmvs = array['gmv']
                        for imti, imt in enumerate(oq.imtls):
                            poes = _gmvs_to_haz_curve(
                                gmvs[:, imti], oq.imtls[imt],
                                oq.ses_per_logic_tree_path)
                            hcurves[rsi2str(rlzi, sid, imt)] = poes
        elif oq.ground_motion_fields:  # fast lane
            with monitor('building hazard', measuremem=True):
                gmfdata = self.get_gmfdata()
        else:
            return dict(gmfdata=(), hcurves=hcurves)
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
        res = dict(gmfdata=gmfdata, hcurves=hcurves,
                   sig_eps=numpy.array(self.sig_eps, self.sig_eps_dt),
                   indices=numpy.array(indices, (U32, 3)))
        return res


def group_by_rlz(data, eid2rlz):
    """
    :param data: a composite array of D elements with a field `eid`
    :param eid2rlz: an array of E >= D elements or a dictionary
    :returns: a dictionary rlzi -> data for each realization
    """
    acc = general.AccumDict(accum=[])
    for rec in data:
        acc[eid2rlz[rec['eid']]].append(rec)
    return {rlzi: numpy.array(recs) for rlzi, recs in acc.items()}


def gen_rupture_getters(dstore, slc=slice(None),
                        concurrent_tasks=1, hdf5cache=None):
    """
    :yields: RuptureGetters
    """
    if dstore.parent:
        dstore = dstore.parent
    csm_info = dstore['csm_info']
    trt_by_grp = csm_info.grp_by("trt")
    samples = csm_info.get_samples_by_grp()
    rlzs_by_gsim = csm_info.get_rlzs_by_gsim_grp()
    rup_array = dstore['ruptures'][slc]
    maxweight = numpy.ceil(len(rup_array) / (concurrent_tasks or 1))
    nr, ne, first_event = 0, 0, 0
    for grp_id, arr in general.group_array(rup_array, 'grp_id').items():
        if not rlzs_by_gsim[grp_id]:
            # this may happen if a source model has no sources, like
            # in event_based_risk/case_3
            continue
        for block in general.block_splitter(arr, maxweight):
            rgetter = RuptureGetter(
                hdf5cache or dstore.filename, numpy.array(block), grp_id,
                trt_by_grp[grp_id], samples[grp_id], rlzs_by_gsim[grp_id],
                first_event)
            rgetter.weight = getattr(block, 'weight', len(block))
            first_event += rgetter.num_events
            yield rgetter
            nr += len(block)
            ne += rgetter.num_events
    logging.info('Read %d ruptures and %d events', nr, ne)


def get_maxloss_rupture(dstore, loss_type):
    """
    :param dstore: a DataStore instance
    :param loss_type: a loss type string
    :returns:
        EBRupture instance corresponding to the maximum loss for the
        given loss type
    """
    lti = dstore['oqparam'].lti[loss_type]
    ridx = dstore.get_attr('rup_loss_table', 'ridx')[lti]
    [rgetter] = gen_rupture_getters(dstore, slice(ridx, ridx + 1))
    [ebr] = rgetter.get_ruptures()
    return ebr


# this is never called directly; gen_rupture_getters is used instead
class RuptureGetter(object):
    """
    Iterable over ruptures.

    :param filename:
        path to an HDF5 file with a dataset names `ruptures`
    :param rup_indices:
        a list of rupture indices of the same group
    """
    def __init__(self, filename, rup_indices, grp_id, trt, samples,
                 rlzs_by_gsim, first_event=0):
        self.filename = filename
        self.rup_indices = rup_indices
        if not isinstance(rup_indices, list):  # is a rup_array
            self.__dict__['rup_array'] = rup_indices
            self.__dict__['num_events'] = int(rup_indices['n_occ'].sum())
        self.grp_id = grp_id
        self.trt = trt
        self.samples = samples
        self.rlzs_by_gsim = rlzs_by_gsim
        self.first_event = first_event
        self.rlz2idx = {}
        nr = 0
        rlzi = []
        for gsim, rlzs in rlzs_by_gsim.items():
            assert not isinstance(gsim, str)
            for rlz in rlzs:
                self.rlz2idx[rlz] = nr
                rlzi.append(rlz)
                nr += 1
        self.rlzs = numpy.array(rlzi)

    @general.cached_property
    def rup_array(self):
        with hdf5.File(self.filename, 'r') as h5:
            return h5['ruptures'][self.rup_indices]  # must be a list

    @general.cached_property
    def num_events(self):
        n_occ = self.rup_array['n_occ'].sum()
        ne = n_occ if self.samples > 1 else n_occ * len(self.rlzs)
        return int(ne)

    @property
    def num_ruptures(self):
        return len(self.rup_indices)

    @property
    def num_rlzs(self):
        return len(self.rlz2idx)

    # used in ebrisk
    def set_weights(self, src_filter, num_taxonomies_by_site):
        """
        :returns: the weights of the ruptures in the getter
        """
        weights = []
        for rup in self.rup_array:
            sids = src_filter.close_sids(rup, self.trt, rup['mag'])
            weights.append(num_taxonomies_by_site[sids].sum())
        self.weights = numpy.array(weights)
        self.weight = self.weights.sum()

    def split(self, maxweight):
        """
        :yields: RuptureGetters with weight <= maxweight
        """
        # NB: can be called only after .set_weights() has been called
        idx = {ri: i for i, ri in enumerate(self.rup_indices)}
        fe = self.first_event
        for rup_indices in general.block_splitter(
                self.rup_indices, maxweight, lambda ri: self.weights[idx[ri]]):
            if rup_indices:
                # some indices may have weight 0 and are discarded
                rgetter = self.__class__(
                    self.filename, list(rup_indices), self.grp_id,
                    self.trt, self.samples, self.rlzs_by_gsim, fe)
                fe += rgetter.num_events
                rgetter.weight = sum([self.weights[idx[ri]]
                                      for ri in rup_indices])
                yield rgetter

    def get_eid_rlz(self, monitor=None):
        """
        :returns: a composite array with the associations eid->rlz
        """
        eid_rlz = []
        for rup in self.rup_array:
            ebr = EBRupture(mock.Mock(serial=rup['serial']), rup['srcidx'],
                            self.grp_id, rup['n_occ'], self.samples)
            for rlz, eids in ebr.get_eids_by_rlz(self.rlzs_by_gsim).items():
                for eid in eids:
                    eid_rlz.append((eid, rlz))
        return numpy.array(eid_rlz, [('eid', U64), ('rlz', U16)])

    def get_rupdict(self):
        """
        :returns: a dictionary with the parameters of the rupture
        """
        assert len(self.rup_array) == 1, 'Please specify a slice of length 1'
        dic = {'trt': self.trt, 'samples': self.samples}
        with datastore.read(self.filename) as dstore:
            rupgeoms = dstore['rupgeoms']
            source_ids = dstore['source_info']['source_id']
            rec = self.rup_array[0]
            geom = rupgeoms[rec['gidx1']:rec['gidx2']].reshape(
                rec['sy'], rec['sz'])
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

    def get_ruptures(self, srcfilter=calc.filters.nofilter):
        """
        :returns: a list of EBRuptures filtered by bounding box
        """
        ebrs = []
        with datastore.read(self.filename) as dstore:
            rupgeoms = dstore['rupgeoms']
            for rec in self.rup_array:
                if srcfilter.integration_distance:
                    sids = srcfilter.close_sids(rec, self.trt, rec['mag'])
                    if len(sids) == 0:  # the rupture is far away
                        continue
                else:
                    sids = None
                mesh = numpy.zeros((3, rec['sy'], rec['sz']), F32)
                geom = rupgeoms[rec['gidx1']:rec['gidx2']].reshape(
                    rec['sy'], rec['sz'])
                mesh[0] = geom['lon']
                mesh[1] = geom['lat']
                mesh[2] = geom['depth']
                rupture_cls, surface_cls = code2cls[rec['code']]
                rupture = object.__new__(rupture_cls)
                rupture.serial = rec['serial']
                rupture.surface = object.__new__(surface_cls)
                rupture.mag = rec['mag']
                rupture.rake = rec['rake']
                rupture.hypocenter = geo.Point(*rec['hypo'])
                rupture.occurrence_rate = rec['occurrence_rate']
                rupture.tectonic_region_type = self.trt
                if surface_cls is geo.PlanarSurface:
                    rupture.surface = geo.PlanarSurface.from_array(
                        mesh[:, 0, :])
                elif surface_cls is geo.MultiSurface:
                    # mesh has shape (3, n, 4)
                    rupture.surface.__init__([
                        geo.PlanarSurface.from_array(mesh[:, i, :])
                        for i in range(mesh.shape[1])])
                elif surface_cls is geo.GriddedSurface:
                    # fault surface, strike and dip will be computed
                    rupture.surface.strike = rupture.surface.dip = None
                    rupture.surface.mesh = Mesh(*mesh)
                else:
                    # fault surface, strike and dip will be computed
                    rupture.surface.strike = rupture.surface.dip = None
                    rupture.surface.__init__(RectangularMesh(*mesh))
                grp_id = rec['grp_id']
                ebr = EBRupture(rupture, rec['srcidx'], grp_id,
                                rec['n_occ'], self.samples)
                # not implemented: rupture_slip_direction
                ebr.sids = sids
                ebrs.append(ebr)
        return ebrs

    def E2R(self, array, rlzi):
        """
        :param array: an array of shape (E, ...)
        :param rlzi: an array of E realization indices
        :returns: an aggregated array of shape (R, ...)
        """
        z = numpy.zeros((self.num_rlzs,) + array.shape[1:], array.dtype)
        for a, r in zip(array, rlzi):
            z[self.rlz2idx[r]] += a
        return z

    def __len__(self):
        return len(self.rup_indices)

    def __repr__(self):
        wei = ' [w=%d]' % self.weight if hasattr(self, 'weight') else ''
        return '<%s grp_id=%d, %d rupture(s)%s>' % (
            self.__class__.__name__, self.grp_id, len(self.rup_indices), wei)
