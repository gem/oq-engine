# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
import numpy

from openquake.hazardlib.stats import set_rlzs_stats
from openquake.risklib import scientific, riskinput
from openquake.calculators import base, views

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64  # higher precision to avoid task order dependency
stat_dt = numpy.dtype([('mean', F64), ('stddev', F64)])


def scenario_risk(riskinputs, param, monitor):
    """
    Core function for a scenario computation.

    :param riskinput:
        a of :class:`openquake.risklib.riskinput.RiskInput` object
    :param param:
        dictionary of extra parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a dictionary {
        'agg': array of shape (E, L, R, 2),
        'avg': list of tuples (lt_idx, rlz_idx, asset_ordinal, statistics)
        }
        where E is the number of simulated events, L the number of loss types,
        R the number of realizations  and statistics is an array of shape
        (n, R, 4), with n the number of assets in the current riskinput object
    """
    crmodel = monitor.read('crmodel')
    E = param['E']
    L = len(crmodel.loss_types)
    result = dict(agg=numpy.zeros((E, L), F64), avg=[])
    for ri in riskinputs:
        for out in ri.gen_outputs(crmodel, monitor, param['tempname']):
            r = out.rlzi
            num_events = param['num_events'][r]
            for l, loss_type in enumerate(crmodel.loss_types):
                losses = out[loss_type]
                if numpy.product(losses.shape) == 0:  # happens for all NaNs
                    continue
                mal = param['minimum_asset_loss'][loss_type]
                avg = numpy.zeros(len(ri.assets), F64)
                for a, asset in enumerate(ri.assets):
                    ok = losses[a] >= mal  # shape E'
                    okeids = out.eids[ok]
                    oklosses = losses[a, ok]
                    aid = asset['ordinal']
                    avg[a] = oklosses.sum() / num_events
                    result['avg'].append((l, r, aid, avg[a]))
                    result['agg'][okeids, l] += oklosses
    return result


@base.calculators.add('scenario_risk')
class ScenarioRiskCalculator(base.RiskCalculator):
    """
    Run a scenario risk calculation
    """
    core_task = scenario_risk
    is_stochastic = True
    precalc = 'scenario'
    accept_precalc = ['scenario']

    def pre_execute(self):
        """
        Compute the GMFs, build the epsilons, the riskinputs, and a dictionary
        with the unit of measure, used in the export phase.
        """
        oq = self.oqparam
        super().pre_execute()
        self.assetcol = self.datastore['assetcol']
        E = oq.number_of_ground_motion_fields * self.R
        self.riskinputs = self.build_riskinputs('gmf')
        self.param['tempname'] = riskinput.cache_epsilons(
            self.datastore, oq, self.assetcol, self.crmodel, E)
        self.param['E'] = E
        # assuming the weights are the same for all IMTs
        try:
            self.param['weights'] = self.datastore['weights'][()]
        except KeyError:
            self.param['weights'] = [1 / self.R for _ in range(self.R)]
        self.rlzs = self.datastore['events']['rlz_id']
        self.param['num_events'] = numpy.bincount(self.rlzs)  # events by rlz

    def combine(self, acc, res):
        """
        Combine the outputs from scenario_risk
        """
        if res is None:
            raise MemoryError('You ran out of memory!')
        return acc + res

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        loss_dt = self.oqparam.loss_dt()
        L = len(loss_dt.names)
        R = self.R
        with self.monitor('saving outputs'):
            A = len(self.assetcol)

            # agg losses
            res = result['agg']
            E, L = res.shape
            agglosses = numpy.zeros((R, L), stat_dt)
            for r in range(R):
                mean, std = scientific.mean_std(res[self.rlzs == r])
                agglosses[r]['mean'] = mean
                agglosses[r]['stddev'] = std

            # avg losses
            losses_by_asset = numpy.zeros((A, R, L), F64)
            for (l, r, aid, avg) in result['avg']:
                losses_by_asset[aid, r, l] = avg

            self.datastore['avg_losses-rlzs'] = losses_by_asset
            set_rlzs_stats(self.datastore, 'avg_losses',
                           asset_id=self.assetcol['id'],
                           loss_type=self.oqparam.loss_names)
            self.datastore['agglosses'] = agglosses

            # losses by event
            self.datastore['agg_loss_table/event_id'] = numpy.arange(E)
            self.datastore['agg_loss_table/agg_id'] = numpy.zeros(E, U16)
            for l, lname in enumerate(self.oqparam.loss_names):
                self.datastore['agg_loss_table/' + lname] = res[:, l]

            cols = ['event_id', 'agg_id'] + self.oqparam.loss_names
            self.datastore.set_attrs(
                'agg_loss_table', __pdcolumns__=' '.join(cols))

            # sanity check
            totlosses = losses_by_asset.sum(axis=0)
            msg = ('%s, rlz=%d: the total loss %s is different from the sum '
                   'of the average losses %s')
            for r in range(R):
                for l, name in enumerate(loss_dt.names):
                    totloss = totlosses[r, l]
                    aggloss = agglosses[r, l]['mean']
                    if not numpy.allclose(totloss, aggloss, rtol=1E-6):
                        logging.warning(msg, name, r, totloss, aggloss)
        logging.info('Mean portfolio loss\n' +
                     views.view('portfolio_loss', self.datastore))
