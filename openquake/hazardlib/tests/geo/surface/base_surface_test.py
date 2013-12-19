# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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

import numpy

from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.geo.surface.base import BaseQuadrilateralSurface

from openquake.hazardlib.tests.geo.surface import _planar_test_data as test_data


class DummySurface(BaseQuadrilateralSurface):
    def __init__(self, coordinates_list):
        self.coordinates_list = coordinates_list
        super(DummySurface, self).__init__()

    def _create_mesh(self):
        points = [[Point(*coordinates) for coordinates in row]
                  for row in self.coordinates_list]
        return RectangularMesh.from_points_list(points)

    def get_strike(self):
        raise NotImplementedError()

    def get_dip(self):
        raise NotImplementedError()

    def get_width(self):
        raise NotImplementedError()


class GetMinDistanceTestCase(unittest.TestCase):
    def test_1(self):
        surface = DummySurface(test_data.TEST_7_RUPTURE_6_MESH)
        sites = Mesh.from_points_list([Point(0, 0)])
        self.assertAlmostEqual(8.01185807319,
                               surface.get_min_distance(sites)[0])

    def test_2(self):
        surface = DummySurface(test_data.TEST_7_RUPTURE_6_MESH)
        sites = Mesh.from_points_list([Point(-0.25, 0.25)])
        self.assertAlmostEqual(40.1213468,
                               surface.get_min_distance(sites)[0],
                               places=4)

    def test_3(self):
        surface = DummySurface(test_data.TEST_7_RUPTURE_2_MESH)
        sites = Mesh.from_points_list([Point(0, 0)])
        self.assertAlmostEqual(7.01186304977,
                               surface.get_min_distance(sites)[0])

    def test_4(self):
        surface = DummySurface(test_data.TEST_7_RUPTURE_2_MESH)
        sites = Mesh.from_points_list([Point(-0.3, 0.4)])
        self.assertAlmostEqual(55.6159556,
                               surface.get_min_distance(sites)[0],
                               places=4)

    def test_several_sites(self):
        surface = DummySurface(test_data.TEST_7_RUPTURE_2_MESH)
        sites = Mesh.from_points_list([Point(0, 0), Point(-0.3, 0.4)])
        dists = surface.get_min_distance(sites)
        expected_dists = [7.01186304977, 55.6159556]
        self.assertTrue(numpy.allclose(dists, expected_dists))


class GetJoynerBooreDistanceTestCase(unittest.TestCase):
    def test_point_inside(self):
        corners = [[(-0.1, -0.1, 1), (0.1, -0.1, 1)],
                   [(-0.1, 0.1, 2), (0.1, 0.1, 2)]]
        surface = DummySurface(corners)
        sites = Mesh.from_points_list([Point(0, 0), Point(0, 0, 20),
                                       Point(0.01, 0.03)])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [0] * 3
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test_point_on_the_border(self):
        corners = [[(0.1, -0.1, 1), (-0.1, -0.1, 1)],
                   [(0.1, 0.1, 2), (-0.1, 0.1, 2)]]
        surface = DummySurface(corners)
        sites = Mesh.from_points_list([Point(-0.1, 0.04), Point(0.1, 0.03)])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [0] * 2
        self.assertTrue(numpy.allclose(dists, expected_dists, atol=1e-4))

    def test_point_outside(self):
        corners = [[(0.1, -0.1, 1), (-0.1, -0.1, 1)],
                   [(0.1, 0.1, 2), (-0.1, 0.1, 2)]]
        surface = DummySurface(corners)
        sites = Mesh.from_points_list([Point(-0.2, -0.2), Point(1, 1, 1),
                                       Point(4, 5), Point(8, 10.4),
                                       Point(0.05, 0.15, 10)])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [
            Point(-0.2, -0.2).distance(Point(-0.1, -0.1)),
            Point(1, 1).distance(Point(0.1, 0.1)),
            Point(4, 5).distance(Point(0.1, 0.1)),
            Point(8, 10.4).distance(Point(0.1, 0.1)),
            Point(0.05, 0.15).distance(Point(0.05, 0.1))
        ]
        self.assertTrue(numpy.allclose(dists, expected_dists, atol=0.2))


