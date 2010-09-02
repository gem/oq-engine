#!/usr/bin/env python
# encoding: utf-8
"""
Test cases for the probablistic scenario described
in the scientific model. The values we check against are from
the documentation you can find at <http://to_be_defined>.
"""

import unittest

from opengem.risk.probabilistic_scenario import *

ASSET_TEST_VALUE = 5.0
INVALID_ASSET_VALUE = 0.0

class ProbabilisticScenarioTestCase(unittest.TestCase):

    # loss curve tests

    def test_empty_loss_curve(self):
        """Degenerate case."""
        
        self.assertEqual(compute_loss_curve(EMPTY_CURVE, ASSET_TEST_VALUE),
                EMPTY_CURVE)
    
    def test_a_loss_curve_is_not_defined_when_the_asset_is_not_valid(self):
        self.assertEqual(compute_loss_curve(
                Curve({0.1: 1.0, 0.2: 2.0, 0.3: 3.0}), INVALID_ASSET_VALUE),
                EMPTY_CURVE)
    
    def test_loss_curve_computation(self):
        loss_ratio_curve = Curve({0.1: 1.0, 0.2: 2.0, 0.3: 3.0})
        loss_curve = compute_loss_curve(loss_ratio_curve, ASSET_TEST_VALUE)

        self.assertEqual(Curve({0.1 * ASSET_TEST_VALUE: 1.0,
                0.2 * ASSET_TEST_VALUE: 2.0,
                0.3 * ASSET_TEST_VALUE: 3.0}), loss_curve)
                
    # loss ratio exceedance matrix * po tests
    
    def test_empty_when_the_vulnerability_function_is_empty(self):
        """Degenerate case."""
        
        self.assertEqual([], compute_lrem_po(EMPTY_CURVE, [], EMPTY_CURVE))
        
    def test_lrem_po_computation(self):
        vuln_function = Curve({5.0: 0.0, 6.0: 0.0, 7.0: 0.0, 8.0: 0.0})
        hazard_curve = Curve({5.0: 0.138, 6.0: 0.099, 7.0: 0.068, 8.0: 0.041})
        lrem = [[0.695, 0.858, 0.990, 1.000], [0.266, 0.510, 0.841, 0.999]]

        self.assertAlmostEquals(0.0959, compute_lrem_po(vuln_function,
                lrem, hazard_curve)[0][0], 0.0001)
                
        self.assertAlmostEquals(0.0367, compute_lrem_po(vuln_function,
                lrem, hazard_curve)[1][0], 0.0001)
        
        self.assertAlmostEquals(0.0849, compute_lrem_po(vuln_function,
                lrem, hazard_curve)[0][1], 0.0001)
                
        self.assertAlmostEquals(0.0504, compute_lrem_po(vuln_function,
                lrem, hazard_curve)[1][1], 0.0001)
                
        self.assertAlmostEquals(0.0673, compute_lrem_po(vuln_function,
                lrem, hazard_curve)[0][2], 0.0001)
                
        self.assertAlmostEquals(0.0571, compute_lrem_po(vuln_function,
                lrem, hazard_curve)[1][2], 0.0001)
                
        self.assertAlmostEquals(0.0410, compute_lrem_po(vuln_function, 
                lrem, hazard_curve)[0][3], 0.0001)
                
        self.assertAlmostEquals(0.0410, compute_lrem_po(vuln_function,
                lrem, hazard_curve)[1][3], 0.0001)
