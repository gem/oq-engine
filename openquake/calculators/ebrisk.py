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
from openquake.baselib.python3compat import zip, encode
from openquake.calculators import base, event_based, getters
from openquake.calculators.export.loss_curves import get_loss_builder

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
U64 = numpy.uint64


def start_ebrisk(rupgetter, srcfilter, param, monitor):
    """
    Launcher for ebrisk tasks
    """
    with monitor('weighting ruptures'):
        rupgetter.set_weights(srcfilter, param['num_taxonomies'])
    if rupgetter.weights.sum() <= param['maxweight']:
        yield ebrisk(rupgetter, srcfilter, param, monitor)
    else:
        for rgetter in rupgetter.split(param['maxweight']):
            yield ebrisk, rgetter, srcfilter, param


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
    with datastore.read(srcfilter.filename) as dstore:
        assgetter = getters.AssetGetter(dstore)
    getter = getters.GmfGetter(rupgetter, srcfilter, param['oqparam'])
    with monitor('getting hazard'):
        getter.init()  # instantiate the computers
        hazard = getter.get_hazard()  # sid -> (rlzi, sid, eid, gmv)
    mon_risk = monitor('computing losses', measuremem=False)
    mon_agg = monitor('aggregating losses', measuremem=False)
    imts = getter.imts
    events = rupgetter.get_eid_rlz()
    eid2idx = {eid: idx for idx, eid in enumerate(events['eid'])}
    tagnames = param['aggregate_by']
    shape = assgetter.tagcol.agg_shape((len(events), L), tagnames)
    elt_dt = [('eid', U64), ('rlzi', U16), ('loss', (F32, shape[1:]))]
    acc = numpy.zeros(shape, F32)  # shape (E, L, T...)
    if param['avg_losses']:
        losses_by_A = numpy.zeros((assgetter.num_assets, L), F32)
    else:
        losses_by_A = None
    times = numpy.zeros(N)  # risk time per site_id
    for sid, haz in hazard.items():
        t0 = time.time()
        weights = getter.weights[haz['rlzi']]
        assets_on_sid, tagidxs = assgetter.get(sid, tagnames)
        eidx = [eid2idx[eid] for eid in haz['eid']]
        mon.duration += time.time() - t0
        mon.counts += 1
        with mon_risk:
            assets_ratios = riskmodel.get_assets_ratios(
                assets_on_sid, haz['gmv'], imts)
        with mon_agg:
            for assets, triples in assets_ratios:
                for lti, (lt, imt, loss_ratios) in enumerate(triples):
                    w = weights[imt]
                    for asset in assets:
                        aid = asset.ordinal
                        losses = loss_ratios * asset.value(lt)
                        acc[(eidx, lti) + tagidxs[aid]] += losses
                        if param['avg_losses']:
                            losses_by_A[aid, lti] += losses @ w
            times[sid] = time.time() - t0
    with monitor('building event loss table'):
        elt = numpy.fromiter(
            ((event['eid'], event['rlz'], losses)
             for event, losses in zip(events, acc) if losses.sum()), elt_dt)
        agg = general.AccumDict(accum=numpy.zeros(shape[1:], F32))  # rlz->agg
        for rec in elt:
            agg[rec['rlzi']] += rec['loss'] * param['ses_ratio']
    return {'elt': elt, 'agg_losses': agg, 'losses_by_A': losses_by_A,
            'times': times}


