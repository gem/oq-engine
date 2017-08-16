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

import numpy

from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface
from openquake.hazardlib.geo.surface.base import BaseQuadrilateralSurface

from openquake.hazardlib.tests.geo.surface import _planar_test_data


class DummySurface(BaseQuadrilateralSurface):
    def __init__(self, coordinates_list):
        self.coordinates_list = coordinates_list
        super(DummySurface, self).__init__()

    def _create_mesh(self):
        points = [[Point(*coordinates) for coordinates in row]
                  for row in self.coordinates_list]
        return RectangularMesh.from_points_list(points)

    def get_strike(self):
        top_row = self.get_mesh()[0:2]
        self.dip, self.strike = top_row.get_mean_inclination_and_azimuth()
        return self.strike

    def get_dip(self):
        raise NotImplementedError()

    def get_width(self):
        raise NotImplementedError()


class GetMinDistanceTestCase(unittest.TestCase):
    def test_1(self):
        surface = DummySurface(_planar_test_data.TEST_7_RUPTURE_6_MESH)
        sites = Mesh.from_points_list([Point(0, 0)])
        self.assertAlmostEqual(8.01185807319,
                               surface.get_min_distance(sites)[0])

    def test_2(self):
        surface = DummySurface(_planar_test_data.TEST_7_RUPTURE_6_MESH)
        sites = Mesh.from_points_list([Point(-0.25, 0.25)])
        self.assertAlmostEqual(40.1213468,
                               surface.get_min_distance(sites)[0],
                               places=4)

    def test_3(self):
        surface = DummySurface(_planar_test_data.TEST_7_RUPTURE_2_MESH)
        sites = Mesh.from_points_list([Point(0, 0)])
        self.assertAlmostEqual(7.01186304977,
                               surface.get_min_distance(sites)[0])

    def test_4(self):
        surface = DummySurface(_planar_test_data.TEST_7_RUPTURE_2_MESH)
        sites = Mesh.from_points_list([Point(-0.3, 0.4)])
        self.assertAlmostEqual(55.6159556,
                               surface.get_min_distance(sites)[0],
                               places=4)

    def test_several_sites(self):
        surface = DummySurface(_planar_test_data.TEST_7_RUPTURE_2_MESH)
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


class GetRY0DistanceTestCase(unittest.TestCase):
    def _test_rectangular_surface(self):
        corners = [[(0, 0, 8), (-0.05, 0, 8), (-0.1, 0, 8)],
                   [(0, 0, 9), (-0.05, 0, 9), (-0.1, 0, 9)]]
        surface = DummySurface(corners)
        return surface

    def test1_site_on_the_edges(self):
        surface = self._test_rectangular_surface()
        sites = Mesh.from_points_list([Point(0.0, 0.05), Point(0.0, -0.05)])
        dists = surface.get_ry0_distance(sites)
        expected_dists = [0.0]
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test2_sites_at_one_degree_distance(self):
        surface = self._test_rectangular_surface()
        sites = Mesh.from_points_list([Point(+1.0, 0.0), Point(+1.0, -1.0),
                                       Point(+1.0, 1.0), Point(-1.1, +0.0),
                                       Point(-1.1, 1.0), Point(-1.1, -1.0)])
        dists = surface.get_ry0_distance(sites)
        expected_dists = [111.19505230826488, 111.177990689, 111.177990689,
                          111.19505230826488, 111.177990689, 111.177990689]
        self.assertTrue(numpy.allclose(dists, expected_dists))


class GetRXDistanceTestCase(unittest.TestCase):
    def _test1to7surface(self):
        corners = [[(0, 0, 8), (-0.05, 0, 8), (-0.1, 0, 8)],
                   [(0, 0, 9), (-0.05, 0, 9), (-0.1, 0, 9)]]
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

    def test9_non_planar_surface_case1(self):
        # vertical, non-planar surface made of two segments, both of 40 km
        # length. The first segment has an azimuth of 80 degrees while the
        # second has an azimuth of 30 degrees. The surface presents therefore
        # a kink pointing towards south-east
        corners = [
            [(0., 0., 0.), (0.354264, 0.062466, 0), (0.534131, 0.373999, 0)],
            [(0., 0., 10.), (0.354264, 0.062466, 10), (0.534131, 0.373999, 10)]
        ]
        surface = DummySurface(corners)

        # distances are tested on 4 points. The first two are on the hanging-
        # wall and foot-wall of the first segment (10 km distance), while
        # the third and fourth are on the hanging-wall and foot-wall of the
        # second segment (20 km distance)
        sites = Mesh.from_points_list([
            Point(0.192748, -0.057333), Point(0.161515, 0.119799),
            Point(0.599964, 0.128300), Point(0.288427, 0.308164)
        ])
        numpy.testing.assert_allclose(
            surface.get_rx_distance(sites),
            [10., -10., 20., -20], rtol=1e-5
        )

    def test10_non_planar_surface_case2(self):
        # vertical, non-planar surface made of two segments, both of 40 km
        # length. The first segment has an azimuth of 30 degrees while the
        # second has an azimuth of 80 degrees. The surface presents therefore
        # a kink pointing towards north-west
        corners = [
            [(0., 0., 0.), (0.179866, 0.311534, 0), (0.534137, 0.373994, 0)],
            [(0., 0., 10.), (0.179866, 0.311534, 10), (0.534137, 0.373994, 10)]
        ]
        surface = DummySurface(corners)

        # distances are tested on 4 points. The first two are on the hanging-
        # wall and foot-wall of the first segment (10 km distance), while
        # the third and fourth are on the hanging-wall and foot-wall of the
        # second segment (20 km distance)
        sites = Mesh.from_points_list([
            Point(0.167816, 0.110801), Point(0.012048, 0.200733),
            Point(0.388234, 0.165633), Point(0.325767, 0.519897)
        ])
        numpy.testing.assert_allclose(
            surface.get_rx_distance(sites),
            [10., -10., 20., -20], rtol=1e-5
        )

    def test11_non_planar_surface_case3(self):
        # same geometry as 'test10_non_planar_surface_case2' but with reversed
        # strike (edges specified in the opposite direction)
        corners = [
            [(0.534137, 0.373994, 0), (0.179866, 0.311534, 0), (0., 0., 0.)],
            [(0.534137, 0.373994, 10), (0.179866, 0.311534, 10), (0., 0., 10.)]
        ]
        surface = DummySurface(corners)

        # distances are tested on 4 points. The first two are on the foot-
        # wall and hanging-wall of the first segment (10 km distance), while
        # the third and fourth are on the foot-wall and hanging-wall of the
        # second segment (20 km distance)
        sites = Mesh.from_points_list([
            Point(0.167816, 0.110801), Point(0.012048, 0.200733),
            Point(0.388234, 0.165633), Point(0.325767, 0.519897)
        ])
        # distances remain the same, but signs are reversed
        numpy.testing.assert_allclose(
            surface.get_rx_distance(sites),
            [-10., 10., -20., 20], rtol=1e-5
        )


