# encoding: utf-8

import unittest

from nhe.common import geo
from nhe.surface.simple_fault import SimpleFaultSurface

import _simple_fault_test_data as test_data
import utils


class SimpleFaultSurfaceTestCase(utils.SurfaceTestCase):

    def setUp(self):
        self.fault_trace = geo.Line(
            [geo.Point(0.0, 0.0), geo.Point(1.0, 1.0)])

    def test_dip_inside_range(self):
        self.assertRaises(RuntimeError, SimpleFaultSurface,
                self.fault_trace, 0.0, 1.0, 0.0)

        self.assertRaises(RuntimeError, SimpleFaultSurface,
                self.fault_trace, 0.0, 1.0, -0.1)

        self.assertRaises(RuntimeError, SimpleFaultSurface,
                self.fault_trace, 0.0, 1.0, 90.1)

        SimpleFaultSurface(self.fault_trace, 0.0, 1.0, 0.1)
        SimpleFaultSurface(self.fault_trace, 0.0, 1.0, 90.0)

    def test_upper_seismo_depth_range(self):
        self.assertRaises(RuntimeError, SimpleFaultSurface,
                self.fault_trace, -0.1, None, 90.0)

        SimpleFaultSurface(self.fault_trace, 0.0, 1.0, 90.0)
        SimpleFaultSurface(self.fault_trace, 1.0, 1.0, 90.0)

    def test_upper_lower_seismo_values(self):
        self.assertRaises(RuntimeError, SimpleFaultSurface,
                self.fault_trace, 1.0, 0.9, 90.0)

    def test_fault_trace_on_surface(self):
        fault_trace = geo.Line(
            [geo.Point(0.0, 0.0, 1.0), geo.Point(1.0, 1.0, 0.0)])

        self.assertRaises(RuntimeError, SimpleFaultSurface,
                fault_trace, 0.0, 1.0, 90.0)

    def test_mesh_spacing_range(self):
        surface = SimpleFaultSurface(self.fault_trace, 0.0, 1.0, 90.0)

        self.assertRaises(RuntimeError, surface.get_mesh, 0.0)
        self.assertRaises(RuntimeError, surface.get_mesh, -0.1)

    def test_fault_trace_points(self):
        fault_trace = geo.Line([geo.Point(0.0, 0.0)])

        self.assertRaises(RuntimeError, SimpleFaultSurface,
                fault_trace, 0.0, 1.0, 90.0)

    def test_get_mesh_1(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 0.0359728811759, 0.0)
        p3 = geo.Point(0.0190775080917, 0.0550503815182, 0.0)
        p4 = geo.Point(0.03974514139, 0.0723925718856, 0.0)

        fault = SimpleFaultSurface(
            geo.Line([p1, p2, p3, p4]), 0.0, 4.2426406871192848, 45.0)

        self.assert_mesh_is(fault, 1.0, test_data.TEST_1_MESH)

    def test_get_mesh_2(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 0.0359728811759, 0.0)
        p3 = geo.Point(0.0190775080917, 0.0550503815182, 0.0)
        p4 = geo.Point(0.03974514139, 0.0723925718856, 0.0)

        fault = SimpleFaultSurface(geo.Line([p1, p2, p3, p4]),
                2.12132034356, 4.2426406871192848, 45.0)

        self.assert_mesh_is(fault, 1.0, test_data.TEST_2_MESH)

    def test_get_mesh_3(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 0.0359728811759, 0.0)
        p3 = geo.Point(0.0190775080917, 0.0550503815182, 0.0)
        p4 = geo.Point(0.03974514139, 0.0723925718856, 0.0)

        fault = SimpleFaultSurface(geo.Line([p1, p2, p3, p4]),
                2.12132034356, 2.12132034356, 45.0)

        self.assert_mesh_is(fault, 1.0, test_data.TEST_3_MESH)

    def test_get_mesh_4(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 0.0359728811759, 0.0)
        p3 = geo.Point(0.0190775080917, 0.0550503815182, 0.0)
        p4 = geo.Point(0.03974514139, 0.0723925718856, 0.0)

        fault = SimpleFaultSurface(geo.Line([p1, p2, p3, p4]),
                0.0, 4.0, 90.0)

        self.assert_mesh_is(fault, 1.0, test_data.TEST_4_MESH)

    @unittest.skip("line intersection must be fixed first")
    def test_get_mesh_5(self):
        p1 = geo.Point(179.9, 0.0)
        p2 = geo.Point(180.0, 0.0)
        p3 = geo.Point(-179.9, 0.0)

        fault = SimpleFaultSurface(geo.Line([p1, p2, p3]),
                1.0, 6.0, 90.0)

        self.assert_mesh_is(fault, 1.0, test_data.TEST_5_MESH)
