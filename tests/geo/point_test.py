# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
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
import numpy

from nhlib import geo
from nhlib.geo._utils import EARTH_RADIUS


class PointTestCase(unittest.TestCase):

    def test_point_at_1(self):
        p1 = geo.Point(0.0, 0.0, 10.0)
        expected = geo.Point(0.0635916667129, 0.0635916275455, 15.0)
        self.assertEqual(expected, p1.point_at(10.0, 5.0, 45.0))

    def test_point_at_2(self):
        p1 = geo.Point(0.0, 0.0, 10.0)
        expected = geo.Point(0.0635916667129, 0.0635916275455, 5.0)
        self.assertEqual(expected, p1.point_at(10.0, -5.0, 45.0))

    def test_azimuth(self):
        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.5, 0.5)

        self.assertAlmostEqual(44.9989091554, p1.azimuth(p2))

    def test_azimuth_over_180_degree(self):
        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.5, 0.5)
        self.assertAlmostEqual(225.0010908, p2.azimuth(p1))

    def test_horizontal_distance(self):
        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.5, 0.5)

        self.assertAlmostEqual(78.6261876769, p1.horizontal_distance(p2), 4)

    def test_distance(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.5, 0.5, 5.0)

        self.assertAlmostEqual(78.7849704355, p1.distance(p2))

    def test_equally_spaced_points_1(self):
        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.190775520815, 0.190774854966)

        points = p1.equally_spaced_points(p2, 10.0)
        self.assertEqual(4, len(points))

        self.assertEqual(p1, points[0])  # first point is the start point
        self.assertEqual(p2, points[3])  # last point is the end point

        expected = geo.Point(0.0635916966572, 0.0635916574897, 0.0)
        self.assertEqual(expected, points[1])

        expected = geo.Point(0.127183510817, 0.127183275812, 0.0)
        self.assertEqual(expected, points[2])

    def test_equally_spaced_points_2(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.134898484431, 0.134898249018, 21.2132034356)

        points = p1.equally_spaced_points(p2, 10.0)
        self.assertEqual(4, len(points))

        self.assertEqual(p1, points[0])  # first point is the start point
        self.assertEqual(p2, points[3])  # last point is the end point

        expected = geo.Point(0.0449661107016, 0.0449660968538, 7.07106781187)
        self.assertEqual(expected, points[1])

        expected = geo.Point(0.0899322629466, 0.0899321798598, 14.1421356237)
        self.assertEqual(expected, points[2])

    def test_equally_spaced_points_3(self):
        """
        Corner case where the end point is equal to the start point.
        In this situation we have just one point (the start/end point).
        """

        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.0, 0.0)

        points = p1.equally_spaced_points(p2, 10.0)

        self.assertEqual(1, len(points))
        self.assertEqual(p1, points[0])
        self.assertEqual(p2, points[0])

    def test_equally_spaced_points_4(self):
        p1 = geo.Point(0, 0, 10)
        p2 = geo.Point(0, 0, 7)
        points = p1.equally_spaced_points(p2, 1)
        self.assertEqual(points,
                         [p1, geo.Point(0, 0, 9), geo.Point(0, 0, 8), p2])

    def test_equally_spaced_points_last_point(self):
        points = geo.Point(0, 50).equally_spaced_points(geo.Point(10, 50), 10)
        self.assertAlmostEqual(points[-1].latitude, 50, places=2)

    def test_longitude_inside_range(self):
        self.assertRaises(ValueError, geo.Point, 180.1, 0.0, 0.0)
        self.assertRaises(ValueError, geo.Point, -180.1, 0.0, 0.0)

        geo.Point(180.0, 0.0)
        geo.Point(-180.0, 0.0)

    def test_latitude_inside_range(self):
        self.assertRaises(ValueError, geo.Point, 0.0, 90.1, 0.0)
        self.assertRaises(ValueError, geo.Point, 0.0, -90.1, 0.0)

        geo.Point(0.0, 90.0, 0.0)
        geo.Point(0.0, -90.0, 0.0)

    def test_depth_inside_range(self):
        self.assertRaises(ValueError, geo.Point, 0.0, 0.0, EARTH_RADIUS)
        self.assertRaises(ValueError, geo.Point, 0.0, 0.0, EARTH_RADIUS + 0.1)

        geo.Point(0.0, 90.0, EARTH_RADIUS - 0.1)

    def test_position_vector_1(self):
        point = geo.Point(0.0, 0.0, 0.0)

        self.assertTrue(numpy.allclose(
                [6371.0, 0.0, 0.0], point.position_vector()))

    def test_position_vector_2(self):
        point = geo.Point(0.0, 90.0, 0.0)

        self.assertTrue(numpy.allclose(
                [0.0, 0.0, 6371.0], point.position_vector()))

    def test_position_vector_3(self):
        point = geo.Point(0.0, 90.0, 10.0)

        self.assertTrue(numpy.allclose(
                [0.0, 0.0, 6361.0], point.position_vector()))
