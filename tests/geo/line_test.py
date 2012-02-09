import unittest

from nhe import geo


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

    def test_must_not_intersect_itself(self):
        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.0, 1.0)
        p3 = geo.Point(1.0, 1.0)
        p4 = geo.Point(0.0, 0.5)

        self.assertRaises(ValueError, geo.Line, [p1, p2, p3, p4])

        # doesn't take into account depth
        p1 = geo.Point(0.0, 0.0, 1.0)
        p2 = geo.Point(0.0, 1.0, 1.0)
        p3 = geo.Point(1.0, 1.0, 1.0)
        p4 = geo.Point(0.0, 0.5, 1.5)

        self.assertRaises(ValueError, geo.Line, [p1, p2, p3, p4])

    def test_invalid_line_crossing_international_date_line(self):
        broken_points = [geo.Point(178, 0), geo.Point(178, 10),
                         geo.Point(-178, 0), geo.Point(170, 5)]
        self.assertRaises(ValueError, geo.Line, broken_points)

    def test_valid_line_crossing_international_date_line(self):
        points = [geo.Point(178, 0), geo.Point(178, 10),
                  geo.Point(179, 5), geo.Point(-178, 5)]
        geo.Line(points)
