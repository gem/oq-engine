from __future__ import absolute_import
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
from math import pi, sin, cos, atan2, degrees

import numpy

from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface

from . import _simple_fault_test_data as test_data
from openquake.hazardlib.tests.geo.surface import _utils as utils


class SimpleFaultSurfaceCheckFaultDataTestCase(utils.SurfaceTestCase):
    def setUp(self):
        self.fault_trace = Line([Point(0.0, 0.0), Point(1.0, 1.0)])

    def test_dip_inside_range(self):
        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, 0.0, 1.0, 0.0, 1.0)

        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, 0.0, 1.0, -0.1, 1.0)

        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, 0.0, 1.0, 90.1, 1.0)

        SimpleFaultSurface.check_fault_data(self.fault_trace,
                                            0.0, 1.0, 0.1, 1.0)
        SimpleFaultSurface.check_fault_data(self.fault_trace,
                                            0.0, 1.0, 90.0, 1.0)

    def test_upper_seismo_depth_range(self):
        SimpleFaultSurface.check_fault_data(self.fault_trace,
                                            0.0, 1.0, 90.0, 1.0)
        SimpleFaultSurface.check_fault_data(self.fault_trace,
                                            1.0, 1.1, 90.0, 1.0)

    def test_upper_lower_seismo_values(self):
        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, 1.0, 1.0, 90.0, 1.0)

        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, 1.0, 0.9, 90.0, 1.0)

    def test_fault_trace_horizontal(self):
        fault_trace = Line([Point(0.0, 0.0, 1.0), Point(1.0, 1.0, 0.0)])

        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          fault_trace, 0.0, 1.0, 90.0, 1.0)

    def test_fault_below_upper_seismo_depth(self):
        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, -1.0, 5, 90.0, 1.0)

    def test_mesh_spacing_range(self):
        SimpleFaultSurface.check_fault_data(self.fault_trace,
                                            0.0, 1.0, 90.0, 1.0)

        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, 0.0, 1.0, 90.0, 0.0)

        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, 0.0, 1.0, 90.0, -1.0)

    def test_fault_trace_points(self):
        """
        The fault trace must have at least two points.
        """
        fault_trace = Line([Point(0.0, 0.0)])
        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          fault_trace, 0.0, 1.0, 90.0, 1.0)


class SimpleFaultSurfaceGetMeshTestCase(utils.SurfaceTestCase):
    def test_get_mesh_1(self):
        p1 = Point(0.0, 0.0, 0.0)
        p2 = Point(0.0, 0.0359728811759, 0.0)
        p3 = Point(0.0190775080917, 0.0550503815182, 0.0)
        p4 = Point(0.03974514139, 0.0723925718856, 0.0)

        fault = SimpleFaultSurface.from_fault_data(
            Line([p1, p2, p3, p4]), 0.0, 4.2426406871192848, 45.0, 1.0)

        self.assert_mesh_is(fault, test_data.TEST_1_MESH)

    def test_get_mesh_2(self):
        p1 = Point(0.0, 0.0, 0.0)
        p2 = Point(0.0, 0.0359728811759, 0.0)
        p3 = Point(0.0190775080917, 0.0550503815182, 0.0)
        p4 = Point(0.03974514139, 0.0723925718856, 0.0)

        fault = SimpleFaultSurface.from_fault_data(
            Line([p1, p2, p3, p4]), 2.12132034356,
            4.2426406871192848, 45.0, 1.0)

        self.assert_mesh_is(fault, test_data.TEST_2_MESH)

    def test_get_mesh_4(self):
        p1 = Point(0.0, 0.0, 0.0)
        p2 = Point(0.0, 0.0359728811759, 0.0)
        p3 = Point(0.0190775080917, 0.0550503815182, 0.0)
        p4 = Point(0.03974514139, 0.0723925718856, 0.0)

        fault = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3, p4]),
                                                   0.0, 4.0, 90.0, 1.0)

        self.assert_mesh_is(fault, test_data.TEST_4_MESH)

    def test_get_mesh_5(self):
        p1 = Point(179.9, 0.0)
        p2 = Point(180.0, 0.0)
        p3 = Point(-179.9, 0.0)

        fault = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3]), 1.0,
                                                   6.0, 90.0, 1.0)

        self.assert_mesh_is(fault, test_data.TEST_5_MESH)

    def test_get_mesh_topo(self):
        p1 = Point(0.0, 0.0, -2.0)
        p2 = Point(0.0, 0.0359728811759, -2.0)
        p3 = Point(0.0190775080917, 0.0550503815182, -2.0)
        p4 = Point(0.03974514139, 0.0723925718856, -2.0)

        fault = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3, p4]),
                                                   -2.0, 2.0, 90.0, 1.0)

        self.assert_mesh_is(fault, test_data.TEST_TOPO_MESH)


