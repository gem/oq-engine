# nhlib: A New Hazard Library
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

from nhlib.geo.point import Point
from nhlib.geo.mesh import RectangularMesh
from nhlib.geo.surface.base import BaseSurface

from tests.geo.surface import _planar_test_data as test_data


class DummySurface(BaseSurface):
    def __init__(self, coordinates_list):
        self.coordinates_list = coordinates_list
        super(DummySurface, self).__init__()
    def _create_mesh(self):
        points = [[Point(*coordinates) for coordinates in row]
                  for row in self.coordinates_list]
        return RectangularMesh.from_points_list(points)
    def get_strike(self):
        top_edge = list(self.get_mesh()[0:1])
        return top_edge[1].azimuth(top_edge[0])
    def get_dip(self):
        raise NotImplementedError()


class GetMinDistanceTestCase(unittest.TestCase):
    def test_1(self):
        surface = DummySurface(test_data.TEST_7_RUPTURE_6_MESH)
        self.assertAlmostEqual(8.01185807319,
                               surface.get_min_distance(Point(0, 0)))

    def test_2(self):
        surface = DummySurface(test_data.TEST_7_RUPTURE_6_MESH)
        self.assertAlmostEqual(40.1213468,
                               surface.get_min_distance(Point(-0.25, 0.25)),
                               places=6)

    def test_3(self):
        surface = DummySurface(test_data.TEST_7_RUPTURE_2_MESH)
        self.assertAlmostEqual(7.01186304977,
                               surface.get_min_distance(Point(0, 0)))

    def test_4(self):
        surface = DummySurface(test_data.TEST_7_RUPTURE_2_MESH)
        self.assertAlmostEqual(55.6159556,
                               surface.get_min_distance(Point(-0.3, 0.4)),
                               places=5)


class GetJoynerBooreDistanceTestCase(unittest.TestCase):
    def test_point_inside(self):
        corners = [[(-1, -1, 1), (1, -1, 1)],
                   [(-1, 1, 2), (1, 1, 2)]]
        surface = DummySurface(corners)
        self.assertEqual(surface.get_joyner_boore_distance(Point(0, 0)), 0)
        self.assertEqual(surface.get_joyner_boore_distance(Point(0, 0, 20)), 0)
        self.assertEqual(surface.get_joyner_boore_distance(Point(0.1, 0.3)), 0)

    def test_point_on_the_border(self):
        corners = [[(0.1, -0.1, 1), (-0.1, -0.1, 1)],
                   [(0.1, 0.1, 2), (-0.1, 0.1, 2)]]
        surface = DummySurface(corners)
        aae = self.assertAlmostEqual
        aae(surface.get_joyner_boore_distance(Point(-0.1, 0.04)), 0, delta=0.3)
        aae(surface.get_joyner_boore_distance(Point(0.1, 0.03)), 0, delta=0.3)

    def test_point_outside(self):
        corners = [[(0.1, -0.1, 1), (-0.1, -0.1, 1)],
                   [(0.1, 0.1, 2), (-0.1, 0.1, 2)]]
        surface = DummySurface(corners)
        aae = self.assertAlmostEqual
        aae(surface.get_joyner_boore_distance(Point(-0.2, -0.2)),
            Point(-0.2, -0.2).distance(Point(-0.1, -0.1)), delta=0.2)
        aae(surface.get_joyner_boore_distance(Point(1, 1, 1)),
            Point(1, 1).distance(Point(0.1, 0.1)), delta=0.4)
        aae(surface.get_joyner_boore_distance(Point(4, 5)),
            Point(4, 5).distance(Point(0.1, 0.1)), delta=0.3)
        aae(surface.get_joyner_boore_distance(Point(8, 10.4)),
            Point(8, 10.4).distance(Point(0.1, 0.1)), delta=0.3)


class GetRXDistanceTestCase(unittest.TestCase):
    def _test1to7surface(self):
        corners = [[(0, 0, 8), (-0.1, 0, 8)],
                   [(0, 0, 9), (-0.1, 0, 9)]]
        surface = DummySurface(corners)
        return surface

    def test1_site_on_the_footwall(self):
        surface = self._test1to7surface()
        self.assertAlmostEqual(surface.get_rx_distance(Point(0.05, 0.05)),
                               -5.559752615413244, places=3)

    def test2_site_on_the_hanging_wall(self):
        surface = self._test1to7surface()
        self.assertAlmostEqual(surface.get_rx_distance(Point(0.05, -0.05)),
                               5.559752615413244, places=3)

    def test3_site_on_centroid(self):
        surface = self._test1to7surface()
        self.assertAlmostEqual(surface.get_rx_distance(Point(0.05, 0)),
                               0, places=3)

    def test4_site_along_strike(self):
        surface = self._test1to7surface()
        self.assertAlmostEqual(surface.get_rx_distance(Point(0.2, 0)),
                               0, places=3)

    def test5_site_opposite_to_strike_direction(self):
        surface = self._test1to7surface()
        self.assertAlmostEqual(surface.get_rx_distance(Point(-0.2, 0)),
                               0, places=3)

    def test6_one_degree_distance(self):
        surface = self._test1to7surface()
        self.assertAlmostEqual(surface.get_rx_distance(Point(0.05, -1)),
                               111.19505230826488, places=3)

    def test7_ten_degrees_distance(self):
        surface = self._test1to7surface()
        self.assertAlmostEqual(surface.get_rx_distance(Point(0.05, -10)),
                               1111.9505230826487, places=2)

    def test8_strike_of_45_degrees(self):
        corners = [[(0.05, 0.05, 8), (-0.05, -0.05, 8)],
                   [(0.05, 0.05, 9), (-0.05, -0.05, 9)]]
        surface = DummySurface(corners)
        self.assertAlmostEqual(surface.get_rx_distance(Point(0.05, 0)),
                               3.9313415355436705, places=3)


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
