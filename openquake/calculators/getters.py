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
from openquake.baselib.general import AccumDict, group_array
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib import calc

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64


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
