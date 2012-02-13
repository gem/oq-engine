import unittest

import numpy

from nhe.geo.point import Point
from nhe.geo.mesh import Mesh


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
        lons = lats = numpy.array(range(100)).reshape((10, 10))
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
        coords = numpy.array(range(16))
        mesh = self._make_mesh(coords, coords, coords)
        with self.assertRaises(AssertionError):
            mesh[1]
        coords = coords.reshape((4, 4))
        mesh = self._make_mesh(coords, coords, coords)
        with self.assertRaises(AssertionError):
            mesh[1]
        with self.assertRaises(AssertionError):
            mesh[1:, 5]
