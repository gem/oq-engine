# The Hazard Library
# Copyright (C) 2014-2021 GEM Foundation
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

POINTS = [Point(0, 0, 0.1), Point(0, 1, 0), Point(1, 1, 0.1),
          Point(1, 0, 0.1)]

POINTS2 = [Point(0, 0, 5), Point(0, 1, 8), Point(1, 1, 9),
          Point(1, 0, 9)]

POINTSIDL = [Point(179.5, 0, 0.1), Point(179.5, 1, 0), Point(-179.5, 1, 0.1),
             Point(-179.5, 0, 0.1)]


class GriddedSurfaceTestCase(unittest.TestCase):

    def setUp(self):
        self.surf = GriddedSurface.from_points_list(POINTS)
        self.mesh = Mesh(np.array([1.]), np.array([2.]), np.array([3.]))
        self.surf2 = GriddedSurface.from_points_list(POINTS2)

    def test_get_min_distance(self):
        dists = self.surf.get_min_distance(self.mesh)
        expected = np.array([111.204])
        np.testing.assert_allclose(dists, expected, rtol=1e-5, atol=0)

    def test_get_closest_points(self):
        res = self.surf.get_closest_points(self.mesh)
        self.assertEqual(res.lons, [1.0])
        self.assertEqual(res.lats, [1.0])
        self.assertEqual(res.depths, [0.1])

    def test_get_joyner_boore_distance(self):
        dists = self.surf.get_joyner_boore_distance(self.mesh)
        expected = np.array([111.1935])
        np.testing.assert_allclose(dists, expected, rtol=1e-5, atol=0)

    def test_get_rx_distance(self):
        self.assertRaises(NotImplementedError, self.surf.get_rx_distance,
                          self.surf)

    def test_get_top_edge_depth(self):
        depth = self.surf.get_top_edge_depth()
        self.assertEqual(depth, 0)

    def test_get_top_edge_depth_nonzero(self):
        depth = self.surf2.get_top_edge_depth()
        self.assertEqual(depth, 5)

    def test_get_ry0_distance(self):
        self.assertRaises(NotImplementedError, self.surf.get_ry0_distance,
                          self.mesh)

    def test_get_strike(self):
        np.testing.assert_equal(np.nan, self.surf.get_strike())

    def test_get_dip(self):
        np.testing.assert_equal(np.nan, self.surf.get_dip())

    def test_get_width(self):
        self.assertRaises(NotImplementedError, self.surf.get_width)

    def test_get_area(self):
        self.assertRaises(NotImplementedError, self.surf.get_area)

    def test_get_bounding_box(self):
        self.assertEqual((0.0, 1.0, 1.0, 0.0), self.surf.get_bounding_box())

    def test_get_middle_point(self):
        point = self.surf.get_middle_point()
        self.assertEqual(point.x, 0)
        self.assertEqual(point.y, 0)
        self.assertEqual(point.z, 0.1)


# FIXME: this test is nearly useless, since the bugs are in the SourceFilter,
# not in surface.get_closest_points
class GriddedSurfaceTestCaseIDL(unittest.TestCase):

    def setUp(self):
        self.surf = GriddedSurface.from_points_list(POINTSIDL)
        self.mesh = Mesh(np.array([-179.5]), np.array([2.]), np.array([3.]))

    def test_get_min_distance(self):
        dists = self.surf.get_min_distance(self.mesh)
        expected = np.array([111.204])
        np.testing.assert_allclose(dists, expected, rtol=1e-5, atol=0)

    def test_get_closest_points(self):
        res = self.surf.get_closest_points(self.mesh)
        self.assertEqual(res.lons, [-179.5])
        self.assertEqual(res.lats, [1.0])
        self.assertEqual(res.depths, [0.1])

    def test_get_joyner_boore_distance(self):
        dists = self.surf.get_joyner_boore_distance(self.mesh)
        expected = np.array([111.1935])
        np.testing.assert_allclose(dists, expected, rtol=1e-5, atol=0)

    def test_get_bounding_box(self):
        self.assertEqual((179.5, -179.5, 1., 0.), self.surf.get_bounding_box())

    def test_surface_boundaries_3d(self):
        xs, ys, zs = self.surf.get_surface_boundaries_3d()
        self.assertEqual(xs, (179.5, -179.5, -179.5, 179.5, 179.5))
        self.assertEqual(ys, (0.0, 0.0, 1.0, 1.0, 0.0))
        self.assertEqual(zs, (0, 0, 0, 0, 0))

    def test_get_middle_point(self):
        point = self.surf.get_middle_point()
        self.assertEqual(point.x, 179.5)
        self.assertEqual(point.y, 0)
        self.assertEqual(point.z, 0.1)
