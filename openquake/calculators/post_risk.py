# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019-2020, GEM Foundation
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

import os
import getpass
import logging
import itertools
import numpy
import pandas

from openquake.baselib import general, parallel, python3compat
from openquake.hazardlib.stats import weighted_quantiles
from openquake.risklib import asset, scientific, reinsurance
from openquake.commonlib import datastore, logs
from openquake.calculators import base, views
from openquake.calculators.base import expose_outputs

U8 = numpy.uint8
F32 = numpy.float32
F64 = numpy.float64
U16 = numpy.uint16
U32 = numpy.uint32


class FakeBuilder:
    eff_time = 0.
    pla_factor = None


def fix_investigation_time(oq, dstore):
    """
    If starting from GMFs, fix oq.investigation_time.
    :returns: the number of hazard realizations
    """
    R = len(dstore['weights'])
    if 'gmfs' in oq.inputs and not oq.investigation_time:
        attrs = dstore['gmf_data'].attrs
        inv_time = attrs['investigation_time']
        eff_time = attrs['effective_time']
        if inv_time:  # is zero in scenarios
            oq.investigation_time = inv_time
            oq.ses_per_logic_tree_path = eff_time / (oq.investigation_time * R)
    return R


def save_curve_stats(dstore):
    """
    Save agg_curves-stats
    """
    oq = dstore['oqparam']
    units = dstore['exposure'].cost_calculator.get_units(oq.loss_types)
    try:
        K = len(dstore['agg_keys'])
    except KeyError:
        K = 0
    stats = oq.hazard_stats()
    S = len(stats)
    weights = dstore['weights'][:]
    aggcurves_df = dstore.read_df('aggcurves')
    periods = aggcurves_df.return_period.unique()
    P = len(periods)
    ep_fields = []
    if 'loss' in aggcurves_df:
        ep_fields = ['loss']
    if 'loss_aep' in aggcurves_df:
        ep_fields.append('loss_aep')
    if 'loss_oep' in aggcurves_df:
        ep_fields.append('loss_oep')
    EP = len(ep_fields)
    for lt in oq.ext_loss_types:
        loss_id = scientific.LOSSID[lt]
        out = numpy.zeros((K + 1, S, P, EP))
        aggdf = aggcurves_df[aggcurves_df.loss_id == loss_id]
        for agg_id, df in aggdf.groupby("agg_id"):
            for s, stat in enumerate(stats.values()):
                for p in range(P):
                    for e, ep_field in enumerate(ep_fields):
                        dfp = df[df.return_period == periods[p]]
                        ws = weights[dfp.rlz_id.to_numpy()]
                        ws /= ws.sum()
                        out[agg_id, s, p, e] = stat(dfp[ep_field].to_numpy(),
                                                    ws)
        stat = 'agg_curves-stats/' + lt
        dstore.create_dset(stat, F64, (K + 1, S, P, EP))
        dstore.set_shape_descr(stat, agg_id=K+1, stat=list(stats),
                               return_period=periods, ep_fields=ep_fields)
        dstore.set_attrs(stat, units=units)
        dstore[stat][:] = out


def reagg_idxs(num_tags, tagnames):
    """
    :param num_tags: dictionary tagname -> number of tags with that tagname
    :param tagnames: subset of tagnames of interest
    :returns: T = T1 x ... X TN indices with repetitions

    Reaggregate indices. Consider for instance a case with 3 tagnames,
    taxonomy (4 tags), region (3 tags) and country (2 tags):

    >>> num_tags = dict(taxonomy=4, region=3, country=2)

    There are T = T1 x T2 x T3 = 4 x 3 x 2 = 24 combinations.
    The function will return 24 reaggregated indices with repetions depending
    on the selected subset of tagnames.

    For instance reaggregating by taxonomy and region would give:

    >>> list(reagg_idxs(num_tags, ['taxonomy', 'region']))  # 4x3
    [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11]

    Reaggregating by taxonomy and country would give:

    >>> list(reagg_idxs(num_tags, ['taxonomy', 'country']))  # 4x2
    [0, 1, 0, 1, 0, 1, 2, 3, 2, 3, 2, 3, 4, 5, 4, 5, 4, 5, 6, 7, 6, 7, 6, 7]

    Reaggregating by region and country would give:

    >>> list(reagg_idxs(num_tags, ['region', 'country']))  # 3x2
    [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5]

    Here is an example of single tag aggregation:

    >>> list(reagg_idxs(num_tags, ['taxonomy']))  # 4
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3]
    """
    shape = list(num_tags.values())
    T = numpy.prod(shape)
    arr = numpy.arange(T).reshape(shape)
    ranges = [numpy.arange(n) if t in tagnames else [slice(None)]
              for t, n in num_tags.items()]
    for i, idx in enumerate(itertools.product(*ranges)):
        arr[idx] = i
    return arr.flatten()


