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
from nhlib.geo.point import Point
from nhlib.geo.line import Line
from nhlib.geo.surface.simple_fault import SimpleFaultSurface

import _simple_fault_test_data as test_data
from tests.geo.surface import _utils as utils


class SimpleFaultSurfaceTestCase(utils.SurfaceTestCase):
    def setUp(self):
        self.fault_trace = Line(
            [Point(0.0, 0.0), Point(1.0, 1.0)])

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
                1.0, 6.0, 90.0, 1.0)

        self.assertAlmostEquals(40.0, surface.get_strike(), delta=0.02)

    def test_get_strike_along_meridian(self):
        line = Line([Point(0, 0), Point(1e-5, 1e-3), Point(0, 2e-3)])
        surface = SimpleFaultSurface.from_fault_data(line, 1.0, 6.0, 90.0, 0.1)
        self.assertAlmostEquals(0, surface.get_strike(), delta=6e-2)

    def test_get_dip_1(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0635916966572, 0.0635916574897)
        p3 = Point(0.0860747816618, 0.102533437776)

        surface = SimpleFaultSurface.from_fault_data(Line([p1, p2, p3]),
                1.0, 6.0, 90.0, 1.0)

        self.assertAlmostEquals(90.0, surface.get_dip())

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
                0.0, 10.0, 45.0, 10.0)

        self.assertAlmostEquals(75.0, surface.get_dip(), 1)
