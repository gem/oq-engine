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
import math

import numpy

from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.geo import utils as geo_utils

from openquake.hazardlib.tests import assert_angles_equal
from openquake.hazardlib.tests.geo import _mesh_test_data


class _BaseMeshTestCase(unittest.TestCase):
    def _make_mesh(self, lons, lats, depths=None):
        mesh = Mesh(lons, lats, depths)
        self.assertIs(mesh.lons, lons)
        self.assertIs(mesh.lats, lats)
        self.assertIs(mesh.depths, depths)
        return mesh


class MeshCreationTestCase(_BaseMeshTestCase):
    def test_1d(self):
        mesh = self._make_mesh(numpy.array([1, 2, 3, 5]),
                               numpy.array([-1, -2, 4, 0]))
        self.assertEqual(len(mesh), 4)
        mesh = self._make_mesh(numpy.array([1, 2]), numpy.array([0, 0]),
                               numpy.array([10, 10]))
        self.assertEqual(len(mesh), 2)

    def test_2d(self):
        mesh = self._make_mesh(numpy.array([[1, 2], [3, 5]]),
                               numpy.array([[-1, -2], [4, 0]]))
        self.assertEqual(len(mesh), 4)
        mesh = self._make_mesh(numpy.array([[1, 2], [5, 6]]),
                               numpy.array([[0, 0], [10, 10]]),
                               numpy.array([[10, 10], [30, 30]]))
        self.assertEqual(len(mesh), 4)

    def test_one_point(self):
        co = numpy.array([0])
        mesh = self._make_mesh(co, co, co)
        self.assertEqual(len(mesh), 1)

    def test_wrong_arguments(self):
        self.assertRaises(AssertionError, self._make_mesh, [1, 2], [2, 3])
        self.assertRaises(AssertionError, self._make_mesh,
                          numpy.array([1, 2]), numpy.array([2, 3, 4]))
        self.assertRaises(AssertionError, self._make_mesh,
                          numpy.array([1, 2]), numpy.array([2, 3]),
                          numpy.array([0]))
        self.assertRaises(AssertionError, self._make_mesh,
                          numpy.array([[1], [2]]), numpy.array([[2], [3]]),
                          numpy.array([0, 1]))

    def test_from_points_list_no_depth(self):
        points = [Point(0, 1), Point(2, 3), Point(5, 7)]
        mesh = Mesh.from_points_list(points)
        self.assertTrue((mesh.lons == [0, 2, 5]).all())
        self.assertTrue((mesh.lats == [1, 3, 7]).all())
        self.assertEqual(mesh.lons.dtype, numpy.float)
        self.assertEqual(mesh.lats.dtype, numpy.float)
        self.assertIs(mesh.depths, None)

    def test_from_points_list_with_depth(self):
        points = [Point(0, 1, 2), Point(2, 3, 4), Point(5, 7, 10)]
        mesh = Mesh.from_points_list(points)
        self.assertTrue((mesh.depths == [2, 4, 10]).all())
        self.assertEqual(mesh.depths.dtype, numpy.float)


class MeshIterTestCase(_BaseMeshTestCase):
    def test_1d(self):
        mesh = self._make_mesh(numpy.array([1, 2, 3, 5]),
                               numpy.array([-1, -2, 4, 0]))
        self.assertEqual(list(mesh), [Point(1, -1), Point(2, -2),
                                      Point(3, 4), Point(5, 0)])

        mesh = self._make_mesh(numpy.array([0.1, 0.2, 0.3]),
                               numpy.array([0.9, 0.8, 0.7]),
                               numpy.array([0.4, 0.5, 0.6]))
        self.assertEqual(list(mesh),
                         [Point(0.1, 0.9, 0.4), Point(0.2, 0.8, 0.5),
                          Point(0.3, 0.7, 0.6)])

    def test_2d(self):
        lons = numpy.array([[1.1, 2.2], [2.2, 3.3]])
        lats = numpy.array([[-7, -8], [-9, -10]])
        points = list(self._make_mesh(lons, lats))
        self.assertEqual(points, [Point(1.1, -7), Point(2.2, -8),
                                  Point(2.2, -9), Point(3.3, -10)])

        depths = numpy.array([[11, 12], [13, 14]])
        points = list(self._make_mesh(lons, lats, depths))
        self.assertEqual(points, [Point(1.1, -7, 11), Point(2.2, -8, 12),
                                  Point(2.2, -9, 13), Point(3.3, -10, 14)])


