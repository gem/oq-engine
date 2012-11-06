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


from tests.utils import helpers
from openquake.calculators.risk import general as risk
from openquake.db import models as openquake


class BaseRiskCalculatorTestCase(unittest.TestCase):
    """
    Integration test for the base class supporting the risk
    calculators
    """
    def setUp(self):
        cfg = helpers.demo_file(
            'classical_psha_based_risk/job.ini')
        self.job = helpers.get_risk_job(cfg)

        self.base_calculator = risk.BaseRiskCalculator(self.job)

    def test_store_exposure(self):
        """
        Test that exposure data and models are properly stored and
        associated with the calculator
        """
        self.base_calculator._store_exposure()

        actual_model_queryset = openquake.ExposureModel.objects.filter(
            input__input2rcalc__risk_calculation=self.job.risk_calculation,
            input__input_type="exposure")

        self.assertEqual(1, actual_model_queryset.count())

        model = actual_model_queryset.all()[0]

        actual_asset_queryset = openquake.ExposureData.objects.filter(
            exposure_model=model)

        self.assertEqual(1, actual_asset_queryset.count())

        asset = actual_asset_queryset.all()[0]

        self.assertEqual("a1", asset.asset_ref)

    def test_store_risk_model(self):
        """
        Test that Vulnerability model and functions are properly
        stored and associated with the calculator
        """

        [vulnerability_input] = openquake.inputs4rcalc(
            self.job.risk_calculation, input_type='vulnerability')

        self.base_calculator.store_risk_model()

        actual_model_queryset = openquake.VulnerabilityModel.objects.filter(
            input=vulnerability_input)
        self.assertEqual(1, actual_model_queryset.count())

        model = actual_model_queryset.all()[0]

        self.assertEqual("QA_test1", model.name)

        self.assertEqual(1, model.vulnerabilityfunction_set.count())

    def test_create_outputs(self):
        """
        Test that exposure data and models are properly stored and
        associated with the calculator
        """

        outputs = self.base_calculator.create_outputs()

        self.assertTrue('loss_curve' in outputs)
        self.assertTrue(openquake.LossCurve.objects.filter(
            pk=outputs['loss_curve']).exists())
