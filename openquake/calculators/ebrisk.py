# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import numpy

from openquake.baselib import datastore, hdf5, parallel, general
from openquake.baselib.python3compat import zip, encode
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.risklib import riskmodels
from openquake.risklib.scientific import losses_by_period, LossesByAsset
from openquake.risklib.riskinput import (
    cache_epsilons, get_assets_by_taxo, get_output)
from openquake.calculators import base, event_based, getters
from openquake.calculators.event_based_risk import build_loss_tables
from openquake.calculators.export.loss_curves import get_loss_builder

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
get_n_occ = operator.itemgetter(1)

gmf_info_dt = numpy.dtype([('ridx', U32), ('task_no', U16),
                           ('nsites', U16), ('gmfbytes', F32), ('dt', F32)])


def start_ebrisk(rupgetter, srcfilter, param, monitor):
    """
    Launcher for ebrisk tasks
    """
    rupgetters = rupgetter.split(srcfilter)
    if rupgetters:
        yield from parallel.split_task(
            ebrisk, rupgetters, srcfilter, param, monitor,
            duration=param['task_duration'])


def _calc_risk(hazard, param, monitor):
    gmfs = numpy.concatenate(hazard['gmfs'])
    events = numpy.concatenate(hazard['events'])
    mon_risk = monitor('computing risk', measuremem=False)
    mon_agg = monitor('aggregating losses', measuremem=False)
    dstore = datastore.read(param['hdf5path'])
    with monitor('getting assets'):
        assetcol = dstore['assetcol']
        assets_by_site = assetcol.assets_by_site()
    with monitor('getting crmodel'):
        crmodel = riskmodels.CompositeRiskModel.read(dstore)
        weights = dstore['weights'][()]
    E = len(events)
    L = len(param['lba'].loss_names)
    A = sum(len(assets) for assets in assets_by_site)
    shape = assetcol.tagcol.agg_shape((E, L), param['aggregate_by'])
    elt_dt = [('event_id', U32), ('rlzi', U16), ('loss', (F32, shape[1:]))]
    acc = dict(elt=numpy.zeros(shape, F32),  # shape (E, L, T...)
               alt=numpy.zeros((A, E, L), F32) if param['asset_loss_table']
               else None, gmf_info=[], events_per_sid=0, lossbytes=0)
    arr = acc['elt']
    alt = acc['alt']
    lba = param['lba']
    epspath = param['epspath']
    tagnames = param['aggregate_by']
    eid2rlz = dict(events[['id', 'rlz_id']])
    eid2idx = {eid: idx for idx, eid in enumerate(eid2rlz)}

    for sid, haz in general.group_array(gmfs, 'sid').items():
        assets_on_sid = assets_by_site[sid]
        if len(assets_on_sid) == 0:
            continue
        acc['events_per_sid'] += len(haz)
        if param['avg_losses']:
            ws = weights[[eid2rlz[eid] for eid in haz['eid']]]
        assets_by_taxo = get_assets_by_taxo(assets_on_sid, epspath)
        eidx = [eid2idx[eid] for eid in haz['eid']]
        with mon_risk:
            out = get_output(crmodel, assets_by_taxo, haz)
        with mon_agg:
            for a, asset in enumerate(assets_on_sid):
                aid = asset['ordinal']
                tagi = asset[tagnames] if tagnames else ()
                tagidxs = tuple(idx - 1 for idx in tagi)
                losses_by_lt = {}
                for lti, lt in enumerate(crmodel.loss_types):
                    lratios = out[lt][a]
                    if lt == 'occupants':
                        losses = lratios * asset['occupants_None']
                    else:
                        losses = lratios * asset['value-' + lt]
                    if param['asset_loss_table']:
                        alt[aid, eidx, lti] = losses
                    losses_by_lt[lt] = losses
                for loss_idx, losses in lba.compute(asset, losses_by_lt):
                    arr[(eidx, loss_idx) + tagidxs] += losses
                    if param['avg_losses']:
                        lba.losses_by_A[aid, loss_idx] += (
                            losses @ ws * param['ses_ratio'])
                    acc['lossbytes'] += losses.nbytes
    if len(gmfs):
        acc['events_per_sid'] /= len(gmfs)
    acc['gmf_info'] = numpy.array(hazard['gmf_info'], gmf_info_dt)
    acc['elt'] = numpy.fromiter(  # this is ultra-fast
        ((event['id'], event['rlz_id'], losses)  # losses (L, T...)
         for event, losses in zip(events, arr) if losses.sum()), elt_dt)
    if param['avg_losses']:
        acc['losses_by_A'] = param['lba'].losses_by_A
        # without resetting the cache the sequential avg_losses would be wrong!
        del param['lba'].__dict__['losses_by_A']
    if param['asset_loss_table']:
        acc['alt'] = alt, events['id']
    return acc


