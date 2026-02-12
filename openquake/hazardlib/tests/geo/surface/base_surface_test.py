# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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
from openquake.hazardlib.geo.surface.base import BaseSurface

from openquake.hazardlib.tests.geo.surface import _planar_test_data


class FakeSurface(BaseSurface):
    def __init__(self, coordinates_list):
        points = [[Point(*coordinates) for coordinates in row]
                  for row in coordinates_list]
        self.mesh = RectangularMesh.from_points_list(points)

    def get_strike(self):
        top_row = self.mesh[0:2]
        self.dip, self.strike = top_row.get_mean_inclination_and_azimuth()
        return self.strike

    def get_dip(self):
        raise NotImplementedError()

    def get_width(self):
        raise NotImplementedError()


class GetMinDistanceTestCase(unittest.TestCase):
    def test_1(self):
        surface = FakeSurface(_planar_test_data.TEST_7_RUPTURE_6_MESH)
        sites = Mesh.from_points_list([Point(0, 0)])
        self.assertAlmostEqual(8.01185807319,
                               surface.get_min_distance(sites)[0])

    def test_2(self):
        surface = FakeSurface(_planar_test_data.TEST_7_RUPTURE_6_MESH)
        sites = Mesh.from_points_list([Point(-0.25, 0.25)])
        self.assertAlmostEqual(40.09707543926,
                               surface.get_min_distance(sites)[0],
                               places=4)

    def test_3(self):
        surface = FakeSurface(_planar_test_data.TEST_7_RUPTURE_2_MESH)
        sites = Mesh.from_points_list([Point(0, 0)])
        self.assertAlmostEqual(7.01186304977,
                               surface.get_min_distance(sites)[0])

    def test_4(self):
        surface = FakeSurface(_planar_test_data.TEST_7_RUPTURE_2_MESH)
        sites = Mesh.from_points_list([Point(-0.3, 0.4)])
        self.assertAlmostEqual(55.58568426746,
                               surface.get_min_distance(sites)[0],
                               places=4)

    def test_several_sites(self):
        surface = FakeSurface(_planar_test_data.TEST_7_RUPTURE_2_MESH)
        sites = Mesh.from_points_list([Point(0, 0), Point(-0.3, 0.4)])
        dists = surface.get_min_distance(sites)
        expected_dists = [7.01186301, 55.58568427]
        numpy.testing.assert_allclose(dists, expected_dists)


class GetJoynerBooreDistanceTestCase(unittest.TestCase):
    def test_point_inside(self):
        corners = [[(-0.1, -0.1, 1), (0.1, -0.1, 1)],
                   [(-0.1, 0.1, 2), (0.1, 0.1, 2)]]
        surface = FakeSurface(corners)
        sites = Mesh.from_points_list([Point(0, 0), Point(0, 0, 20),
                                       Point(0.01, 0.03)])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [0] * 3
        numpy.testing.assert_allclose(dists, expected_dists)

    def test_point_on_the_border(self):
        corners = [[(0.1, -0.1, 1), (-0.1, -0.1, 1)],
                   [(0.1, 0.1, 2), (-0.1, 0.1, 2)]]
        surface = FakeSurface(corners)
        sites = Mesh.from_points_list([Point(-0.1, 0.04), Point(0.1, 0.03)])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [0] * 2
        numpy.testing.assert_allclose(dists, expected_dists, atol=1e-4)

    def test_point_outside(self):
        corners = [[(0.1, -0.1, 1), (-0.1, -0.1, 1)],
                   [(0.1, 0.1, 2), (-0.1, 0.1, 2)]]
        surface = FakeSurface(corners)
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
        numpy.testing.assert_allclose(dists, expected_dists, rtol=0.01)


