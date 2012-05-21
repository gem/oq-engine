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
from nhlib.geo import _utils as geo_utils
from nhlib.geo import polygon


class PolygonCreationTestCase(unittest.TestCase):
    def assert_failed_creation(self, points, exc, msg):
        with self.assertRaises(exc) as ae:
            geo.Polygon(points)
        self.assertEqual(ae.exception.message, msg)

    def test_less_than_three_points(self):
        msg = 'polygon must have at least 3 unique vertices'
        self.assert_failed_creation([], ValueError, msg)
        self.assert_failed_creation([geo.Point(1, 1)], ValueError, msg)
        self.assert_failed_creation([geo.Point(1, 1),
                                     geo.Point(2, 1)], ValueError, msg)

    def test_less_than_three_unique_points(self):
        msg = 'polygon must have at least 3 unique vertices'
        points = [geo.Point(1, 2)] * 3 + [geo.Point(4, 5)]
        self.assert_failed_creation(points, ValueError, msg)

    def test_intersects_itself(self):
        msg = 'polygon perimeter intersects itself'
        points = [geo.Point(0, 0), geo.Point(0, 1),
                  geo.Point(1, 1), geo.Point(-1, 0)]
        self.assert_failed_creation(points, ValueError, msg)

    def test_intersects_itself_being_closed(self):
        msg = 'polygon perimeter intersects itself'
        points = [geo.Point(0, 0), geo.Point(0, 1),
                  geo.Point(1, 0), geo.Point(1, 1)]
        self.assert_failed_creation(points, ValueError, msg)

    def test_valid_points(self):
        points = [geo.Point(170, -10), geo.Point(170, 10), geo.Point(176, 0),
                  geo.Point(-170, -5), geo.Point(-175, -10),
                  geo.Point(-178, -6)]
        polygon = geo.Polygon(points)
        self.assertEqual(len(polygon.lons), 6)
        self.assertEqual(len(polygon.lats), 6)
        self.assertEqual(list(polygon.lons),
                         [170,  170,  176, -170, -175, -178])
        self.assertEqual(list(polygon.lats), [-10, 10, 0, -5, -10, -6])
        self.assertEqual(polygon.lons.dtype, 'float')
        self.assertEqual(polygon.lats.dtype, 'float')


class PolygonResampleSegmentsTestCase(unittest.TestCase):
    def test_1(self):
        input_lons = [-2, 0, 0, -2]
        input_lats = [-2, -2, 0, 0]

        lons, lats = polygon.get_resampled_coordinates(input_lons, input_lats)
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
        input_lons = [177, 179, -179, -177, -177, -179, 179, 177]
        input_lats = [40, 40, 40, 40, 43, 43, 43, 43]

        lons, lats = polygon.get_resampled_coordinates(input_lons, input_lats)
        self.assertTrue(all(-180 <= lon <= 180 for lon in lons))
        expected_lons = [177, 178, 179, -180, -179, -178, -177,
                         -177, -178, -179, -180, 179, 178, 177, 177]
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
        mesh = poly.discretize(mesh_spacing=MESH_SPACING)
        self.assertIsInstance(mesh, geo.Mesh)
        mesh = list(mesh)

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


class PolygonEdgesTestCase(unittest.TestCase):
    # Test that points very close to the edges of a polygon are actually
    # 'contained' by the polygon.

    # Simple case:
    # We create a 'rectangular' polygon, defined by 4 corner points.
    # In Cartesian space, the shape would look something like this:
    #   *.......*
    #   .       .
    #   .       .
    #   .       .
    #   .       .
    #   .       .
    #   *.......*
    #
    # Projecting onto a sphere, however gives us a rather different shape.
    # The lines connecting the points become arcs. The resulting shape
    # looks like this:
    #     ..---..
    #    *       *
    #   .         .
    #   .         .
    #   .         .
    #   .         .
    #   .         .
    #    *       *
    #     --...--
    #
    # Constructing a realistic polygon to represent this shapes requires us
    # to resample the lines between points--adding points where necessary
    # to increase the resolution of a line. (Resampling only occurs if a
    # given line segment exceeds a certain distance threshold.)
    #
    # If we don't do this, we get a distorted shape (with concave edges):
    #   *-.....-*
    #   .       .
    #    .     .
    #    .     .
    #    .     .
    #   .       .
    #   *.-----.*
    #
    # This distortion can cause points, which lie near the edges of the
    # polygon, to be considered 'outside'. This is of course not correct.
    # Example:
    #   *-.....-*
    #   .       .
    #    .     .
    #    .     .o  <--
    #    .     .
    #   .       .
    #   *.-----.*
    # Note that, with this distortion, there is a greater margin of error
    # toward the center of each line segement. Areas near the points
    # (corners in this cases) are less error prone.
    #
    # With proper resampling, such errors can be minimized:
    #     ..---..
    #    *       *
    #   .         .
    #   .         .
    #   .        o.  <--
    #   .         .
    #   .         .
    #    *       *
    #     --...--

    def setUp(self):
        self.corners = [
            geo.Point(-10, 10), geo.Point(10, 10), geo.Point(10, -10),
            geo.Point(-10, -10),
        ]
        self.poly = geo.Polygon(self.corners)

    def test_corners(self):
        for pt in self.corners:
            self.assertFalse(self.poly.contains(pt.longitude, pt.latitude))

    def test_points_close_to_edges(self):
        # Test points close to the edges:
        # Note that any point which lies directly on a meridian (with a
        # longitude component of -10 or 10, in this case) intersects but is not
        # contained by the polygon. This is because meridians are great circle
        # arcs themselves. This test illustrates the difference in behavior
        # between North/South lines and East/West lines.

        # [North, South, East, West]
        points = [(0, 10), (0, -10.0), (9.9999999, 0), (-9.9999999, 0)]

        for pt in points:
            self.assertTrue(self.poly.contains(*pt))

    def test_points_close_to_corners(self):
        # The same boundary conditions apply here (as noted in the test above).
        points = [
            (-9.999999, 10), (9.999999, 10),
            (-9.999999, 9.999999), (9.999999, 9.999999),
            (-9.999999, -9.99999), (-9.999999, 9.999999),
            (-9.999999, -10), (9.999999, -10),
        ]

        for pt in points:
            self.assertTrue(self.poly.contains(*pt))


class PolgonContainsTestCase(unittest.TestCase):
    """Test that :class:`nhlib.geo.polygon.Polygon.contains` can be called on
    either scalar inputs or numpy arrays.
    """

    def setUp(self):
        corners = [
            geo.Point(-10, 10), geo.Point(10, 10), geo.Point(10, -10),
            geo.Point(-10, -10),
        ]
        self.poly = geo.Polygon(corners)

    def test_contains_with_numpy_array(self):
        # If `contains` is called with numpy arrays as input, the output should
        # be a numpy array of `bool` values with the same shape.
        expected = numpy.array(
            [True, True, True, True, True, False, False, True]
        ).reshape((2, 2, 2))

        lons = numpy.array(
            [0.0, 0, 0, 9.999999, -9.999999, 10, 9.999999, 5]
        ).reshape((2, 2, 2))

        lats = numpy.array(
            [0.0, 10, -10, 0, 0, 10, 10.0000001, 5]
        ).reshape((2,2,2))

        actual = self.poly.contains(lons, lats)

        self.assertTrue((expected == actual).all())
