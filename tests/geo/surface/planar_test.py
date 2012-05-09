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

from nhlib.geo import Point
from nhlib.geo.mesh import Mesh
from nhlib.geo.surface.planar import PlanarSurface

from tests.geo.surface import _planar_test_data as test_data
from tests.geo.surface import _utils as utils


class PlanarSurfaceCreationTestCase(unittest.TestCase):
    def assert_failed_creation(self, mesh_spacing, strike, dip, corners,
                               exc, msg):
        with self.assertRaises(exc) as ae:
            PlanarSurface(mesh_spacing, strike, dip, *corners)
        self.assertEqual(ae.exception.message, msg)

    def test_top_edge_depth_differs(self):
        corners = [Point(0, -1, 0.3), Point(0, 1, 0.30001),
                   Point(0, 1, 0.5), Point(0, -1, 0.5)]
        self.assert_failed_creation(1, 0, 90, corners, ValueError,
            'top and bottom edges must be parallel to the earth surface'
        )

    def test_bottom_edge_depth_differs(self):
        corners = [Point(0, -1, 0.3), Point(0, 1, 0.3),
                   Point(0, 1, 0.5), Point(0, -1, 0.499999)]
        self.assert_failed_creation(1, 0, 90, corners, ValueError,
            'top and bottom edges must be parallel to the earth surface'
        )

    def test_twisted_surface(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, -1, 2), Point(0, 1, 2)]
        self.assert_failed_creation(1, 0, 90, corners, ValueError,
            'planar surface corners must represent a rectangle'
        )

    def test_edges_not_parallel(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(-0.3, 1, 2), Point(0.3, -1, 2)]
        self.assert_failed_creation(1, 0, 90, corners, ValueError,
            'planar surface corners must represent a rectangle'
        )

    def test_top_edge_shorter_than_bottom_edge(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, 1.2, 2), Point(0, -1.2, 2)]
        self.assert_failed_creation(1, 0, 90, corners, ValueError,
            'planar surface corners must represent a rectangle'
        )

    def test_non_positive_mesh_spacing(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, 1, 2), Point(0, -1, 2)]
        msg = 'mesh spacing must be positive'
        self.assert_failed_creation(0, 0, 90, corners, ValueError, msg)
        self.assert_failed_creation(-1, 0, 90, corners, ValueError, msg)

    def test_strike_out_of_range(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, 1, 2), Point(0, -1, 2)]
        msg = 'strike is out of range [0, 360)'
        self.assert_failed_creation(10, -1, 90, corners, ValueError, msg)
        self.assert_failed_creation(10, 360, 90, corners, ValueError, msg)

    def test_dip_out_of_range(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, 1, 2), Point(0, -1, 2)]
        msg = 'dip is out of range (0, 90]'
        self.assert_failed_creation(10, 0, 0, corners, ValueError, msg)
        self.assert_failed_creation(10, 0, 91, corners, ValueError, msg)
        self.assert_failed_creation(10, 0, -1, corners, ValueError, msg)

    def assert_successfull_creation(self, mesh_spacing, strike, dip,
                                    tl, tr, br, bl):
        surface = PlanarSurface(mesh_spacing, strike, dip, tl, tr, br, bl)
        self.assertEqual(surface.top_left, tl)
        self.assertEqual(surface.top_right, tr)
        self.assertEqual(surface.bottom_left, bl)
        self.assertEqual(surface.bottom_right, br)
        self.assertEqual(surface.mesh_spacing, mesh_spacing)
        self.assertEqual(surface.strike, strike)
        self.assertEqual(surface.get_strike(), strike)
        self.assertEqual(surface.dip, dip)
        self.assertEqual(surface.get_dip(), dip)
        self.assertAlmostEqual(surface.length, tl.distance(tr), delta=0.2)
        self.assertAlmostEqual(surface.width, tl.distance(bl), delta=0.2)

    def test_edges_not_parallel_within_tolerance(self):
        self.assert_successfull_creation(
            10, 20, 30,
            Point(0, -1, 1), Point(0, 1, 1),
            Point(-0.0003, 1, 2), Point(0.0003, -1, 2)
        )

    def test_edges_azimuths_cross_north_direction(self):
        self.assert_successfull_creation(
            10, 150, 45,
            Point(-0.0001, 0, 1), Point(0.0001, -1, 1),
            Point(-0.0001, -1, 2), Point(0.0001, 0, 2)
        )
        self.assert_successfull_creation(
            1, 2, 3,
            Point(0.0001, 0, 1), Point(-0.0001, -1, 1),
            Point(0.0001, -1, 2), Point(-0.0001, 0, 2)
        )

    def test_edges_differ_in_length_within_tolerance(self):
        self.assert_successfull_creation(
            1, 2, 3,
            Point(0, -1, 1), Point(0, 1, 1),
            Point(0, 1.000001, 2), Point(0, -1, 2)
        )


