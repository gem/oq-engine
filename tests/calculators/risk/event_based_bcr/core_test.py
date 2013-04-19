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
from tests.utils import helpers
from tests.utils.helpers import demo_file

from openquake.engine.db import models
from openquake.engine.calculators.risk.event_based_bcr import core


class EventBasedBCRRiskCalculatorTestCase(
        general_test.BaseRiskCalculatorTestCase):
    """
    Integration test for the event based bcr risk calculator
    """

    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            demo_file('event_based_bcr/job.ini'),
            demo_file('event_based_hazard/job.ini'), output_type="gmf")

        self.calculator = core.EventBasedBCRRiskCalculator(self.job)

    def shortDescription(self):
        """
        Use method names instead of docstrings for verbose output
        """
        return None

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

        self.assertEqual(1, models.Output.objects.filter(
            oq_job=self.job).count())

        self.assertEqual(1, models.BCRDistribution.objects.filter(
            output__oq_job=self.job).count())

        self.assertEqual(3, models.BCRDistributionData.objects.filter(
            bcr_distribution__output__oq_job=self.job).count())

    def test_hazard_id(self):
        """
        Test that the hazard output used by the calculator is a
        `openquake.engine.db.models.HazardCurve` object
        """

        outputs = self.calculator.hazard_outputs(
            self.calculator.rc.get_hazard_calculation())

        self.assertEqual(1, outputs.count())

        self.assertEqual(set(["gmf"]), set([o.output_type for o in outputs]))

    def test_create_outputs(self):
        """
        Test that the proper output containers are created
        """

        for hazard_output in self.hazard_outputs:
            self.assertTrue(models.BCRDistribution.objects.filter(
                hazard_output=hazard_output,
                pk=self.calculator.create_outputs(hazard_output)[0]).exists())
