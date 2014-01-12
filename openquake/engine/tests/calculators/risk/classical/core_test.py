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
from openquake.engine.tests.calculators.risk import base_test

from openquake.engine.calculators.risk.classical import core as classical
from openquake.engine.db import models


class ClassicalRiskCalculatorTestCase(base_test.BaseRiskCalculatorTestCase):
    """
    Integration test for the classical risk calculator
    """
    def setUp(self):
        super(ClassicalRiskCalculatorTestCase, self).setUp()

        self.calculator = classical.ClassicalRiskCalculator(self.job)

    def test_celery_task(self):
        self.calculator.pre_execute()
        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()

        patch = helpers.patch(
            'openquake.engine.calculators.risk.writers.loss_curve')

        try:
            mocked_writer = patch.start()
            classical.classical(*self.calculator.task_arg_gen().next())
        finally:
            patch.stop()

        self.assertEqual(1, mocked_writer.call_count)

    def test_complete_workflow(self):
        # Test the complete risk classical calculation workflow and test
        # for the presence of the outputs

        self.calculator.pre_execute()

        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()
        self.calculator.execute()

        # 1 loss curve + 3 loss maps + 1 mean + 2 quantile
        self.assertEqual(4,
                         models.Output.objects.filter(oq_job=self.job).count())
        self.assertEqual(1,
                         models.LossCurve.objects.filter(
                             output__oq_job=self.job).count())
        self.assertEqual(2,
                         models.LossCurveData.objects.filter(
                             loss_curve__output__oq_job=self.job).count())
        self.assertEqual(3,
                         models.LossMap.objects.filter(
                             output__oq_job=self.job).count())
        self.assertEqual(6,
                         models.LossMapData.objects.filter(
                             loss_map__output__oq_job=self.job).count())

        files = self.calculator.export(exports=['xml'])
        self.assertEqual(4, len(files))
