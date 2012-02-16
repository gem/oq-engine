import unittest

import pyproj

from nhe import geo
from nhe.geo import _utils as utils


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
