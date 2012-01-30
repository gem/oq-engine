# encoding: utf-8

import unittest

from nhe.common import geo


class SurfaceTestCase(unittest.TestCase):

    def assert_mesh_is(self, surface, mesh_spacing, expected_mesh):
        mesh = surface.get_mesh(mesh_spacing=mesh_spacing)
        self.assertEqual(len(mesh), len(expected_mesh))

        num_hor_points = len(expected_mesh[0])
        self.assertTrue(all(len(row) == num_hor_points for row in mesh))

        for i, row in enumerate(mesh):
            expected_row = expected_mesh[i]

            for j, point in enumerate(row):
                expected_point = geo.Point(*expected_row[j])
                distance = expected_point.distance(point) * 1e3

                self.assertAlmostEqual(
                    0, distance, delta=2,  # allow discrepancy of 2 meters
                    msg="row %d point %d is off: %s != %s (distance is %.3fm)"
                        % (i, j, point, expected_point, distance))
