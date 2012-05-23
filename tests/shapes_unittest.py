# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import decimal
import json
import numpy
import re
import unittest

from numpy import allclose

from openquake import shapes
from openquake.utils import round_float

from tests.utils import helpers


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

    TEST_IMLS = [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269]

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

        for i, _ in enumerate(in_values):
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

    def test_clip_low_iml_values(self):
        """
        Test :py:method:`openquake.shapes.range_clip` to
        ensure that low values are clipped to the lowest valid value in the
        IML range.
        """
        self.assertEqual(0.005, shapes.range_clip(0.0049, self.TEST_IMLS))

    def test_clip_low_imls_many_values(self):
        """
        Test :py:method:`openquake.shapes.range_clip` to
        ensure that low values are clipped to the lowest valid value in the
        IML range.
        """
        expected_imls = numpy.array([0.005, 0.005, 0.005])
        test_input = [0.0049, 0.00001, 0.002]

        self.assertTrue(allclose(expected_imls,
            shapes.range_clip(test_input, self.TEST_IMLS)))
        # same test, except with a numpy.array-type input:
        self.assertTrue(allclose(expected_imls,
            shapes.range_clip(numpy.array(test_input), self.TEST_IMLS)))

    def test_clip_high_iml_values(self):
        """
        Test :py:method:`openquake.shapes.range_clip` to
        ensure that the high values are clipped to the highest valid value in
        the IML range.
        """
        self.assertEqual(0.0269, shapes.range_clip(0.027, self.TEST_IMLS))

    def test_clip_high_imls_many_values(self):
        """
        Test :py:method:`openquake.shapes.range_clip` to
        ensure that the high values are clipped to the highest valid value in
        the IML range.
        """
        expected_imls = numpy.array([0.0269, 0.0269, 0.0269])
        test_input = [0.027, 0.3, 10]

        self.assertTrue(allclose(expected_imls,
            shapes.range_clip(test_input, self.TEST_IMLS)))
        # same test, except with a numpy.array-type input:
        self.assertTrue(allclose(expected_imls,
            shapes.range_clip(numpy.array(test_input), self.TEST_IMLS)))

    def test_clip_iml_with_normal_value(self):
        """
        Test :py:method:`openquake.shapes.range_clip` to
        ensure that normal values (values within the defined IML range) are not
        changed.
        """
        valid_imls = numpy.array([0.005, 0.0051, 0.0268, 0.0269])
        for i in valid_imls:
            self.assertEqual(i, shapes.range_clip(i, valid_imls))

    def test_clip_imls_with_many_normal_values(self):
        """
        Test :py:method:`openquake.shapes.range_clip` to
        ensure that normal values (values within the defined IML range) are not
        changed.
        """
        valid_imls = [0.005, 0.0269, 0.0051, 0.0268]
        expected_result = numpy.array(valid_imls)

        self.assertTrue(allclose(expected_result,
            shapes.range_clip(valid_imls, self.TEST_IMLS)))
        # same test, except with numpy.array-type input:
        self.assertTrue(allclose(expected_result,
            shapes.range_clip(numpy.array(valid_imls), self.TEST_IMLS)))

    def test_for_hash_collisions(self):
        """The hash values for similar sites should *not* collide."""
        s1 = shapes.Site(-0.9, -1.0)
        s2 = shapes.Site(0.9, 0.0)
        self.assertNotEqual(hash(s1), hash(s2))


