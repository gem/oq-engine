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
import numpy

from openquake.baselib import hdf5, datastore, parallel, performance
from openquake.baselib.general import group_array, humansize
from openquake.baselib.python3compat import zip, encode
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.hazardlib.calc.stochastic import TWO32
from openquake.risklib import riskinput, scientific
from openquake.calculators import base, event_based, getters
from openquake.calculators.export.loss_curves import get_loss_builder

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
U64 = numpy.uint64


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
    with monitor('getting ruptures'):
        ebruptures = rupgetter.get_ruptures(srcfilter)
    with monitor('getting assetcol'):
        with datastore.read(rupgetter.hdf5path) as dstore:
            assetcol = dstore['assetcol']
        assets_by_site = assetcol.assets_by_site()
    getter = getters.GmfGetter(
        rupgetter.rlzs_by_gsim, ebruptures, srcfilter.sitecol,
        param['oqparam'], param['min_iml'])
    tagnames = param['aggregate_by']
    with monitor('getting hazard'):
        getter.init()  # instantiate the computers
        data = getter.get_hazard(rlzidx=False)  # (sid, eid, gmv)
        haz_by_sid = group_array(data, 'sid')
    eids = numpy.unique(data['eid'])
    eid2idx = {eid: idx for idx, eid in enumerate(eids)}
    shape = assetcol.agg_shape((len(eids), L), tagnames)
    acc = numpy.zeros(shape, F32)  # shape (E, L, T, ...)
    for loss_type, asset, eids_, loss_ratios in getter.gen_risk(
            assets_by_site, riskmodel, haz_by_sid):
        losses = asset.value(loss_type) * loss_ratios * param['ses_ratio']
        lti = riskmodel.lti[loss_type]
        tagi = assetcol.array[asset.ordinal][tagnames]
        tagidxs = tuple(idx - 1 for idx in tagi)
        for eid, loss in zip(eids_, losses):
            acc[(eid2idx[eid], lti) + tagidxs] += loss
    return hdf5.ArrayWrapper(acc, {'eids': eids})


def compute_loss_curves_maps(hdf5path, multi_index, clp, individual_curves,
                             monitor):
    with datastore.read(hdf5path) as dstore:
        oq = dstore['oqparam']
        stats = oq.risk_stats()
        builder = get_loss_builder(dstore)
        indices = dstore['events_indices']
        R = len(indices)
        losses_by_event = dstore['losses_by_event']
        losses = [None] * R
        for r, startstop in enumerate(indices):
            losses[r] = numpy.concatenate([
                losses_by_event[(slice(*ss),) + multi_index]
                for ss in startstop])
    result = {'idx': multi_index}
    result['loss_curves/rlzs'], result['loss_curves/stats'] = (
        builder.build_pair(losses, stats))
    if R > 1 and individual_curves is False:
        del result['loss_curves/rlzs']
    if clp:
        result['loss_maps/rlzs'], result['loss_maps/stats'] = (
            builder.build_loss_maps(losses, clp, stats))
        if R > 1 and individual_curves is False:
            del result['loss_maps/rlzs']
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
        # initialize the riskmodel
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy
        self.param['riskmodel'] = self.riskmodel
        self.param['ses_ratio'] = self.oqparam.ses_ratio

    def agg_dicts(self, dummy, arr):
        """
        :param dummy: unused parameter
        :param arr: ArrayWrapper with an attribute .eids
        """
        if 'losses_by_event' not in self.datastore:  # first time
            L = len(self.riskmodel.lti)
            shp = self.get_shape(len(self.eid2idx), L)
            logging.info('Creating losses_by_event of shape %s, %s', shp,
                         humansize(numpy.product(shp) * 4))
            self.datastore.create_dset('losses_by_event', F32, shp)
            self.oqparam.ground_motion_fields = False
        with self.monitor('saving losses_by_event', measuremem=True):
            if not hasattr(self, 'eid2idx'):
                self.eid2idx = dict(
                    zip(self.datastore['events']['eid'], range(self.E)))
            if len(arr):
                idx = [self.eid2idx[eid] for eid in arr.eids]
                self.datastore['losses_by_event'][idx] = arr
        return 1

    def get_shape(self, *sizes):
        return self.assetcol.agg_shape(sizes, self.oqparam.aggregate_by)

    def build_datasets(self, builder):
        oq = self.oqparam
        stats = oq.risk_stats()
        R = len(builder.weights)
        S = len(stats)
        L = len(self.riskmodel.lti)
        P = len(builder.return_periods)
        C = len(oq.conditional_loss_poes)
        if oq.individual_curves or R == 1:
            shp = self.get_shape(P, R, L)
            self.datastore.create_dset('loss_curves/rlzs', F32, shp)
            self.datastore.set_attrs(
                'loss_curves/rlzs', return_periods=builder.return_periods)
        if oq.conditional_loss_poes:
            shp = self.get_shape(C, R, L)
            self.datastore.create_dset('loss_maps/rlzs', F32, shp)
        if R > 1:
            shp = self.get_shape(P, S, L)
            self.datastore.create_dset('loss_curves/stats', F32, shp)
            self.datastore.set_attrs(
                'loss_curves/stats', return_periods=builder.return_periods,
                stats=[encode(name) for (name, func) in stats])
            if oq.conditional_loss_poes:
                shp = self.get_shape(C, S, L)
                self.datastore.create_dset('loss_maps/stats', F32, shp)
                self.datastore.set_attrs(
                    'loss_maps/stats',
                    stats=[encode(name) for (name, func) in stats])

    def post_execute(self, dummy):
        """
        Compute and store average losses from the losses_by_event dataset,
        and then loss curves and maps.
        """
        oq = self.oqparam
        builder = get_loss_builder(self.datastore)
        self.build_datasets(builder)
        mon = performance.Monitor(hdf5=hdf5.File(self.datastore.hdf5cache()))
        smap = parallel.Starmap(compute_loss_curves_maps, monitor=mon)
        first = self.datastore['losses_by_event'][0]  # to get the multi_index
        self.datastore.close()
        for idx, _ in numpy.ndenumerate(first):
            smap.submit(self.datastore.hdf5path, idx,
                        oq.conditional_loss_poes, oq.individual_curves)
        acc = []
        for res in smap:
            idx = res.pop('idx')
            for name, arr in res.items():
                if arr is not None:
                    acc.append((name, idx, arr))
        self.datastore.open('r+')  # reopen
        for name, idx, arr in acc:
            for ij, val in numpy.ndenumerate(arr):
                self.datastore[name][ij + idx] = val
