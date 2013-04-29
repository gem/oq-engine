# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.

import unittest
import pickle
from openquake.risklib.curve import Curve
from numpy import allclose


class CurveTestCase(unittest.TestCase):
    """
    Tests for :py:class:`openquake.shapes.Curve`.
    """

    @classmethod
    def setUpClass(cls):
        # simple curve: f(x) = x^2
        cls.x_vals = [1, 2, 3]
        cls.y_vals = [x ** 2 for x in cls.x_vals]
        cls.simple_curve = Curve(zip(cls.x_vals, cls.y_vals))

        # straight line
        cls.straight_curve = Curve(zip(range(1, 4), range(1, 4)))

    def test_ordinate_for_basic(self):
        """
        Test that we can find the appropriate y value given the basic Curve
        definition.
        """
        self.assertEqual(1, self.simple_curve.ordinate_for(1))
        self.assertEqual(4, self.simple_curve.ordinate_for(2))
        self.assertEqual(9, self.simple_curve.ordinate_for(3))

    def test_ordinate_for_interpolate(self):
        """
        Test that we can find the appropriate y value on a Curve by
        interpolating.
        """
        # Since this line is straight, the interpolated y value should be the
        # same as the x value passed to ordinate_for.
        self.assertEqual(1.11, self.straight_curve.ordinate_for(1.11))
        self.assertEqual(2.9999, self.straight_curve.ordinate_for(2.9999))

    def test_curve_ordinate_for_clipping(self):
        """
        Test that :py:method:`openquake.shapes.Curve.ordinate_for` properly
        clips input values to the valid range defined (and thus, doesn't throw
        interpolation errors).
        """
        # test low-end:
        self.assertEqual(1.0, self.straight_curve.ordinate_for(0.9))

        # test high-end:
        self.assertEqual(3.0, self.straight_curve.ordinate_for(3.1))

    def test_can_construct_with_unordered_values(self):
        curve = Curve([(0.5, 1.0), (0.4, 2.0), (0.3, 2.0)])

        self.assertEqual(1.0, curve.ordinate_for(0.5))
        self.assertEqual(2.0, curve.ordinate_for(0.4))
        self.assertEqual(2.0, curve.ordinate_for(0.3))

    def test_ordinate_diffs(self):
        hazard_curve = Curve([
            (0.01, 0.99), (0.08, 0.96),
            (0.17, 0.89), (0.26, 0.82),
            (0.36, 0.70), (0.55, 0.40),
            (0.70, 0.01),
        ])

        expected_pos = [0.0673, 0.1336, 0.2931, 0.4689]
        pes = [0.05, 0.15, 0.3, 0.5, 0.7]

        self.assertTrue(allclose(expected_pos,
                                 hazard_curve.ordinate_diffs(pes),
                                 atol=0.00005))
