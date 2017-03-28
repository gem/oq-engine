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
import shapely.geometry

from openquake.hazardlib import geo
from openquake.hazardlib.geo import utils as geo_utils
from openquake.hazardlib.geo import polygon


class PolygonCreationTestCase(unittest.TestCase):
    def assert_failed_creation(self, points, exc, msg):
        with self.assertRaises(exc) as ae:
            geo.Polygon(points)
        self.assertEqual(str(ae.exception), msg)

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
        expected_lons = [-2, -1, 0, 0, 0, -1, -2, -2]
        expected_lats = [-2, -2, -2, -1, 0, 0, 0, -1]
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
                         177, 177, 177]
        self.assertTrue(
            numpy.allclose(lons, expected_lons, atol=1e-4, rtol=0),
            msg='%s != %s' % (lons, expected_lons)
        )


class PolygonDiscretizeTestCase(unittest.TestCase):
    def test_mesh_spacing_uniformness(self):
        MESH_SPACING = 10
        tl = geo.Point(60, 60)
        tr = geo.Point(70, 60)
        bottom_line = [geo.Point(lon, 58) for lon in range(70, 59, -1)]
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

        result = self.poly.intersects(mesh)

        for x in result.flatten():
            self.assertTrue(x)

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

        self.assertTrue(self.poly.intersects(mesh).all())

    def test_points_close_to_corners(self):
        # The same boundary conditions apply here (as noted in the test above).
        points = [
            geo.Point(-9.999999, 10), geo.Point(9.999999, 10),
            geo.Point(-9.999999, 9.999999), geo.Point(9.999999, 9.999999),
            geo.Point(-9.999999, -9.99999), geo.Point(-9.999999, 9.999999),
            geo.Point(-9.999999, -10), geo.Point(9.999999, -10),
        ]
        mesh = geo.Mesh.from_points_list(points)

        self.assertTrue(self.poly.intersects(mesh).all())


