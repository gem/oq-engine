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

from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo import utils as geo_utils
from openquake.hazardlib.geo.surface.planar import PlanarSurface

from openquake.hazardlib.tests.geo.surface \
    import _planar_test_data as test_data
from openquake.hazardlib.tests.geo.surface import _utils as utils

assert_aeq = numpy.testing.assert_almost_equal


class PlanarSurfaceCreationTestCase(unittest.TestCase):
    def assert_failed_creation(self, mesh_spacing, strike, dip, corners,
                               exc, msg):
        with self.assertRaises(exc) as ae:
            PlanarSurface(mesh_spacing, strike, dip, *corners)
        self.assertEqual(str(ae.exception), msg)

    def test_top_edge_depth_differs(self):
        corners = [Point(0, -1, 0.3), Point(0, 1, 0.30001),
                   Point(0, 1, 0.5), Point(0, -1, 0.5)]
        msg = 'top and bottom edges must be parallel to the earth surface'
        self.assert_failed_creation(1, 0, 90, corners, ValueError, msg)

    def test_bottom_edge_depth_differs(self):
        corners = [Point(0, -1, 0.3), Point(0, 1, 0.3),
                   Point(0, 1, 0.5), Point(0, -1, 0.499999)]
        msg = 'top and bottom edges must be parallel to the earth surface'
        self.assert_failed_creation(1, 0, 90, corners, ValueError, msg)

    def test_twisted_surface(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, -1, 2), Point(0, 1, 2)]
        msg = 'corners are in the wrong order'
        self.assert_failed_creation(1, 0, 90, corners, ValueError, msg)

    def test_corners_not_on_the_same_plane(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(-0.3, 1, 2), Point(0.3, -1, 2)]
        msg = 'corner points do not lie on the same plane'
        self.assert_failed_creation(1, 0, 90, corners, ValueError, msg)

    def test_top_edge_shorter_than_bottom_edge(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, 1.2, 2), Point(0, -1.2, 2)]
        msg = 'top and bottom edges have different lengths'
        self.assert_failed_creation(1, 0, 90, corners, ValueError, msg)

    def test_non_positive_mesh_spacing(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, 1, 2), Point(0, -1, 2)]
        msg = 'mesh spacing must be positive'
        self.assert_failed_creation(0, 0, 90, corners, ValueError, msg)
        self.assert_failed_creation(-1, 0, 90, corners, ValueError, msg)

    def test_strike_out_of_range(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, 1, 2), Point(0, -1, 2)]
        for strike in [-1, 360]:
            msg = 'strike %g is out of range [0, 360)' % strike
            self.assert_failed_creation(10, strike, 90,
                                        corners, ValueError, msg)

    def test_dip_out_of_range(self):
        corners = [Point(0, -1, 1), Point(0, 1, 1),
                   Point(0, 1, 2), Point(0, -1, 2)]
        for dip in [0, 91, -1]:
            msg = 'dip %g is out of range (0, 90]' % dip
            self.assert_failed_creation(10, 0, dip, corners, ValueError, msg)

    def assert_successfull_creation(self, mesh_spacing, strike, dip,
                                    tl, tr, br, bl):
        surface1 = PlanarSurface(mesh_spacing, strike, dip, tl, tr, br, bl)
        translated = surface1.translate(tl, tr).translate(tr, tl)
        for surface in [surface1, translated]:
            self.assertIsInstance(surface, PlanarSurface)
            self.assertEqual(surface.top_left, tl)
            self.assertEqual(surface.top_right, tr)
            self.assertEqual(surface.bottom_left, bl)
            self.assertEqual(surface.bottom_right, br)
            self.assertEqual(surface.mesh_spacing, mesh_spacing)
            self.assertEqual(surface.strike, strike)
            self.assertEqual(surface.get_strike(), strike)
            self.assertEqual(surface.dip, dip)
            self.assertEqual(surface.get_dip(), dip)
            self.assertIsNone(surface.mesh)
            self.assertAlmostEqual(surface.length, tl.distance(tr), delta=0.2)
            self.assertAlmostEqual(surface.width, tl.distance(bl), delta=0.2)

    def test_edges_not_parallel_within_tolerance(self):
        self.assert_successfull_creation(
            10, 20, 30,
            Point(0, -1, 1), Point(0, 1, 1),
            Point(-0.0003, 1, 2), Point(0.0003, -1, 2)
        )

    def test_edges_azimuths_cross_north_direction(self):
        self.assert_successfull_creation(
            10, 150, 45,
            Point(-0.0001, 0, 1), Point(0.0001, -1, 1),
            Point(-0.0001, -1, 2), Point(0.0001, 0, 2)
        )
        self.assert_successfull_creation(
            1, 2, 3,
            Point(0.0001, 0, 1), Point(-0.0001, -1, 1),
            Point(0.0001, -1, 2), Point(-0.0001, 0, 2)
        )

    def test_edges_differ_in_length_within_tolerance(self):
        self.assert_successfull_creation(
            1, 2, 3,
            Point(0, -1, 1), Point(0, 1, 1),
            Point(0, 1.000001, 2), Point(0, -1, 2)
        )

    def test_vertical_surf_from_corner_points(self):
        # vertical surface pointing North
        surf = PlanarSurface.from_corner_points(
            2., Point(0, 0, 0), Point(0, 1, 0), Point(0, 1, 5), Point(0, 0, 5)
        )
        self.assertEqual(surf.mesh_spacing, 2.)
        self.assertAlmostEqual(surf.strike, 0.)
        self.assertAlmostEqual(surf.dip, 90.)
        self.assertEqual(surf.top_left, Point(0, 0, 0))
        self.assertEqual(surf.top_right, Point(0, 1, 0))
        self.assertEqual(surf.bottom_left, Point(0, 0, 5))
        self.assertEqual(surf.bottom_right, Point(0, 1, 5))

    def test_vertical_surf_from_corner_points_topo(self):
        # vertical surface pointing North
        surf = PlanarSurface.from_corner_points(
            2., Point(0, 0, -1), Point(0, 1, -1), Point(0, 1, 4), Point(0, 0, 4)
        )
        self.assertEqual(surf.mesh_spacing, 2.)
        self.assertAlmostEqual(surf.strike, 0.)
        self.assertAlmostEqual(surf.dip, 90.)
        self.assertEqual(surf.top_left, Point(0, 0, -1))
        self.assertEqual(surf.top_right, Point(0, 1, -1))
        self.assertEqual(surf.bottom_left, Point(0, 0, 4))
        self.assertEqual(surf.bottom_right, Point(0, 1, 4))

    def test_inclined_surf_from_corner_points(self):
        # inclined surface (dip = 45) with 45 degrees strike
        surf = PlanarSurface.from_corner_points(
            2., Point(0, 0, 0), Point(0.5, 0.5, 0),
            Point(0.563593, 0.436408, 10.), Point(0.063592, -0.063592, 10)
        )
        self.assertEqual(surf.mesh_spacing, 2.)
        self.assertAlmostEqual(surf.strike, 45., delta=0.1)
        self.assertAlmostEqual(surf.dip, 45., delta=0.1)
        self.assertEqual(surf.top_left, Point(0, 0, 0))
        self.assertEqual(surf.top_right, Point(0.5, 0.5, 0))
        self.assertEqual(surf.bottom_left, Point(0.063592, -0.063592, 10))
        self.assertEqual(surf.bottom_right, Point(0.563593, 0.436408, 10.))

    def test_inclined_surf_from_corner_points_topo(self):
        # inclined surface (dip = 45) with 45 degrees strike
        surf = PlanarSurface.from_corner_points(
            2., Point(0, 0, -1), Point(0.5, 0.5, -1),
            Point(0.563593, 0.436408, 9.), Point(0.063592, -0.063592, 9)
        )
        self.assertEqual(surf.mesh_spacing, 2.)
        self.assertAlmostEqual(surf.strike, 45., delta=0.1)
        self.assertAlmostEqual(surf.dip, 45., delta=0.1)
        self.assertEqual(surf.top_left, Point(0, 0, -1))
        self.assertEqual(surf.top_right, Point(0.5, 0.5, -1))
        self.assertEqual(surf.bottom_left, Point(0.063592, -0.063592, 9))
        self.assertEqual(surf.bottom_right, Point(0.563593, 0.436408, 9.))