class MeshSlicingTestCase(_BaseMeshTestCase):
    def test_1d(self):
        lons = numpy.array([1, 2, 3, 4, 5, 6])
        lats = numpy.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        mesh = self._make_mesh(lons, lats)
        submesh = mesh[1:4]
        self.assertIsNot(submesh, mesh)
        self.assertEqual(len(submesh), 3)
        self.assertTrue((submesh.lons == [2, 3, 4]).all())
        self.assertTrue((submesh.lats == [0.2, 0.3, 0.4]).all())
        self.assertIs(submesh.depths, None)

        depths = numpy.array([7.1, 7.2, 7.3, 7.4, 7.5, 7.6])
        mesh = self._make_mesh(lons, lats, depths)
        submesh = mesh[-4:]
        self.assertEqual(len(submesh), 4)
        self.assertTrue((submesh.lons == [3, 4, 5, 6]).all())
        self.assertTrue((submesh.lats == [0.3, 0.4, 0.5, 0.6]).all())
        self.assertTrue((submesh.depths == [7.3, 7.4, 7.5, 7.6]).all())

        with self.assertRaises(AssertionError):
            submesh = mesh[0:0]

    def test_2d(self):
        lons = lats = numpy.arange(100).reshape((10, 10))
        mesh = self._make_mesh(lons, lats)
        submesh = mesh[:3, 5:7]
        self.assertEqual(submesh.lons.shape, (3, 2))
        self.assertEqual(submesh.lats.shape, (3, 2))
        self.assertTrue((submesh.lons == [[5, 6], [15, 16], [25, 26]]).all())
        self.assertTrue((submesh.lats == submesh.lons).all())

        depths = lons + 3.1
        mesh = self._make_mesh(lons, lats, depths)
        submesh = mesh[2:4, 2:6]
        self.assertEqual(submesh.lons.shape, (2, 4))
        self.assertEqual(submesh.lats.shape, (2, 4))
        self.assertTrue((submesh.lats == submesh.lons).all())
        self.assertTrue((submesh.depths == [[25.1, 26.1, 27.1, 28.1],
                                            [35.1, 36.1, 37.1, 38.1]]).all())

    def test_wrong_indexing(self):
        coords = numpy.arange(16)
        mesh = self._make_mesh(coords, coords, coords)
        with self.assertRaises(ValueError):
            mesh[1]
        coords = coords.reshape((4, 4))
        mesh = self._make_mesh(coords, coords, coords)
        with self.assertRaises(ValueError):
            mesh[1]
        with self.assertRaises(IndexError):
            mesh[1:, 5]

    def test_preserving_the_type(self):
        lons = lats = numpy.arange(100).reshape((10, 10))
        mesh = RectangularMesh(lons, lats, depths=None)
        submesh = mesh[1:2, 3:4]
        self.assertIsInstance(submesh, RectangularMesh)


class MeshEqualityTestCase(_BaseMeshTestCase):
    def test_meshes_equal(self):
        """
        Tests if two meshes are equal
        """
        mesh1 = self._make_mesh(lons=numpy.array([1., 2., 3., 4.]),
                                lats=numpy.array([5., 6., 7., 8.]),
                                depths=numpy.array([0.5, 0.5, 0.5, 0.5]))
        mesh2 = self._make_mesh(mesh1.lons, mesh1.lats, mesh1.depths)
        self.assertTrue(mesh1 == mesh2)

    def test_meshes_unequal(self):
        """
        Checks unequal meshes
        """
        # Test 1 - depths present but values different
        mesh1 = self._make_mesh(lons=numpy.array([1., 2., 3., 4.]),
                                lats=numpy.array([5., 6., 7., 8.]),
                                depths=numpy.array([0.5, 0.5, 0.5, 0.5]))
        mesh2 = self._make_mesh(lons=numpy.array([1., 2., 3., 4.]),
                                lats=numpy.array([5.01, 6., 7., 8.3]),
                                depths=numpy.array([0.5, 0.5, 0.5, 0.5]))
        self.assertFalse(mesh1 == mesh2)
        # Test 2 - depths present in the first case, missing in the second
        mesh3 = self._make_mesh(lons=numpy.array([1., 2., 3., 4.]),
                                lats=numpy.array([5., 6., 7., 8.]),
                                depths=None)
        self.assertFalse(mesh1 == mesh3)
        # Depths missing in first case, present in the second
        self.assertFalse(mesh3 == mesh2)


class MeshGetMinDistanceTestCase(unittest.TestCase):
    # test case depends on Point.distance() working right
    def _test(self, mesh, target_mesh, expected_distance_indices):
        mesh_points = list(mesh)
        target_points = list(target_mesh)
        dists = mesh.get_min_distance(target_mesh)
        expected_dists = [mesh_points[mi].distance(target_points[ti])
                          for ti, mi in enumerate(expected_distance_indices)]
        self.assertEqual(list(dists.flat), expected_dists)
        closest_points_mesh = mesh.get_closest_points(target_mesh)
        numpy.testing.assert_equal(closest_points_mesh.lons.flat,
                                   mesh.lons.take(expected_distance_indices))
        numpy.testing.assert_equal(closest_points_mesh.lats.flat,
                                   mesh.lats.take(expected_distance_indices))
        if mesh.depths is None:
            self.assertIsNone(closest_points_mesh.depths)
        else:
            numpy.testing.assert_equal(
                closest_points_mesh.depths.flat,
                mesh.depths.take(expected_distance_indices)
            )
        self.assertEqual(closest_points_mesh.lats.shape, target_mesh.shape)

    def test_mesh_and_point_on_surface(self):
        self._test(Mesh.from_points_list([Point(0, 0), Point(0, 1),
                                          Point(0, 2)]),
                   Mesh.from_points_list([Point(1, 1), Point(-1, 0)]),
                   expected_distance_indices=[1, 0])

    def test_mesh_on_surface(self):
        self._test(Mesh.from_points_list([Point(0, 0), Point(0, 1),
                                          Point(0, 2)]),
                   Mesh.from_points_list([Point(-1, -1, 3.4), Point(2, 5)]),
                   expected_distance_indices=[0, 2])

    def test_point_on_surface(self):
        self._test(Mesh.from_points_list([Point(0, 0, 1), Point(0, 1, 2),
                                          Point(0, 2, 3)]),
                   Mesh.from_points_list([Point(0.5, 1.5)]),
                   expected_distance_indices=[1])

    def test_mesh_and_point_not_on_surface(self):
        self._test(Mesh.from_points_list([Point(0, 0, 1), Point(0, 1, 2),
                                          Point(0, 2, 3)]),
                   Mesh.from_points_list([Point(0, 1.5, 3),
                                          Point(0, 1.5, 0.9)]),
                   expected_distance_indices=[2, 1])

    def test_2d_mesh(self):
        mesh = Mesh(numpy.array([[0., 1.], [2., 3.]]),
                    numpy.array([[0., 0.], [0., 0.]]), None)
        target_mesh = Mesh(
            numpy.array([[3., 4., 5.], [-6., -7., 8.], [9., 10., 11.]]),
            numpy.array([[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]]), None
        )
        self._test(mesh, target_mesh,
                   expected_distance_indices=[3, 3, 3, 0, 0, 3, 3, 3, 3])