def get_loss_builder(dstore, oq, return_periods=None, loss_dt=None,
                     num_events=None):
    """
    :param dstore: datastore for an event based risk calculation
    :returns: a LossCurvesMapsBuilder instance or a Mock object for scenarios
    """
    assert oq.investigation_time
    weights = dstore['weights'][()]
    haz_time = oq.investigation_time * oq.ses_per_logic_tree_path * (
        len(weights) if oq.collect_rlzs else 1)
    if oq.collect_rlzs:
        try:
            etime = dstore['gmf_data'].attrs['effective_time']
        except KeyError:
            etime = None
        haz_time = (oq.investigation_time * oq.ses_per_logic_tree_path *
                    len(weights))
        if etime and etime != haz_time:
            raise ValueError('The effective time stored in gmf_data is %d, '
                             'which is inconsistent with %d' %
                             (etime, haz_time))
        num_events = numpy.array([len(dstore['events'])])
        weights = numpy.ones(1)
    else:
        haz_time = oq.investigation_time * oq.ses_per_logic_tree_path
    if num_events is None:
        num_events = numpy.bincount(
            dstore['events']['rlz_id'], minlength=len(weights))
    max_events = num_events.max()
    periods = return_periods or oq.return_periods or scientific.return_periods(
        haz_time, max_events)  # in case_master [1, 2, 5, 10]
    if 'post_loss_amplification' in oq.inputs:
        pla_factor = scientific.pla_factor(
            dstore.read_df('post_loss_amplification'))
    else:
        pla_factor = None
    return scientific.LossCurvesMapsBuilder(
        oq.conditional_loss_poes, numpy.array(periods),
        loss_dt or oq.loss_dt(), weights,
        haz_time, oq.risk_investigation_time or oq.investigation_time,
        pla_factor=pla_factor)


def get_src_loss_table(dstore, loss_id):
    """
    :returns:
        (source_ids, array of losses of shape Ns)
    """
    K = dstore['risk_by_event'].attrs.get('K', 0)
    alt = dstore.read_df('risk_by_event', 'agg_id',
                         dict(agg_id=K, loss_id=loss_id))
    if len(alt) == 0:  # no losses for this loss type
        return [], ()

    ws = dstore['weights'][:]
    events = dstore['events'][:]
    ruptures = dstore['ruptures'][:]
    source_id = dstore['source_info']['source_id']
    eids = alt.event_id.to_numpy()
    evs = events[eids]
    rlz_ids = evs['rlz_id']
    srcidx = dict(ruptures[['id', 'source_id']])
    srcids = [srcidx[rup_id] for rup_id in evs['rup_id']]
    srcs = python3compat.decode(source_id[srcids])
    acc = general.AccumDict(accum=0)
    for src, rlz_id, loss in zip(srcs, rlz_ids, alt.loss.to_numpy()):
        acc[src] += loss * ws[rlz_id]
    return zip(*sorted(acc.items()))


def fix_dtype(dic, dtype, names):
    for name in names:
        dic[name] = dtype(dic[name])


def fix_dtypes(dic):
    """
    Fix the dtypes of the given columns inside a dictionary (to be
    called before conversion to a DataFrame)
    """
    fix_dtype(dic, U32, ['agg_id'])
    fix_dtype(dic, U8, ['loss_id'])
    if 'event_id' in dic:
        fix_dtype(dic, U32, ['event_id'])
    if 'rlz_id' in dic:
        fix_dtype(dic, U16, ['rlz_id'])
    if 'return_period' in dic:
        fix_dtype(dic, U32, ['return_period'])
    floatcolumns = [col for col in dic if col not in {
        'agg_id', 'loss_id', 'event_id', 'rlz_id', 'return_period'}]
    fix_dtype(dic, F32, floatcolumns)