class SimpleFaultSurfaceGetStrikeTestCase(utils.SurfaceTestCase):
    def test_get_strike_1(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0635916966572, 0.0635916574897)

        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2]), 1.0, 6.0,
                                                     89.9, 1.0)

        self.assertAlmostEquals(45.0, surface.get_strike(), delta=1e-4)

    def test_get_strike_2(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0635916966572, 0.0635916574897)
        p3 = Point(0.0860747816618, 0.102533437776)

        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3]), 1.0,
                                                     6.0, 89.9, 1.0)

        self.assertAlmostEquals(40.0, surface.get_strike(), delta=0.02)

    def test_get_strike_along_meridian(self):
        line = Line([Point(0, 0), Point(1e-5, 1e-3), Point(0, 2e-3)])
        surface = SimpleFaultSurface.from_fault_data(line, 1.0, 6.0, 89.9, 0.1)
        self.assertAlmostEquals(0, surface.get_strike(), delta=6e-2)


class SimpleFaultSurfaceGetDipTestCase(utils.SurfaceTestCase):
    def test_get_dip_1(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0635916966572, 0.0635916574897)
        p3 = Point(0.0860747816618, 0.102533437776)

        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3]), 1.0,
                                                     6.0, 90.0, 1.0)

        self.assertAlmostEquals(90.0, surface.get_dip(), delta=1e-6)

    def test_get_dip_2(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0635916966572, 0.0635916574897)

        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2]), 1.0, 6.0,
                                                     30.0, 1.0)

        self.assertAlmostEquals(30.0, surface.get_dip(), 1)

    def test_get_dip_5(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0, 0.0899322029395)
        p3 = Point(0.0899323137217, 0.0899320921571)
        p4 = Point(0.0899323137217, -1.10782376538e-07)

        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3, p4]),
                                                     0.0, 10.0, 45.0, 1.0)

        # fault contains three segments. the one in the middle is inclined
        # with dip of 45 degrees. other two are purely vertical (they are
        # perpendicular to the middle one). the middle segment is rectangle
        # and the side ones are parallelograms. area of those parallelograms
        # is area of middle segment times sine of their acute angle.
        mid_area = 1.0
        mid_dip = pi / 4  # 45 degree
        side_area = sin(mid_dip) * mid_area
        side_dip = pi / 2  # 90 degree

        expected_dip = degrees(atan2(
            (mid_area * sin(mid_dip) + 2 * (side_area * sin(side_dip))) / 3.0,
            (mid_area * cos(mid_dip) + 2 * (side_area * cos(side_dip))) / 3.0
        ))
        self.assertAlmostEquals(surface.get_dip(), expected_dip, delta=1e-3)