class PlanarSurfaceGetMeshTestCase(utils.SurfaceTestCase):

    def _surface(self, corners):
        return PlanarSurface(1.0, 0.0, 90.0, *corners)

    def test_2(self):
        self.assert_mesh_is(self._surface(test_data.TEST_2_CORNERS),
                expected_mesh=test_data.TEST_2_MESH)

    def test_3(self):
        self.assert_mesh_is(self._surface(test_data.TEST_3_CORNERS),
                expected_mesh=test_data.TEST_3_MESH)

    def test_4(self):
        self.assert_mesh_is(self._surface(test_data.TEST_4_CORNERS),
                            expected_mesh=test_data.TEST_4_MESH)

    def test_5(self):
        self.assert_mesh_is(self._surface(test_data.TEST_5_CORNERS),
                expected_mesh=test_data.TEST_5_MESH)

    def test_6(self):
        corners = [Point(0, 0, 9), Point(0, 1e-9, 9),
                   Point(0, 1e-9, 9.0 + 1e-9), Point(0, 0, 9.0 + 1e-9)]
        mesh = [[(0, 0, 9)]]
        self.assert_mesh_is(self._surface(corners),
                expected_mesh=mesh)

    def test_7_rupture_1(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_1_CORNERS),
                expected_mesh=test_data.TEST_7_RUPTURE_1_MESH)

    def test_7_rupture_2(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_2_CORNERS),
                expected_mesh=test_data.TEST_7_RUPTURE_2_MESH)

    def test_7_rupture_3(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_3_CORNERS),
                expected_mesh=test_data.TEST_7_RUPTURE_3_MESH)

    def test_7_rupture_4(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_4_CORNERS),
                expected_mesh=test_data.TEST_7_RUPTURE_4_MESH)

    def test_7_rupture_5(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_5_CORNERS),
                expected_mesh=test_data.TEST_7_RUPTURE_5_MESH)

    def test_7_rupture_6(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_6_CORNERS),
                expected_mesh=test_data.TEST_7_RUPTURE_6_MESH)

    def test_7_rupture_7(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_7_CORNERS),
                expected_mesh=test_data.TEST_7_RUPTURE_7_MESH)

    def test_7_rupture_8(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_8_CORNERS),
                expected_mesh=test_data.TEST_7_RUPTURE_8_MESH)


class PlanarSurfaceGetMinDistanceTestCase(unittest.TestCase):
    def test_1(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_6_CORNERS)
        sites = Mesh.from_points_list([Point(0, 0)])
        self.assertAlmostEqual(8.01185807319,
                               surface.get_min_distance(sites)[0], places=2)

    def test_2(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_6_CORNERS)
        sites = Mesh.from_points_list([Point(-0.25, 0.25)])
        self.assertAlmostEqual(40.1213468,
                               surface.get_min_distance(sites)[0], places=1)

    def test_3(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_2_CORNERS)
        sites = Mesh.from_points_list([Point(0, 0)])
        self.assertAlmostEqual(7.01186304977,
                               surface.get_min_distance(sites)[0], places=2)

    def test_4(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_2_CORNERS)
        sites = Mesh.from_points_list([Point(-0.3, 0.4)])
        self.assertAlmostEqual(55.6159556,
                               surface.get_min_distance(sites)[0], delta=0.6)


