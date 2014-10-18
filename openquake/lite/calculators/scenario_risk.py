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
from openquake.commonlib import readinput, riskmodels, general
from openquake.lite.calculators import calculator, \
    BaseScenarioCalculator, core
from openquake.lite.export import export


def add_epsilons(assets_by_site, num_samples, seed, correlation):
    """
    Add an attribute named .epsilons to each asset in the assets_by_site
    container.
    """
    assets_by_taxonomy = collections.defaultdict(list)
    for assets in assets_by_site:
        for asset in assets:
            assets_by_taxonomy[asset.taxonomy].append(asset)
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


@calculator.add('scenario_risk')
class ScenarioRiskCalculator(BaseScenarioCalculator):
    """
    Run a scenario risk calculation
    """
    def pre_execute(self):
        super(ScenarioRiskCalculator, self).pre_execute()
        # build the epsilon matrix and add the epsilons to the assets
        num_samples = self.oqparam.number_of_ground_motion_fields
        seed = getattr(self.oqparam, 'master_seed', 42)
        correlation = getattr(self.oqparam, 'asset_correlation', 0)
        add_epsilons(self.assets_by_site, num_samples, seed, correlation)
        exposure_metadata = readinput.get_exposure_metadata(
            self.oqparam.inputs['exposure'])
        self.unit = {riskmodels.cost_type_to_loss_type(ct['name']): ct['unit']
                     for ct in exposure_metadata.cost_types}

    def post_execute(self, result):
        fnames = []  # exported files
        aggcurves = general.AccumDict()  # key_type -> AggLossCurves
        for (key_type, loss_type), values in result.iteritems():
            mean, std = scientific.mean_std(values)
            curve = AggLossCurve(loss_type, self.unit[loss_type], mean, std)
            aggcurves += {key_type: [curve]}
        for key_type in aggcurves:
            fname = export('%s_loss_csv' % key_type, self.oqparam.export_dir,
                           aggcurves[key_type])
            fnames.append(fname)
        return fnames


@core(ScenarioRiskCalculator)
def scenario_risk(riskinputs, riskmodel):
    """
    Core function for a scenario computation.
    :returns:
        a dictionary ("agg"|"ins", loss_type) -> losses
    """
    logging.info('Process %d, considering %d risk input(s) of weight %d',
                 os.getpid(), len(riskinputs),
                 sum(ri.weight for ri in riskinputs))

    result = parallel.AccumDict()  # agg_type, loss_type -> losses
    for loss_type, outs in riskmodel.gen_outputs(riskinputs):
        (_assets, _loss_ratio_matrix, aggregate_losses,
         _insured_loss_matrix, insured_losses) = outs
        result += {('agg', loss_type): aggregate_losses}
        if insured_losses is not None:
            result += {('ins', loss_type): insured_losses}
    return result