def build_aggcurves(items, builder, num_events, aggregate_loss_curves_types, monitor):
    """
    :param items: a list of pairs ((agg_id, rlz_id, loss_id), losses)
    :param builder: a :class:`LossCurvesMapsBuilder` instance
    """
    dic = general.AccumDict(accum=[])
    for (agg_id, rlz_id, loss_id), data in items:
        year = data.pop('year', ())
        curve = {
            col: builder.build_curve(
                # col is 'losses' in the case of consequences
                year, 'loss' if col == 'losses' else col,
                data[col], aggregate_loss_curves_types,
                scientific.LOSSTYPE[loss_id], num_events[rlz_id])
            for col in data}
        for p, period in enumerate(builder.return_periods):
            dic['agg_id'].append(agg_id)
            dic['rlz_id'].append(rlz_id)
            dic['loss_id'].append(loss_id)
            dic['return_period'].append(period)
            for col in data:
                # NB: 'fatalities' in EventBasedDamageTestCase.test_case_15
                for k, c in curve[col].items():
                    dic[k].append(c[p])
    return dic


def get_loss_id(ext_loss_types):
    if 'structural' in ext_loss_types:
        return scientific.LOSSID['structural']
    return scientific.LOSSID[ext_loss_types[0]]


# launch Starmap building the aggcurves and store them
def store_aggcurves(oq, agg_ids, rbe_df, builder, loss_cols,
                    events, num_events, dstore):
    aggtypes = oq.aggregate_loss_curves_types
    logging.info('Building aggcurves')
    units = dstore['exposure'].cost_calculator.get_units(oq.loss_types)
    try:
        year = events['year']
        if len(numpy.unique(year)) == 1:  # there is a single year
            year = ()
    except ValueError:  # missing in case of GMFs from CSV
        year = ()
    items = []
    for agg_id in agg_ids:
        gb = rbe_df[rbe_df.agg_id == agg_id].groupby(['rlz_id', 'loss_id'])
        for (rlz_id, loss_id), df in gb:
            data = {col: df[col].to_numpy() for col in loss_cols}
            if len(year):
                data['year'] = year[df.event_id.to_numpy()]
            items.append([(agg_id, rlz_id, loss_id), data])
    dstore.swmr_on()
    dic = parallel.Starmap.apply(
        build_aggcurves, (items, builder, num_events, aggtypes),
        concurrent_tasks=oq.concurrent_tasks,
        h5=dstore.hdf5).reduce()
    fix_dtypes(dic)
    suffix = {'ep': '', 'aep': '_aep', 'oep': '_oep'}
    ep_fields = ['loss' + suffix[a] for a in aggtypes.split(', ')]
    dstore.create_df('aggcurves', pandas.DataFrame(dic),
                     limit_states=' '.join(oq.limit_states),
                     units=units, ep_fields=ep_fields)