class GetRY0DistanceTestCase(unittest.TestCase):
    def _test_rectangular_surface(self):
        corners = [[(0, 0, 8), (-0.05, 0, 8), (-0.1, 0, 8)],
                   [(0, 0, 9), (-0.05, 0, 9), (-0.1, 0, 9)]]
        surface = FakeSurface(corners)
        return surface

    def test1_site_on_the_edges(self):
        surface = self._test_rectangular_surface()
        sites = Mesh.from_points_list([Point(0.0, 0.05), Point(0.0, -0.05)])
        dists = surface.get_ry0_distance(sites)
        expected_dists = [0, 0]
        numpy.testing.assert_allclose(dists, expected_dists)

    def test2_sites_at_one_degree_distance(self):
        surface = self._test_rectangular_surface()
        sites = Mesh.from_points_list([Point(+1.0, 0.0), Point(+1.0, -1.0),
                                       Point(+1.0, 1.0), Point(-1.1, +0.0),
                                       Point(-1.1, 1.0), Point(-1.1, -1.0)])
        dists = surface.get_ry0_distance(sites)
        expected_dists = [111.19505230826488, 111.177990689, 111.177990689,
                          111.19505230826488, 111.177990689, 111.177990689]
        numpy.testing.assert_allclose(dists, expected_dists, rtol=.01)


class GetRXDistanceTestCase(unittest.TestCase):
    def _test1to7surface(self):
        corners = [[(0, 0, 8), (-0.05, 0, 8), (-0.1, 0, 8)],
                   [(0, 0, 9), (-0.05, 0, 9), (-0.1, 0, 9)]]
        surface = FakeSurface(corners)
        return surface

    def test1_site_on_the_hanging_wall(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, 0.05), Point(40.0, 0.05)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [5.559752615413244] * 2
        numpy.testing.assert_allclose(dists, expected_dists, rtol=.01)

    def test2_site_on_the_foot_wall(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, -0.05), Point(-140, -0.05)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [-5.559752615413244] * 2
        numpy.testing.assert_allclose(dists, expected_dists, rtol=.01)

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
        numpy.testing.assert_allclose(dists, expected_dists)

    def test5_site_opposite_to_strike_direction(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(-0.2, 0), Point(-67.6, 0),
                                       Point(-90.33, 0)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [0] * 3
        numpy.testing.assert_allclose(dists, expected_dists)

    def test6_one_degree_distance(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, -1), Point(20, 1)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [-111.19505230826488, +111.19505230826488]
        numpy.testing.assert_allclose(dists, expected_dists, rtol=.01)

    def test7_ten_degrees_distance(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0, -10), Point(-15, 10)])
        dists = surface.get_rx_distance(sites)
        expected_dists = [-1111.9505230826488, +1111.9505230826488]
        numpy.testing.assert_allclose(dists, expected_dists, rtol=.01)

    def test8_strike_of_255_degrees(self):
        corners = [[(0.05, 0.05, 8), (-0.05, -0.05, 8)],
                   [(0.05, 0.05, 9), (-0.05, -0.05, 9)]]
        surface = FakeSurface(corners)
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
        surface = FakeSurface(corners)

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
        surface = FakeSurface(corners)

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
        surface = FakeSurface(corners)

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
        surface = FakeSurface(corners)
        self.assertAlmostEqual(surface.get_top_edge_depth(), 3.3)

    def test_with_depth_topo(self):
        corners = [[(-0.5, -0.5, -3.3), (0.5, 0.5, -3.5)],
                   [(-0.5, -0.5, 9.3), (0.5, 0.5, 9.8)]]
        surface = FakeSurface(corners)
        self.assertAlmostEqual(surface.get_top_edge_depth(), -3.5)

    def test_one_row_no_depth(self):
        corners = [[(-0.5, -0.5), (0.5, 0.5)]]
        surface = FakeSurface(corners)
        self.assertAlmostEqual(surface.get_top_edge_depth(), 0)


class GetAreaTestCase(unittest.TestCase):
    def test_get_area(self):
        corners = [[(0.0, 0.0, 0.0), (0.0, 0.089932, 0.0)],
                   [(0.0, 0.0, 10.0), (0.0, 0.089932, 10.0)]]
        surface = FakeSurface(corners)
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
        surface = FakeSurface(corners)
        west, east, north, south = surface.get_bounding_box()
        self.assertEqual(0.0, west)
        self.assertEqual(0.3, east)
        self.assertEqual(0.2, north)
        self.assertEqual(-0.3, south)


