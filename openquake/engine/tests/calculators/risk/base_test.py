# Copyright (c) 2010-2014, GEM Foundation.
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

from openquake.engine.tests.utils import helpers
from openquake.engine.tests.utils.helpers import get_data_path
from openquake.engine.calculators.risk import base, hazard_getters
from openquake.engine.db import models


class BaseRiskCalculatorTestCase(unittest.TestCase):
    """
    An abstract class that just setup a risk job
    """
    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            get_data_path('classical_psha_based_risk/job.ini'),
            get_data_path('simple_fault_demo_hazard/job.ini'))
        models.JobStats.objects.create(oq_job=self.job)
        self.job.is_running = True
        self.job.save()


class FakeWorkflow:
    """Fake Workflow class used in FakeRiskCalculator"""


class FakeRiskCalculator(base.RiskCalculator):
    """
    Fake Risk Calculator. Used to test the base class
    """
    output_builders = []
    getter_class = hazard_getters.GroundMotionGetter

    @staticmethod
    def core(workflow, getter, outputdict, params, monitor):
        return dict(result=1)

    # NB: fake_risk_task returns {job.id: 1}
    def agg_result(self, acc, res):
        newacc = dict((key, acc.get(key, 0) + res[key]) for key in res)
        return newacc

    def get_workflow(self, vulnerability_functions):
        FakeWorkflow.risk_functions = vulnerability_functions
        FakeWorkflow.loss_types = ('structural',)
        return FakeWorkflow()


class RiskCalculatorTestCase(BaseRiskCalculatorTestCase):
    """
    Integration test for the base class supporting the risk
    calculators.
    """
    def setUp(self):
        super(RiskCalculatorTestCase, self).setUp()
        self.calculator = FakeRiskCalculator(self.job)

    def test(self):
        self.calculator.pre_execute()
        # there are 2 assets and 1 taxonomy, two tasks are generated
        self.assertEqual(self.calculator.taxonomies_asset_count, {'VF': 2})

        self.calculator.execute()
        self.assertEqual(self.calculator.acc, {'result': 2})