class PolygonFromWktTestCase(unittest.TestCase):
    def test(self):
        wkt_string = 'POLYGON((22.0 -15.0, 24.0 -15.0, 24.0 -10.0, 22.0 -15.0))'
        poly = polygon.Polygon.from_wkt(wkt_string)
        self.assertEqual(list(poly.lats), [-15, -15, -10])
        self.assertEqual(list(poly.lons), [22, 24, 24])
        self.assertEqual(poly.lats.dtype, 'float')
        self.assertEqual(poly.lons.dtype, 'float')
        self.assertEqual(poly.wkt, wkt_string)


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
    def test_clockwise(self):
        poly = polygon.Polygon([geo.Point(0, 0), geo.Point(0, 1),
                                geo.Point(1, 0.5)])
        dilated = poly.dilate(20)
        elons = [
            0.0804399, 0.0645005, 0.0479561, 0.0309619, 0.0136773,
            -0.0037356, -0.0211136, -0.0382935, -0.0551142, -0.0714181,
            -0.0870522, -0.1018698, -0.1157321, -0.1285089, -0.1400805,
            -0.1503383, -0.1591861, -0.1665409, -0.1723339, -0.1765105,
            -0.1790318, -0.1798739, -0.1799013, -0.1790601, -0.1765397,
            -0.1723637, -0.1665713, -0.1592168, -0.1503691, -0.1401112,
            -0.1285392, -0.1157618, -0.1018986, -0.0870797, -0.0714441,
            -0.0551384, -0.0383156, -0.0211335, -0.0037531, 0.0136624,
            0.0309498, 0.0479468, 0.0644941, 0.0804365, 1.0804671,
            1.0955589, 1.1097657, 1.1229560, 1.1350074, 1.1458085,
            1.1552592, 1.1632720, 1.1697727, 1.1747011, 1.1780116,
            1.1796735, 1.1796714, 1.1780054, 1.1746910, 1.1697588,
            1.1632545, 1.1552383, 1.1457846, 1.1349808, 1.1229271,
            1.1097349, 1.0955266, 1.0804337
        ]
        elats = [
            -0.1608776, -0.1679056, -0.1733589, -0.1771863, -0.1793519,
            -0.1798355, -0.1786324, -0.1757539, -0.1712271, -0.1650944,
            -0.1574134, -0.1482560, -0.1377081, -0.1258688, -0.1128490,
            -0.0987708, -0.0837663, -0.0679761, -0.0515485, -0.0346374,
            -0.0174015, -0.0000025, 0.9999975, 1.0173956, 1.0346306,
            1.0515410, 1.0679680, 1.0837578, 1.0987621, 1.1128403,
            1.1258603, 1.1377001, 1.1482485, 1.1574067, 1.1650887,
            1.1712225, 1.1757506, 1.1786305, 1.1798351, 1.1793533,
            1.1771894, 1.1733639, 1.1679125, 1.1608864, 0.6608661,
            0.6523872, 0.6424971, 0.6312873, 0.6188616, 0.6053351,
            0.5908330, 0.5754898, 0.5594475, 0.5428546, 0.5258649,
            0.5086357, 0.4913265, 0.4740977, 0.4571088, 0.4405171,
            0.4244763, 0.4091349, 0.3946351, 0.3811110, 0.3686880,
            0.3574810, 0.3475939, 0.3391182
        ]
        ebbox = [-0.17990133, 1.17967345, 1.17983512, -0.17983547]
        numpy.testing.assert_allclose(dilated.lons, elons, rtol=0, atol=1e-7)
        numpy.testing.assert_allclose(dilated.lats, elats, rtol=0, atol=1e-7)
        numpy.testing.assert_allclose(dilated._bbox, ebbox)
        self.assertIs(dilated._projection, poly._projection)
        self.assertEqual(len(dilated._polygon2d.boundary.coords),
                         len(elons) + 1)

    def test_counterclockwise(self):
        poly = polygon.Polygon([geo.Point(5, 6), geo.Point(4, 6),
                                geo.Point(4, 5)])
        dilated = poly.dilate(20)
        elons = [
            5.1280424, 4.1280406, 4.1149304, 4.1007112, 4.0855200, 4.0695036,
            4.0528165, 4.0356198, 4.0180793, 4.0003644, 3.9826460, 3.9650949,
            3.9478807, 3.9311693, 3.9151220, 3.8998938, 3.8856315, 3.8724729,
            3.8605451, 3.8499631, 3.8408293, 3.8332319, 3.8272443, 3.8229245,
            3.8203143, 3.8194390, 3.8191353, 3.8199981, 3.8225928, 3.8268944,
            3.8328618, 3.8404377, 3.8495493, 3.8601090, 3.8720154, 3.8851539,
            3.8993981, 3.9146108, 3.9306458, 3.9473485, 3.9645582, 3.9821092,
            3.9998325, 5.0001675, 5.0178827, 5.0354259, 5.0526283, 5.0693244,
            5.0853535, 5.1005616, 5.1148024, 5.1279389, 5.1398448, 5.1504059,
            5.1595205, 5.1671011, 5.1730751, 5.1773852, 5.1799900, 5.1808646,
            5.1800010, 5.1774074, 5.1731090, 5.1671473, 5.1595797, 5.1504790,
            5.1399327
        ]
        elats = [
            5.8729890, 4.8731997, 4.8612916, 4.8507226, 4.8415948, 4.8339963,
            4.8280004, 4.8236650, 4.8210319, 4.8201265, 4.8209575, 4.8235169,
            4.8277800, 4.8337058, 4.8412369, 4.8503008, 4.8608099, 4.8726630,
            4.8857454, 4.8999311, 4.9150831, 4.9310551, 4.9476930, 4.9648361,
            4.9823190, 4.9999728, 5.9999728, 6.0175942, 6.0350466, 6.0521621,
            6.0687761, 6.0847286, 6.0998661, 6.1140429, 6.1271226, 6.1389792,
            6.1494986, 6.1585795, 6.1661344, 6.1720906, 6.1763909, 6.1789936,
            6.1798739, 6.1798739, 6.1789944, 6.1763940, 6.1720977, 6.1661467,
            6.1585984, 6.1495254, 6.1390149, 6.1271681, 6.1140988, 6.0999329,
            6.0848065, 6.0688651, 6.0522620, 6.0351568, 6.0177140, 6.0001013,
            5.9824878, 5.9650430, 5.9479344, 5.9313265, 5.9153789, 5.9002447,
            5.8860693
        ]
        ebbox = [3.81913534, 5.18086464, 6.17987385, 4.82012646]
        numpy.testing.assert_allclose(dilated.lons, elons, rtol=0, atol=1e-7)
        numpy.testing.assert_allclose(dilated.lats, elats, rtol=0, atol=1e-7)
        numpy.testing.assert_allclose(dilated._bbox, ebbox)
        self.assertIs(dilated._projection, poly._projection)
        self.assertEqual(len(dilated._polygon2d.boundary.coords),
                         len(elons) + 1)

    def test_extremely_convex(self):
        # Exercise a case where the area polygon is so convex that holes will
        # appear after dilating a certain distance.
        # This test data is based on sample data which produced this failure:
        # https://bugs.launchpad.net/openquake/+bug/1091130
        poly_coords = [
            [16.956879, 41.628004],
            [16.966878, 41.932705],
            [17.606256, 41.897445],
            [19.181572, 41.046135],
            [19.06223673, 40.58765479],
            [18.61629494, 39.63362123],
            [18.919869, 39.501369],
            [18.968954, 39.479085],
            [19.22257, 40.290941],
            [20.203748, 38.900256],
            [20.2, 38.6],
            [19.67226639, 38.00730337],
            [19.67226639, 38.00730337],
            [18.812336, 38.816193],
            [18.540406, 39.043834],
            [16.956879, 41.628004],
        ]
        poly = polygon.Polygon([geo.Point(*x) for x in poly_coords])
        dilation = 15.554238346616508
        poly.dilate(dilation)


class PolygonWKTTestCase(unittest.TestCase):
    """
    Test generation of WKT from a
    :class:`~openquake.hazardlib.geo.polygon.Polygon`.
    """

    def test_wkt(self):
        expected_wkt = (
            'POLYGON((-1.111111 2.222222, -3.333333 4.444444, '
            '5.555555 -6.666666, -1.111111 2.222222))'
        )

        poly = polygon.Polygon(
            [geo.Point(-1.111111, 2.222222), geo.Point(-3.333333, 4.444444),
             geo.Point(5.555555, -6.666666)]
        )

        self.assertEqual(expected_wkt, poly.wkt)
