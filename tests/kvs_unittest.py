# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import time
import unittest

from openquake import java
from openquake import logs
from openquake import kvs
from openquake import settings
from openquake import shapes
from openquake import test
from openquake import settings

from openquake.kvs import reader
from openquake.parser import vulnerability

from openquake.output import hazard as hazard_output
from openquake.parser import hazard as hazard_parser

LOG = logs.LOG

TEST_FILE = "nrml_test_result.xml"


EMPTY_MODEL = '{"modelName":"","hcRepList":[],"endBranchLabels":[]}'
ONE_CURVE_MODEL = '{"modelName":"","hcRepList":[{"gridNode":[{"location":{"lat":0.017453292519943295,"lon":0.03490658503988659,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[0.1,0.2,0.3]],"unitsMeas":"","intensityMeasureType":"IMT","timeSpan":50.0}],"endBranchLabels":["label"]}'
MULTIPLE_CURVES_ONE_BRANCH = '{"modelName":"","hcRepList":[{"gridNode":[{"location":{"lat":0.017453292519943295,"lon":0.03490658503988659,"depth":0.0},"params":[],"constraintNameMap":{}},{"location":{"lat":0.06981317007977318,"lon":0.06981317007977318,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[5.1,5.2,5.3],[6.1,6.2,6.3]],"unitsMeas":"","intensityMeasureType":"PGA","timeSpan":50.0}],"endBranchLabels":["label"]}'
MULTIPLE_CURVES_MULTIPLE_BRANCHES = '{"modelName":"","hcRepList":[{"gridNode":[{"location":{"lat":0.06981317007977318,"lon":0.06981317007977318,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[1.8,2.8,3.8]],"unitsMeas":"","intensityMeasureType":"PGA","timeSpan":50.0},{"gridNode":[{"location":{"lat":0.017453292519943295,"lon":0.06981317007977318,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[1.5,2.5,3.5]],"unitsMeas":"","intensityMeasureType":"PGA","timeSpan":50.0}],"endBranchLabels":["label1","label2"]}'

