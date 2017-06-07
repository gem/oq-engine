# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest

from openquake.hazardlib import geo


class LineResampleTestCase(unittest.TestCase):
    def test_resample(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 0.127183341091, 14.1421356237)
        p3 = geo.Point(0.134899286793, 0.262081472606, 35.3553390593)

        resampled = geo.Line([p1, p2, p3]).resample(10.0)

        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 0.0635916705456, 7.07106781187)
        p3 = geo.Point(0.0, 0.127183341091, 14.1421356237)
        p4 = geo.Point(0.0449662998195, 0.172149398777, 21.2132034356)
        p5 = geo.Point(0.0899327195183, 0.217115442616, 28.2842712475)
        p6 = geo.Point(0.134899286793, 0.262081472606, 35.3553390593)

        expected = geo.Line([p1, p2, p3, p4, p5, p6])
        self.assertEqual(expected, resampled)

    def test_resample_2(self):
        """
        Line made of 3 points (aligned in the same direction) equally spaced
        (spacing equal to 10 km). The resampled line contains 2 points
        (with spacing of 30 km) consistent with the number of points
        as predicted by n = round(20 / 30) + 1.
        """

        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.0, 0.089932202939476777)
        p3 = geo.Point(0.0, 0.1798644058789465)

        self.assertEqual(2, len(geo.Line([p1, p2, p3]).resample(30.0)))

    def test_resample_3(self):
        """
        Line made of 3 points (aligned in the same direction) equally spaced
        (spacing equal to 10 km). The resampled line contains 1 point
        (with spacing of 50 km) consistent with the number of points
        as predicted by n = round(20 / 50) + 1.
        """

        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.0, 0.089932202939476777)
        p3 = geo.Point(0.0, 0.1798644058789465)

        self.assertEqual(1, len(geo.Line([p1, p2, p3]).resample(50.0)))

        self.assertEqual(geo.Line([p1]), geo.Line(
                [p1, p2, p3]).resample(50.0))

    def test_resample_4(self):
        """
        When resampling a line with a single point, the result
        is a one point line with the same point.
        """

        p1 = geo.Point(0.0, 0.0)

        self.assertEqual(geo.Line([p1]), geo.Line([p1]).resample(10.0))


class LineCreationTestCase(unittest.TestCase):
    def test_one_point_needed(self):
        self.assertRaises(ValueError, geo.Line, [])

    def test_remove_adjacent_duplicates(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 1.0, 0.0)
        p3 = geo.Point(0.0, 1.0, 0.0)
        p4 = geo.Point(0.0, 2.0, 0.0)
        p5 = geo.Point(0.0, 3.0, 0.0)
        p6 = geo.Point(0.0, 3.0, 0.0)

        expected = [p1, p2, p4, p5]
        self.assertEquals(expected, geo.Line([p1, p2, p3, p4, p5, p6]).points)


class LineResampleToNumPointsTestCase(unittest.TestCase):
    def test_simple(self):
        points = [geo.Point(0, 0), geo.Point(0.1, 0.3)]

        line = geo.Line(points).resample_to_num_points(3)
        expected_points = [geo.Point(0, 0), geo.Point(0.05, 0.15),
                           geo.Point(0.1, 0.3)]
        self.assertEqual(line.points, expected_points)

        line = geo.Line(points).resample_to_num_points(4)
        expected_points = [geo.Point(0, 0), geo.Point(0.0333333, 0.1),
                           geo.Point(0.0666666, 0.2), geo.Point(0.1, 0.3)]
        self.assertEqual(line.points, expected_points)

    def test_fewer_points(self):
        points = [geo.Point(i / 10., 0) for i in range(13)]

        line = geo.Line(points).resample_to_num_points(2)
        expected_points = [points[0], points[-1]]
        self.assertEqual(line.points, expected_points)

        line = geo.Line(points).resample_to_num_points(4)
        expected_points = points[::4]
        self.assertEqual(line.points, expected_points)

    def test_cutting_corners(self):
        p1 = geo.Point(0., 0.)
        p2 = p1.point_at(1, 0, 1)
        p3 = p2.point_at(1, 0, 179)
        p4 = p3.point_at(5, 0, 90)
        line = geo.Line([p1, p2, p3, p4]).resample_to_num_points(3)
        self.assertEqual(len(line), 3)

    def test_line_of_one_point(self):
        line = geo.Line([geo.Point(0, 0)])
        self.assertRaises(AssertionError, line.resample_to_num_points, 10)

    def test_hangup(self):
        p1 = geo.Point(0.00899322032502, 0., 0.)
        p2 = geo.Point(0.01798644058385, 0., 1.)
        p3 = geo.Point(0.02697966087241, 0., 2.)
        line = geo.Line([p1, p2, p3]).resample_to_num_points(3)
        self.assertEqual(line.points, [p1, p2, p3])

    def test_single_segment(self):
        line = geo.Line([
            geo.Point(0., 0.00899322029302, 0.),
            geo.Point(0.03344582378948, -0.00936927115925, 4.24264069)
        ])
        line = line.resample_to_num_points(7)
        self.assertEqual(len(line), 7)


class LineLengthTestCase(unittest.TestCase):
    def test(self):
        line = geo.Line([geo.Point(0, 0), geo.Point(0, 1), geo.Point(1, 2)])
        length = line.get_length()
        expected_length = line.points[0].distance(line.points[1]) \
                          + line.points[1].distance(line.points[2])
        self.assertEqual(length, expected_length)
