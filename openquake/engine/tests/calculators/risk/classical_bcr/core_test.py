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

from openquake.engine.tests.calculators.risk import base_test
from openquake.engine.tests.utils import helpers
from openquake.engine.tests.utils.helpers import get_data_path

from openquake.engine.db import models
from openquake.engine.calculators.risk.classical_bcr import (
    core as classical_bcr)


class ClassicalBCRRiskCalculatorTestCase(base_test.BaseRiskCalculatorTestCase):
    """
    Integration test for the classical bcr risk calculator
    """

    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            get_data_path('classical_bcr/job.ini'),
            get_data_path('simple_fault_demo_hazard/job.ini'))

        self.calculator = classical_bcr.ClassicalBCRRiskCalculator(self.job)
        models.JobStats.objects.create(oq_job=self.job)

    def shortDescription(self):
        """
        Use method names instead of docstrings for verbose output
        """
        return None

    def test_complete_workflow(self):
        # Test the complete risk classical calculation workflow and test
        # for the presence of the outputs
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
