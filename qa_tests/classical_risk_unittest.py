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


import os
import unittest

from openquake.db.models import OqCalculation

from tests.utils import helpers


class ClassicalRiskQATestCase(unittest.TestCase):
    """Single site QA tests for the Classical Risk calculator."""

    def test_classical_psha_based_risk(self):
        """Run the full hazard+risk job, serialize all results to the db,
        and verify them against expected values."""

        expected_results = None

        helpers.run_job(helpers.demo_file(
            os.path.join('classical_psha_based_risk', 'config.gem')))

        calc_id = OqCalculation.objects.latest('id')
