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

import pyproj
import numpy

from nhlib import geo
from nhlib.geo import _utils as utils


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
        super(LineIntersectsItselfTestCase, self).__init__(*args, **kwargs)
        self.func = utils.line_intersects_itself

    def test_too_few_points(self):
        for (lats, lons) in [([], []), ([1], [2]),
                             ([1, 2], [3, 4]), ([1, 2, 3], [0, 2, 0])]:
            self.assertEqual(False, self.func(lons, lats))
            self.assertEqual(False, self.func(lons, lats, closed_shape=True))

    def test_doesnt_intersect(self):
        lons = [-1, -2, -3, -5]
        lats = [ 0,  2,  4,  6]
        self.assertEqual(False, self.func(lons, lats))
        self.assertEqual(False, self.func(lons, lats, closed_shape=True))

    def test_doesnt_intersect_on_a_pole(self):
        lons = [80] * 4
        lats = [10, 100, -360 + 190, -360 + 280]
        self.assertEqual(False, self.func(lons, lats))
        self.assertEqual(False, self.func(lons, lats, closed_shape=True))

    def test_intersects(self):
        lons = [0, 0, 1, -1]
        lats = [0, 1, 0,  1]
        self.assertEqual(True, self.func(lons, lats))
        self.assertEqual(True, self.func(lons, lats, closed_shape=True))

    def test_intersects_on_a_pole(self):
        lons = [45, 165, -150, 80]
        lats = [-80, -80, -80, -70]
        self.assertEqual(True, self.func(lons, lats))
        self.assertEqual(True, self.func(lons, lats, closed_shape=True))

    def test_intersects_only_after_being_closed(self):
        lons = [0, 0, 1, 1]
        lats = [0, 1, 0, 1]
        self.assertEqual(False, self.func(lons, lats))
        self.assertEqual(True, self.func(lons, lats, closed_shape=True))


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
        super(GetSphericalBoundingBox, self).__init__(*args, **kwargs)
        self.func = utils.get_spherical_bounding_box

    def test_one_point(self):
        lons = [20]
        lats = [-40]
        self.assertEqual(self.func(lons, lats), (20, 20, -40, -40))

    def test_small_extent(self):
        lons = [10, -10]
        lats = [50,  60]
        self.assertEqual(self.func(lons, lats), (-10, 10, 60, 50))

    def test_international_date_line(self):
        lons = [-20, 180, 179, 178]
        lats = [-1,   -2,   1,   2]
        self.assertEqual(self.func(lons, lats), (178, -20, 2, -2))

    def test_too_wide_longitudinal_extent(self):
        for lons, lats in [([-45, -135, 135, 45], [80] * 4),
                           ([0, 10, -175], [0] * 4)]:
            with self.assertRaises(ValueError) as ae:
                self.func(lons, lats)
                self.assertEqual(ae.exception.message,
                                 'points collection has longitudinal '
                                 'extent wider than 180 deg')


class GetOrthographicProjectionTestCase(unittest.TestCase):
    def _get_proj_params(self, bounding_box):
        proj = utils.get_orthographic_projection(*bounding_box)
        self.assertIsInstance(proj, pyproj.Proj)
        params = dict(param.strip().split('=')
                      for param in proj.srs.split('+')
                      if param)
        return params

    def test_simple(self):
        params = self._get_proj_params((10, 16, -29.98, 30))
        self.assertEqual(params.pop('proj'), 'ortho')
        self.assertEqual(params.pop('units'), 'km')
        self.assertAlmostEqual(float(params.pop('lat_0')), 0.01, delta=0.0001)
        self.assertAlmostEqual(float(params.pop('lon_0')), 13, delta=0.0004)
        self.assertEqual(params, {})
        params = self._get_proj_params((-20, 40, 55, 56))
        self.assertAlmostEqual(float(params.pop('lat_0')), 59.2380983)
        self.assertAlmostEqual(float(params.pop('lon_0')), 9.5799719)

    def test_international_date_line(self):
        params = self._get_proj_params((177.6, -175.8, -10, 10))
        self.assertAlmostEqual(float(params.pop('lat_0')), 0)
        self.assertAlmostEqual(float(params.pop('lon_0')), -179.1)


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


