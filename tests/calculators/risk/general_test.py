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

import unittest
import mock

from tests.utils import helpers
from tests.utils.helpers import demo_file
from openquake.engine.calculators.risk import general as risk
from openquake.engine.db import models
from openquake.engine.utils import stats


class BaseRiskCalculatorTestCase(unittest.TestCase):
    """
    An abstract class that just setup a risk job
    """
    def setUp(self):
        self.job, _ = helpers.get_risk_job(
            demo_file('classical_psha_based_risk/job.ini'),
            demo_file('simple_fault_demo_hazard/job.ini'))

    @property
    def hazard_calculation(self):
        "A shortcut to a the corresponding hazard calculation"
        return self.job.risk_calculation.get_hazard_calculation()

    @property
    def hazard_outputs(self):
        return self.hazard_calculation.oqjob_set.latest(
            'last_update').output_set.filter(output_type='hazard_curve')


class FakeRiskCalculator(risk.BaseRiskCalculator):
    """
    Fake Risk Calculator. Used to test the base class
    """

    celery_task = mock.Mock()

    def hazard_outputs(self, _hc):
        return mock.Mock()

    def create_getter(self, output, imt, assets):
        return mock.Mock()

    @property
    def hazard_getter(self):
        return "hazard_getter"

    @property
    def calculation_parameters(self):
        return []


class RiskCalculatorTestCase(BaseRiskCalculatorTestCase):
    """
    Integration test for the base class supporting the risk
    calculators.
    """

    def setUp(self):
        super(RiskCalculatorTestCase, self).setUp()
        self.calculator = FakeRiskCalculator(self.job)

    def test_store_exposure(self):
        # Test that exposure data and models are properly stored and
        # associated with the calculator

        self.calculator._store_exposure(
            self.calculator.rc.inputs.get(input_type='exposure'))

        actual_model_queryset = models.ExposureModel.objects.filter(
            input__input2rcalc__risk_calculation=self.job.risk_calculation,
            input__input_type="exposure")

        self.assertEqual(1, actual_model_queryset.count())

        model = actual_model_queryset.all()[0]

        actual_asset_queryset = models.ExposureData.objects.filter(
            exposure_model=model)

        self.assertEqual(3, actual_asset_queryset.count())

        asset_refs = [a.asset_ref
                      for a
                      in actual_asset_queryset.all().order_by('asset_ref')]

        self.assertEqual(["a1", "a2", "a3"], asset_refs)

    def test_set_risk_models(self):
        # Test that Vulnerability model and functions are properly
        # stored and associated with the calculator

        self.calculator.taxonomies = {'VF': 10}
        self.calculator.set_risk_models()
        self.assertEqual(1, len(self.calculator.vulnerability_functions))
        self.assertEqual({'VF': 'PGA'}, self.calculator.taxonomies_imts)

    def test_create_outputs(self):
        # Test that the proper output containers are created

        for hazard_output in self.hazard_outputs:
            [loss_curve_id, loss_map_ids] = \
                self.calculator.create_outputs(hazard_output)

            self.assertTrue(
                models.LossCurve.objects.filter(pk=loss_curve_id).exists())

            self.assertEqual(
                sorted(self.job.risk_calculation.conditional_loss_poes),
                sorted(loss_map_ids.keys()))

            for _, map_id in loss_map_ids.items():
                self.assertTrue(models.LossMap.objects.filter(
                    pk=map_id).exists())

    def test_initialize_progress(self):
        # Tests that the progress counter has been initialized
        # properly

        self.calculator.pre_execute()

        total = 2  # expected
        self.calculator._initialize_progress(total)

        self.assertEqual(total, stats.pk_get(
            self.calculator.job.id, "nrisk_total"))
        self.assertEqual(2, total)
        self.assertEqual({'VF': 2}, self.calculator.taxonomies)
        done = stats.pk_get(self.calculator.job.id, "nrisk_done")
        self.assertEqual(0, done)