def compute_aggrisk(dstore, oq, rbe_df, num_events, agg_ids):
    """
    Compute the aggrisk DataFrame with columns agg_id, rlz_id, loss_id, loss
    """
    L = len(oq.loss_types)
    weights = dstore['weights'][:]
    if oq.investigation_time:  # event based
        tr = oq.time_ratio  # (risk_invtime / haz_invtime) * num_ses
        if oq.collect_rlzs:  # reduce the time ratio by the number of rlzs
            tr /= len(weights)
    columns = [col for col in rbe_df.columns if col not in {
        'event_id', 'agg_id', 'rlz_id', 'loss_id', 'variance'}]
    if oq.investigation_time is None or all(
            col.startswith('dmg_') for col in columns):
        builder = FakeBuilder()
    else:
        builder = get_loss_builder(dstore, oq, num_events=num_events)
    dmgs = [col for col in columns if col.startswith('dmg_')]
    if dmgs:
        aggnumber = dstore['agg_values']['number']
    acc = general.AccumDict(accum=[])
    quantiles = general.AccumDict(accum=([], []))
    for agg_id in agg_ids:
        gb = rbe_df[rbe_df.agg_id == agg_id].groupby(['rlz_id', 'loss_id'])
        for (rlz_id, loss_id), df in gb:
            ne = num_events[rlz_id]
            acc['agg_id'].append(agg_id)
            acc['rlz_id'].append(rlz_id)
            acc['loss_id'].append(loss_id)
            if dmgs:
                # infer the number of buildings in nodamage state
                ndamaged = sum(df[col].sum() for col in dmgs)
                dmg0 = aggnumber[agg_id] - ndamaged / (ne * L)
                assert dmg0 >= 0, dmg0
                acc['dmg_0'].append(dmg0)
            for col in columns:
                losses = df[col].sort_values().to_numpy()
                sorted_losses, _, eperiods = scientific.fix_losses(
                    losses, ne, builder.eff_time)
                if oq.quantiles and not col.startswith('dmg_'):
                    ls, ws = quantiles[agg_id, loss_id]
                    ls.extend(sorted_losses)
                    ws.extend([weights[rlz_id]] * len(sorted_losses))
                agg = sorted_losses.sum()
                acc[col].append(
                    agg * tr if oq.investigation_time else agg/ne)
                if builder.pla_factor:
                    agg = sorted_losses @ builder.pla_factor(eperiods)
                    acc['pla_' + col].append(
                        agg * tr if oq.investigation_time else agg/ne)
    fix_dtypes(acc)
    aggrisk = pandas.DataFrame(acc)
    out = general.AccumDict(accum=[])
    if quantiles:
        for (agg_id, loss_id), (losses, ws) in quantiles.items():
            qs = weighted_quantiles(oq.quantiles, losses, ws)
            out['agg_id'].append(agg_id)
            out['loss_id'].append(loss_id)
            for q, qvalue in zip(oq.quantiles, qs):
                qstring = ('%.2f' % q).replace('0.', 'q')  # ie. 'q05' or 'q95'
                out[qstring].append(qvalue)
    aggrisk_quantiles = pandas.DataFrame(out)
    return aggrisk, aggrisk_quantiles, columns, builder


# aggcurves are built in parallel, aggrisk sequentially
def build_store_agg(dstore, oq, rbe_df, num_events):
    """
    Build the aggrisk and aggcurves tables from the risk_by_event table
    """
    size = dstore.getsize('risk_by_event')
    logging.info('Building aggrisk from %s of risk_by_event',
                 general.humansize(size))
    rups = len(dstore['ruptures'])
    events = dstore['events'][:]
    rlz_id = events['rlz_id']
    rup_id = events['rup_id']
    if len(num_events) > 1:
        rbe_df['rlz_id'] = rlz_id[rbe_df.event_id.to_numpy()]
    else:
        rbe_df['rlz_id'] = 0

    agg_ids = rbe_df.agg_id.unique()
    K = agg_ids.max()
    T = scientific.LOSSID[oq.total_losses or 'structural']
    logging.info("Performing %d aggregations", len(agg_ids))

    aggrisk, aggrisk_quantiles, columns, builder = compute_aggrisk(
        dstore, oq, rbe_df, num_events, agg_ids)
    dstore.create_df(
        'aggrisk', aggrisk, limit_states=' '.join(oq.limit_states))
    if len(aggrisk_quantiles):
        dstore.create_df('aggrisk_quantiles', aggrisk_quantiles)
    loss_cols = [col for col in columns if not col.startswith('dmg_')]
    for agg_id in agg_ids:
        # build loss_by_event and loss_by_rupture
        if agg_id == K and ('loss' in columns or 'losses' in columns) and rups:
            df = rbe_df[(rbe_df.agg_id == K) & (rbe_df.loss_id == T)].copy()
            if len(df):
                df['rup_id'] = rup_id[df.event_id.to_numpy()]
                if 'losses' in columns:  # for consequences
                    df['loss'] = df['losses']
                lbe_df = df[['event_id', 'loss']].sort_values(
                    'loss',  ascending=False)
                gb = df[['rup_id', 'loss']].groupby('rup_id')
                rbr_df = gb.sum().sort_values('loss', ascending=False)
                dstore.create_df('loss_by_rupture', rbr_df.reset_index())
                dstore.create_df('loss_by_event', lbe_df)
    if oq.investigation_time and loss_cols:
        store_aggcurves(oq, agg_ids, rbe_df, builder, loss_cols, events,
                        num_events, dstore)
    return aggrisk


