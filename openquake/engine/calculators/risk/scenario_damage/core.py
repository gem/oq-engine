#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2010-2014, GEM Foundation

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

"""
Core functionality for the scenario_damage risk calculator.
"""

import numpy

from django import db

from openquake.risklib import calculators

from openquake.engine.calculators.risk import (
    base, hazard_getters, writers, validation, loaders)
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.utils import tasks
from openquake.engine.db import models


@tasks.oqtask
def scenario_damage(job_id, risk_models, outputdict, params):
    """
    Celery task for the scenario damage risk calculator.

    :param int job_id:
      ID of the currently running job
    :param list risk_models:
    :param outputdict:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (in this case only `LossMap`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
   :returns:
      A matrix of fractions and a taxonomy string
    """
    monitor = EnginePerformanceMonitor(
        None, job_id, scenario_damage, tracing=True)

    # in scenario damage calculation we have only ONE risk_model
    # since the only loss_type is 'damage'
    [risk_model] = risk_models
    [getter] = risk_model.getters

    # and NO containes
    assert len(outputdict) == 0

    with db.transaction.commit_on_success(using='job_init'):
        return do_scenario_damage(
            risk_model.workflow, getter, params, monitor)


def do_scenario_damage(workflow, getter, params, monitor):
    ground_motion_values = getter(monitor.copy('getting hazard'))

    with monitor.copy('computing risk'):
        fraction_matrix = workflow(ground_motion_values)
        aggfractions = sum(fraction_matrix[i] * asset.number_of_units
                           for i, asset in enumerate(getter.assets))

    with monitor.copy('saving damage per assets'):
        writers.damage_distribution(
            getter.assets, fraction_matrix, params.damage_state_ids)

    return aggfractions, getter.assets[0].taxonomy


class ScenarioDamageRiskCalculator(base.RiskCalculator):
    """
    Scenario Damage Risk Calculator. Computes four kinds of damage
    distributions: per asset, per taxonomy, total and collapse map.

    :attr dict fragility_functions:
        A dictionary of dictionary mapping taxonomy ->
        (limit state -> fragility function) where a fragility function is an
        instance of
        :class:`openquake.risklib.scientific.FragilityFunctionContinuous` or
        :class:`openquake.risklib.scientific.FragilityFunctionDiscrete`.
    """

    #: The core calculation celery task function
    core_calc_task = scenario_damage
    validators = [validation.HazardIMT, validation.EmptyExposure,
                  validation.OrphanTaxonomies,
                  validation.NoRiskModels, validation.RequireScenarioHazard]

    # FIXME. scenario damage calculator does not use output builders
    output_builders = []
    getter_class = hazard_getters.ScenarioGetter

    def __init__(self, job):
        super(ScenarioDamageRiskCalculator, self).__init__(job)
        # let's define a dictionary taxonomy -> fractions
        # updated in task_completed method when the fractions per taxonomy
        # becomes available, as computed by the workers
        self.ddpt = {}
        self.damage_state_ids = None

    def get_workflow(self, taxonomy):
        return calculators.Damage(
            self.risk_models[taxonomy].fragility_functions)

    def task_completed(self, task_result):
        """
        Update the dictionary self.ddpt, i.e. aggregate the damage distribution
        by taxonomy; called every time a block of assets is computed for each
        taxonomy. Fractions and taxonomy are extracted from task_result

        :param task_result:
            A pair (fractions, taxonomy)
        """
        self.log_percent(task_result)
        fractions, taxonomy = task_result

        if fractions is not None:
            if taxonomy not in self.ddpt:
                self.ddpt[taxonomy] = numpy.zeros(fractions.shape)
            self.ddpt[taxonomy] += fractions

    def post_process(self):
        """
        Save the damage distributions by taxonomy and total on the db.
        """

        models.Output.objects.create_output(
            self.job, "Damage Distribution per Asset",
            "dmg_dist_per_asset")

        models.Output.objects.create_output(
            self.job, "Collapse Map per Asset",
            "collapse_map")

        if self.ddpt:
            models.Output.objects.create_output(
                self.job, "Damage Distribution per Taxonomy",
                "dmg_dist_per_taxonomy")

        tot = None
        for taxonomy, fractions in self.ddpt.iteritems():
            writers.damage_distribution_per_taxonomy(
                fractions, self.damage_state_ids, taxonomy)
            if tot is None:  # only the first time
                tot = numpy.zeros(fractions.shape)
            tot += fractions

        if tot is not None:
            models.Output.objects.create_output(
                self.job, "Damage Distribution Total",
                "dmg_dist_total")
            writers.total_damage_distribution(tot, self.damage_state_ids)

    def get_risk_models(self, retrofitted=False):
        """
        Load fragility model and store damage states
        """
        risk_models, damage_state_ids = loaders.fragility(
            self.rc, self.rc.inputs['fragility'])

        self.damage_state_ids = damage_state_ids
        for rm in risk_models.values():
            rm['damage'].loss_type = 'damage'  # single loss_type
        return risk_models

    @property
    def calculator_parameters(self):
        """
        Provides calculator specific params coming from
        :class:`openquake.engine.db.RiskCalculation`
        """

        return base.make_calc_params(damage_state_ids=self.damage_state_ids)
