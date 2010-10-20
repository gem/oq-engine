# -*- coding: utf-8 -*-

import os
import unittest

from opengem import test
from opengem import config
from opengem import identifiers
from opengem import memcached

RISK_CONFIG_FILE = "risk-config.gem"
HAZARD_CONFIG_FILE = "hazard-config.gem"

class ConfigTestCase(unittest.TestCase):
    
    def setUp(self):
        self.reader = config.Config(os.path.join(test.DATA_DIR, 
                RISK_CONFIG_FILE), os.path.join(test.DATA_DIR, 
                HAZARD_CONFIG_FILE))
    
    def test_reads_hazard_configuration_file(self):
        self.assertEqual(3, len(self.reader.hazard))
        self.assertEqual("ErfLogicTree.inp", self.reader["ERF_LOGIC_TREE_FILE"])
        self.assertEqual("GmpeLogicTree.inp", self.reader["GMPE_LOGIC_TREE_FILE"])
        self.assertEqual("~/gem_output", self.reader["OUTPUT_DIR"])
    
    def test_reads_risk_configuration_file(self):
        self.assertEqual(7, len(self.reader.risk))
        self.assertEqual("exposure.xml", self.reader["EXPOSURE"])
        self.assertEqual("vulnerability.xml", self.reader["VULNERABILITY"])
        self.assertEqual("loss_ratio_map.tiff", self.reader["LOSS_RATIO_MAP"])
    
    def test_an_exception_is_raised_with_unknown_key(self):
        self.assertRaises(ValueError, self.reader.__getitem__, "UNKNOWN_KEY")

    def test_generates_a_new_job(self):
        job = self.reader.generate_job(1)
        self.assertEqual("JOB%s1" % identifiers.MEMCACHE_KEY_SEPARATOR, job["JOB_ID"])
        
        # 3 hazard parameters defined, 7 risk parameters defined and the job id
        self.assertEqual(11, len(job))
        
        self.assertEqual("vulnerability.xml", job["vulnerability"])
        self.assertEqual("GmpeLogicTree.inp", job["gmpe_logic_tree_file"])
    
    def test_stores_a_new_job_in_memcached(self):
        memcached_client = memcached.get_client(binary=False)
        self.reader.generate_and_store_job(1)
        self.assertEqual(self.reader.generate_job(1), config.Config.job_with_id(1))
