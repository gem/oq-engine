# -*- coding: utf-8 -*-

import json
import logging
import os
import time
import unittest

from openquake import hazard
from openquake import kvs
from openquake import shapes
from openquake import test
from openquake import job
from openquake.job import mixins
from openquake.kvs import tokens
from openquake.hazard import tasks
from openquake.hazard import opensha # pylint ignore, needed for register
import openquake.hazard.job
from tests.kvs_unittest import ONE_CURVE_MODEL

MEAN_GROUND_INTENSITY='{"site":"+35.0000 +35.0000", "intensity": 1.9249e+00, \
                        "site":"+35.0500 +35.0000", "intensity": 1.9623e+00, \
                        "site":"+35.1000 +35.0000", "intensity": 2.0320e+00, \
                        "site":"+35.1500 +35.0000", "intensity": 2.0594e+00}'

TASK_JOBID_SIMPLE = ["JOB1", "JOB2", "JOB3", "JOB4"]
TEST_JOB_FILE = test.smoketest_file('simplecase/config.gem')

TEST_SOURCE_MODEL = ""
with open(test.smoketest_file('simplecase/expected_source_model.json'), 'r') as f:
    TEST_SOURCE_MODEL = f.read()

TEST_GMPE_MODEL = ""
with open(test.smoketest_file('simplecase/expected_gmpe_model.json'), 'r') as f:
    TEST_GMPE_MODEL = f.read()

def generate_job():
    jobobj = job.Job.from_file(TEST_JOB_FILE)
    return jobobj.id

# TODO(JMC): THIS IS REALLY BITROTTED, DOES NOT REPRESENT CURRENT GOLDEN PATH

