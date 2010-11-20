#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test cases for the probablistic scenario described
in the scientific model. The values we check against are taken from
the documentation you can find at <http://to_be_defined>.
"""

import unittest

from decimal import *
from ordereddict import *

from opengem import logs
from opengem import kvs 
from opengem import shapes
from opengem import test

from opengem.parser import vulnerability
from opengem.risk.classical_psha_based import *
from opengem.risk.classical_psha_based import _compute_lrem_po, \
    _compute_lrem, _split_loss_ratios, _generate_loss_ratios, \
    _compute_loss_ratio_curve_from_lrem_po

logger = logs.RISK_LOG

# input test values
ASSET_VALUE = 5.0
INVALID_ASSET_VALUE = 0.0
HAZARD_CURVE = shapes.Curve(
    [(5.0, 0.138), (6.0, 0.099), (7.0, 0.068), (8.0, 0.041)])

LOSS_RATIO_EXCEEDANCE_MATRIX = [[0.695, 0.858, 0.990, 1.000], \
        [0.266, 0.510, 0.841, 0.999]]

class ClassicalPSHABasedMeanLossTestCase(unittest.TestCase):
    # Step One
    def setUp(self):
        # construct a loss_ratio_pe_curve with loss ratio values of
        # [0, 0.0600, 0.1200, 0.1800, 0.2400, 0.3000, 0.4500]  
        # and pe of : [0.3460, 0.1200, 0.0570, 0.0400, 0.0190, 0.0090,  0]
        # 
        self.loss_ratio_pe_curve = shapes.Curve([
            (0, 0.3460), (0.06, 0.12), (0.12, 0.057), (0.18, 0.04), 
            (0.24, 0.019), (0.3, 0.009), (0.45, 0)])
        
        self.loss_ratio_pe_mid_curve = shapes.Curve([(0.0300, 0.2330), 
            (0.0900, 0.0885), (0.1500, 0.0485), (0.2100, 0.0295), 
            (0.2700, 0.0140), (0.3750, 0.0045)])
            
        self.loss_ratio_po_curve = shapes.Curve([(0.0600, 0.1445),
        	(0.1200, 0.0400), (0.1800, 0.0190), (0.2300, 0.0155), 
        	(0.300, 0.0095)])
        
        self.loss_ratio_po_mid_curve = ([(0.0600, 0.1445), (0.1200, 0.0400), 
            (0.1800, 0.0190), (0.2400, 0.0155), (0.3000, 0.0095)])
        
    # Step Two
    # compute mean pe (PE1 + PE0 /2)
    #
    #@test.skipit
    def test_loss_ratio_pe_mid_curve_computation(self):
        
        loss_ratio_pe_mid_curve = compute_mid_mean_pe(self.loss_ratio_pe_curve)
            
        for idx, val in enumerate(self.loss_ratio_pe_mid_curve.ordinates):
            self.assertAlmostEqual(val, loss_ratio_pe_mid_curve[idx])        

    # todo BW itarate these test values one by one
      
    # Step three	
    # Compute the PO (PE1 - PE2)
    # assert that the PO values match: [0.1445, 0.0400, 0.0190, 0.0155, 0.0095]
    # 
    #@test.skipit
    def test_loss_ratio_po_computation(self):
        
        loss_ratio_po_mid_curve = compute_mid_po(
            self.loss_ratio_pe_mid_curve.ordinates)
        
        self.loss_ratio_po_curve_codomain = \
            [0.1445, 0.0400, 0.0190, 0.0155, 0.0095]
            
        for idx, val in enumerate(self.loss_ratio_po_curve_codomain):
            self.assertAlmostEqual(val, loss_ratio_po_mid_curve[idx])
            
    # todo BW itarate these test values one by one
        
    # Step four
    # compute mean loss (POn*LRn)
    # assert that the mean loss ratio =  0.023305
    #
    @test.skipit
    def test_mean_loss_ratio_computation(self):

    	mean_loss_ratio = compute_mean_loss(self.loss_ratio_po_curve, 
    	    self.loss_ratio_po_mid_curve)
    	    
    	self.mean_loss = [0.023305]
    	
    	for idx, val in enumerate(self.mean_loss):
            self.assertAlmostEqual(val, mean_loss_ratio[idx])


class ClassicalPSHABasedTestCase(unittest.TestCase):

    # loss curve tests

    def setUp(self):
        # get random ID as job_id
        self.job_id = kvs.generate_random_id()

        self.vuln_curve_code_test = "TEST"
        vuln_curve_test = shapes.Curve(
            [(5.0, (0.25, 0.5)),
             (6.0, (0.4, 0.4)),
             (7.0, (0.6, 0.3))])

        # make this a function that adds a given vuln curve dict
        # to vuln curves in memcached
        self.vulnerability_curves = vulnerability.register_vuln_curves(
            {self.vuln_curve_code_test: vuln_curve_test,
             vulnerability.EMPTY_CODE: shapes.EMPTY_CURVE}, 
            self.job_id)

    def tearDown(self):
        # flush vulnerability curves in memcache
        vulnerability.delete_vuln_curves(self.job_id)

    def test_empty_loss_curve(self):
        """Degenerate case."""
        
        self.assertEqual(compute_loss_curve(
                shapes.EMPTY_CURVE, None),
                shapes.EMPTY_CURVE)

    def test_a_loss_curve_is_not_defined_when_the_asset_is_invalid(self):
        self.assertEqual(compute_loss_curve(
                shapes.Curve([(0.1, 1.0), (0.2, 2.0), (0.3, 3.0)]),
                INVALID_ASSET_VALUE),
                shapes.EMPTY_CURVE)
    
    def test_loss_curve_computation(self):
        loss_ratio_curve = shapes.Curve([(0.1, 1.0), (0.2, 2.0), 
                                             (0.3, 3.0)])
        loss_curve = compute_loss_curve(loss_ratio_curve, ASSET_VALUE)

        self.assertEqual(shapes.Curve([
                (0.1 * ASSET_VALUE, 1.0),
                (0.2 * ASSET_VALUE, 2.0),
                (0.3 * ASSET_VALUE, 3.0)]), loss_curve)

    # loss ratio exceedance matrix * po tests
    def test_empty_matrix(self):
        """Degenerate case."""
        self.assertEqual([], _compute_lrem_po(shapes.EMPTY_CURVE,
                None, None))
        
    def test_lrem_po_computation(self):
        lrem_po = _compute_lrem_po(
            self.vulnerability_curves[self.vuln_curve_code_test], 
            LOSS_RATIO_EXCEEDANCE_MATRIX, HAZARD_CURVE)

        self.assertAlmostEquals(0.0959, lrem_po[0][0], 4)
        self.assertAlmostEquals(0.0367, lrem_po[1][0], 4)
        self.assertAlmostEquals(0.0849, lrem_po[0][1], 4)
        self.assertAlmostEquals(0.05049, lrem_po[1][1], 4)
        self.assertAlmostEquals(0.0673, lrem_po[0][2], 4)
        self.assertAlmostEquals(0.05718, lrem_po[1][2], 4)

    # loss ratio curve tests
    def test_empty_loss_ratio_curve(self):
        """Degenerate case."""
        self.assertEqual(shapes.EMPTY_CURVE, compute_loss_ratio_curve(None, []))
        
    def test_end_to_end(self):
        """These values were hand-computed by Vitor Silva."""
        hazard_curve = shapes.Curve(
            [(5.0, 0.4), (6.0, 0.2), (7.0, 0.05)])
        
        lrem = _compute_lrem(
            self.vulnerability_curves[self.vuln_curve_code_test])
        
        loss_ratio_curve = compute_loss_ratio_curve(
            self.vulnerability_curves[self.vuln_curve_code_test], 
            hazard_curve)
        
        lr_curve_expected = shapes.Curve([(0.0, 0.650), 
                                              (0.05, 0.650),
                                              (0.10, 0.632),
                                              (0.15, 0.569),
                                              (0.20, 0.477),
                                              (0.25, 0.382),
                                              (0.28, 0.330),
                                              (0.31, 0.283),
                                              (0.34, 0.241),
                                              (0.37, 0.205),
                                              (0.40, 0.173),
                                              (0.44, 0.137),
                                              (0.48, 0.108),
                                              (0.52, 0.085),
                                              (0.56, 0.066),
                                              (0.60, 0.051)])

        for x_value in lr_curve_expected.abscissae:
            self.assertAlmostEqual(lr_curve_expected.ordinate_for(x_value),
                    loss_ratio_curve.ordinate_for(x_value), 3)
    
    def test_empty_matrix(self):
        """Degenerate case."""
        # cself.assertEqual([], _compute_lrem(shapes.EMPTY_CURVE, shapes.EMPTY_CURVE))
        self.assertEqual([None], _compute_lrem(
            self.vulnerability_curves[vulnerability.EMPTY_CODE], 
            shapes.EMPTY_CURVE))
        
    # loss ratios splitting tests

    # TODO (ac): Maybe SciPy already defines something like this?
    def test_splits_single_interval_with_no_steps_between(self):
        self.assertEqual([1.0, 2.0], _split_loss_ratios([1.0, 2.0], 1))
        
    def test_splits_single_interval_with_a_step_between(self):
        self.assertEqual([1.0, 1.5, 2.0], _split_loss_ratios([1.0, 2.0], 2))
    
    def test_splits_single_interval_with_steps_between(self):
        self.assertEqual([1.0, 1.25, 1.50, 1.75, 2.0],
                _split_loss_ratios([1.0, 2.0], 4))
    
    def test_splits_multiple_intervals_with_a_step_between(self):
        self.assertEqual([1.0, 1.5, 2.0, 2.5, 3.0],
                _split_loss_ratios([1.0, 2.0, 3.0], 2))
    
    def test_splits_multiple_intervals_with_steps_between(self):
        self.assertEqual([1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0], 
                _split_loss_ratios([1.0, 2.0, 3.0], 4))    

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
        
        self.assertEqual(result, _split_loss_ratios(loss_ratios))

    def test_splits_with_real_values_from_taiwan(self):
        loss_ratios = [0.0, 1.877E-20, 8.485E-17, 8.427E-14,
                2.495E-11, 2.769E-09, 1.372E-07, 3.481E-06,
                5.042E-05, 4.550E-04, 2.749E-03, 1.181E-02]
        
        self.assertEqual(56, len(_split_loss_ratios(loss_ratios)))

    # conditional loss test (for computing loss ratio or loss maps)

    # TODO (bw): Should we check also if the curve has no values?
    def test_ratio_is_zero_if_probability_is_out_of_bounds(self):
        loss_curve = shapes.Curve([(0.21, 0.131), (0.24, 0.108),
                (0.27, 0.089), (0.30, 0.066)])
                
        self.assertEqual(0.0, compute_conditional_loss(loss_curve, 0.050))
                
        self.assertEqual(0.0, compute_conditional_loss(
                loss_curve, 0.200))        

    def test_conditional_loss_computation(self):
        loss_curve = shapes.Curve([(0.21, 0.131), (0.24, 0.108),
                (0.27, 0.089), (0.30, 0.066)])

        self.assertAlmostEqual(0.2526, 
                compute_conditional_loss(loss_curve, 0.100), 4)
