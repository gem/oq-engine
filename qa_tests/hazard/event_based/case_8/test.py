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

import numpy
import os

from nose.plugins.attrib import attr
from openquake.db import models
from qa_tests import _utils as qa_utils


class EventBasedHazardCase8TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        expected_curve_poes_b1_b2 = [0.095163, 0.012362, 0.002262, 0.0]
        expected_curve_poes_b1_b3 = [0.009950, 0.00076, 9.99995E-6, 0.0]
        expected_curve_poes_b1_b4 = [0.0009995, 4.5489E-5, 4.07365E-6, 0.0]

        job = self.run_hazard(cfg)

        # Test the poe values for the three curves:
        curve_b1_b2, curve_b1_b3, curve_b1_b4 = \
            models.HazardCurveData.objects\
                .filter(hazard_curve__output__oq_job=job.id)\
                .order_by('hazard_curve__lt_realization__sm_lt_path')

        # Sanity check, to make sure we have the curves ordered correctly:
        self.assertEqual(
            ['b1', 'b2'],
            curve_b1_b2.hazard_curve.lt_realization.sm_lt_path)
        self.assertEqual(
            ['b1', 'b3'],
            curve_b1_b3.hazard_curve.lt_realization.sm_lt_path)
        self.assertEqual(
            ['b1', 'b4'],
            curve_b1_b4.hazard_curve.lt_realization.sm_lt_path)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes_b1_b2, curve_b1_b2.poes, decimal=3)
        numpy.testing.assert_array_almost_equal(
            expected_curve_poes_b1_b3, curve_b1_b3.poes, decimal=3)
        numpy.testing.assert_array_almost_equal(
            expected_curve_poes_b1_b4, curve_b1_b4.poes, decimal=3)
