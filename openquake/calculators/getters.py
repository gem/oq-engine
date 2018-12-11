# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018 GEM Foundation
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
import mock
import numpy
from openquake.baselib import hdf5, datastore, general
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.hazardlib import calc, geo, probability_map, stats
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.source.rupture import EBRupture, classes
from openquake.risklib.riskinput import rsi2str
from openquake.commonlib.calc import _gmvs_to_haz_curve

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64


class PmapGetter(object):
    """
    Read hazard curves from the datastore for all realizations or for a
    specific realization.

    :param dstore: a DataStore instance or file system path to it
    :param sids: the subset of sites to consider (if None, all sites)
    :param rlzs_assoc: a RlzsAssoc instance (if None, infers it)
    """
    def __init__(self, dstore, rlzs_assoc=None, sids=None):
        self.dstore = dstore
        self.sids = dstore['sitecol'].sids if sids is None else sids
        self.rlzs_assoc = rlzs_assoc or dstore['csm_info'].get_rlzs_assoc()
        self.eids = None
        self.nbytes = 0
        self.sids = sids

    @property
    def weights(self):
        return [rlz.weight for rlz in self.rlzs_assoc.realizations]

    @property
    def imts(self):
        return list(self.imtls)

    def init(self):
        """
        Read the poes and set the .data attribute with the hazard curves
        """
        if hasattr(self, 'data'):  # already initialized
            return
        if isinstance(self.dstore, str):
            self.dstore = hdf5.File(self.dstore, 'r')
        else:
            self.dstore.open('r')  # if not
        if self.sids is None:
            self.sids = self.dstore['sitecol'].sids
        oq = self.dstore['oqparam']
        self.imtls = oq.imtls
        self.poes = oq.poes
        self.data = {}
        try:
            hcurves = self.get_hcurves(self.imtls)  # shape (R, N)
        except IndexError:  # no data
            return
        for sid, hcurve_by_rlz in zip(self.sids, hcurves.T):
            self.data[sid] = datadict = {}
            for rlzi, hcurve in enumerate(hcurve_by_rlz):
                datadict[rlzi] = lst = [None for imt in self.imtls]
                for imti, imt in enumerate(self.imtls):
                    lst[imti] = hcurve[imt]  # imls

    @property
    def pmap_by_grp(self):
        """
        :returns: dictionary "grp-XXX" -> ProbabilityMap instance
        """
        if hasattr(self, '_pmap_by_grp'):  # already called
            return self._pmap_by_grp
        # populate _pmap_by_grp
        self._pmap_by_grp = {}
        if 'poes' in self.dstore:
            # build probability maps restricted to the given sids
            ok_sids = set(self.sids)
            for grp, dset in self.dstore['poes'].items():
                ds = dset['array']
                L, I = ds.shape[1:]
                pmap = probability_map.ProbabilityMap(L, I)
                for idx, sid in enumerate(dset['sids'].value):
                    if sid in ok_sids:
                        pmap[sid] = probability_map.ProbabilityCurve(ds[idx])
                self._pmap_by_grp[grp] = pmap
                self.nbytes += pmap.nbytes
        return self._pmap_by_grp

    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: an dict rlzi -> datadict
        """
        return self.data

    def get(self, rlzi, grp=None):
        """
        :param rlzi: a realization index
        :param grp: None (all groups) or a string of the form "grp-XX"
        :returns: the hazard curves for the given realization
        """
        self.init()
        assert self.sids is not None
        pmap = probability_map.ProbabilityMap(len(self.imtls.array), 1)
        grps = [grp] if grp is not None else sorted(self.pmap_by_grp)
        array = self.rlzs_assoc.by_grp()
        for grp in grps:
            for gsim_idx, rlzis in enumerate(array[grp]):
                for r in rlzis:
                    if r == rlzi:
                        pmap |= self.pmap_by_grp[grp].extract(gsim_idx)
                        break
        return pmap

    def get_pmaps(self, sids):  # used in classical
        """
        :param sids: an array of S site IDs
        :returns: a list of R probability maps
        """
        return self.rlzs_assoc.combine_pmaps(self.pmap_by_grp)

    def get_hcurves(self, imtls=None):
        """
        :param imtls: intensity measure types and levels
        :returns: an array of (R, N) hazard curves
        """
        self.init()
        if imtls is None:
            imtls = self.imtls
        pmaps = [pmap.convert2(imtls, self.sids)
                 for pmap in self.get_pmaps(self.sids)]
        return numpy.array(pmaps)

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
        if not kind:  # use default
            if 'hcurves' in self.dstore:
                for k in sorted(self.dstore['hcurves']):
                    yield k, self.dstore['hcurves/' + k].value
            elif num_rlzs == 1:
                yield 'mean', self.get(0)
            return
        if 'poes' in self.dstore and kind in ('rlzs', 'all'):
            for rlzi in range(num_rlzs):
                hcurves = self.get(rlzi)
                yield 'rlz-%03d' % rlzi, hcurves
        elif 'poes' in self.dstore and kind.startswith('rlz-'):
            yield kind, self.get(int(kind[4:]))
        if 'hcurves' in self.dstore and kind in ('stats', 'all'):
            for k in sorted(self.dstore['hcurves']):
                yield k, self.dstore['hcurves/' + k].value

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
                array = numpy.zeros(pcurve.array.shape[:-1] + (2,))
                array[:, 0] = pcurve.array[:, 0]
                pcurve.array = array
            return pmap
        else:  # multiple realizations
            dic = ({g: self.dstore['poes/' + g] for g in self.dstore['poes']}
                   if grp is None else {grp: self.dstore['poes/' + grp]})
            return self.rlzs_assoc.compute_pmap_stats(
                dic, [stats.mean_curve, stats.std_curve])


class GmfDataGetter(collections.Mapping):
    """
    A dictionary-like object {sid: dictionary by realization index}
    """
    def __init__(self, dstore, sids, num_rlzs):
        self.dstore = dstore
        self.sids = sids
        self.num_rlzs = num_rlzs

    def init(self):
        if hasattr(self, 'data'):  # already initialized
            return
        self.dstore.open('r')  # if not already open
        try:
            self.imts = self.dstore['gmf_data/imts'].value.split()
        except KeyError:  # engine < 3.3
            self.imts = list(self.dstore['oqparam'].imtls)
        self.data = {}
        for sid in self.sids:
            self.data[sid] = data = self[sid]
            if not data:  # no GMVs, return 0, counted in no_damage
                self.data[sid] = {rlzi: 0 for rlzi in range(self.num_rlzs)}
        # now some attributes set for API compatibility with the GmfGetter
        # number of ground motion fields
        # dictionary rlzi -> array(imts, events, nbytes)
        self.E = len(self.dstore['events'])

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
        return general.group_array(numpy.concatenate(data), 'rlzi')

    def __iter__(self):
        return iter(self.sids)

    def __len__(self):
        return len(self.sids)


class GmfGetter(object):
    """
    An hazard getter with methods .gen_gmv and .get_hazard returning
    ground motion values.
    """
    def __init__(self, rlzs_by_gsim, ebruptures, sitecol, oqparam, min_iml):
        self.rlzs_by_gsim = rlzs_by_gsim
        self.ebruptures = ebruptures
        self.sitecol = sitecol.complete
        self.oqparam = oqparam
        self.min_iml = min_iml
        self.N = len(self.sitecol)
        self.num_rlzs = sum(len(rlzs) for rlzs in self.rlzs_by_gsim.values())
        self.I = len(oqparam.imtls)
        self.gmv_dt = numpy.dtype(
            [('sid', U32), ('eid', U64), ('gmv', (F32, (self.I,)))])
        self.gmv_eid_dt = numpy.dtype(
            [('gmv', (F32, (self.I,))), ('eid', U64)])
        self.cmaker = ContextMaker(
            rlzs_by_gsim,
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
        if hasattr(self, 'eids'):  # init already called
            return
        self.computers = []
        for ebr in self.ebruptures:
            try:
                computer = calc.gmf.GmfComputer(
                    ebr, self.sitecol, self.oqparam.imtls, self.cmaker,
                    self.oqparam.truncation_level, self.correl_model)
            except FarAwayRupture:
                # due to numeric errors ruptures within the maximum_distance
                # when written can be outside when read; I found a case with
                # a distance of 99.9996936 km over a maximum distance of 100 km
                continue
            self.computers.append(computer)

    def gen_gmv(self):
        """
        Compute the GMFs for the given realization and
        yields tuples of the form (sid, eid, imti, gmv).
        """
        for computer in self.computers:
            rup = computer.rupture
            sids = computer.sids
            eids_by_rlz = rup.get_eids_by_rlz(self.rlzs_by_gsim)
            for gs, rlzs in self.rlzs_by_gsim.items():
                num_events = sum(len(eids_by_rlz[rlzi]) for rlzi in rlzs)
                if num_events == 0:
                    continue
                # NB: the trick for performance is to keep the call to
                # compute.compute outside of the loop over the realizations
                # it is better to have few calls producing big arrays
                array = computer.compute(gs, num_events).transpose(1, 0, 2)
                # shape (N, I, E)
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
                        gmf = array[:, :, n + ei]  # shape (N, I)
                        tot = gmf.sum(axis=0)  # shape (I,)
                        if not tot.sum():
                            continue
                        for sid, gmv in zip(sids, gmf):
                            if gmv.sum():
                                yield rlzi, sid, eid, gmv
                    n += e

    def get_hazard(self, data=None):
        """
        :param data: if given, an iterator of records of dtype gmf_data_dt
        :returns: an array (rlzi, sid, imti) -> array(gmv, eid)
        """
        if data is None:
            data = self.gen_gmv()
        hazard = numpy.array([collections.defaultdict(list)
                              for _ in range(self.N)])
        for rlzi, sid, eid, gmv in data:
            hazard[sid][rlzi].append((gmv, eid))
        for haz in hazard:
            for rlzi in haz:
                haz[rlzi] = numpy.array(haz[rlzi], self.gmv_eid_dt)
        return hazard

    def compute_gmfs_curves(self, monitor):
        """
        :returns: a dict with keys gmfdata, indices, hcurves
        """
        oq = self.oqparam
        dt = oq.gmf_data_dt()
        with monitor('GmfGetter.init', measuremem=True):
            self.init()
        hcurves = {}  # key -> poes
        if oq.hazard_curves_from_gmfs:
            hc_mon = monitor('building hazard curves', measuremem=False)
            duration = oq.investigation_time * oq.ses_per_logic_tree_path
            with monitor('building hazard', measuremem=True):
                gmfdata = numpy.fromiter(self.gen_gmv(), dt)
                hazard = self.get_hazard(data=gmfdata)
            for sid, hazardr in zip(self.sids, hazard):
                for rlzi, array in hazardr.items():
                    if len(array) == 0:  # no data
                        continue
                    with hc_mon:
                        gmvs = array['gmv']
                        for imti, imt in enumerate(oq.imtls):
                            poes = _gmvs_to_haz_curve(
                                gmvs[:, imti], oq.imtls[imt],
                                oq.investigation_time, duration)
                            hcurves[rsi2str(rlzi, sid, imt)] = poes
        elif oq.ground_motion_fields:  # fast lane
            with monitor('building hazard', measuremem=True):
                gmfdata = numpy.fromiter(self.gen_gmv(), dt)
        else:
            return {}
        indices = []
        gmfdata.sort(order=('sid', 'rlzi', 'eid'))
        start = stop = 0
        for sid, rows in itertools.groupby(gmfdata['sid']):
            for row in rows:
                stop += 1
            indices.append((sid, start, stop))
            start = stop
        res = dict(gmfdata=gmfdata, hcurves=hcurves,
                   indices=numpy.array(indices, (U32, 3)))
        return res


def get_rupture_getters(dstore, slc=slice(None), split=0, hdf5cache=None):
    """
    :returns: a list of RuptureGetters
    """
    csm_info = dstore['csm_info']
    grp_trt = csm_info.grp_by("trt")
    samples = csm_info.get_samples_by_grp()
    rlzs_by_gsim = csm_info.get_rlzs_by_gsim_grp()
    rup_array = dstore['ruptures'][slc]
    code2cls = get_code2cls(dstore.get_attrs('ruptures'))
    rgetters = []
    by_grp = operator.itemgetter(2)  # serial, srcidx, grp_id
    for block in general.split_in_blocks(rup_array, split, key=by_grp):
        rups = numpy.array(block)
        grp_id = rups[0]['grp_id']
        if not rlzs_by_gsim[grp_id]:
            # this may happen if a source model has no sources, like
            # in event_based_risk/case_3
            continue
        rgetter = RuptureGetter(
            hdf5cache or dstore.hdf5path, code2cls, rups,
            grp_trt[grp_id], samples[grp_id], rlzs_by_gsim[grp_id])
        rgetters.append(rgetter)
    return rgetters


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
    [[ebr]] = get_rupture_getters(dstore, slice(ridx, ridx + 1))
    return ebr


def get_code2cls(ruptures_attrs):
    code2cls = {}  # code -> rupture_cls, surface_cls
    for key, val in ruptures_attrs.items():
        if key.startswith('code_'):
            code2cls[int(key[5:])] = [classes[v] for v in val.split()]
    return code2cls


class RuptureGetter(object):
    """
    Iterable over ruptures.

    :param hdf5path:
        path to an HDF5 file with a dataset names `ruptures`
    :param rup_array:
        an array of rupture parameters with homogeneous grp_id
    """
    def __init__(self, hdf5path, code2cls, rup_array, trt, samples,
                 rlzs_by_gsim):
        self.hdf5path = hdf5path
        self.code2cls = code2cls
        self.rup_array = rup_array
        self.trt = trt
        self.samples = samples
        self.rlzs_by_gsim = rlzs_by_gsim
        [self.grp_id] = numpy.unique(rup_array['grp_id'])

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

    def __iter__(self):
        with datastore.read(self.hdf5path) as dstore:
            rupgeoms = dstore['rupgeoms']
            for rec in self.rup_array:
                mesh = numpy.zeros((3, rec['sy'], rec['sz']), F32)
                geom = rupgeoms[rec['gidx1']:rec['gidx2']].reshape(
                    rec['sy'], rec['sz'])
                mesh[0] = geom['lon']
                mesh[1] = geom['lat']
                mesh[2] = geom['depth']
                rupture_cls, surface_cls = self.code2cls[rec['code']]
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
                yield ebr

    def __len__(self):
        return len(self.rup_array)

    def __repr__(self):
        return '<%s grp_id=%d, %d rupture(s)>' % (
            self.__class__.__name__, self.grp_id, len(self))
