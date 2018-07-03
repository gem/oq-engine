# The Hazard Library
# Copyright (C) 2014-2018 GEM Foundation
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
import collections

import numpy
try:
    import rtree
except ImportError:
    rtree = None
import shapely.geometry

from openquake.hazardlib import geo
from openquake.hazardlib.geo import utils

Point = collections.namedtuple("Point",  'lon lat')
aac = numpy.testing.assert_allclose


class CleanPointTestCase(unittest.TestCase):
    def test_exact_duplicates(self):
        a, b, c = geo.Point(1, 2, 3), geo.Point(3, 4, 5), geo.Point(5, 6, 7)
        self.assertEqual(utils.clean_points([a, a, a, b, a, c, c]),
                         [a, b, a, c])

    def test_close_duplicates(self):
        a, b, c = geo.Point(1e-4, 1e-4), geo.Point(0, 0), geo.Point(1e-6, 1e-6)
        self.assertEqual(utils.clean_points([a, b, c]), [a, b])


class LineIntersectsItselfTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = utils.line_intersects_itself

    def test_too_few_points(self):
        for (lats, lons) in [([], []), ([1], [2]),
                             ([1, 2], [3, 4]), ([1, 2, 3], [0, 2, 0])]:
            self.assertEqual(False, self.func(lons, lats))
            self.assertEqual(False, self.func(lons, lats, closed_shape=True))

    def test_doesnt_intersect(self):
        lons = numpy.array([-1, -2, -3, -5])
        lats = numpy.array([0,  2,  4,  6])
        self.assertEqual(False, self.func(lons, lats))
        self.assertEqual(False, self.func(lons, lats, closed_shape=True))

    def test_intersects(self):
        lons = numpy.array([0, 0, 1, -1])
        lats = numpy.array([0, 1, 0,  1])
        self.assertEqual(True, self.func(lons, lats))
        self.assertEqual(True, self.func(lons, lats, closed_shape=True))

    def test_intersects_on_a_pole(self):
        lons = numpy.array([45, 165, -150, 80])
        lats = numpy.array([-80, -80, -80, -70])
        self.assertEqual(True, self.func(lons, lats))
        self.assertEqual(True, self.func(lons, lats, closed_shape=True))

    def test_intersects_only_after_being_closed(self):
        lons = numpy.array([0, 0, 1, 1])
        lats = numpy.array([0, 1, 0, 1])
        self.assertEqual(False, self.func(lons, lats))
        self.assertEqual(True, self.func(lons, lats, closed_shape=True))

    def test_intersects_on_international_date_line(self):
        lons = numpy.array([178, 178, -178, 170])
        lats = [0, 10, 0, 5]
        self.assertEqual(True, self.func(lons, lats))

    def test_doesnt_intersect_on_international_date_line(self):
        lons = numpy.array([178, 178, 179, -178])
        lats = numpy.array([0, 10, 5, 5])
        self.assertEqual(False, self.func(lons, lats))


