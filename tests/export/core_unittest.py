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


import os
import shutil
import tempfile
import unittest
import uuid

from django.core.exceptions import ObjectDoesNotExist

from openquake.db import models
from openquake.engine import import_job_profile
from openquake.export import core as export

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
        self._create_job_profiles(self.user_name)
        self._set_up_complete_calcs()
        self._set_up_outputs()

        expected_cpsha = [self.cpsha_hc_output, self.cpsha_mean_hc_output,
                          self.cpsha_lc_output]
        actual_cpsha = list(export.get_outputs(self.cpsha_calc_fail.id))
        self.assertEqual(expected_cpsha, actual_cpsha)

        expected_uhs = [self.uhs_output]
        actual_uhs = list(export.get_outputs(self.uhs_calc.id))
        self.assertEqual(expected_uhs, actual_uhs)

    def test_get_outputs_no_outputs(self):
        self._create_job_profiles(self.user_name)
        self._set_up_complete_calcs()

        self.assertTrue(len(export.get_outputs(self.uhs_calc.id)) == 0)
        self.assertTrue(len(export.get_outputs(self.cpsha_calc_fail.id)) == 0)


class ExportFunctionsTestCase(GetOutputsTestCase):
    """This test case ensures that the correct export function is executed for
    each type of output.
    """

    def test_export_unknown_output_type(self):
        self._create_job_profiles(self.user_name)
        self._set_up_complete_calcs()
        self._set_up_outputs()

        self.uhs_output.output_type = 'unknown'
        self.uhs_output.save()

        self.assertRaises(NotImplementedError, export.export,
                          self.uhs_output.id, '/some/dir/')

    def test_export_with_bogus_output_id(self):
        # If `export` is called with a non-existent output_id,
        # a ObjectDoesNotExist error should be raised.

        self.assertRaises(ObjectDoesNotExist, export.export,
                          -1, '/some/dir/')

    def test_export_expands_user(self):
        # If the user specifies a path using '~' (to indicate the current
        # user's home directory), make sure the path is expanded properly.
        # See `os.path.expanduser`.
        self._create_job_profiles(self.user_name)
        self._set_up_complete_calcs()
        self._set_up_outputs()

        self.uhs_output.output_type = 'unknown'
        self.uhs_output.save()

        expanded_dir = '%s/uhs_results/some_subdir/' % os.getenv('HOME')

        with helpers.patch(
            'openquake.export.core._export_fn_not_implemented') as expt_patch:
            export.export(self.uhs_output.id, '~/uhs_results/some_subdir/')

            self.assertEqual(1, expt_patch.call_count)
            self.assertEqual(((self.uhs_output, expanded_dir), {}),
                             expt_patch.call_args)


@export.makedirs
def _decorated(_output, _target_dir):
    """Just a test function for exercising the `makedirs` decorator."""
    return []


class UtilsTestCase(unittest.TestCase):
    """Tests for misc. export utilties."""

    def test_makedirs_deco(self):
        temp_dir = tempfile.mkdtemp()

        try:
            target_dir = os.path.join(temp_dir, 'some', 'nonexistent', 'dir')

            self.assertFalse(os.path.exists(target_dir))

            _decorated(None, target_dir)

            self.assertTrue(os.path.exists(target_dir))
        finally:
            shutil.rmtree(temp_dir)

    def test_makedirs_deco_dir_already_exists(self):
        # If the dir already exists, this should work with no errors.
        # The decorator should just gracefully pass through.
        temp_dir = tempfile.mkdtemp()
        try:
            _decorated(None, temp_dir)
        finally:
            shutil.rmtree(temp_dir)

    def test_makedirs_deco_target_exists_as_file(self):
        # If a file exists with the exact path of the target dir,
        # we should get a RuntimeError.
        _, temp_file = tempfile.mkstemp()

        try:
            self.assertRaises(RuntimeError, _decorated, None, temp_file)
        finally:
            os.unlink(temp_file)
