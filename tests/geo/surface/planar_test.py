import itertools
import unittest

from nhe.geo import Point
from nhe.geo.surface.planar import PlanarSurface
from nhe.geo.mesh import Mesh

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
            'top and bottom edges must be parallel'
        )

    def test_edges_not_parallel(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(-0.3, 1, 2), Point(0.3, -1, 2)]
        self.assert_failed_creation(1, 0, 90, corners, ValueError,
            'top and bottom edges must be parallel'
        )

    def test_top_edge_shorter_than_bottom_edge(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, 1.2, 2), Point(0, -1.2, 2)]
        self.assert_failed_creation(1, 0, 90, corners, ValueError,
            'top and bottom edges must have the same length'
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
        self.assertAlmostEqual(surface.length, tl.distance(tr))
        self.assertAlmostEqual(surface.width, tl.distance(bl))

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
        corners = [Point(0, 0, 9)] * 4
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
        self.assertAlmostEqual(8.01185807319,
                               surface.get_min_distance(Point(0, 0)))

    def test_2(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_6_CORNERS)
        self.assertAlmostEqual(40.1213468,
                               surface.get_min_distance(Point(-0.25, 0.25)))

    def test_3(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_2_CORNERS)
        self.assertAlmostEqual(7.01186304977,
                               surface.get_min_distance(Point(0, 0)))

    def test_4(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_2_CORNERS)
        self.assertAlmostEqual(55.6159556,
                               surface.get_min_distance(Point(-0.3, 0.4)))
