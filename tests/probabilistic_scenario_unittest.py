#!/usr/bin/env python
# encoding: utf-8
"""
Test cases for the probablistic scenario described
in the scientific model. The values we check against are taken from
the documentation you can find at <http://to_be_defined>.
"""

import unittest

from opengem.risk.probabilistic_scenario import *
from opengem import shapes

# input test values
ASSET_VALUE = 5.0
INVALID_ASSET_VALUE = 0.0
HAZARD_CURVE = shapes.Curve({5.0: 0.138, 6.0: 0.099, 7.0: 0.068, 8.0: 0.041})

VULNERABILITY_FUNCTION = shapes.Curve({5.0: (0.0, 0.0),
        6.0: (0.0, 0.0), 7.0: (0.0, 0.0), 8.0: (0.0, 0.0)})

LOSS_RATIO_EXCEEDANCE_MATRIX = [[0.695, 0.858, 0.990, 1.000], \
        [0.266, 0.510, 0.841, 0.999]]

class ProbabilisticScenarioTestCase(unittest.TestCase):

    # loss curve tests

    def test_empty_loss_curve(self):
        """Degenerate case."""
        
        self.assertEqual(compute_loss_curve(
                shapes.EMPTY_CURVE, None),
                shapes.EMPTY_CURVE)
    
    def test_a_loss_curve_is_not_defined_when_the_asset_is_invalid(self):
        self.assertEqual(compute_loss_curve(
                shapes.Curve({0.1: 1.0, 0.2: 2.0, 0.3: 3.0}),
                INVALID_ASSET_VALUE),
                shapes.EMPTY_CURVE)
    
    def test_loss_curve_computation(self):
        loss_ratio_curve = shapes.Curve({0.1: 1.0, 0.2: 2.0, 0.3: 3.0})
        loss_curve = compute_loss_curve(loss_ratio_curve, ASSET_VALUE)

        self.assertEqual(shapes.Curve({0.1 * ASSET_VALUE: 1.0,
                0.2 * ASSET_VALUE: 2.0,
                0.3 * ASSET_VALUE: 3.0}), loss_curve)

    # loss ratio exceedance matrix * po tests
    
    def test_empty_matrix(self):
        """Degenerate case."""
        
        self.assertEqual([], compute_lrem_po(shapes.EMPTY_CURVE,
                None, None))
        
    def test_lrem_po_computation(self):
        lrem_po = compute_lrem_po(VULNERABILITY_FUNCTION, 
                LOSS_RATIO_EXCEEDANCE_MATRIX, HAZARD_CURVE)

        self.assertAlmostEquals(0.0959, lrem_po[0][0], 0.0001)
        self.assertAlmostEquals(0.0367, lrem_po[1][0], 0.0001)
        self.assertAlmostEquals(0.0849, lrem_po[0][1], 0.0001)
        self.assertAlmostEquals(0.0504, lrem_po[1][1], 0.0001)
        self.assertAlmostEquals(0.0673, lrem_po[0][2], 0.0001)
        self.assertAlmostEquals(0.0571, lrem_po[1][2], 0.0001)
        self.assertAlmostEquals(0.0410, lrem_po[0][3], 0.0001)
        self.assertAlmostEquals(0.0410, lrem_po[1][3], 0.0001)

    # loss ratio curve tests
    
    def test_empty_loss_ratio_curve(self):
        """Degenerate case."""
        
        self.assertEqual(shapes.EMPTY_CURVE, compute_loss_ratio_curve(None, []))
        
    def test_loss_ratio_curve_computation(self):
        loss_ratio_curve = compute_loss_ratio_curve([1.0, 2.0], 
                compute_lrem_po(VULNERABILITY_FUNCTION,
                LOSS_RATIO_EXCEEDANCE_MATRIX, HAZARD_CURVE))

        self.assertAlmostEquals(0.2891, loss_ratio_curve.get_for(1.0), 0.0001)
        self.assertAlmostEquals(0.1853, loss_ratio_curve.get_for(2.0), 0.0001)

    # lrem tests
    
    def test_empty_matrix(self):
        """Degenerate case."""
        
        self.assertEqual([], compute_lrem([], shapes.EMPTY_CURVE))

    def test_lrem_computation(self):
        vuln_function = shapes.Curve({5.0: (1.0, 0.1), 5.5: (2.0, 0.2) })
        loss_ratios = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]

        # fake distribution
        class FakeDistribution(object):
            
            def cdf(self, value, mean, std_dev):
                probabilities = {0.2: 0.1, 0.4: 0.2, 0.6: 0.3,
                        0.8: 0.4, 1.0: 0.7, 1.2: 0.8, 1.4: 0.9,
                        1.6: 1.0, 1.8: 1.1, 2.0: 1.2}
                
                return probabilities[value]
        
        lrem = compute_lrem(loss_ratios, vuln_function, FakeDistribution())
        
        self.assertEquals(1.0 - 0.1, lrem[0][0])
        self.assertEquals(1.0 - 0.1, lrem[0][1])
        self.assertEquals(1.0 - 0.2, lrem[1][0])
        self.assertEquals(1.0 - 0.2, lrem[1][1])
        self.assertEquals(1.0 - 0.3, lrem[2][0])
        self.assertEquals(1.0 - 0.3, lrem[2][1])
        self.assertEquals(1.0 - 0.4, lrem[3][0])
        self.assertEquals(1.0 - 0.4, lrem[3][1])
        self.assertEquals(1.0 - 0.7, lrem[4][0])
        self.assertEquals(1.0 - 0.7, lrem[4][1])
        self.assertEquals(1.0 - 0.8, lrem[5][0])
        self.assertEquals(1.0 - 0.8, lrem[5][1])
        self.assertEquals(1.0 - 0.9, lrem[6][0])
        self.assertEquals(1.0 - 0.9, lrem[6][1])
        self.assertEquals(1.0 - 1.0, lrem[7][0])
        self.assertEquals(1.0 - 1.0, lrem[7][1])

        # negative values are not allowed
        self.assertEquals(0.0, lrem[8][0], 0.0)
        self.assertEquals(0.0, lrem[8][1], 0.0)
        self.assertEquals(0.0, lrem[9][0], 0.0)
        self.assertEquals(0.0, lrem[9][1], 0.0)
        
        # last loss ratio is always 1.0
        self.assertEquals(1.0 - 0.7, lrem[10][0])
        self.assertEquals(1.0 - 0.7, lrem[10][1])
        
    # loss ratios splitting tests

