# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import logging
import operator
import time
import numpy

from openquake.baselib import hdf5, datastore, parallel, performance, general
from openquake.baselib.general import humansize, AccumDict
from openquake.baselib.python3compat import zip, encode
from openquake.calculators import base, event_based, getters
from openquake.calculators.export.loss_curves import get_loss_builder

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
U64 = numpy.uint64


def gen_risk(assets, riskmodel, haz, imts):
    """
    :param assets: a list of assets on the same site
    :param riskmodel: a CompositeRiskModel instance
    :params haz: hazard on the given site (rlzi, sid, eid, gmv)
    :param imts: intensity measure types
    :yields: loss_type, asset, loss_ratios
    """
    imti = {imt: i for i, imt in enumerate(imts)}
    tdict = riskmodel.get_taxonomy_dict()  # taxonomy -> taxonomy index
    gmvs = haz['gmv']
    E = len(gmvs)
    assets_by_t = general.groupby(assets, operator.attrgetter('taxonomy'))
    for taxo, rm in riskmodel.items():
        t = tdict[taxo]
        try:
            assets = assets_by_t[t]
        except KeyError:  # there are no assets of taxonomy taxo
            continue
        for lt, rf in rm.risk_functions.items():
            means, covs, idxs = rf.interpolate(gmvs[:, imti[rf.imt]])
            loss_ratios = numpy.zeros(E, F32)
            loss_ratios[idxs] = rf.sample(means, covs, idxs, None)
            for asset in assets:
                yield lt, asset, loss_ratios


def ebrisk(rupgetter, srcfilter, param, monitor):
    """
    :param rupgetter:
        a RuptureGetter instance
    :param srcfilter:
        a SourceFilter instance
    :param param:
        a dictionary of parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        an ArrayWrapper with shape (E, L, T, ...)
    """
    riskmodel = param['riskmodel']
    L = len(riskmodel.lti)
    N = len(srcfilter.sitecol.complete)
    mon = monitor('getting assets', measuremem=False)
    mon.counts = 1
    with datastore.read(rupgetter.hdf5path) as dstore:
        assgetter = getters.AssetGetter(dstore)
    with monitor('getting ruptures'):
        ebruptures = rupgetter.get_ruptures(srcfilter)
    getter = getters.GmfGetter(
        rupgetter.rlzs_by_gsim, ebruptures, srcfilter.sitecol,
        param['oqparam'], param['min_iml'])
    with monitor('getting hazard'):
        getter.init()  # instantiate the computers
        hazard = getter.get_hazard()  # sid -> (rlzi, sid, eid, gmv)
    with monitor('building risk'):
        imts = getter.imts
        eids = rupgetter.get_eid_rlz()['eid']
        eid2idx = {eid: idx for idx, eid in enumerate(eids)}
        tagnames = param['aggregate_by']
        shape = assgetter.tagcol.agg_shape((len(eids), L), tagnames)
        acc = numpy.zeros(shape, F32)  # shape (E, L, T, ...)
        if param['avg_losses']:
            losses_by_RN = AccumDict(accum=numpy.zeros((N, L), F32))
        else:
            losses_by_RN = {}
        times = numpy.zeros(N)  # risk time per site_id
        for sid, haz in hazard.items():
            t0 = time.time()
            assets, tagidxs = assgetter.get(sid, tagnames)
            mon.duration += time.time() - t0
            for lt, asset, ratios in gen_risk(assets, riskmodel, haz, imts):
                lti = riskmodel.lti[lt]
                losses = ratios * asset.value(lt)
                for eid, rlz, loss in zip(haz['eid'], haz['rlzi'], losses):
                    acc[(eid2idx[eid], lti) + tagidxs[asset.ordinal]] += loss
                    if param['avg_losses']:
                        losses_by_RN[rlz][sid, lti] += loss
            times[sid] = time.time() - t0
    return {'losses': acc, 'eids': eids, 'losses_by_RN': losses_by_RN,
            'times': times}


def compute_loss_curves_maps(hdf5path, multi_index, clp, individual_curves,
                             monitor):
    with datastore.read(hdf5path) as dstore:
        oq = dstore['oqparam']
        stats = oq.risk_stats()
        builder = get_loss_builder(dstore)
        indices = dstore.get_attr('events', 'indices')
        R = len(indices)
        losses_by_event = dstore['losses_by_event']
        losses = [None] * R
        for r, (s1, s2) in enumerate(indices):
            idx = (slice(s1, s2),) + multi_index
            losses[r] = losses_by_event[idx]
    result = {'idx': multi_index}
    result['agg_curves-rlzs'], result['agg_curves-stats'] = (
        builder.build_pair(losses, stats))
    if R > 1 and individual_curves is False:
        del result['agg_curves-rlzs']
    if clp:
        result['agg_maps-rlzs'], result['agg_maps-stats'] = (
            builder.build_loss_maps(losses, clp, stats))
        if R > 1 and individual_curves is False:
            del result['agg_maps-rlzs']
    return result