def build_reinsurance(dstore, oq, num_events):
    """
    Build and store the tables `reinsurance-avg_policy` and
    `reinsurance-avg_portfolio`;
    for event_based, also build the `reinsurance-aggcurves` table.
    """
    size = dstore.getsize('reinsurance-risk_by_event')
    logging.info('Building reinsurance-aggcurves from %s of '
                 'reinsurance-risk_by_event', general.humansize(size))
    if oq.investigation_time:
        tr = oq.time_ratio  # risk_invtime / (haz_invtime * num_ses)
        if oq.collect_rlzs:  # reduce the time ratio by the number of rlzs
            tr /= len(dstore['weights'])
    events = dstore['events'][:]
    rlz_id = events['rlz_id']
    try:
        year = events['year']
        if len(numpy.unique(year)) == 1:  # there is a single year
            year = ()
    except ValueError:  # missing in case of GMFs from CSV
        year = ()
    rbe_df = dstore.read_df('reinsurance-risk_by_event', 'event_id')
    columns = rbe_df.columns
    if len(num_events) > 1:
        rbe_df['rlz_id'] = rlz_id[rbe_df.index.to_numpy()]
    else:
        rbe_df['rlz_id'] = 0
    builder = (get_loss_builder(dstore, oq, num_events=num_events)
               if oq.investigation_time else FakeBuilder())
    avg = general.AccumDict(accum=[])
    dic = general.AccumDict(accum=[])
    for rlzid, df in rbe_df.groupby('rlz_id'):
        ne = num_events[rlzid]
        avg['rlz_id'].append(rlzid)
        for col in columns:
            agg = df[col].sum()
            avg[col].append(agg * tr if oq.investigation_time else agg / ne)
        if oq.investigation_time:
            if len(year):
                years = year[df.index.to_numpy()]
            else:
                years = ()
            curve = {col: builder.build_curve(
                        years, col, df[col].to_numpy(),
                        oq.aggregate_loss_curves_types,
                        'reinsurance', ne)
                     for col in columns}
            for p, period in enumerate(builder.return_periods):
                dic['rlz_id'].append(rlzid)
                dic['return_period'].append(period)
                for col in curve:
                    for k, c in curve[col].items():
                        dic[k].append(c[p])

    cc = dstore['exposure'].cost_calculator
    dstore.create_df('reinsurance-avg_portfolio', pandas.DataFrame(avg),
                     units=cc.get_units(oq.loss_types))
    # aggrisk by policy
    avg = general.AccumDict(accum=[])
    rbp_df = dstore.read_df('reinsurance_by_policy')
    if len(num_events) > 1:
        rbp_df['rlz_id'] = rlz_id[rbp_df.event_id.to_numpy()]
    else:
        rbp_df['rlz_id'] = 0
    columns = [col for col in rbp_df.columns if col not in
               {'event_id', 'policy_id', 'rlz_id'}]
    for (rlz_id, policy_id), df in rbp_df.groupby(['rlz_id', 'policy_id']):
        ne = num_events[rlz_id]
        avg['rlz_id'].append(rlz_id)
        avg['policy_id'].append(policy_id)
        for col in columns:
            agg = df[col].sum()
            avg[col].append(agg * tr if oq.investigation_time else agg / ne)
    dstore.create_df('reinsurance-avg_policy', pandas.DataFrame(avg),
                     units=cc.get_units(oq.loss_types))
    if oq.investigation_time is None:
        return
    dic['return_period'] = F32(dic['return_period'])
    dic['rlz_id'] = U16(dic['rlz_id'])
    dstore.create_df('reinsurance-aggcurves', pandas.DataFrame(dic),
                     units=cc.get_units(oq.loss_types))