# TODO (ac): Maybe SciPy already defines something like this?
    def test_splits_single_interval_with_no_steps_between(self):
        self.assertEqual([1.0, 2.0], split_loss_ratios([1.0, 2.0], 1))
        
    def test_splits_single_interval_with_a_step_between(self):
        self.assertEqual([1.0, 1.5, 2.0], split_loss_ratios([1.0, 2.0], 2))
    
    def test_splits_single_interval_with_steps_between(self):
        self.assertEqual([1.0, 1.25, 1.50, 1.75, 2.0],
                split_loss_ratios([1.0, 2.0], 4))
    
    def test_splits_multiple_intervals_with_a_step_between(self):
        self.assertEqual([1.0, 1.5, 2.0, 2.5, 3.0],
                split_loss_ratios([1.0, 2.0, 3.0], 2))
    
    def test_splits_multiple_intervals_with_steps_between(self):
        self.assertEqual([1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0], 
                split_loss_ratios([1.0, 2.0, 3.0], 4))    

    def test_splits_with_real_values_from_turkey(self):
        loss_ratios = [0.0, 1.96E-15, 2.53E-12, 8.00E-10, 8.31E-08, 3.52E-06,
                7.16E-05, 7.96E-04, 5.37E-03, 2.39E-02, 7.51E-02, 1.77E-01]
        
        result =  [0.0, 3.9199999999999996e-16, 7.8399999999999992e-16,
                1.1759999999999998e-15, 1.5679999999999998e-15,
                1.9599999999999999e-15, 5.0756799999999998e-13,
                1.0131759999999998e-12, 1.5187839999999998e-12,
                2.024392e-12, 2.5299999999999999e-12, 1.6202400000000001e-10,
                3.2151800000000003e-10, 4.8101199999999999e-10,
                6.4050600000000006e-10, 8.0000000000000003e-10,
                1.726e-08, 3.372e-08, 5.0179999999999997e-08,
                6.6639999999999993e-08, 8.3099999999999996e-08,
                7.7048000000000005e-07, 1.4578600000000002e-06,
                2.1452400000000005e-06, 2.8326200000000003e-06,
                3.5200000000000002e-06, 1.7136000000000003e-05,
                3.0752000000000006e-05, 4.4368000000000013e-05,
                5.7984000000000013e-05, 7.1600000000000006e-05,
                0.00021648000000000001, 0.00036136000000000002,
                0.00050624000000000003, 0.00065112000000000004,
                0.00079600000000000005, 0.0017108000000000002,
                0.0026256000000000001, 0.0035404, 0.0044552000000000003,
                0.0053699999999999998, 0.0090760000000000007, 0.012782,
                0.016487999999999999, 0.020194, 0.023900000000000001,
                0.034140000000000004, 0.044380000000000003,
                0.054620000000000002, 0.064860000000000001, 0.0751,
                0.095479999999999995, 0.11585999999999999, 0.13624,
                0.15661999999999998, 0.17699999999999999]
        
        self.assertEqual(result, split_loss_ratios(loss_ratios))

    def test_splits_with_real_values_from_taiwan(self):
        loss_ratios = [0.0, 1.877E-20, 8.485E-17, 8.427E-14,
                2.495E-11, 2.769E-09, 1.372E-07, 3.481E-06,
                5.042E-05, 4.550E-04, 2.749E-03, 1.181E-02]
        
        self.assertEqual(56, len(split_loss_ratios(loss_ratios)))

    # conditional loss test (for computing loss ratio or loss maps)

# TODO (bw): Should we check also if the curve has no values?
    def test_ratio_is_zero_if_probability_is_out_of_bounds(self):
        loss_curve = shapes.Curve({0.21: 0.131, 0.24: 0.108,
                0.27: 0.089, 0.30: 0.066})
                
        self.assertEqual(0.0, compute_conditional_loss(
                loss_curve, 0.050))
                
        self.assertEqual(0.0, compute_conditional_loss(
                loss_curve, 0.200))        

    def test_conditional_loss_computation(self):
        loss_curve = shapes.Curve({0.21: 0.131, 0.24: 0.108,
                0.27: 0.089, 0.30: 0.066})
        
        self.assertEqual(0.2526, compute_conditional_loss(loss_curve, 0.100))