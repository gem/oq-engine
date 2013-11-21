# Copyright (c) 2010-2013, GEM Foundation.
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

import unittest
import mock

from tests.utils import helpers
from tests.utils.helpers import get_data_path
from openquake.engine.calculators.risk import base
from openquake.engine.db import models
from openquake.engine.utils import stats


class BaseRiskCalculatorTestCase(unittest.TestCase):
    """
    An abstract class that just setup a risk job
    """
    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            get_data_path('classical_psha_based_risk/job.ini'),
            get_data_path('simple_fault_demo_hazard/job.ini'))
        models.JobStats.objects.create(oq_job=self.job)

    @property
    def hazard_calculation(self):
        "A shortcut to a the corresponding hazard calculation"
        return self.job.risk_calculation.get_hazard_calculation()


class FakeRiskCalculator(base.RiskCalculator):
    """
    Fake Risk Calculator. Used to test the base class
    """

    celery_task = mock.Mock()

    @property
    def calculation_parameters(self):
        return base.make_calc_params()


class RiskCalculatorTestCase(BaseRiskCalculatorTestCase):
    """
    Integration test for the base class supporting the risk
    calculators.
    """

    def setUp(self):
        super(RiskCalculatorTestCase, self).setUp()
        self.calculator = FakeRiskCalculator(self.job)