class GetRXDistanceTestCase(unittest.TestCase):
    def _test1to7surface(self):
        corners = [[(0, 0, 8), (-0.1, 0, 8)],
                   [(0, 0, 9), (-0.1, 0, 9)]]
        surface = DummySurface(corners)
        return surface

    def test1_site_on_the_hanging_wall(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, 0.05), Point(40.0, 0.05)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [5.559752615413244] * 2
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test2_site_on_the_foot_wall(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, -0.05), Point(-140, -0.05)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [-5.559752615413244] * 2
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test3_site_on_centroid(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, 0)])
        self.assertAlmostEqual(surface.get_rx_distance(sites)[0], 0)

    def test4_site_along_strike(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.2, 0), Point(67.6, 0),
                                       Point(90.33, 0)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [0] * 3
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test5_site_opposite_to_strike_direction(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(-0.2, 0), Point(-67.6, 0),
                                       Point(-90.33, 0)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [0] * 3
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test6_one_degree_distance(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, -1), Point(20, 1)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [-111.19505230826488, +111.19505230826488]
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test7_ten_degrees_distance(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0, -10), Point(-15, 10)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [-1111.9505230826488, +1111.9505230826488]
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test8_strike_of_255_degrees(self):
        corners = [[(0.05, 0.05, 8), (-0.05, -0.05, 8)],
                   [(0.05, 0.05, 9), (-0.05, -0.05, 9)]]
        surface = DummySurface(corners)
        sites = Mesh.from_points_list([Point(0.05, 0)])
        self.assertAlmostEqual(surface.get_rx_distance(sites)[0],
                               -3.9313415355436705, places=4)


class GetTopEdgeDepthTestCase(unittest.TestCase):
    def test_with_depth(self):
        corners = [[(-0.5, -0.5, 3.3), (0.5, 0.5, 3.5)],
                   [(-0.5, -0.5, 9.3), (0.5, 0.5, 9.8)]]
        surface = DummySurface(corners)
        self.assertAlmostEqual(surface.get_top_edge_depth(), 3.3)

    def test_one_row_no_depth(self):
        corners = [[(-0.5, -0.5), (0.5, 0.5)]]
        surface = DummySurface(corners)
        self.assertAlmostEqual(surface.get_top_edge_depth(), 0)


class GetAreaTestCase(unittest.TestCase):
    def test_get_area(self):
        corners = [[(0.0, 0.0, 0.0), (0.0, 0.089932, 0.0)],
                   [(0.0, 0.0, 10.0), (0.0, 0.089932, 10.0)]]
        surface = DummySurface(corners)
        self.assertAlmostEqual(100.0, surface.get_area(), places=0)


class GetBoundingBoxTestCase(unittest.TestCase):
    def test_get_bounding_box(self):
        corners = [[(0.0, 0.0, 0.0), (0.1, 0.2, 0.0)],
                   [(0.05, -0.3, 10.0), (0.3, 0.05, 10.0)]]
        surface = DummySurface(corners)
        west, east, north, south = surface.get_bounding_box()
        self.assertEqual(0.0, west)
        self.assertEqual(0.3, east)
        self.assertEqual(0.2, north)
        self.assertEqual(-0.3, south)


class GetMiddlePointTestCase(unittest.TestCase):
    def test_get_middle_point(self):
        corners = [[(0.0, 0.0, 0.0), (0.0, 0.089932, 0.0)],
                   [(0.0, 0.0, 10.0), (0.0, 0.089932, 10.0)]]
        surface = DummySurface(corners)
        self.assertTrue(
            Point(0.0, 0.044966, 5.0) == surface.get_middle_point()
        )
