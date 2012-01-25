# encoding: utf-8

import unittest

from nhe.common import geo


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

        self.assertEqual(p1, points[0]) # first point is the start point
        self.assertEqual(p2, points[3]) # last point is the end point

        expected = geo.Point(0.0635916966572, 0.0635916574897, 0.0)
        self.assertEqual(expected, points[1])

        expected = geo.Point(0.127183510817, 0.127183275812, 0.0)
        self.assertEqual(expected, points[2])

    def test_equally_spaced_points_2(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.134898484431, 0.134898249018, 21.2132034356)

        points = p1.equally_spaced_points(p2, 10.0)
        self.assertEqual(4, len(points))

        self.assertEqual(p1, points[0]) # first point is the start point
        self.assertEqual(p2, points[3]) # last point is the end point

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

    def test_longitude_inside_range(self):
        self.assertRaises(RuntimeError, geo.Point, 180.1, 0.0, 0.0)
        self.assertRaises(RuntimeError, geo.Point, -180.1, 0.0, 0.0)

        geo.Point(180.0, 0.0)
        geo.Point(-180.0, 0.0)

    def test_latitude_inside_range(self):
        self.assertRaises(RuntimeError, geo.Point, 0.0, 90.1, 0.0)
        self.assertRaises(RuntimeError, geo.Point, 0.0, -90.1, 0.0)

        geo.Point(0.0, 90.0, 0.0)
        geo.Point(0.0, -90.0, 0.0)


class LineTestCase(unittest.TestCase):

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

    def test_one_point_needed(self):
        self.assertRaises(RuntimeError, geo.Line, [])

    def test_remove_adjacent_duplicates(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 1.0, 0.0)
        p3 = geo.Point(0.0, 1.0, 0.0)
        p4 = geo.Point(0.0, 2.0, 0.0)
        p5 = geo.Point(0.0, 3.0, 0.0)
        p6 = geo.Point(0.0, 3.0, 0.0)

        expected = [p1, p2, p4, p5]
        self.assertEquals(expected, geo.Line([p1, p2, p3, p4, p5, p6]).points)

    def test_must_not_intersect_itself(self):
        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.0, 1.0)
        p3 = geo.Point(1.0, 1.0)
        p4 = geo.Point(0.0, 0.5)

        self.assertRaises(RuntimeError, geo.Line, [p1, p2, p3, p4])

        # doesn't take into account depth
        p1 = geo.Point(0.0, 0.0, 1.0)
        p2 = geo.Point(0.0, 1.0, 1.0)
        p3 = geo.Point(1.0, 1.0, 1.0)
        p4 = geo.Point(0.0, 0.5, 1.5)

        self.assertRaises(RuntimeError, geo.Line, [p1, p2, p3, p4])
