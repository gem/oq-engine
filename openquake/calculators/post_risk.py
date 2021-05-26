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
import logging
import itertools
import numpy

from openquake.baselib import general, parallel, python3compat
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.commonlib import datastore
from openquake.risklib import scientific
from openquake.calculators import base, views

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


def get_loss_builder(dstore, return_periods=None, loss_dt=None):
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
    else:
        num_events = numpy.bincount(dstore['events']['rlz_id'])
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


def post_risk(builder, krl_losses, monitor):
    """
    :returns: dictionary krl -> loss curve
    """
    res = {}
    for k, r, l, losses in krl_losses:
        res[k, r, l] = builder.build_curve(losses, r)
    return res


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
            assetcol = ds['assetcol']
            self.aggkey = base.save_agg_values(
                ds, assetcol, oq.loss_names, oq.aggregate_by)
            aggby = ds.parent['oqparam'].aggregate_by
            self.reaggreate = aggby and oq.aggregate_by != aggby
            if self.reaggreate:
                self.num_tags = dict(
                    zip(aggby, assetcol.tagcol.agg_shape(aggby)))
        else:
            assetcol = ds['assetcol']
            self.aggkey = assetcol.tagcol.get_aggkey(oq.aggregate_by)
        self.L = len(oq.loss_names)
        size = general.humansize(ds.getsize('risk_by_event'))
        logging.info('Stored %s in the risk_by_event', size)

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
            logging.info('Building the src_loss_table')
            with self.monitor('src_loss_table', measuremem=True):
                source_ids, losses = get_src_loss_table(self.datastore, self.L)
                self.datastore['src_loss_table'] = losses
                self.datastore.set_shape_descr('src_loss_table',
                                               source=source_ids,
                                               loss_type=oq.loss_names)
        builder = get_loss_builder(self.datastore)
        K = len(self.aggkey) if oq.aggregate_by else 0
        P = len(builder.return_periods)
        # do everything in process since it is really fast
        rlz_id = self.datastore['events']['rlz_id']
        if oq.collect_rlzs:
            rlz_id = numpy.zeros_like(rlz_id)
        alt_df = self.datastore.read_df('risk_by_event')
        if self.reaggreate:
            idxs = numpy.concatenate([
                reagg_idxs(self.num_tags, oq.aggregate_by),
                numpy.array([K], int)])
            alt_df['agg_id'] = idxs[alt_df['agg_id'].to_numpy()]
            alt_df = alt_df.groupby(
                ['event_id', 'loss_id', 'agg_id']).sum().reset_index()
        alt_df['rlz_id'] = rlz_id[alt_df.event_id.to_numpy()]
        units = self.datastore['cost_calculator'].get_units(oq.loss_names)
        smap = parallel.Starmap(post_risk, h5=self.datastore.hdf5)
        # producing concurrent_tasks/2 = num_cores tasks
        blocksize = int(numpy.ceil(
            (K + 1) * self.R / (oq.concurrent_tasks // 2 or 1)))
        krl_losses = []
        agg_losses = numpy.zeros((K + 1, self.R, self.L), F32)
        agg_curves = numpy.zeros((K + 1, self.R, self.L, P), F32)
        gb = alt_df.groupby([alt_df.agg_id, alt_df.rlz_id, alt_df.loss_id])
        # NB: in the future we may use multiprocessing.shared_memory
        for (k, r, lni), df in gb:
            agg_losses[k, r, lni] = df.loss.sum()
            krl_losses.append((k, r, lni, df.loss.to_numpy()))
            if len(krl_losses) >= blocksize:
                smap.submit((builder, krl_losses))
                krl_losses[:] = []
        if krl_losses:
            smap.submit((builder, krl_losses))
        for krl, curve in smap.reduce().items():
            agg_curves[krl] = curve
        R = len(self.datastore['weights'])
        time_ratio = oq.time_ratio / R if oq.collect_rlzs else oq.time_ratio
        self.datastore['agg_losses-rlzs'] = agg_losses * time_ratio
        set_rlzs_stats(self.datastore, 'agg_losses',
                       agg_id=K + 1, loss_type=oq.loss_names, units=units)
        self.datastore['agg_curves-rlzs'] = agg_curves
        set_rlzs_stats(self.datastore, 'agg_curves',
                       agg_id=K + 1, lti=self.L,
                       return_period=builder.return_periods,
                       units=units)
        return 1

    def post_execute(self, dummy):
        """
        Sanity checks
        """
        logging.info('Total portfolio loss\n' +
                     views.view('portfolio_loss', self.datastore))
        for li, ln in enumerate(self.oqparam.loss_names):
            dloss = views.view('delta_loss:%d' % li, self.datastore)
            if dloss['delta'].mean() > .1:  # more than 10% variation
                logging.warning(
                    'A big variation in the %s loss curve is expected: try\n'
                    '$ oq show delta_loss:%d %d', ln, li,
                    self.datastore.calc_id)
        if not self.aggkey:
            return
        logging.info('Sanity check on agg_losses')
        for kind in 'rlzs', 'stats':
            avg = 'avg_losses-' + kind
            agg = 'agg_losses-' + kind
            if agg not in self.datastore:
                return
            if kind == 'rlzs':
                kinds = ['rlz-%d' % rlz for rlz in range(self.R)]
            else:
                kinds = self.oqparam.hazard_stats()
            for li in range(self.L):
                ln = self.oqparam.loss_names[li]
                for r, k in enumerate(kinds):
                    tot_losses = self.datastore[agg][-1, r, li]
                    agg_losses = self.datastore[agg][:-1, r, li].sum()
                    if kind == 'rlzs' or k == 'mean':
                        if not numpy.allclose(
                                agg_losses, tot_losses, rtol=.001):
                            logging.warning(
                                'Inconsistent total losses for %s, %s: '
                                '%s != %s', ln, k, agg_losses, tot_losses)
                        try:
                            avg_losses = self.datastore[avg][:, r, li]
                        except KeyError:
                            continue
                        # check on the sum of the average losses
                        sum_losses = avg_losses.sum()
                        if not numpy.allclose(
                                sum_losses, tot_losses, rtol=.001):
                            logging.warning(
                                'Inconsistent sum_losses for %s, %s: '
                                '%s != %s', ln, k, sum_losses, tot_losses)
