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

from openquake.risklib import scientific, workflows
from openquake.commonlib import readinput
from openquake.lite.calculators import calculate, calc
from openquake.commonlib.parallel import apply_reduce


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


@calculate.add('scenario_damage', 'scenario_risk')
def run_scenario(oqparam):
    """
    Run a scenario damage or scenario risk computation and returns
    the named of the generated files.
    """
    logging.info('Reading the exposure')
    sitecol, assets_by_site = readinput.get_sitecol_assets(oqparam)

    logging.info('Computing the GMFs')
    gmfs_by_imt = calc.calc_gmfs(oqparam, sitecol)

    logging.info('Preparing the risk input')
    risk_model = readinput.get_risk_model(oqparam)
    risk_inputs = []
    for imt in gmfs_by_imt:
        for site, assets, gmvs in zip(
                sitecol, assets_by_site, gmfs_by_imt[imt]):
            risk_inputs.append(
                workflows.RiskInput(imt, site.id, gmvs, assets))

    if oqparam.calculation_mode == 'scenario_risk':
        # build the epsilon matrix and add the epsilons to the assets
        num_samples = oqparam.number_of_ground_motion_fields
        seed = getattr(oqparam, 'master_seed', 42)
        correlation = getattr(oqparam, 'asset_correlation', 0)
        add_epsilons(assets_by_site, num_samples, seed, correlation)
        taskfunc = core_scenario
    elif oqparam.calculation_mode == 'scenario_damage':
        taskfunc = core_damage
    result = apply_reduce(taskfunc, (risk_inputs, risk_model),
                          agg=calc.add_dicts, acc={},
                          key=lambda ri: ri.imt,
                          weight=lambda ri: ri.weight)
    if oqparam.calculation_mode == 'scenario_risk':
        export()
    elif oqparam.calculation_mode == 'scenario_damage':
        export()



def core_damage(riskinputs, riskmodel):
    """
    Core function for a damage computation.

    :param riskinputs:
        a sequence of :class:`openquake.risklib.workflows.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.workflows.RiskModel` object
    """
    logging.info('Process %d, considering %d risk input(s) of weight %d',
                 os.getpid(), len(riskinputs),
                 sum(ri.weight for ri in riskinputs))
    result = {}  # taxonomy -> aggfractions
    for loss_type, (assets, fractions) in riskmodel.gen_outputs(riskinputs):
        for asset, fraction in zip(assets, fractions):
            result = calc.add_dicts(
                result, {asset.taxonomy: fraction * asset.number})
    return result


def core_scenario(riskinputs, riskmodel):
    """
    Core function for a scenario computation.

    :param riskinputs:
        a sequence of :class:`openquake.risklib.workflows.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.workflows.RiskModel` object
    """
    logging.info('Process %d, considering %d risk input(s) of weight %d',
                 os.getpid(), len(riskinputs),
                 sum(ri.weight for ri in riskinputs))

    result = collections.Counter()  # agg_type, loss_type -> losses
    for loss_type, outs in riskmodel.gen_outputs(riskinputs):
        (_assets, _loss_ratio_matrix, aggregate_losses,
         _insured_loss_matrix, insured_losses) = outs
        result += collections.Counter(
            {('agg', loss_type): aggregate_losses,
             ('ins', loss_type): insured_losses})
    return result
