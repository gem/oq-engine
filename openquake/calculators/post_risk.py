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
from openquake.commonlib import datastore, logs
from openquake.risklib import scientific
from openquake.engine import engine
from openquake.calculators import base, views

U8 = numpy.uint8
F32 = numpy.float32
U16 = numpy.uint16
U32 = numpy.uint32


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


def get_loss_builder(dstore, return_periods=None, loss_dt=None,
                     num_events=None):
    """
    :param dstore: datastore for an event based risk calculation
    :returns: a LossCurvesMapsBuilder instance
    """
    oq = dstore['oqparam']
    weights = dstore['weights'][()]
    try:
        haz_time = dstore['gmf_data'].attrs['effective_time']
    except KeyError:
        haz_time = None
    eff_time = oq.investigation_time * oq.ses_per_logic_tree_path * (
        len(weights) if oq.collect_rlzs else 1)
    if oq.collect_rlzs:
        if haz_time and haz_time != eff_time:
            raise ValueError('The effective time stored in gmf_data is %d, '
                             'which is inconsistent with %d' %
                             (haz_time, eff_time))
        num_events = numpy.array([len(dstore['events'])])
        weights = numpy.ones(1)
    elif num_events is None:
        num_events = numpy.bincount(
            dstore['events']['rlz_id'], minlength=len(weights))
    periods = return_periods or oq.return_periods or scientific.return_periods(
        eff_time, num_events.max())
    return scientific.LossCurvesMapsBuilder(
        oq.conditional_loss_poes, numpy.array(periods),
        loss_dt or oq.loss_dt(), weights, dict(enumerate(num_events)),
        eff_time, oq.risk_investigation_time or oq.investigation_time)


def get_src_loss_table(dstore, L):
    """
    :returns:
        (source_ids, array of losses of shape (Ns, L))
    """
    K = dstore['risk_by_event'].attrs.get('K', 0)
    alt = dstore.read_df('risk_by_event', 'agg_id', dict(agg_id=K))
    eids = alt.event_id.to_numpy()
    evs = dstore['events'][:][eids]
    rlz_ids = evs['rlz_id']
    rup_ids = evs['rup_id']
    source_id = python3compat.decode(dstore['ruptures']['source_id'][rup_ids])
    w = dstore['weights'][:]
    acc = general.AccumDict(accum=numpy.zeros(L, F32))
    for source_id, rlz_id, loss_id, loss in zip(
            source_id, rlz_ids, alt.loss_id.to_numpy(), alt.loss.to_numpy()):
        acc[source_id][loss_id] += loss * w[rlz_id]
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


def build_aggcurves(items, builder):
    """
    :param items: a list of pairs ((agg_id, rlz_id, loss_id), losses)
    :param builder: a :class:`LossCurvesMapsBuilder` instance
    """
    dic = general.AccumDict(accum=[])
    for (agg_id, rlz_id, loss_id), data in items:
        curve = {kind: builder.build_curve(data[kind], rlz_id)
                 for kind in data}
        for p, period in enumerate(builder.return_periods):
            dic['agg_id'].append(agg_id)
            dic['rlz_id'].append(rlz_id)
            dic['loss_id'].append(loss_id)
            dic['return_period'].append(period)
            for kind in data:
                dic[kind].append(curve[kind][p])
    return dic


