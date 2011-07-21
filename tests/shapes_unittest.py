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
import json
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



class CurveTestCase(unittest.TestCase):
    """
    Tests for the :py:class:`openquake.shapes.Curve` class.
    """

    def setUp(self):
        # simple curve: f(x) = x^2
        x_vals = [1,2,3]
        y_vals = [x**2 for x in x_vals]
        self.simple_curve = shapes.Curve(zip(x_vals, y_vals))

        # straight line
        self.straight_curve = shapes.Curve(zip(range(1, 4), range(1, 4)))

    def test_ordinate_for_basic(self):
        """
        Test that we can find the appropriate y value given the basic curve
        definition.
        """
        self.assertEqual(1, self.simple_curve.ordinate_for(1))
        self.assertEqual(4, self.simple_curve.ordinate_for(2))
        self.assertEqual(9, self.simple_curve.ordinate_for(3))

    def test_ordinate_for_interpolate(self):
        """
        Test that we can find the appropriate y value by interpolating.
        """
        # Since this line is straight, the interpolated y value should be the
        # same as the x value passed to ordinate_for.
        self.assertEqual(1.11, self.straight_curve.ordinate_for(1.11))
        self.assertEqual(2.9999, self.straight_curve.ordinate_for(2.9999))


class VulnerabilityFunctionTestCase(unittest.TestCase):
    """
    Test for the :py:class`openquake.shapes.VulnerabilityFunction` class.
    """
    IMLS_GOOD = [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269]
    IMLS_BAD = [0.0, 0.007, 0.0098, 0.0137, 0.0192, 0.0269]
    IMLS_DUPE = [0.005, 0.005, 0.0098, 0.0137, 0.0192, 0.0269]
    IMLS_BAD_ORDER = [0.005, 0.0098, 0.007, 0.0137, 0.0192, 0.0269]

    LOSS_RATIOS_GOOD = [0.1, 0.3, 0.0, 0.5, 1.0, 0.6]
    LOSS_RATIOS_BAD = [0.1, 0.3, 0.0, 1.1, -0.1, 0.6]
    LOSS_RATIOS_TOO_SHORT = [0.1, 0.3, 0.0, 0.5, 1.0]
    LOSS_RATIOS_TOO_LONG = [0.1, 0.3, 0.0, 0.5, 1.0, 0.6, 0.5]

    COVS_GOOD = [0.3, 0.1, 0.3, 0.0, 0.3, 10]
    COVS_BAD = [-0.1, 0.1, 0.3, 0.0, 0.3, 10]
    COVS_TOO_SHORT = [0.3, 0.1, 0.3, 0.0, 0.3]
    COVS_TOO_LONG = [0.3, 0.1, 0.3, 0.0, 0.3, 10, 11]

    TEST_VULN_FUNC = shapes.VulnerabilityFunction(IMLS_GOOD, LOSS_RATIOS_GOOD,
        COVS_GOOD)

    def test_constructor_with_good_input(self):
        """
        This test exercises the VulnerabilityFunction constructor with
        known-good input.
        """
        shapes.VulnerabilityFunction(self.IMLS_GOOD, self.LOSS_RATIOS_GOOD,
            self.COVS_GOOD)

    def test_constructor_raises_on_bad_imls(self):
        """
        This test attempts to invoke AssertionErrors by passing 3 different
        sets of bad IMLs to the constructor:
            - IML list containing out-of-range value(s)
            - IML list containing duplicates
            - IML list ordered improperly
        """
        self.assertRaises(AssertionError, shapes.VulnerabilityFunction,
            self.IMLS_BAD, self.LOSS_RATIOS_GOOD, self.COVS_GOOD)

        self.assertRaises(AssertionError, shapes.VulnerabilityFunction,
            self.IMLS_DUPE, self.LOSS_RATIOS_GOOD, self.COVS_GOOD)

        self.assertRaises(AssertionError, shapes.VulnerabilityFunction,
            self.IMLS_BAD_ORDER, self.LOSS_RATIOS_GOOD, self.COVS_GOOD)

    def test_constructor_raises_on_bad_cov(self):
        """
        This test attempts to invoke AssertionErrors by passing 3 different
        sets of bad CoV values to the constructor:
            - CoV list containing out-range-values
            - CoV list which is shorter than the IML list
            - CoV list which is longer than the IML list
        """
        self.assertRaises(AssertionError, shapes.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_GOOD, self.COVS_BAD)

        self.assertRaises(AssertionError, shapes.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_GOOD, self.COVS_TOO_SHORT)

        self.assertRaises(AssertionError, shapes.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_GOOD, self.COVS_TOO_LONG)

    def test_constructor_raises_on_bad_loss_ratios(self):
        """
        This test attempts to invoke AssertionErrors by passing 3 different
        sets of bad loss ratio values to the constructor:
            - loss ratio list containing out-range-values
            - loss ratio list which is shorter than the IML list
            - loss ratio list which is longer than the IML list
        """
        self.assertRaises(AssertionError, shapes.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_BAD, self.COVS_GOOD)

        self.assertRaises(AssertionError, shapes.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_TOO_SHORT, self.COVS_GOOD)

        self.assertRaises(AssertionError, shapes.VulnerabilityFunction,
            self.IMLS_GOOD, self.LOSS_RATIOS_TOO_LONG, self.COVS_GOOD)

    def test_clip_low_iml_values(self):
        """
        Test :py:method:`openquake.shapes.VulnerabilityFunction._clip_iml` to
        ensure that low values are clipped to the lowest valid value in the
        IML range.
        """
        self.assertEqual(0.005, self.TEST_VULN_FUNC._clip_iml(0.0049))

    def test_clip_high_iml_values(self):
        """
        Test :py:method:`openquake.shapes.VulnerabilityFunction._clip_iml` to
        ensure that the high values are clipped to the highest valid value in
        the IML range.
        """
        self.assertEqual(0.0269, self.TEST_VULN_FUNC._clip_iml(0.027))

    def test_clip_iml_with_normal_value(self):
        """
        Test :py:method:`openquake.shapes.VulnerabilityFunction._clip_iml` to
        ensure that normal values (values within the defined IML range) are not
        changed.
        """
        valid_imls = [0.005, 0.0269, 0.0051, 0.0268]
        for i in valid_imls:
            self.assertEqual(i, self.TEST_VULN_FUNC._clip_iml(i))

    def test_from_dict(self):
        """
        Test that a VulnerabilityFunction can be created from dictionary of
        IML, Loss Ratio, and CoV values.
        """
        test_dict = {
            '0.005': [0.1, 0.2],
            '0.007': [0.3, 0.4],
            0.0098: [0.5, 0.6]}

        vuln_curve = shapes.VulnerabilityFunction.from_dict(test_dict)

        self.assertEqual([0.005, 0.007, 0.0098], vuln_curve.imls)
        self.assertEqual([0.1, 0.3, 0.5], vuln_curve.loss_ratios)
        self.assertEqual([0.2, 0.4, 0.6], vuln_curve.covs)

    def test_from_json(self):
        """
        Test that a VulnerabilityFunction can be constructed from a
        properly formatted JSON string.
        """
        vuln_func_json = \
            '{"0.005": [0.1, 0.2], "0.007": [0.3, 0.4], "0.0098": [0.5, 0.6]}'

        vuln_curve = shapes.VulnerabilityFunction.from_json(vuln_func_json)

        self.assertEqual([0.005, 0.007, 0.0098], vuln_curve.imls)
        self.assertEqual([0.1, 0.3, 0.5], vuln_curve.loss_ratios)
        self.assertEqual([0.2, 0.4, 0.6], vuln_curve.covs)

    def test_to_json(self):
        """
        """
        imls = [0.005, 0.007, 0.0098]
        loss_ratios = [0.1, 0.3, 0.5]
        covs = [0.2, 0.4, 0.6]

        vuln_func = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        expected_json = \
            '{"0.005": [0.1, 0.2], "0.007": [0.3, 0.4], "0.0098": [0.5, 0.6]}'

        # The JSON data (which is essentially a dict) may not come out with the
        # data ordered in a predictable way. So, we'll decode the expected and
        # actual values and compare them as dicts.

        json_decoder = json.JSONDecoder()

        self.assertEqual(
            json_decoder.decode(expected_json),
            json_decoder.decode(vuln_func.to_json()))