class HazardEngineTestCase(unittest.TestCase):
    """The Hazard Engine is a JPype-based wrapper around OpenSHA-lite.
    Most data returned from the engine is via the KVS."""
    
    def setUp(self):
        self.generated_files = []
        self.kvs_client = kvs.get_client(binary=False)

    def tearDown(self):
        for cfg in self.generated_files:
            try:
                os.remove(cfg)
            except OSError, e:
                pass

    def test_hazard_engine_jobber_runs(self):
        """Construction of CommandLineCalculator in Java should not throw
        errors, and should have params loaded from memcached."""
        hazengine = job.Job.from_file(TEST_JOB_FILE)
        self.generated_files.append(hazengine.super_config_path)
        with mixins.Mixin(hazengine, openquake.hazard.job.HazJobMixin, key="hazard"):
            hc = hazengine.execute()
            
            source_model_key = kvs.generate_product_key(hazengine.id, 
                                kvs.tokens.SOURCE_MODEL_TOKEN)
            source_model = self.kvs_client.get(source_model_key)
            # We have the random seed in the config, so this is guaranteed
            # TODO(JMC): Add this back in
            # self.assertEqual(source_model, TEST_SOURCE_MODEL)
            
            gmpe_key = kvs.generate_product_key(hazengine.id, 
                                kvs.tokens.GMPE_TOKEN)
            gmpe_model = self.kvs_client.get(gmpe_key)
            # TODO(JMC): Add this back in
            # self.assertEqual(gmpe_model, TEST_GMPE_MODEL)
    
    def test_generate_hazard_curves_using_classical_psha(self): 
        
        def verify_order_of_haz_curve_keys(hazengine, result_keys):
            """ The classical PSHA execute() returns a list of keys 
            for the curves stored to the KVS. We need to make sure
            the order is correct. """
            print "job id (hazengine id) is", hazengine.id 
            
            expected_keys = []
            realizations = int(hazengine.params['NUMBER_OF_LOGIC_TREE_SAMPLES'])
            print "dir of hazengine is", dir(hazengine)
            for realization in range(0, realizations):    
                for site_list in hazengine.site_list_generator():
                    for site in site_list:
                        key = tokens.hazard_curve_key(hazengine.id,
                                                      realization,
                                                      site.longitude,
                                                      site.latitude) 
                        expected_keys.append(key) 
            self.assertEqual(expected_keys, result_keys)

        def verify_haz_curves_stored_to_kvs(result_keys):
            """ This just tests to make sure there something in the KVS
            for each key in given list of keys. This does NOT test the
            actual results. """
            # TODO (LB): At some point we need to test the actual 
            # results to verify they are correct
            for key in result_keys:
                value = self.kvs_client.get(key)
                print "kvs value is", value
                self.assertTrue(value != None) 

        test_file_path = "smoketests/classical_psha_simple/config.gem"
        hazengine = job.Job.from_file(test_file_path)
        
        with mixins.Mixin(hazengine, openquake.hazard.job.HazJobMixin, key="hazard"):
            result_keys = hazengine.execute()
            verify_order_of_haz_curve_keys(hazengine, result_keys)
            verify_haz_curves_stored_to_kvs(result_keys)

    def test_basic_generate_erf_keeps_order(self):
        results = []
        for job_id in TASK_JOBID_SIMPLE:
            results.append(tasks.generate_erf.delay(job_id))

        self.assertEqual(TASK_JOBID_SIMPLE,
                         [result.get() for result in results])

    def test_generate_erf_returns_erf_via_memcached(self):
        results = []
        result_keys = []
        expected_values = {}

        print kvs.tokens.ERF_KEY_TOKEN
        
        for job_id in TASK_JOBID_SIMPLE:
            erf_key = kvs.generate_product_key(job_id, kvs.tokens.ERF_KEY_TOKEN)

            # Build the expected values
            expected_values[erf_key] = json.JSONEncoder().encode([job_id])

            # Get our result keys
            result_keys.append(erf_key)

            # Spawn our tasks.
            results.append(tasks.generate_erf.apply_async(args=[job_id]))

        test.wait_for_celery_tasks(results)

        result_values = self.kvs_client.get_multi(result_keys)

        self.assertEqual(result_values, expected_values)

    @test.skipit
    def test_compute_hazard_curve_all_sites(self):
        results = []
        block_id = 8801
        for job_id in TASK_JOBID_SIMPLE:
            self._prepopulate_sites_for_block(job_id, block_id)
            results.append(tasks.compute_hazard_curve.apply_async(
                args=[job_id, block_id]))

        test.wait_for_celery_tasks(results)

        for result in results:
            for res in result.get():
                self.assertEqual(res, ONE_CURVE_MODEL)

    def test_compute_mgm_intensity(self):
        results = []
        block_id = 8801
        site = "Testville,TestLand"
    
        mgm_intensity = json.JSONDecoder().decode(MEAN_GROUND_INTENSITY)

        for job_id in TASK_JOBID_SIMPLE:
            mgm_key = kvs.generate_product_key(job_id, kvs.tokens.MGM_KEY_TOKEN, 
                block_id, site)
            self.kvs_client.set(mgm_key, MEAN_GROUND_INTENSITY)

            results.append(tasks.compute_mgm_intensity.apply_async(
                args=[job_id, block_id, site]))

        test.wait_for_celery_tasks(results)

        for result in results:
            self.assertEqual(mgm_intensity, result.get())

    def _prepopulate_sites_for_block(self, job_id, block_id):
        sites = ["Testville,TestLand", "Provaville,TestdiTerra",
                 "Teststadt,Landtesten", "villed'essai,paystest"]
        sites_key = kvs.generate_sites_key(job_id, block_id)

        self.kvs_client.set(sites_key, json.JSONEncoder().encode(sites))

        for site in sites:
            site_key = kvs.generate_product_key(job_id,
                kvs.tokens.HAZARD_CURVE_KEY_TOKEN, block_id, site) 

            self.kvs_client.set(site_key, ONE_CURVE_MODEL)


if __name__ == '__main__':
    import unittest
    unittest.main()
