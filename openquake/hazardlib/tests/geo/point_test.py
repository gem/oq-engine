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

import numpy

from openquake.hazardlib import geo
from openquake.hazardlib.geo.utils import spherical_to_cartesian
from openquake.hazardlib.geo.geodetic import EARTH_RADIUS, EARTH_ELEVATION


class PointPointAtTestCase(unittest.TestCase):
    def test_point_at_1(self):
        p1 = geo.Point(0.0, 0.0, 10.0)
        expected = geo.Point(0.0635916667129, 0.0635916275455, 15.0)
        self.assertEqual(expected, p1.point_at(10.0, 5.0, 45.0))

    def test_point_at_2(self):
        p1 = geo.Point(0.0, 0.0, 10.0)
        expected = geo.Point(0.0635916667129, 0.0635916275455, 5.0)
        self.assertEqual(expected, p1.point_at(10.0, -5.0, 45.0))

    def test_point_at_topo(self):
        p1 = geo.Point(0.0, 0.0, 10.0)
        expected = geo.Point(0.0635916667129, 0.0635916275455, -5.0)
        self.assertEqual(expected, p1.point_at(10.0, -15.0, 45.0))


class PointAzimuthTestCase(unittest.TestCase):
    def test_azimuth(self):
        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.5, 0.5)

        self.assertAlmostEqual(44.9989091554, p1.azimuth(p2))

    def test_azimuth_over_180_degree(self):
        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.5, 0.5)
        self.assertAlmostEqual(225.0010908, p2.azimuth(p1))


class PointDistanceTestCase(unittest.TestCase):
    def test_distance(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.5, 0.5, 5.0)

        self.assertAlmostEqual(78.7849704355, p1.distance(p2), places=4)


class PointEquallySpacedPointsTestCase(unittest.TestCase):
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


class PointCreationTestCase(unittest.TestCase):
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
        self.assertRaises(ValueError, geo.Point, 0.0, 0.0, EARTH_ELEVATION)
        self.assertRaises(ValueError, geo.Point, 0.0, 0.0, EARTH_ELEVATION - 0.1)

        geo.Point(0.0, 90.0, EARTH_RADIUS - 0.1)
        geo.Point(0.0, 90.0, EARTH_ELEVATION + 0.1)


class PointFromVectorTestCase(unittest.TestCase):
    def test_from_vector(self):
        point = geo.Point(12.34, -56.78, 91.011)
        vector = spherical_to_cartesian(point.x, point.y, point.z)
        self.assertEqual(point, geo.Point.from_vector(vector))


class PointToPolygonTestCase(unittest.TestCase):
    def test(self):
        point = geo.Point(10.43, -35.1)
        polygon = point.to_polygon(radius=20)
        elons = [10.6498428, 10.6488315, 10.6457115, 10.6405114, 10.6332800,
                 10.6240861, 10.6130172, 10.6001793, 10.5856956, 10.5697055,
                 10.5523630, 10.5338356, 10.5143024, 10.4939523, 10.4729824,
                 10.4515959, 10.4300000, 10.4084041, 10.3870176, 10.3660477,
                 10.3456976, 10.3261644, 10.3076370, 10.2902945, 10.2743044,
                 10.2598207, 10.2469828, 10.2359139, 10.2267200, 10.2194886,
                 10.2142885, 10.2111685, 10.2101572, 10.2112631, 10.2144741,
                 10.2197581, 10.2270629, 10.2363172, 10.2474309, 10.2602964,
                 10.2747894, 10.2907702, 10.3080851, 10.3265677, 10.3460406,
                 10.3663172, 10.3872032, 10.4084987, 10.4300000, 10.4515013,
                 10.4727968, 10.4936828, 10.5139594, 10.5334323, 10.5519149,
                 10.5692298, 10.5852106, 10.5997036, 10.6125691, 10.6236828,
                 10.6329371, 10.6402419, 10.6455259, 10.6487369, 10.6498428]
        elats = [-35.0998016, -35.1174332, -35.1348988, -35.1520301,
                 -35.1686616, -35.1846330, -35.1997900, -35.2139861,
                 -35.2270840, -35.2389571, -35.2494905, -35.2585822,
                 -35.2661441, -35.2721029, -35.2764010, -35.2789966,
                 -35.2798646, -35.2789966, -35.2764010, -35.2721029,
                 -35.2661441, -35.2585822, -35.2494905, -35.2389571,
                 -35.2270840, -35.2139861, -35.1997900, -35.1846330,
                 -35.1686616, -35.1520301, -35.1348988, -35.1174332,
                 -35.0998016, -35.0821737, -35.0647194, -35.0476066,
                 -35.0309997, -35.0150583, -34.9999357, -34.9857768,
                 -34.9727176, -34.9608831, -34.9503870, -34.9413296,
                 -34.9337978, -34.9278636, -34.9235839, -34.9209996,
                 -34.9201354, -34.9209996, -34.9235839, -34.9278636,
                 -34.9337978, -34.9413296, -34.9503870, -34.9608831,
                 -34.9727176, -34.9857768, -34.9999357, -35.0150583,
                 -35.0309997, -35.0476066, -35.0647194, -35.0821737,
                 -35.0998016]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)
        self.assertAlmostEqual(polygon.lons.mean(), point.x, delta=1e-2)
        self.assertAlmostEqual(polygon.lats.mean(), point.y, delta=1e-2)


