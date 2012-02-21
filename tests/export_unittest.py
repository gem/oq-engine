# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


import unittest
import uuid

from openquake import export
from openquake.db import models
from openquake.engine import import_job_profile
from openquake.engine import run_calculation

from tests.utils import helpers


class BaseExportTestCase(unittest.TestCase):
    """Functionality common to Export API tests."""

    # UHS job profile
    uhs_jp = None
    # UHS calculation
    uhs_calc = None
    # UHS pending calculation
    uhs_pending_calc = None

    # classical psha (haz+risk) job profile
    cpsha_jp = None
    # classical psha (haz+risk) calculation, failed
    cpsha_calc_fail = None

    user_name = None

    def setUp(self):
        self.user_name = str(uuid.uuid4())

    def _create_job_profiles(self, user_name):
        uhs_cfg = helpers.demo_file('uhs/config.gem')
        self.uhs_jp, _, _ = import_job_profile(uhs_cfg, user_name=user_name)

        cpsha_cfg = helpers.demo_file('classical_psha_based_risk/config.gem')
        self.cpsha_jp, _, _ = import_job_profile(cpsha_cfg,
                                                 user_name=user_name)

    def _set_up_complete_calcs(self):
        self.uhs_calc = models.OqCalculation(
            owner=self.uhs_jp.owner, description=self.uhs_jp.description,
            oq_job_profile=self.uhs_jp, status='succeeded')
        self.uhs_calc.save()

        self.cpsha_calc_fail = models.OqCalculation(
            owner=self.cpsha_jp.owner, description=self.cpsha_jp.description,
            oq_job_profile=self.cpsha_jp, status='failed')
        self.cpsha_calc_fail.save()

    def _set_up_incomplete_calcs(self):
        self.uhs_pending_calc = models.OqCalculation(
            owner=self.uhs_jp.owner, description=self.uhs_jp.description,
            oq_job_profile=self.uhs_jp, status='pending')
        self.uhs_pending_calc.save()

        self.cpsha_running_calc = models.OqCalculation(
            owner=self.cpsha_jp.owner, description=self.cpsha_jp.description,
            oq_job_profile=self.cpsha_jp, status='running')
        self.cpsha_running_calc.save()


class GetCalculationsTestCase(BaseExportTestCase):
    """Tests for the :function:`openquake.export.get_calculations` API
    function."""

    def test_get_calculations(self):
        # Test that :function:`openquake.export.get_calculations` retrieves
        # only _completed_ calculations for the given user, in reverse chrono
        # order.
        self._create_job_profiles(self.user_name)
        self._set_up_complete_calcs()
        self._set_up_incomplete_calcs()

        # expeced values, sorted in reverse chronological order:
        expected = sorted([self.uhs_calc, self.cpsha_calc_fail],
                          key=lambda x: x.last_update)[::-1]
        actual = list(export.get_calculations(self.user_name))

        self.assertEqual(expected, actual)

    def test_get_calculations_no_completed_calcs(self):
        # No completed calculations for this user.
        self._create_job_profiles(self.user_name)
        self._set_up_incomplete_calcs()

        self.assertTrue(len(export.get_calculations(self.user_name)) == 0)


    def test_get_calculations_no_results_for_user(self):
        # No calculation records at all for this user.
        self.assertTrue(len(export.get_calculations(self.user_name)) == 0)


class GetOutputsTestCase(BaseExportTestCase):
    """Tests for the :function:`openquake.export.get_outputs` API function."""

    # uniform hazard spectra
    uhs_output = None
    # hazard curve
    cpsha_hc_output = None
    # mean hazard curve
    cpsha_mean_hc_output = None
    # loss curve
    cpsha_lc_output = None

    def _set_up_outputs(self):
        # Set up test Output records
        self._create_job_profiles(self.user_name)
        self._set_up_complete_calcs()

        self.uhs_output = models.Output(
            owner=self.uhs_calc.owner, oq_calculation=self.uhs_calc,
            db_backed=True, output_type='uh_spectra')
        self.uhs_output.save()

        self.cpsha_hc_output = models.Output(
            owner=self.cpsha_calc_fail.owner, 
            oq_calculation=self.cpsha_calc_fail, db_backed=True,
            output_type='hazard_curve')
        self.cpsha_hc_output.save()

        self.cpsha_mean_hc_output = models.Output(
            owner=self.cpsha_calc_fail.owner,
            oq_calculation=self.cpsha_calc_fail, db_backed=True,
            output_type='hazard_curve')
        self.cpsha_mean_hc_output.save()

        self.cpsha_lc_output = models.Output(
            owner=self.cpsha_calc_fail.owner,
            oq_calculation=self.cpsha_calc_fail, db_backed=True,
            output_type='loss_curve')
        self.cpsha_lc_output.save()

    def test_get_outputs_cpsha(self):
        self._set_up_outputs()

        expected_cpsha = [self.cpsha_hc_output, self.cpsha_mean_hc_output,
                          self.cpsha_lc_output]
        actual_cpsha = list(export.get_outputs(self.cpsha_calc_fail.id))
        self.assertEqual(expected_cpsha, actual_cpsha)

        expected_uhs = [self.uhs_output]
        actual_uhs = list(export.get_outputs(self.uhs_calc.id))
        self.assertEqual(expected_uhs, actual_uhs)
