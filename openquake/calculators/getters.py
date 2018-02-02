#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import collections
import numpy
from openquake.baselib.general import AccumDict, group_array, get_array
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib import calc, probability_map, stats

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64
EVENTS = -2
NBYTES = -1


class PmapGetter(object):
    """
    Read hazard curves from the datastore for all realizations or for a
    specific realization.

    :param dstore: a DataStore instance
    :param sids: the subset of sites to consider (if None, all sites)
    :param rlzs_assoc: a RlzsAssoc instance (if None, infers it)
    """
    def __init__(self, dstore, sids=None, rlzs_assoc=None):
        dstore.open()  # if not
        self.rlzs_assoc = rlzs_assoc or dstore['csm_info'].get_rlzs_assoc()
        self.dstore = dstore
        self.weights = [rlz.weight for rlz in self.rlzs_assoc.realizations]
        self.num_levels = len(self.dstore['oqparam'].imtls.array)
        self.sids = sids
        self.eids = None
        self.nbytes = 0
        if sids is None:
            self.sids = dstore['sitecol'].complete.sids

    @property
    def pmap_by_grp(self):
        if hasattr(self, '_pmap_by_grp'):  # already initialized
            return self._pmap_by_grp
        self.dstore.open()  # if not
        # populate _pmap_by_grp
        self._pmap_by_grp = {}
        if 'poes' in self.dstore:
            # build probability maps restricted to the given sids
            for grp, dset in self.dstore['poes'].items():
                sid2idx = {sid: i for i, sid in enumerate(dset.attrs['sids'])}
                L, I = dset.shape[1:]
                pmap = probability_map.ProbabilityMap(L, I)
                for sid in self.sids:
                    try:
                        idx = sid2idx[sid]
                    except KeyError:
                        continue
                    else:
                        pmap[sid] = probability_map.ProbabilityCurve(dset[idx])
                self._pmap_by_grp[grp] = pmap
                self.nbytes += pmap.nbytes

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
        assert self.sids is not None
        pmap = probability_map.ProbabilityMap(self.num_levels, 1)
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

    def get_hcurves(self, imtls):
        """
        :param imtls: intensity measure types and levels
        :returns: an array of (R, N) hazard curves
        """
        assert self.sids is not None, 'PmapGetter not bound to sids'
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
        if self.sids is None:
            self.sids = self.dstore['sitecol'].complete.sids
        if len(self.weights) == 1:  # one realization
            return self.get(0, grp)
        else:  # multiple realizations, assume hcurves/mean is there
            dic = ({g: self.dstore['poes/' + g] for g in self.dstore['poes']}
                   if grp is None else {grp: self.dstore['poes/' + grp]})
            return self.rlzs_assoc.compute_pmap_stats(dic, [stats.mean_curve])


class GmfDataGetter(collections.Mapping):
    """
    A dictionary-like object {sid: dictionary by realization index}
    """
    def __init__(self, dstore, sids, num_rlzs, eids=None):
        self.dstore = dstore
        self.sids = sids
        self.num_rlzs = num_rlzs
        self.eids = eids
        self.E = 0 if eids is None else len(eids)

    def init(self):
        if hasattr(self, 'data'):  # already initialized
            return
        self.dstore.open()  # if not already open
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
        self.imtls = self.dstore['oqparam'].imtls
        self.gmdata = AccumDict(accum=numpy.zeros(len(self.imtls) + 2, F32))

    def get_hazard(self, gsim=None):
        """
        :param gsim: ignored
        :returns: an OrderedDict rlzi -> datadict
        """
        return self.data

    def __getitem__(self, sid):
        dset = self.dstore['gmf_data/data']
        idxs = self.dstore['gmf_data/indices'][sid]
        if len(idxs) == 0:  # site ID with no data
            return {}
        array = numpy.concatenate([dset[start:stop] for start, stop in idxs])
        return group_array(array, 'rlzi')

    def __iter__(self):
        return iter(self.sids)

    def __len__(self):
        return len(self.sids)


