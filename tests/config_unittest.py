# -*- coding: utf-8 -*-

import os
import unittest

from opengem import test
from opengem import config

RISK_CONFIG_FILE = "risk-config.gem"
HAZARD_CONFIG_FILE = "hazard-config.gem"

class JobTestCase(unittest.TestCase):
    
    def setUp(self):
        self.job = config.Job.from_files(os.path.join(test.DATA_DIR, 
                RISK_CONFIG_FILE), os.path.join(test.DATA_DIR, 
                HAZARD_CONFIG_FILE))
    
    def test_can_create_a_job_from_config_files(self):
        self.assertEqual("ErfLogicTree.inp", self.job["erf_logic_tree_file"])
        self.assertEqual("GmpeLogicTree.inp", self.job["gmpe_logic_tree_file"])
        self.assertEqual("~/gem_output", self.job["output_dir"])
        self.assertEqual("exposure.xml", self.job["exposure"])
        self.assertEqual("vulnerability.xml", self.job["vulnerability"])
        self.assertEqual("loss_ratio_map.tiff", self.job["loss_ratio_map"])
        self.assertEqual("", self.job["filter_region"])
        self.assertEqual("", self.job["output_region"])
        self.assertEqual("hazard_curves.xml", self.job["hazard_curves"])
        self.assertEqual("loss_map.tiff", self.job["loss_map"])

    def test_a_job_has_an_identifier(self):
        self.assertEqual(1, config.Job({}, 1).id)
    
    def test_can_store_and_read_jobs_from_memcached(self):
        self.job.to_kvs()
        self.assertEqual(self.job, config.Job.from_kvs(self.job.id))
    
    def test_is_invalid_with_no_region_and_exposure(self):
        # no parameters
        self.assertFalse(config.Job({}).is_valid())

        # parameters defined, but empty
        self.assertFalse(config.Job({config.EXPOSURE: "",
                config.INPUT_REGION: ""}).is_valid())
        
        # parameters defined
        self.assertTrue(config.Job({
                config.EXPOSURE: "exposure.xml"}).is_valid())
        
        self.assertTrue(config.Job({
                config.EXPOSURE: "",
                config.INPUT_REGION: "region.file"}).is_valid())
        
        self.assertTrue(config.Job({
                config.EXPOSURE: "exposure.xml",
                config.INPUT_REGION: "region.file"}).is_valid())