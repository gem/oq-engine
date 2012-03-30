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
from math import pi, sin, cos, atan2, degrees

from nhlib.geo.point import Point
from nhlib.geo.line import Line
from nhlib.geo.surface.simple_fault import SimpleFaultSurface

import _simple_fault_test_data as test_data
from tests.geo.surface import _utils as utils


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
        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, -0.1, None, 90.0, 1.0)

        SimpleFaultSurface.check_fault_data(self.fault_trace,
                                            0.0, 1.0, 90.0, 1.0)
        SimpleFaultSurface.check_fault_data(self.fault_trace,
                                            1.0, 1.1, 90.0, 1.0)

    def test_upper_lower_seismo_values(self):
        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, 1.0, 1.0, 90.0, 1.0)

        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          self.fault_trace, 1.0, 0.9, 90.0, 1.0)

    def test_fault_trace_on_surface(self):
        fault_trace = Line([Point(0.0, 0.0, 1.0), Point(1.0, 1.0, 0.0)])

        self.assertRaises(ValueError, SimpleFaultSurface.check_fault_data,
                          fault_trace, 0.0, 1.0, 90.0, 1.0)

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

        fault = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3, p4]),
                2.12132034356, 4.2426406871192848, 45.0, 1.0)

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

        fault = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3]),
                1.0, 6.0, 90.0, 1.0)

        self.assert_mesh_is(fault, test_data.TEST_5_MESH)


class SimpleFaultSurfaceGetStrikeTestCase(utils.SurfaceTestCase):
    def test_get_strike_1(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0635916966572, 0.0635916574897)

        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2]),
                1.0, 6.0, 90.0, 1.0)

        self.assertAlmostEquals(45.0, surface.get_strike(), delta=1e-4)

    def test_get_strike_2(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0635916966572, 0.0635916574897)
        p3 = Point(0.0860747816618, 0.102533437776)

        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3]),
                1.0, 6.0, 89.9, 1.0)

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

        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3]),
                1.0, 6.0, 90.0, 1.0)

        self.assertAlmostEquals(90.0, surface.get_dip(), delta=1e-6)

    def test_get_dip_2(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0635916966572, 0.0635916574897)

        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2]),
                1.0, 6.0, 30.0, 1.0)

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
