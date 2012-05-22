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
import shapely.geometry

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
        poly = geo.Polygon(points)
        self.assertEqual(len(poly.lons), 6)
        self.assertEqual(len(poly.lats), 6)
        self.assertEqual(list(poly.lons),
                         [170,  170,  176, -170, -175, -178])
        self.assertEqual(list(poly.lats), [-10, 10, 0, -5, -10, -6])
        self.assertEqual(poly.lons.dtype, 'float')
        self.assertEqual(poly.lats.dtype, 'float')


class PolygonResampleSegmentsTestCase(unittest.TestCase):
    def test_1(self):
        input_lons = [-2, 0, 0, -2]
        input_lats = [-2, -2, 0, 0]

        lons, lats = polygon.get_resampled_coordinates(input_lons, input_lats)
        expected_lons = [-2, -1, 0, 0, 0, -1, -2, -2, -2]
        expected_lats = [-2, -2, -2, -1, 0, 0, 0, -1, -2]
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
        expected_lons = [177, 179, -179, -177, -177, -177, -177, -179, 179,
                         177, 177, 177, 177]
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
    # Projecting onto a sphere, however, gives us a rather different shape.
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
        mesh = geo.Mesh.from_points_list(self.corners)

        result = self.poly.contains(mesh)

        for x in result.flatten():
            self.assertFalse(x)

    def test_points_close_to_edges(self):
        # Test points close to the edges:
        # Note that any point which lies directly on a meridian (with a
        # longitude component of -10 or 10, in this case) intersects but is not
        # contained by the polygon. This is because meridians are great circle
        # arcs themselves. This test illustrates the difference in behavior
        # between North/South lines and East/West lines.

        # [North, South, East, West]
        points = [
            geo.Point(0, 10), geo.Point(0, -10.0),
            geo.Point(9.9999999, 0), geo.Point(-9.9999999, 0),
        ]

        mesh = geo.Mesh.from_points_list(points)

        self.assertTrue(self.poly.contains(mesh).all())

    def test_points_close_to_corners(self):
        # The same boundary conditions apply here (as noted in the test above).
        points = [
            geo.Point(-9.999999, 10), geo.Point(9.999999, 10),
            geo.Point(-9.999999, 9.999999), geo.Point(9.999999, 9.999999),
            geo.Point(-9.999999, -9.99999), geo.Point(-9.999999, 9.999999),
            geo.Point(-9.999999, -10), geo.Point(9.999999, -10),
        ]
        mesh = geo.Mesh.from_points_list(points)

        self.assertTrue(self.poly.contains(mesh).all())


class PolygonFrom2dTestCase(unittest.TestCase):
    def test(self):
        polygon2d = shapely.geometry.Polygon([
            (-12, 0), (0, 14.5), (17.1, 3), (18, 0), (16.5, -3), (0, -10)
        ])
        proj = geo_utils.get_orthographic_projection(0, 0, 0, 0)
        poly = polygon.Polygon._from_2d(polygon2d, proj)
        elons = [-0.10791866, 0., 0.1537842, 0.1618781, 0.14838825, 0.]
        elats = [0., 0.13040175, 0.02697965, 0., -0.02697965, -0.0899322]
        ebbox = [-0.10791866, 0.1618781, 0.13040175, -0.0899322]
        numpy.testing.assert_allclose(poly.lons, elons)
        numpy.testing.assert_allclose(poly.lats, elats)
        numpy.testing.assert_allclose(poly._bbox, ebbox)
        self.assertIs(poly._polygon2d, polygon2d)
        self.assertIs(poly._projection, proj)

        poly = polygon.Polygon._from_2d(poly._polygon2d, poly._projection)
        numpy.testing.assert_allclose(poly.lons, elons)
        numpy.testing.assert_allclose(poly.lats, elats)
        numpy.testing.assert_allclose(poly._bbox, ebbox)
        self.assertIs(poly._polygon2d, polygon2d)
        self.assertIs(poly._projection, proj)


class PolygonDilateTestCase(unittest.TestCase):
    def test(self):
        poly = polygon.Polygon([geo.Point(0, 0), geo.Point(0, 1),
                                geo.Point(1, 0.5)])
        dilated = poly.dilate(20)
        elats = [
            -0.00001616, 0.99999753, 1.01739562, 1.03463065, 1.05154098,
            1.06796804, 1.08375777, 1.09876209, 1.11284028, 1.12586031,
            1.13770006, 1.14824849, 1.15740666, 1.16508868, 1.17122250,
            1.17575058, 1.17863046, 1.17983512, 1.17935326, 1.17718941,
            1.17336385, 1.16791248, 1.16088642, 0.66086607, 0.65238723,
            0.64249710, 0.63128727, 0.61886156, 0.60533506, 0.59083304,
            0.57548982, 0.55944750, 0.54285465, 0.52586494, 0.50863571,
            0.49132653, 0.47409770, 0.45710878, 0.44051708, 0.42447628,
            0.40913491, 0.39463506, 0.38111099, 0.36868796, 0.35748101,
            0.34759391, 0.33911824, -0.16087760, -0.16790540, -0.17335857,
            -0.17718599, -0.17935175, -0.17983554, -0.17863283, -0.17575489,
            -0.17122872, -0.16509676, -0.15741653, -0.14826004, -0.13771318,
            -0.12587485, -0.11285608, -0.09877895, -0.08377549, -0.06798640,
            -0.05155976, -0.03464961, -0.01741453, -0.00001616
        ]
        elons = [
            -0.17987393, -0.17990133, -0.17906009, -0.17653968, -0.17236372,
            -0.16657133, -0.15921681, -0.15036912, -0.14011120, -0.12853924,
            -0.11576176, -0.10189857, -0.08707969, -0.07144409, -0.05513843,
            -0.03831563, -0.02113347, -0.00375312, 0.01366242, 0.03094978,
            0.04794683, 0.06449414, 0.08043653, 1.08046705, 1.09555891,
            1.10976574, 1.12295597, 1.13500743, 1.14580853, 1.15525923,
            1.16327202, 1.16977271, 1.17470110, 1.17801156, 1.17967345,
            1.17967139, 1.17800542, 1.17469098, 1.16975876, 1.16325446,
            1.15523833, 1.14578459, 1.13498082, 1.12292705, 1.10973493,
            1.09552662, 1.08043370, 0.08043994, 0.06450112, 0.04795736,
            0.03096383, 0.01367988, -0.00373238, -0.02110967, -0.03828900,
            -0.05510927, -0.07141274, -0.08704649, -0.10186393, -0.11572609,
            -0.12850296, -0.14007473, -0.15033288, -0.15918121, -0.16653674,
            -0.17233050, -0.17650814, -0.17903051, -0.17987393
        ]
        ebbox = [-0.17990133, 1.17967345, 1.17983512, -0.17983554]
        numpy.testing.assert_allclose(dilated.lons, elons, rtol=0, atol=1e-7)
        numpy.testing.assert_allclose(dilated.lats, elats, rtol=0, atol=1e-7)
        numpy.testing.assert_allclose(dilated._bbox, ebbox)
        self.assertIs(dilated._projection, poly._projection)
        self.assertEqual(len(dilated._polygon2d.boundary.coords),
                         len(elons) + 1)