class GetMiddlePointTestCase(unittest.TestCase):
    def test_get_middle_point(self):
        corners = [[(0.0, 0.0, 0.0), (0.0, 0.089932, 0.0)],
                   [(0.0, 0.0, 10.0), (0.0, 0.089932, 10.0)]]
        surface = FakeSurface(corners)
        self.assertTrue(
            Point(0.0, 0.044966, 5.0) == surface.get_middle_point()
        )


class GetAzimuthTestCase(unittest.TestCase):
    def test_01(self):
        corners = [[(0.0, 0.0, 0.0), (0.0, 0.1, 0.0)],
                   [(0.0, 0.0, 10.0), (0.0, 0.1, 10.0)]]
        surface = FakeSurface(corners)
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
        surface = FakeSurface(corners)
        mesh = Mesh.from_points_list([Point(0.0, 0.2),
                                      Point(0.0, -0.2),
                                      Point(-0.1, 0.1)])
        azimuths = surface.get_azimuth(mesh)
        expected = numpy.array([270., 90., 225.])
        numpy.testing.assert_almost_equal(expected, azimuths, 2)


class GetAzimuthClosestPointTestCase(unittest.TestCase):

    def test_01(self):
        corners = [[(0.0, 0.0, 0.0), (0.0, 0.1, 0.0)],
                   [(0.0, 0.0, 10.0), (0.0, 0.1, 10.0)]]
        surface = FakeSurface(corners)
        mesh = Mesh.from_points_list([Point(0.0, 0.2),
                                      Point(0.1, 0.1),
                                      Point(0.0, -0.2)])
        azimuths = surface.get_azimuth_of_closest_point(mesh)
        expected = numpy.array([180, -90, 0])
        azimuths[azimuths > 180] = azimuths[azimuths > 180] - 360
        numpy.testing.assert_almost_equal(expected, azimuths, 1)


class GetSurfaceTraceTestCase(unittest.TestCase):
    """Tests for _get_top_rupture_trace()."""

    def test_simple_fault_returns_top_row(self):
        """SimpleFaultSurface: trace should be mesh row 0."""
        trace = Line([Point(0.0, 0.0), Point(0.0, 0.1), Point(0.0, 0.2)])
        surface = SimpleFaultSurface.from_fault_data(
            trace, upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0, dip=90.0,
            mesh_spacing=0.5
        )
        result = surface._get_top_rupture_trace()
        # Must be 2D with shape (N, 2)
        self.assertEqual(result.ndim, 2)
        self.assertEqual(result.shape[1], 2)
        # Must have at least 2 points
        self.assertGreaterEqual(result.shape[0], 2)
        # Top edge depths should be ~0 (we got lons/lats from row 0)
        top_depths = surface.mesh[0:1].depths[0, :]
        numpy.testing.assert_allclose(top_depths, 0.0, atol=0.01)

    def test_get_top_rupture_trace(self):
        """Test _get_top_rupture_trace() with a given fault trace and surface plan.

        Surface is a 2-column × 2-row rectangular mesh:
            Top edge:    (0.0, 0.0, 0.0) → (0.1, 0.0, 0.0)
            Bottom edge: (0.0, 0.0, 10.0) → (0.1, 0.0, 10.0)

        The trace is the top row, so exactly 2 points:
            point 0: lon=0.0, lat=0.0
            point 1: lon=0.1, lat=0.0
        """
        corners = [[(0.0, 0.0, 0.0), (0.1, 0.0, 0.0)],
                   [(0.0, 0.0, 10.0), (0.1, 0.0, 10.0)]]
        surface = FakeSurface(corners)

        trace = surface._get_top_rupture_trace()

        # Exact shape: 2 top-edge points, 2 columns (lon, lat)
        self.assertEqual(trace.shape, (2, 2))

        # Expected full trace
        expected_lons = numpy.array([0.0, 0.1])
        expected_lats = numpy.array([0.0, 0.0])

        numpy.testing.assert_array_almost_equal(trace[:, 0], expected_lons)
        numpy.testing.assert_array_almost_equal(trace[:, 1], expected_lats)

    def test_get_top_rupture_trace_realistic_fault(self):
        """Test _get_top_rupture_trace() with a fault geometry.
        """
        # Fault trace running ~NW-SE for about 30 km:
        #   Point A: (13.30, 42.40)
        #   Point B: (13.45, 42.30)
        #   Point C: (13.60, 42.20)
        corners = [
            [(13.30, 42.40, 2.0), (13.45, 42.30, 2.0),
             (13.60, 42.20, 2.0)],
            [(13.293, 42.393, 15.0), (13.443, 42.293, 15.0),
             (13.593, 42.193, 15.0)],
        ]
        surface = FakeSurface(corners)

        trace = surface._get_top_rupture_trace()

        self.assertEqual(trace.ndim, 2)
        self.assertEqual(trace.shape[1], 2)
        self.assertEqual(trace.shape[0], 3)
        self.assertTrue(numpy.all(numpy.isfinite(trace)))

        # Expected top-edge longitudes and latitudes
        expected_lons = numpy.array([13.30, 13.45, 13.60])
        expected_lats = numpy.array([42.40, 42.30, 42.20])

        numpy.testing.assert_array_almost_equal(
            trace[:, 0], expected_lons, decimal=5)
        numpy.testing.assert_array_almost_equal(
            trace[:, 1], expected_lats, decimal=5)

        lon_range = trace[-1, 0] - trace[0, 0]
        lat_range = trace[0, 1] - trace[-1, 1]
        self.assertAlmostEqual(lon_range, 0.30, places=2)
        self.assertAlmostEqual(lat_range, 0.20, places=2)