class PointCloserThanTestCase(unittest.TestCase):
    def test_no_depths(self):
        p = geo.Point(20, 30)
        mesh = geo.Mesh(numpy.array([[18., 19., 20., 21., 22.]] * 3),
                        numpy.array([[29] * 5, [30] * 5, [31] * 5]),
                        depths=None)
        closer = p.closer_than(mesh, 120)
        self.assertEqual(closer.dtype, bool)
        ec = [[0, 0, 1, 0, 0],
              [0, 1, 1, 1, 0],
              [0, 0, 1, 0, 0]]
        numpy.testing.assert_array_equal(closer, ec)
        closer = p.closer_than(mesh, 100)
        ec = [[0, 0, 0, 0, 0],
              [0, 1, 1, 1, 0],
              [0, 0, 0, 0, 0]]
        numpy.testing.assert_array_equal(closer, ec)

    def test_point_depth(self):
        p = geo.Point(0, 0, 10)
        mesh = geo.Mesh(numpy.array([0.1, 0.2, 0.3, 0.4]),
                        numpy.array([0., 0., 0., 0.]),
                        depths=None)
        closer = p.closer_than(mesh, 30)
        numpy.testing.assert_array_equal(closer, [1, 1, 0, 0])
        closer = p.closer_than(mesh, 35)
        numpy.testing.assert_array_equal(closer, [1, 1, 1, 0])
        closer = p.closer_than(mesh, 15)
        numpy.testing.assert_array_equal(closer, [1, 0, 0, 0])

    def test_point_topo(self):
        p = geo.Point(0, 0, -5)
        mesh = geo.Mesh(numpy.array([0.1, 0.2, 0.3, 0.4]),
                        numpy.array([0., 0., 0., 0.]),
                        depths=None)
        closer = p.closer_than(mesh, 30)
        numpy.testing.assert_array_equal(closer, [1, 1, 0, 0])
        closer = p.closer_than(mesh, 35)
        numpy.testing.assert_array_equal(closer, [1, 1, 1, 0])
        closer = p.closer_than(mesh, 15)
        numpy.testing.assert_array_equal(closer, [1, 0, 0, 0])

    def test_mesh_depth(self):
        p = geo.Point(0.5, -0.5)
        mesh = geo.Mesh(numpy.array([0.5, 0.5, 0.5, 0.5]),
                        numpy.array([-0.5, -0.5, -0.5, -0.5]),
                        numpy.array([0., 1., 2., 3.]))
        closer = p.closer_than(mesh, 0.1)
        numpy.testing.assert_array_equal(closer, [1, 0, 0, 0])
        closer = p.closer_than(mesh, 1.5)
        numpy.testing.assert_array_equal(closer, [1, 1, 0, 0])
        closer = p.closer_than(mesh, 3)
        numpy.testing.assert_array_equal(closer, [1, 1, 1, 1])

    def test_mesh_topo(self):
        p = geo.Point(0.5, -0.5)
        mesh = geo.Mesh(numpy.array([0.5, 0.5, 0.5, 0.5]),
                        numpy.array([-0.5, -0.5, -0.5, -0.5]),
                        numpy.array([0., -1., -2., -3.]))
        closer = p.closer_than(mesh, 0.1)
        numpy.testing.assert_array_equal(closer, [1, 0, 0, 0])
        closer = p.closer_than(mesh, 1.5)
        numpy.testing.assert_array_equal(closer, [1, 1, 0, 0])
        closer = p.closer_than(mesh, 3)
        numpy.testing.assert_array_equal(closer, [1, 1, 1, 1])

    def test_both_depths(self):
        p = geo.Point(3, 7, 9)
        mesh = geo.Mesh(numpy.array([2.9, 2.9, 3., 3., 3.1, 3.1]),
                        numpy.array([7., 7.1, 6.9, 7.1, 6.8, 7.2]),
                        numpy.array([20., 30., 10., 20., 40., 50.]))
        closer = p.closer_than(mesh, 20)
        numpy.testing.assert_array_equal(closer, [1, 0, 1, 1, 0, 0])
        closer = p.closer_than(mesh, 40)
        numpy.testing.assert_array_equal(closer, [1, 1, 1, 1, 1, 0])
        closer = p.closer_than(mesh, 10)
        numpy.testing.assert_array_equal(closer, [0, 0, 0, 0, 0, 0])
        closer = p.closer_than(mesh, 60)
        numpy.testing.assert_array_equal(closer, [1, 1, 1, 1, 1, 1])

    def test_both_topo(self):
        p = geo.Point(3, 7, -1)
        mesh = geo.Mesh(numpy.array([2.9, 2.9, 3., 3., 3.1, 3.1]),
                        numpy.array([7., 7.1, 6.9, 7.1, 6.8, 7.2]),
                        numpy.array([-2., -3., -1., -2., -4., -5.]))
        closer = p.closer_than(mesh, 10)
        numpy.testing.assert_array_equal(closer, [0, 0, 0, 0, 0, 0])
        closer = p.closer_than(mesh, 15)
        numpy.testing.assert_array_equal(closer, [1, 0, 1, 1, 0, 0])
        closer = p.closer_than(mesh, 20)
        numpy.testing.assert_array_equal(closer, [1, 1, 1, 1, 0, 0])
        closer = p.closer_than(mesh, 30)
        numpy.testing.assert_array_equal(closer, [1, 1, 1, 1, 1, 1])


