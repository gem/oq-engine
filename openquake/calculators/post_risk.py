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

from openquake.baselib import general, datastore, parallel, python3compat
from openquake.hazardlib.stats import set_rlzs_stats
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
    eff_time = oq.investigation_time * oq.ses_per_logic_tree_path
    num_events = numpy.bincount(dstore['events']['rlz_id'])
    periods = return_periods or oq.return_periods or scientific.return_periods(
        eff_time, num_events.max())
    return scientific.LossCurvesMapsBuilder(
        oq.conditional_loss_poes, numpy.array(periods),
        loss_dt or oq.loss_dt(), weights, dict(enumerate(num_events)),
        eff_time, oq.risk_investigation_time)


def get_src_loss_table(dstore, L):
    """
    :returns:
        (source_ids, array of losses of shape (Ns, L))
    """
    K = dstore['agg_loss_table'].attrs.get('K', 0)
    alt = dstore.read_df('agg_loss_table', 'agg_id', dict(agg_id=K))
    eids = alt.event_id.to_numpy()
    evs = dstore['events'][:][eids]
    rlz_ids = evs['rlz_id']
    rup_ids = evs['rup_id']
    source_id = python3compat.decode(dstore['ruptures']['source_id'][rup_ids])
    w = dstore['weights'][:]
    acc = general.AccumDict(accum=numpy.zeros(L, F32))
    del alt['event_id']
    all_losses = numpy.array(alt)
    for source_id, rlz_id, losses in zip(source_id, rlz_ids, all_losses):
        acc[source_id] += losses * w[rlz_id]
    return zip(*sorted(acc.items()))


def post_risk(builder, kr_losses, monitor):
    """
    :returns: dictionary kr -> L loss curves
    """
    res = {}
    for k, r, losses in kr_losses:
        res[k, r] = builder.build_curves(losses, r)
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
            self.reaggreate = oq.aggregate_by != aggby
            if self.reaggreate:
                self.num_tags = dict(
                    zip(aggby, assetcol.tagcol.agg_shape(aggby)))
        else:
            assetcol = ds['assetcol']
            self.aggkey = assetcol.tagcol.get_aggkey(oq.aggregate_by)
        self.L = len(oq.loss_names)
        size = general.humansize(ds.getsize('agg_loss_table'))
        logging.info('Stored %s in the agg_loss_table', size)

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
        alt_df = self.datastore.read_df('agg_loss_table')
        if self.reaggreate:
            idxs = numpy.concatenate([
                reagg_idxs(self.num_tags, oq.aggregate_by),
                numpy.array([K], int)])
            alt_df['agg_id'] = idxs[alt_df['agg_id'].to_numpy()]
            alt_df = alt_df.groupby(['event_id', 'agg_id']).sum().reset_index()
        alt_df['rlz_id'] = rlz_id[alt_df.event_id.to_numpy()]
        units = self.datastore['cost_calculator'].get_units(oq.loss_names)
        dist = ('no' if os.environ.get('OQ_DISTRIBUTE') == 'no'
                else 'processpool')  # use only the local cores
        smap = parallel.Starmap(post_risk, h5=self.datastore.hdf5,
                                distribute=dist)
        # producing concurrent_tasks/2 = num_cores tasks
        blocksize = int(numpy.ceil(
            (K + 1) * self.R / (oq.concurrent_tasks // 2 or 1)))
        kr_losses = []
        agg_losses = numpy.zeros((K + 1, self.R, self.L), F32)
        agg_curves = numpy.zeros((K + 1, self.R, self.L, P), F32)
        gb = alt_df.groupby([alt_df.agg_id, alt_df.rlz_id])
        # NB: in the future we may use multiprocessing.shared_memory
        for (k, r), df in gb:
            arr = numpy.zeros((self.L, len(df)), F32)
            for lni, ln in enumerate(oq.loss_names):
                arr[lni] = df[ln].to_numpy()
            agg_losses[k, r] = arr.sum(axis=1)
            kr_losses.append((k, r, arr))
            if len(kr_losses) >= blocksize:
                size = sum(ls.nbytes for k, r, ls in kr_losses)
                logging.info('Sending %s of losses',
                             general.humansize(size))
                smap.submit((builder, kr_losses))
                kr_losses[:] = []
        if kr_losses:
            smap.submit((builder, kr_losses))
        for (k, r), curve in smap.reduce().items():
            agg_curves[k, r] = curve
        self.datastore['agg_losses-rlzs'] = agg_losses * oq.ses_ratio
        set_rlzs_stats(self.datastore, 'agg_losses',
                       agg_id=K + 1, loss_types=oq.loss_names, units=units)
        self.datastore['agg_curves-rlzs'] = agg_curves
        set_rlzs_stats(self.datastore, 'agg_curves',
                       agg_id=K + 1, lti=self.L,
                       return_period=builder.return_periods,
                       units=units)
        return 1

    def post_execute(self, dummy):
        """
        Sanity check on tot_losses
        """
        logging.info('Total portfolio loss\n' +
                     views.view('portfolio_loss', self.datastore))
        if not self.aggkey:
            return
        logging.info('Sanity check on agg_losses')
        for kind in 'rlzs', 'stats':
            agg = 'agg_losses-' + kind
            if agg not in self.datastore:
                return
            if kind == 'rlzs':
                kinds = ['rlz-%d' % rlz for rlz in range(self.R)]
            else:
                kinds = self.oqparam.hazard_stats()
            for l in range(self.L):
                ln = self.oqparam.loss_names[l]
                for r, k in enumerate(kinds):
                    tot_losses = self.datastore[agg][-1, r, l]
                    agg_losses = self.datastore[agg][:-1, r, l].sum()
                    if kind == 'rlzs' or k == 'mean':
                        ok = numpy.allclose(agg_losses, tot_losses, rtol=.001)
                        if not ok:
                            logging.warning(
                                'Inconsistent total losses for %s, %s: '
                                '%s != %s', ln, k, agg_losses, tot_losses)
