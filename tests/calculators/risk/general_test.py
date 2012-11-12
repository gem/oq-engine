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
from openquake.utils import config
from openquake.calculators.risk import general as risk
from openquake.db import models as openquake


class BaseRiskCalculatorTestCase(unittest.TestCase):
    """
    An abstract class that just setup a risk job
    """
    def setUp(self):
        cfg = helpers.demo_file(
            'classical_psha_based_risk/job.ini')
        self.job = helpers.get_risk_job(cfg)


class RiskCalculatorTestCase(BaseRiskCalculatorTestCase):
    """
    Integration test for the base class supporting the risk
    calculators
    """

    def setUp(self):
        super(RiskCalculatorTestCase, self).setUp()
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

        self.assertEqual(3, actual_asset_queryset.count())

        asset_refs = [a.asset_ref for a in actual_asset_queryset.all()]

        self.assertEqual(["a1", "a2", "a3"], asset_refs)

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

    def test_filter_exposure(self):
        """
        Test that the exposure is filtered properly
        """
        model = openquake.ExposureModel.objects.get(
            input__input2rcalc__risk_calculation=self.job.risk_calculation,
            input__input_type="exposure")

        asset_ids = self.base_calculator._filter_exposure(model)
        self.assertEqual(2, len(asset_ids))
        self.assertEqual(
            ["a1", "a2"],
            [a.asset_ref
             for a in openquake.ExposureData.objects.filter(pk__in=asset_ids)])

    def test_pre_execute(self):
        # Most of the pre-execute functionality is implement in other methods.
        # For this test, just make sure each method gets called.
        base_path = ('openquake.calculators.risk.classical.general'
                     '.BaseRiskCalculator')
        patches = (
            helpers.patch(
                '%s.%s' % (base_path, '_store_exposure')),
            helpers.patch(
                '%s.%s' % (base_path, 'store_risk_model')),
            helpers.patch(
                '%s.%s' % (base_path, 'create_outputs')),
            helpers.patch(
                '%s.%s' % (base_path, '_filter_exposure')))

        mocks = [p.start() for p in patches]

        self.base_calculator.pre_execute()

        for i, m in enumerate(mocks):
            self.assertEqual(1, m.call_count)
            m.stop()
            patches[i].stop()

    def test_execute(self):
        """
        Test that the distribute function is called properly
        """

        # TODO (lp) use mock instead of accessing internal fields of
        # the Config object
        config.get_section('risk').cfg['block_size'] = 1

        
