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

import logging
import numpy

from openquake.baselib import general, parallel, datastore
from openquake.baselib.python3compat import encode
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.risklib import scientific
from openquake.calculators import base

F32 = numpy.float32
U32 = numpy.uint32


def get_loss_builder(dstore, return_periods=None, loss_dt=None):
    """
    :param dstore: datastore for an event based risk calculation
    :returns: a LossCurvesMapsBuilder instance
    """
    oq = dstore['oqparam']
    weights = dstore['weights'][()]
    eff_time = oq.investigation_time * oq.ses_per_logic_tree_path
    num_events = general.countby(dstore['events'][()], 'rlz_id')
    periods = return_periods or oq.return_periods or scientific.return_periods(
        eff_time, max(num_events.values()))
    return scientific.LossCurvesMapsBuilder(
        oq.conditional_loss_poes, numpy.array(periods),
        loss_dt or oq.loss_dt(), weights, num_events,
        eff_time, oq.risk_investigation_time)


def build_loss_tables(dstore):
    """
    Compute the total losses by rupture
    """
    oq = dstore['oqparam']
    R = dstore['csm_info'].get_num_rlzs()
    lbe = dstore['losses_by_event'][()]
    loss = lbe['loss']  # shape (E, L, T...)
    shp = (R,) + lbe.dtype['loss'].shape
    rup_id = dstore['events']['rup_id']
    if len(shp) > 2:
        loss = loss.sum(axis=tuple(range(2, len(shp))))  # shape (E, L)
    losses_by_rupid = general.fast_agg(rup_id[lbe['event_id']], loss)
    lst = [('rup_id', U32)] + [(name, F32) for name in oq.loss_names]
    tbl = numpy.zeros(len(losses_by_rupid), lst)
    tbl['rup_id'] = numpy.arange(len(tbl))
    for li, name in enumerate(oq.loss_names):
        tbl[name] = losses_by_rupid[:, li]
    tbl.sort(order=oq.loss_names[0])
    dstore['rup_loss_table'] = tbl


def post_risk(dstore, rlzi, monitor):
    """
    :param dstore: a DataStore instance
    :param rlzi: realization index
    :param monitor: Monitor instance
    :returns: a dictionary with keys rlzi, agg_losses, tot_curves
    """
    with dstore:
        oq = dstore['oqparam']
        idxs = dstore['losses_by_event']['rlzi'] == rlzi
        alt = dstore['losses_by_event'][idxs]
        builder = get_loss_builder(dstore)
    L = len(oq.loss_names)
    tot = general.AccumDict(accum=numpy.zeros(L))  # eid -> totloss
    for rec in alt:
        tot[rec['event_id']] += rec['loss']
    tot_curves = builder.build_curves(list(tot.values()), rlzi)
    if len(tot_curves) == 0:  # like in test_case_2_sampling
        P = len(builder.return_periods)
        tot_curves = numpy.zeros((P, L), F32)
    res = {'tot_losses': alt['loss'].sum(axis=0) * oq.ses_ratio,
           'tot_curves': tot_curves, 'rlzi': rlzi}
    return res


