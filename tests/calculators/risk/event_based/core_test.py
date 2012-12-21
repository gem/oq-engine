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

import mock
from tests.utils import helpers
from tests.calculators.risk import general_test

from openquake.db import models
from openquake.calculators.risk.event_based import core as event_based


class EventBasedRiskCalculatorTestCase(
        general_test.BaseRiskCalculatorTestCase):
    """
    Integration test for the event based risk calculator
    """
    def setUp(self):
        self.job, _ = helpers.get_risk_job(
            'event_based_risk/job.ini',
            'event_based_hazard/job.ini', output_type="gmf")

        self.calculator = event_based.EventBasedRiskCalculator(self.job)

    def calculation_parameters(self):
        """
        Test that the specific calculation parameters are present
        """

        params = self.calculator.calculation_parameters
        for field in ['loss_curve_resolution', 'insured_losses',
                      'conditional_loss_poes']:
            self.assertTrue(field in params)

        self.assertEqual(50, params['loss_curve_resolution'])
        self.assertEqual([0.01, 0.02, 0.05], params['conditional_loss_poes'])
        self.assertEqual(None, params['insured_losses'])

    def test_hazard_id(self):
        """
        Test that the hazard output used by the calculator is a
        `openquake.db.models.HazardCurve` object
        """

        self.assertEqual(1,
                         models.GmfCollection.objects.filter(
                             pk=self.calculator.hazard_id).count())

    def test_imt_validation(self):
        self.calculator.pre_execute()
        model = self.calculator.rc.model('vulnerability')
        model.imt = 'fake'
        model.save()

        patch = helpers.patch(
            'openquake.calculators.risk.general.store_risk_model')
        patch.start()
        self.assertRaises(RuntimeError, self.calculator.pre_execute)
        patch.stop()

    def test_celery_task(self):
        # Test that the celery task when called properly call the
        # specific method to write loss curves

        self.calculator.pre_execute()
        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()

        hazard_id = self.job.risk_calculation.hazard_output.gmfcollection.id

        patch = helpers.patch(
            'openquake.calculators.risk.general.write_loss_curve')
        mocked_writer = patch.start()

        loss_curve_id = mock.Mock()
        exposure_model_id = self.job.risk_calculation.model('exposure').id
        region_constraint = self.job.risk_calculation.region_constraint
        event_based.event_based(self.job.id,
                            0,
                            assets_per_task=3,
                            exposure_model_id=exposure_model_id,
                            hazard_getter="ground_motion_field",
                            hazard_id=hazard_id,
                            region_constraint=region_constraint,
                            loss_curve_id=loss_curve_id,
                            insured_curve_id=None,
                            loss_map_ids={},
                            insured_losses=False,
                            conditional_loss_poes=[],
                            seed=None)
        patch.stop()

        # we expect 1 asset being filtered out by the region
        # constraint, so there are only two loss curves to be written
        self.assertEqual(2, mocked_writer.call_count)