class PlanarSurfaceProjectTestCase(unittest.TestCase):
    def test1(self):
        lons, lats, depths = geo_utils.cartesian_to_spherical(
            numpy.array([[60, -10, -10], [60, -10, 10],
                         [60, 10, 10], [60, 10, -10]], float)
        )
        surface = PlanarSurface(10, 20, 30, *Mesh(lons, lats, depths))
        aaae = numpy.testing.assert_array_almost_equal

        plons, plats, pdepths = geo_utils.cartesian_to_spherical(
            numpy.array([[60, -10, -10], [59, 0, 0], [70, -11, -10]], float)
        )

        dists, xx, yy = surface._project(plons, plats, pdepths)
        aaae(xx, [0, 10, 0])
        aaae(yy, [0, 10, -1])
        aaae(dists, [0, 1, -10])

        lons, lats, depths = surface._project_back(dists, xx, yy)
        aaae(lons, plons)
        aaae(lats, plats)
        aaae(depths, pdepths)

    def test2(self):
        surface = PlanarSurface(
            10, 20, 30,
            Point(3.9, 2.2, 10), Point(4.90402718, 3.19634248, 10),
            Point(5.9, 2.2, 90), Point(4.89746275, 1.20365263, 90)
        )
        plons, plats, pdepths = [[4., 4.3, 3.1], [1.5, 1.7, 3.5],
                                 [11., 12., 13.]]
        dists, xx, yy = surface._project(plons, plats, pdepths)
        lons, lats, depths = surface._project_back(dists, xx, yy)
        aaae = numpy.testing.assert_array_almost_equal
        aaae(lons, plons)
        aaae(lats, plats)
        aaae(depths, pdepths)


