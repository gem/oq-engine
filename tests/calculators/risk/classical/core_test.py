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

        self.assertEqual(4,
                         models.Output.objects.filter(oq_job=self.job).count())
        self.assertEqual(1,
                         models.LossCurve.objects.filter(
                             output__oq_job=self.job).count())
        self.assertEqual(3,
                         models.LossCurveData.objects.filter(
                             loss_curve__output__oq_job=self.job).count())
        self.assertEqual(9,
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

    def test_create_outputs(self):
        """
        Test that the proper output containers are created
        """

        outputs = self.calculator.create_outputs()

        self.assertTrue('loss_curve_id' in outputs)

        self.assertTrue(models.LossCurve.objects.filter(
            pk=outputs['loss_curve_id']).exists())

        self.assertEqual(
            sorted(self.job.risk_calculation.conditional_loss_poes),
            sorted(outputs['loss_map_ids'].keys()))

        for _, map_id in outputs['loss_map_ids'].items():
            self.assertTrue(models.LossMap.objects.filter(
                pk=map_id).exists())