class CurveTestCase(unittest.TestCase):
    """
    Tests for :py:class:`openquake.shapes.Curve`.
    """

    @classmethod
    def setUpClass(cls):
        # simple curve: f(x) = x^2
        cls.x_vals = [1, 2, 3]
        cls.y_vals = [x ** 2 for x in cls.x_vals]
        cls.simple_curve = shapes.Curve(zip(cls.x_vals, cls.y_vals))

        # straight line
        cls.straight_curve = shapes.Curve(zip(range(1, 4), range(1, 4)))

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

    def test_abscissa_for_in_not_ascending_order_with_dups(self):
        """ This tests the corner case when:
            "vals must be arranged in ascending order with no duplicates"
        """
        vals = [1, 1, 1]

        curve = shapes.Curve(zip(vals, vals))

        self.assertRaises(AssertionError, curve.abscissa_for, vals)

    def test_abscissa_for_with_multiple_yvals(self):
        """ tests the correctness of the abscissa method """
        self.assertEqual(
            self.simple_curve.abscissa_for(self.y_vals).tolist(),
                self.x_vals)

    def test_equals_when_have_the_same_values(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve3 = shapes.Curve([(0.1, 1.0), (0.2, 5.0)])
        curve4 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve5 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve6 = shapes.Curve([(0.1, (1.0, 0.5)), (0.2, (2.0, 0.3))])

        self.assertEquals(curve1, curve2)
        self.assertNotEquals(curve1, curve3)
        self.assertNotEquals(curve1, curve4)
        self.assertNotEquals(curve3, curve4)
        self.assertEquals(curve4, curve5)
        self.assertNotEquals(curve5, curve6)

    def test_can_construct_a_curve_from_dict(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve.from_dict({"0.1": 1.0, "0.2": 2.0})
        curve3 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve4 = shapes.Curve.from_dict({"0.1": (1.0, 0.3), "0.2": (2.0, 0.3)})

        # keys are already floats
        curve5 = shapes.Curve.from_dict({0.1: (1.0, 0.3), 0.2: (2.0, 0.3)})

        self.assertEquals(curve1, curve2)
        self.assertEquals(curve3, curve4)
        self.assertEquals(curve3, curve5)

    def test_can_serialize_in_json(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        self.assertEquals(curve1, shapes.Curve.from_json(curve1.to_json()))
        self.assertEquals(curve2, shapes.Curve.from_json(curve2.to_json()))

    def test_can_construct_with_unordered_values(self):
        curve = shapes.Curve([(0.5, 1.0), (0.4, 2.0), (0.3, 2.0)])

        self.assertEqual(1.0, curve.ordinate_for(0.5))
        self.assertEqual(2.0, curve.ordinate_for(0.4))
        self.assertEqual(2.0, curve.ordinate_for(0.3))


class VulnerabilityFunctionTestCase(unittest.TestCase):
    """
    Test for :py:class:`openquake.shapes.VulnerabilityFunction`.
    """
    IMLS_GOOD = [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269]
    IMLS_BAD = [-0.1, 0.007, 0.0098, 0.0137, 0.0192, 0.0269]
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

    @classmethod
    def setUpClass(cls):
        cls.test_func = shapes.VulnerabilityFunction(cls.IMLS_GOOD,
            cls.LOSS_RATIOS_GOOD, cls.COVS_GOOD)

    def test_vuln_func_constructor_with_good_input(self):
        """
        This test exercises the VulnerabilityFunction constructor with
        known-good input.
        """
        shapes.VulnerabilityFunction(self.IMLS_GOOD, self.LOSS_RATIOS_GOOD,
            self.COVS_GOOD)

    def test_vuln_func_constructor_raises_on_bad_imls(self):
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

    def test_vuln_func_constructor_raises_on_bad_cov(self):
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

    def test_vuln_func_constructor_raises_on_bad_loss_ratios(self):
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

        self.assertEqual([0.005, 0.007, 0.0098], vuln_curve._imls)
        self.assertEqual([0.1, 0.3, 0.5], vuln_curve._loss_ratios)
        self.assertEqual([0.2, 0.4, 0.6], vuln_curve._covs)

    def test_from_json(self):
        """
        Test that a VulnerabilityFunction can be constructed from a
        properly formatted JSON string.
        """
        vuln_func_json = \
            '{"0.005": [0.1, 0.2], "0.007": [0.3, 0.4], "0.0098": [0.5, 0.6]}'

        vuln_curve = shapes.VulnerabilityFunction.from_json(vuln_func_json)

        self.assertEqual([0.005, 0.007, 0.0098], vuln_curve._imls)
        self.assertEqual([0.1, 0.3, 0.5], vuln_curve._loss_ratios)
        self.assertEqual([0.2, 0.4, 0.6], vuln_curve._covs)

    def test_to_json(self):
        """
        Test that a VulnerabilityFunction can produce a correct JSON
        representation of itself.
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

    def test_eq(self):
        """
        Exercise equality comparison of VulnerabilityFunctions. Two functions
        created with the same IML, Loss Ratio, and CoV values should be
        considered equal.
        """
        imls = [0.005, 0.007]
        loss_ratios = [0.0, 1.0]
        covs = [0.05, 0.05]

        func1 = shapes.VulnerabilityFunction(imls, loss_ratios, covs)
        func2 = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        self.assertEqual(func1, func2)

    def test_loss_ratio_interp_single_value(self):
        """
        Test that single loss ratio values are properly interpolated.
        """
        # lower boundary:
        self.assertEqual(0.1, self.test_func.loss_ratio_for(0.005))
        # upper boundary:
        self.assertEqual(0.6, self.test_func.loss_ratio_for(0.0269))
        # between the first 2 IMLs:
        self.assertEqual(0.2, self.test_func.loss_ratio_for(0.006))

    def test_loss_ratio_interp_single_value_clipped(self):
        """
        Test that loss ratio interpolation properly clips out-of-range input
        values to the IML range defined for the vulnerability function.
        """
        # test low-end clipping:
        self.assertEqual(0.1, self.test_func.loss_ratio_for(0.0049))
        # test high-end clipping:
        self.assertEqual(0.6, self.test_func.loss_ratio_for(0.027))

    def test_loss_ratio_interp_many_values(self):
        """
        Given a list of IML values (abscissae), test for proper interpolation
        of loss ratios (ordinates).
        """
        expected_lrs = numpy.array([0.1, 0.2, 0.6])
        test_input = [0.005, 0.006, 0.0269]

        self.assertTrue(allclose(expected_lrs,
            self.test_func.loss_ratio_for(test_input)))
        # same thing, except the input is a numpy.ndarray type:
        self.assertTrue(allclose(expected_lrs,
            self.test_func.loss_ratio_for(numpy.array(test_input))))

    def test_loss_ratio_interp_many_values_clipped(self):
        """
        Given a list of IML values (abscissae), test for proper interpolation
        of loss ratios (ordinates).

        This test also ensures that input IML values are 'clipped' to the IML
        range defined for the vulnerability function.
        """
        expected_lrs = numpy.array([0.1, 0.2, 0.6])
        test_input = [0.0049, 0.006, 0.027]

        self.assertTrue(allclose(expected_lrs,
            self.test_func.loss_ratio_for(test_input)))
        # same thing, except the input is a numpy.ndarray type:
        self.assertTrue(allclose(expected_lrs,
            self.test_func.loss_ratio_for(numpy.array(test_input))))

    def test_cov_interp_single_value(self):
        """
        Test that single CoV values are properly interpolated.
        """
        # lower boundary:
        self.assertEqual(0.3, self.test_func.cov_for(0.005))
        # upper boundary:
        self.assertEqual(10, self.test_func.cov_for(0.0269))
        # between the first 2 IMLs:
        self.assertEqual(0.2, self.test_func.cov_for(0.006))

    def test_cov_interp_single_value_clipped(self):
        """
        Test that CoV interpolation properly clips out-of-range input values
        to the IML range defined for the vulnerability function.
        """
        # test low-end clipping:
        self.assertEqual(0.3, self.test_func.cov_for(0.0049))
        # test high-end clipping:
        self.assertEqual(10, self.test_func.cov_for(0.027))

    def test_cov_interp_many_values(self):
        """
        Given a list of IML values (abscissae), test for proper interpolation
        of CoVs.
        """
        expected_covs = numpy.array([0.3, 0.2, 10])
        test_input = [0.005, 0.006, 0.0269]

        self.assertTrue(allclose(expected_covs,
            self.test_func.cov_for(test_input)))
        # same thing, except the input is a numpy.ndarray type:
        self.assertTrue(allclose(expected_covs,
            self.test_func.cov_for(numpy.array(test_input))))

    def test_cov_interp_many_values_clipped(self):
        """
        Given a list of IML values (abscissae), test for proper interpolation
        of CoVs.

        This test also ensures that input IML values are 'clipped' to the IML
        range defined for the vulnerability function.
        """
        expected_covs = numpy.array([0.3, 0.2, 10])
        test_input = [0.0049, 0.006, 0.027]

        self.assertTrue(allclose(expected_covs,
            self.test_func.cov_for(test_input)))
        # same thing, except the input is a numpy.ndarray type:
        self.assertTrue(allclose(expected_covs,
            self.test_func.cov_for(numpy.array(test_input))))

    def test_is_empty(self):
        """
        Test the 'is_empty' property of a vulnerability function.
        """
        empty_func = shapes.VulnerabilityFunction([], [], [])

        # Test empty function:
        self.assertTrue(empty_func.is_empty)

        # Test non-empty function:
        self.assertFalse(self.test_func.is_empty)

    def test_iter(self):
        """
        Test iterability of a vulnerability function.
        """
        expected = zip(self.IMLS_GOOD, self.LOSS_RATIOS_GOOD, self.COVS_GOOD)

        # iterate and accumulate all of the vuln function values:
        actual = [x for x in self.test_func]

        self.assertEqual(expected, actual)


class SiteTestCase(unittest.TestCase):
    """
    Tests for the :py:class:`openquake.shapes.Site` class.
    """

    def test_sites_can_be_keys(self):
        """ Site objects can be dictionary keys,
        So must hash reliably."""
        lat = 10.5
        lon = -49.5
        first_site = shapes.Site(lon, lat)
        second_site = shapes.Site(lon, lat)
        sites = {}
        sites[first_site] = "one"
        sites[second_site] = "two"
        # BOTH will now be "two"! This is correct

        self.assertEqual(first_site, second_site)
        self.assertEqual(sites[first_site], "two")
        self.assertEqual(sites[second_site], "two")

    def test_sites_have_geo_accessors(self):
        lat = 10.5
        lon = -49.5
        first_site = shapes.Site(lon, lat)
        self.assertEqual(first_site.latitude, lat)
        self.assertEqual(first_site.longitude, lon)

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

    def test_eq(self):
        """
        Test Site equality comparisons. Two sites with the same lon/lat should
        be considered equal.
        """
        lon = 121.0
        lat = 29.0

        site1 = shapes.Site(lon, lat)
        site2 = shapes.Site(lon, lat)

        self.assertEqual(site1, site2)

    def test_eq_with_rounded_lon_lat(self):
        """
        Test Site equality comparisons when using high-precision lon/lat values
        (which are rounded down when the Site object is created).
        """
        site1 = shapes.Site(-121.0, 29.0000001)
        site2 = shapes.Site(-121.00000004, 29.00000006)

        self.assertEqual(site1, site2)

    def test_hash(self):
        """
        Verify that two Sites with the same lon/lat have the same __hash__().
        """
        lon = 121.0
        lat = 29.0

        site1 = shapes.Site(lon, lat)
        site2 = shapes.Site(lon, lat)

        self.assertEqual(site1.__hash__(), site2.__hash__())

    def test_hash_with_rounded_lon_lat(self):
        """
        Test the __hash__() equality of two Sites when using high-precision
        lon/lat values (which are rounded down when the Site object is
        created).
        """
        site1 = shapes.Site(-121.0, 29.0000001)
        site2 = shapes.Site(-121.00000004, 29.00000006)

        self.assertEqual(site1.__hash__(), site2.__hash__())


class ShapesUtilsTestCase(unittest.TestCase):
    '''
    Tests for utility methods in the shapes module.
    '''

    def test_multipoint_ewkt(self):
        '''
        Test typical usage of
        :py:function:`openquake.shapes.multipoint_ewkt_from_coords`
        '''
        expected_ewkt = \
            'SRID=4326;MULTIPOINT((-122.0 38.113), (-122.114 38.113))'

        coords = '38.113, -122.0, 38.113, -122.114'

        actual_ewkt = shapes.multipoint_ewkt_from_coords(coords)

        self.assertEqual(expected_ewkt, actual_ewkt)

    def test_multipoint_ewkt_round_float(self):
        '''
        Test usage of
        :py:function:`openquake.shapes.multipoint_ewkt_from_coords` to ensure
        that high-precision coordinate values are rounded down a reasonable
        level of precision.
        '''
        expected_ewkt = \
            'SRID=4326;MULTIPOINT((-122.0 38.1130001), (-122.114 38.113))'

        coords = '38.11300006, -122.00000001, 38.113, -122.114'

        actual_ewkt = shapes.multipoint_ewkt_from_coords(coords)

        self.assertEqual(expected_ewkt, actual_ewkt)

    def test_polygon_ewkt(self):
        '''
        Test typical usage of
        :py:function:`openquake.shapes.polygon_ewkt_from_coords`
        '''
        # Note that the first & last coord are the same to form a closed loop.
        expected_ewkt = (
            'SRID=4326;POLYGON((-122.0 38.113, -122.114 38.113, '
            '-122.57 38.111, -122.0 38.113))')

        coords = '38.113, -122.0, 38.113, -122.114, 38.111, -122.57'

        actual_ewkt = shapes.polygon_ewkt_from_coords(coords)

        self.assertEqual(expected_ewkt, actual_ewkt)

    def test_polygon_ewkt_round_float(self):
        '''
        Test usage of
        :py:function:`openquake.shapes.polygon_ewkt_from_coords` to ensure
        that high-precision coordinate values are rounded down a reasonable
        level of precision.
        '''
        # Note that the first & last coord are the same to form a closed loop.
        expected_ewkt = (
            'SRID=4326;POLYGON((-122.0 38.113, -122.114 38.113, '
            '-122.57 38.1110001, -122.0 38.113))')

        coords = \
            '38.113, -122.00000001, 38.113, -122.114, 38.11100006, -122.57'

        actual_ewkt = shapes.polygon_ewkt_from_coords(coords)

        self.assertEqual(expected_ewkt, actual_ewkt)

    def test_hdistance(self):
        """Expected values are taken from OpenSHA,
        org.opensha.commons.geo.LocationUtilsTest.testHorzDistance."""

        site1 = shapes.Site(0.0, 90.0)
        site2 = shapes.Site(20.4, 32.6)
        site3 = shapes.Site(20.0, 32.4)
        site4 = shapes.Site(0.0, -90.0)
        site5 = shapes.Site(20.2, 32.0)
        site6 = shapes.Site(20.6, 32.2)

        test = lambda result, site1, site2: self.assertAlmostEqual(
            result, shapes.hdistance(site1.latitude, site1.longitude,
                                     site2.latitude, site2.longitude),
            places=6
        )
        test(6382.5960025, site1, site2)
        test(6404.835013, site3, site1)
        test(13565.796382, site5, site4)
        test(13588.035392, site4, site6)
        test(43.6090311, site2, site3)
        test(48.2790582, site2, site6)
        test(69.3145862, site2, site5)
        test(60.6198752, site3, site6)
        test(48.2952067, site5, site3)
        test(43.7518411, site5, site6)

    def test_java_site(self):
        lon = -118.3
        lat = 34.12
        site = shapes.java_site(lon, lat)

        self.assertEquals('org.opensha.commons.data.Site',
                          site.__class__.__name__)
        self.assertAlmostEqual(lon, site.getLocation().getLongitude())
        self.assertAlmostEqual(lat, site.getLocation().getLatitude())


class FieldTestCase(unittest.TestCase):

    def setUp(self):
        self.gmf_string = open(helpers.get_data_path("gmfs.json")).readline()
        region = shapes.Region.from_coordinates(
                 [(-118.30, 34.12), (-118.18, 34.12),
                 (-118.18, 34.00), (-118.30, 34.00)])
        region.cell_size = 0.02
        self.grid = region.grid

    def test_can_serialize_field(self):
        field_set = shapes.FieldSet.from_json(self.gmf_string, grid=self.grid)
        for field in field_set:
            print field.field
            self.assertTrue(field)
            print field.get(5, 5)


class GridTestCase(unittest.TestCase):

    def _test_expected_points(self, grid):
        for i, point in enumerate(grid):
            # check point iteration order
            expected_row = int(i / grid.columns)
            expected_column = i % grid.columns

            self.assertEquals((expected_row, expected_column),
                              (point.row, point.column))

    def test_grid_iterates_all_points(self):
        # basic grid
        constraint = shapes.RegionConstraint.from_simple(
            (10.0, 10.0), (100.0, 100.0))
        constraint.cell_size = 10.0
        self._test_expected_points(constraint.grid)

        # rounding (from the NSHMP smoke test)
        constraint = shapes.RegionConstraint.from_simple(
            (-118.3, 34.0), (-118.18, 34.12))
        constraint.cell_size = 0.02
        self._test_expected_points(constraint.grid)


class RegionTestCase(unittest.TestCase):
    INSIDE = [(50, 50),
              (11, 11),
              (99, 99)]

    OUTSIDE = [(50, 9),
               (9, 50),
               (9, 9),
               (101, 50),
               (50, 101),
               (101, 101)]

    def _check_match(self, constraint):
        for point in self.INSIDE:
            self.assert_(constraint.match(point),
                         'did not match inside: %s' % str(point))

        for point in self.OUTSIDE:
            self.assert_(not constraint.match(point),
                         'matched outside: %s' % str(point))

    def test_from_coordinates(self):
        constraint = shapes.RegionConstraint.from_coordinates(
                [(10.0, 100.0), (100.0, 100.0), (100.0, 10.0), (10.0, 10.0)])
        self._check_match(constraint)

    def test_from_simple(self):
        constraint = shapes.RegionConstraint.from_simple(
            (10.0, 10.0), (100.0, 100.0))
        self._check_match(constraint)

    def test_region_sites_boundary_1(self):
        # check that points really close to the
        # border of the region (longitude) have a corresponding
        # grid point. This is done by adding an additional
        # column to the grid (in this case [(2.5, 2.0),
        # (2.5, 1.5), (2.5, 1.0)]), even if the points that
        # are the center of the cell are outside the region.
        region = shapes.Region.from_coordinates(
            [(1.0, 2.0), (2.3, 2.0), (2.3, 1.0), (1.0, 1.0)])

        region.cell_size = 0.5

        expected_sites = set([
            shapes.Site(1.0, 1.0), shapes.Site(1.5, 1.0),
            shapes.Site(2.0, 1.0), shapes.Site(1.0, 1.5),
            shapes.Site(1.5, 1.5), shapes.Site(2.0, 1.5),
            shapes.Site(1.0, 2.0), shapes.Site(1.5, 2.0),
            shapes.Site(2.0, 2.0), shapes.Site(2.5, 2.0),
            shapes.Site(2.5, 1.0), shapes.Site(2.5, 1.5)])

        self.assertEquals(expected_sites, set(region.grid.centers()))

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(2.25, 2.0))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(2.27, 2.0))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(2.30, 2.0))) in region.grid.centers())

        # check we can ask for valid grid points from
        # the sites that represent the center of the cells
        for cell_center in region.grid.centers():
            self.assertTrue(region.grid.site_inside(cell_center))

    def test_region_sites_boundary_2(self):
        # same as above, but for latitude
        region = shapes.Region.from_coordinates(
            [(1.0, 2.0), (2.0, 2.0), (2.0, 0.6), (1.0, 0.6)])

        region.cell_size = 0.5

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(1.5, 0.61))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(1.5, 0.60))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(1.5, 2.0))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(1.5, 1.9))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(1.5, 1.8))) in region.grid.centers())

        # check we can ask for valid grid points from
        # the sites that represent the center of the cells
        for cell_center in region.grid.centers():
            self.assertTrue(region.grid.site_inside(cell_center))

    def test_region_sites_boundary_3(self):
        region = shapes.RegionConstraint.from_simple((0.0, 1.0), (1.0, 0.0))

        # Site(1.1, 1.1) is outside the region
        self.assertFalse(region.match(shapes.Site(1.1, 1.1)))

        # but inside the underlying grid because we add an
        # additional row and column
        self.assertTrue(region.grid.site_inside(shapes.Site(1.1, 1.1)))

        # same as above
        self.assertFalse(region.match(shapes.Site(1.04, 1.04)))
        self.assertFalse(region.match(shapes.Site(1.05, 1.05)))

        self.assertTrue(region.grid.site_inside(shapes.Site(1.04, 1.04)))
        self.assertTrue(region.grid.site_inside(shapes.Site(1.05, 1.05)))

        # this is too far away, even outside the grid
        self.assertRaises(ValueError,
                region.grid.point_at, shapes.Site(30.0, 30.0))

        region = shapes.RegionConstraint.from_simple((0.0, 1.0), (1.0, 0.0))
        region.cell_size = 0.5

        # same, points are outside the region
        self.assertFalse(region.match(shapes.Site(1.24, 1.24)))
        self.assertFalse(region.match(shapes.Site(1.25, 1.25)))
        self.assertFalse(region.match(shapes.Site(-0.24, -0.24)))
        self.assertFalse(region.match(shapes.Site(-0.25, -0.25)))

        # but inside the grid
        self.assertTrue(region.grid.site_inside(shapes.Site(1.24, 1.24)))
        self.assertTrue(region.grid.site_inside(shapes.Site(1.25, 1.25)))
        self.assertTrue(region.grid.site_inside(shapes.Site(-0.25, -0.25)))
        self.assertTrue(region.grid.site_inside(shapes.Site(-0.25, -0.24)))

        # latitude too low, too high
        self.assertFalse(region.grid.site_inside(shapes.Site(-0.25, -0.26)))
        self.assertFalse(region.grid.site_inside(shapes.Site(-0.25, 1.76)))

        # longitude too low, too high
        self.assertFalse(region.grid.site_inside(shapes.Site(1.76, 1.5)))
        self.assertFalse(region.grid.site_inside(shapes.Site(-0.26, 1.5)))
