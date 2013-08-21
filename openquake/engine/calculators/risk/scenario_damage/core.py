#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2010-2013, GEM foundation

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

from openquake.risklib import workflows, calculators

from openquake.engine.calculators.risk import (
    base, hazard_getters, writers, validation, loaders)
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.utils import tasks
from openquake.engine.db import models
from openquake.engine import logs
from openquake.engine.calculators.base import signal_task_complete


@tasks.oqtask
@base.count_progress_risk('r')
def scenario_damage(job_id, units, containers, params):
    """
    Celery task for the scenario damage risk calculator.

    :param int job_id:
      ID of the currently running job
    :param list units:
    :param containers:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (in this case only `LossMap`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    """
    def profile(name):
        return EnginePerformanceMonitor(
            name, job_id, scenario_damage, tracing=True)

    # in scenario damage calculation we have only ONE calculation unit
    unit = units[0]

    # and NO containes
    assert len(containers) == 0

    with db.transaction.commit_on_success(using='reslt_writer'):
        fractions, taxonomy = do_scenario_damage(unit, params, profile)

    num_items = base.get_num_items(units)
    signal_task_complete(
        job_id=job_id, num_items=num_items,
        fractions=fractions, taxonomy=taxonomy)
scenario_damage.ignore_result = False


def do_scenario_damage(unit, params, profile):
    with profile('getting hazard'):
        _hid, assets, ground_motion_values = unit.getter().next()

    if not len(assets):
        logs.LOG.warn("Exit from task as no asset could be processed")
        return None, None

    elif not len(ground_motion_values[0]):
        logs.LOG.warn("Exit from task as no GMVs could be processed")
        return None, None

    with profile('computing risk'):
        fraction_matrix = unit.workflow(ground_motion_values)
        aggfractions = sum(fraction_matrix[i] * asset.number_of_units
                           for i, asset in enumerate(assets))

    with profile('saving damage per assets'):
        writers.damage_distribution(
            assets, fraction_matrix, params.damage_state_ids)

    return aggfractions, assets[0].taxonomy


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

    def __init__(self, job):
        super(ScenarioDamageRiskCalculator, self).__init__(job)
        # let's define a dictionary taxonomy -> fractions
        # updated in task_completed_hook when the fractions per taxonomy
        # becomes available, as computed by the workers
        self.ddpt = {}
        self.damage_state_ids = None

    def calculation_unit(self, loss_type, assets):
        """
        :returns:
          a list of :class:`..base.CalculationUnit` instances
        """
        taxonomy = assets[0].taxonomy
        model = self.risk_models[taxonomy][loss_type]

        # no loss types support at the moment. Use the sentinel key
        # "damage" instead of a loss type for consistency with other
        # methods
        ret = workflows.CalculationUnit(
            loss_type,
            calculators.Damage(model.fragility_functions),
            hazard_getters.GroundMotionValuesGetter(
                self.rc.hazard_outputs(),
                assets,
                self.rc.best_maximum_distance,
                model.imt))
        return ret

    def task_completed_hook(self, message):
        """
        Update the dictionary self.ddpt, i.e. aggregate the damage distribution
        by taxonomy; called every time a block of assets is computed for each
        taxonomy. Fractions and taxonomy are extracted from the message.

        :param dict message:
            The message sent by the worker
        """
        taxonomy = message['taxonomy']
        fractions = message.get('fractions')

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
            self.rc, self.rc.inputs.get(input_type='fragility'))

        self.damage_state_ids = damage_state_ids
        return risk_models

    @property
    def calculator_parameters(self):
        """
        Provides calculator specific params coming from
        :class:`openquake.engine.db.RiskCalculation`
        """

        return base.make_calc_params(damage_state_ids=self.damage_state_ids)