class PointWktTestCase(unittest.TestCase):
    def test_point_wkt2d(self):
        pt = geo.Point(13.5, 17.8)
        self.assertEqual('POINT(13.5 17.8)', pt.wkt2d)

        # Test a point with depth; the 2d wkt should be the same
        pt = geo.Point(13.5, 17.8, 1.5)
        self.assertEqual('POINT(13.5 17.8)', pt.wkt2d)


class DistanceToMeshTestCase(unittest.TestCase):
    def test_no_depths(self):
        p = geo.Point(20, 30)
        mesh = geo.Mesh(numpy.array([[18., 19., 20.]] * 3),
                        numpy.array([[29.] * 3, [30.] * 3, [31.] * 3]),
                        depths=None)
        distances = p.distance_to_mesh(mesh, with_depths=False)
        ed = [[223.21812393, 147.4109544,  111.19492664],
              [192.59281778,  96.29732568,   0],
              [221.53723588, 146.77568123, 111.19492664]]
        numpy.testing.assert_array_almost_equal(distances, ed)

    # this is the case when computing Repi
    def test_neglect_depths(self):
        p = geo.Point(0.5, -0.5, 10)
        mesh = geo.Mesh(numpy.array([0.5, 0.5, 0.5, 0.5]),
                        numpy.array([-0.5, -0.5, -0.5, -0.5]),
                        numpy.array([0., -1., -2., -3.]))
        distances = p.distance_to_mesh(mesh, with_depths=False)
        ed = [0, 0, 0, 0]
        numpy.testing.assert_array_almost_equal(distances, ed)

    def test_point_depth(self):
        p = geo.Point(0, 0, 10)
        mesh = geo.Mesh(numpy.array([0.1, 0.2, 0.3, 0.4]),
                        numpy.array([0., 0., 0., 0.]),
                        depths=None)
        distances = p.distance_to_mesh(mesh)
        ed = [14.95470217, 24.38385672, 34.82510666, 45.58826465]
        numpy.testing.assert_array_almost_equal(distances, ed)

    def test_point_topo(self):
        p = geo.Point(0, 0, -5)
        mesh = geo.Mesh(numpy.array([0.1, 0.2, 0.3, 0.4]),
                        numpy.array([0., 0., 0., 0.]),
                        depths=None)
        distances = p.distance_to_mesh(mesh)
        ed = [12.19192836, 22.79413233, 33.73111403, 44.75812634]
        numpy.testing.assert_array_almost_equal(distances, ed)

    def test_mesh_depth(self):
        p = geo.Point(0.5, -0.5)
        mesh = geo.Mesh(numpy.array([0.5, 0.5, 0.5, 0.5]),
                        numpy.array([-0.5, -0.5, -0.5, -0.5]),
                        numpy.array([0., 1., 2., 3.]))
        distances = p.distance_to_mesh(mesh)
        ed = [0., 1., 2., 3.]
        numpy.testing.assert_array_almost_equal(distances, ed)

    def test_mesh_topo(self):
        p = geo.Point(0.5, -0.5)
        mesh = geo.Mesh(numpy.array([0.5, 0.5, 0.5, 0.5]),
                        numpy.array([-0.5, -0.5, -0.5, -0.5]),
                        numpy.array([0., -1., -2., -3.]))
        distances = p.distance_to_mesh(mesh)
        ed = [0., 1., 2., 3.]
        numpy.testing.assert_array_almost_equal(distances, ed)

    def test_both_depths(self):
        p = geo.Point(3, 7, 9)
        mesh = geo.Mesh(numpy.array([2.9, 2.9, 3., 3., 3.1, 3.1]),
                        numpy.array([7., 7.1, 6.9, 7.1, 6.8, 7.2]),
                        numpy.array([20., 30., 10., 20., 40., 50.]))
        distances = p.distance_to_mesh(mesh)
        ed = [15.58225761, 26.19968783, 11.16436819, 15.64107148,
              39.71688472, 47.93043417]
        numpy.testing.assert_array_almost_equal(distances, ed)

    def test_both_topo(self):
        p = geo.Point(0.5, -0.5, -1)
        mesh = geo.Mesh(numpy.array([0.5, 0.5, 0.5, 0.5]),
                        numpy.array([-0.5, -0.5, -0.5, -0.5]),
                        numpy.array([-1., -2, -3., -4.]))
        distances = p.distance_to_mesh(mesh)
        ed = [0., 1., 2., 3.]
        numpy.testing.assert_array_almost_equal(distances, ed)
