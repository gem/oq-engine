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

from openquake.risklib import workflows
from openquake.risklib.workflows import RiskModel

from openquake.engine.calculators.risk import (
    base, hazard_getters, writers, validation, loaders)
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.utils import tasks
from openquake.engine.db import models


@tasks.oqtask
def scenario_damage(job_id, risk_model, getters, outputdict, params):
    """
    Celery task for the scenario damage risk calculator.

    :param int job_id:
      ID of the currently running job
    :param risk_model:
      A :class:`openquake.risklib.workflows.RiskModel` instance
    :param getters:
      A list of callable hazard getters
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
    # in scenario damage calculation the only loss_type is 'damage'
    [getter] = getters
    [ffs] = risk_model.vulnerability_functions

    # and NO containes
    assert len(outputdict) == 0
    with db.transaction.commit_on_success(using='job_init'):

        with monitor.copy('getting hazard'):
            ground_motion_values = getter.get_data(ffs.imt)

        with monitor.copy('computing risk'):
            fractions = risk_model.workflow(ground_motion_values)
            aggfractions = sum(fractions[i] * asset.number_of_units
                               for i, asset in enumerate(getter.assets))

        with monitor.copy('saving damage per assets'):
            writers.damage_distribution(
                getter.assets, fractions, params.damage_state_ids)

        return aggfractions, risk_model.taxonomy


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
        self.acc = {}
        self.damage_state_ids = None

    def get_workflow(self, fragility_functions):
        return workflows.Damage(fragility_functions)

    def agg_result(self, acc, task_result):
        """
        Update the dictionary acc, i.e. aggregate the damage distribution
        by taxonomy; called every time a block of assets is computed for each
        taxonomy. Fractions and taxonomy are extracted from task_result

        :param task_result:
            A pair (fractions, taxonomy)
        """
        acc = acc.copy()
        fractions, taxonomy = task_result
        if fractions is not None:
            if taxonomy not in acc:
                acc[taxonomy] = numpy.zeros(fractions.shape)
            acc[taxonomy] += fractions
        return acc

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

        if self.acc:
            models.Output.objects.create_output(
                self.job, "Damage Distribution per Taxonomy",
                "dmg_dist_per_taxonomy")

        tot = None
        for taxonomy, fractions in self.acc.iteritems():
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

    def get_risk_models(self):
        """
        Load fragility model and store damage states
        """
        data, damage_state_ids = loaders.fragility(
            self.rc, self.rc.inputs['fragility'])
        self.damage_state_ids = damage_state_ids
        self.loss_types.add('damage')  # single loss_type
        risk_models = {}
        for taxonomy, ffs in data:
            risk_models[taxonomy] = RiskModel(taxonomy, self.get_workflow(ffs))

        return risk_models

    @property
    def calculator_parameters(self):
        """
        Provides calculator specific params coming from
        :class:`openquake.engine.db.RiskCalculation`
        """

        return base.make_calc_params(damage_state_ids=self.damage_state_ids)