class PlanarSurfaceGetMeshTestCase(utils.SurfaceTestCase):

    def _surface(self, corners):
        return PlanarSurface(1.0, 0.0, 90.0, *corners)

    def test_2(self):
        self.assert_mesh_is(self._surface(test_data.TEST_2_CORNERS),
                            expected_mesh=test_data.TEST_2_MESH)

    def test_3(self):
        self.assert_mesh_is(self._surface(test_data.TEST_3_CORNERS),
                            expected_mesh=test_data.TEST_3_MESH)

    def test_4(self):
        self.assert_mesh_is(self._surface(test_data.TEST_4_CORNERS),
                            expected_mesh=test_data.TEST_4_MESH)

    def test_5(self):
        self.assert_mesh_is(self._surface(test_data.TEST_5_CORNERS),
                            expected_mesh=test_data.TEST_5_MESH)

    def test_6(self):
        corners = [Point(0, 0, 9), Point(0, 1e-9, 9),
                   Point(0, 1e-9, 9.0 + 1e-9), Point(0, 0, 9.0 + 1e-9)]
        mesh = [[(0, 0, 9)]]
        self.assert_mesh_is(self._surface(corners),
                            expected_mesh=mesh)

    def test_7_rupture_1(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_1_CORNERS),
                            expected_mesh=test_data.TEST_7_RUPTURE_1_MESH)

    def test_7_rupture_2(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_2_CORNERS),
                            expected_mesh=test_data.TEST_7_RUPTURE_2_MESH)

    def test_7_rupture_3(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_3_CORNERS),
                            expected_mesh=test_data.TEST_7_RUPTURE_3_MESH)

    def test_7_rupture_4(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_4_CORNERS),
                            expected_mesh=test_data.TEST_7_RUPTURE_4_MESH)

    def test_7_rupture_5(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_5_CORNERS),
                            expected_mesh=test_data.TEST_7_RUPTURE_5_MESH)

    def test_7_rupture_6(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_6_CORNERS),
                            expected_mesh=test_data.TEST_7_RUPTURE_6_MESH)

    def test_7_rupture_7(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_7_CORNERS),
                            expected_mesh=test_data.TEST_7_RUPTURE_7_MESH)

    def test_7_rupture_8(self):
        self.assert_mesh_is(self._surface(test_data.TEST_7_RUPTURE_8_CORNERS),
                            expected_mesh=test_data.TEST_7_RUPTURE_8_MESH)