class GetLongitudinalExtentTestCase(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(utils.get_longitudinal_extent(10, 20), 10)
        self.assertEqual(utils.get_longitudinal_extent(-120, 30), 150)

    def test_negative(self):
        self.assertEqual(utils.get_longitudinal_extent(20, 10), -10)
        self.assertEqual(utils.get_longitudinal_extent(-10, -15), -5)

    def test_international_date_line(self):
        self.assertEqual(utils.get_longitudinal_extent(-178.3, 177.7), -4)
        self.assertEqual(utils.get_longitudinal_extent(177.7, -178.3), 4)

        self.assertEqual(utils.get_longitudinal_extent(95, -180 + 94), 179)
        self.assertEqual(utils.get_longitudinal_extent(95, -180 + 96), -179)


class GetSphericalBoundingBox(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = utils.get_spherical_bounding_box

    def test_one_point(self):
        lons = numpy.array([20])
        lats = numpy.array([-40])
        self.assertEqual(self.func(lons, lats), (20, 20, -40, -40))

    def test_small_extent(self):
        lons = numpy.array([10, -10])
        lats = numpy.array([50,  60])
        self.assertEqual(self.func(lons, lats), (-10, 10, 60, 50))

    def test_international_date_line(self):
        lons = numpy.array([-20, 180, 179, 178])
        lats = numpy.array([-1,   -2,   1,   2])
        self.assertEqual(self.func(lons, lats), (178, -20, 2, -2))

    def test_too_wide_longitudinal_extent(self):
        for lons, lats in [([-45, -135, 135, 45], [80] * 4),
                           ([0, 10, -175], [0] * 4)]:
            with self.assertRaises(ValueError) as ae:
                self.func(numpy.array(lons), numpy.array(lats))
                self.assertEqual(str(ae.exception),
                                 'points collection has longitudinal '
                                 'extent wider than 180 deg')


class GetOrthographicProjectionTestCase(unittest.TestCase):
    def test_projection(self):
        # values verified against pyproj's implementation
        proj = utils.OrthographicProjection(10, 16, -2, 30)
        lons = numpy.array([10., 20., 30., 40.])
        lats = numpy.array([-1., -2., -3., -4.])
        xx, yy = proj(lons, lats)
        exx = [-309.89151465, 800.52541443, 1885.04014687, 2909.78079661]
        eyy = [-1650.93260348, -1747.79256663, -1797.62444771, -1802.28117183]
        aac(xx, exx, atol=0.01, rtol=0.005)
        aac(yy, eyy, atol=0.01, rtol=0.005)

    def test_projecting_back_and_forth(self):
        lon0, lat0 = -10.4, 20.3
        proj = utils.OrthographicProjection(lon0, lat0, lon0, lat0)
        lons = lon0 + (numpy.random.random((20, 10)) * 50 - 25)
        lats = lat0 + (numpy.random.random((20, 10)) * 50 - 25)
        xx, yy = proj(lons, lats, reverse=False)
        self.assertEqual(xx.shape, (20, 10))
        self.assertEqual(yy.shape, (20, 10))
        blons, blats = proj(xx, yy, reverse=True)
        aac(blons, lons)
        aac(blats, lats)

    def test_points_too_far(self):
        proj = utils.OrthographicProjection(180, 180, 45, 45)
        with self.assertRaises(ValueError) as ar:
            proj(90, -45)
        self.assertEqual(str(ar.exception),
                         'some points are too far from the projection '
                         'center lon=180.0 lat=45.0')

    def test_projection_across_international_date_line(self):
        # tests that given a polygon crossing the internation date line,
        # projecting its coordinates from spherical to cartesian and then back
        # to spherical gives the original values
        west = 179.7800
        east = -179.8650
        north = 51.4320
        south = 50.8410
        proj = utils.OrthographicProjection(west, east, north, south)

        lons = numpy.array([179.8960, 179.9500, -179.9930, -179.9120,
                            -179.8650, -179.9380, 179.9130, 179.7800])
        lats = numpy.array([50.8410, 50.8430, 50.8490, 50.8540, 51.4160,
                            51.4150, 51.4270, 51.4320])
        xx, yy = proj(lons, lats)
        comp_lons, comp_lats = proj(xx, yy, reverse=True)
        numpy.testing.assert_allclose(lons, comp_lons)
        numpy.testing.assert_allclose(lats, comp_lats)

        west = 179.
        east = -179.
        north = 1
        south = -1
        proj = utils.OrthographicProjection(west, east, north, south)
        lons = numpy.array([179.0, -179.0])
        lats = numpy.array([-1, 1])
        xx, yy = proj(lons, lats)
        comp_lons, comp_lats = proj(xx, yy, reverse=True)
        numpy.testing.assert_allclose(lons, comp_lons)
        numpy.testing.assert_allclose(lats, comp_lats)


class GetMiddlePointTestCase(unittest.TestCase):
    def test_same_points(self):
        self.assertEqual(
            geo.Point(*utils.get_middle_point(1.2, -1.4, 1.2, -1.4)),
            geo.Point(1.2, -1.4)
        )
        self.assertEqual(
            geo.Point(*utils.get_middle_point(-150.33, 22.1, -150.33, 22.1)),
            geo.Point(-150.33, 22.1)
        )

    def test_differnet_point(self):
        self.assertEqual(
            geo.Point(*utils.get_middle_point(0, 0, 0.2, -0.2)),
            geo.Point(0.1, -0.1),
        )
        self.assertEqual(
            geo.Point(*utils.get_middle_point(20, 40, 20.02, 40)),
            geo.Point(20.01, 40)
        )

    def test_international_date_line(self):
        self.assertEqual(
            geo.Point(*utils.get_middle_point(-178, 10, 178, -10)),
            geo.Point(180, 0)
        )
        self.assertEqual(
            geo.Point(*utils.get_middle_point(-179, 43, 179, 43)),
            geo.Point(180, 43.004353)
        )


class SphericalToCartesianAndBackTestCase(unittest.TestCase):
    def _test(self, lons_lats_depths, vectors):
        lons, lats, depths = lons_lats_depths
        res_cart = utils.spherical_to_cartesian(lons, lats, depths)
        aac(vectors, res_cart, atol=1E-7)
        res_sphe = utils.cartesian_to_spherical(res_cart)
        self.assertIsInstance(res_sphe, tuple)
        self.assertEqual(len(res_sphe), 3)
        if depths is None:
            depths = numpy.zeros_like(lons)
        self.assertEqual(numpy.array(res_sphe).shape,
                         numpy.array([lons, lats, depths]).shape)
        aac([lons, lats, depths], res_sphe)

    def test_zero_zero_zero(self):
        self._test((0, 0, 0), (6371, 0, 0))
        self._test((0, 0, None), (6371, 0, 0))
        self._test(([0], [0], [0]), [(6371, 0, 0)])
        self._test(([0], [0], None), [(6371, 0, 0)])

    def test_north_pole(self):
        self._test((0, 90, 0), (0, 0, 6371))
        self._test((0, 90, None), (0, 0, 6371))
        self._test(([0], [90], [0]), [(0, 0, 6371)])
        self._test(([0], [90], None), [(0, 0, 6371)])

    def test_north_pole_10_km_depth(self):
        self._test((0, 90, 10), (0, 0, 6361))
        self._test(([0], [90], [10]), [(0, 0, 6361)])

    def test_topo(self):
        self._test((0, 0, -10), (6381, 0, 0))
        self._test(([0], [0], [-10]), [(6381, 0, 0)])

    def test_arrays(self):
        lons = numpy.array([10.0, 20.0])
        lats = numpy.array([-10.0, 0.0])
        depths = numpy.array([1.0, 10.0])
        vectors = numpy.array([
            (6177.9209972, 1089.33415649, -1106.13889174),
            (5977.38476082, 2175.59013169, 0.)])
        self._test((lons, lats, depths), vectors)


class TriangleAreaTestCase(unittest.TestCase):
    def test_one_triangle(self):
        a = numpy.array([0., 0., 0.])
        b = numpy.array([1., 0., 0.])
        c = numpy.array([0., 1., 0.])
        self.assertAlmostEqual(utils.triangle_area(a - b, a - c, b - c), 0.5)
        b = numpy.array([1., 0., 1.])
        self.assertAlmostEqual(utils.triangle_area(a - b, a - c, b - c),
                               (2 ** 0.5) / 2)

    def test_arrays(self):
        # 1d array of vectors
        aa = numpy.array([(0.5, 0., 3.), (0., 2., -1.)])
        bb = numpy.array([(0.5, 4., 3.), (0, 2, -2.)])
        cc = numpy.array([(-1.5, 0., 3.), (1, 2, -2)])
        areas = utils.triangle_area(aa - bb, aa - cc, bb - cc)
        aac(areas, [4.0, 0.5])

        # 2d array
        aa = numpy.array([aa, aa * 2])
        bb = numpy.array([bb, bb * 2])
        cc = numpy.array([cc, cc * 2])
        expected_area = [[4.0, 0.5], [16.0, 2.0]]
        areas = utils.triangle_area(aa - bb, aa - cc, bb - cc)
        aac(areas, expected_area)

        # 3d array
        aa = numpy.array([aa])
        bb = numpy.array([bb])
        cc = numpy.array([cc])
        expected_area = numpy.array([expected_area])
        areas = utils.triangle_area(aa - bb, aa - cc, bb - cc)
        aac(areas, expected_area)


class NormalizedTestCase(unittest.TestCase):
    def test_one_vector(self):
        v = numpy.array([0., 0., 2.])
        aac(utils.normalized(v), [0, 0, 1])
        v = numpy.array([0., -1., -1.])
        n = utils.normalized(v)
        aac(n, [0, -2 ** 0.5 / 2., -2 ** 0.5 / 2.])

    def test_arrays(self):
        # 1d array of vectors
        vv = numpy.array([(0., 0., -0.1), (10., 0., 0.)])
        nn = numpy.array([(0., 0., -1.), (1., 0., 0.)])
        aac(utils.normalized(vv), nn)

        # 2d array
        vv = numpy.array([vv, vv * 2, vv * (-3)])
        nn = numpy.array([nn, nn, -nn])
        aac(utils.normalized(vv), nn)

        # 3d array
        vv = numpy.array([vv])
        nn = numpy.array([nn])
        aac(utils.normalized(vv), nn)


class ConvexToPointDistanceTestCase(unittest.TestCase):
    polygon = shapely.geometry.Polygon([
        (0, 0), (1, 0), (1, 1), (0, 1)
    ])

    def test_one_point(self):
        dist = utils.point_to_polygon_distance(self.polygon, 0.5, 0.5)
        self.assertEqual(dist, 0)
        dist = utils.point_to_polygon_distance(self.polygon, 0.5, 1.5)
        self.assertAlmostEqual(dist, 0.5)

    def test_list_of_points(self):
        pxx = [-1., 0.3, -0.25]
        pyy = [2., 1.1, 3.9]
        dist = utils.point_to_polygon_distance(self.polygon, pxx, pyy)
        numpy.testing.assert_almost_equal(dist, [1.4142135, 0.1, 2.9107559])

    def test_2d_array_of_points(self):
        pxx = [[-1., 0.3], [-0.25, 0.5]]
        pyy = [[2., 1.1], [3.9, -0.3]]
        dist = utils.point_to_polygon_distance(self.polygon, pxx, pyy)
        numpy.testing.assert_almost_equal(dist, [[1.4142135, 0.1],
                                                 [2.9107559, 0.3]])

    def test_nonconvex_polygon(self):
        coords = [(0, 0), (0, 3), (2, 2), (1, 2), (1, 1), (1, 0), (0, 0)]
        for polygon_coords in (coords, list(reversed(coords))):
            polygon = shapely.geometry.Polygon(polygon_coords)
            pxx = numpy.array([0.5, 0.5, 0.5, 0.5, 0.5])
            pyy = numpy.array([0.0, 0.5, 1.0, 2.0, 2.5])
            dist = utils.point_to_polygon_distance(polygon, pxx, pyy)
            numpy.testing.assert_equal(dist, 0)

            pxx = numpy.array([1.5, 3.0, -2.0])
            pyy = numpy.array([1.5, 2.0, 2.0])
            dist = utils.point_to_polygon_distance(polygon, pxx, pyy)
            numpy.testing.assert_almost_equal(dist, [0.5, 1, 2])


class WithinTestCase(unittest.TestCase):
    """
    Test geo.utils.within(bbox, lonlat_index)
    """

    def test(self):
        if rtree is None:  # not installed
            raise unittest.SkipTest
        self.lons = [
            -179.75, -179.5, -179.25, -179.0, -178.75, -178.5, -178.25, -178.0,
            -177.75, -177.5, -177.25, -177.0, -176.75, -176.5, -176.25, -176.0,
            -175.75, -175.5, -175.25, 178.25, 178.5, 178.75, 179.0, 179.25,
            179.5, 179.75, -180.0]
        self.lats = [-30.5] * 27
        self.index = rtree.index.Index(
            (i, (x, y, x, y), None)
            for i, (x, y) in enumerate(zip(self.lons, self.lats)))

        all_sites = numpy.arange(27, dtype=numpy.uint32)
        expected = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 19, 20, 21, 22, 23,
                    24, 25, 26]

        # bounding box taking 20 of the 27 sites
        indices = utils.within(
            [176.73699, -39, -176.9016, -12], self.index)
        numpy.testing.assert_equal(indices, expected)

        # one can invert lon1, lon2
        indices = utils.within(
            [-176.9016, -39, 176.73699, -12], self.index)
        numpy.testing.assert_equal(indices, expected)

        # bounding box large enough to contain all sites
        indices = utils.within(
            [174.12916, -39, -169.9217, -12], self.index)
        numpy.testing.assert_equal(indices, all_sites)

        # lat on the edge from below is (strangely) taken
        indices = utils.within(
            [174.12916, -39, -169.9217, -30], self.index)
        numpy.testing.assert_equal(indices, all_sites)

        # lat on the edge from up is discarded
        indices = utils.within(
            [174.12916, -30, -169.9217, -12], self.index)
        numpy.testing.assert_equal(indices, [])


class PlaneFit(unittest.TestCase):
    """
    In order to test the method we fit a plane to a cloud of points
    generated from a given plane equation.

    ax + by + cz + d = 0
    """

    def setUp(self):
        # Set the seed of the random number generator
        numpy.random.seed(41)
        # Compute the x and y coordinates of the points which lay on the plane
        self.npts = 20
        self.points = numpy.zeros((self.npts, 3))
        self.points[:, 0] = (numpy.random.random(self.npts) - 0.5) * 10.
        self.points[:, 1] = (numpy.random.random(self.npts) - 0.5) * 10.
        # Plane equation coefficients
        self.c = numpy.random.random(4)
        # Normalise the plane equation coefficients to get the direction
        # cosines
        self.c[0:3] = self.c[0:3] / (sum(self.c[0:3]**2.))**0.5
        # Compute the constant term
        self.c[-1] = -abs(self.c[-1])
        # Compute the z coordinate of the points
        self.points[:, 2] = (-self.points[:, 0] * self.c[0] +
                             -self.points[:, 1] * self.c[1] +
                             -self.c[3]) / self.c[2]

    def test_plane_fit01(self):
        """
        Tests the parameters of the plane obtained through the regression.
        """
        pnt, par = utils.plane_fit(self.points)
        numpy.testing.assert_allclose(self.c[0:3], par, rtol=1e-5, atol=0)
        self.assertAlmostEqual(self.c[-1], -sum(par*pnt))

    def test_plane_fit02(self):
        """
        Tests the parameters of the plane obtained through the regression.
        In this second case we add noise to the z values
        """
        self.points[:, 2] += numpy.random.random(self.npts) * 0.01
        pnt, par = utils.plane_fit(self.points)
        numpy.testing.assert_allclose(self.c[0:3], par, rtol=1e-3, atol=0)
        self.assertAlmostEqual(self.c[-1], -sum(par*pnt), 2)


# NB: utils.assoc is tested in the engine
