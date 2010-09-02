#!/usr/bin/env python
# encoding: utf-8
"""
Test cases for the probablistic scenario described
in the scientific model. The values we check against are taken from the as well.
"""

import unittest

from opengem.risk.probabilistic_scenario import *
from opengem import shapes

ASSET_TEST_VALUE = 5.0
INVALID_ASSET_VALUE = 0.0

class ProbabilisticScenarioTestCase(unittest.TestCase):

    def test_empty_loss_curve(self):
        """Degenerate case."""
        
        self.assertEqual(compute_loss_curve(shapes.EMPTY_CURVE, ASSET_TEST_VALUE), \
                shapes.EMPTY_CURVE)
    
    def test_a_loss_curve_is_not_defined_when_the_asset_is_not_valid(self):
        self.assertEqual(compute_loss_curve(\
                shapes.Curve({0.1: 1.0, 0.2: 2.0, 0.3: 3.0}), INVALID_ASSET_VALUE), \
                shapes.EMPTY_CURVE)
    
    def test_loss_curve_computation(self):
        loss_ratio_curve = shapes.Curve({0.1: 1.0, 0.2: 2.0, 0.3: 3.0})
        loss_curve = compute_loss_curve(loss_ratio_curve, ASSET_TEST_VALUE)

        self.assertEqual(shapes.Curve({0.1 * ASSET_TEST_VALUE: 1.0, \
                0.2 * ASSET_TEST_VALUE: 2.0, \
                0.3 * ASSET_TEST_VALUE: 3.0}), loss_curve)