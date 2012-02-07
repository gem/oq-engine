import unittest

import numpy

from nhe import geo
from nhe.geo import _utils as geo_utils


class PolygonCreationTestCase(unittest.TestCase):
    def assert_failed_creation(self, points, exc, msg):
        with self.assertRaises(exc) as ae:
            geo.Polygon(points)
        self.assertEqual(ae.exception.message, msg)

    def test_less_than_three_points(self):
        msg = 'polygon must have at least 3 unique vertices'
        self.assert_failed_creation([], RuntimeError, msg)
        self.assert_failed_creation([geo.Point(1, 1)], RuntimeError, msg)
        self.assert_failed_creation([geo.Point(1, 1),
                                     geo.Point(2, 1)], RuntimeError, msg)

    def test_less_than_three_unique_points(self):
        msg = 'polygon must have at least 3 unique vertices'
        points = [geo.Point(1, 2)] * 3 + [geo.Point(4, 5)]
        self.assert_failed_creation(points, RuntimeError, msg)

    def test_intersects_itself(self):
        msg = 'polygon perimeter intersects itself'
        points = [geo.Point(0, 0), geo.Point(0, 1),
                  geo.Point(1, 1), geo.Point(-1, 0)]
        self.assert_failed_creation(points, RuntimeError, msg)

    def test_intersects_itself_being_closed(self):
        msg = 'polygon perimeter intersects itself'
        points = [geo.Point(0, 0), geo.Point(0, 1),
                  geo.Point(1, 0), geo.Point(1, 1)]
        self.assert_failed_creation(points, RuntimeError, msg)

    def test_valid_points(self):
        points = [geo.Point(170, -10), geo.Point(170, 10), geo.Point(176, 0),
                  geo.Point(-170, -5), geo.Point(-175, -10),
                  geo.Point(-178, -6)]
        polygon = geo.Polygon(points)
        self.assertEqual(polygon.num_points, 6)
        self.assertEqual(list(polygon.lons),
                         [170,  170,  176, -170, -175, -178])
        self.assertEqual(list(polygon.lats), [-10, 10, 0, -5, -10, -6])
        self.assertEqual(polygon.lons.dtype, 'float')
        self.assertEqual(polygon.lats.dtype, 'float')


class PolygonResampleSegmentsTestCase(unittest.TestCase):
    def test_1(self):
        poly = geo.Polygon([geo.Point(-2, -2), geo.Point(0, -2),
                            geo.Point(0, 0), geo.Point(-2, 0)])
        lons, lats = poly._get_resampled_coordinates()
        expected_lons = [-2, -1,  0,  0, -1, -2, -2]
        expected_lats = [-2, -2, -2,  0,  0,  0, -2]
        self.assertTrue(
            numpy.allclose(lons, expected_lons, atol=1e-3, rtol=0),
            msg='%s != %s' % (lons, expected_lons)
        )
        self.assertTrue(
            numpy.allclose(lats, expected_lats, atol=1e-3, rtol=0),
            msg='%s != %s' % (lats, expected_lats)
        )

    def test_international_date_line(self):
        poly = geo.Polygon([
            geo.Point(177, 40), geo.Point(179, 40), geo.Point(-179, 40),
            geo.Point(-177, 40),
            geo.Point(-177, 43), geo.Point(-179, 43), geo.Point(179, 43),
            geo.Point(177, 43)
        ])
        lons, lats = poly._get_resampled_coordinates()
        self.assertTrue(all(-180 < lon <= 180 for lon in lons))
        expected_lons = [177, 178, 179, 180, -179, -178, -177,
                         -177, -178, -179, 180, 179, 178, 177, 177]
        self.assertTrue(
            numpy.allclose(lons, expected_lons, atol=1e-4, rtol=0),
            msg='%s != %s' % (lons, expected_lons)
        )


class PolygonDiscretizeTestCase(unittest.TestCase):
    def test_mesh_spacing_uniformness(self):
        MESH_SPACING = 10
        tl = geo.Point(60, 60)
        tr = geo.Point(70, 60)
        bottom_line = [geo.Point(lon, 58) for lon in xrange(70, 59, -1)]
        poly = geo.Polygon([tl, tr] + bottom_line)
        mesh = list(poly.discretize(mesh_spacing=MESH_SPACING))

        for i, point in enumerate(mesh):
            if i == len(mesh) - 1:
                # the point is last in the mesh
                break
            next_point = mesh[i + 1]
            if next_point.longitude < point.longitude:
                # this is the next row (down along the meridian).
                # let's check that the new row stands exactly
                # mesh spacing kilometers below the previous one.
                self.assertAlmostEqual(
                    point.distance(geo.Point(point.longitude,
                                             next_point.latitude)),
                    MESH_SPACING, places=4
                )
                continue
            dist = point.distance(next_point)
            self.assertAlmostEqual(MESH_SPACING, dist, places=4)

    def test_polygon_on_international_date_line(self):
        MESH_SPACING = 10
        bl = geo.Point(177, 40)
        bml = geo.Point(179, 40)
        bmr = geo.Point(-179, 40)
        br = geo.Point(-177, 40)
        tr = geo.Point(-177, 43)
        tmr = geo.Point(-179, 43)
        tml = geo.Point(179, 43)
        tl = geo.Point(177, 43)
        poly = geo.Polygon([bl, bml, bmr, br, tr, tmr, tml, tl])
        mesh = list(poly.discretize(mesh_spacing=MESH_SPACING))

        west = east = mesh[0]
        for point in mesh:
            if geo_utils.get_longitudinal_extent(point.longitude,
                                                 west.longitude) > 0:
                west = point
            if geo_utils.get_longitudinal_extent(point.longitude,
                                                 east.longitude) < 0:
                east = point

        self.assertLess(west.longitude, 177.15)
        self.assertGreater(east.longitude, -177.15)

    def test_no_points_outside_of_polygon(self):
        dist = 1e-4
        points = [
            geo.Point(0, 0),
            geo.Point(dist * 4.5, 0),
            geo.Point(dist * 4.5, -dist * 4.5),
            geo.Point(dist * 3.5, -dist * 4.5),
            geo.Point(dist * (4.5 - 0.8), -dist * 1.5),
            geo.Point(0, -dist * 1.5)
        ]
        poly = geo.Polygon(points)
        mesh = list(poly.discretize(mesh_spacing=1.1e-2))
        self.assertEqual(mesh, [
            geo.Point(dist, -dist),
            geo.Point(dist * 2, -dist),
            geo.Point(dist * 3, -dist),
            geo.Point(dist * 4, -dist),

            geo.Point(dist * 4, -dist * 2),
            geo.Point(dist * 4, -dist * 3),
            geo.Point(dist * 4, -dist * 4),
        ])

    def test_longitudinally_extended_boundary(self):
        points = [geo.Point(lon, -60) for lon in xrange(-10, 11)]
        points += [geo.Point(10, -60.1), geo.Point(-10, -60.1)]
        poly = geo.Polygon(points)
        mesh = list(poly.discretize(mesh_spacing=10.62))

        south = mesh[0]
        for point in mesh:
            if point.latitude < south.latitude:
                south = point

        # the point with the lowest latitude should be somewhere
        # in the middle longitudinally (around Greenwich meridian)
        # and be below -60th parallel.
        self.assertTrue(-0.1 < south.longitude < 0.1)
        self.assertTrue(-60.5 < south.latitude < -60.4)