class GetTopEdgeDepthTestCase(unittest.TestCase):
    def test_with_depth(self):
        corners = [[(-0.5, -0.5, 3.3), (0.5, 0.5, 3.5)],
                   [(-0.5, -0.5, 9.3), (0.5, 0.5, 9.8)]]
        surface = DummySurface(corners)
        self.assertAlmostEqual(surface.get_top_edge_depth(), 3.3)

    def test_with_depth_topo(self):
        corners = [[(-0.5, -0.5, -3.3), (0.5, 0.5, -3.5)],
                   [(-0.5, -0.5, 9.3), (0.5, 0.5, 9.8)]]
        surface = DummySurface(corners)
        self.assertAlmostEqual(surface.get_top_edge_depth(), -3.5)

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


class GetResampledTopEdge(unittest.TestCase):
    def test_get_resampled_top_edge(self):
        upper_seismogenic_depth = 0.
        lower_seismogenic_depth = 40.
        dip = 90.

        mesh_spacing = 10.
        fault_trace = Line([Point(0.0, 0.0), Point(0.5, 0.5), Point(1.0, 1.0)])

        whole_fault_surface = SimpleFaultSurface.from_fault_data(
            fault_trace, upper_seismogenic_depth,
            lower_seismogenic_depth, dip, mesh_spacing
        )

        ref = Line([Point(0., 0.), Point(1.0, 1.0)])
        result = whole_fault_surface.get_resampled_top_edge()
        for ref_point, result_point in zip(ref.points, result.points):

            self.assertAlmostEqual(ref_point.longitude,
                                   result_point.longitude, delta=0.1)
            self.assertAlmostEqual(ref_point.latitude,
                                   result_point.latitude, delta=0.1)
            self.assertAlmostEqual(ref_point.depth,
                                   result_point.depth, delta=0.1)

    def test_get_resampled_top_edge_non_planar(self):
        upper_seismogenic_depth = 0.
        lower_seismogenic_depth = 40.
        dip = 90.

        mesh_spacing = 10.
        fault_trace = Line([Point(0.0, 0.0), Point(0.5, 0.5), Point(1.5, 1.0)])

        whole_fault_surface = SimpleFaultSurface.from_fault_data(
            fault_trace, upper_seismogenic_depth,
            lower_seismogenic_depth, dip, mesh_spacing
        )

        ref = Line([Point(0., 0.), Point(0.5, 0.5), Point(1.5, 1.0)])
        result = whole_fault_surface.get_resampled_top_edge()
        for ref_point, result_point in zip(ref.points, result.points):

            self.assertAlmostEqual(ref_point.longitude,
                                   result_point.longitude, delta=0.1)
            self.assertAlmostEqual(ref_point.latitude,
                                   result_point.latitude, delta=0.1)
            self.assertAlmostEqual(ref_point.depth,
                                   result_point.depth, delta=0.1)


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


class GetAzimuthTestCase(unittest.TestCase):
    def test_01(self):
        corners = [[(0.0, 0.0, 0.0), (0.0, 0.1, 0.0)],
                   [(0.0, 0.0, 10.0), (0.0, 0.1, 10.0)]]
        surface = DummySurface(corners)
        mesh = Mesh.from_points_list([Point(0.0, 0.2),
                                      Point(0.1, 0.05),
                                      Point(0.0, -0.2)])
        azimuths = surface.get_azimuth(mesh)
        expected = numpy.array([0, 90, 180])
        azimuths[azimuths > 180] = azimuths[azimuths > 180] - 360
        numpy.testing.assert_almost_equal(expected, azimuths, 1)

    def test_02(self):
        corners = [[(-1.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                   [(-1.0, 0.0, 10.0), (1.0, 0.0, 10.0)]]
        surface = DummySurface(corners)
        mesh = Mesh.from_points_list([Point(0.0, 0.2),
                                      Point(0.0, -0.2),
                                      Point(-0.1, 0.1)])
        azimuths = surface.get_azimuth(mesh)
        expected = numpy.array([270., 90., 225.])
        numpy.testing.assert_almost_equal(expected, azimuths, 2)
