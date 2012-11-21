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
from openquake.calculators.risk import general as risk
from openquake.db import models
from openquake.utils import stats


class BaseRiskCalculatorTestCase(unittest.TestCase):
    """
    An abstract class that just setup a risk job
    """
    def setUp(self):
        self.job, _ = helpers.get_risk_job(
            'classical_psha_based_risk/job.ini',
            'simple_fault_demo_hazard/job.ini')


class FakeRiskCalculator(risk.BaseRiskCalculator):
    """
    Fake Risk Calculator. Used to test the base class
    """

    celery_task = mock.Mock()

    @property
    def hazard_id(self):
        return 0

    @property
    def calculation_parameters(self):
        return {}


class RiskCalculatorTestCase(BaseRiskCalculatorTestCase):
    """
    Integration test for the base class supporting the risk
    calculators.
    """

    def setUp(self):
        super(RiskCalculatorTestCase, self).setUp()
        self.calculator = FakeRiskCalculator(self.job)

    def test_store_exposure(self):
        """
        Test that exposure data and models are properly stored and
        associated with the calculator
        """
        self.calculator._store_exposure()

        actual_model_queryset = models.ExposureModel.objects.filter(
            input__input2rcalc__risk_calculation=self.job.risk_calculation,
            input__input_type="exposure")

        self.assertEqual(1, actual_model_queryset.count())

        model = actual_model_queryset.all()[0]

        actual_asset_queryset = models.ExposureData.objects.filter(
            exposure_model=model)

        self.assertEqual(3, actual_asset_queryset.count())

        asset_refs = [a.asset_ref for a in actual_asset_queryset.all()]

        self.assertEqual(["a1", "a2", "a3"], asset_refs)

    def test_store_risk_model(self):
        """
        Test that Vulnerability model and functions are properly
        stored and associated with the calculator
        """

        [vulnerability_input] = models.inputs4rcalc(
            self.job.risk_calculation, input_type='vulnerability')

        self.calculator.store_risk_model()

        actual_model_queryset = models.VulnerabilityModel.objects.filter(
            input=vulnerability_input)
        self.assertEqual(1, actual_model_queryset.count())

        model = actual_model_queryset.all()[0]

        self.assertEqual("QA_test1", model.name)

        self.assertEqual(1, model.vulnerabilityfunction_set.count())

    def test_create_outputs(self):
        """
        Test that the proper output containers are created
        """

        outputs = self.calculator.create_outputs()

        self.assertTrue('loss_curve_id' in outputs)

        self.assertTrue(models.LossCurve.objects.filter(
            pk=outputs['loss_curve_id']).exists())

    def test_pre_execute(self):
        # Most of the pre-execute functionality is implement in other methods.
        # For this test, just make sure each method gets called.
        path = ('openquake.calculators.risk.general.BaseRiskCalculator')
        patches = (
            helpers.patch(
                '%s.%s' % (path, '_store_exposure')),
            helpers.patch(
                '%s.%s' % (path, 'store_risk_model')),
            helpers.patch(
                '%s.%s' % (path, 'create_outputs')),
            helpers.patch(
                '%s.%s' % (path, '_initialize_progress')),
            helpers.patch(
                'openquake.db.models.ExposureData.objects.contained_in'))

        mocks = [p.start() for p in patches]

        mocks[0].return_value = models.ExposureModel.objects.all()[0]
        mocks[4].return_value = models.ExposureData.objects.all()

        self.calculator.pre_execute()

        for i, m in enumerate(mocks):
            self.assertEqual(1, m.call_count)
            m.stop()
            patches[i].stop()

    def test_execute(self):
        """
        Test that the distribute function is called properly
        """

        patch = helpers.patch(
            'openquake.utils.tasks.distribute')
        distribute = patch.start()

        self.calculator.pre_execute()
        self.calculator.execute()

        self.assertEqual(1, distribute.call_count)

        expected_region_constraint = (
            self.job.risk_calculation.region_constraint)
        expected_model_id = self.calculator.exposure_model_id
        expected_kwargs = dict(job_id=self.job.id,
                               hazard_getter="one_query_per_asset",
                               assets_per_task=1,
                               region_constraint=expected_region_constraint,
                               exposure_model_id=expected_model_id,
                               hazard_id=self.calculator.hazard_id)
        expected_kwargs.update(self.calculator.output_container_ids)
        expected_kwargs.update(self.calculator.calculation_parameters)

        expected_call = ((self.calculator.celery_task,
                          ("offset", range(0, 3, 4))),
                          dict(tf_args=expected_kwargs))
        self.assertEqual(1, distribute.call_count)
        self.assertEqual(expected_call[1:], distribute.call_args_list[0][1:])
        patch.stop()

    def test_initialize_progress(self):
        """
        Tests that the progress counter has been initialized properly
        """

        self.calculator.pre_execute()
        self.calculator._initialize_progress()

        total = stats.pk_get(self.calculator.job.id, "nrisk_total")
        self.assertEqual(self.calculator.assets_nr, total)
        done = stats.pk_get(self.calculator.job.id, "nrisk_done")
        self.assertEqual(0, done)
