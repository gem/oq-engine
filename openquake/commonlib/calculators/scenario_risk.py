#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import collections

from openquake.risklib import scientific
from openquake.baselib import general
from openquake.commonlib import riskmodels, parallel
from openquake.commonlib.calculators import base
from openquake.commonlib.export import export


AggLoss = collections.namedtuple(
    'AggLoss', 'loss_type unit mean stddev')

PerAssetLoss = collections.namedtuple(  # the loss map
    'PerAssetLoss', 'loss_type unit asset_ref mean stddev')


def losses_per_asset(tag, loss_type, assets, means, stddevs,
                     multiply_by_value=True):
    """
    :returns: a dictionary {
    (tag, loss_type): [(asset_ref, mean_value, stddev), ...]}
    """
    lst = []
    for a, m, s in zip(assets, means, stddevs):
        if multiply_by_value:
            # this is really ugly: we should change workflow.Scenario
            # to return the already multiplied insured_loss_matrix;
            # we postpone the fix to the future when the engine
            # scenario_risk calculator will be removed
            v = a.value(loss_type)
        else:
            v = 1
        lst.append((a.id, m * v, s * v))
    return {(tag, loss_type): lst}


@parallel.litetask
def scenario_risk(riskinputs, riskmodel, rlzs_assoc, monitor):
    """
    Core function for a scenario computation.

    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.RiskModel` instance
    :param rlzs_assoc:
        a class:`openquake.commonlib.source.RlzsAssoc` instance
    :param monitor:
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    :returns:
        a dictionary (key_type, loss_type) -> losses where the `key_type` can
        be "agg" (for the aggregate losses) or "ins" (for the insured losses).
    """
    logging.info('Process %d, considering %d risk input(s) of weight %d',
                 os.getpid(), len(riskinputs),
                 sum(ri.weight for ri in riskinputs))
    with monitor:
        result = general.AccumDict()  # agg_type, loss_type -> losses
        for out_by_rlz in riskmodel.gen_outputs(
                riskinputs, rlzs_assoc, monitor):
            for out in out_by_rlz:
                assets = out.assets
                means = out.loss_matrix.mean(axis=1),
                stddevs = out.loss_matrix.std(ddof=1, axis=1)
                result += losses_per_asset(
                    'asset-loss', out.loss_type, assets, means, stddevs)
                result += {('agg', out.loss_type): out.aggregate_losses}

                if out.insured_loss_matrix is not None:
                    means = out.insured_loss_matrix.mean(axis=1),
                    stddevs = out.insured_loss_matrix.std(ddof=1, axis=1)
                    result += losses_per_asset(
                        'asset-ins', out.loss_type, assets, means, stddevs,
                        multiply_by_value=False)
                    result += {('ins', out.loss_type): out.insured_losses}
    return result


@base.calculators.add('scenario_risk')
class ScenarioRiskCalculator(base.RiskCalculator):
    """
    Run a scenario risk calculation
    """
    core_func = scenario_risk
    result_kind = 'losses_by_key'
    hazard_calculator = 'scenario'

    def pre_execute(self):
        """
        Compute the GMFs, build the epsilons, the riskinputs, and a dictionary
        with the unit of measure, used in the export phase.
        """
        base.RiskCalculator.pre_execute(self)
        gmfs = base.get_gmfs(self)

        logging.info('Building the epsilons')
        eps_dict = self.make_eps_dict(
            self.oqparam.number_of_ground_motion_fields)

        self.riskinputs = self.build_riskinputs(gmfs, eps_dict)
        self.unit = {riskmodels.cost_type_to_loss_type(ct['name']): ct['unit']
                     for ct in self.exposure.cost_types}
        self.unit['fatalities'] = 'people'

    def post_execute(self, result):
        """
        Export the aggregate loss curves in CSV format.
        """
        losses = general.AccumDict()
        for key, values in result.iteritems():
            key_type, loss_type = key
            unit = self.unit[loss_type]
            if key_type in ('agg', 'ins'):
                mean, std = scientific.mean_std(values)
                losses += {key_type: [
                    AggLoss(loss_type, unit, mean, std)]}
            else:
                losses += {key_type: [
                    PerAssetLoss(loss_type, unit, *vals) for vals in values]}
        out = {}
        for key_type in losses:
            out += export((key_type, 'csv'),
                          self.oqparam.export_dir, losses[key_type])
        return out
