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

from openquake.db import models
from openquake.calculators.risk.event_based import core as event_based


class EventBasedRiskCalculatorTestCase(
        general_test.BaseRiskCalculatorTestCase):
    """
    Integration test for the event based risk calculator
    """
    def setUp(self):
        self.job, _ = helpers.get_risk_job(
            'event_based_risk/job.ini',
            'event_based_hazard/job.ini', output_type="gmf")

        self.calculator = event_based.EventBasedRiskCalculator(self.job)
        self.calculator.pre_execute()

        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()

    def test_calculator_parameters(self):
        """
        Test that the specific calculation parameters are present
        """

        params_as_list = self.calculator.calculator_parameters
        params = dict(zip(
            ['conditional_loss_poes', 'insured_losses',
             'imt', 'time_span', 'tses', 'loss_curve_resolution',
             'asset_correlation'], params_as_list))

        self.assertEqual(80, params['loss_curve_resolution'])
        self.assertEqual([0.1, 0.2, 0.3], params['conditional_loss_poes'])
        self.assertEqual(True, params['insured_losses'])
        self.assertEqual(250, params['tses'])
        self.assertEqual(50, params['time_span'])
        self.assertEqual('PGA', params['imt'])
        self.assertEqual(None, params['asset_correlation'])

    def test_hazard_id(self):
        """
        Test that the hazard output used by the calculator is a
        `openquake.db.models.HazardCurve` object
        """

        self.assertEqual(1,
                         models.GmfCollection.objects.filter(
                             pk=self.calculator.hazard_id).count())

    def test_imt_validation(self):
        # Test the validation of the imt associated with the
        # vulnerability model that must match the one of the hazard
        # output
        model = self.calculator.rc.model('vulnerability')
        model.imt = 'fake'
        model.save()

        patch = helpers.patch(
            'openquake.calculators.risk.general.store_risk_model')
        patch.start()
        self.assertRaises(RuntimeError, self.calculator.pre_execute)
        patch.stop()

    def test_celery_task(self):
        # Test that the celery task when called properly call the
        # specific method to write loss curves

        patches = [helpers.patch(x) for x in [
            'openquake.calculators.risk.general.write_loss_curve',
            'openquake.calculators.risk.general.update_aggregate_losses']]

        mocked_loss_writer = patches[0].start()
        mocked_agg_loss_writer = patches[1].start()

        event_based.event_based(
            *self.calculator.task_arg_gen(self.calculator.block_size()).next())

        patches[0].stop()
        patches[1].stop()

        # we expect 1 asset being filtered out by the region
        # constraint, so there are only four loss curves (2 of them
        # are insured) to be written
        self.assertEqual(2, mocked_loss_writer.call_count)

        self.assertEqual(1, mocked_agg_loss_writer.call_count)

    def test_complete_workflow(self):
        """
        Test the complete risk classical calculation workflow and test
        for the presence of the outputs
        """
        self.calculator.execute()

        # 1 loss curve + 3 loss maps + 1 aggregate curve + 1 insured curve
        self.assertEqual(6,
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

        files = self.calculator.export(exports='xml')
        self.assertEqual(6, len(files))