class MeshGetDistanceMatrixTestCase(unittest.TestCase):
    def test_zeroes(self):
        mesh = Mesh(numpy.zeros(1000), numpy.zeros(1000), None)
        matrix = mesh.get_distance_matrix()
        self.assertIsInstance(matrix, numpy.matrix)
        self.assertEqual(matrix.shape, (1000, 1000))
        self.assertTrue((matrix == 0).all())

    def test(self):
        mesh = Mesh(numpy.array([0., 1., 2., 3.]), numpy.zeros(4), None)
        matrix = mesh.get_distance_matrix()
        aaae = numpy.testing.assert_array_almost_equal
        aaae(matrix[0], [[0, 111.2, 222.4, 333.6]], decimal=1)
        aaae(matrix[1], [[111.2, 0, 111.2, 222.4]], decimal=1)
        aaae(matrix[2], [[222.4, 111.2, 0, 111.2]], decimal=1)
        aaae(matrix[3], [[333.6, 222.4, 111.2, 0]], decimal=1)
        for i in range(4):
            for j in range(i, 4):
                self.assertEqual(matrix[i, j], matrix[j, i])


class MeshConvexHullTestCase(unittest.TestCase):
    def test_two_points(self):
        mesh = Mesh(numpy.array([-10., -11.]), numpy.array([-12., -13.]), None)
        polygon = mesh.get_convex_hull()
        self.assertIsInstance(polygon, Polygon)
        elons = [-10.99996704, -11.0000323, -11.00003296, -10.00003295,
                 -9.99996795, -9.99996705]
        elats = [-13.00003147, -13.00003212, -12.99996853, -11.99996865,
                 -11.99996776, -12.00003135]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_many_points(self):
        lons = numpy.array([0.7, 0.6, 0.4, 0.6, 0.3, 0.9, 0.5, 0.4])
        lats = numpy.array([0.8, 0.5, 0.2, 0.7, 0.2, 0.4, 0.9, 0.4])
        mesh = Mesh(lons, lats, None)
        polygon = mesh.get_convex_hull()
        elons = [0.4, 0.3, 0.5, 0.7, 0.9]
        elats = [0.2, 0.2, 0.9, 0.8, 0.4]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_one_point(self):
        mesh = Mesh.from_points_list([Point(7, 7)])
        polygon = mesh.get_convex_hull()
        elons = [7.0000453, 7., 6.9999547, 7]
        elats = [7., 6.99995503, 7., 7.00004497]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)


class RectangularMeshCreationTestCase(unittest.TestCase):
    def test_wrong_shape(self):
        with self.assertRaises(AssertionError):
            RectangularMesh(numpy.array([0, 1, 2]),
                            numpy.array([0, 0, 0]), None)
            RectangularMesh(numpy.array([0, -1]), numpy.array([2, 10]),
                            numpy.array([5, 44]))

    def test_from_points_list(self):
        lons = [[0, 1], [2, 3], [4, 5]]
        lats = [[1, 2], [-1, -2], [10, 20]]
        depths = [[11.1, 11.2], [11.3, 11.4], [11.5, 11.6]]
        points = [
            [Point(lons[i][j], lats[i][j], depths[i][j])
             for j in range(len(lons[i]))]
            for i in range(len(lons))
        ]
        mesh = RectangularMesh.from_points_list(points)
        self.assertTrue((mesh.lons == lons).all())
        self.assertTrue((mesh.lats == lats).all())
        self.assertTrue((mesh.depths == depths).all())

        points = [
            [Point(lons[i][j], lats[i][j], depth=0)
             for j in range(len(lons[i]))]
            for i in range(len(lons))
        ]
        mesh = RectangularMesh.from_points_list(points)
        self.assertTrue((mesh.lons == lons).all())
        self.assertTrue((mesh.lats == lats).all())
        self.assertIsNone(mesh.depths)


