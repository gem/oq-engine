# -*- coding: utf-8 -*-

import unittest


from opengem import risk
from opengem import shapes
from opengem import kvs 
from opengem.parser import vulnerability
from opengem.risk import engines

JOB_ID = 1
BLOCK_ID = 1
SITE = shapes.Site(1.0, 1.0)

GMF = {"IMLs": (0.079888, 0.273488, 0.115856, 0.034912, 0.271488, 0.00224,
        0.04336, 0.099552, 0.071968, 0.003456, 0.030704, 0.011744,
        0.024176, 0.002224, 0.008912, 0.004224, 0.033584, 0.041088,
        0.012864, 0.001728, 0.06648, 0.000736, 0.01992, 0.011616,
        0.001104, 0.033264, 0.021552, 0.055088, 0.00176, 0.001088, 0.041872,
        0.005152, 0.007424, 0.002464, 0.008496, 0.019744, 0.025136, 0.005552,
        0.00168, 0.00704, 0.00272, 0.081328, 0.001408, 0.025568, 0.051376,
        0.003456, 0.01208, 0.002496, 0.001152, 0.007552, 0.004944, 0.024944,
        0.01168, 0.027408, 0.00504, 0.003136, 0.20608, 0.00344, 0.01448,
        0.03664, 0.124992, 0.005024, 0.007536, 0.015696, 0.00608,
        0.001248, 0.005744, 0.017328, 0.002272, 0.06384, 0.029104,
        0.001152, 0.016384, 0.002096, 0.00328, 0.004304, 0.020544,
        0.000768, 0.011456, 0.004528, 0.024688, 0.024304, 0.126928,
        0.002416, 0.0032, 0.024768, 0.00608, 0.02544, 0.003392,
        0.381296, 0.013808, 0.002256, 0.181776, 0.038912, 0.023888,
        0.002848, 0.014176, 0.001936, 0.089408, 0.001008, 0.02152,
        0.002464, 0.00464, 0.064384, 0.001712, 0.01584, 0.012544,
        0.028128, 0.005808, 0.004928, 0.025536, 0.008304, 0.112528,
        0.06472, 0.01824, 0.002624, 0.003456, 0.014832, 0.002592,
        0.041264, 0.004368, 0.016144, 0.008032, 0.007344, 0.004976, 
        0.00072, 0.022192, 0.002496, 0.001456, 0.044976, 0.055424,
        0.009232, 0.010368, 0.000944, 0.002976, 0.00656, 0.003184,
        0.004288, 0.00632, 0.286512, 0.007568, 0.00104, 0.00144,
        0.004896, 0.053248, 0.046144, 0.0128, 0.033072, 0.02968,
        0.002096, 0.021008, 0.017536, 0.000656, 0.016032, 0.012768,
        0.002752, 0.007392, 0.007072, 0.044112, 0.023072, 0.013232,
        0.001824, 0.020064, 0.008912, 0.039504, 0.00144, 0.000816,
        0.008544, 0.077056, 0.113984, 0.001856, 0.053024, 0.023792,
        0.013056, 0.0084, 0.009392, 0.010928, 0.041904, 0.000496,
        0.041936, 0.035664, 0.03176, 0.003552, 0.00216, 0.0476, 0.028944,
        0.006832, 0.011136, 0.025712, 0.006368, 0.004672, 0.001312,
        0.008496, 0.069136, 0.011568, 0.01576, 0.01072, 0.002336,
        0.166192, 0.00376, 0.013216, 0.000592, 0.002832, 0.052928,
        0.007872, 0.001072, 0.021136, 0.029568, 0.012944, 0.004064,
        0.002336, 0.010832, 0.10104, 0.00096, 0.01296, 0.037104),
        "TSES": 900, "TimeSpan": 50}

class ProbabilisticEventBasedCalculatorTestCase(unittest.TestCase):
    
    def setUp(self):
        self.memcached_client = kvs.get_client(binary=False)
        self.calculator = engines.ProbabilisticEventBasedCalculator(JOB_ID, BLOCK_ID)

        self.key_exposure = kvs.generate_product_key(JOB_ID,
            risk.EXPOSURE_KEY_TOKEN, BLOCK_ID, SITE)

        self.key_gmf = kvs.generate_product_key(JOB_ID,
            risk.GMF_KEY_TOKEN, BLOCK_ID, SITE)

        # delete old keys
        self.memcached_client.delete(self.key_exposure)
        self.memcached_client.delete(vulnerability.generate_memcache_key(JOB_ID))
        self.memcached_client.delete(self.key_gmf)
    
    def test_no_loss_curve_with_no_asset_value(self):
        self.assertEqual(None, self.calculator.compute_loss_curve(
                SITE, shapes.EMPTY_CURVE))
    
    def test_computes_the_loss_curve(self):
        kvs.set_value_json_encoded(
                self.memcached_client, self.key_exposure, {"AssetValue": 5.0})

        loss_ratio_curve = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        
        self.assertEqual(shapes.Curve([(0.5, 1.0), (1.0, 2.0)]), 
                self.calculator.compute_loss_curve(SITE, loss_ratio_curve))
        
    def test_computes_the_loss_ratio_curve(self):
        # saving in memcached the vuln function
        vuln_curve = self.vuln_function = shapes.Curve([
                (0.01, (0.001, 1.00)), (0.04, (0.022, 1.0)), 
                (0.07, (0.051, 1.0)), (0.10, (0.080, 1.0)),
                (0.12, (0.100, 1.0)), (0.22, (0.200, 1.0)),
                (0.37, (0.405, 1.0)), (0.52, (0.700, 1.0))])
        
        # ugly, it shouldn't take the json format
        vulnerability.write_vulnerability_curves_to_memcache(
                self.memcached_client, JOB_ID, {"Type1": vuln_curve.to_json()})
        
        # recreate the calculator to get the vuln function
        calculator = engines.ProbabilisticEventBasedCalculator(JOB_ID, BLOCK_ID)
        
        # saving the exposure
        kvs.set_value_json_encoded(
                self.memcached_client, self.key_exposure, {"AssetValue": 5.0,
                "VulnerabilityFunction": "Type1"})
        
        # saving the ground motion field
        kvs.set_value_json_encoded(self.memcached_client, self.key_gmf, GMF)
        
        # manually computed curve
        expected_curve = shapes.Curve([
                (0.014583333333333332, 0.99999385578764666),
                (0.043749999999999997, 0.82133133505033484),
                (0.072916666666666657, 0.61110443601077713),
                (0.10208333333333333, 0.48658288096740798),
                (0.13124999999999998, 0.32219042199454972),
                (0.16041666666666665, 0.32219042199454972),
                (0.18958333333333333, 0.24253487160303355),
                (0.21874999999999997, 0.19926259708319194),
                (0.24791666666666662, 0.19926259708319194),
                (0.27708333333333329, 0.19926259708319194),
                (0.30624999999999997, 0.054040531093234589),
                (0.33541666666666664, 0.054040531093234589),
                (0.36458333333333331, 0.054040531093234589),
                (0.39374999999999993, 0.054040531093234589),
                (0.42291666666666661, 0.054040531093234589),
                (0.45208333333333328, 0.0), (0.48124999999999996, 0.0),
                (0.5395833333333333, 0.0), (0.59791666666666665, 0.0),
                (0.51041666666666663, 0.0), (0.56874999999999987, 0.0),
                (0.62708333333333321, 0.0), (0.65625, 0.0),
                (0.68541666666666656, 0.0)])
        
        self.assertEqual(expected_curve, calculator.compute_loss_ratio_curve(SITE))
