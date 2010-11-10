# -*- coding: utf-8 -*-

import os
import unittest

from opengem import test
from opengem.job import Job

CONFIG_FILE = "config.gem"
CONFIG_WITH_INCLUDES = "config_with_includes.gem"

class JobTestCase(unittest.TestCase):
    def setUp(self):
        self.job = Job.from_file(os.path.join(test.DATA_DIR, CONFIG_FILE))
        self.job_with_includes = Job.from_file(os.path.join(test.DATA_DIR,
            CONFIG_WITH_INCLUDES))
    
    def test_can_create_a_job_from_config_files(self):
        self.assertEqual("ErfLogicTree.inp", self.job["ERF_LOGIC_TREE_FILE"])
        self.assertEqual("GmpeLogicTree.inp", self.job["GMPE_LOGIC_TREE_FILE"])
        self.assertEqual("~/gem_output", self.job["OUTPUT_DIR"])
        self.assertEqual("exposure.xml", self.job["EXPOSURE"])
        self.assertEqual("vulnerability.xml", self.job["VULNERABILITY"])
        self.assertEqual("loss_ratio_map.tiff", self.job["LOSS_RATIO_MAP"])
        self.assertEqual("", self.job["FILTER_REGION"])
        self.assertEqual("", self.job["OUTPUT_REGION"])
        self.assertEqual("hazard_curves.xml", self.job["HAZARD_CURVES"])
        self.assertEqual("loss_map.tiff", self.job["LOSS_MAP"])

    def test_configuration_is_the_same_no_matter_which_way_its_provided(self):
        self.assertEqual(self.job.params, self.job_with_includes.params)

    def test_a_job_has_an_identifier(self):
        self.assertEqual(1, Job({}, 1).id)
    
    def test_can_store_and_read_jobs_from_kvs(self):
        self.job.to_kvs()
        self.assertEqual(self.job, Job.from_kvs(self.job.id))
