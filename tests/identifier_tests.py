import unittest

from opengem import identifiers

class IdentifierTestCase(unittest.TestCase):
    def setUp(self):
        self.job_id = 123456
        self.product = "TestProduct"
        self.block_id = 8801 # This is just an interesting number
        self.site = "Testville,TestLand"

    def test_generate_product_key_with_only_job_id_and_product(self):
        key = identifiers.generate_product_key(self.job_id, self.product)

        ev = "%s!!!%s" % (self.job_id, self.product)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_job_id_product_and_block_id(self):
        key = identifiers.generate_product_key(self.job_id, self.product, 
            self.block_id)

        ev =  "%s!%s!!%s" % (self.job_id, self.block_id, self.product)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_job_id_product_and_site(self):
        key = identifiers.generate_product_key(self.job_id, self.product, 
            site=self.site)

        ev =  "%s!!%s!%s" % (self.job_id, self.site, self.product)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_all_test_data(self):
        key = identifiers.generate_product_key(self.job_id, self.product,
            self.block_id, self.site)

        ev = "%s!%s!%s!%s" % (self.job_id, self.block_id, self.site, 
            self.product) 
        self.assertEqual(key, ev)

    def test_generate_product_key_with_tokens_from_identifiers(self):
        products = [identifiers.SITES_KEY_TOKEN, 
            identifiers.EXPOSURE_KEY_TOKEN,
            identifiers.HAZARD_CURVE_KEY_TOKEN, 
            identifiers.LOSS_CURVE_KEY_TOKEN,
            identifiers.VULNERABILITY_CURVE_KEY_TOKEN, 
            identifiers.LOSS_RATIO_CURVE_KEY_TOKEN, 
            identifiers.CONDITIONAL_LOSS_KEY_TOKEN
        ]

        for product in products:
            key = identifiers.generate_product_key(self.job_id, product,
                self.block_id, self.site)

            ev = "%s!%s!%s!%s" % (self.job_id, self.block_id, self.site,
                product)
            self.assertEqual(key, ev)
    
    def test_memcached_doesnt_support_spaces_in_keys(self):
        self.product = "A TestProduct"
        self.site = "Testville, TestLand"
        key = identifiers.generate_product_key(
                self.job_id, self.product, site=self.site)

        ev = "%s!!Testville,TestLand!ATestProduct" % self.job_id
        self.assertEqual(key, ev)