def ebrisk(rupgetters, srcfilter, param, monitor):
    """
    :param rupgetters: RuptureGetters with 1 rupture each
    :param srcfilter: a SourceFilter
    :param param: dictionary of parameters coming from oqparam
    :param monitor: a Monitor instance
    :returns: a dictionary with keys elt, alt, ...
    """
    mon_haz = monitor('getting hazard', measuremem=False)
    computers = []
    with monitor('getting ruptures'):
        for rupgetter in rupgetters:
            gg = getters.GmfGetter(rupgetter, srcfilter, param['oqparam'])
            gg.init()
            computers.extend(gg.computers)
    if not computers:  # all filtered out
        return {}
    rupgetters.clear()
    computers.sort(key=lambda c: c.rupture.ridx)
    hazard = dict(gmfs=[], events=[], gmf_info=[])
    for c in computers:
        with mon_haz:
            data = c.compute_all(gg.min_iml, gg.rlzs_by_gsim)
            hazard['gmfs'].append(data)
            hazard['events'].append(c.rupture.get_events(gg.rlzs_by_gsim))
        hazard['gmf_info'].append(
            (c.rupture.ridx, mon_haz.task_no, len(c.sids),
             data.nbytes, mon_haz.dt))
    computers.clear()
    acc = _calc_risk(hazard, param, monitor)
    return acc


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
        oq = self.oqparam
        oq.ground_motion_fields = False
        super().pre_execute()
        self.param['lba'] = lba = (
            LossesByAsset(self.assetcol, oq.loss_names,
                          self.policy_name, self.policy_dict))
        self.param['ses_ratio'] = oq.ses_ratio
        self.param['aggregate_by'] = oq.aggregate_by
        self.param['asset_loss_table'] = oq.asset_loss_table
        self.param.pop('oqparam', None)  # unneeded
        self.L = L = len(lba.loss_names)
        A = len(self.assetcol)
        self.datastore.create_dset('avg_losses-stats', F32, (A, 1, L))  # mean
        if oq.asset_loss_table:
            self.datastore.create_dset('asset_loss_table', F32, (A, self.E, L))
        shp = self.get_shape(L)  # shape L, T...
        elt_dt = [('event_id', U32), ('rlzi', U16), ('loss', (F32, shp))]
        self.datastore.create_dset('losses_by_event', elt_dt)
        self.zerolosses = numpy.zeros(shp, F32)  # to get the multi-index
        shp = self.get_shape(self.L, self.R)  # shape L, R, T...
        self.datastore.create_dset('agg_losses-rlzs', F32, shp)
        self.datastore.create_dset('gmf_info', gmf_info_dt)

    def execute(self):
        self.datastore.flush()  # just to be sure
        oq = self.oqparam
        parent = self.datastore.parent
        if parent:
            grp_indices = parent['ruptures'].attrs['grp_indices']
            n_occ = parent['ruptures']['n_occ']
            dstore = parent
        else:
            grp_indices = self.datastore['ruptures'].attrs['grp_indices']
            n_occ = self.datastore['ruptures']['n_occ']
            dstore = self.datastore
        per_block = numpy.ceil(n_occ.sum() / (oq.concurrent_tasks or 1))
        self.set_param(
            hdf5path=self.datastore.filename,
            task_duration=oq.task_duration or 600,  # 10min
            epspath=cache_epsilons(
                self.datastore, oq, self.assetcol, self.crmodel, self.E))
        self.init_logic_tree(self.csm_info)
        trt_by_grp = self.csm_info.grp_by("trt")
        samples = self.csm_info.get_samples_by_grp()
        rlzs_by_gsim_grp = self.csm_info.get_rlzs_by_gsim_grp()
        ngroups = 0
        fe = 0
        eslices = self.datastore['eslices']
        allargs = []
        allpairs = list(enumerate(n_occ))
        srcfilter = self.src_filter(dstore.filename)
        for grp_id, rlzs_by_gsim in rlzs_by_gsim_grp.items():
            start, stop = grp_indices[grp_id]
            if start == stop:  # no ruptures for the given grp_id
                continue
            ngroups += 1
            for pairs in general.block_splitter(
                    allpairs[start:stop], per_block, weight=get_n_occ):
                indices = [i for i, n in pairs]
                rup_array = dstore['ruptures'][indices]
                rgetter = getters.RuptureGetter(
                    rup_array, dstore.filename, grp_id,
                    trt_by_grp[grp_id], samples[grp_id], rlzs_by_gsim,
                    eslices[fe:fe + len(indices), 0])
                allargs.append((rgetter, srcfilter, self.param))
                fe += len(indices)
        logging.info('Found %d/%d source groups with ruptures',
                     ngroups, len(rlzs_by_gsim_grp))
        self.events_per_sid = []
        self.lossbytes = 0
        self.datastore.swmr_on()
        smap = parallel.Starmap(
            self.core_task.__func__, allargs, h5=self.datastore.hdf5)
        res = smap.reduce(self.agg_dicts, numpy.zeros(self.N))
        gmf_bytes = self.datastore['gmf_info']['gmfbytes'].sum()
        logging.info(
            'Produced %s of GMFs', general.humansize(gmf_bytes))
        logging.info(
            'Produced %s of losses', general.humansize(self.lossbytes))
        return res

    def agg_dicts(self, acc, dic):
        """
        :param dummy: unused parameter
        :param dic: dictionary with keys elt, losses_by_A
        """
        if not dic:
            return 1
        self.oqparam.ground_motion_fields = False  # hack
        elt = dic['elt']
        hdf5.extend(self.datastore['gmf_info'], dic['gmf_info'])
        if len(elt):
            with self.monitor('saving losses_by_event'):
                hdf5.extend(self.datastore['losses_by_event'], elt)
        if self.oqparam.avg_losses:
            with self.monitor('saving avg_losses'):
                self.datastore['avg_losses-stats'][:, 0] += dic['losses_by_A']
        if self.oqparam.asset_loss_table:
            with self.monitor('saving asset_loss_table'):
                alt, eids = dic['alt']
                idx = numpy.argsort(eids)  # indices sorting the eids
                self.datastore['asset_loss_table'][:, eids[idx]] = alt[:, idx]
        self.events_per_sid.append(dic['events_per_sid'])
        self.lossbytes += dic['lossbytes']
        return 1

    def get_shape(self, *sizes):
        """
        :returns: a shape (S1, ... SN, T1 ... TN)
        """
        return self.assetcol.tagcol.agg_shape(sizes, self.oqparam.aggregate_by)

    def build_datasets(self, builder):
        oq = self.oqparam
        stats = oq.hazard_stats().items()
        S = len(stats)
        P = len(builder.return_periods)
        C = len(oq.conditional_loss_poes)
        loss_types = oq.loss_names
        aggregate_by = {'aggregate_by': oq.aggregate_by}
        for tagname in oq.aggregate_by:
            aggregate_by[tagname] = getattr(self.assetcol.tagcol, tagname)[1:]
        units = self.datastore['cost_calculator'].get_units(loss_types)
        shp = self.get_shape(P, self.R, self.L)  # shape P, R, L, T...
        shape_descr = (['return_periods', 'rlzs', 'loss_types'] +
                       oq.aggregate_by)
        self.datastore.create_dset('agg_curves-rlzs', F32, shp)
        self.datastore.set_attrs(
            'agg_curves-rlzs', return_periods=builder.return_periods,
            shape_descr=shape_descr, loss_types=loss_types, units=units,
            rlzs=numpy.arange(self.R), **aggregate_by)
        if oq.conditional_loss_poes:
            shp = self.get_shape(C, self.R, self.L)  # shape C, R, L, T...
            self.datastore.create_dset('agg_maps-rlzs', F32, shp)
        if self.R > 1:
            shape_descr = (['return_periods', 'stats', 'loss_types'] +
                           oq.aggregate_by)
            shp = self.get_shape(P, S, self.L)  # shape P, S, L, T...
            self.datastore.create_dset('agg_curves-stats', F32, shp)
            self.datastore.set_attrs(
                'agg_curves-stats', return_periods=builder.return_periods,
                stats=[encode(name) for (name, func) in stats],
                shape_descr=shape_descr, loss_types=loss_types, units=units,
                **aggregate_by)
            if oq.conditional_loss_poes:
                shp = self.get_shape(C, S, self.L)  # shape C, S, L, T...
                self.datastore.create_dset('agg_maps-stats', F32, shp)
                self.datastore.set_attrs(
                    'agg_maps-stats',
                    stats=[encode(name) for (name, func) in stats],
                    loss_types=loss_types, units=units)

    def post_execute(self, dummy):
        """
        Compute and store average losses from the losses_by_event dataset,
        and then loss curves and maps.
        """
        oq = self.oqparam
        if oq.avg_losses:
            self.datastore['avg_losses-stats'].attrs['stats'] = [b'mean']
        logging.info('Building loss tables')
        build_loss_tables(self.datastore)
        self.datastore.flush()  # just to be sure
        shp = self.get_shape(self.L)  # (L, T...)
        text = ' x '.join(
            '%d(%s)' % (n, t) for t, n in zip(oq.aggregate_by, shp[1:]))
        logging.info('Producing %d(loss_types) x %s loss curves', self.L, text)
        builder = get_loss_builder(self.datastore)
        self.build_datasets(builder)
        self.datastore.close()  # so that the readers see the data
        self.datastore.open('r+')
        self.datastore.swmr_on()
        args = [(self.datastore.filename, builder, oq.ses_ratio, rlzi)
                for rlzi in range(self.R)]
        acc = list(parallel.Starmap(postprocess, args,
                                    h5=self.datastore.hdf5))
        for r, (curves, maps), agg_losses in acc:
            if len(curves):  # some realization can give zero contribution
                self.datastore['agg_curves-rlzs'][:, r] = curves
            if len(maps):  # conditional_loss_poes can be empty
                self.datastore['agg_maps-rlzs'][:, r] = maps
            self.datastore['agg_losses-rlzs'][:, r] = agg_losses
        if self.R > 1:
            logging.info('Computing aggregate statistics')
            set_rlzs_stats(self.datastore, 'agg_curves')
            set_rlzs_stats(self.datastore, 'agg_losses')
            if oq.conditional_loss_poes:
                set_rlzs_stats(self.datastore, 'agg_maps')

        # sanity check with the asset_loss_table
        if oq.asset_loss_table and len(oq.aggregate_by) == 1:
            alt = self.datastore['asset_loss_table'][()]
            if alt.sum() == 0:  # nothing was saved
                return
            logging.info('Checking the loss curves')
            tags = getattr(self.assetcol.tagcol, oq.aggregate_by[0])[1:]
            T = len(tags)
            P = len(builder.return_periods)
            # sanity check on the loss curves for simple tag aggregation
            arr = self.assetcol.aggregate_by(oq.aggregate_by, alt)
            # shape (T, E, L)
            rlzs = self.datastore['events']['rlz_id']
            curves = numpy.zeros((P, self.R, self.L, T))
            for t in range(T):
                for r in range(self.R):
                    for l in range(self.L):
                        curves[:, r, l, t] = losses_by_period(
                            arr[t, rlzs == r, l],
                            builder.return_periods,
                            builder.num_events[r],
                            builder.eff_time)
            numpy.testing.assert_allclose(
                curves, self.datastore['agg_curves-rlzs'][()])


# 1) parallelizing by events does not work, we need all the events
# 2) parallelizing by multi_index slows down everything with warnings
# kernel:NMI watchdog: BUG: soft lockup - CPU#26 stuck for 21s!
# due to excessive reading, and then we run out of memory
def postprocess(filename, builder, ses_ratio, rlzi, monitor):
    """
    :param filename: path to the datastore
    :param builder: LossCurvesMapsBuilder instance
    :param rlzi: realization index
    :param monitor: Monitor instance
    :returns: rlzi, (curves, maps), agg_losses
    """
    with datastore.read(filename) as dstore:
        rlzs = dstore['losses_by_event']['rlzi']
        losses = dstore['losses_by_event'][rlzs == rlzi]['loss']
    agg_losses = losses.sum(axis=0) * ses_ratio  # shape (L, T, ...)
    return rlzi, builder.build_curves_maps(losses, rlzi), agg_losses
