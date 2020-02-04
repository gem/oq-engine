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


def post_ebrisk(dstore, aggkey, monitor):
    """
    :param dstore: a DataStore instance
    :param aggkey: aggregation key
    :param monitor: Monitor instance
    :returns: a dictionary rlzi -> {agg_curves, agg_losses, idx}
    """
    dstore.open('r')
    oq = dstore['oqparam']
    try:
        df = dstore.read_df('event_loss_table/' + aggkey,
                            ['event_id', 'rlzi'])
    except (KeyError, dstore.EmptyDataset):   # no data for this realization
        return {}
    if ',' in aggkey:
        idx = tuple(idx - 1 for idx in ast.literal_eval(aggkey))
    else:
        idx = (int(aggkey) - 1,)
    builder = get_loss_builder(dstore)
    out = {}
    for rlzi, curves, losses in builder.gen_curves_by_rlz(df, oq.ses_ratio):
        out[rlzi] = dict(agg_curves=curves, agg_losses=losses, idx=idx)
    return out


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
            aggby[tagname] = encode(getattr(self.tagcol, tagname)[1:])
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
            aggkeys = list(ds['event_loss_table'])
            ds.swmr_on()
            smap = parallel.Starmap(
                post_ebrisk, [(self.datastore, aggkey) for aggkey in aggkeys],
                h5=self.datastore.hdf5)
        else:
            smap = ()
        # do everything in process since it is really fast
        elt = ds.read_df('losses_by_event', ['event_id', 'rlzi'])
        for r, curves, losses in builder.gen_curves_by_rlz(elt, oq.ses_ratio):
            ds['tot_curves-rlzs'][:, r] = curves  # PL
            ds['tot_losses-rlzs'][:, r] = losses  # L
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
