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

    #: UHS job profile
    uhs_jp = None
    #: UHS calculation
    uhs_calc = None
    #: UHS pending calculation
    uhs_pending_calc = None

    #: classical psha (haz+risk) job profile
    cpsha_jp = None
    #: classical psha (haz+risk) calculation
    cpsha_calc_fail = None
    #: classical psha (haz+risk) running calculation

    def tearDown(self):
        self.uhs_jp = None
        self.uhs_calc = None
        self.uhs_pending_calc = None

        self.cpsha_jp = None
        self.cpsha_calc_fail = None
        self.cpsha_running_calc = None

    @classmethod
    def _create_job_profiles(cls, user_name):
        uhs_cfg = helpers.demo_file('uhs/config.gem')
        cls.uhs_jp, _, _ = import_job_profile(uhs_cfg, user_name=user_name)

        cpsha_cfg = helpers.demo_file('classical_psha_based_risk/config.gem')
        cls.cpsha_jp, _, _ = import_job_profile(cpsha_cfg, user_name=user_name)

    @classmethod
    def _set_up_complete_calcs(cls):
        cls.uhs_calc = models.OqCalculation(
            owner=cls.uhs_jp.owner, description=cls.uhs_jp.description,
            oq_job_profile=cls.uhs_jp, status='succeeded')
        cls.uhs_calc.save()

        cls.cpsha_calc_fail = models.OqCalculation(
            owner=cls.cpsha_jp.owner, description=cls.cpsha_jp.description,
            oq_job_profile=cls.cpsha_jp, status='failed')
        cls.cpsha_calc_fail.save()

    @classmethod
    def _set_up_incomplete_calcs(cls):
        cls.uhs_pending_calc = models.OqCalculation(
            owner=cls.uhs_jp.owner, description=cls.uhs_jp.description,
            oq_job_profile=cls.uhs_jp, status='pending')
        cls.uhs_pending_calc.save()

        cls.cpsha_running_calc = models.OqCalculation(
            owner=cls.cpsha_jp.owner, description=cls.cpsha_jp.description,
            oq_job_profile=cls.cpsha_jp, status='running')
        cls.cpsha_running_calc.save()


class GetCalculationsTestCase(BaseExportTestCase):
    """Tests for the :function:`openquake.export.get_calculations` API
    function."""

    def test_get_calculations(self):
        # Test that :function:`openquake.export.get_calculations` retrieves
        # only _completed_ calculations for the given user, in reverse chrono
        # order.
        user_name = str(uuid.uuid4())
        self._create_job_profiles(user_name)
        self._set_up_complete_calcs()
        self._set_up_incomplete_calcs()

        # expeced values, sorted in reverse chronological order:
        expected = sorted([self.uhs_calc, self.cpsha_calc_fail],
                          key=lambda x: x.last_update)[::-1]
        actual = export.get_calculations(user_name)

        helpers.assertDeepAlmostEqual(self, expected, actual)

    def test_get_calculations_no_completed_calcs(self):
        # No completed calculations for this user.
        user_name = str(uuid.uuid4())
        self._create_job_profiles(user_name)
        self._set_up_incomplete_calcs()

        self.assertTrue(len(export.get_calculations(user_name)) == 0)


    def test_get_calculations_no_results_for_user(self):
        # No calculation records at all for this user.
        user_name = str(uuid.uuid4())
        self.assertTrue(len(export.get_calculations(user_name)) == 0)


class GetOutputsTestCase(BaseExportTestCase):
    """Tests for the :function:`openquake.export.get_outputs` API function."""

    def test_get_outputs(self):
        pass