class MeshJoynerBooreDistanceTestCase(unittest.TestCase):
    def test_simple(self):
        lons = numpy.array([numpy.arange(-1, 1.2, 0.2)] * 11)
        lats = lons.transpose() + 1
        depths = lats + 10
        mesh = RectangularMesh(lons, lats, depths)
        check = lambda lon, lat, depth, expected_distance, **kwargs: \
            self.assertAlmostEqual(
                mesh.get_joyner_boore_distance(
                    Mesh.from_points_list([Point(lon, lat, depth)])
                )[0],
                expected_distance, **kwargs
            )

        check(lon=0, lat=0.5, depth=0, expected_distance=0)
        check(lon=1, lat=1, depth=0, expected_distance=0)
        check(lon=0.6, lat=-1, depth=0,
              expected_distance=Point(0.6, -1).distance(Point(0.6, 0)),
              delta=0.1)
        check(lon=-0.8, lat=2.1, depth=10,
              expected_distance=Point(-0.8, 2.1).distance(Point(-0.8, 2)),
              delta=0.02)
        check(lon=0.75, lat=2.3, depth=3,
              expected_distance=Point(0.75, 2.3).distance(Point(0.75, 2)),
              delta=0.04)

    def test_vertical_mesh(self):
        lons = numpy.array([[0, 0.5, 1, 2], [0, 0.5, 1, 2]], float)
        lats = numpy.array([[0, 0, 0, 0], [0, 0, 0, 0]], float)
        depths = numpy.array([[1, 1, 1, 1], [2, 2, 2, 2]], float)
        mesh = RectangularMesh(lons, lats, depths)
        target_mesh = Mesh.from_points_list([Point(0.5, 0), Point(0.5, 1),
                                             Point(0.5, 5)])
        dists = mesh.get_joyner_boore_distance(target_mesh)
        expected_dists = [
            0, Point(0.5, 1).distance(Point(0.5, 0)),
            Point(0.5, 5).distance(Point(0.5, 0))
        ]
        numpy.testing.assert_almost_equal(dists, expected_dists)

    def test_mesh_of_two_points(self):
        lons = numpy.array([[0, 0.5, 1]], float)
        lats = numpy.array([[0, 0, 0]], float)
        depths = numpy.array([[1, 0, 1]], float)
        mesh = RectangularMesh(lons, lats, depths)
        target_mesh = Mesh.from_points_list([Point(0.5, 1), Point(0.5, 0)])
        dists = mesh.get_joyner_boore_distance(target_mesh)
        expected_dists = [Point(0.5, 1).distance(Point(0.5, 0)), 0]
        numpy.testing.assert_almost_equal(dists, expected_dists)

    def test_mesh_of_one_point(self):
        lons = numpy.array([[1.]])
        lats = numpy.array([[0.]])
        depths = numpy.array([[1.]])
        mesh = RectangularMesh(lons, lats, depths)
        target_mesh = Mesh.from_points_list([Point(1, 0), Point(0.5, 0)])
        dists = mesh.get_joyner_boore_distance(target_mesh)
        expected_dists = [0, Point(0.5, 0).distance(Point(1, 0))]
        self.assertTrue(numpy.allclose(dists, expected_dists, atol=0.2))

    def _test(self, points, site, expected_distance):
        lons, lats, depths = numpy.array(points).transpose()
        lons = lons.transpose()
        lats = lats.transpose()
        depths = depths.transpose()
        mesh = RectangularMesh(lons, lats, depths)
        distance = mesh.get_joyner_boore_distance(
            Mesh.from_points_list([Point(*site)])
        )[0]
        self.assertAlmostEqual(distance, expected_distance, delta=0.02)

    def test3(self):
        self._test(_mesh_test_data.TEST3_MESH, _mesh_test_data.TEST3_SITE,
                   _mesh_test_data.TEST3_JB_DISTANCE)

    def test4(self):
        self._test(_mesh_test_data.TEST4_MESH, _mesh_test_data.TEST4_SITE,
                   _mesh_test_data.TEST4_JB_DISTANCE)

    def test5(self):
        self._test(_mesh_test_data.TEST5_MESH, _mesh_test_data.TEST5_SITE,
                   _mesh_test_data.TEST5_JB_DISTANCE)

    def test_version(self):
        # this test is sensitive to different versions of shapely/libgeos
        lons = numpy.array(
            [[-121.3956, -121.41050474, -121.42542273, -121.44035399,
              -121.45529855, -121.47025643],
             [-121.3956, -121.41050474, -121.42542273, -121.44035399,
              -121.45529855, -121.47025643]])
        lats = numpy.array(
            [[36.8257, 36.85963772, 36.89357357, 36.92750756,
              36.96143968, 36.99536993],
             [36.8257, 36.85963772, 36.89357357, 36.92750756,
              36.96143968,  36.99536993]])
        mesh = RectangularMesh(lons, lats)
        dist = mesh.get_joyner_boore_distance(
            Mesh.from_points_list([Point(-121.76, 37.23)]))
        dist_ubuntu_12_04 = 36.61260128
        dist_ubuntu_14_04 = 36.61389245
        self.assertTrue(numpy.allclose(dist, dist_ubuntu_12_04) or
                        numpy.allclose(dist, dist_ubuntu_14_04))