class GmfGetter(object):
    """
    An hazard getter with methods .gen_gmv and .get_hazard returning
    ground motion values.
    """
    def __init__(self, rlzs_by_gsim, ebruptures, sitecol, imtls,
                 min_iml, maximum_distance, truncation_level,
                 correlation_model, samples=1):
        assert sitecol is sitecol.complete, sitecol
        self.rlzs_by_gsim = rlzs_by_gsim
        self.num_rlzs = sum(len(rlzs) for gsim, rlzs in rlzs_by_gsim.items())
        self.ebruptures = ebruptures
        self.sitecol = sitecol
        self.imtls = imtls
        self.min_iml = min_iml
        self.cmaker = ContextMaker(
            rlzs_by_gsim,
            calc.filters.IntegrationDistance(maximum_distance)
            if isinstance(maximum_distance, dict) else maximum_distance)
        self.truncation_level = truncation_level
        self.correlation_model = correlation_model
        self.samples = samples
        self.gmf_data_dt = numpy.dtype(
            [('rlzi', U16), ('sid', U32),
             ('eid', U64), ('gmv', (F32, (len(imtls),)))])

    def init(self):
        """
        Initialize the computers. Should be called on the workers
        """
        if hasattr(self, 'eids'):  # init already called
            return
        self.N = len(self.sitecol.complete)
        self.I = I = len(self.imtls)
        self.R = sum(len(rlzs) for rlzs in self.rlzs_by_gsim.values())
        self.gmv_dt = numpy.dtype(
            [('sid', U32), ('eid', U64), ('gmv', (F32, (I,)))])
        self.gmv_eid_dt = numpy.dtype([('gmv', (F32, (I,))), ('eid', U64)])
        self.sids = self.sitecol.sids
        self.computers = []
        eids = []
        for ebr in self.ebruptures:
            computer = calc.gmf.GmfComputer(
                ebr, self.sitecol, self.imtls, self.cmaker,
                self.truncation_level, self.correlation_model)
            self.computers.append(computer)
            eids.append(ebr.events['eid'])
        self.eids = numpy.concatenate(eids) if eids else []
        # dictionary rlzi -> array(imtls, events, nbytes)
        self.gmdata = AccumDict(accum=numpy.zeros(len(self.imtls) + 2, F32))
        # dictionary eid -> index
        self.eid2idx = dict(zip(self.eids, range(len(self.eids))))

    def gen_gmv(self, gsim=None):
        """
        Compute the GMFs for the given realization and populate the .gmdata
        array. Yields tuples of the form (sid, eid, imti, gmv).
        """
        itemsize = self.gmf_data_dt.itemsize
        sample = 0  # in case of sampling the realizations have a corresponding
        # sample number from 0 to the number of samples of the given src model
        gsims = self.rlzs_by_gsim if gsim is None else [gsim]
        for gs in gsims:  # OrderedDict
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
                    gmdata[EVENTS] += e
                    for ei, eid in enumerate(all_eids[r]):
                        gmf = array[:, :, n + ei]  # shape (N, I)
                        tot = gmf.sum(axis=0)  # shape (I,)
                        if not tot.sum():
                            continue
                        for i, val in enumerate(tot):
                            gmdata[i] += val
                        for sid, gmv in zip(sids, gmf):
                            if gmv.sum():
                                gmdata[NBYTES] += itemsize
                                yield rlzi, sid, eid, gmv
                    n += e
            sample += len(rlzs)

    def get_hazard(self, gsim=None, data=None):
        """
        :param data: if given, an iterator of records of dtype gmf_data_dt
        :returns: an array (rlzi, sid, imti) -> array(gmv, eid)
        """
        if data is None:
            data = self.gen_gmv(gsim)
        hazard = numpy.array([collections.defaultdict(list)
                              for _ in range(self.N)])
        for rlzi, sid, eid, gmv in data:
            hazard[sid][rlzi].append((gmv, eid))
        for haz in hazard:
            for rlzi in haz:
                haz[rlzi] = numpy.array(haz[rlzi], self.gmv_eid_dt)
        return hazard


class LossRatiosGetter(object):
    """
    Read loss ratios from the datastore for all realizations or for a specific
    realization.

    :param dstore: a DataStore instance
    """
    def __init__(self, dstore, aids=None, lazy=True):
        self.dstore = dstore
        dset = self.dstore['all_loss_ratios/indices']
        self.aids = list(aids or range(len(dset)))
        self.indices = [dset[aid] for aid in self.aids]
        self.data = None if lazy else self.get_all()

    # used in the loss curves exporter
    def get(self, rlzi):
        """
        :param rlzi: a realization ordinal
        :returns: a dictionary aid -> array of shape (E, LI)
        """
        data = self.dstore['all_loss_ratios/data']
        dic = collections.defaultdict(list)  # aid -> ratios
        for aid, idxs in zip(self.aids, self.indices):
            for idx in idxs:
                for rec in data[idx[0]: idx[1]]:  # dtype (rlzi, ratios)
                    if rlzi == rec['rlzi']:
                        dic[aid].append(rec['ratios'])
        return {a: numpy.array(dic[a]) for a in dic}

    # used in the calculator
    def get_all(self):
        """
        :returns: a list of A composite arrays of dtype `lrs_dt`
        """
        if getattr(self, 'data', None) is not None:
            return self.data
        self.dstore.open()  # if closed
        data = self.dstore['all_loss_ratios/data']
        loss_ratio_data = []
        for aid, idxs in zip(self.aids, self.indices):
            if len(idxs):
                arr = numpy.concatenate([data[idx[0]: idx[1]] for idx in idxs])
            else:
                # FIXME: a test for this case is missing
                arr = numpy.array([], data.dtype)
            loss_ratio_data.append(arr)
        return loss_ratio_data
