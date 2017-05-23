# The Hazard Library
# Copyright (C) 2014-2017 GEM Foundation
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
import numpy as np

from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.surface.gridded import GriddedSurface
from openquake.hazardlib.geo.mesh import Mesh

POINTS = [Point(0, 0, 0), Point(0, 1, 0), Point(1, 1, 0),
          Point(1, 0, 0)]


class GriddedSurfaceTestCase(unittest.TestCase):

    def setUp(self):
        self.surf = GriddedSurface.from_points_list(POINTS)
        self.mesh = Mesh(np.array([1.]), np.array([2.]), np.array([3.]))
        self.meshA = Mesh(np.array([1., 2.]), np.array([2., 2.]),
                          np.array([3., 2.]))

    def test_get_min_distance(self):
        dists = self.surf.get_min_distance(self.mesh)
        expected = np.array([111.235389])
        np.testing.assert_allclose(dists, expected, rtol=1e-5, atol=0)

    def test_get_closest_points(self):
        self.assertRaises(NotImplementedError, self.surf.get_closest_points,
                          self.mesh)

    def test_get_joyner_boore_distance(self):
        dists = self.surf.get_joyner_boore_distance(self.mesh)
        expected = np.array([111.19493])
        np.testing.assert_allclose(dists, expected, rtol=1e-5, atol=0)

    def test_get_rx_distance(self):
        self.assertRaises(NotImplementedError, self.surf.get_rx_distance,
                          self.surf)

    def test_get_top_edge_depth(self):
        self.assertRaises(NotImplementedError, self.surf.get_top_edge_depth)

    def test_get_ry0_distance(self):
        self.assertRaises(NotImplementedError, self.surf.get_ry0_distance,
                          self.mesh)

    def test_get_strike(self):
        self.assertRaises(NotImplementedError, self.surf.get_strike)

    def test_get_dip(self):
        self.assertRaises(NotImplementedError, self.surf.get_dip)

    def test_get_width(self):
        self.assertRaises(NotImplementedError, self.surf.get_width)

    def test_get_area(self):
        self.assertRaises(NotImplementedError, self.surf.get_area)

    def test_get_bounding_box(self):
        self.assertEqual((0.0, 1.0, 1.0, 0.0), self.surf.get_bounding_box())

    def test_get_middle_point(self):
        raise unittest.SkipTest(
            'surface.get_middle_point() has to be implemented')
