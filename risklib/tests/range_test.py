# -*- coding: utf-8 -*-
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

import numpy
import unittest

from risklib.curve import Curve


class RangeClipTestCase(unittest.TestCase):

    TEST_IMLS = [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269]

    def test_clip_low_iml_values(self):
        """
        Test :py:method:`risklib.range.Curve.range_clip` to
        ensure that low values are clipped to the lowest valid value in the
        IML range.
        """
        self.assertEqual(0.005, Curve.range_clip(0.0049, self.TEST_IMLS))

    def test_clip_low_imls_many_values(self):
        """
        Test :py:method:`risklib.range.Curve.range_clip` to
        ensure that low values are clipped to the lowest valid value in the
        IML range.
        """
        expected_imls = numpy.array([0.005, 0.005, 0.005])
        test_input = [0.0049, 0.00001, 0.002]

        numpy.testing.assert_allclose(
            expected_imls, Curve.range_clip(test_input, self.TEST_IMLS))
        # same test, except with a numpy.array-type input:
        numpy.testing.assert_allclose(
            expected_imls,
            Curve.range_clip(numpy.array(test_input), self.TEST_IMLS))

    def test_clip_high_iml_values(self):
        """
        Test :py:method:`risklib.range.Curve.range_clip` to
        ensure that the high values are clipped to the highest valid value in
        the IML range.
        """
        self.assertEqual(0.0269, Curve.range_clip(0.027, self.TEST_IMLS))

    def test_clip_high_imls_many_values(self):
        """
        Test :py:method:`risklib.range.Curve.range_clip` to
        ensure that the high values are clipped to the highest valid value in
        the IML range.
        """
        expected_imls = numpy.array([0.0269, 0.0269, 0.0269])
        test_input = [0.027, 0.3, 10]

        numpy.testing.assert_allclose(
            expected_imls,
            Curve.range_clip(test_input, self.TEST_IMLS))
        # same test, except with a numpy.array-type input:
        numpy.testing.assert_allclose(
            expected_imls,
            Curve.range_clip(numpy.array(test_input), self.TEST_IMLS))

    def test_clip_iml_with_normal_value(self):
        """
        Test :py:method:`risklib.range.Curve.range_clip` to
        ensure that normal values (values within the defined IML range) are not
        changed.
        """
        valid_imls = numpy.array([0.005, 0.0051, 0.0268, 0.0269])
        for i in valid_imls:
            self.assertEqual(i, Curve.range_clip(i, valid_imls))

    def test_clip_imls_with_many_normal_values(self):
        """
        Test :py:method:`risklib.range.Curve.range_clip` to
        ensure that normal values (values within the defined IML range) are not
        changed.
        """
        valid_imls = [0.005, 0.0269, 0.0051, 0.0268]
        expected_result = numpy.array(valid_imls)

        numpy.testing.assert_allclose(
            expected_result,
            Curve.range_clip(valid_imls, self.TEST_IMLS))
        # same test, except with numpy.array-type input:
        numpy.testing.assert_allclose(
            expected_result,
            Curve.range_clip(numpy.array(valid_imls), self.TEST_IMLS))