@base.calculators.add('ebrisk')
class EbriskCalculator(event_based.EventBasedCalculator):
    """
    Event based PSHA calculator generating event loss tables
    """
    core_task = start_ebrisk
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['event_based', 'event_based_risk', 'ucerf_hazard']

    def pre_execute(self):
        self.oqparam.ground_motion_fields = False
        super().pre_execute()
        # save a copy of the assetcol in hdf5cache
        self.hdf5cache = self.datastore.hdf5cache()
        with hdf5.File(self.hdf5cache, 'w') as cache:
            cache['sitecol'] = self.sitecol.complete
            cache['assetcol'] = self.assetcol
        self.param['ses_ratio'] = self.oqparam.ses_ratio
        self.param['aggregate_by'] = self.oqparam.aggregate_by
        # initialize the riskmodel
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy
        self.param['riskmodel'] = self.riskmodel
        self.L = L = len(self.riskmodel.loss_types)
        A = len(self.assetcol)
        self.datastore.create_dset('avg_losses', F32, (A, L))
        shp = self.get_shape(L)  # shape L, T...
        elt_dt = [('eid', U64), ('rlzi', U16), ('loss', (F32, shp))]
        self.datastore.create_dset('losses_by_event', elt_dt)
        self.zerolosses = numpy.zeros(shp, F32)  # to get the multi-index
        shp = self.get_shape(self.L, self.R)  # shape L, R, T...
        self.datastore.create_dset('agg_losses-rlzs', F32, shp)

    def execute(self):
        oq = self.oqparam
        self.set_param(
            num_taxonomies=self.assetcol.num_taxonomies_by_site(),
            maxweight=oq.ebrisk_maxweight / (oq.concurrent_tasks or 1))
        parent = self.datastore.parent
        if parent:
            hdf5path = parent.filename
            grp_indices = parent['ruptures'].attrs['grp_indices']
            nruptures = len(parent['ruptures'])
        else:
            hdf5path = self.datastore.hdf5cache()
            grp_indices = self.datastore['ruptures'].attrs['grp_indices']
            nruptures = len(self.datastore['ruptures'])
            with hdf5.File(hdf5path, 'r+') as cache:
                self.datastore.hdf5.copy('weights', cache)
                self.datastore.hdf5.copy('ruptures', cache)
                self.datastore.hdf5.copy('rupgeoms', cache)
        self.init_logic_tree(self.csm_info)
        smap = parallel.Starmap(
            self.core_task.__func__, monitor=self.monitor())
        trt_by_grp = self.csm_info.grp_by("trt")
        samples = self.csm_info.get_samples_by_grp()
        rlzs_by_gsim_grp = self.csm_info.get_rlzs_by_gsim_grp()
        ruptures_per_block = numpy.ceil(nruptures / (oq.concurrent_tasks or 1))
        for grp_id, rlzs_by_gsim in rlzs_by_gsim_grp.items():
            start, stop = grp_indices[grp_id]
            for indices in general.block_splitter(
                    range(start, stop), ruptures_per_block):
                rgetter = getters.RuptureGetter(
                    hdf5path, list(indices), grp_id,
                    trt_by_grp[grp_id], samples[grp_id], rlzs_by_gsim)
                smap.submit(rgetter, self.src_filter, self.param)
        return smap.reduce(self.agg_dicts, numpy.zeros(self.N))

    def agg_dicts(self, acc, dic):
        """
        :param dummy: unused parameter
        :param dic: a dictionary with keys eids, losses, losses_by_N
        """
        self.oqparam.ground_motion_fields = False  # hack
        if len(dic['elt']):
            with self.monitor('saving losses_by_event', autoflush=True):
                self.datastore.extend('losses_by_event', dic['elt'])
        with self.monitor('saving agg_losses-rlzs', autoflush=True):
            for r, aggloss in dic['agg_losses'].items():
                self.datastore['agg_losses-rlzs'][:, r] += aggloss
        if self.oqparam.avg_losses:
            with self.monitor('saving avg_losses', autoflush=True):
                self.datastore['avg_losses'] += dic['losses_by_A']
        return acc + dic['times']

    def get_shape(self, *sizes):
        """
        :returns: a shape (S1, ... SN, T1 ... TN)
        """
        return self.assetcol.tagcol.agg_shape(sizes, self.oqparam.aggregate_by)

    def build_datasets(self, builder):
        oq = self.oqparam
        stats = oq.hazard_stats()
        S = len(stats)
        P = len(builder.return_periods)
        C = len(oq.conditional_loss_poes)
        loss_types = ' '.join(self.riskmodel.loss_types)
        if oq.individual_curves or self.R == 1:
            shp = self.get_shape(P, self.R, self.L)  # shape P, R, L, T...
            self.datastore.create_dset('agg_curves-rlzs', F32, shp)
            self.datastore.set_attrs(
                'agg_curves-rlzs', return_periods=builder.return_periods,
                loss_types=loss_types)
        if oq.conditional_loss_poes:
            shp = self.get_shape(C, self.R, self.L)  # shape C, R, L, T...
            self.datastore.create_dset('agg_maps-rlzs', F32, shp)
        if self.R > 1:
            shp = self.get_shape(P, S, self.L)  # shape P, S, L, T...
            self.datastore.create_dset('agg_curves-stats', F32, shp)
            self.datastore.set_attrs(
                'agg_curves-stats', return_periods=builder.return_periods,
                stats=[encode(name) for (name, func) in stats],
                loss_types=loss_types)
            if oq.conditional_loss_poes:
                shp = self.get_shape(C, S, self.L)  # shape C, S, L, T...
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
        self.datastore.set_attrs('task_info/start_ebrisk', times=times)
        oq = self.oqparam
        elt_length = len(self.datastore['losses_by_event'])
        builder = get_loss_builder(self.datastore)
        self.build_datasets(builder)
        mon = performance.Monitor(hdf5=hdf5.File(self.datastore.hdf5cache()))
        smap = parallel.Starmap(compute_loss_curves_maps, monitor=mon)
        self.datastore.close()
        acc = []
        ct = oq.concurrent_tasks or 1
        for elt_slice in general.split_in_slices(elt_length, ct):
            smap.submit(self.datastore.filename, elt_slice,
                        oq.conditional_loss_poes, oq.individual_curves)
        acc = smap.reduce(acc=[])
        # copy performance information from the cache to the datastore
        pd = mon.hdf5['performance_data'].value
        hdf5.extend3(self.datastore.filename, 'performance_data', pd)
        self.datastore.open('r+')  # reopen
        self.datastore['task_info/compute_loss_curves_and_maps'] = (
            mon.hdf5['task_info/compute_loss_curves_maps'].value)
        with self.monitor('saving loss_curves and maps', autoflush=True):
            for name, idx, arr in acc:
                for ij, val in numpy.ndenumerate(arr):
                    self.datastore[name][ij + idx] = val


