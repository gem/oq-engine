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

from django import db
import risklib.api
from openquake.calculators.risk import general
from openquake.utils import tasks, stats
from openquake import logs
from openquake.calculators import base


@tasks.oqtask
@stats.count_progress('r')
def scenario_damage(job_id, assets, hazard_getter, hazard_id,
                    fragility_model, fragility_functions, imt):
    """
    Celery task for the scenario damage risk calculator.

    :param job_id: the id of the current `:class:openquake.db.models.OqJob`
    :param assets: the list of `:class:risklib.scientific.Asset`
    instances considered
    :param hazard_getter: the name of an hazard getter to be used
    :param hazard_id: the hazard output id
    :param seed: the seed used to initialize the rng
    ...
    """

    hazard_getter = general.hazard_getter(hazard_getter, hazard_id, imt)

    calculator = risklib.api.ScenarioDamage(
        fragility_model, fragility_functions)
    aggfractions = None  # TODO: finish this
    for asset in assets:
        output = calculator(asset, hazard_getter(asset.site))
        aggfractions = aggregate([output], aggfractions)

    #losses = None
    #with db.transaction.commit_on_success(using='reslt_writer'):
    #    logs.LOG.debug(
    #        'launching compute_on_assets over %d assets' % len(assets))
    #    for asset_output in api.compute_on_assets(
    #            assets, hazard_getter, calculator):
    #        losses = api.aggregate_losses([asset_output], losses)
    base.signal_task_complete(job_id=job_id, num_items=len(assets),
                              fractions=aggfractions)

scenario_damage.ignore_result = False


class ScenarioDamageRiskCalculator(general.BaseRiskCalculator):
    """
    Scenario Damage Risk Calculator. Computes ...
    """

    #: The core calculation celery task function
    core_calc_task = scenario_damage

    hazard_getter = "GroundMotionScenarioGetter"

    @property
    def hazard_id(self):
        """
        The ID of the :class:`openquake.db.models.Output` from which the
        hazard getter can extract the ground motion fields used by the risk
        calculation
        """
        if not self.rc.hazard_output.is_ground_motion_field():
            raise RuntimeError(
                "The provided hazard output is not a ground motion field")
        return self.rc.hazard_output.id

    def worker_args(self, taxonomy):
        """
        :returns: a fixed list of arguments that a calculator may want
        to pass to a worker. In this case the list of fragility_functions
        for the given taxonomy.
        """
        return [self.fragility_model, self.fragility_functions[taxonomy]]

    @property
    def calculator_parameters(self):
        """
        Calculator specific parameters
        """
        return [self.imt]

    def create_outputs(self):
        """
        """
        return []

    def set_risk_models(self):
        self.fragility_model, self.fragility_functions = \
            self.parse_fragility_model()

    def parse_fragility_model(self):
        from risklib.models import input as i
        self.rc.inputs.get(input_type='fragility').path  # will be used
        self.imt = "MMI"
        imls = [7.0, 8.0, 9.0, 10.0, 11.0]
        limit_states = ['minor', 'moderate', 'severe', 'collapse']
        fm = i.FragilityModel('discrete', imls, limit_states)
        ffs = {}

        ffs['RC/DMRF-D/LR'] = i.FragilityFunctionSeq(
            fm, i.FragilityFunctionDiscrete,
            [[0.0, 0.09, 0.56, 0.91, 0.98],
             [0.0, 0.0, 0.04, 0.78, 0.96],
             [0.0, 0.0, 0.0, 0.29, 0.88],
             [0.0, 0.0, 0.0, 0.03, 0.63]])
        ffs['RC/DMRF-D/HR'] = i.FragilityFunctionSeq(
            fm, i.FragilityFunctionDiscrete,
            [[0.0, 0.09, 0.56, 0.92, 0.99],
             [0.0, 0.0, 0.04, 0.79, 0.97],
             [0.0, 0.0, 0.0, 0.3, 0.89],
             [0.0, 0.0, 0.0, 0.04, 0.64]])

        return fm, ffs