class PlanarSurfaceGetMinDistanceTestCase(unittest.TestCase):
    def test_1(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_6_CORNERS)
        sites = Mesh.from_points_list([Point(0, 0)])
        self.assertAlmostEqual(8.01185807319,
                               surface.get_min_distance(sites)[0], places=2)

    def test_2(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_6_CORNERS)
        sites = Mesh.from_points_list([Point(-0.25, 0.25)])
        self.assertAlmostEqual(40.1213468,
                               surface.get_min_distance(sites)[0], places=1)

    def test_3(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_2_CORNERS)
        sites = Mesh.from_points_list([Point(0, 0)])
        self.assertAlmostEqual(7.01186304977,
                               surface.get_min_distance(sites)[0], places=2)

    def test_4(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_2_CORNERS)
        sites = Mesh.from_points_list([Point(-0.3, 0.4)])
        self.assertAlmostEqual(55.6159556,
                               surface.get_min_distance(sites)[0], delta=0.6)

    def test_topo(self):
        surface = PlanarSurface(1, 2, 3, *test_data.TEST_7_RUPTURE_9_CORNERS)
        sites = Mesh.from_points_list([Point(-0.3, 0.4, -8)])
        self.assertAlmostEqual(55.6159556,
                               surface.get_min_distance(sites)[0], delta=0.6)

    def test_nine_positions(self):
        def v2p(*vectors):  # "vectors to points"
            return [Point(*coords)
                    for coords in zip(*geo_utils.cartesian_to_spherical(
                        numpy.array(vectors, dtype=float)
                    ))]

        corners = v2p([6370, 0, -0.5], [6370, 0, 0.5],
                      [6369, 2, 0.5], [6369, 2, -0.5])
        surface = PlanarSurface(1, 2, 3, *corners)

        # first three positions: point projection is above the top edge
        dists = surface.get_min_distance(Mesh.from_points_list(
            v2p([6371, 0, -1.5], [6371, 0, 1.5], [6371, 0, 0.33])
        ))
        self.assertTrue(numpy.allclose(dists, [2 ** 0.5, 2 ** 0.5, 1.0],
                                       atol=1e-4))

        # next three positions: point projection is below the bottom edge
        dists = surface.get_min_distance(Mesh.from_points_list(
            v2p([6368, 2, -1.5], [6368, 2, 1.5], [6368, 2, -0.45])
        ))
        self.assertTrue(numpy.allclose(dists, [2 ** 0.5, 2 ** 0.5, 1.0],
                                       atol=1e-4))

        # next three positions: point projection is left to rectangle,
        # right to it or lies inside
        dists = surface.get_min_distance(Mesh.from_points_list(
            v2p([6369.5, 1, -1.5], [6369.5, 1, 1.5], [6369.5, 1, -0.1])
        ))
        self.assertTrue(numpy.allclose(dists, [1, 1, 0], atol=1e-4))


