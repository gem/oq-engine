# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019, GEM Foundation
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

import ast
import logging
import itertools
import numpy
import pandas

from openquake.baselib import general, parallel, datastore
from openquake.baselib.python3compat import encode
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.risklib import scientific
from openquake.calculators import base, views

F32 = numpy.float32
U32 = numpy.uint32


def build_aggkeys(aggregate_by, tagcol, full_aggregate_by):
    """
    :param aggregate_by: what to aggregate
    :param tagcol: the TagCollection
    :param full_aggregate_by: maximum possible aggregation
    """
    name2index = {n: i for i, n in enumerate(full_aggregate_by)}
    indexes = [name2index[n] for n in aggregate_by]
    if indexes != sorted(indexes):
        raise ValueError('The aggregation tags must be an ordered subset of '
                         '%s, got %s' % (full_aggregate_by, aggregate_by))
    tagids = []
    for tagname in full_aggregate_by:
        n1 = len(getattr(tagcol, tagname))
        lst = list(range(1, n1))
        if tagname in aggregate_by:
            tagids.append(lst)
        else:
            tagids.append([lst])
    aggkeys = []
    for ids in itertools.product(*tagids):
        aggkeys.append(','.join(map(str, ids)) + ',')
    return sorted(aggkeys)


def get_loss_builder(dstore, return_periods=None, loss_dt=None):
    """
    :param dstore: datastore for an event based risk calculation
    :returns: a LossCurvesMapsBuilder instance
    """
    oq = dstore['oqparam']
    weights = dstore['weights'][()]
    eff_time = oq.investigation_time * oq.ses_per_logic_tree_path
    num_events = numpy.bincount(dstore['events']['rlz_id'])
    periods = return_periods or oq.return_periods or scientific.return_periods(
        eff_time, num_events.max())
    return scientific.LossCurvesMapsBuilder(
        oq.conditional_loss_poes, numpy.array(periods),
        loss_dt or oq.loss_dt(), weights, dict(enumerate(num_events)),
        eff_time, oq.risk_investigation_time)


def post_ebrisk(dstore, aggkey, monitor):
    """
    :param dstore: a DataStore instance
    :param aggkey: aggregation key
    :param monitor: Monitor instance
    :returns: a dictionary rlzi -> {agg_curves, agg_losses, idx}
    """
    dstore.open('r')
    oq = dstore['oqparam']
    L = len(oq.loss_names)
    agglist = [x if isinstance(x, list) else [x]
               for x in ast.literal_eval(aggkey)]
    idx = tuple(x[0] - 1 for x in agglist if len(x) == 1)
    rlz_id = dstore['events']['rlz_id']
    E = len(rlz_id)
    arr = numpy.zeros((E, L))
    for ids in itertools.product(*agglist):
        key = ','.join(map(str, ids)) + ','
        try:
            recs = dstore['event_loss_table/' + key][()]
        except dstore.EmptyDataset:   # no data
            continue
        for rec in recs:
            arr[rec['event_id']] += rec['loss']
    builder = get_loss_builder(dstore)
    out = {}
    for rlz in numpy.unique(rlz_id):
        # DO NOT USE groupby here! you would run out of memory
        array = arr[rlz_id == rlz]  # shape E', L
        out[rlz] = dict(agg_curves=builder.build_curves(array, rlz),
                        agg_losses=array.sum(axis=0) * oq.ses_ratio,
                        idx=idx)
    return out


def get_src_loss_table(dstore, L):
    """
    :returns:
        (source_ids, array of losses of shape (Ns, L))
    """
    lbe = dstore['losses_by_event'][:]
    evs = dstore['events'][()]
    rlz_ids = evs['rlz_id'][lbe['event_id']]
    rup_ids = evs['rup_id'][lbe['event_id']]
    source_id = dstore['ruptures']['source_id'][rup_ids]
    w = dstore['weights'][:]
    acc = general.AccumDict(accum=numpy.zeros(L, F32))
    for source_id, rlz_id, loss in zip(source_id, rlz_ids, lbe['loss']):
        acc[source_id] += loss * w[rlz_id]
    return zip(*sorted(acc.items()))


