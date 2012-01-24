import unittest

from nhe.common.geo import Point
from nhe.surface.planar import PlanarSurface
import _planar_test_data as test_data


class PlanarSurfaceGetMeshTestCase(unittest.TestCase):
    def _test(self, corner_points, mesh_spacing, expected_mesh):
        surface = PlanarSurface(*corner_points)
        mesh = surface.get_mesh(mesh_spacing=mesh_spacing)
        self.assertEqual(len(mesh), len(expected_mesh))
        num_hor_points = len(expected_mesh[0])
        self.assertTrue(all(len(row) == num_hor_points for row in mesh))
        for i, row in enumerate(mesh):
            expected_row = expected_mesh[i]
            for j, point in enumerate(row):
                expected_point = Point(*expected_row[j])
                distance = expected_point.distance(point) * 1e3
                self.assertAlmostEqual(
                    0, distance, delta=2,  # allow discrepancy of 2 meters
                    msg='row %d point %d is off: %s != %s (distance is %.3fm)'
                        % (i, j, point, expected_point, distance)
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
