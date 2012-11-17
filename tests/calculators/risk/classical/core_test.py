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

from openquake.db import models as openquake
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
        Test the complete calculation workflow and test for the
        presence of the outputs
        """
        self.calculator.pre_execute()

        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()
        self.calculator.execute()

        self.assertEqual(1,
                         openquake.Output.objects.filter(oq_job=self.job))
        self.assertEqual(1,
                         openquake.LossCurve.objects.filter(
                             output__oq_job=self.job).count())
        self.assertEqual(2,
                         openquake.LossCurveData.objects.filter(
                             losscurve__output__oq_job=self.job).count())

    def test_classical_task(self):
        """
        Test the main calculator task but execute it as a normal
        function
        """

        classical.classical(self.job.id,