class RectangularMeshGetMiddlePointTestCase(unittest.TestCase):
    def test_odd_rows_odd_columns_no_depths(self):
        lons = numpy.array([numpy.arange(-1, 1.2, 0.2)] * 11)
        lats = lons.transpose() * 10
        mesh = RectangularMesh(lons, lats, depths=None)
        self.assertEqual(mesh.get_middle_point(), Point(0, 0, 0))

    def test_odd_rows_odd_columns_with_depths(self):
        lons = numpy.array([numpy.arange(-1, 1.2, 0.2)] * 11)
        lats = lons.transpose() * 10
        depths = lats + 10
        mesh = RectangularMesh(lons, lats, depths)
        self.assertEqual(mesh.get_middle_point(), Point(0, 0, 10))

    def test_odd_rows_odd_columns_with_topo(self):
        lons = numpy.array([numpy.arange(-1, 1.2, 0.2)] * 11)
        lats = lons.transpose()
        depths = lats - 1
        mesh = RectangularMesh(lons, lats, depths)
        self.assertEqual(mesh.get_middle_point(), Point(0, 0, -1))

    def test_odd_rows_even_columns_no_depths(self):
        lons = numpy.array([[10, 20, 30, 40]])
        lats = numpy.array([[30] * 4])
        mesh = RectangularMesh(lons, lats, depths=None)
        self.assertEqual(mesh.get_middle_point(), Point(25, 30.094679))

    def test_odd_rows_even_columns_with_depths(self):
        lons = numpy.array([[0, 20, 30, 90]])
        lats = numpy.array([[30] * 4])
        depths = numpy.array([[2, 7, 8, 10]])
        mesh = RectangularMesh(lons, lats, depths=depths)
        self.assertEqual(mesh.get_middle_point(), Point(25, 30.094679, 7.5))

    def test_odd_rows_even_columns_with_topo(self):
        lons = numpy.array([[0, 20, 30, 90]])
        lats = numpy.array([[30] * 4])
        depths = numpy.array([[2, 1, -3, -5]])
        mesh = RectangularMesh(lons, lats, depths=depths)
        self.assertEqual(mesh.get_middle_point(), Point(25, 30.094679, -1))

    def test_even_rows_odd_columns_no_depths(self):
        lons = numpy.array([[-1, 0, 1, 2, 3], [-1.5, 0.5, 1.5, 2.5, 3.5]])
        lats = numpy.array([[-0.01] * 5, [-0.015] * 5])
        mesh = RectangularMesh(lons, lats, depths=None)
        self.assertEqual(mesh.get_middle_point(), Point(1.25, -0.0125, 0))

    def test_even_rows_odd_columns_with_depth(self):
        lons = numpy.array([[20], [21]])
        lats = numpy.array([[-1], [1]])
        depths = numpy.array([[11.1], [11.3]])
        mesh = RectangularMesh(lons, lats, depths=depths)
        self.assertEqual(mesh.get_middle_point(), Point(20.5, 0, 11.2))

    def test_even_rows_odd_columns_with_topo(self):
        lons = numpy.array([[20], [21]])
        lats = numpy.array([[-1], [1]])
        depths = numpy.array([[-1.1], [-1.3]])
        mesh = RectangularMesh(lons, lats, depths=depths)
        self.assertEqual(mesh.get_middle_point(), Point(20.5, 0, -1.2))

    def test_even_rows_even_columns_no_depths(self):
        lons = numpy.array([[10, 20], [10.002, 20.002]])
        lats = numpy.array([[10, -10], [8, -8]])
        mesh = RectangularMesh(lons, lats, depths=None)
        self.assertEqual(mesh.get_middle_point(), Point(15.001, 0))

    def test_even_rows_even_columns_with_depths(self):
        lons = numpy.array([[10, 20], [12, 22]])
        lats = numpy.array([[10, -10], [8, -9]])
        depths = numpy.array([[2, 3], [4, 5]])
        mesh = RectangularMesh(lons, lats, depths=depths)
        self.assertEqual(mesh.get_middle_point(),
                         Point(15.996712, -0.250993, 3.5))

    def test_even_rows_even_columns_with_topo(self):
        lons = numpy.array([[10, 20], [12, 22]])
        lats = numpy.array([[10, -10], [8, -9]])
        depths = numpy.array([[-2, -3], [-4, -5]])
        mesh = RectangularMesh(lons, lats, depths=depths)
        self.assertEqual(mesh.get_middle_point(),
                         Point(15.996712, -0.250993, -3.5))


