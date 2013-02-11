# Copyright (c) 2010-2012, GEM Foundation.
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

from tests.utils import helpers
from tests.calculators.risk import general_test

from openquake.engine.db import models
from openquake.engine.calculators.risk.scenario import core as scenario


class ScenarioRiskCalculatorTestCase(
        general_test.BaseRiskCalculatorTestCase):
    """
    Integration test for the scenario risk calculator
    """

    def setUp(self):
        self.job, _ = helpers.get_risk_job(
            'scenario_risk/job.ini',
            'scenario_hazard/job.ini', output_type="gmf_scenario")

        self.calculator = scenario.ScenarioRiskCalculator(self.job)
        self.calculator.pre_execute()

        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()

    def test_calculator_parameters(self):
        """
        Test that the specific calculation parameters are present
        """

        params = dict(zip(['imt', 'asset_correlation'],
            self.calculator.calculator_parameters))

        self.assertEqual('PGA', params['imt'])
        self.assertEqual(0.0, params['asset_correlation'])
