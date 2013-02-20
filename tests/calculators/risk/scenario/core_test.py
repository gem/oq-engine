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

        params = dict(zip(['asset_correlation'],
                          self.calculator.calculator_parameters))

        self.assertEqual(0.0, params['asset_correlation'])

    def test_imt_validation(self):
        # Test the validation of the imt associated with the
        # vulnerability model that must match the one of the hazard
        # output.

        patch = helpers.patch(
            'openquake.engine.calculators.risk.general'
            '.BaseRiskCalculator.set_risk_models')
        patch.start()
        self.calculator.imt = 'Hope'
        self.assertRaises(RuntimeError, self.calculator.pre_execute)
        patch.stop()

    def test_celery_task(self):
        # Test that the celery task when called properly call the
        # specific method to write loss map data.

        patch_dbwriter = helpers.patch(
            'openquake.engine.calculators.risk.general.write_loss_map_data',)
        write_lossmap_mock = patch_dbwriter.start()
        scenario.scenario(
            *self.calculator.task_arg_gen(self.calculator.block_size()).next())
        patch_dbwriter.stop()

        self.assertEqual(1, write_lossmap_mock.call_count)

    def test_complete_workflow(self):
        """
        Test the complete risk scenario calculation workflow and test
        for the presence of the outputs
        """
        self.calculator.execute()
        self.calculator.post_process()

        self.assertEqual(
            2, models.Output.objects.filter(oq_job=self.job).count())

        # One Loss map
        self.assertEqual(1, models.LossMap.objects.filter(
                         output__oq_job=self.job).count())

        # One Aggregagte Loss
        self.assertEqual(1, models.AggregateLossData.objects.filter(
                         output__oq_job=self.job).count())

        files = self.calculator.export(exports=True)
        self.assertEqual(2, len(files))
