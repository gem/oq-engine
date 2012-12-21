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

import mock
from tests.utils import helpers
from tests.calculators.risk import general_test

from openquake.db import models
from openquake.calculators.risk.classical import core as classical


class ClassicalRiskCalculatorTestCase(general_test.BaseRiskCalculatorTestCase):
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

        hazard_id = self.job.risk_calculation.hazard_output.hazardcurve.id

        patch = helpers.patch(
            'openquake.calculators.risk.general.write_loss_curve')
        mocked_writer = patch.start()

        loss_curve_id = mock.Mock()
        exposure_model_id = self.job.risk_calculation.model('exposure').id
        region_constraint = self.job.risk_calculation.region_constraint
        classical.classical(self.job.id,
                            0,
                            assets_per_task=3,
                            exposure_model_id=exposure_model_id,
                            hazard_getter="one_query_per_asset",
                            hazard_id=hazard_id,
                            region_constraint=region_constraint,
                            loss_curve_id=loss_curve_id,
                            loss_map_ids={},
                            lrem_steps_per_interval=3,
                            conditional_loss_poes=[])
        patch.stop()

        # we expect 1 asset being filtered out by the region
        # constraint, so there are only two loss curves to be written
        self.assertEqual(2, mocked_writer.call_count)

    def test_complete_workflow(self):
        """
        Test the complete risk classical calculation workflow and test
        for the presence of the outputs
        """
        self.calculator.pre_execute()

        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()
        self.calculator.execute()

        # 1 loss curve + 3 loss maps
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

        files = self.calculator.export(exports='xml')
        self.assertEqual(4, len(files))

    def calculation_parameters(self):
        """
        Test that the specific calculation parameters are present
        """

        params = self.calculator.calculation_parameters
        for field in ['lrem_steps_per_interval', 'conditional_loss_poes']:
            self.assertTrue(
                field in params)

        self.assertEqual(5, params['lrem_steps_per_interval'])
        self.assertEqual([0.01, 0.02, 0.05], params['conditional_loss_poes'])

    def test_hazard_id(self):
        """
        Test that the hazard output used by the calculator is a
        `openquake.db.models.HazardCurve` object
        """

        self.assertEqual(1,
                         models.HazardCurve.objects.filter(
                             pk=self.calculator.hazard_id).count())