class SphericalToCartesianTestCase(unittest.TestCase):
    def _test(self, (lons, lats, depths), (xx, yy, zz)):
        res = utils.spherical_to_cartesian(lons, lats, depths)
        self.assertIsInstance(res, numpy.ndarray)
        self.assertTrue(numpy.allclose([xx, yy, zz], res), str(res))

    def test_zero_zero_zero(self):
        self._test((0, 0, 0), (6371, 0, 0))
        self._test((0, 0, None), (6371, 0, 0))
        self._test(([0], [0], [0]), ([6371], [0], [0]))
        self._test(([0], [0], None), ([6371], [0], [0]))

    def test_north_pole(self):
        self._test((0, 90, 0), (0, 0, 6371))
        self._test((0, 90, None), (0, 0, 6371))
        self._test(([0], [90], [0]), ([0], [0], [6371]))
        self._test(([0], [90], None), ([0], [0], [6371]))

    def test_north_pole_10_km_depth(self):
        self._test((0, 90, 10), (0, 0, 6361))
        self._test(([0], [90], [10]), ([0], [0], [6361]))

    def test_arrays(self):
        lons = numpy.array([10.0, 20.0, 30.0])
        lats = numpy.array([-10.0, 0.0, 10.0])
        depths = numpy.array([1.0, 10.0, 100.0])
        self._test((lons, lats, depths),
                   ([6177.9209972, 5977.38476082, 5348.33856387],
                    [1089.33415649, 2175.59013169, 3087.86470957],
                    [-1106.13889174, 0., 1088.94772215]))
        self._test((lons, lats, None),
                   ([6178.89084351, 5986.78168703, 5433.62541707],
                    [1089.50516656, 2179.01033313, 3137.10509722],
                    [-1106.31253992, 0., 1106.31253992]))


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
        self.assertTrue(numpy.allclose(areas, [4.0, 0.5]))

        # 2d array
        aa = numpy.array([aa, aa * 2])
        bb = numpy.array([bb, bb * 2])
        cc = numpy.array([cc, cc * 2])
        expected_area = [[4.0, 0.5], [16.0, 2.0]]
        areas = utils.triangle_area(aa - bb, aa - cc, bb - cc)
        self.assertTrue(numpy.allclose(areas, expected_area), msg=str(areas))

        # 3d array
        aa = numpy.array([aa])
        bb = numpy.array([bb])
        cc = numpy.array([cc])
        expected_area = numpy.array([expected_area])
        areas = utils.triangle_area(aa - bb, aa - cc, bb - cc)
        self.assertTrue(numpy.allclose(areas, expected_area), msg=str(areas))


class NormalizedTestCase(unittest.TestCase):
    def test_one_vector(self):
        v = numpy.array([0., 0., 2.])
        self.assertTrue(numpy.allclose(utils.normalized(v), [0, 0, 1]))
        v = numpy.array([0., -1., -1.])
        n = utils.normalized(v)
        self.assertTrue(numpy.allclose(n, [0, -2 ** 0.5 / 2., -2 ** 0.5 / 2.]))

    def test_arrays(self):
        # 1d array of vectors
        vv = numpy.array([(0., 0., -0.1), (10., 0., 0.)])
        nn = numpy.array([(0., 0., -1.), (1., 0., 0.)])
        self.assertTrue(numpy.allclose(utils.normalized(vv), nn))

        # 2d array
        vv = numpy.array([vv, vv * 2, vv * (-3)])
        nn = numpy.array([nn, nn, -nn])
        self.assertTrue(numpy.allclose(utils.normalized(vv), nn))

        # 3d array
        vv = numpy.array([vv])
        nn = numpy.array([nn])
        self.assertTrue(numpy.allclose(utils.normalized(vv), nn))
