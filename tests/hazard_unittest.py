# -*- coding: utf-8 -*-

import json
import logging
import os
import time
import unittest
import numpy

from openquake import hazard
from openquake import kvs
from openquake import shapes
from openquake import test
from openquake import job
from openquake.job import mixins
from openquake.kvs import tokens
from openquake.hazard import tasks
from openquake.hazard import classical_psha
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
        errors, and should have params loaded from kvs."""

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

    def test_generate_erf_returns_erf_via_kvs(self):
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


class MeanHazardCurveComputationTestCase(unittest.TestCase):

    def setUp(self):
        self.job_id = 1234

        self.expected_mean_curve = numpy.array([9.8542200e-01, 9.8196600e-01,
                9.5842000e-01, 9.2639600e-01, 8.6713000e-01, 7.7081800e-01,
                6.3448600e-01, 4.7256800e-01, 3.3523400e-01, 3.1255000e-01,
                1.7832000e-01, 9.0883400e-02, 4.2189200e-02, 1.7874200e-02,
                6.7449200e-03, 2.1658200e-03, 5.3878600e-04, 9.4369400e-05,
                8.9830380e-06])

        self.empty_curve = {"curve": []}

        # deleting server side cached data
        kvs.flush()

    def test_process_the_curves_for_a_single_site(self):
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), self.empty_curve)
        
        self._run([shapes.Site(2.0, 5.0)])

        self._has_computed_mean_curve_for_site(shapes.Site(2.0, 5.0))
    
    def test_process_the_curves_for_multiple_sites(self):
        self._store_hazard_curve_at(shapes.Site(1.5, 1.0), self.empty_curve)
        self._store_hazard_curve_at(shapes.Site(2.0, 1.0), self.empty_curve)
        self._store_hazard_curve_at(shapes.Site(1.5, 1.5), self.empty_curve)
        self._store_hazard_curve_at(shapes.Site(2.0, 1.5), self.empty_curve)
        
        self._run([shapes.Site(1.5, 1.0), shapes.Site(2.0, 1.0), 
                shapes.Site(1.5, 1.5), shapes.Site(2.0, 1.5)])

        self._has_computed_mean_curve_for_site(shapes.Site(1.5, 1.0))
        self._has_computed_mean_curve_for_site(shapes.Site(2.0, 1.0))
        self._has_computed_mean_curve_for_site(shapes.Site(1.5, 1.5))
        self._has_computed_mean_curve_for_site(shapes.Site(2.0, 1.5))
    
    def test_computes_the_mean_curve(self):
        hazard_curve_1 = numpy.array([9.8161000e-01, 9.7837000e-01,
                9.5579000e-01, 9.2555000e-01, 8.7052000e-01, 7.8214000e-01,
                6.5708000e-01, 5.0526000e-01, 3.7044000e-01, 3.4740000e-01,
                2.0502000e-01, 1.0506000e-01, 4.6531000e-02, 1.7548000e-02,
                5.4791000e-03, 1.3377000e-03, 2.2489000e-04, 2.2345000e-05,
                4.2696000e-07])

        hazard_curve_2 = numpy.array([9.7309000e-01, 9.6857000e-01,
                9.3853000e-01, 9.0089000e-01, 8.3673000e-01, 7.4057000e-01,
                6.1272000e-01, 4.6467000e-01, 3.3694000e-01, 3.1536000e-01,
                1.8340000e-01, 9.2412000e-02, 4.0202000e-02, 1.4900000e-02,
                4.5924000e-03, 1.1126000e-03, 1.8647000e-04, 1.8882000e-05,
                4.7123000e-07])
    
        hazard_curve_3 = numpy.array([9.9178000e-01, 9.8892000e-01,
                9.6903000e-01, 9.4030000e-01, 8.8405000e-01, 7.8782000e-01,
                6.4627000e-01, 4.7537000e-01, 3.3168000e-01, 3.0827000e-01,
                1.7279000e-01, 8.8360000e-02, 4.2766000e-02, 1.9643000e-02,
                8.1923000e-03, 2.9157000e-03, 7.9955000e-04, 1.5233000e-04,
                1.5582000e-05])

        hazard_curve_4 = numpy.array([9.8885000e-01, 9.8505000e-01,
                9.5972000e-01, 9.2494000e-01, 8.6030000e-01, 7.5574000e-01,
                6.1009000e-01, 4.4217000e-01, 3.0543000e-01, 2.8345000e-01,
                1.5760000e-01, 8.0225000e-02, 3.8681000e-02, 1.7637000e-02,
                7.2685000e-03, 2.5474000e-03, 6.8347000e-04, 1.2596000e-04,
                1.2853000e-05])

        hazard_curve_5 = numpy.array([9.9178000e-01, 9.8892000e-01,
                9.6903000e-01, 9.4030000e-01, 8.8405000e-01, 7.8782000e-01,
                6.4627000e-01, 4.7537000e-01, 3.3168000e-01, 3.0827000e-01,
                1.7279000e-01, 8.8360000e-02, 4.2766000e-02, 1.9643000e-02,
                8.1923000e-03, 2.9157000e-03, 7.9955000e-04, 1.5233000e-04,
                1.5582000e-05])
    
        mean_hazard_curve = classical_psha.compute_mean_curve([
                hazard_curve_1, hazard_curve_2, hazard_curve_3,
                hazard_curve_4, hazard_curve_5])

        self.assertTrue(numpy.allclose(
                self.expected_mean_curve, mean_hazard_curve))

    def test_an_empty_hazard_curve_produces_an_empty_mean_curve(self):
        hazard_curve = {"site_lon": 2.0, "site_lat": 5.0, "curve": []}
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve)

        self._run([shapes.Site(2.0, 5.0)])

        result = kvs.get_value_json_decoded(
                kvs.tokens.mean_hazard_curve_key(
                self.job_id, shapes.Site(2.0, 5.0)))

        # site is correct
        self.assertEqual(2.0, result["site_lon"])
        self.assertEqual(5.0, result["site_lat"])
        
        # no values
        self.assertTrue(numpy.allclose([], numpy.array(result["curve"])))

    def test_reads_and_stores_the_mean_curve_in_kvs(self):
        hazard_curve_1 = {"site_lon": 2.0, "site_lat": 5.0, "curve": [
                {"y": 9.8161000e-01, "x": 0}, {"y": 9.7837000e-01, "x": 0},
                {"y": 9.5579000e-01, "x": 0}, {"y": 9.2555000e-01, "x": 0},
                {"y": 8.7052000e-01, "x": 0}, {"y": 7.8214000e-01, "x": 0},
                {"y": 6.5708000e-01, "x": 0}, {"y": 5.0526000e-01, "x": 0},
                {"y": 3.7044000e-01, "x": 0}, {"y": 3.4740000e-01, "x": 0},
                {"y": 2.0502000e-01, "x": 0}, {"y": 1.0506000e-01, "x": 0},
                {"y": 4.6531000e-02, "x": 0}, {"y": 1.7548000e-02, "x": 0},
                {"y": 5.4791000e-03, "x": 0}, {"y": 1.3377000e-03, "x": 0},
                {"y": 2.2489000e-04, "x": 0}, {"y": 2.2345000e-05, "x": 0},
                {"y": 4.2696000e-07, "x": 0}]}

        hazard_curve_2 = {"site_lon": 2.0, "site_lat": 5.0, "curve": [
                {"y": 9.7309000e-01, "x": 0}, {"y": 9.6857000e-01, "x": 0},
                {"y": 9.3853000e-01, "x": 0}, {"y": 9.0089000e-01, "x": 0},
                {"y": 8.3673000e-01, "x": 0}, {"y": 7.4057000e-01, "x": 0},
                {"y": 6.1272000e-01, "x": 0}, {"y": 4.6467000e-01, "x": 0},
                {"y": 3.3694000e-01, "x": 0}, {"y": 3.1536000e-01, "x": 0},
                {"y": 1.8340000e-01, "x": 0}, {"y": 9.2412000e-02, "x": 0},
                {"y": 4.0202000e-02, "x": 0}, {"y": 1.4900000e-02, "x": 0},
                {"y": 4.5924000e-03, "x": 0}, {"y": 1.1126000e-03, "x": 0},
                {"y": 1.8647000e-04, "x": 0}, {"y": 1.8882000e-05, "x": 0},
                {"y": 4.7123000e-07, "x": 0}]}
    
        hazard_curve_3 = {"site_lon": 2.0, "site_lat": 5.0, "curve": [
                {"y": 9.9178000e-01, "x": 0}, {"y": 9.8892000e-01, "x": 0},
                {"y": 9.6903000e-01, "x": 0}, {"y": 9.4030000e-01, "x": 0},
                {"y": 8.8405000e-01, "x": 0}, {"y": 7.8782000e-01, "x": 0},
                {"y": 6.4627000e-01, "x": 0}, {"y": 4.7537000e-01, "x": 0},
                {"y": 3.3168000e-01, "x": 0}, {"y": 3.0827000e-01, "x": 0},
                {"y": 1.7279000e-01, "x": 0}, {"y": 8.8360000e-02, "x": 0},
                {"y": 4.2766000e-02, "x": 0}, {"y": 1.9643000e-02, "x": 0},
                {"y": 8.1923000e-03, "x": 0}, {"y": 2.9157000e-03, "x": 0},
                {"y": 7.9955000e-04, "x": 0}, {"y": 1.5233000e-04, "x": 0},
                {"y": 1.5582000e-05, "x": 0}]}

        hazard_curve_4 = {"site_lon": 2.0, "site_lat": 5.0, "curve": [
                {"y": 9.8885000e-01, "x": 0}, {"y": 9.8505000e-01, "x": 0},
                {"y": 9.5972000e-01, "x": 0}, {"y": 9.2494000e-01, "x": 0},
                {"y": 8.6030000e-01, "x": 0}, {"y": 7.5574000e-01, "x": 0},
                {"y": 6.1009000e-01, "x": 0}, {"y": 4.4217000e-01, "x": 0},
                {"y": 3.0543000e-01, "x": 0}, {"y": 2.8345000e-01, "x": 0},
                {"y": 1.5760000e-01, "x": 0}, {"y": 8.0225000e-02, "x": 0},
                {"y": 3.8681000e-02, "x": 0}, {"y": 1.7637000e-02, "x": 0},
                {"y": 7.2685000e-03, "x": 0}, {"y": 2.5474000e-03, "x": 0},
                {"y": 6.8347000e-04, "x": 0}, {"y": 1.2596000e-04, "x": 0},
                {"y": 1.2853000e-05, "x": 0}]}

        hazard_curve_5 = {"site_lon": 2.0, "site_lat": 5.0, "curve": [
                {"y": 9.9178000e-01, "x": 0}, {"y": 9.8892000e-01, "x": 0},
                {"y": 9.6903000e-01, "x": 0}, {"y": 9.4030000e-01, "x": 0},
                {"y": 8.8405000e-01, "x": 0}, {"y": 7.8782000e-01, "x": 0},
                {"y": 6.4627000e-01, "x": 0}, {"y": 4.7537000e-01, "x": 0},
                {"y": 3.3168000e-01, "x": 0}, {"y": 3.0827000e-01, "x": 0},
                {"y": 1.7279000e-01, "x": 0}, {"y": 8.8360000e-02, "x": 0},
                {"y": 4.2766000e-02, "x": 0}, {"y": 1.9643000e-02, "x": 0},
                {"y": 8.1923000e-03, "x": 0}, {"y": 2.9157000e-03, "x": 0},
                {"y": 7.9955000e-04, "x": 0}, {"y": 1.5233000e-04, "x": 0},
                {"y": 1.5582000e-05, "x": 0}]}
        
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_1, 1)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_2, 2)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_3, 3)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_4, 4)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_5, 5)
        
        self._run([shapes.Site(2.0, 5.0)])

        result = kvs.get_value_json_decoded(
                kvs.tokens.mean_hazard_curve_key(
                self.job_id, shapes.Site(2.0, 5.0)))

        # site is correct
        self.assertEqual(2.0, result["site_lon"])
        self.assertEqual(5.0, result["site_lat"])
        
        # values are correct
        self.assertTrue(numpy.allclose(self.expected_mean_curve,
                numpy.array(result["curve"])))

    def test_end_to_end(self):
        test_file_path = "smoketests/classical_psha_simple/config.gem"
        engine = job.Job.from_file(test_file_path)

        with mixins.Mixin(engine,
                openquake.hazard.job.HazJobMixin, key="hazard"):

            engine.execute()

# TODO (ac): Find out a better way to do this...
        time.sleep(1)
        
        self.assertTrue(len(kvs.mget("%s*%s*" % (
                kvs.tokens.MEAN_HAZARD_CURVE_KEY_TOKEN, engine.id))) > 0)

    def _run(self, sites):
        classical_psha.compute_mean_hazard_curves(
                self.job_id, sites)

    def _store_hazard_curve_at(self, site, curve, realization=1):
        kvs.set_value_json_encoded(
                kvs.tokens.hazard_curve_key(self.job_id, realization,
                site.longitude, site.latitude), curve)

    def _has_computed_mean_curve_for_site(self, site):
        self.assertTrue(kvs.get(kvs.tokens.mean_hazard_curve_key(
                self.job_id, site)) != None)


class QuantileHazardCurveComputationTestCase(unittest.TestCase):
    
    def setUp(self):
        self.job_id = 1234
        
        self.params = {}
        self.quantiles_levels = classical_psha.QUANTILE_PARAM_NAME
        self.engine = job.Job(self.params,  self.job_id)

        self.expected_curve = numpy.array([9.9178000e-01, 9.8892000e-01,
                9.6903000e-01, 9.4030000e-01, 8.8405000e-01, 7.8782000e-01,
                6.4897250e-01, 4.8284250e-01, 3.4531500e-01, 3.2337000e-01,
                1.8880500e-01, 9.5574000e-02, 4.3707250e-02, 1.9643000e-02,
                8.1923000e-03, 2.9157000e-03, 7.9955000e-04, 1.5233000e-04,
                1.5582000e-05])

        # deleting server side cached data
        kvs.flush()

    def test_no_computation_when_no_parameter_specified(self):
        self._run([])

        self._no_stored_values_for("%s" %
                kvs.tokens.QUANTILE_HAZARD_CURVE_KEY_TOKEN)

    def test_no_computation_when_the_parameter_is_empty(self):
        self.params[self.quantiles_levels] = ""
        self._run([])

        self._no_stored_values_for("%s" %
                kvs.tokens.QUANTILE_HAZARD_CURVE_KEY_TOKEN)

    def test_computes_all_the_levels_specified(self):
        self.params[self.quantiles_levels] = "0.25 0.50 0.75"
        self._run([shapes.Site(2.0, 5.0)])

        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.25)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.75)

    def test_computes_just_the_quantiles_in_range(self):
        self.params[self.quantiles_levels] = \
                "-0.33 0.00 0.25 0.50 0.75 1.00 1.10"

        self._run([shapes.Site(2.0, 5.0)])

        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.00)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.25)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.75)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 1.00)

        self._no_computed_quantiles_for(1.10)
        self._no_computed_quantiles_for(0.33)

    def test_just_numeric_values_are_allowed(self):
        self.params[self.quantiles_levels] = \
                "-0.33 0.00 XYZ 0.50 ;;; 1.00 BBB"

        self._run([shapes.Site(2.0, 5.0)])
        
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.00)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 1.00)

        self._no_computed_quantiles_for(0.33)

    def test_accepts_also_signs(self):
        self.params[self.quantiles_levels] = "-0.33 +0.0 XYZ +0.5 +1.00"
        self._run([shapes.Site(2.0, 5.0)])

        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.00)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 5.0), 1.00)

    def test_process_all_the_sites_given(self):
        self.params[self.quantiles_levels] = "0.25 0.50"

        self._run([shapes.Site(1.5, 1.0), shapes.Site(2.0, 1.0),
                shapes.Site(1.5, 1.5), shapes.Site(2.0, 1.5)])

        self._has_computed_quantile_for_site(shapes.Site(1.5, 1.0), 0.25)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 1.0), 0.25)
        self._has_computed_quantile_for_site(shapes.Site(1.5, 1.5), 0.25)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 1.5), 0.25)

        self._has_computed_quantile_for_site(shapes.Site(1.5, 1.0), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 1.0), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(1.5, 1.5), 0.50)
        self._has_computed_quantile_for_site(shapes.Site(2.0, 1.5), 0.50)

    def test_computes_the_quantile_curve(self):
        hazard_curve_1 = numpy.array([9.8161000e-01, 9.7837000e-01,
                9.5579000e-01, 9.2555000e-01, 8.7052000e-01, 7.8214000e-01,
                6.5708000e-01, 5.0526000e-01, 3.7044000e-01, 3.4740000e-01,
                2.0502000e-01, 1.0506000e-01, 4.6531000e-02, 1.7548000e-02,
                5.4791000e-03, 1.3377000e-03, 2.2489000e-04, 2.2345000e-05,
                4.2696000e-07])

        hazard_curve_2 = numpy.array([9.7309000e-01, 9.6857000e-01,
                9.3853000e-01, 9.0089000e-01, 8.3673000e-01, 7.4057000e-01,
                6.1272000e-01, 4.6467000e-01, 3.3694000e-01, 3.1536000e-01,
                1.8340000e-01, 9.2412000e-02, 4.0202000e-02, 1.4900000e-02,
                4.5924000e-03, 1.1126000e-03, 1.8647000e-04, 1.8882000e-05,
                4.7123000e-07])

        hazard_curve_3 = numpy.array([9.9178000e-01, 9.8892000e-01,
                9.6903000e-01, 9.4030000e-01, 8.8405000e-01, 7.8782000e-01,
                6.4627000e-01, 4.7537000e-01, 3.3168000e-01, 3.0827000e-01,
                1.7279000e-01, 8.8360000e-02, 4.2766000e-02, 1.9643000e-02,
                8.1923000e-03, 2.9157000e-03, 7.9955000e-04, 1.5233000e-04,
                1.5582000e-05])

        hazard_curve_4 = numpy.array([9.8885000e-01, 9.8505000e-01,
                9.5972000e-01, 9.2494000e-01, 8.6030000e-01, 7.5574000e-01,
                6.1009000e-01, 4.4217000e-01, 3.0543000e-01, 2.8345000e-01,
                1.5760000e-01, 8.0225000e-02, 3.8681000e-02, 1.7637000e-02,
                7.2685000e-03, 2.5474000e-03, 6.8347000e-04, 1.2596000e-04,
                1.2853000e-05])

        hazard_curve_5 = numpy.array([9.9178000e-01, 9.8892000e-01,
                9.6903000e-01, 9.4030000e-01, 8.8405000e-01, 7.8782000e-01,
                6.4627000e-01, 4.7537000e-01, 3.3168000e-01, 3.0827000e-01,
                1.7279000e-01, 8.8360000e-02, 4.2766000e-02, 1.9643000e-02,
                8.1923000e-03, 2.9157000e-03, 7.9955000e-04, 1.5233000e-04,
                1.5582000e-05])

        quantile_hazard_curve = classical_psha.compute_quantile_curve([
                hazard_curve_1, hazard_curve_2, hazard_curve_3,
                hazard_curve_4, hazard_curve_5], 0.75)

# TODO (ac): Check if this tolerance is enough
        self.assertTrue(numpy.allclose(
                self.expected_curve, quantile_hazard_curve, atol=0.005))

    def test_an_empty_hazard_curve_produces_an_empty_quantile_curve(self):
        hazard_curve = {"site_lon": 2.0, "site_lat": 5.0, "curve": []}
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve)

        self.params[self.quantiles_levels] = "0.75"

        self._run([shapes.Site(2.0, 5.0)])

        result = kvs.get_value_json_decoded(
                kvs.tokens.quantile_hazard_curve_key(
                self.job_id, shapes.Site(2.0, 5.0), 0.75))

        # site is correct
        self.assertEqual(2.0, result["site_lon"])
        self.assertEqual(5.0, result["site_lat"])

        # no values
        self.assertTrue(numpy.allclose([], numpy.array(result["curve"])))

    def test_reads_and_stores_the_quantile_curve_in_kvs(self):
        self.params[self.quantiles_levels] = "0.75"

        hazard_curve_1 = {"site_lon": 2.0, "site_lat": 5.0, "curve": [
                {"y": 9.8161000e-01, "x": 0}, {"y": 9.7837000e-01, "x": 0},
                {"y": 9.5579000e-01, "x": 0}, {"y": 9.2555000e-01, "x": 0},
                {"y": 8.7052000e-01, "x": 0}, {"y": 7.8214000e-01, "x": 0},
                {"y": 6.5708000e-01, "x": 0}, {"y": 5.0526000e-01, "x": 0},
                {"y": 3.7044000e-01, "x": 0}, {"y": 3.4740000e-01, "x": 0},
                {"y": 2.0502000e-01, "x": 0}, {"y": 1.0506000e-01, "x": 0},
                {"y": 4.6531000e-02, "x": 0}, {"y": 1.7548000e-02, "x": 0},
                {"y": 5.4791000e-03, "x": 0}, {"y": 1.3377000e-03, "x": 0},
                {"y": 2.2489000e-04, "x": 0}, {"y": 2.2345000e-05, "x": 0},
                {"y": 4.2696000e-07, "x": 0}]}

        hazard_curve_2 = {"site_lon": 2.0, "site_lat": 5.0, "curve": [
                {"y": 9.7309000e-01, "x": 0}, {"y": 9.6857000e-01, "x": 0},
                {"y": 9.3853000e-01, "x": 0}, {"y": 9.0089000e-01, "x": 0},
                {"y": 8.3673000e-01, "x": 0}, {"y": 7.4057000e-01, "x": 0},
                {"y": 6.1272000e-01, "x": 0}, {"y": 4.6467000e-01, "x": 0},
                {"y": 3.3694000e-01, "x": 0}, {"y": 3.1536000e-01, "x": 0},
                {"y": 1.8340000e-01, "x": 0}, {"y": 9.2412000e-02, "x": 0},
                {"y": 4.0202000e-02, "x": 0}, {"y": 1.4900000e-02, "x": 0},
                {"y": 4.5924000e-03, "x": 0}, {"y": 1.1126000e-03, "x": 0},
                {"y": 1.8647000e-04, "x": 0}, {"y": 1.8882000e-05, "x": 0},
                {"y": 4.7123000e-07, "x": 0}]}

        hazard_curve_3 = {"site_lon": 2.0, "site_lat": 5.0, "curve": [
                {"y": 9.9178000e-01, "x": 0}, {"y": 9.8892000e-01, "x": 0},
                {"y": 9.6903000e-01, "x": 0}, {"y": 9.4030000e-01, "x": 0},
                {"y": 8.8405000e-01, "x": 0}, {"y": 7.8782000e-01, "x": 0},
                {"y": 6.4627000e-01, "x": 0}, {"y": 4.7537000e-01, "x": 0},
                {"y": 3.3168000e-01, "x": 0}, {"y": 3.0827000e-01, "x": 0},
                {"y": 1.7279000e-01, "x": 0}, {"y": 8.8360000e-02, "x": 0},
                {"y": 4.2766000e-02, "x": 0}, {"y": 1.9643000e-02, "x": 0},
                {"y": 8.1923000e-03, "x": 0}, {"y": 2.9157000e-03, "x": 0},
                {"y": 7.9955000e-04, "x": 0}, {"y": 1.5233000e-04, "x": 0},
                {"y": 1.5582000e-05, "x": 0}]}

        hazard_curve_4 = {"site_lon": 2.0, "site_lat": 5.0, "curve": [
                {"y": 9.8885000e-01, "x": 0}, {"y": 9.8505000e-01, "x": 0},
                {"y": 9.5972000e-01, "x": 0}, {"y": 9.2494000e-01, "x": 0},
                {"y": 8.6030000e-01, "x": 0}, {"y": 7.5574000e-01, "x": 0},
                {"y": 6.1009000e-01, "x": 0}, {"y": 4.4217000e-01, "x": 0},
                {"y": 3.0543000e-01, "x": 0}, {"y": 2.8345000e-01, "x": 0},
                {"y": 1.5760000e-01, "x": 0}, {"y": 8.0225000e-02, "x": 0},
                {"y": 3.8681000e-02, "x": 0}, {"y": 1.7637000e-02, "x": 0},
                {"y": 7.2685000e-03, "x": 0}, {"y": 2.5474000e-03, "x": 0},
                {"y": 6.8347000e-04, "x": 0}, {"y": 1.2596000e-04, "x": 0},
                {"y": 1.2853000e-05, "x": 0}]}

        hazard_curve_5 = {"site_lon": 2.0, "site_lat": 5.0, "curve": [
                {"y": 9.9178000e-01, "x": 0}, {"y": 9.8892000e-01, "x": 0},
                {"y": 9.6903000e-01, "x": 0}, {"y": 9.4030000e-01, "x": 0},
                {"y": 8.8405000e-01, "x": 0}, {"y": 7.8782000e-01, "x": 0},
                {"y": 6.4627000e-01, "x": 0}, {"y": 4.7537000e-01, "x": 0},
                {"y": 3.3168000e-01, "x": 0}, {"y": 3.0827000e-01, "x": 0},
                {"y": 1.7279000e-01, "x": 0}, {"y": 8.8360000e-02, "x": 0},
                {"y": 4.2766000e-02, "x": 0}, {"y": 1.9643000e-02, "x": 0},
                {"y": 8.1923000e-03, "x": 0}, {"y": 2.9157000e-03, "x": 0},
                {"y": 7.9955000e-04, "x": 0}, {"y": 1.5233000e-04, "x": 0},
                {"y": 1.5582000e-05, "x": 0}]}

        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_1, 1)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_2, 2)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_3, 3)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_4, 4)
        self._store_hazard_curve_at(shapes.Site(2.0, 5.0), hazard_curve_5, 5)

        self._run([shapes.Site(2.0, 5.0)])

        result = kvs.get_value_json_decoded(
                kvs.tokens.quantile_hazard_curve_key(
                self.job_id, shapes.Site(2.0, 5.0), 0.75))

        # site is correct
        self.assertEqual(2.0, result["site_lon"])
        self.assertEqual(5.0, result["site_lat"])

        # values are correct
        self.assertTrue(numpy.allclose(self.expected_curve,
                numpy.array(result["curve"]), atol=0.005))

    def test_end_to_end(self):
        test_file_path = "smoketests/classical_psha_simple/config.gem"
        engine = job.Job.from_file(test_file_path)

        with mixins.Mixin(engine,
                openquake.hazard.job.HazJobMixin, key="hazard"):

            engine.execute()

# TODO (ac): Find out a better way to do this...
        time.sleep(1)

        self.assertTrue(len(kvs.mget("%s*%s*" % (
                kvs.tokens.QUANTILE_HAZARD_CURVE_KEY_TOKEN, engine.id))) > 0)

    def _run(self, sites):
        classical_psha.compute_quantile_hazard_curves(
                self.engine, sites)

    def _store_hazard_curve_at(self, site, curve, realization=1):
        kvs.set_value_json_encoded(
                kvs.tokens.hazard_curve_key(self.job_id, realization,
                site.longitude, site.latitude), curve)

    def _no_stored_values_for(self, pattern):
        self.assertEqual([], kvs.mget(pattern))

    def _no_computed_quantiles_for(self, value):
        self._no_stored_values_for("%s*%s*%s*" %
                (kvs.tokens.QUANTILE_HAZARD_CURVE_KEY_TOKEN,
                self.job_id, str(value).replace(".", "")))

    def _has_computed_quantile_for_site(self, site, value):
        self.assertTrue(kvs.mget("%s*%s*%s*%s*%s*" %
                (kvs.tokens.QUANTILE_HAZARD_CURVE_KEY_TOKEN,
                self.job_id, site.longitude, site.latitude,
                str(value).replace(".", ""))))


class MeanQuantileHazardMapsComputationTestCase(unittest.TestCase):
    
    def setUp(self):
        self.job_id = 1234
        
        self.poes_levels = classical_psha.POES_PARAM_NAME

        self.params = {}
        self.params["REFERENCE_VS30_VALUE"] = 500
        self.params["INTENSITY_MEASURE_LEVELS"] = "5.0000e-03 7.0000e-03 \
                1.3700e-02 1.9200e-02 2.6900e-02 3.7600e-02 5.2700e-02 \
                7.3800e-02 9.8000e-02 1.0300e-01 1.4500e-01 2.0300e-01 \
                2.8400e-01 3.9700e-01 5.5600e-01 7.7800e-01 1.0900e+00 \
                1.5200e+00 2.1300e+00" 

        self.engine = job.Job(self.params,  self.job_id)
        
        self.empty_mean_curve = {"site_lon": 2.0,
                "site_lat": 5.0, "curve": []}

        # deleting server side cached data
        kvs.flush()

        mean_curve = {"site_lon": 2.0, "site_lat": 5.0,
                "curve": [9.8728e-01, 9.8266e-01, 9.4957e-01,
                9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01, 3.6143e-01,
                2.4231e-01, 2.2452e-01, 1.2831e-01, 7.0352e-02, 3.6060e-02,
                1.6579e-02, 6.4213e-03, 2.0244e-03, 4.8605e-04, 8.1752e-05,
                7.3425e-06]}

        self._store_mean_curve_at(shapes.Site(2.0, 5.0), mean_curve)

    def test_no_computation_when_no_parameter_specified(self):
        self._run()

        self._no_stored_values_for("%s" %
                kvs.tokens.MEAN_HAZARD_MAP_KEY_TOKEN)
    
    def test_no_computation_when_the_parameter_is_empty(self):
        self.params[self.poes_levels] = ""

        self._run()

        self._no_stored_values_for("%s" %
                kvs.tokens.MEAN_HAZARD_MAP_KEY_TOKEN)

    def test_computes_all_the_levels_specified(self):
        self.params[self.poes_levels] = "0.10 0.20 0.50"

        self._run()

        self._has_computed_IML_for_site(shapes.Site(2.0, 5.0), 0.10)
        self._has_computed_IML_for_site(shapes.Site(2.0, 5.0), 0.20)
        self._has_computed_IML_for_site(shapes.Site(2.0, 5.0), 0.50)

    def test_stores_also_the_vs30_parameter(self):
        self.params[self.poes_levels] = "0.25"

        self._run()
        
        im_level = self._get_iml_at(shapes.Site(2.0, 5.0), 0.25)
        self.assertEqual(500, im_level["vs30"])

    def test_computes_the_iml_level(self):
        self.params[self.poes_levels] = "0.10"
        
        mean_curve = {"site_lon": 3.0, "site_lat": 3.0,
                "curve": [9.8784e-01, 9.8405e-01, 9.5719e-01, 9.1955e-01,
                8.5019e-01, 7.4038e-01, 5.9153e-01, 4.2626e-01, 2.9755e-01,
                2.7731e-01, 1.6218e-01, 8.8035e-02, 4.3499e-02, 1.9065e-02,
                7.0442e-03, 2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]}

        self._store_mean_curve_at(shapes.Site(3.0, 3.0), mean_curve)

        self._run()
        
        im_level = self._get_iml_at(shapes.Site(2.0, 5.0), 0.10)
        self.assertEqual(2.0, im_level["site_lon"])
        self.assertEqual(5.0, im_level["site_lat"])

        self.assertTrue(numpy.allclose([1.6789e-01],
                numpy.array(im_level["IML"]), atol=0.005))

        im_level = self._get_iml_at(shapes.Site(3.0, 3.0), 0.10)
        self.assertEqual(3.0, im_level["site_lon"])
        self.assertEqual(3.0, im_level["site_lat"])

        self.assertTrue(numpy.allclose([1.9078e-01],
                numpy.array(im_level["IML"]), atol=0.005))

    def test_when_poe_is_too_high_the_min_iml_is_taken(self):
        # highest value is 9.8728e-01
        self.params[self.poes_levels] = "0.99"
        
        self._run()
        
        im_level = self._get_iml_at(shapes.Site(2.0, 5.0), 0.99)

        self.assertTrue(numpy.allclose([5.0000e-03],
                numpy.array(im_level["IML"])))

    def test_when_poe_is_too_low_the_max_iml_is_taken(self):
        # lowest value is 7.3425e-06
        self.params[self.poes_levels] = "0.00"

        self._run()

        im_level = self._get_iml_at(shapes.Site(2.0, 5.0), 0.00)

        self.assertTrue(numpy.allclose([2.1300e+00],
                numpy.array(im_level["IML"])))

    def _get_iml_at(self, site, poe):
        return kvs.mget_decoded("%s*%s*%s*%s*%s*" %
                (kvs.tokens.MEAN_HAZARD_MAP_KEY_TOKEN,
                self.job_id, site.longitude, site.latitude,
                str(poe).replace(".", "")))[0]

    def _run(self):
        classical_psha.compute_mean_hazard_map(self.engine)

    def _no_stored_values_for(self, pattern):
        self.assertEqual([], kvs.mget(pattern))

    def _store_mean_curve_at(self, site, mean_curve):
        kvs.set_value_json_encoded(
                kvs.tokens.mean_hazard_curve_key(
                self.job_id, site), mean_curve)

    def _has_computed_IML_for_site(self, site, poe):
        self.assertTrue(kvs.mget("%s*%s*%s*%s*%s*" %
                (kvs.tokens.MEAN_HAZARD_MAP_KEY_TOKEN,
                self.job_id, site.longitude, site.latitude,
                str(poe).replace(".", ""))))
