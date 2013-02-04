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

import risklib

from openquake.calculators import base
from openquake.calculators.risk import general
from openquake.utils import tasks, stats
from openquake.db import models


@tasks.oqtask
@stats.count_progress('r')
def scenario(job_id, assets, hazard_getter_name, hazard,
        seed, vulnerability_function, output_containers,
        imt, asset_correlation):
    """
    Celery task for the scenario damage risk calculator.

    :param job_id: the id of the current :class:`openquake.db.models.OqJob`
    :param assets: the list of :class:`risklib.scientific.Asset`
        instances considered
    :param hazard_getter: the name of an hazard getter to be used
    :param hazard: the hazard output dictionary
    :param seed: the seed used to initialize the rng
    :param output_containers: a dictionary {hazard_id: output_id}
        of output_type "dmg_dist_per_asset"
    :param imt: the Intensity Measure Type of the ground motion field
    :param asset_correlation: asset correlation coefficient
    """

    calc = risklib.api.Scenario(vulnerability_function,
            seed, asset_correlation)

    hazard_getter = general.hazard_getter(hazard_getter_name,
                    hazard.keys()[0], imt)

    outputs = calc(assets, [hazard_getter(a.site) for a in assets])

    outputs_id = output_containers.values()[0][0]

    with db.transaction.commit_on_success(using='reslt_writer'):
        for i, output in enumerate(outputs):
            general.write_loss_map_data(outputs_id, assets[i].asset_ref,
                value=output.mean, std_dev=output.standard_deviation,
                location=assets[i].site)

    base.signal_task_complete(job_id=job_id, num_items=len(assets))


class ScenarioRiskCalculator(general.BaseRiskCalculator):
    """
    Scenario Risk Calculator. Computes a Loss Map,
    for a given set of assets.
    """

    hazard_getter = "GroundMotionScenarioGetter"

    core_calc_task = scenario

    def hazard_output(self, output):
        """
        Returns hazard output id
        """

        return output.id

    @property
    def calculator_parameters(self):
        """
        Provides calculator specific params
        in a list format where first value
        represents the intensity measure
        type and the second one the asset
        correlation value.
        """

        if self.rc.asset_correlation is None:
            return [self.imt, 0]
        else:
            return [self.imt, self.rc.asset_correlation]

    def create_outputs(self, hazard_output):
        """
        Create the the output of a ScenarioRisk calculator
        which is a LossMap.
        """

        return [models.LossMap.objects.create(
                output=models.Output.objects.create_output(
                                self.job, "Loss Map", "loss_map"),
                                hazard_output=hazard_output).id]