def compute_loss_curves_maps(filename, elt_slice, clp, individual_curves,
                             monitor):
    """
    :param filename: path to the datastore
    :param elt_slice: slice of the event loss table
    :param clp: conditional loss poes used to computed the maps
    :param individual_curves: if True, build the individual curves and maps
    :param monitor: a Monitor instance
    :yields:
        dictionaries with keys idx, agg_curves-rlzs, agg_curves-stats,
        agg_maps-rlzs, agg_maps-stats
    """
    with datastore.read(filename) as dstore:
        oq = dstore['oqparam']
        stats = oq.hazard_stats()
        builder = get_loss_builder(dstore)
        R = len(dstore['weights'])
        losses = [[] for _ in range(R)]
        elt = dstore['losses_by_event'][elt_slice]
        for rec in elt:
            losses[rec['rlzi']].append(rec['loss'])
    results = []
    for multi_index, _ in numpy.ndenumerate(elt[0]['loss']):
        result = {}
        thelosses = [[ls[multi_index] for ls in loss] for loss in losses]
        result['agg_curves-rlzs'], result['agg_curves-stats'] = (
            builder.build_pair(thelosses, stats))
        if R > 1 and individual_curves is False:
            del result['agg_curves-rlzs']
        if clp:
            result['agg_maps-rlzs'], result['agg_maps-stats'] = (
                builder.build_loss_maps(thelosses, clp, stats))
            if R > 1 and individual_curves is False:
                del result['agg_maps-rlzs']
        for name, arr in result.items():
            if arr is not None:
                results.append((name, multi_index, arr))
    return results