class PlanarSurfaceGetJoynerBooreDistanceTestCase(unittest.TestCase):
    def test_point_inside(self):
        corners = [Point(-1, -1, 1), Point(1, -1, 1),
                   Point(1, 1, 2), Point(-1, 1, 2)]
        surface = PlanarSurface(10, 0, 45, *corners)
        sites = Mesh.from_points_list([Point(0, 0), Point(0, 0, 20),
                                       Point(0.1, 0.3)])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [0] * 3
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test_point_on_the_border(self):
        corners = [Point(0.1, -0.1, 1), Point(-0.1, -0.1, 1),
                   Point(-0.1, 0.1, 2), Point(0.1, 0.1, 2)]
        surface = PlanarSurface(1, 0, 45, *corners)
        sites = Mesh.from_points_list([Point(-0.1, 0.04), Point(0.1, 0.03)])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [0] * 2
        self.assertTrue(numpy.allclose(dists, expected_dists, atol=0.3))

    def test_point_outside(self):
        corners = [Point(0.1, -0.1, 1), Point(-0.1, -0.1, 1),
                   Point(-0.1, 0.1, 2), Point(0.1, 0.1, 2)]
        surface = PlanarSurface(1, 0, 45, *corners)
        sites = Mesh.from_points_list([Point(-0.2, -0.2), Point(1, 1, 1),
                                       Point(4, 5), Point(8, 10.4),
                                       Point(0.05, 0.15, 10)])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [
            Point(-0.2, -0.2).distance(Point(-0.1, -0.1)),
            Point(1, 1).distance(Point(0.1, 0.1)),
            Point(4, 5).distance(Point(0.1, 0.1)),
            Point(8, 10.4).distance(Point(0.1, 0.1)),
            Point(0.05, 0.15).distance(Point(0.05, 0.1))
        ]
        self.assertTrue(numpy.allclose(dists, expected_dists, atol=0.4))


class PlanarSurfaceGetRXDistanceTestCase(unittest.TestCase):
    def _test1to7surface(self):
        corners = [Point(0, 0, 8), Point(-0.1, 0, 8),
                   Point(-0.1, 0, 9), Point(0, 0, 9)]
        surface = PlanarSurface(1, 90, 60, *corners)
        return surface

    def test1_site_on_the_footwall(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, 0.05), Point(40.0, 0.05)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [-5.559752615413244] * 2
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test2_site_on_the_hanging_wall(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, -0.05), Point(-140, -0.05)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [5.559752615413244] * 2
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test3_site_on_centroid(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, 0)])
        self.assertAlmostEqual(surface.get_rx_distance(sites)[0], 0)

    def test4_site_along_strike(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.2, 0), Point(67.6, 0),
                                       Point(90.33, 0)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [0] * 3
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test5_site_opposite_to_strike_direction(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(-0.2, 0), Point(-67.6, 0),
                                       Point(-90.33, 0)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [0] * 3
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test6_one_degree_distance(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, -1), Point(20, 1)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [111.19505230826488, -111.19505230826488]
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test7_ten_degrees_distance(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0, -10), Point(-15, 10)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [1111.9505230826488, -1111.9505230826488]
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test8_strike_of_45_degrees(self):
        corners = [Point(-0.05, -0.05, 8), Point(0.05, 0.05, 8),
                   Point(0.05, 0.05, 9), Point(-0.05, -0.05, 9)]
        surface = PlanarSurface(1, 45, 60, *corners)
        sites = Mesh.from_points_list([Point(0.05, 0)])
        self.assertAlmostEqual(surface.get_rx_distance(sites)[0],
                               3.9313415355436705, places=4)
