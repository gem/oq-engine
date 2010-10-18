# -*- coding: utf-8 -*-

import unittest

from opengem.risk import engines
from opengem import shapes
from opengem import memcached
from opengem import identifiers

JOB_ID = 1
BLOCK_ID = 1
SITE = shapes.Site(1.0, 1.0)

class ProbabilisticEventBasedCalculatorTestCase(unittest.TestCase):
    
    def setUp(self):
        self.memcached_client = memcached.get_client(binary=False)
        self.calculator = engines.ProbabilisticEventBasedCalculator(JOB_ID, BLOCK_ID)

        self.key_exposure = identifiers.generate_product_key(JOB_ID,
                BLOCK_ID, SITE, identifiers.EXPOSURE_KEY_TOKEN)

        # delete old keys
        self.memcached_client.delete(self.key_exposure)
    
    def test_no_loss_curve_with_no_asset_value(self):
        self.assertEqual(None, self.calculator.compute_loss_curve(
                SITE, shapes.EMPTY_CURVE))
    
    def test_computes_the_loss_curve(self):
        memcached.set_value_json_encoded(
                self.memcached_client, self.key_exposure, {"AssetValue": 5.0})

        loss_ratio_curve = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        
        self.assertEqual(shapes.Curve([(0.5, 1.0), (1.0, 2.0)]), 
                self.calculator.compute_loss_curve(SITE, loss_ratio_curve))
        
    
    def test_computes_the_loss_ratio_curve(self):
        pass