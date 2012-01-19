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

from openquake.db.models import LossCurveData
from openquake.db.models import OqCalculation

from tests.utils import helpers


class ClassicalRiskQATestCase(unittest.TestCase):
    """Single site QA tests for the Classical Risk calculator."""

    def test_classical_psha_based_risk(self):
        """Run the full hazard+risk job, serialize all results to the db,
        and verify them against expected values."""

        self.maxDiff =None

        expected_lc_poes = [
            0.03881,
            0.03879,
            0.03793,
            0.03485,
            0.03059,
            0.02644,
            0.02282,
            0.01975,
            0.01717,
            0.01501,
            0.01323,
            0.01054,
            0.00862,
            0.00713,
            0.00591,
            0.00491,
            0.00353,
            0.00274,
            0.00219,
            0.00168,
            0.00119,
            0.00051,
            0.00026,
            0.00019,
            0.00015,
            0.00009,
            0.00005,
            0.00003,
            0.00001,
            0.00001,
            0.00000, 
        ]

        helpers.run_job(helpers.demo_file(
            os.path.join('classical_psha_based_risk', 'config.gem')),
            debug='debug')

        calculation = OqCalculation.objects.latest('id')

        loss_curve = LossCurveData.objects.get(
            loss_curve__output__oq_calculation=calculation.id)

        self.assertEqual(expected_lc_poes, loss_curve.poes)
