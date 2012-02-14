import itertools
import unittest

from nhe.geo.point import Point
from nhe.geo.mesh import Mesh


class SurfaceTestCase(unittest.TestCase):

    def assert_mesh_is(self, surface, expected_mesh):
        mesh = surface.get_mesh()
        self.assertIs(mesh, surface.get_mesh())

        expected_mesh = list(itertools.chain(*expected_mesh))
        self.assertEqual(len(mesh), len(expected_mesh))
        self.assertIsInstance(mesh, Mesh)

        for i, point in enumerate(mesh):
            expected_point = Point(*expected_mesh[i])
            distance = expected_point.distance(point) * 1e3

            self.assertAlmostEqual(
                0, distance, delta=2, # allow discrepancy of 2 meters
                msg="point %d is off: %s != %s (distance is %.3fm)"
                    % (i, point, expected_point, distance)
            )
