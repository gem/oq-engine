# -*- coding: utf-8 -*-

import os
import unittest

from opengem import test
from opengem import config

RISK_CONFIG_FILE = "risk-config.gem"
HAZARD_CONFIG_FILE = "hazard-config.gem"


def fname():
    """docstring for fname"""
    pass

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
    
    def test_can_store_and_read_jobs_from_kvs(self):
        self.job.to_kvs()
        self.assertEqual(self.job, config.Job.from_kvs(self.job.id))
    
    def test_is_invalid_with_no_region_and_exposure(self):
        self.job = config.Job({})
        self.assertFalse(self._decorated_function()())

        # parameters defined, but empty
        self.job = config.Job({config.EXPOSURE: "", config.INPUT_REGION: ""})
        self.assertFalse(self._decorated_function()())
        
        # parameters defined
        self.job = config.Job({config.EXPOSURE: "exposure.xml"})
        self.assertTrue(self._decorated_function()())
        
        self.job = config.Job({config.INPUT_REGION: "region.file"})
        self.assertTrue(self._decorated_function()())
        
        self.job = config.Job({
                config.EXPOSURE: "exposure.xml",
                config.INPUT_REGION: "region.file"})

        self.assertTrue(self._decorated_function()())
    
    def _decorated_function(self):
        @self.job.validate
        def f():
            return True
        
        return f