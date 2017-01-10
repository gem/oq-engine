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
import itertools
import unittest

from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.mesh import Mesh


def assert_mesh_is(testcase, surface, expected_mesh):
    mesh = surface.get_mesh()
    testcase.assertIs(mesh, surface.get_mesh())

    expected_mesh = list(itertools.chain(*expected_mesh))
    testcase.assertEqual(len(mesh), len(expected_mesh))
    testcase.assertIsInstance(mesh, Mesh)

    for i, point in enumerate(mesh):
        expected_point = Point(*expected_mesh[i])
        distance = expected_point.distance(point) * 1e3

        testcase.assertAlmostEqual(
            0, distance, delta=2, # allow discrepancy of 2 meters
            msg="point %d is off: %s != %s (distance is %.3fm)"
                % (i, point, expected_point, distance)
        )

class SurfaceTestCase(unittest.TestCase):
    def assert_mesh_is(self, surface, expected_mesh):
        return assert_mesh_is(self, surface, expected_mesh)
