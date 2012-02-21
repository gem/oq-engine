# encoding: utf-8

import unittest

from nhe.geo.point import Point
from nhe.geo.line import Line
from nhe.geo.surface.simple_fault import SimpleFaultSurface

import _simple_fault_test_data as test_data
from tests.geo.surface import _utils as utils


class SimpleFaultSurfaceTestCase(utils.SurfaceTestCase):

    def setUp(self):
        self.fault_trace = Line(
            [Point(0.0, 0.0), Point(1.0, 1.0)])

    def test_dip_inside_range(self):
        self.assertRaises(ValueError, SimpleFaultSurface,
                self.fault_trace, 0.0, 1.0, 0.0, 1.0)

        self.assertRaises(ValueError, SimpleFaultSurface,
                self.fault_trace, 0.0, 1.0, -0.1, 1.0)

        self.assertRaises(ValueError, SimpleFaultSurface,
                self.fault_trace, 0.0, 1.0, 90.1, 1.0)

        SimpleFaultSurface(self.fault_trace, 0.0, 1.0, 0.1, 1.0)
        SimpleFaultSurface(self.fault_trace, 0.0, 1.0, 90.0, 1.0)

    def test_upper_seismo_depth_range(self):
        self.assertRaises(ValueError, SimpleFaultSurface,
                self.fault_trace, -0.1, None, 90.0, 1.0)

        SimpleFaultSurface(self.fault_trace, 0.0, 1.0, 90.0, 1.0)
        SimpleFaultSurface(self.fault_trace, 1.0, 1.1, 90.0, 1.0)

    def test_upper_lower_seismo_values(self):
        self.assertRaises(ValueError, SimpleFaultSurface,
                self.fault_trace, 1.0, 1.0, 90.0, 1.0)

        self.assertRaises(ValueError, SimpleFaultSurface,
                self.fault_trace, 1.0, 0.9, 90.0, 1.0)

    def test_fault_trace_on_surface(self):
        fault_trace = Line(
            [Point(0.0, 0.0, 1.0), Point(1.0, 1.0, 0.0)])

        self.assertRaises(ValueError, SimpleFaultSurface,
                fault_trace, 0.0, 1.0, 90.0, 1.0)

    def test_mesh_spacing_range(self):
        SimpleFaultSurface(self.fault_trace, 0.0, 1.0, 90.0, 1.0)

        self.assertRaises(ValueError, SimpleFaultSurface,
                self.fault_trace, 0.0, 1.0, 90.0, 0.0)

        self.assertRaises(ValueError, SimpleFaultSurface,
                self.fault_trace, 0.0, 1.0, 90.0, -1.0)

    def test_fault_trace_points(self):
        """
        The fault trace must have at least two points.
        """
        fault_trace = Line([Point(0.0, 0.0)])

        self.assertRaises(ValueError, SimpleFaultSurface,
                fault_trace, 0.0, 1.0, 90.0, 1.0)

    def test_get_mesh_1(self):
        p1 = Point(0.0, 0.0, 0.0)
        p2 = Point(0.0, 0.0359728811759, 0.0)
        p3 = Point(0.0190775080917, 0.0550503815182, 0.0)
        p4 = Point(0.03974514139, 0.0723925718856, 0.0)

        fault = SimpleFaultSurface(
            Line([p1, p2, p3, p4]), 0.0, 4.2426406871192848, 45.0, 1.0)

        self.assert_mesh_is(fault, test_data.TEST_1_MESH)

    def test_get_mesh_2(self):
        p1 = Point(0.0, 0.0, 0.0)
        p2 = Point(0.0, 0.0359728811759, 0.0)
        p3 = Point(0.0190775080917, 0.0550503815182, 0.0)
        p4 = Point(0.03974514139, 0.0723925718856, 0.0)

        fault = SimpleFaultSurface(Line([p1, p2, p3, p4]),
                2.12132034356, 4.2426406871192848, 45.0, 1.0)

        self.assert_mesh_is(fault, test_data.TEST_2_MESH)

    def test_get_mesh_4(self):
        p1 = Point(0.0, 0.0, 0.0)
        p2 = Point(0.0, 0.0359728811759, 0.0)
        p3 = Point(0.0190775080917, 0.0550503815182, 0.0)
        p4 = Point(0.03974514139, 0.0723925718856, 0.0)

        fault = SimpleFaultSurface(Line([p1, p2, p3, p4]),
                0.0, 4.0, 90.0, 1.0)

        self.assert_mesh_is(fault, test_data.TEST_4_MESH)

    def test_get_mesh_5(self):
        p1 = Point(179.9, 0.0)
        p2 = Point(180.0, 0.0)
        p3 = Point(-179.9, 0.0)

        fault = SimpleFaultSurface(Line([p1, p2, p3]),
                1.0, 6.0, 90.0, 1.0)

        self.assert_mesh_is(fault, test_data.TEST_5_MESH)

    def test_get_strike_1(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0635916966572, 0.0635916574897)
        
        surface = SimpleFaultSurface(Line([p1, p2]),
                1.0, 6.0, 90.0, 1.0)
        
        self.assertAlmostEquals(45.0, surface.get_strike())

    def test_get_strike_2(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0635916966572, 0.0635916574897)
        p3 = Point(0.0860747816618, 0.102533437776)

        surface = SimpleFaultSurface(Line([p1, p2, p3]),
                1.0, 6.0, 90.0, 1.0)

        self.assertAlmostEquals(40.0, surface.get_strike())