class GetXLRatioTestCase(unittest.TestCase):
    """Tests for get_x_l_ratio()."""

    def _make_simple_surface(self, lon_start=0.0, lon_end=0.0,
                              lat_start=0.0, lat_end=1.0):
        """Helper: create a simple vertical fault surface."""
        trace = Line([Point(lon_start, lat_start),
                      Point(lon_end, lat_end)])
        return SimpleFaultSurface.from_fault_data(
            trace, upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0, dip=90.0,
            mesh_spacing=0.5
        )

    def test_norcia_fault_site_near_se_end(self):
        """x/L for a site near the SE end of the Norcia MVFS fault.

        Geodetic computation:
            Cumulative distance to site projection ≈ 32.5 km
            x/L (from NW start, OQ convention) ≈ 0.96
            x/L (from nearest end, PFDHA convention) ≈ 0.04
        """
        # Norcia MVFS fault trace
        trace = Line([
            Point(13.1015, 43.0131),
            Point(13.1332, 42.9931),
            Point(13.1523, 42.9766),
            Point(13.1685, 42.9544),
            Point(13.1627, 42.9394),
            Point(13.1750, 42.9201),
            Point(13.1970, 42.9097),
            Point(13.2264, 42.8846),
            Point(13.2476, 42.8449),
            Point(13.2482, 42.8211),
            Point(13.2616, 42.8094),
            Point(13.2725, 42.7865),
            Point(13.2813, 42.7550),
        ])
        surface = SimpleFaultSurface.from_fault_data(
            trace, upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=11.0, dip=47.0,
            mesh_spacing=1.0
        )

        # Site near the SE end of the fault
        site_mesh = Mesh(
            numpy.array([13.278]),
            numpy.array([42.767]),
            depths=None
        )
        x_over_L, L_km = surface.get_x_l_ratio(site_mesh)
        self.assertAlmostEqual(float(x_over_L[0]), 0.96, delta=0.02)

        # PFDHA convention: x/L = min(x/L, 1 - x/L) ≈ 0.04
        x_l_pfdha = min(float(x_over_L[0]), 1.0 - float(x_over_L[0]))
        self.assertAlmostEqual(x_l_pfdha, 0.05, delta=0.02)

        # Total trace length ≈ 33.9 km
        self.assertAlmostEqual(L_km, 33.9, delta=0.2)