@base.calculators.add('post_risk')
class PostRiskCalculator(base.RiskCalculator):
    """
    Compute losses and loss curves starting from an event loss table.
    """
    def pre_execute(self):
        oq = self.oqparam
        if oq.hazard_calculation_id and not self.datastore.parent:
            self.datastore.parent = datastore.read(oq.hazard_calculation_id)
        self.L = len(oq.loss_names)
        self.tagcol = self.datastore['assetcol/tagcol']

    def build_datasets(self, builder, aggregate_by, prefix):
        """
        Create the datasets agg_curves-XXX, tot_curves-XXX,
        agg_losses-XXX, tot_losses-XXX.
        """
        P = len(builder.return_periods)
        aggby = {'aggregate_by': aggregate_by}
        for tagname in aggregate_by:
            aggby[tagname] = encode(getattr(self.tagcol, tagname)[1:])
        shp = self.get_shape(self.L, self.R, aggregate_by=aggregate_by)
        # shape L, R, T...
        self.datastore.create_dset(prefix + 'losses-rlzs', F32, shp)
        shp = self.get_shape(P, self.R, self.L, aggregate_by=aggregate_by)
        # shape P, R, L, T...
        self.datastore.create_dset(prefix + 'curves-rlzs', F32, shp)

    def execute(self):
        oq = self.oqparam
        if oq.return_periods != [0]:
            # setting return_periods = 0 disable loss curves
            eff_time = oq.investigation_time * oq.ses_per_logic_tree_path
            if eff_time < 2:
                logging.warning(
                    'eff_time=%s is too small to compute loss curves',
                    eff_time)
                return
        if 'source_info' in self.datastore:  # missing for gmf_ebrisk
            logging.info('Building src_loss_table')
            source_ids, losses = get_src_loss_table(self.datastore, self.L)
            self.datastore['src_loss_table'] = losses
            self.datastore.set_shape_attrs('src_loss_table',
                                           source=source_ids,
                                           loss_type=oq.loss_names)
        shp = self.get_shape(self.L)  # (L, T...)
        text = ' x '.join(
            '%d(%s)' % (n, t) for t, n in zip(oq.aggregate_by, shp[1:]))
        logging.info('Producing %d(loss_types) x %s loss curves', self.L, text)
        builder = get_loss_builder(self.datastore)
        if oq.aggregate_by:
            self.build_datasets(builder, oq.aggregate_by, 'agg_')
        self.build_datasets(builder, [], 'app_')
        self.build_datasets(builder, [], 'tot_')
        parent = self.datastore.parent
        full_aggregate_by = (parent['oqparam'].aggregate_by if parent
                             else ()) or oq.aggregate_by
        if oq.aggregate_by:
            aggkeys = build_aggkeys(oq.aggregate_by, self.tagcol,
                                    full_aggregate_by)
            if parent and 'event_loss_table' in parent:
                ds = parent
            else:
                ds = self.datastore
                ds.swmr_on()
            smap = parallel.Starmap(
                post_ebrisk, [(ds, aggkey) for aggkey in aggkeys],
                h5=self.datastore.hdf5)
        else:
            smap = ()
        # do everything in process since it is really fast
        ds = self.datastore
        for res in smap:
            if not res:
                continue
            for r, dic in res.items():
                if oq.aggregate_by:
                    ds['agg_curves-rlzs'][
                        (slice(None), r, slice(None)) + dic['idx']  # PRLT..
                    ] = dic['agg_curves']
                    ds['agg_losses-rlzs'][
                        (slice(None), r) + dic['idx']  # LRT...
                    ] = dic['agg_losses']
                    ds['app_curves-rlzs'][:, r] += dic['agg_curves']  # PL

        lbe = ds['losses_by_event'][()]
        rlz_ids = ds['events']['rlz_id'][lbe['event_id']]
        dic = dict(enumerate(lbe['loss'].T))  # lti -> losses
        df = pandas.DataFrame(dic, rlz_ids)
        for r, losses_df in df.groupby(rlz_ids):
            losses = numpy.array(losses_df)
            curves = builder.build_curves(losses, r),
            ds['tot_curves-rlzs'][:, r] = curves  # PL
            ds['tot_losses-rlzs'][:, r] = losses.sum(axis=0) * oq.ses_ratio
        units = self.datastore['cost_calculator'].get_units(oq.loss_names)
        aggby = {tagname: encode(getattr(self.tagcol, tagname)[1:])
                 for tagname in oq.aggregate_by}
        set_rlzs_stats(self.datastore, 'app_curves',
                       return_periods=builder.return_periods,
                       loss_types=oq.loss_names, **aggby, units=units)
        set_rlzs_stats(self.datastore, 'tot_curves',
                       return_periods=builder.return_periods,
                       loss_types=oq.loss_names, **aggby, units=units)
        set_rlzs_stats(self.datastore, 'tot_losses',
                       loss_types=oq.loss_names, **aggby, units=units)
        if oq.aggregate_by:
            set_rlzs_stats(self.datastore, 'agg_curves',
                           return_periods=builder.return_periods,
                           loss_types=oq.loss_names, **aggby, units=units)
            set_rlzs_stats(self.datastore, 'agg_losses',
                           loss_types=oq.loss_names, **aggby, units=units)
        return 1

    def post_execute(self, dummy):
        """
        Sanity check on tot_losses
        """
        logging.info('Mean portfolio loss\n' +
                     views.view('portfolio_loss', self.datastore))
        logging.info('Sanity check on agg_losses/tot_losses')
        for kind in 'rlzs', 'stats':
            agg = 'agg_losses-' + kind
            tot = 'tot_losses-' + kind
            if agg not in self.datastore:
                return
            if kind == 'rlzs':
                kinds = ['rlz-%d' % rlz for rlz in range(self.R)]
            else:
                kinds = self.oqparam.hazard_stats()
            for l in range(self.L):
                ln = self.oqparam.loss_names[l]
                for r, k in enumerate(kinds):
                    tot_losses = self.datastore[tot][l, r]
                    agg_losses = self.datastore[agg][l, r].sum()
                    if kind == 'rlzs' or k == 'mean':
                        ok = numpy.allclose(agg_losses, tot_losses, rtol=.001)
                        if not ok:
                            logging.warning(
                                'Inconsistent total losses for %s, %s: '
                                '%s != %s', ln, k, agg_losses, tot_losses)

    def get_shape(self, *sizes, aggregate_by=None):
        """
        :returns: a shape (S1, ... SN, T1 ... TN)
        """
        if aggregate_by is None:
            aggregate_by = self.oqparam.aggregate_by
        return self.tagcol.agg_shape(sizes, aggregate_by)
