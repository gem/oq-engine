# encoding: utf-8

import unittest

from nhe.common import geo
from nhe.surface.simple_fault import SimpleFaultSurface


class SimpleFaultSurfaceTestCase(unittest.TestCase):

    def setUp(self):
        self.fault_trace = geo.Line(
            [geo.Point(0.0, 0.0), geo.Point(1.0, 1.0)])

    def test_dip_inside_range(self):
        self.assertRaises(RuntimeError, SimpleFaultSurface,
                self.fault_trace, 0.0, None, 0.0)

        self.assertRaises(RuntimeError, SimpleFaultSurface,
                self.fault_trace, 0.0, None, -0.1)

        self.assertRaises(RuntimeError, SimpleFaultSurface,
                self.fault_trace, 0.0, None, 90.1)
        
        SimpleFaultSurface(self.fault_trace, 0.0, None, 0.1)
        SimpleFaultSurface(self.fault_trace, 0.0, None, 90.0)

    def test_upper_seismo_depth_range(self):
        self.assertRaises(RuntimeError, SimpleFaultSurface,
                self.fault_trace, -0.1, None, 90.0)

        SimpleFaultSurface(self.fault_trace, 0.0, None, 90.0)
        SimpleFaultSurface(self.fault_trace, 1.0, None, 90.0)

    def test_fault_trace_on_surface(self):
        fault_trace = geo.Line(
            [geo.Point(0.0, 0.0, 1.0), geo.Point(1.0, 1.0, 0.0)])

        self.assertRaises(RuntimeError, SimpleFaultSurface,
                fault_trace, 0.0, None, 90.0)

    def test_mesh_spacing_range(self):
        surface = SimpleFaultSurface(self.fault_trace, 0.0, None, 90.0)
        
        self.assertRaises(RuntimeError, surface.get_mesh, 0.0)
        self.assertRaises(RuntimeError, surface.get_mesh, -0.1)

    def test_fault_width_range(self):
        # (lower_seismo_depth - upper_seismo_depth) / sin(dip) is 1.0
        surface = SimpleFaultSurface(self.fault_trace, 1.0, 2.0, 90.0)
        self.assertRaises(RuntimeError, surface.get_mesh, 1.5)

    def test_fault_trace_points(self):
        fault_trace = geo.Line([geo.Point(0.0, 0.0)])

        self.assertRaises(RuntimeError, SimpleFaultSurface,
                fault_trace, 0.0, None, 90.0)