class PlanarSurfaceGetJoynerBooreDistanceTestCase(unittest.TestCase):
    def test_point_inside(self):
        corners = [Point(-1, -1, 1), Point(1, -1, 1),
                   Point(1, 1, 2), Point(-1, 1, 2)]
        surface = PlanarSurface(10, 90, 45, *corners)
        sites = Mesh.from_points_list([Point(0, 0), Point(0, 0, 20),
                                       Point(0.1, 0.3)])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [0] * 3
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test_point_on_the_border(self):
        corners = [Point(0.1, -0.1, 1), Point(-0.1, -0.1, 1),
                   Point(-0.1, 0.1, 2), Point(0.1, 0.1, 2)]
        surface = PlanarSurface(1, 270, 45, *corners)
        sites = Mesh.from_points_list([Point(-0.1, 0.04), Point(0.1, 0.03)])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [0] * 2
        self.assertTrue(numpy.allclose(dists, expected_dists))

    def test_point_outside(self):
        corners = [Point(0.1, -0.1, 1), Point(-0.1, -0.1, 1),
                   Point(-0.1, 0.1, 2), Point(0.1, 0.1, 2)]
        surface = PlanarSurface(1, 270, 45, *corners)
        sites = Mesh.from_points_list([
            Point(-0.2, -0.2), Point(1, 1, 1), Point(4, 5),
            Point(0.8, 0.01), Point(0.2, -0.15), Point(0.02, -0.12),
            Point(-0.14, 0), Point(-3, 3), Point(0.05, 0.15, 10)
        ])
        dists = surface.get_joyner_boore_distance(sites)
        expected_dists = [
            Point(-0.2, -0.2).distance(Point(-0.1, -0.1)),
            Point(1, 1).distance(Point(0.1, 0.1)),
            Point(4, 5).distance(Point(0.1, 0.1)),
            Point(0.8, 0.01).distance(Point(0.1, 0.01)),
            Point(0.2, -0.15).distance(Point(0.1, -0.1)),
            Point(0.02, -0.12).distance(Point(0.02, -0.1)),
            Point(-0.14, 0).distance(Point(-0.1, 0)),
            Point(-3, 3).distance(Point(-0.1, 0.1)),
            Point(0.05, 0.15).distance(Point(0.05, 0.1))
        ]
        self.assertTrue(numpy.allclose(dists, expected_dists, atol=0.05))

    def test_distance_to_2d_mesh(self):
        corners = [Point(0.0, 1.0), Point(1.0, 1.0),
                   Point(1.0, 0.114341), Point(0.0, 0.114341)]
        surface = PlanarSurface(1, 90.0, 10.0, *corners)
        sites = Mesh(numpy.array([[0.25, 0.75], [0.25, 0.75]]),
                     numpy.array([[0.75, 0.75], [0.25, 0.25]]),
                     None)
        dists = surface.get_joyner_boore_distance(sites)
        numpy.testing.assert_equal(dists, numpy.zeros((2, 2)))


