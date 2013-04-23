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

import StringIO
import unittest
import mock

from tests.utils import helpers
from tests.utils.helpers import demo_file
from openquake.engine import engine
from openquake.engine.calculators.risk import general as risk
from openquake.engine.db import models
from openquake.engine.utils import stats


class BaseRiskCalculatorTestCase(unittest.TestCase):
    """
    An abstract class that just setup a risk job
    """
    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            demo_file('classical_psha_based_risk/job.ini'),
            demo_file('simple_fault_demo_hazard/job.ini'))

    @property
    def hazard_calculation(self):
        "A shortcut to a the corresponding hazard calculation"
        return self.job.risk_calculation.get_hazard_calculation()

    @property
    def hazard_outputs(self):
        return self.hazard_calculation.oqjob_set.latest(
            'last_update').output_set.filter(output_type='hazard_curve_multi')


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


class ParseVulnerabilityModelTestCase(unittest.TestCase):

    def setUp(self):
        cfg = helpers.get_data_path('end-to-end-hazard-risk/job_risk.ini')
        self.job = helpers.get_risk_job(cfg)
        self.calc = risk.BaseRiskCalculator(self.job)

    def test_one_taxonomy_many_imts(self):
        # Should raise a ValueError if a vulnerabilityFunctionID is used for
        # multiple IMTs.
        # In this test input, we've defined two functions in separate sets
        # with the same ID and different IMTs.
        vuln_content = StringIO.StringIO("""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
    <vulnerabilityModel>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="fatalities">
            <IML IMT="PGA">0.005 0.007 0.0098 0.0137</IML>
            <discreteVulnerability vulnerabilityFunctionID="A"
                                   probabilisticDistribution="LN">
                <lossRatio>0.01 0.06 0.18 0.36</lossRatio>
                <coefficientsVariation>0.30 0.30 0.30 0.30</coefficientsVariation>
            </discreteVulnerability>
        </discreteVulnerabilitySet>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="fatalities">
            <IML IMT="MMI">0.005 0.007 0.0098 0.0137</IML>
            <discreteVulnerability vulnerabilityFunctionID="A"
                                   probabilisticDistribution="LN">
                <lossRatio>0.01 0.06 0.18 0.36</lossRatio>
                <coefficientsVariation>0.30 0.30 0.30 0.30</coefficientsVariation>
            </discreteVulnerability>
        </discreteVulnerabilitySet>
    </vulnerabilityModel>
</nrml>
""")
        self.job.risk_calculation.hazard_output = None
        with self.assertRaises(ValueError) as ar:
            self.calc.parse_vulnerability_model(vuln_content)
        expected_error = ('The same taxonomy is associated with different imts'
                          ' MMI and PGA')
        self.assertEqual(expected_error, ar.exception.message)

    def test_lr_eq_0_cov_gt_0(self):
        # If a vulnerability function loss ratio is 0 and its corresponding CoV
        # is > 0, a ValueError should be raised
        vuln_content = StringIO.StringIO("""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
    <vulnerabilityModel>
        <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
                                  assetCategory="population"
                                  lossCategory="fatalities">
            <IML IMT="PGV">0.005 0.007 0.0098 0.0137</IML>
            <discreteVulnerability vulnerabilityFunctionID="A"
                                   probabilisticDistribution="LN">
                <lossRatio>0.00 0.06 0.18 0.36</lossRatio>
                <coefficientsVariation>0.30 0.30 0.30 0.30</coefficientsVariation>
            </discreteVulnerability>
        </discreteVulnerabilitySet>
    </vulnerabilityModel>
</nrml>
""")
        with self.assertRaises(ValueError) as ar:
            self.calc.parse_vulnerability_model(vuln_content)
        expected_error = ("Invalid vulnerability function with ID 'A': It is "
                          "not valid to define a loss ratio = 0.0 with a "
                          "corresponding coeff. of varation > 0.0")
        self.assertEqual(expected_error, ar.exception.message)
