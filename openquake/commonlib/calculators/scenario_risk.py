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

import numpy
from openquake.risklib import scientific
from openquake.commonlib import riskmodels, general
from openquake.commonlib.calculators import calculators, base, calc
from openquake.commonlib.export import export


def add_epsilons(assets_by_site, num_samples, seed, correlation):
    """
    Add an attribute named .epsilons to each asset in the assets_by_site
    container.
    """
    assets_by_taxonomy = sum(
        (general.groupby(assets, key=lambda a: a.taxonomy)
         for assets in assets_by_site), {})

    for taxonomy, assets in assets_by_taxonomy.iteritems():
        logging.info('Building (%d, %d) epsilons for taxonomy %s',
                     len(assets), num_samples, taxonomy)
        eps_matrix = scientific.make_epsilons(
            numpy.zeros((len(assets), num_samples)),
            seed, correlation)
        for asset, epsilons in zip(assets, eps_matrix):
            asset.epsilons = epsilons

AggLossCurve = collections.namedtuple(
    'AggLossCurve', 'loss_type unit mean stddev')


def scenario_risk(riskinputs, riskmodel, monitor):
    """
    Core function for a scenario computation.

    :param riskinputs:
        a list of :class:`openquake.risklib.workflows.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.workflows.RiskModel` instance
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
        for loss_type, outs in riskmodel.gen_outputs(riskinputs):
            (_assets, _loss_ratio_matrix, aggregate_losses,
             _insured_loss_matrix, insured_losses) = outs
            result += {('agg', loss_type): aggregate_losses}
            if insured_losses is not None:
                result += {('ins', loss_type): insured_losses}
    return result


@calculators.add('scenario_risk')
class ScenarioRiskCalculator(base.BaseRiskCalculator):
    """
    Run a scenario risk calculation
    """
    core_func = scenario_risk

    def pre_execute(self):
        """
        Compute the GMFs, build the epsilons, the riskinputs, and a dictionary
        with the unit of measure, used in the export phase.
        """
        super(ScenarioRiskCalculator, self).pre_execute()

        logging.info('Computing the GMFs')
        gmfs_by_imt = calc.calc_gmfs(self.oqparam, self.sitecol)

        logging.info('Preparing the risk input')
        self.riskinputs = self.build_riskinputs(gmfs_by_imt)

        # build the epsilon matrix and add the epsilons to the assets
        num_samples = self.oqparam.number_of_ground_motion_fields
        seed = getattr(self.oqparam, 'master_seed', 42)
        correlation = getattr(self.oqparam, 'asset_correlation', 0)
        add_epsilons(self.assets_by_site, num_samples, seed, correlation)
        self.unit = {riskmodels.cost_type_to_loss_type(ct['name']): ct['unit']
                     for ct in self.exposure.cost_types}
        self.unit['fatalities'] = 'people'

    def post_execute(self, result):
        """
        Export the aggregate loss curves in CSV format.
        """
        aggcurves = general.AccumDict()  # key_type -> AggLossCurves
        for (key_type, loss_type), values in result.iteritems():
            mean, std = scientific.mean_std(values)
            curve = AggLossCurve(loss_type, self.unit[loss_type], mean, std)
            aggcurves += {key_type: [curve]}
        out = {}
        for key_type in aggcurves:
            fname = export('%s_loss_csv' % key_type, self.oqparam.export_dir,
                           aggcurves[key_type])
            out[key_type] = fname
        return out
