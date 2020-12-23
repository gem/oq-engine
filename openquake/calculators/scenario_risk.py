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

import numpy

from openquake.baselib import general
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.risklib import scientific, riskinput
from openquake.calculators import base, post_risk

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
    result = dict(avg=[], alt=param['alt'])
    for ri in riskinputs:
        for out in ri.gen_outputs(crmodel, monitor, param['tempname']):
            num_events = param['num_events'][out.rlzi]
            param['alt'].aggregate(
                out, param['minimum_asset_loss'], param['aggregate_by'])
            # NB: after the aggregation out contains losses, not loss ratios
            for l, loss_type in enumerate(crmodel.loss_types):
                losses = out[loss_type]
                if numpy.product(losses.shape) == 0:  # happens for all NaNs
                    continue
                avg = numpy.zeros(len(ri.assets), F64)
                for a, asset in enumerate(ri.assets):
                    aid = asset['ordinal']
                    avg[a] = losses.sum() / num_events
                    result['avg'].append((l, out.rlzi, aid, avg[a]))
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
        self.param['aggregate_by'] = oq.aggregate_by
        # assuming the weights are the same for all IMTs
        try:
            self.param['weights'] = self.datastore['weights'][()]
        except KeyError:
            self.param['weights'] = [1 / self.R for _ in range(self.R)]
        self.rlzs = self.datastore['events']['rlz_id']
        self.param['num_events'] = numpy.bincount(self.rlzs)  # events by rlz
        aggkey = self.assetcol.tagcol.get_aggkey(oq.aggregate_by)
        self.param['alt'] = scientific.AggLossTable.new(
            aggkey, oq.loss_names, sec_losses=[])

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        oq = self.oqparam
        L = len(oq.loss_names)
        with self.monitor('saving outputs'):
            A = len(self.assetcol)
            # avg losses
            # must be 32 bit otherwise export losses_by_asset will break
            # the QGIS test for ScenarioRisk
            losses_by_asset = numpy.zeros((A, self.R, L), F32)
            for (l, r, aid, avg) in result['avg']:
                losses_by_asset[aid, r, l] = avg

            self.datastore['avg_losses-rlzs'] = losses_by_asset
            set_rlzs_stats(self.datastore, 'avg_losses',
                           asset_id=self.assetcol['id'],
                           loss_type=self.oqparam.loss_names)

            # agg loss table
            out = general.AccumDict(accum=[])  # col -> values
            for eid, arr in result['alt'].items():
                for k, vals in enumerate(arr):  # arr has shape K, L
                    if vals.sum() > 0:
                        out['event_id'].append(eid)
                        out['agg_id'].append(k)
                        for l, ln in enumerate(oq.loss_names):
                            out[ln].append(vals[l])
            out['event_id'] = U32(out['event_id'])
            out['agg_id'] = U16(out['agg_id'])
            for ln in oq.loss_names:
                out[ln] = F32(out['agg_id'])
            self.datastore.create_dframe('agg_loss_table', out.items())
        oq.investigation_time = 1
        post_risk.PostRiskCalculator(oq, self.datastore.calc_id).run()