class KVSTestCase(unittest.TestCase):
    
    def setUp(self):
        # starting the jvm...
        print "About to start the jvm..."
        jpype = java.jvm()
        java_class = jpype.JClass("org.gem.engine.hazard.redis.Cache")
        print ("Not dead yet, and found the class...")
        self.java_client = java_class(settings.KVS_HOST, settings.KVS_PORT)
        
        self.python_client = kvs.get_client(binary=False)

        self.reader = reader.Reader(self.python_client)
        self._delete_test_file()
    
    def tearDown(self):
        self._delete_test_file()
        self.python_client.flushdb()
    
    def _delete_test_file(self):
        try:
            os.remove(os.path.join(test.DATA_DIR, TEST_FILE))
        except OSError:
             pass
    
    def test_can_wrap_the_java_client(self):
        self.java_client.set("KEY", "VALUE")
        result = self.java_client.get("KEY")
        self.assertEqual("VALUE", self.java_client.get("KEY"))

    def test_can_write_in_java_and_read_in_python(self):
        self.java_client.set("KEY", "VALUE")
        self.assertEqual("VALUE", self.python_client.get("KEY"))
    
    def test_can_write_in_python_and_read_in_java(self):
        self.python_client.set("KEY", "VALUE")
        self.assertEqual("VALUE", self.java_client.get("KEY"))
    
    def test_an_empty_model_produces_an_empty_curve_set(self):
        self.python_client.set("KEY", EMPTY_MODEL)
        self.assertEqual(0, len(self.reader.as_curve("KEY")))

    def test_an_error_is_raised_if_no_model_cached(self):
        self.assertRaises(ValueError, self.reader.as_curve, "KEY")
    
    def test_reads_one_curve(self):
        self.python_client.set("KEY", ONE_CURVE_MODEL)
        curves = self.reader.as_curve("KEY")
        
        self.assertEqual(1, len(curves))
        self.assertEqual(shapes.Curve(
                ((1.0, 0.1), (2.0, 0.2), (3.0, 0.3))), curves[0])
    
    def test_reads_multiple_curves_in_one_branch(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_ONE_BRANCH)
        curves = self.reader.as_curve("KEY")

        self.assertEqual(2, len(curves))
        self.assertEqual(shapes.Curve(
                ((1.0, 5.1), (2.0, 5.2), (3.0, 5.3))), curves[0])
                
        self.assertEqual(shapes.Curve(
                ((1.0, 6.1), (2.0, 6.2), (3.0, 6.3))), curves[1])
    
    def test_reads_multiple_curves_in_multiple_branches(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_MULTIPLE_BRANCHES)
        curves = self.reader.as_curve("KEY")
        
        self.assertEqual(2, len(curves))
        self.assertEqual(shapes.Curve(
                ((1.0, 1.8), (2.0, 2.8), (3.0, 3.8))), curves[0])
        
        self.assertEqual(shapes.Curve(
                ((1.0, 1.5), (2.0, 2.5), (3.0, 3.5))), curves[1])

    def test_end_to_end_curves_reading(self):
        # Hazard object model serialization in JSON is tested in the Java side
        self.java_client.set("KEY", ONE_CURVE_MODEL)
        
        time.sleep(0.3)
        
        curves = self.reader.as_curve("KEY")
        
        self.assertEqual(1, len(curves))
        self.assertEqual(shapes.Curve(
                ((1.0, 0.1), (2.0, 0.2), (3.0, 0.3))), curves[0])
    
    def test_an_empty_model_produces_an_empty_curve_set_nrml(self):
        self.python_client.set("KEY", EMPTY_MODEL)
        self.assertEqual(0, len(self.reader.for_nrml("KEY")))
    
    def test_an_error_is_raised_if_no_model_cached_nrml(self):
        self.assertRaises(ValueError, self.reader.for_nrml, "KEY")
    
    def test_reads_one_curve_nrml(self):
        self.python_client.set("KEY", ONE_CURVE_MODEL)
        nrmls = self.reader.for_nrml("KEY")

        data = {shapes.Site(2.0, 1.0): {
                    "IMT": "IMT",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label",
                    "IMLValues": [1.0, 2.0, 3.0],
                    "Values": [0.1,0.2,0.3]}}

        self.assertEqual(1, len(nrmls.items()))
        self.assertEquals(data, nrmls)
    
    def test_reads_multiple_curves_in_one_branch_nrml(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_ONE_BRANCH)
        nrmls = self.reader.for_nrml("KEY")

        data = {shapes.Site(2.0, 1.0): {
                    "IMT": "PGA",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label",
                    "IMLValues": [1.0, 2.0, 3.0],
                    "Values": [5.1,5.2,5.3]},
                shapes.Site(4.0, 4.0): {
                    "IMT": "PGA",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label",
                    "IMLValues": [1.0, 2.0, 3.0],
                    "Values": [6.1,6.2,6.3]} 
                }

        self.assertEqual(2, len(nrmls.items()))
        self.assertEquals(data, nrmls)
    
    def test_reads_multiple_curves_in_multiple_branches_nrml(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_MULTIPLE_BRANCHES)
        nrmls = self.reader.for_nrml("KEY")

        data = {shapes.Site(4.0, 4.0): {
                    "IMT": "PGA",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label1",
                    "IMLValues": [1.0, 2.0, 3.0],
                    "Values": [1.8,2.8,3.8]},
                shapes.Site(4.0, 1.0): {
                    "IMT": "PGA",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label2",
                    "IMLValues": [1.0, 2.0, 3.0],
                    "Values": [1.5,2.5,3.5]} 
                }

        print "data: %s" % data
        print nrmls

        self.assertEqual(2, len(nrmls.items()))
        self.assertEquals(data, nrmls)

    @test.skipit
    def test_end_to_end_from_kvs_to_nrml(self):
        # storing in kvs from java side
        self.java_client.set("KEY", ONE_CURVE_MODEL)
        
        time.sleep(0.3)
        
        # reading in python side
        nrmls = self.reader.for_nrml("KEY")
        
        LOG.debug("Nrmls are %s", nrmls)
        
        # writing result
        writer = hazard_output.HazardCurveXMLWriter(
                os.path.join(test.DATA_DIR, TEST_FILE))

        writer.serialize(nrmls)
        
        # reading and checking
        constraint = shapes.RegionConstraint.from_simple(
                (1.5, 1.5), (2.5, 0.5))

        reader = hazard_parser.NrmlFile(
                os.path.join(test.DATA_DIR, TEST_FILE))
        
        number_of_curves = 0

        data = {shapes.Site(2.0, 1.0): {
            "IMT": "PGA",
            "IDmodel": "FIXED",
            "timeSpanDuration": 50.0,
            "endBranchLabel": "label",
            "IMLValues": [1.0, 2.0, 3.0],
            "Values": [0.1,0.2,0.3]}}

        for nrml_point, nrml_values in reader.filter(constraint):
            number_of_curves += 1

            self.assertTrue(nrml_point in data.keys())
            for key, val in nrml_values.items():
                self.assertEqual(val, data.values()[0][key])

        self.assertEqual(1, number_of_curves)


