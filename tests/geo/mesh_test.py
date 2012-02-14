import unittest

import numpy

from nhe.geo.point import Point
from nhe.geo.mesh import Mesh, RectangularMesh

from tests.geo import _mesh_test_data


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

    def test_preserving_the_type(self):
        lons = lats = numpy.array(range(100)).reshape((10, 10))
        mesh = RectangularMesh(lons, lats, depths=None)
        submesh = mesh[1:2, 3:4]
        self.assertIsInstance(submesh, RectangularMesh)


class MeshGetMinDistanceTestCase(unittest.TestCase):
    def test_1(self):
        mesh = Mesh.from_points_list([Point(0, 0), Point(0, 1), Point(0, 2)])
        self.assertEqual(mesh.get_min_distance(Point(1, 1)),
                         Point(1, 1).distance(Point(0, 1)))
        self.assertEqual(mesh.get_min_distance(Point(-1, 0)),
                         Point(-1, 0).distance(Point(0, 0)))


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
             for j in xrange(len(lons[i]))]
            for i in xrange(len(lons))
        ]
        mesh = RectangularMesh.from_points_list(points)
        self.assertTrue((mesh.lons == lons).all())
        self.assertTrue((mesh.lats == lats).all())
        self.assertTrue((mesh.depths == depths).all())

        points = [
            [Point(lons[i][j], lats[i][j], depth=0)
             for j in xrange(len(lons[i]))]
            for i in xrange(len(lons))
        ]
        mesh = RectangularMesh.from_points_list(points)
        self.assertTrue((mesh.lons == lons).all())
        self.assertTrue((mesh.lats == lats).all())
        self.assertIsNone(mesh.depths)


class RectangularMeshBoundingMeshTestCase(unittest.TestCase):
    def test_single_row(self):
        lons = numpy.array([[0, 1, 2, 3, 4, 5]])
        lats = numpy.array([[-1, -2, -3, -4, -5, -6]])
        mesh = RectangularMesh(lons, lats, depths=None)
        bounding_mesh = mesh._get_bounding_mesh()
        self.assertIsInstance(bounding_mesh, Mesh)
        self.assertTrue((bounding_mesh.lons == lons[0]).all())
        self.assertTrue((bounding_mesh.lats == lats[0]).all())
        self.assertIsNone(bounding_mesh.depths)

        depths = numpy.array([[10, 11, 12, 13, 14, 15]])
        mesh = RectangularMesh(lons, lats, depths)
        bounding_mesh = mesh._get_bounding_mesh()
        self.assertIsNotNone(bounding_mesh.depths)
        self.assertTrue((bounding_mesh.depths == depths[0]).all())

        bounding_mesh = mesh._get_bounding_mesh(with_depths=False)
        self.assertIsNone(bounding_mesh.depths)

    def test_single_column(self):
        lons = numpy.array([[0], [1], [2], [3], [4], [5]])
        lats = numpy.array([[-1], [-2], [-3], [-4], [-5], [-6]])
        mesh = RectangularMesh(lons, lats, depths=None)
        bounding_mesh = mesh._get_bounding_mesh()
        self.assertTrue((bounding_mesh.lons == lons.flatten()).all())
        self.assertTrue((bounding_mesh.lats == lats.flatten()).all())
        self.assertIsNone(bounding_mesh.depths)

        depths = numpy.array([[10], [11], [12], [13], [14], [15]])
        mesh = RectangularMesh(lons, lats, depths)
        bounding_mesh = mesh._get_bounding_mesh()
        self.assertIsNotNone(bounding_mesh.depths)
        self.assertTrue((bounding_mesh.depths == depths.flatten()).all())

        bounding_mesh = mesh._get_bounding_mesh(with_depths=False)
        self.assertIsNone(bounding_mesh.depths)

    def test_rectangular(self):
        lons = numpy.array(range(100)).reshape((10, 10))
        lats = numpy.negative(lons)

        mesh = RectangularMesh(lons, lats, depths=None)
        bounding_mesh = mesh._get_bounding_mesh()
        expected_lons = numpy.array([
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
            19, 29, 39, 49, 59, 69, 79, 89,
            99, 98, 97, 96, 95, 94, 93, 92, 91,
            90, 80, 70, 60, 50, 40, 30, 20, 10
        ])
        expected_lats = numpy.negative(expected_lons)
        self.assertTrue((bounding_mesh.lons == expected_lons).all())
        self.assertTrue((bounding_mesh.lats == expected_lats).all())
        self.assertIsNone(bounding_mesh.depths)

        depths = lons + 10
        mesh = RectangularMesh(lons, lats, depths)
        expected_depths = expected_lons + 10
        bounding_mesh = mesh._get_bounding_mesh()
        self.assertIsNotNone(bounding_mesh.depths)
        self.assertTrue((bounding_mesh.depths
                         == expected_depths.flatten()).all())

        bounding_mesh = mesh._get_bounding_mesh(with_depths=False)
        self.assertIsNone(bounding_mesh.depths)


class RectangularMeshJoynerBooreDistanceTestCase(unittest.TestCase):
    def test_simple(self):
        lons = numpy.array([numpy.arange(-1, 1.2, 0.2)] * 11)
        lats = lons.transpose() + 1
        depths = lats + 10
        mesh = RectangularMesh(lons, lats, depths)

        check = lambda lon, lat, depth, expected_distance: \
            self.assertAlmostEqual(
                mesh.get_joyner_boore_distance(Point(lon, lat, depth)),
                expected_distance
            )

        check(lon=0, lat=0.5, depth=0, expected_distance=0)
        check(lon=1, lat=1, depth=0, expected_distance=0)
        check(lon=0.6, lat=-1, depth=0, expected_distance=111.1948743)
        check(lon=-0.8, lat=2.1, depth=10, expected_distance=11.1194874)

    def test_vertical_mesh(self):
        lons = numpy.array([[0, 1], [1, 0]])
        lats = numpy.array([[0, 0], [0, 0]])
        depths = numpy.array([[1, 1], [2, 2]])
        mesh = RectangularMesh(lons, lats, depths)
        self.assertEqual(mesh.get_joyner_boore_distance(Point(0.5, 0, 0)), 0)

    def _test(self, points, site, expected_distance):
        lons, lats, depths = numpy.array(points).transpose()
        lons = lons.transpose()
        lats = lats.transpose()
        depths = depths.transpose()
        mesh = RectangularMesh(lons, lats, depths)
        distance = mesh.get_joyner_boore_distance(Point(*site))
        self.assertAlmostEqual(distance, expected_distance, places=4)

    def test3(self):
        self._test(_mesh_test_data.TEST3_MESH, _mesh_test_data.TEST3_SITE,
                   _mesh_test_data.TEST3_JB_DISTANCE)

    def test4(self):
        self._test(_mesh_test_data.TEST4_MESH, _mesh_test_data.TEST4_SITE,
                   _mesh_test_data.TEST4_JB_DISTANCE)

    def test5(self):
        self._test(_mesh_test_data.TEST5_MESH, _mesh_test_data.TEST5_SITE,
                   _mesh_test_data.TEST5_JB_DISTANCE)
