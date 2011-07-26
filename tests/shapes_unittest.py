# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
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


import decimal
import re
import unittest

from openquake import shapes
from openquake.utils import round_float


def coord_list_from_wkt(wkt):
    """
    Given a Well Known Text string, extract the coordinate values and return
    them as a list of float values.

    Note: This is intended for use with 'primitve' WKT shapes (such as POINT,
    LINESTRING, and POLYGON). Input POLYGON shapes should not have holes.

    :param wkt: Well Known Text string for a POINT, LINESTRING, or POLYGON
        shape

    :returns: list of floats
    """
    return [float(x) for x in re.findall('[\d+?\.\d+]+', wkt)]


class ShapesTestCase(unittest.TestCase):

    def test_round_float(self):
        """
        This test exercises the :py:function:`openquake.utils.round_float`
        function.

        Basically, the function should take any float number and round it to a
        fixed number of decimal places (for example, 7 places). The rounding
        method used is the default for the :py:module:`decimal` module, which
        is ROUND_HALF_EVEN.

        For more information on 'half-even' rounding, there is a good
        explanation here:
        http://www.diycalculator.com/popup-m-round.shtml#A5
        """
        in_values = (
            29.000000000000004, -121.00000009, -121.00000001, 121.00000005,
            121.00000006)
        out_values = (29.0, -121.0000001, -121.0, 121.0, 121.0000001)

        for i, val in enumerate(in_values):
            self.assertEqual(out_values[i], round_float(in_values[i]))

    def test_round_float_rounding(self):
        """
        By default, the :py:module:`decimal` module uses the 'round-half-even'
        algorithm for rounding numbers.

        Since the rounding method can be set in a global context for the
        :py:module:`decimal` module, we want to make sure the
        :py:function:`openquake.utils.round_float` is unaffected context
        changes.
        """
        decimal.getcontext().rounding = decimal.ROUND_FLOOR

        # changing the decimal context rounding should not affect the behavior
        # of round_float
        self.assertEqual(-121.0000001, round_float(-121.00000009))

        # reset the global context so we don't potentially screw up other tests
        decimal.getcontext().rounding = decimal.ROUND_HALF_EVEN

    def test_simple_region_uses_round_floats(self):
        """
        This test ensures the coordinate precision is properly limited for
        instances of :py:class:`openquake.shapes.Region`.

        The region will be created using the
        :py:method:`openquake.shapes.Region.from_simple` method.
        """
        up_left = (29.00000006, 40.90000003)
        low_right = (25.70000005, 46.00000009)

        # Constrained versions of the corner points:
        exp_ul = (29.0000001, 40.9)
        exp_lr = (25.7, 46.0000001)

        region = shapes.Region.from_simple(up_left, low_right)

        # The easiest way to verify that the number precision of the region
        # is correct is to look at the WKT for the region polygon.
        coords = coord_list_from_wkt(region.polygon.wkt)

        actual_ul = tuple(coords[0:2])
        actual_lr = tuple(coords[4:6])

        self.assertEqual(exp_ul, actual_ul)
        self.assertEqual(exp_lr, actual_lr)

    def test_complex_region_uses_round_floats(self):
        """
        This test ensures the coordinate precision is properly limited for
        instance of :py:class:`openquake.shapes.Region`.

        The region will be created using the
        :py:method:`openquake.shapes.Region.from_coordinates` method.
        """
        # triangle
        input_coord_pairs = [
            (29.00000006, 40.90000003),
            (25.70000005, 46.00000009),
            (26.0, 45.00000001)]

        # we expect the first & last coord pair to be the same, since wkt
        # POLYGON shapes must form a closed loop
        expected_coord_list = [
            29.0000001, 40.9,
            25.7, 46.0000001,
            26.0, 45.0,
            29.0000001, 40.9]

        region = shapes.Region.from_coordinates(input_coord_pairs)

        actual_coord_list = coord_list_from_wkt(region.polygon.wkt)

        self.assertEqual(expected_coord_list, actual_coord_list)

    def test_site_uses_round_floats(self):
        """
        This test ensures the coordinate precision is properly limited for
        instances of :py:class:`openquake.shapes.Site`.
        """
        lon = -121.00000004
        lat = 29.00000006

        exp_lon = -121.0
        exp_lat = 29.0000001

        site = shapes.Site(lon, lat)

        self.assertEqual(exp_lon, site.longitude)
        self.assertEqual(exp_lat, site.latitude)

    def test_abscissa_for_is_correct(self):
        curve_params = [(5.0, 0.138), (6.0, 0.099),
                    (7.0, 0.068), (8.0, 0.041)]

        expected_xvalues = [curve_param[0] for curve_param in curve_params]
        y_values = [curve_param[1] for curve_param in curve_params]

        curve = shapes.Curve(curve_params)

        self.assertEqual(curve.abscissa_for(y_values).tolist(), 
                expected_xvalues)