class SimpleFaultSurfaceProjectionTestCase(unittest.TestCase):
    def test_three_points(self):
        polygon = SimpleFaultSurface.surface_projection_from_fault_data(
            Line([Point(10, -20), Point(11, -20.2), Point(12, -19.7)]),
            dip=30,
            upper_seismogenic_depth=25.3, lower_seismogenic_depth=53.6,
        )
        elons = [11.13560807, 10.1354272, 10.06374285, 12.06361991,
                 12.13515987]
        elats = [-21.02520738, -20.82520794, -20.3895235, -20.08952368,
                 -20.52520878]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_dip_90_three_points(self):
        polygon = SimpleFaultSurface.surface_projection_from_fault_data(
            Line([Point(1, -20), Point(1, -20.2), Point(2, -19.7)]),
            dip=90,
            upper_seismogenic_depth=30, lower_seismogenic_depth=50,
        )
        elons = [1, 1, 2]
        elats = [-20.2, -20., -19.7]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_dip_90_two_points(self):
        polygon = SimpleFaultSurface.surface_projection_from_fault_data(
            Line([Point(2, 2), Point(1, 1)]),
            dip=90,
            upper_seismogenic_depth=10, lower_seismogenic_depth=20,
        )
        elons = [1.00003181, 0.99996821, 0.99996819, 1.99996819, 2.00003182,
                 2.00003181]
        elats = [0.99996822, 0.99996819, 1.00003178, 2.0000318, 2.0000318,
                 1.9999682]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_dip_90_self_intersection(self):
        polygon = SimpleFaultSurface.surface_projection_from_fault_data(
            Line([Point(1, -2), Point(2, -1.9), Point(3, -2.1), Point(4, -2)]),
            dip=90,
            upper_seismogenic_depth=10, lower_seismogenic_depth=20,
        )
        elons = [3., 1., 2., 4.]
        elats = [-2.1, -2., -1.9, -2.]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_get_fault_vertices_3d(self):
        p0, p1, p2, p3 = SimpleFaultSurface.get_fault_patch_vertices(
            Line([Point(10., 45.2), Point(10.5, 45.3), Point(10., 45.487783)]),
            upper_seismogenic_depth=0., lower_seismogenic_depth=14.,
            dip=30, index_patch=1.
        )
        p4, p5, p6, p7 = SimpleFaultSurface.get_fault_patch_vertices(
            Line([Point(10., 45.2), Point(10.5, 45.3), Point(10., 45.487783)]),
            upper_seismogenic_depth=0., lower_seismogenic_depth=14.,
            dip=30, index_patch=2.
        )
        # Test for the first patch
        self.assertAlmostEqual(p0.longitude, 10., delta=0.1)
        self.assertAlmostEqual(p0.latitude, 45.2, delta=0.1)
        self.assertAlmostEqual(p0.depth, 0., delta=0.1)
        self.assertAlmostEqual(p1.longitude, 10.5, delta=0.1)
        self.assertAlmostEqual(p1.latitude, 45.3, delta=0.1)
        self.assertAlmostEqual(p1.depth, 0., delta=0.1)
        self.assertAlmostEqual(p2.longitude, 10.81, delta=0.1)
        self.assertAlmostEqual(p2.latitude, 45.2995, delta=0.1)
        self.assertAlmostEqual(p2.depth, 14., delta=0.1)
        self.assertAlmostEqual(p3.longitude, 10.31, delta=0.1)
        self.assertAlmostEqual(p3.latitude, 45.1995, delta=0.1)
        self.assertAlmostEqual(p3.depth, 14., delta=0.1)

        # Test for the second patch
        self.assertAlmostEqual(p4.longitude, 10.5, delta=0.1)
        self.assertAlmostEqual(p4.latitude, 45.3, delta=0.1)
        self.assertAlmostEqual(p4.depth, 0., delta=0.1)
        self.assertAlmostEqual(p5.longitude, 10.0, delta=0.1)
        self.assertAlmostEqual(p5.latitude, 45.4877, delta=0.1)
        self.assertAlmostEqual(p5.depth, 0., delta=0.1)
        self.assertAlmostEqual(p6.longitude, 10.311, delta=0.1)
        self.assertAlmostEqual(p6.latitude, 45.4873, delta=0.1)
        self.assertAlmostEqual(p6.depth, 14., delta=0.1)
        self.assertAlmostEqual(p7.longitude, 10.81, delta=0.1)
        self.assertAlmostEqual(p7.latitude, 45.2995, delta=0.1)
        self.assertAlmostEqual(p7.depth, 14., delta=0.1)

    def test_get_fault_vertices_3d_upper_seismogenic_depth_with_depth(self):
        p0, p1, p2, p3 = SimpleFaultSurface.get_fault_patch_vertices(
            Line([Point(10., 45.0), Point(10., 45.5)]),
            upper_seismogenic_depth=10., lower_seismogenic_depth=14.,
            dip=90, index_patch=1.
        )
        # The value used for this test is by hand calculation
        self.assertAlmostEqual(p0.longitude, 10., delta=0.1)
        self.assertAlmostEqual(p0.latitude, 45.0, delta=0.1)
        self.assertAlmostEqual(p0.depth, 10., delta=0.1)
        self.assertAlmostEqual(p1.longitude, 10.0, delta=0.1)
        self.assertAlmostEqual(p1.latitude, 45.5, delta=0.1)
        self.assertAlmostEqual(p1.depth, 10., delta=0.1)
        self.assertAlmostEqual(p2.longitude, 10.0, delta=0.1)
        self.assertAlmostEqual(p2.latitude, 45.5, delta=0.1)
        self.assertAlmostEqual(p2.depth, 14., delta=0.1)
        self.assertAlmostEqual(p3.longitude, 10.0, delta=0.1)
        self.assertAlmostEqual(p3.latitude, 45.0, delta=0.1)
        self.assertAlmostEqual(p3.depth, 14., delta=0.1)


