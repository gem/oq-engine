import unittest
from opengem import hazard
from opengem import kvs
from opengem import risk
from opengem.parser import vulnerability

class IdentifierTestCase(unittest.TestCase):
    def setUp(self):
        self.job_id = 123456
        self.product = "TestProduct"
        self.block_id = 8801 # This is just an interesting number
        self.site = "Testville,TestLand"

    def test_generate_product_key_with_only_job_id_and_product(self):
        key = kvs.generate_product_key(self.job_id, self.product)

        ev = "%s!!!%s" % (self.job_id, self.product)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_job_id_product_and_block_id(self):
        key = kvs.generate_product_key(self.job_id, self.product, self.block_id)

        ev =  "%s!%s!!%s" % (self.job_id, self.block_id, self.product)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_job_id_product_and_site(self):
        key = kvs.generate_product_key(self.job_id, self.product, 
            site=self.site)

        ev =  "%s!!%s!%s" % (self.job_id, self.site, self.product)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_all_test_data(self):
        key = kvs.generate_product_key(self.job_id, self.product, self.block_id,
            self.site)

        ev = "%s!%s!%s!%s" % (self.job_id, self.block_id, self.site, 
            self.product) 
        self.assertEqual(key, ev)

    def test_generate_product_key_with_tokens_from_kvs(self):
        products = [
            hazard.ERF_KEY_TOKEN,
            hazard.MGM_KEY_TOKEN,
            hazard.HAZARD_CURVE_KEY_TOKEN,
            risk.CONDITIONAL_LOSS_KEY_TOKEN,
            risk.EXPOSURE_KEY_TOKEN,
            risk.GMF_KEY_TOKEN,
            risk.LOSS_RATIO_CURVE_KEY_TOKEN,
            risk.LOSS_CURVE_KEY_TOKEN,
            vulnerability.VULNERABILITY_CURVE_KEY_TOKEN,
        ]

        for product in products:
            key = kvs.generate_product_key(self.job_id, product,
                self.block_id, self.site)

            ev = "%s!%s!%s!%s" % (self.job_id, self.block_id, self.site,
                product)
            self.assertEqual(key, ev)
    
    def test_memcached_doesnt_support_spaces_in_keys(self):
        self.product = "A TestProduct"
        self.site = "Testville, TestLand"
        key = kvs.generate_product_key(self.job_id, self.product, 
            site=self.site)

        ev = "%s!!Testville,TestLand!ATestProduct" % self.job_id
        self.assertEqual(key, ev)