def store_agg(dstore, rbe_df, num_events):
    """
    Build the aggrisk and aggcurves tables from the risk_by_event table
    """
    oq = dstore['oqparam']
    size = dstore.getsize('risk_by_event')
    logging.info('Building aggrisk from %s of risk_by_event',
                 general.humansize(size))
    rlz_id = dstore['events']['rlz_id']
    if len(num_events) > 1:
        rbe_df['rlz_id'] = rlz_id[rbe_df.event_id.to_numpy()]
    else:
        rbe_df['rlz_id'] = 0
    del rbe_df['event_id']
    aggrisk = general.AccumDict(accum=[])
    columns = [col for col in rbe_df.columns if col not in {
        'event_id', 'agg_id', 'rlz_id', 'loss_id', 'variance'}]
    dmgs = [col for col in columns if col.startswith('dmg_')]
    if dmgs:
        aggnumber = dstore['agg_values']['number']
    gb = rbe_df.groupby(['agg_id', 'rlz_id', 'loss_id'])
    for (agg_id, rlz_id, loss_id), df in gb:
        ne = num_events[rlz_id]
        aggrisk['agg_id'].append(agg_id)
        aggrisk['rlz_id'].append(rlz_id)
        aggrisk['loss_id'].append(loss_id)
        if dmgs:
            # infer the number of buildings in nodamage state
            ndamaged = sum(df[col].sum() for col in dmgs)
            aggrisk['dmg_0'].append(aggnumber[agg_id] - ndamaged / ne)
        for col in columns:
            aggrisk[col].append(df[col].sum() / ne)
    fix_dtypes(aggrisk)
    aggrisk = pandas.DataFrame(aggrisk)
    dstore.create_df(
        'aggrisk', aggrisk, limit_states=' '.join(oq.limit_states))

    loss_kinds = [col for col in columns if not col.startswith('dmg_')]
    if oq.investigation_time and loss_kinds:  # build aggcurves
        logging.info('Building aggcurves')
        builder = get_loss_builder(dstore, num_events=num_events)
        items = []
        for (agg_id, rlz_id, loss_id), df in gb:
            data = {kind: df[kind].to_numpy() for kind in loss_kinds}
            items.append([(agg_id, rlz_id, loss_id), data])
        dic = parallel.Starmap.apply(
            build_aggcurves, (items, builder),
            concurrent_tasks=oq.concurrent_tasks,
            h5=dstore.hdf5).reduce()
        fix_dtypes(dic)
        dstore.create_df('aggcurves', pandas.DataFrame(dic),
                         limit_states=' '.join(oq.limit_states),
                         units=dstore['cost_calculator'].get_units(
                             oq.loss_types))
    return aggrisk


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
            self.aggkey = base.save_agg_values(
                ds, self.assetcol, oq.loss_types, oq.aggregate_by)
            aggby = ds.parent['oqparam'].aggregate_by
            self.reaggreate = aggby and oq.aggregate_by != aggby
            if self.reaggreate:
                self.num_tags = dict(
                    zip(aggby, self.assetcol.tagcol.agg_shape(aggby)))
        else:
            assetcol = ds['assetcol']
            self.aggkey = assetcol.tagcol.get_aggkey(oq.aggregate_by)
        self.L = len(oq.loss_types)
        if self.R > 1:
            self.num_events = numpy.bincount(
                ds['events']['rlz_id'], minlength=self.R)  # events by rlz
        else:
            self.num_events = numpy.array([len(ds['events'])])

    def execute(self):
        oq = self.oqparam
        if oq.investigation_time and oq.return_periods != [0]:
            # setting return_periods = 0 disable loss curves
            eff_time = oq.investigation_time * oq.ses_per_logic_tree_path
            if eff_time < 2:
                logging.warning(
                    'eff_time=%s is too small to compute loss curves',
                    eff_time)
                return
        logging.info('Aggregating by %s', oq.aggregate_by)
        if 'source_info' in self.datastore and 'risk' in oq.calculation_mode:
            logging.info('Building the src_loss_table')
            with self.monitor('src_loss_table', measuremem=True):
                source_ids, losses = get_src_loss_table(self.datastore, self.L)
                self.datastore['src_loss_table'] = losses
                self.datastore.set_shape_descr('src_loss_table',
                                               source=source_ids,
                                               loss_type=oq.loss_types)
        K = len(self.aggkey) if oq.aggregate_by else 0
        rbe_df = self.datastore.read_df('risk_by_event')
        if self.reaggreate:
            idxs = numpy.concatenate([
                reagg_idxs(self.num_tags, oq.aggregate_by),
                numpy.array([K], int)])
            rbe_df['agg_id'] = idxs[rbe_df['agg_id'].to_numpy()]
            rbe_df = rbe_df.groupby(
                ['event_id', 'loss_id', 'agg_id']).sum().reset_index()
        self.aggrisk = store_agg(self.datastore, rbe_df, self.num_events)
        return 1

    def post_execute(self, dummy):
        """
        Sanity checks
        """
        oq = self.oqparam
        # logging.info('Total portfolio loss\n' +
        #              views.view('portfolio_loss', self.datastore))
        if oq.investigation_time and 'risk' in oq.calculation_mode:
            for li, ln in enumerate(self.oqparam.loss_types):
                dloss = views.view('delta_loss:%d' % li, self.datastore)
                if dloss['delta'].mean() > .1:  # more than 10% variation
                    logging.warning(
                        'A big variation in the %s loss curve is expected: try'
                        '\n$ oq show delta_loss:%d %d', ln, li,
                        self.datastore.calc_id)
        logging.info('Sanity check on avg_losses and aggrisk')
        if 'avg_losses-rlzs' in self.datastore:
            url = ('https://docs.openquake.org/oq-engine/advanced/'
                   'addition-is-non-associative.html')
            num_haz_rlzs = len(self.datastore['weights'])
            event_rates = oq.risk_event_rates(self.num_events, num_haz_rlzs)
            K = len(self.aggkey) if oq.aggregate_by else 0
            aggrisk = self.aggrisk[self.aggrisk.agg_id == K]
            avg_losses = self.datastore['avg_losses-rlzs'][:].sum(axis=0)
            # shape (R, L)
            for _, row in aggrisk.iterrows():
                ri, li = int(row.rlz_id), int(row.loss_id)
                # check on the sum of the average losses
                avg = avg_losses[ri, li]
                agg = row.loss * event_rates[ri]
                if not numpy.allclose(avg, agg, rtol=.001):
                    logging.warning(
                        'Due to rounding errors inherent in floating-point '
                        'arithmetic, agg_losses != sum(avg_losses) [%s]: '
                        '%s != %s\nsee %s', oq.loss_types[li], agg, avg, url)


def post_aggregate(calc_id: int, aggregate_by):
    """
    Re-run the postprocessing after an event based risk calculation
    """
    parent = datastore.read(calc_id)
    oqp = parent['oqparam']
    aggby = aggregate_by.split(',')
    for tagname in aggby:
        if tagname not in oqp.aggregate_by:
            raise ValueError('%r not in %s' % (tagname, oqp.aggregate_by))
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
        prc.assetcol = parent['assetcol']
        prc.run(aggregate_by=aggby)
        engine.expose_outputs(prc.datastore)