class PatchIndexTest(unittest.TestCase):

    def test_hypocentre_index_1stpatch(self):
        hypocentre = Point(10.164151, 45.466944, 8.0)
        upper_seismogenic_depth = 0.
        lower_seismogenic_depth = 15.
        dip = 30.

        mesh_spacing = 1.
        fault_trace = Line([Point(10., 45.2), Point(10.0, 45.559729),
                           Point(10.365145, 45.813659)])

        whole_fault_surface = SimpleFaultSurface.from_fault_data(
            fault_trace, upper_seismogenic_depth,
            lower_seismogenic_depth, dip, mesh_spacing
        )

        target_rupture_surface = whole_fault_surface.get_resampled_top_edge()
        index = SimpleFaultSurface.hypocentre_patch_index(
            hypocentre, target_rupture_surface, upper_seismogenic_depth,
            lower_seismogenic_depth, dip)
        # The value used for this test is by hand calculation
        self.assertEqual(index, 1)

    def test_hypocentre_index_2ndpatch(self):
        hypocentre = Point(10.237155, 45.562761, 8.0)
        upper_seismogenic_depth = 0.
        lower_seismogenic_depth = 15.
        dip = 30.

        mesh_spacing = 1.
        fault_trace = Line([Point(10., 45.2), Point(10.0, 45.559729),
                           Point(10.365145, 45.813659)])

        whole_fault_surface = SimpleFaultSurface.from_fault_data(
            fault_trace, upper_seismogenic_depth,
            lower_seismogenic_depth, dip, mesh_spacing
        )

        target_rupture_surface = whole_fault_surface.get_resampled_top_edge()
        index = SimpleFaultSurface.hypocentre_patch_index(
            hypocentre, target_rupture_surface, upper_seismogenic_depth,
            lower_seismogenic_depth, dip)
        # The value used for this test is by hand calculation
        self.assertEqual(index, 2)

    def test_hypocentre_index_large_mesh_spacing(self):
        hypocentre = Point(10.443522, 45.379006, 20.0)
        upper_seismogenic_depth = 10.
        lower_seismogenic_depth = 28.
        dip = 30.

        mesh_spacing = 10.
        fault_trace = Line([Point(10., 45.2), Point(10., 45.487783)])

        whole_fault_surface = SimpleFaultSurface.from_fault_data(
            fault_trace, upper_seismogenic_depth,
            lower_seismogenic_depth, dip, mesh_spacing
        )

        target_rupture_surface = whole_fault_surface.get_resampled_top_edge()
        index = SimpleFaultSurface.hypocentre_patch_index(
            hypocentre, target_rupture_surface, upper_seismogenic_depth,
            lower_seismogenic_depth, dip)
        # The value used for this test is by hand calculation
        self.assertEqual(index, 1)

    def test_hypocentre_index_multi_segments(self):
        hypocentre = Point(0.588100, 0.479057, 7.1711)
        upper_seismogenic_depth = 0.5
        lower_seismogenic_depth = 15.
        dip = 56.5

        mesh_spacing = 2.
        fault_trace = Line([Point(0., 0.), Point(0.55, 0.5), Point(1.2, 1.2)])

        whole_fault_surface = SimpleFaultSurface.from_fault_data(
            fault_trace, upper_seismogenic_depth,
            lower_seismogenic_depth, dip, mesh_spacing
        )

        target_rupture_surface = whole_fault_surface.get_resampled_top_edge()
        index = SimpleFaultSurface.hypocentre_patch_index(
            hypocentre, target_rupture_surface, upper_seismogenic_depth,
            lower_seismogenic_depth, dip)
        # The value used for this test is by hand calculation
        self.assertEqual(index, 2)


class SimpleFaultSurfaceGetWidthTestCase(unittest.TestCase):
    def test_vertical_planar_surface(self):
        p1 = Point(0.1, 0.1, 0.0)
        p2 = Point(0.1, 0.126979648178, 0.0)
        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2]),
                                                     2.0, 4.0, 90.0, 1.0)
        self.assertAlmostEqual(surface.get_width(), 2.0)

    def test_inclined_non_planar_surface(self):
        p1 = Point(0.1, 0.1, 0.0)
        p2 = Point(0.1, 0.117986432118, 0.0)
        p3 = Point(0.117986470254, 0.117986426305, 0.0)
        p4 = Point(0.117986470254, 0.0999999941864, 0.0)
        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3, p4]),
                                                     2.0, 4.0, 30.0, 1.0)
        self.assertAlmostEqual(surface.get_width(), 4.0, places=2)
