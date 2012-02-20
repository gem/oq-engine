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


class ExportAPITestCase(unittest.TestCase):
    """Tests for the export API defined in :module:`openquake.export`."""

    @classmethod
    def _set_up_calculations(cls):
        cls.user_name = str(uuid.uuid4())
        uhs_cfg = helpers.demo_file('uhs/config.gem')
        uhs_jp, _, _ = import_job_profile(uhs_cfg, user_name=cls.user_name)
        cls.uhs_calc = models.OqCalculation(
            owner=uhs_jp.owner, description=uhs_jp.description,
            oq_job_profile=uhs_jp, status='succeeded')
        cls.uhs_calc.save()

        cpsha_cfg = helpers.demo_file('classical_psha_based_risk/config.gem')
        cpsha_jp, _, _ = import_job_profile(cpsha_cfg, user_name=cls.user_name)
        cls.cpsha_calc = models.OqCalculation(
            owner=cpsha_jp.owner, description=cpsha_jp.description,
            oq_job_profile=cpsha_jp, status='failed')
        cls.cpsha_calc.save()

        # We'll some other calculations (1 pending and 1 running) to make sure
        # that the API function under test only retrieves 'completed'
        # calculations.
        cls.uhs_pending_calc = models.OqCalculation(
            owner=uhs_jp.owner, description=uhs_jp.description,
            oq_job_profile=uhs_jp, status='pending')
        cls.uhs_pending_calc.save()

        cls.uhs_running_calc = models.OqCalculation(
            owner=uhs_jp.owner, description=uhs_jp.description,
            oq_job_profile=uhs_jp, status='running')
        cls.uhs_running_calc.save()

    def test_get_calculations(self):
        # Test that :function:`openquake.export.get_calculations` retrieves
        # only _completed_ calculations for the given user, in reverse chrono
        # order.
        self._set_up_calculations()

        # expeced values, sorted in reverse chronological order:
        expected = sorted([self.uhs_calc, self.cpsha_calc],
                          key=lambda x: x.last_update)[::-1]
        actual = export.get_calculations(self.user_name)

        helpers.assertDeepAlmostEqual(self, expected, actual)
