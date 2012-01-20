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


import numpy
import os
import unittest

from nose.plugins.attrib import attr

from openquake.db.models import LossCurveData
from openquake.db.models import OqCalculation

from tests.utils import helpers


class ClassicalRiskQATestCase(unittest.TestCase):
    """Single site QA tests for the Classical Risk calculator."""

    @attr('qa')
    def test_classical_psha_based_risk(self):
        """Run the full hazard+risk job, serialize all results to the db,
        and verify them against expected values."""

        expected_lc_poes = [
            0.03944,
            0.03943,
            0.03857,
            0.03548,
            0.03123,
            0.02708,
            0.02346,
            0.02039,
            0.01780,
            0.01565,
            0.01386,
            0.01118,
            0.00926,
            0.00776,
            0.00654,
            0.00555,
            0.00417,
            0.00338,
            0.00283,
            0.00231,
            0.00182,
            0.00114,
            0.00089,
            0.00082,
            0.00069,
            0.00039,
            0.00024,
            0.00013,
            0.00006,
            0.00002,
            0.00001,
        ]

        helpers.run_job(helpers.demo_file(
            os.path.join('classical_psha_based_risk', 'config.gem')))

        calculation = OqCalculation.objects.latest('id')
        self.assertEqual('succeeded', calculation.status)

        loss_curve = LossCurveData.objects.get(
            loss_curve__output__oq_calculation=calculation.id)

        self.assertTrue(numpy.allclose(expected_lc_poes, loss_curve.poes,
                                       atol=0.0009))
