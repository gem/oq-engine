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
import operator
import collections

import numpy

from openquake.risklib import scientific, workflows
from openquake.commonlib import readinput, riskmodels
from openquake.commonlib.parallel import apply_reduce
from openquake.lite.calculators import calculate, calc, BaseCalculator
from openquake.lite.export import export

DmgDistPerTaxonomy = collections.namedtuple(
    'DmgDistPerTaxonomy', 'taxonomy dmg_state mean stddev')


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


class BaseScenarioCalculator(BaseCalculator):
    def pre_execute(self):
        logging.info('Reading the exposure')
        sitecol, self.assets_by_site = readinput.get_sitecol_assets(
            self.oqparam)

        logging.info('Computing the GMFs')
        gmfs_by_imt = calc.calc_gmfs(self.oqparam, sitecol)

        logging.info('Preparing the risk input')
        self.riskmodel = riskmodels.get_risk_model(self.oqparam)
        self.riskinputs = []
        for imt in gmfs_by_imt:
            for site, assets, gmvs in zip(
                    sitecol, self.assets_by_site, gmfs_by_imt[imt]):
                self.riskinputs.append(
                    workflows.RiskInput(imt, site.id, gmvs, assets))

    def execute(self):
        return apply_reduce(self.core, (self.riskinputs, self.riskmodel),
                            agg=calc.add_dicts, acc={},
                            concurrent_tasks=self.oqparam.concurrent_tasks,
                            key=operator.attrgetter('imt'),
                            weight=operator.attrgetter('weight'))


@calculate.add('scenario_risk')
class ScenarioRiskCalculator(BaseScenarioCalculator):

    def pre_execute(self):
        super(ScenarioRiskCalculator, self).pre_execute()
        # build the epsilon matrix and add the epsilons to the assets
        num_samples = self.oqparam.number_of_ground_motion_fields
        seed = getattr(self.oqparam, 'master_seed', 42)
        correlation = getattr(self.oqparam, 'asset_correlation', 0)
        add_epsilons(self.assets_by_site, num_samples, seed, correlation)

    @staticmethod
    def core(riskinputs, riskmodel):
        """
        Core function for a scenario computation.
        :returns:
            a dictionary ("agg"|"ins", loss_type) -> losses
        """
        logging.info('Process %d, considering %d risk input(s) of weight %d',
                     os.getpid(), len(riskinputs),
                     sum(ri.weight for ri in riskinputs))

        result = {}  # agg_type, loss_type -> losses
        for loss_type, outs in riskmodel.gen_outputs(riskinputs):
            (_assets, _loss_ratio_matrix, aggregate_losses,
             _insured_loss_matrix, insured_losses) = outs
            result = calc.add_dicts(
                result, {('agg', loss_type): aggregate_losses,
                         ('ins', loss_type): insured_losses})
        return result


@calculate.add('scenario_damage')
class ScenarioDamageCalculator(BaseScenarioCalculator):
    """
    """
    @staticmethod
    def core(riskinputs, riskmodel):
        """
        Core function for a damage computation.
        :returns:
            a dictionary (taxonomy, damage_state) -> fractions
        """
        logging.info('Process %d, considering %d risk input(s) of weight %d',
                     os.getpid(), len(riskinputs),
                     sum(ri.weight for ri in riskinputs))
        result = {}  # taxonomy -> aggfractions
        for loss_type, (assets, fractions) in \
                riskmodel.gen_outputs(riskinputs):
            for asset, fraction in zip(assets, fractions):
                result = calc.add_dicts(
                    result, {asset.taxonomy: fraction * asset.number})
        return result

    def post_execute(self, result):
        """
        Export the result as a dmg_per_taxonomy.xml file
        """
        data = []
        dmg_states = map(DmgState, self.riskmodel.damage_states)
        for taxonomy, fractions in result.iteritems():
            means, stds = scientific.mean_std(fractions)
            for dmg_state, mean, std in zip(dmg_states, means, stds):
                data.append(
                    DmgDistPerTaxonomy(taxonomy, dmg_state, mean, std))
        fname = export('dmg_per_taxonomy_xml', self.oqparam.export_dir,
                       self.riskmodel.damage_states, data)
        return [fname]


class DmgState(object):
    def __init__(self, dmg_state):
        self.dmg_state = dmg_state