class PlanarSurfaceGetClosestPointsTestCase(unittest.TestCase):
    corners = [Point(-0.1, -0.1, 0), Point(0.1, -0.1, 0),
               Point(0.1, 0.1, 2), Point(-0.1, 0.1, 2)]
    surface = PlanarSurface(10, 90, 45, *corners)

    def test_point_above_surface(self):
        sites = Mesh.from_points_list([Point(0, 0), Point(-0.03, 0.05, 0.5)])
        res = self.surface.get_closest_points(sites)
        self.assertIsInstance(res, Mesh)
        aae = numpy.testing.assert_almost_equal
        aae(res.lons, [0, -0.03], decimal=4)
        aae(res.lats, [-0.00081824,  0.04919223])
        aae(res.depths, [1.0113781, 1.50822185])

    def test_corner_is_closest(self):
        sites = Mesh.from_points_list(
            [Point(-0.11, 0.11), Point(0.14, -0.12, 10),
             Point(0.3, 0.2, 0.5), Point(-0.6, -0.6, 0.3)]
        )
        res = self.surface.get_closest_points(sites)
        aae = numpy.testing.assert_almost_equal
        aae(res.lons, [-0.1, 0.1, 0.1, -0.1], decimal=4)
        aae(res.lats, [0.1, -0.1, 0.1, -0.1])
        aae(res.depths, [2, 0, 2, 0], decimal=5)

    def test_top_or_bottom_edge_is_closest(self):
        sites = Mesh.from_points_list([Point(-0.04, -0.28, 0),
                                       Point(0.033, 0.15, 0)])
        res = self.surface.get_closest_points(sites)
        aae = numpy.testing.assert_almost_equal
        aae(res.lons, [-0.04, 0.033], decimal=5)
        aae(res.lats, [-0.1, 0.1], decimal=5)
        aae(res.depths, [0, 2], decimal=2)

    def test_left_or_right_edge_is_closest(self):
        sites = Mesh.from_points_list([Point(-0.24, -0.08, 0.55),
                                       Point(0.17, 0.07, 0)])
        res = self.surface.get_closest_points(sites)
        aae = numpy.testing.assert_almost_equal
        aae(res.lons, [-0.1, 0.1], decimal=5)
        aae(res.lats, [-0.08, 0.07], decimal=3)
        aae(res.depths, [0.20679306, 1.69185737])

    def test_against_mesh_to_mesh(self):
        corners = [Point(2.6, 3.7, 20), Point(2.90102155, 3.99961567, 20),
                   Point(3.2, 3.7, 75), Point(2.89905849, 3.40038407, 75)]
        surface = PlanarSurface(0.5, 45, 70, *corners)
        lons, lats = numpy.meshgrid(numpy.linspace(2.2, 3.6, 7),
                                    numpy.linspace(3.4, 4.2, 7))
        sites = Mesh(lons, lats, depths=None)

        res1 = surface.get_closest_points(sites)
        res2 = super(PlanarSurface, surface).get_closest_points(sites)

        aae = numpy.testing.assert_almost_equal
        # precision up to ~1 km
        aae(res1.lons, res2.lons, decimal=2)
        aae(res1.lats, res2.lats, decimal=2)
        aae(res1.depths, res2.depths, decimal=0)

    corners_topo = [Point(-0.1, -0.1, -2), Point(0.1, -0.1, -2),
                    Point(0.1, 0.1, 0), Point(-0.1, 0.1, 0)]
    surface_topo = PlanarSurface(10, 90, 45, *corners_topo)

    def test_point_above_surface_topo(self):
        sites = Mesh.from_points_list([Point(0, 0, -2),
                                       Point(-0.03, 0.05, -1.5)])
        res = self.surface_topo.get_closest_points(sites)
        self.assertIsInstance(res, Mesh)
        aae = numpy.testing.assert_almost_equal
        aae(res.lons, [0, -0.03], decimal=5)
        aae(res.lats, [-0.00081824,  0.04919223], decimal=5)
        aae(res.depths, [1.0113781-2., 1.50822185-2.], decimal=5)


class PlanarSurfaceGetRXDistanceTestCase(unittest.TestCase):
    def _test1to7surface(self):
        corners = [Point(0, 0, 8), Point(-0.1, 0, 8),
                   Point(-0.1, 0, 9), Point(0, 0, 9)]
        surface = PlanarSurface(1, 270, 90, *corners)
        return surface

    def test1_site_on_the_hangin_wall(self):
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

    def test8_strike_of_45_degrees(self):
        corners = [Point(-0.05, -0.05, 8), Point(0.05, 0.05, 8),
                   Point(0.05, 0.05, 9), Point(-0.05, -0.05, 9)]
        surface = PlanarSurface(1, 45, 60, *corners)
        sites = Mesh.from_points_list([Point(0.05, 0)])
        self.assertAlmostEqual(surface.get_rx_distance(sites)[0],
                               3.9313415355436705, places=4)


class PlanarSurfaceGetRy0DistanceTestCase(unittest.TestCase):
    def _test1to7surface(self):
        corners = [Point(0, 0, 8), Point(-0.1, 0, 8),
                   Point(-0.1, 0, 9), Point(0, 0, 9)]
        surface = PlanarSurface(1, 270, 90, *corners)
        return surface

    def test1_sites_within_fault_width(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(-0.05, 0.05),
                                       Point(-0.05, -0.05)])
        dists = surface.get_ry0_distance(sites)
        numpy.testing.assert_allclose(dists, numpy.array([0.0, 0.0]))

    def test2_sites_parallel_to_fault_ends(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.0, 0.05),
                                       Point(-0.10, -0.05)])
        dists = surface.get_ry0_distance(sites)
        numpy.testing.assert_allclose(dists, numpy.array([0.0, 0.0]))

    def test3_sites_off_fault_ends(self):
        surface = self._test1to7surface()
        sites = Mesh.from_points_list([Point(0.05, 0.05),
                                       Point(-0.15, -0.05)])
        dists = surface.get_ry0_distance(sites)
        numpy.testing.assert_allclose(dists, 5.55974422 * numpy.ones(2))