class IdentifierTestCase(unittest.TestCase):
    def setUp(self):
        self.job_id = 123456
        self.product = "TestProduct"
        self.block_id = 8801 # This is just an interesting number
        self.site = "Testville,TestLand"

    def test_generate_product_key_with_only_job_id_and_product(self):
        key = kvs.generate_product_key(self.job_id, self.product)

        ev = "%s!%s!!" % (self.job_id, self.product)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_job_id_product_and_block_id(self):
        key = kvs.generate_product_key(self.job_id, self.product, self.block_id)

        ev =  "%s!%s!%s!" % (self.job_id, self.product, self.block_id)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_job_id_product_and_site(self):
        key = kvs.generate_product_key(self.job_id, self.product, 
            site=self.site)

        ev =  "%s!%s!!%s" % (self.job_id, self.product, self.site)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_all_test_data(self):
        key = kvs.generate_product_key(self.job_id, self.product, self.block_id,
            self.site)

        ev = "%s!%s!%s!%s" % (
                self.job_id, self.product, self.block_id, self.site) 
        self.assertEqual(key, ev)

    def test_generate_product_key_with_tokens_from_kvs(self):
        products = [
            kvs.tokens.ERF_KEY_TOKEN,
            kvs.tokens.MGM_KEY_TOKEN,
            kvs.tokens.HAZARD_CURVE_KEY_TOKEN,
            kvs.tokens.EXPOSURE_KEY_TOKEN,
            kvs.tokens.GMF_KEY_TOKEN,
            kvs.tokens.LOSS_RATIO_CURVE_KEY_TOKEN,
            kvs.tokens.LOSS_CURVE_KEY_TOKEN,
            kvs.tokens.loss_token(0.01),
            vulnerability.VULNERABILITY_CURVE_KEY_TOKEN,
        ]

        for product in products:
            key = kvs.generate_product_key(self.job_id, product,
                self.block_id, self.site)

            ev = "%s!%s!%s!%s" % (self.job_id, product, 
                    self.block_id, self.site)
            self.assertEqual(key, ev)
    
    def test_kvs_doesnt_support_spaces_in_keys(self):
        self.product = "A TestProduct"
        self.site = "Testville, TestLand"
        key = kvs.generate_product_key(self.job_id, self.product, 
            site=self.site)

        ev = "%s!ATestProduct!!Testville,TestLand" % self.job_id
        self.assertEqual(key, ev)