def post_ebrisk(dstore, rlzi, monitor):
    """
    :param dstore: a DataStore instance
    :param rlzi: realization index
    :param monitor: Monitor instance
    :returns: a dictionary with keys rlzi, agg_curves, agg_losses, tot_curves
    """
    dstore.open('r')
    oq = dstore['oqparam']
    assetcol = dstore['assetcol']
    data = dstore['asset_loss_table/data']
    try:
        ss = dstore['asset_loss_table/indices/rlz-%03d' % rlzi][()]
    except KeyError:   # no data for this realization
        return {}
    builder = get_loss_builder(dstore)
    aggby = oq.aggregate_by
    L = len(oq.loss_names)
    P = len(builder.return_periods)
    tot = general.AccumDict(accum=numpy.zeros(L))  # eid -> loss
    acc = general.AccumDict(accum=general.AccumDict(accum=numpy.zeros(L)))
    shp = assetcol.tagcol.agg_shape((P, L), aggby)
    agg_losses = numpy.zeros(shp[1:], F32)  # shape (L, T...)
    tagidxs = assetcol.array[aggby]
    for start, stop in ss:
        alt = data[start:stop]
        if len(alt) == 0:
            continue
        for rec in alt:
            tot[rec['event_id']] += rec['loss']
        if oq.aggregate_by:
            for rec in general.add_columns(alt, tagidxs, 'asset_id'):
                key = tuple(rec[n] - 1 for n in aggby)
                acc[key][rec['event_id']] += rec['loss']
                agg_losses[(slice(None),) + key] += rec['loss']
    res = {'agg_curves': numpy.zeros(shp, F32)}  # shape (P, L, T...)
    for key, dic in acc.items():
        tup = (slice(None), slice(None)) + key
        res['agg_curves'][tup] = builder.build_curves(list(dic.values()), rlzi)
    res.update(post_risk(dstore, rlzi, monitor))
    if oq.aggregate_by:
        res['agg_losses'] = agg_losses * oq.ses_ratio
    if tot:
        res['app_curves'] = builder.build_curves(list(tot.values()), rlzi)
    return res


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
        oq = self.oqparam
        stats = oq.hazard_stats().items()
        S = len(stats)
        P = len(builder.return_periods)
        loss_types = oq.loss_names
        aggby = {'aggregate_by': aggregate_by}
        for tagname in aggregate_by:
            aggby[tagname] = getattr(self.tagcol, tagname)[1:]
        units = self.datastore['cost_calculator'].get_units(loss_types)
        shp = self.get_shape(self.L, self.R, aggregate_by=aggregate_by)
        # shape L, R, T...
        self.datastore.create_dset(prefix + 'losses-rlzs', F32, shp)
        shp = self.get_shape(P, self.R, self.L, aggregate_by=aggregate_by)
        # shape P, R, L, T...
        shape_descr = ['return_periods', 'rlzs', 'loss_types'] + aggregate_by
        self.datastore.create_dset(prefix + 'curves-rlzs', F32, shp)
        self.datastore.set_attrs(
            prefix + 'curves-rlzs', return_periods=builder.return_periods,
            shape_descr=shape_descr, loss_types=loss_types, units=units,
            rlzs=numpy.arange(self.R), **aggby)
        if self.R > 1:
            shape_descr = (['return_periods', 'stats', 'loss_types'] +
                           aggregate_by)
            shp = self.get_shape(P, S, self.L, aggregate_by=aggregate_by)
            # shape P, S, L, T...
            self.datastore.create_dset(prefix + 'curves-stats', F32, shp)
            self.datastore.set_attrs(
                prefix + 'curves-stats', return_periods=builder.return_periods,
                stats=[encode(name) for (name, func) in stats],
                shape_descr=shape_descr, loss_types=loss_types, units=units,
                **aggby)

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
        logging.info('Building loss tables')
        build_loss_tables(self.datastore)
        shp = self.get_shape(self.L)  # (L, T...)
        text = ' x '.join(
            '%d(%s)' % (n, t) for t, n in zip(oq.aggregate_by, shp[1:]))
        logging.info('Producing %d(loss_types) x %s loss curves', self.L, text)
        builder = get_loss_builder(self.datastore)
        self.build_datasets(builder, oq.aggregate_by, 'agg_')
        self.build_datasets(builder, [], 'app_')
        self.build_datasets(builder, [], 'tot_')
        ds = self.datastore
        if oq.aggregate_by:
            pr = post_ebrisk
            ds.swmr_on()
            smap = parallel.Starmap(
                pr, [(self.datastore, rlzi) for rlzi in range(self.R)],
                h5=self.datastore.hdf5)
        else:
            # do everything in process since it is really fast
            elt = ds.read_df('losses_by_event', ['event_id', 'rlzi'])
            smap = []
            for rlzi, losses_df in elt.groupby('rlzi'):
                losses = numpy.array(losses_df)
                smap.append(
                    {'tot_curves': builder.build_curves(losses, rlzi),
                     'tot_losses': losses.sum(axis=0) * oq.ses_ratio,
                     'rlzi': rlzi})
        for dic in smap:
            if not dic:
                continue
            r = dic['rlzi']
            ds['tot_curves-rlzs'][:, r] = dic['tot_curves']  # PL
            ds['tot_losses-rlzs'][:, r] = dic['tot_losses']  # L
            if oq.aggregate_by:
                ds['agg_curves-rlzs'][:, r] = dic['agg_curves']  # PLT..
                ds['agg_losses-rlzs'][:, r] = dic['agg_losses']  # LT...
            if 'app_curves' in dic:
                ds['app_curves-rlzs'][:, r] = dic['app_curves']  # PL
        if self.R > 1:
            logging.info('Computing aggregate statistics')
            set_rlzs_stats(self.datastore, 'app_curves')
            set_rlzs_stats(self.datastore, 'tot_curves')
            set_rlzs_stats(self.datastore, 'tot_losses')
            if oq.aggregate_by:
                set_rlzs_stats(self.datastore, 'agg_curves')
                set_rlzs_stats(self.datastore, 'agg_losses')

    def post_execute(self, dummy):
        pass

    def get_shape(self, *sizes, aggregate_by=None):
        """
        :returns: a shape (S1, ... SN, T1 ... TN)
        """
        if aggregate_by is None:
            aggregate_by = self.oqparam.aggregate_by
        return self.tagcol.agg_shape(sizes, aggregate_by)
