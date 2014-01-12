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
from openquake.engine.calculators.risk.event_based import core as event_based


class EventBasedRiskCalculatorTestCase(base_test.BaseRiskCalculatorTestCase):
    """
    Integration test for the event based risk calculator
    """
    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            get_data_path('event_based_risk/job.ini'),
            get_data_path('event_based_hazard/job.ini'), output_type="gmf")

        self.calculator = event_based.EventBasedRiskCalculator(self.job)
        models.JobStats.objects.create(oq_job=self.job)
        self.calculator.pre_execute()
        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()

    def test_calculator_parameters(self):
        # Test that the specific calculation parameters are present

        params = self.calculator.calculator_parameters

        self.assertEqual([0.1, 0.2, 0.3], params.conditional_loss_poes)
        self.assertTrue(params.insured_losses)

    def test_celery_task(self):
        # Test that the celery task when called properly call the
        # specific method to write loss curves

        base_path = 'openquake.engine.calculators.risk.writers'
        patches = [
            helpers.patch('%s.loss_curve' % base_path),
            helpers.patch('%s.event_loss_curve' % base_path)]

        try:
            mocked_loss_writer, mocked_event_loss_writer = [
                p.start() for p in patches]

            event_based.event_based(
                *self.calculator.task_arg_gen().next())

            # we expect 1 asset being filtered out by the region
            # constraint, so there are only four loss curves (2 of them
            # are insured) to be written
            self.assertEqual(0, mocked_loss_writer.call_count)
            self.assertEqual(2, mocked_event_loss_writer.call_count)
        finally:
            [p.stop() for p in patches]

    def test_complete_workflow(self):
        # Test the complete risk classical calculation workflow and test
        # for the presence of the outputs
        self.calculator.execute()
        self.calculator.post_process()

        # 1 loss curve + 3 loss maps + 1 aggregate curve + 1 insured
        # curve + 1 event loss table
        self.assertEqual(7,
                         models.Output.objects.filter(oq_job=self.job).count())
        self.assertEqual(1,
                         models.LossCurve.objects.filter(
                             output__oq_job=self.job,
                             insured=False,
                             aggregate=False).count())
        self.assertEqual(1,
                         models.LossCurve.objects.filter(
                             output__oq_job=self.job,
                             insured=True,
                             aggregate=False).count())
        self.assertEqual(1,
                         models.LossCurve.objects.filter(
                             output__oq_job=self.job,
                             insured=False,
                             aggregate=True).count())
        # 2 individual loss curves, 2 insured ones
        self.assertEqual(4,
                         models.LossCurveData.objects.filter(
                             loss_curve__output__oq_job=self.job).count())
        self.assertEqual(1,
                         models.AggregateLossCurveData.objects.filter(
                             loss_curve__output__oq_job=self.job).count())
        self.assertEqual(3,
                         models.LossMap.objects.filter(
                             output__oq_job=self.job).count())
        self.assertEqual(6,
                         models.LossMapData.objects.filter(
                             loss_map__output__oq_job=self.job).count())

        files = self.calculator.export(exports=['xml'])
        self.assertEqual(7, len(files))
