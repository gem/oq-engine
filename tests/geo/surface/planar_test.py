import itertools
import unittest

from nhe.geo import Point
from nhe.geo.surface.planar import PlanarSurface
from nhe.geo.mesh import RectangularMesh

from tests.geo.surface import _planar_test_data as test_data


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


class PlanarSurfaceGetMeshTestCase(unittest.TestCase):
    def _test(self, corner_points, mesh_spacing, expected_mesh):
        strike = 0
        dip = 90
        surface = PlanarSurface(mesh_spacing, strike, dip, *corner_points)
        mesh = surface.get_mesh()
        self.assertIs(mesh, surface.get_mesh())
        expected_mesh = list(itertools.chain(*expected_mesh))
        self.assertEqual(len(mesh), len(expected_mesh))
        self.assertIsInstance(mesh, RectangularMesh)
        for i, point in enumerate(mesh):
            expected_point = Point(*expected_mesh[i])
            distance = expected_point.distance(point) * 1e3
            self.assertAlmostEqual(
                0, distance, delta=2,  # allow discrepancy of 2 meters
                msg='point %d is off: %s != %s (distance is %.3fm)'
                    % (i, point, expected_point, distance)
            )

    def test_2(self):
        self._test(test_data.TEST_2_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_2_MESH)

    def test_3(self):
        self._test(test_data.TEST_3_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_3_MESH)

    def test_4(self):
        self._test(test_data.TEST_4_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_4_MESH)

    def test_5(self):
        self._test(test_data.TEST_5_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_5_MESH)

    def test_6(self):
        corners = [Point(0, 0, 9)] * 4
        mesh = [[(0, 0, 9)]]
        self._test(corners, mesh_spacing=1, expected_mesh=mesh)

    def test_7_rupture_1(self):
        self._test(test_data.TEST_7_RUPTURE_1_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_7_RUPTURE_1_MESH)

    def test_7_rupture_2(self):
        self._test(test_data.TEST_7_RUPTURE_2_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_7_RUPTURE_2_MESH)

    def test_7_rupture_3(self):
        self._test(test_data.TEST_7_RUPTURE_3_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_7_RUPTURE_3_MESH)

    def test_7_rupture_4(self):
        self._test(test_data.TEST_7_RUPTURE_4_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_7_RUPTURE_4_MESH)

    def test_7_rupture_5(self):
        self._test(test_data.TEST_7_RUPTURE_5_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_7_RUPTURE_5_MESH)

    def test_7_rupture_6(self):
        self._test(test_data.TEST_7_RUPTURE_6_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_7_RUPTURE_6_MESH)

    def test_7_rupture_7(self):
        self._test(test_data.TEST_7_RUPTURE_7_CORNERS, mesh_spacing=1,
                   expected_mesh=test_data.TEST_7_RUPTURE_7_MESH)

    def test_7_rupture_8(self):
        self._test(test_data.TEST_7_RUPTURE_8_CORNERS, mesh_spacing=1,
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
