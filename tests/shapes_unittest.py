#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from opengem import shapes

class ShapesTestCase(unittest.TestCase):
    
    def test_equals_when_have_the_same_values(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve3 = shapes.Curve([(0.1, 1.0), (0.2, 5.0)])
        curve4 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve5 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve6 = shapes.Curve([(0.1, (1.0, 0.5)), (0.2, (2.0, 0.3))])
        
        self.assertEquals(curve1, curve2)
        self.assertNotEquals(curve1, curve3)
        self.assertNotEquals(curve1, curve4)
        self.assertNotEquals(curve3, curve4)
        self.assertEquals(curve4, curve5)
        self.assertNotEquals(curve5, curve6)
    
    def test_can_construct_a_curve_from_dict(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve.from_dict({"0.1": 1.0, "0.2": 2.0})
        curve3 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve4 = shapes.Curve.from_dict({"0.1": (1.0, 0.3), "0.2": (2.0, 0.3)})
        
        # keys are already floats
        curve5 = shapes.Curve.from_dict({0.1: (1.0, 0.3), 0.2: (2.0, 0.3)})
        
        self.assertEquals(curve1, curve2)
        self.assertEquals(curve3, curve4)
        self.assertEquals(curve3, curve5)
    
    def test_can_serialize_in_json(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        self.assertEquals(curve1, shapes.Curve.from_json(curve1.to_json()))
        self.assertEquals(curve2, shapes.Curve.from_json(curve2.to_json()))

    def test_can_construct_with_unordered_values(self):
        curve = shapes.Curve([(0.5, 1.0), (0.4, 2.0), (0.3, 2.0)])
        
        self.assertEqual(1.0, curve.ordinate_for(0.5))
        self.assertEqual(2.0, curve.ordinate_for(0.4))
        self.assertEqual(2.0, curve.ordinate_for(0.3))