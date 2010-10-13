# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import time
import jpype
import pylibmc
import unittest

from opengem import logs
from opengem import memcached
from opengem import shapes
from opengem import test
from opengem.output import hazard as hazard_output
from opengem.parser import hazard as hazard_parser

LOG = logs.LOG

MEMCACHED_PORT = 11211
MEMCACHED_HOST = "localhost"

TEST_FILE = "nrml_test_result.xml"

# starting the jvm...
jarpath = os.path.join(os.path.abspath("."), "lib")
jpype.startJVM(jpype.getDefaultJVMPath(), "-Dlog4j.disableOverride=false", 
                "-Dlog4j.disable=WARN", "-Dlog4j.debug", 
                "-Dlog4j.logger.net.spy=WARN", "-Djava.ext.dirs=%s" % jarpath)

EMPTY_MODEL = '{"modelName":"","hcRepList":[],"endBranchLabels":[]}'
ONE_CURVE_MODEL = '{"modelName":"","hcRepList":[{"gridNode":[{"location":{"lat":0.017453292519943295,"lon":0.03490658503988659,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[0.1,0.2,0.3]],"unitsMeas":"","intensityMeasureType":"IMT","timeSpan":50.0}],"endBranchLabels":["label"]}'
MULTIPLE_CURVES_ONE_BRANCH = '{"modelName":"","hcRepList":[{"gridNode":[{"location":{"lat":0.017453292519943295,"lon":0.03490658503988659,"depth":0.0},"params":[],"constraintNameMap":{}},{"location":{"lat":0.06981317007977318,"lon":0.06981317007977318,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[5.1,5.2,5.3],[6.1,6.2,6.3]],"unitsMeas":"","intensityMeasureType":"IMT","timeSpan":50.0}],"endBranchLabels":["label"]}'
MULTIPLE_CURVES_MULTIPLE_BRANCHES = '{"modelName":"","hcRepList":[{"gridNode":[{"location":{"lat":0.06981317007977318,"lon":0.06981317007977318,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[1.8,2.8,3.8]],"unitsMeas":"","intensityMeasureType":"IMT","timeSpan":50.0},{"gridNode":[{"location":{"lat":0.017453292519943295,"lon":0.06981317007977318,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[1.5,2.5,3.5]],"unitsMeas":"","intensityMeasureType":"IMT","timeSpan":50.0}],"endBranchLabels":["label1","label2"]}'

class MemcachedTestCase(unittest.TestCase):
    
    def setUp(self):
        java_class = jpype.JClass("org.gem.engine.hazard.memcached.Cache")
        self.java_client = java_class(MEMCACHED_HOST, MEMCACHED_PORT)
        
        self.python_client = pylibmc.Client([
                MEMCACHED_HOST + ":%d" % MEMCACHED_PORT], binary=False)
        
        # clean server side cache
        self.python_client.flush_all()
        
        self.reader = memcached.Reader(self.python_client)
        self._delete_test_file()
    
    def tearDown(self):
        self._delete_test_file()
    
    def _delete_test_file(self):
        try:
            os.remove(os.path.join(test.DATA_DIR, TEST_FILE))
        except OSError:
             pass
    
    def test_can_wrap_the_java_client(self):
        self.java_client.set("KEY", "VALUE")
        
        # TODO (ac): I know, it's weird. Looking for something better...
        time.sleep(0.3)
        
        self.assertEqual("VALUE", self.java_client.get("KEY"))

    def test_can_write_in_java_and_read_in_python(self):
        self.java_client.set("KEY", "VALUE")
        
        time.sleep(0.3)
        
        self.assertEqual("VALUE", self.python_client.get("KEY"))
    
    def test_can_write_in_python_and_read_in_java(self):
        self.python_client.set("KEY", "VALUE")
        
        time.sleep(0.3)
        
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
    
    # input compatible to the nrml writer
    
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
    
    @test.skipit
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
    
    @test.skipit
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

        self.assertEqual(2, len(nrmls.items()))
        self.assertEquals(data, nrmls)
    @test.skipit
    def test_end_to_end_from_memcached_to_nrml(self):
        # storing in memcached from java side
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
