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

from openquake.commonlib.readinput import get_risk_model

from openquake.engine.calculators.risk import (
    base, hazard_getters, writers, validation)
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.db import models
from openquake.engine.calculators import calculators


def scenario_damage(workflow, getter, outputdict, params, monitor):
    """
    Celery task for the scenario damage risk calculator.

    :param workflow:
      A :class:`openquake.risklib.workflows.Workflow` instance
    :param getter:
      A HazardGetter instance
    :param outputdict:
      An instance of :class:`..writers.OutputDict` containing
      output container instances (in this case only `LossMap`)
    :param params:
      An instance of :class:`..base.CalcParams` used to compute
      derived outputs
    :param monitor:
      A monitor instance
   :returns:
      A matrix of fractions and a taxonomy string
    """
    [ffs] = workflow.risk_functions

    # and no output containers
    assert len(outputdict) == 0, outputdict
    with monitor('computing risk'):
        assets, fractions = workflow(
            'damage', getter.assets, getter.get_data(), None)
        aggfractions = sum(fractions[i] * asset.number_of_units
                           for i, asset in enumerate(assets))

    with monitor('saving damage per assets'):
        writers.damage_distribution(
            getter.assets, fractions, params.damage_state_ids)

    return {assets[0].taxonomy: aggfractions}


@calculators.add('scenario_damage')
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
    core = staticmethod(scenario_damage)
    validators = [validation.HazardIMT, validation.EmptyExposure,
                  validation.OrphanTaxonomies,
                  validation.NoRiskModels, validation.RequireScenarioHazard]

    # FIXME. scenario damage calculator does not use output builders
    output_builders = []
    getter_class = hazard_getters.GroundMotionGetter

    def __init__(self, job):
        super(ScenarioDamageRiskCalculator, self).__init__(job)
        self.acc = {}  # taxonomy -> fractions
        self.damage_state_ids = None

    @EnginePerformanceMonitor.monitor
    def agg_result(self, acc, task_result):
        """
        Update the dictionary acc, i.e. aggregate the damage distribution
        by taxonomy; called every time a block of assets is computed for each
        taxonomy. Fractions and taxonomy are extracted from task_result

        :param task_result:
            A pair (fractions, taxonomy)
        """
        acc = acc.copy()
        for taxonomy, fractions in task_result.iteritems():
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

    def get_risk_model(self):
        """
        Load fragility model and store damage states
        """
        risk_model = get_risk_model(models.oqparam(self.job.id))

        for lsi, dstate in enumerate(risk_model.damage_states):
            models.DmgState.objects.get_or_create(
                risk_calculation=self.job, dmg_state=dstate, lsi=lsi)

        self.damage_state_ids = [d.id for d in models.DmgState.objects.filter(
            risk_calculation=self.job).order_by('lsi')]

        self.loss_types.add('damage')  # single loss_type
        return risk_model

    @property
    def calculator_parameters(self):
        """
        The specific calculation parameters passed as args to the
        celery task function. A calculator must override this to
        provide custom arguments to its celery task
        """
        oqparam = self.job.get_oqparam()
        oqparam.damage_state_ids = self.damage_state_ids
        return oqparam
