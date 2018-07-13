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
import logging
import numpy
from openquake.baselib import hdf5
from openquake.baselib.general import (
    AccumDict, groupby, group_array, get_array, block_splitter)
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.hazardlib import calc, geo, probability_map, stats
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.source.rupture import BaseRupture, EBRupture, classes
from openquake.risklib.riskinput import rsi2str
from openquake.commonlib.calc import _gmvs_to_haz_curve

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64

BaseRupture.init()  # initialize rupture codes


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
        self.imtls = self.dstore['oqparam'].imtls
        self.data = collections.OrderedDict()
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
        :returns: an OrderedDict rlzi -> datadict
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
            for gsim_idx, rlzis in array[grp]:
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
                    yield k, self.dstore['hcurves/' + k]
            elif num_rlzs == 1:
                yield 'rlz-000', self.get(0)
            return
        if 'poes' in self.dstore and kind in ('rlzs', 'all'):
            for rlzi in range(num_rlzs):
                hcurves = self.get(rlzi)
                yield 'rlz-%03d' % rlzi, hcurves
        elif 'poes' in self.dstore and kind.startswith('rlz-'):
            yield kind, self.get(int(kind[4:]))
        if 'hcurves' in self.dstore and kind in ('stats', 'all'):
            for k in sorted(self.dstore['hcurves']):
                yield k, self.dstore['hcurves/' + k]

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
        else:  # multiple realizations, assume hcurves/mean is there
            dic = ({g: self.dstore['poes/' + g] for g in self.dstore['poes']}
                   if grp is None else {grp: self.dstore['poes/' + grp]})
            return self.rlzs_assoc.compute_pmap_stats(
                dic, [stats.mean_curve, stats.std_curve])


class GmfDataGetter(collections.Mapping):
    """
    A dictionary-like object {sid: dictionary by realization index}
    """
    def __init__(self, dstore, sids, num_rlzs, num_events, imtls):
        self.dstore = dstore
        self.sids = sids
        self.num_rlzs = num_rlzs
        self.E = num_events
        self.imtls = imtls

    def init(self):
        if hasattr(self, 'data'):  # already initialized
            return
        self.dstore.open('r')  # if not already open
        self.eids = self.dstore['events']['eid']
        self.eids.sort()
        self.data = collections.OrderedDict()
        for sid in self.sids:
            self.data[sid] = data = self[sid]
            if not data:  # no GMVs, return 0, counted in no_damage
                self.data[sid] = {rlzi: 0 for rlzi in range(self.num_rlzs)}
        # dictionary eid -> index
        if self.eids is not None:
            self.eid2idx = dict(zip(self.eids, range(len(self.eids))))
        # now some attributes set for API compatibility with the GmfGetter
        # number of ground motion fields
        # dictionary rlzi -> array(imts, events, nbytes)
        self.gmdata = AccumDict(accum=numpy.zeros(len(self.imtls) + 1, F32))

    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: an OrderedDict rlzi -> datadict
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
        return group_array(numpy.concatenate(data), 'rlzi')

    def __iter__(self):
        return iter(self.sids)

    def __len__(self):
        return len(self.sids)


class GmfGetter(object):
    """
    An hazard getter with methods .gen_gmv and .get_hazard returning
    ground motion values.
    """
    def __init__(self, rlzs_by_gsim, ebruptures, sitecol, oqparam,
                 min_iml, samples=1):
        assert sitecol is sitecol.complete, sitecol
        self.rlzs_by_gsim = rlzs_by_gsim
        self.ebruptures = ebruptures
        self.sitecol = sitecol
        self.oqparam = oqparam
        self.min_iml = min_iml
        self.N = len(self.sitecol.complete)
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
            oqparam.filter_distance)
        self.correl_model = oqparam.correl_model
        self.samples = samples

    @property
    def sids(self):
        return self.sitecol.sids

    @property
    def imtls(self):
        return self.oqparam.imtls

    def init(self):
        """
        Initialize the computers. Should be called on the workers
        """
        if hasattr(self, 'eids'):  # init already called
            return
        self.computers = []
        eids = []
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
            eids.append(ebr.events['eid'])
        self.eids = numpy.concatenate(eids) if eids else []
        # dictionary rlzi -> array(imtls, events, nbytes)
        self.gmdata = AccumDict(accum=numpy.zeros(self.I + 1, F32))
        # dictionary eid -> index
        self.eid2idx = dict(zip(self.eids, range(len(self.eids))))

    def gen_gmv(self):
        """
        Compute the GMFs for the given realization and populate the .gmdata
        array. Yields tuples of the form (sid, eid, imti, gmv).
        """
        sample = 0  # in case of sampling the realizations have a corresponding
        # sample number from 0 to the number of samples of the given src model
        for gs in self.rlzs_by_gsim:  # OrderedDict
            rlzs = self.rlzs_by_gsim[gs]
            for computer in self.computers:
                rup = computer.rupture
                sids = computer.sids
                if self.samples > 1:
                    # events of the current slice of realizations
                    all_eids = [get_array(rup.events, sample=s)['eid']
                                for s in range(sample, sample + len(rlzs))]
                else:
                    all_eids = [rup.events['eid']] * len(rlzs)
                num_events = sum(len(eids) for eids in all_eids)
                # NB: the trick for performance is to keep the call to
                # compute.compute outside of the loop over the realizations
                # it is better to have few calls producing big arrays
                array = computer.compute(gs, num_events).transpose(1, 0, 2)
                # shape (N, I, E)
                for i, miniml in enumerate(self.min_iml):  # gmv < minimum
                    arr = array[:, i, :]
                    arr[arr < miniml] = 0
                n = 0
                for r, rlzi in enumerate(rlzs):
                    e = len(all_eids[r])
                    gmdata = self.gmdata[rlzi]
                    gmdata[-1] += e  # increase number of events
                    for ei, eid in enumerate(all_eids[r]):
                        gmf = array[:, :, n + ei]  # shape (N, I)
                        tot = gmf.sum(axis=0)  # shape (I,)
                        if not tot.sum():
                            continue
                        for i, val in enumerate(tot):
                            gmdata[i] += val
                        for sid, gmv in zip(sids, gmf):
                            if gmv.sum():
                                yield rlzi, sid, eid, gmv
                    n += e
            sample += len(rlzs)

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
        :returns: a dict with keys gmdata, gmfdata, indices, hcurves
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
        res = dict(gmfdata=gmfdata, hcurves=hcurves, gmdata=self.gmdata,
                   indices=numpy.array(indices, (U32, 3)))
        return res


