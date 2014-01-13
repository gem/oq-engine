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

from openquake.engine.tests.utils import helpers
from openquake.engine.tests.utils.helpers import get_data_path
from openquake.engine.tests.calculators.risk import base_test

from openquake.engine.db import models
from openquake.engine.calculators.risk.scenario import core as scenario


class ScenarioRiskCalculatorTestCase(base_test.BaseRiskCalculatorTestCase):
    """
    Integration test for the scenario risk calculator
    """

    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            get_data_path('scenario_risk/job.ini'),
            get_data_path('scenario_hazard/job.ini'),
            output_type="gmf_scenario")

        self.calculator = scenario.ScenarioRiskCalculator(self.job)
        models.JobStats.objects.create(oq_job=self.job)
        self.calculator.pre_execute()

        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()

    def test_celery_task(self):
        # Test that the celery task when called properly call the
        # specific method to write loss map data.

        patch_dbwriter = helpers.patch(
            'openquake.engine.calculators.risk.writers.loss_map',)
        try:
            write_lossmap_mock = patch_dbwriter.start()
            scenario.scenario(
                *self.calculator.task_arg_gen(
                    self.calculator.block_size()).next())
        finally:
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
        self.assertEqual(1, models.AggregateLoss.objects.filter(
                         output__oq_job=self.job).count())

        files = self.calculator.export(exports=['xml'])
        self.assertEqual(2, len(files))