@base.calculators.add('post_risk')
class PostRiskCalculator(base.RiskCalculator):
    """
    Compute losses and loss curves starting from an event loss table.
    """
    def pre_execute(self):
        oq = self.oqparam
        ds = self.datastore
        self.reaggreate = False
        if oq.hazard_calculation_id and not ds.parent:
            ds.parent = datastore.read(oq.hazard_calculation_id)
            if not hasattr(self, 'assetcol'):
                self.assetcol = ds.parent['assetcol']
            base.save_agg_values(
                ds, self.assetcol, oq.loss_types, oq.aggregate_by)
            aggby = ds.parent['oqparam'].aggregate_by
            self.reaggreate = (aggby and oq.aggregate_by and
                               set(oq.aggregate_by[0]) < set(aggby[0]))
            if self.reaggreate:
                [names] = aggby
                self.num_tags = dict(
                    zip(names, self.assetcol.tagcol.agg_shape(names)))
        self.L = len(oq.loss_types)
        if self.R > 1:
            self.num_events = numpy.bincount(
                ds['events']['rlz_id'], minlength=self.R)  # events by rlz
        else:
            self.num_events = numpy.array([len(ds['events'])])

    def execute(self):
        oq = self.oqparam
        R = fix_investigation_time(oq, self.datastore)
        if oq.investigation_time:
            eff_time = oq.investigation_time * oq.ses_per_logic_tree_path * R

        if 'reinsurance' in oq.inputs:
            logging.warning('Reinsurance calculations are still experimental')
            self.policy_df = self.datastore.read_df('policy')
            self.treaty_df = self.datastore.read_df('treaty_df')
            # there must be a single loss type (possibly a total type)
            ideduc = self.datastore['assetcol/array']['ideductible'].any()
            if (oq.total_losses or len(oq.loss_types) == 1) and ideduc:
                # claim already computed and present in risk_by_event
                lt = 'claim'
            else:
                # claim to be computed from the policies
                [lt] = oq.inputs['reinsurance']
            loss_id = scientific.LOSSID[lt]
            parent = self.datastore.parent
            if parent and 'risk_by_event' in parent:
                dstore = parent
            else:
                dstore = self.datastore
            ct = oq.concurrent_tasks or 1

            # now aggregate risk_by_event by policy
            allargs = [(dstore, pdf, self.treaty_df, loss_id)
                       for pdf in numpy.array_split(self.policy_df, ct)]
            self.datastore.swmr_on()
            smap = parallel.Starmap(reinsurance.reins_by_policy, allargs,
                                    h5=self.datastore.hdf5)
            rbp = pandas.concat(list(smap))
            if len(rbp) == 0:
                raise ValueError('No data in risk_by_event for %r' % lt)
            rbe = reinsurance.by_event(rbp, self.treaty_df, self._monitor)
            self.datastore.create_df('reinsurance_by_policy', rbp)
            self.datastore.create_df('reinsurance-risk_by_event', rbe)

        if oq.investigation_time and oq.return_periods != [0]:
            # setting return_periods = 0 disable loss curves
            if eff_time < 2:
                logging.warning(
                    'eff_time=%s is too small to compute loss curves',
                    eff_time)
                return
        logging.info('Aggregating by %s', oq.aggregate_by)
        if 'source_info' in self.datastore and 'risk' in oq.calculation_mode:
            logging.info('Building the src_loss_table')
            with self.monitor('src_loss_table', measuremem=True):
                for loss_type in oq.loss_types:
                    source_ids, losses = get_src_loss_table(
                        self.datastore, scientific.LOSSID[loss_type])
                    self.datastore['src_loss_table/' + loss_type] = losses
                    self.datastore.set_shape_descr(
                        'src_loss_table/' + loss_type, source=source_ids)
        K = len(self.datastore['agg_keys']) if oq.aggregate_by else 0
        rbe_df = self.datastore.read_df('risk_by_event')
        if len(rbe_df) == 0:
            logging.warning('The risk_by_event table is empty, perhaps the '
                            'hazard is too small?')
            return 0
        if self.reaggreate:
            idxs = numpy.concatenate([
                reagg_idxs(self.num_tags, oq.aggregate_by[0]),
                numpy.array([K], int)])
            rbe_df['agg_id'] = idxs[rbe_df['agg_id'].to_numpy()]
            rbe_df = rbe_df.groupby(
                ['event_id', 'loss_id', 'agg_id']).sum().reset_index()
        self.aggrisk = build_store_agg(
            self.datastore, oq, rbe_df, self.num_events)
        if 'reinsurance-risk_by_event' in self.datastore:
            build_reinsurance(self.datastore, oq, self.num_events)
        return 1

    def post_execute(self, ok):
        """
        Sanity checks and save agg_curves-stats
        """
        if os.environ.get('OQ_APPLICATION_MODE') == 'ARISTOTLE':
            try:
                self._plot_assets()
            except Exception:
                logging.error('', exc_info=True)

        if not ok:  # the hazard is to small
            return
        oq = self.oqparam
        if 'risk' in oq.calculation_mode:
            self.datastore['oqparam'] = oq
            for ln in self.oqparam.loss_types:
                li = scientific.LOSSID[ln]
                dloss = views.view('delta_loss:%d' % li, self.datastore)
                if dloss['delta'].mean() > .1:  # more than 10% variation
                    logging.warning(
                        'A big variation in the %s losses is expected: try'
                        '\n$ oq show delta_loss:%d %d', ln, li,
                        self.datastore.calc_id)
        logging.info('Sanity check on avg_losses and aggrisk')
        if 'avg_losses-rlzs' in set(self.datastore):
            url = ('https://docs.openquake.org/oq-engine/advanced/'
                   'addition-is-non-associative.html')
            K = len(self.datastore['agg_keys']) if oq.aggregate_by else 0
            aggrisk = self.aggrisk[self.aggrisk.agg_id == K]
            avg_losses = {
                lt: self.datastore['avg_losses-rlzs/' + lt][:].sum(axis=0)
                for lt in oq.loss_types}
            # shape (R, L)
            for _, row in aggrisk.iterrows():
                ri, li = int(row.rlz_id), int(row.loss_id)
                lt = scientific.LOSSTYPE[li]
                if lt not in avg_losses:
                    continue
                # check on the sum of the average losses
                avg = avg_losses[lt][ri]
                agg = row.loss
                if not numpy.allclose(avg, agg, rtol=.1):
                    # a serious discrepancy is an error
                    raise ValueError("agg != sum(avg) [%s]: %s %s" %
                                     (lt, agg, avg))
                if not numpy.allclose(avg, agg, rtol=.001):
                    # a small discrepancy is expected
                    logging.warning(
                        'Due to rounding errors inherent in floating-point '
                        'arithmetic, agg_losses != sum(avg_losses) [%s]: '
                        '%s != %s\nsee %s', lt, agg, avg, url)

        # save agg_curves-stats
        if self.R > 1 and 'aggcurves' in self.datastore:
            save_curve_stats(self.datastore)


def post_aggregate(calc_id: int, aggregate_by):
    """
    Re-run the postprocessing after an event based risk calculation
    """
    parent = datastore.read(calc_id)
    oqp = parent['oqparam']
    aggby = aggregate_by.split(',')
    parent_tags = asset.tagset(oqp.aggregate_by)
    if aggby and not parent_tags:
        raise ValueError('Cannot reaggregate from a parent calculation '
                         'without aggregate_by')
    for tag in aggby:
        if tag not in parent_tags:
            raise ValueError('%r not in %s' % (tag, oqp.aggregate_by[0]))
    dic = dict(
        calculation_mode='reaggregate',
        description=oqp.description + '[aggregate_by=%s]' % aggregate_by,
        user_name=getpass.getuser(), is_running=1, status='executing',
        pid=os.getpid(), hazard_calculation_id=calc_id)
    log = logs.init('job', dic, logging.INFO)
    if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
        os.environ['OQ_DISTRIBUTE'] = 'processpool'
    with log:
        oqp.hazard_calculation_id = parent.calc_id
        parallel.Starmap.init()
        prc = PostRiskCalculator(oqp, log.calc_id)
        prc.run(aggregate_by=[aggby])
        expose_outputs(prc.datastore)