class PlanarSurfaceGetTopEdgeDepthTestCase(unittest.TestCase):
    def test(self):
        corners = [Point(-0.05, -0.05, 8), Point(0.05, 0.05, 8),
                   Point(0.05, 0.05, 9), Point(-0.05, -0.05, 9)]
        surface = PlanarSurface(1, 45, 60, *corners)
        self.assertEqual(surface.get_top_edge_depth(), 8)


class PlanarSurfaceGetWidthTestCase(unittest.TestCase):
    def test_vertical_surface(self):
        corners = [Point(-0.05, -0.05, 8), Point(0.05, 0.05, 8),
                   Point(0.05, 0.05, 10), Point(-0.05, -0.05, 10)]
        surface = PlanarSurface(1, 45, 60, *corners)
        self.assertAlmostEqual(surface.get_width(), 2.0, places=4)

    def test_inclined_surface(self):
        corners = [Point(-0.00317958, -0.00449661, 4.64644661),
                   Point(-0.00317958, 0.00449661, 4.64644661),
                   Point(0.00317958, 0.00449661, 5.35355339),
                   Point(0.00317958, -0.00449661, 5.35355339)]
        surface = PlanarSurface(1, 0.0, 45.0, *corners)
        self.assertAlmostEqual(surface.get_width(), 1.0, places=3)


class PlanarSurfaceGetAreaTestCase(unittest.TestCase):
    def test(self):
        corners = [Point(0.0, 0.0, 0.0), Point(0.0, 0.089932, 0.0),
                   Point(0.0, 0.089932, 10.0), Point(0.0, 0.0, 10.0)]
        surface = PlanarSurface(1, 45, 90, *corners)
        self.assertAlmostEqual(surface.get_area(), 100.0, places=0)


class PlanarSurfaceGetBoundingBoxTestCase(unittest.TestCase):
    def test(self):
        corners = [Point(-0.00317958, -0.00449661, 4.64644661),
                   Point(-0.00317958, 0.00449661, 4.64644661),
                   Point(0.00317958, 0.00449661, 5.35355339),
                   Point(0.00317958, -0.00449661, 5.35355339)]
        surface = PlanarSurface(1, 0.0, 45.0, *corners)
        west, east, north, south = surface.get_bounding_box()
        self.assertEqual(-0.00317958, west)
        self.assertEqual(0.00317958, east)
        self.assertEqual(0.00449661, north)
        self.assertEqual(-0.00449661, south)


class PlanarSurfaceGetMiddlePointTestCase(unittest.TestCase):
    def test(self):
        corners = [Point(0.0, 0.0, 0.0), Point(0.0, 0.089932, 0.0),
                   Point(0.0, 0.089932, 10.0), Point(0.0, 0.0, 10.0)]
        surface = PlanarSurface(1, 45, 90, *corners)
        midpoint = surface.get_middle_point()
        assert_aeq(midpoint.longitude, 0.0, decimal=5)
        assert_aeq(midpoint.latitude, 0.044966, decimal=5)
        assert_aeq(midpoint.depth, 5.0, decimal=5)

    def test_topo(self):
        corners = [Point(0.0, 0.0, 0.0), Point(0.0, 0.089932, 0.0),
                   Point(0.0, 0.089932, -8.0), Point(0.0, 0.0, -8.0)]
        surface = PlanarSurface(1, 45, 90, *corners)
        midpoint = surface.get_middle_point()
        assert_aeq(midpoint.longitude, 0.0, decimal=5)
        assert_aeq(midpoint.latitude, 0.044966, decimal=5)
        assert_aeq(midpoint.depth, -4.0, decimal=5)
