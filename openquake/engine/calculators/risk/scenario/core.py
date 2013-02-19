# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


"""
Core functionality for the scenario risk calculator.
"""
from django import db

import openquake.risklib

from openquake.engine.calculators import base
from openquake.engine.calculators.risk import general
from openquake.engine.utils import tasks, stats
from openquake.engine.db import models


@tasks.oqtask
@stats.count_progress('r')
def scenario(job_id, hazard, seed, vulnerability_function, output_containers,
             asset_correlation):
    """
    Celery task for the scenario damage risk calculator.

    :param job_id: the id of the current
    :class:`openquake.engine.db.models.OqJob`
    :param dict hazard:
      A dictionary mapping IDs of
      :class:`openquake.engine.db.models.Output` (with output_type set
      to 'gmfscenario') to a tuple where the first element is an instance of
      :class:`..hazard_getters.GroundMotionScenarioGetter2`, and the second
      element is the corresponding weight.
    :param seed: the seed used to initialize the rng
    :param output_containers: a dictionary {hazard_id: output_id}
        where output id represents the id of the loss map
    :param asset_correlation: asset correlation coefficient
    """

    calc = openquake.risklib.api.Scenario(
        vulnerability_function, seed, asset_correlation)

    hazard_getter = hazard.values()[0][0]

    assets, ground_motion_values, missings = hazard_getter()

    outputs = calc(assets, ground_motion_values)

    # Risk output container id
    outputs_id = output_containers.values()[0][0]

    with db.transaction.commit_on_success(using='reslt_writer'):
        for i, output in enumerate(outputs):
            general.write_loss_map_data(
                outputs_id, assets[i].asset_ref,
                value=output.mean, std_dev=output.standard_deviation,
                location=assets[i].site)

    base.signal_task_complete(job_id=job_id,
                              num_items=len(assets) + len(missings))


class ScenarioRiskCalculator(general.BaseRiskCalculator):
    """
    Scenario Risk Calculator. Computes a Loss Map,
    for a given set of assets.
    """
    hazard_getter = general.hazard_getters.GroundMotionScenarioGetter

    core_calc_task = scenario

    def hazard_outputs(self, hazard_calculation):
        """
        :returns: the single hazard output associated to
        `hazard_calculation`
        """

        # in scenario hazard calculation we do not have hazard logic
        # tree realizations, and we have only one output
        return hazard_calculation.oqjob_set.filter(status="complete").latest(
            'last_update').output_set.get(
                output_type='gmf_scenario')

    def hazard_output(self, output, assets):
        """
        :param output: an instance of
          :class:`openquake.engine.db.models.Output` having
          output_type == gmf_scenario
        :param assets: a list of assets
        :returns: a tuple with an instance of an hazard getter for the
        specified hazard output and assets
        """
        if output.output_type != 'gmf_scenario':
            raise RuntimeError(
                "The provided hazard output is not a ground motion field: %s"
                % output.output_type)
        return (self.hazard_getter(
            output.id, self.imt, assets,
            self.rc.get_hazard_maximum_distance()),
            1)

    @property
    def calculator_parameters(self):
        """
        Provides calculator specific params
        in a list format where first value
        represents the intensity measure
        type and the second one the asset
        correlation value.
        """

        return [self.rc.asset_correlation or 0]

    def create_outputs(self, hazard_output):
        """
        Create the the output of a ScenarioRisk calculator
        which is a LossMap.
        """

        return [models.LossMap.objects.create(
                output=models.Output.objects.create_output(
                    self.job, "Loss Map", "loss_map"),
                hazard_output=hazard_output).id]