def get_ruptures_by_grp(dstore, slice_=slice(None)):
    """
    Extracts the ruptures corresponding to the given slice. If missing,
    extract all ruptures.

    :returns: a dictionary grp_id -> list of EBRuptures
    """
    if slice_.stop is None:
        n = len(dstore['ruptures']) - (slice_.start or 0)
        logging.info('Reading %d ruptures from the datastore', n)
    rgetter = RuptureGetter(dstore, slice_)
    return groupby(rgetter, operator.attrgetter('grp_id'))


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
    [ebr] = RuptureGetter(dstore, slice(ridx, ridx + 1))
    return ebr


class RuptureGetter(object):
    """
    Iterable over ruptures.

    :param dstore:
        a DataStore instance with a dataset names `ruptures`
    :param mask:
        which ruptures to read; it can be:
        - None: read all ruptures
        - a slice
        - a boolean mask
        - a list of integers
    :param grp_id:
        the group ID of the ruptures, if they are homogeneous, or None
    """
    @classmethod
    def from_(cls, dstore):
        """
        :returns: a dictionary grp_id -> RuptureGetter instance
        """
        array = dstore['ruptures'].value
        grp_ids = numpy.unique(array['grp_id'])
        return {grp_id: cls(dstore, array['grp_id'] == grp_id, grp_id)
                for grp_id in grp_ids}

    def __init__(self, dstore, mask=None, grp_id=None):
        self.dstore = dstore
        self.mask = slice(None) if mask is None else mask
        self.grp_id = grp_id

    def split(self, block_size):
        """
        Split a RuptureGetter in multiple getters, each one containing a block
        of ruptures.

        :param block_size:
            maximum length of the rupture blocks
        :returns:
            `RuptureGetters` containing `block_size` ruptures and with
            an attribute `.n_events` counting the total number of events
        """
        getters = []
        indices, = self.mask.nonzero()
        for block in block_splitter(indices, block_size):
            idxs = list(block)  # not numpy.int_(block)!
            rgetter = self.__class__(self.dstore, idxs, self.grp_id)
            rup = self.dstore['ruptures'][idxs]
            # use int below, otherwise n_events would be a numpy.uint64
            rgetter.n_events = int((rup['eidx2'] - rup['eidx1']).sum())
            getters.append(rgetter)
        return getters

    def __iter__(self):
        self.dstore.open('r')  # if needed
        attrs = self.dstore.get_attrs('ruptures')
        code2cls = {}  # code -> rupture_cls, surface_cls
        for key, val in attrs.items():
            if key.startswith('code_'):
                code2cls[int(key[5:])] = [classes[v] for v in val.split()]
        grp_trt = self.dstore['csm_info'].grp_by("trt")
        events = self.dstore['events']
        ruptures = self.dstore['ruptures'][self.mask]
        rupgeoms = self.dstore['rupgeoms'][self.mask]
        # NB: ruptures.sort(order='serial') causes sometimes a SystemError:
        # <ufunc 'greater'> returned a result with an error set
        # this is way I am sorting with Python and not with numpy below
        data = sorted((serial, ridx) for ridx, serial in enumerate(
            ruptures['serial']))
        for serial, ridx in data:
            rec = ruptures[ridx]
            evs = events[rec['eidx1']:rec['eidx2']]
            if self.grp_id is not None and self.grp_id != rec['grp_id']:
                continue
            mesh = rupgeoms[ridx].reshape(3, rec['sy'], rec['sz'])
            rupture_cls, surface_cls = code2cls[rec['code']]
            rupture = object.__new__(rupture_cls)
            rupture.serial = serial
            rupture.surface = object.__new__(surface_cls)
            rupture.mag = rec['mag']
            rupture.rake = rec['rake']
            rupture.seed = rec['seed']
            rupture.hypocenter = geo.Point(*rec['hypo'])
            rupture.occurrence_rate = rec['occurrence_rate']
            rupture.tectonic_region_type = grp_trt[rec['grp_id']]
            pmfx = rec['pmfx']
            if pmfx != -1:
                rupture.pmf = self.dstore['pmfs'][pmfx]
            if surface_cls is geo.PlanarSurface:
                rupture.surface = geo.PlanarSurface.from_array(mesh[:, 0, :])
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
            ebr = EBRupture(rupture, (), evs)
            ebr.eidx1 = rec['eidx1']
            ebr.eidx2 = rec['eidx2']
            # not implemented: rupture_slip_direction
            yield ebr

    def __len__(self):
        if hasattr(self.mask, 'start'):  # is a slice
            if self.mask.start is None and self.mask.stop is None:
                return len(self.dstore['ruptures'])
            else:
                return self.mask.stop - self.mask.start
        elif isinstance(self.mask, list):
            # NB: h5py wants lists, not arrays of indices
            return len(self.mask)
        else:  # is a boolean mask
            return self.mask.sum()