@base.calculators.add('ebrisk')
class EbriskCalculator(event_based.EventBasedCalculator):
    """
    Event based PSHA calculator generating event loss tables
    """
    core_task = ebrisk
    is_stochastic = True

    def pre_execute(self, pre_calculator=None):
        super().pre_execute(pre_calculator)
        # save a copy of the assetcol in hdf5cache
        self.hdf5cache = self.datastore.hdf5cache()
        with hdf5.File(self.hdf5cache) as cache:
            cache['assetcol'] = self.assetcol
        self.param['aggregate_by'] = self.oqparam.aggregate_by
        self.N = len(self.sitecol.complete)
        # initialize the riskmodel
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy
        self.param['riskmodel'] = self.riskmodel
        L = len(self.riskmodel.loss_types)
        self.num_assets = self.assetcol.num_assets_by_site()
        self.datastore.create_dset('losses_by_site', F32, (self.N, self.R, L))

    def acc0(self):
        return numpy.zeros(self.N)

    def rup_weight(self, rup):
        """
        :returns: the number of assets affected by the rupture
        """
        return 1
        trt = self.csm_info.trt_by_grp[rup['grp_id']]
        sids = self.src_filter.close_sids(rup, trt, rup['mag'])
        return self.num_assets[sids].sum() * rup['n_occ']

    def agg_dicts(self, acc, dic):
        """
        :param dummy: unused parameter
        :param dic: a dictionary with keys eids, losses, losses_by_RN
        """
        self.oqparam.ground_motion_fields = False  # hack
        if 'losses_by_event' not in set(self.datastore):  # first time
            L = len(self.riskmodel.lti)
            shp = self.get_shape(len(self.eid2idx), L)
            logging.info('Creating losses_by_event of shape %s, %s', shp,
                         humansize(numpy.product(shp) * 4))
            self.datastore.create_dset('losses_by_event', F32, shp)
        if len(dic['losses']):
            with self.monitor('saving losses_by_event', autoflush=True):
                lbe = self.datastore['losses_by_event']
                idx = [self.eid2idx[eid] for eid in dic['eids']]
                sort_idx, sort_arr = zip(*sorted(zip(idx, dic['losses'])))
                # h5py requires the indices to be sorted
                lbe[list(sort_idx)] = numpy.array(sort_arr)
        with self.monitor('saving losses_by_site', autoflush=True):
            for r, arr in dic['losses_by_RN'].items():
                self.datastore['losses_by_site'][:, r] += arr
        return acc + dic['times']

    def get_shape(self, *sizes):
        return self.assetcol.tagcol.agg_shape(sizes, self.oqparam.aggregate_by)

    def build_datasets(self, builder):
        oq = self.oqparam
        stats = oq.risk_stats()
        R = len(builder.weights)
        S = len(stats)
        L = len(self.riskmodel.lti)
        P = len(builder.return_periods)
        C = len(oq.conditional_loss_poes)
        loss_types = ' '.join(self.riskmodel.loss_types)
        if oq.individual_curves or R == 1:
            shp = self.get_shape(P, R, L)
            self.datastore.create_dset('agg_curves-rlzs', F32, shp)
            self.datastore.set_attrs(
                'agg_curves-rlzs', return_periods=builder.return_periods,
                loss_types=loss_types)
        if oq.conditional_loss_poes:
            shp = self.get_shape(C, R, L)
            self.datastore.create_dset('agg_maps-rlzs', F32, shp)
        if R > 1:
            shp = self.get_shape(P, S, L)
            self.datastore.create_dset('agg_curves-stats', F32, shp)
            self.datastore.set_attrs(
                'agg_curves-stats', return_periods=builder.return_periods,
                stats=[encode(name) for (name, func) in stats],
                loss_types=loss_types)
            if oq.conditional_loss_poes:
                shp = self.get_shape(C, S, L)
                self.datastore.create_dset('agg_maps-stats', F32, shp)
                self.datastore.set_attrs(
                    'agg_maps-stats',
                    stats=[encode(name) for (name, func) in stats],
                    loss_types=loss_types)

    def post_execute(self, times):
        """
        Compute and store average losses from the losses_by_event dataset,
        and then loss curves and maps.
        """
        self.datastore.set_attrs('task_info/ebrisk', times=times)
        logging.info('Building losses_by_rlz')
        with self.monitor('building avg_losses-rlzs', autoflush=True):
            self.build_avg_losses()
        oq = self.oqparam
        builder = get_loss_builder(self.datastore)
        self.build_datasets(builder)
        mon = performance.Monitor(hdf5=hdf5.File(self.datastore.hdf5cache()))
        smap = parallel.Starmap(compute_loss_curves_maps, monitor=mon)
        first = self.datastore['losses_by_event'][0]  # to get the multi_index
        self.datastore.close()
        acc = []
        for idx, _ in numpy.ndenumerate(first):
            smap.submit(self.datastore.hdf5path, idx,
                        oq.conditional_loss_poes, oq.individual_curves)
        for res in smap:
            idx = res.pop('idx')
            for name, arr in res.items():
                if arr is not None:
                    acc.append((name, idx, arr))
        # copy performance information from the cache to the datastore
        pd = mon.hdf5['performance_data'].value
        hdf5.extend3(self.datastore.hdf5path, 'performance_data', pd)
        self.datastore.open('r+')  # reopen
        self.datastore['task_info/compute_loss_curves_and_maps'] = (
            mon.hdf5['task_info/compute_loss_curves_maps'].value)
        with self.monitor('saving loss_curves and maps', autoflush=True):
            for name, idx, arr in acc:
                for ij, val in numpy.ndenumerate(arr):
                    self.datastore[name][ij + idx] = val

    def build_avg_losses(self):
        """
        Build the dataset avg_losses-rlzs from losses_by_event
        """
        indices = self.datastore.get_attr('events', 'indices')
        R = len(indices)
        dset = self.datastore['losses_by_event']
        E, L, *shp = dset.shape
        lbr = self.datastore.create_dset(
            'avg_losses-rlzs', F32, [L, R] + shp)
        for r, (s1, s2) in enumerate(indices):
            lbr[:, r] = dset[s1:s2].sum(axis=0) * self.oqparam.ses_ratio
