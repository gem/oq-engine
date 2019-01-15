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
import time
import numpy

from openquake.baselib import hdf5, datastore, parallel, performance
from openquake.baselib.general import group_array, humansize
from openquake.baselib.python3compat import zip, encode
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
        data = getter.get_hazard(rlzidx=False)  # (sid, eid, gmv)
        haz_by_sid = group_array(data, 'sid')
    eids = numpy.unique(data['eid'])
    eid2idx = {eid: idx for idx, eid in enumerate(eids)}
    tagnames = param['aggregate_by']
    shape = assgetter.tagcol.agg_shape((len(eids), L), tagnames)
    acc = numpy.zeros(shape, F32)  # shape (E, L, T, ...)
    expvalue = numpy.zeros(shape[1:], F32)  # shape (L, T, ...)
    for sid, haz in haz_by_sid.items():
        t0 = time.time()
        assets, ass_by_aid = assgetter.get(sid)
        mon.duration += time.time() - t0
        for lti, aid, aval, eids_, losses in getter.gen_risk(
                assets, riskmodel, haz):
            tagi = ass_by_aid[aid][tagnames] if tagnames else ()
            tagidxs = tuple(idx - 1 for idx in tagi)
            for eid, loss in zip(eids_, losses):
                acc[(eid2idx[eid], lti) + tagidxs] += loss
                expvalue[(lti,) + tagidxs] += aval
    return {'losses': acc, 'eids': eids, 'expvalue': expvalue}


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
        # initialize the riskmodel
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy
        self.param['riskmodel'] = self.riskmodel

    def agg_dicts(self, dummy, dic):
        """
        :param dummy: unused parameter
        :param dic: a dictionary with keys losses, expvalue, eids
        """
        if 'losses_by_event' not in self.datastore:  # first time
            L = len(self.riskmodel.lti)
            shp = self.get_shape(len(self.eid2idx), L)
            logging.info('Creating losses_by_event of shape %s, %s', shp,
                         humansize(numpy.product(shp) * 4))
            self.datastore.create_dset('losses_by_event', F32, shp)
            self.datastore['exposed_value'] = dic['expvalue']
            self.oqparam.ground_motion_fields = False
        if len(dic['losses']):
            with self.monitor('saving losses_by_event', measuremem=True):
                lbe = self.datastore['losses_by_event']
                idx = [self.eid2idx[eid] for eid in dic['eids']]
                sort_idx, sort_arr = zip(*sorted(zip(idx, dic['losses'])))
                # h5py requires the indices to be sorted
                lbe[list(sort_idx)] = numpy.array(sort_arr)
                self.datastore['exposed_value'] += dic['expvalue']
        return 1

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

    def post_execute(self, dummy):
        """
        Compute and store average losses from the losses_by_event dataset,
        and then loss curves and maps.
        """
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