class RectangularMeshGetMeanInclinationAndAzimuthTestCase(unittest.TestCase):
    def test_on_surface(self):
        row1 = [Point(0, 0), Point(0, 1)]
        row2 = [Point(1, 0), Point(1, 1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertEqual(dip, 0)
        self.assertAlmostEqual(strike, 0, delta=0.5)

        row1 = [Point(0, 0), Point(0, -1)]
        row2 = [Point(1, 0), Point(1, -1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertEqual(dip, 0)
        self.assertAlmostEqual(strike, 180, delta=0.5)

        row1 = [Point(0, 0), Point(1, 1)]
        row2 = [Point(1, 0), Point(2, 1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertEqual(dip, 0)
        self.assertAlmostEqual(strike, 45, delta=0.01)

        row1 = [Point(0, 0), Point(1, -1)]
        row2 = [Point(1, 0), Point(2, -1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertEqual(dip, 0)
        self.assertAlmostEqual(strike, 135, delta=0.01)

        row1 = [Point(0, 0), Point(-1, -1)]
        row2 = [Point(-1, 0), Point(-2, -1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertEqual(dip, 0)
        self.assertAlmostEqual(strike, 225, delta=0.01)

        row1 = [Point(0, 0), Point(-1, 1)]
        row2 = [Point(-1, 0), Point(-2, 1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertEqual(dip, 0)
        self.assertAlmostEqual(strike, 315, delta=0.01)

    def test_one_cell(self):
        top = [Point(0, -0.01), Point(0, 0.01)]
        bottom = [Point(0.01, -0.01, 1.11), Point(0.01, 0.01, 1.11)]

        mesh = RectangularMesh.from_points_list([top, bottom])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(dip, 45, delta=0.05)
        self.assertAlmostEqual(strike, 0, delta=0.05)

        row1 = [Point(45, -0.1), Point(45.2, 0.1)]
        row2 = [Point(45, -0.1, 1), Point(45.2, 0.1, 1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(dip, 90)
        self.assertAlmostEqual(strike, 45, delta=0.1)

        row1 = [Point(90, -0.1), Point(90, 0.1)]
        row2 = [Point(90, -0.1, 1), Point(90, 0.1, 1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(dip, 90)
        self.assertAlmostEqual(strike, 0, delta=0.1)

    def test_one_cell_topo(self):
        top = [Point(0, -0.01, -3.00), Point(0, 0.01, -3.00)]
        bottom = [Point(0.01, -0.01, -1.89), Point(0.01, 0.01, -1.89)]

        mesh = RectangularMesh.from_points_list([top, bottom])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(dip, 45, delta=0.1)
        self.assertAlmostEqual(strike, 0, delta=0.05)

        row1 = [Point(45, -0.1, -3.00), Point(45.2, 0.1, -3.00)]
        row2 = [Point(45, -0.1, -2.00), Point(45.2, 0.1, -2.00)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(dip, 90)
        self.assertAlmostEqual(strike, 225, delta=0.1)

        row1 = [Point(90, -0.1, -3.00), Point(90, 0.1, -3.00)]
        row2 = [Point(90, -0.1, -2.00), Point(90, 0.1, -2.00)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(dip, 90)
        self.assertAlmostEqual(strike, 0, delta=0.1)

    def test_two_cells(self):
        top = [Point(0, -0.01), Point(0, 0.01)]
        middle = [Point(0.01, -0.01, 1.11), Point(0.01, 0.01, 1.11)]
        bottom = [Point(0.01, -0.01, 2.22), Point(0.01, 0.01, 2.22)]

        mesh = RectangularMesh.from_points_list([top, middle, bottom])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(dip, math.degrees(math.atan2(2, 1)), delta=0.1)
        self.assertAlmostEqual(strike, 0, delta=0.02)

        bottom = [Point(0.01, -0.01, 3.33), Point(0.01, 0.01, 3.33)]
        mesh = RectangularMesh.from_points_list([top, middle, bottom])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(dip, math.degrees(math.atan2(3, 1)), delta=0.1)
        self.assertAlmostEqual(strike, 0, delta=0.02)

        row1 = [Point(90, -0.1), Point(90, 0), Point(90, 0.1)]
        row2 = [Point(90, -0.1, 1), Point(90, 0, 1), Point(90, 0.1, 1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(dip, 90)
        assert_angles_equal(self, strike, 360, delta=1e-7)

        row1 = [Point(-90.1, -0.1), Point(-90, 0), Point(-89.9, 0.1)]
        row2 = [Point(-90.0, -0.1, 1), Point(-89.9, 0, 1),
                Point(-89.8, 0.1, 1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(strike, 45, delta=1e-4)

        row1 = [Point(-90.1, -0.1), Point(-90, 0), Point(-89.9, 0.1)]
        row2 = [Point(-90.0, -0.1, 1), Point(-89.9, 0, 1),
                Point(-89.8, 0.1, 1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(strike, 45, delta=1e-3)

        row1 = [Point(-90.1, -0.1), Point(-90, 0), Point(-89.9, 0.1)]
        row2 = [Point(-90.2, -0.1, 1), Point(-90.1, 0, 1), Point(-90, 0.1, 1)]
        mesh = RectangularMesh.from_points_list([row1, row2])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(strike, 225, delta=1e-3)

    def test_one_cell_unequal_area(self):
        # top-left triangle is vertical, has dip of 90 degrees, zero
        # strike and area of 1 by 1 over 2. bottom-right one has dip
        # of atan2(1, sqrt(2) / 2.0) which is 54.73561 degrees, strike
        # of 45 degrees and area that is 1.73246136 times area of the
        # first one's. weighted mean dip is 67.5 degrees and weighted
        # mean strike is 28.84 degrees
        top = [Point(0, -0.01), Point(0, 0.01)]
        bottom = [Point(0, -0.01, 2.22), Point(0.02, 0.01, 2.22)]

        mesh = RectangularMesh.from_points_list([top, bottom])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        self.assertAlmostEqual(dip, 67.5, delta=0.05)
        self.assertAlmostEqual(strike, 28.84, delta=0.05)

    def test_dip_over_90_degree(self):
        top = [Point(0, -0.01), Point(0, 0.01)]
        bottom = [Point(-0.01, -0.01, 1.11), Point(-0.01, 0.01, 1.11)]

        mesh = RectangularMesh.from_points_list([top, bottom])
        dip, strike = mesh.get_mean_inclination_and_azimuth()
        # dip must be still in a range 0..90
        self.assertAlmostEqual(dip, 45, delta=0.05)
        # strike must be reversed
        self.assertAlmostEqual(strike, 180, delta=0.05)


class RectangularMeshGetCellDimensionsTestCase(unittest.TestCase):
    def setUp(self):
        super(RectangularMeshGetCellDimensionsTestCase, self).setUp()
        self.original_spherical_to_cartesian = geo_utils.spherical_to_cartesian
        geo_utils.spherical_to_cartesian = lambda lons, lats, depths: (
            self.points
        )

    def tearDown(self):
        geo_utils.spherical_to_cartesian = self.original_spherical_to_cartesian

    def _test(self, points, centroids, lengths, widths, areas):
        fake_coords = numpy.array([[0]])
        self.points = numpy.array(points, dtype=float)
        mesh = RectangularMesh(fake_coords, fake_coords, fake_coords)
        cell_center, cell_length, cell_width, cell_area \
                = mesh.get_cell_dimensions()
        self.assertTrue(numpy.allclose(cell_length, lengths),
                        '%s != %s' % (cell_length, lengths))
        self.assertTrue(numpy.allclose(cell_width, widths),
                        '%s != %s' % (cell_width, widths))
        self.assertTrue(numpy.allclose(cell_area, areas),
                        '%s != %s' % (cell_area, areas))
        self.assertTrue(numpy.allclose(cell_center, centroids),
                        '%s != %s' % (cell_center, centroids))

    def test_one_cell(self):
        self._test(
            points=[[(1., 1., 1.), (2., 1., 1.)],
                    [(1., 1., -2.), (2., 1., -2.)]],
            centroids=[(1.5, 1, -0.5)],
            lengths=[1],
            widths=[3],
            areas=[3]
        )

    def test_unequal_triangle_areas(self):
        self._test(
            points=[[(10, 0, 0), (11, 0, 0)],
                    [(10, -1, 0), (11, -2, 0)]],
            centroids=[(((10 + 1/3.) * 0.5 + (10 + 2/3.) * 1) / 1.5,
                        ((-1/3.) * 0.5 + (-1) * 1) / 1.5,
                        0)],
            lengths=[(1 * 0.5 + math.sqrt(2) * 1) / (0.5 + 1)],
            widths=[(1 * 0.5 + 2 * 1) / (0.5 + 1)],
            areas=[0.5 + 1]
        )

    def test_unequal_triangle_areas_topo(self):
        self._test(
            points=[[(10, 0, 0), (11, 0, 0)],
                   [(10, 0, -1), (11, 0, -2)]],
            centroids=[(((10 + 1/3.) * 0.5 + (10 + 2/3.) * 1) / 1.5, 0,
                        ((-1/3.) * 0.5 + (-1) * 1) / 1.5)],
            lengths=[(1 * 0.5 + math.sqrt(2) * 1) / (0.5 + 1)],
            widths=[(1 * 0.5 + 2 * 1) / (0.5 + 1)],
            areas=[0.5 + 1]
        )

    def test_two_unequal_cells(self):
        self._test(
            points=[[(0, 0, 0), (0, 0, 1), (0, 0, 3)],
                    [(0, 1, 0), (0, 1, 1), (0, 1, 3)]],
            centroids=[(0, 0.5, 0.5), (0, 0.5, 2)],
            lengths=[1, 2],
            widths=[1, 1],
            areas=[1, 2]
        )

    def test_two_unequal_cells_topo(self):
        self._test(
            points=[[(0, 0, -1), (0, 0, 0), (0, 0, 2)],
                    [(0, 1, -1), (0, 1, 0), (0, 1, 2)]],
            centroids=[(0, 0.5, -0.5), (0, 0.5, 1)],
            lengths=[1, 2],
            widths=[1, 1],
            areas=[1, 2]
        )


class RectangularMeshTriangulateTestCase(unittest.TestCase):
    def test_simple(self):
        lons = numpy.array([[0, 0.0089946277931563321],
                            [0, 0.0089974527390248322]])
        lats = numpy.array([[0, 0], [0, 0]], dtype=float)
        depths = numpy.array([[1, 0.99992150706475513],
                              [3, 2.9999214824129012]])
        mesh = RectangularMesh(lons, lats, depths)
        points, along_azimuth, updip, diag = mesh.triangulate()
        self.assertTrue(numpy.allclose(points, [
            [(6370, 0, 0), (6370, 1, 0)],
            [(6368, 0, 0), (6368, 1, 0)]
        ]))
        self.assertTrue(numpy.allclose(along_azimuth, [
            [(0, 1, 0)], [(0, 1, 0)]
        ]))
        self.assertTrue(numpy.allclose(updip, [
            [(2, 0, 0)], [(2, 0, 0)],
        ]))
        self.assertTrue(numpy.allclose(diag, [
            [(2, 1, 0)]
        ]))


class RectangularMeshGetProjectionEnclosingPolygonTestCase(unittest.TestCase):
    def _test(self, lons, lats, depths, expected_coords):
        mesh = RectangularMesh(lons, lats, depths)
        proj, polygon = mesh._get_proj_enclosing_polygon()
        self.assertTrue(polygon.is_valid)
        self.assertEqual(list(polygon.interiors), [])
        coords = numpy.array(proj(*numpy.array(polygon.exterior).transpose(),
                                  reverse=True)).transpose()
        numpy.testing.assert_almost_equal(coords, expected_coords, decimal=4)
        return polygon

    def test_simple(self):
        lons = numpy.array([[-0.1, 0.1],
                            [-0.1, 0.1]])
        lats = numpy.array([[-0.1, -0.1],
                            [0.1, 0.1]])
        depths = numpy.array([[2., 3.],
                              [8., 9.]])
        expected_coords = [(-0.1, -0.1), (-0.1, 0.1), (0.1, 0.1), (0.1, -0.1),
                           (-0.1, -0.1)]
        polygon = self._test(lons, lats, depths, expected_coords)

        coords2d = numpy.array(polygon.exterior.coords)
        expected_coords2d = [(-11.12, -11.12), (-11.12, 11.12), (11.12, 11.12),
                             (11.12, -11.12), (-11.12, -11.12)]
        numpy.testing.assert_almost_equal(coords2d, expected_coords2d,
                                          decimal=2)

    def test_4_cells_by_4_cells(self):
        lons, lats = numpy.meshgrid(numpy.arange(-2, 3) / 10.,
                                    numpy.arange(-2, 3) / 10.)
        depths = None
        expected_coords = [(-0.2, -0.2), (-0.2, 0.2), (0.2, 0.2),
                           (0.2, -0.2), (-0.2, -0.2)]
        self._test(lons, lats, depths, expected_coords)

    def test_vertical_mesh(self):
        lons = numpy.array([[-0.2, -0.1, 0., 0.1, 0.2]] * 5)
        depths = numpy.array([[9] * 5, [11] * 5, [12] * 5, [13] * 5, [14] * 5])
        lats = numpy.zeros_like(lons)
        expected_coords = [(-0.2, 0), (0.2, 0), (0.2, 0), (-0.2, 0),
                           (-0.2, 0)]
        self._test(lons, lats, depths, expected_coords)

    def test_halfvertical_mesh(self):
        lons = numpy.array([[22.3, 22.3, 22.3], [22.3, 22.3, 22.4]])
        lats = numpy.array([[0.2, 0.3, 0.4]] * 2)
        depths = numpy.array([[1., 1., 1.], [2., 2., 2.]])
        expected_coords = [(22.3, 0.2), (22.3, 0.4), (22.4, 0.4), (22.3, 0.3),
                           (22.3, 0.2), (22.3, 0.2)]
        self._test(lons, lats, depths, expected_coords)

    def test_bowtie_mesh(self):
        lons = numpy.array([[0., 0., 0.1], [0.1, 0.1, 0.]])
        lats = numpy.array([[0., 0.1, 0.2]] * 2)
        depths = numpy.array([[1., 1., 1.], [2., 2., 2.]])
        expected_coords = [(0.05, 0.15), (-0, 0.2), (0.1, 0.2), (0.05, 0.15),
                           (0.1, 0.1), (0.1, -0), (-0, -0), (-0, 0.1),
                           (0.05, 0.15)]
        self._test(lons, lats, depths, expected_coords)

    def test_bowtie_mesh2(self):
        lons = numpy.array([[0., 0.05, 0.], [0.1, 0.05, 0.1]])
        lats = numpy.array([[0., 0.1, 0.2]] * 2)
        depths = numpy.array([[1., 1., 1.], [2., 2., 2.]])
        expected_coords = [(-0, 0.2), (0.1, 0.2), (0.05, 0.1), (0.1, -0),
                           (-0, -0), (0.05, 0.1), (-0, 0.2)]
        self._test(lons, lats, depths, expected_coords)

    def test_reversing_dip(self):
        lons = numpy.array([[0., 0., 0.], [0.1, 0.1, 0.1], [0., 0., 0.]])
        lats = numpy.array([[0., 0.1, 0.2]] * 3)
        depths = numpy.array([[1., 1., 1.], [2., 2., 2.], [3., 3., 3.]])
        expected_coords = [(-0, 0.2), (0.1, 0.2), (0.1, -0), (-0, -0),
                           (-0, 0.2)]
        self._test(lons, lats, depths, expected_coords)


class RectangularMeshGetMeanWidthTestCase(unittest.TestCase):
    def test_invalid_mesh(self):
        lons = numpy.array([[0.1]])
        lats = numpy.array([[0.1]])
        depths = numpy.array([[2.0]])
        mesh = RectangularMesh(lons, lats, depths)
        self.assertRaises(AssertionError, mesh.get_mean_width)

    def test_mesh_width(self):
        lons = numpy.array([[0.1, 0.1, 0.1, 0.1],
                            [0.1, 0.1, 0.1, 0.1],
                            [0.1, 0.1, 0.1, 0.1]])
        lats = numpy.array([[0.1, 0.10899322, 0.11798643, 0.12697965],
                            [0.1, 0.10899322, 0.11798643, 0.12697965],
                            [0.1, 0.10899322, 0.11798643, 0.12697965]])
        depths = numpy.array([[2.0, 2.0, 2.0, 2.0],
                              [3.0, 3.0, 3.0, 3.0],
                              [4.0, 4.0, 4.0, 4.0]])
        mesh = RectangularMesh(lons, lats, depths)
        self.assertAlmostEqual(mesh.get_mean_width(), 2.0)
