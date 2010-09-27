# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import time
import jpype
import pylibmc
import unittest

from opengem import memcached
from opengem import shapes
from opengem import test
from opengem.output import shaml
from opengem.parser import shaml_output

MEMCACHED_PORT = 11211
MEMCACHED_HOST = "localhost"

TEST_FILE = "shaml_test_result.xml"

# starting the jvm...
jarpath = os.path.join(os.path.abspath("."), "lib")
jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.ext.dirs=%s" % jarpath)

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
        self.assertEqual(shapes.FastCurve(
                ((1.0, 0.1), (2.0, 0.2), (3.0, 0.3))), curves[0])
    
    def test_reads_multiple_curves_in_one_branch(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_ONE_BRANCH)
        curves = self.reader.as_curve("KEY")

        self.assertEqual(2, len(curves))
        self.assertEqual(shapes.FastCurve(
                ((1.0, 5.1), (2.0, 5.2), (3.0, 5.3))), curves[0])
                
        self.assertEqual(shapes.FastCurve(
                ((1.0, 6.1), (2.0, 6.2), (3.0, 6.3))), curves[1])
    
    def test_reads_multiple_curves_in_multiple_branches(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_MULTIPLE_BRANCHES)
        curves = self.reader.as_curve("KEY")
        
        self.assertEqual(2, len(curves))
        self.assertEqual(shapes.FastCurve(
                ((1.0, 1.8), (2.0, 2.8), (3.0, 3.8))), curves[0])
        
        self.assertEqual(shapes.FastCurve(
                ((1.0, 1.5), (2.0, 2.5), (3.0, 3.5))), curves[1])

    def test_end_to_end_curves_reading(self):
        # Hazard object model serialization in JSON is tested in the Java side
        self.java_client.set("KEY", ONE_CURVE_MODEL)
        
        time.sleep(0.3)
        
        curves = self.reader.as_curve("KEY")
        
        self.assertEqual(1, len(curves))
        self.assertEqual(shapes.FastCurve(
                ((1.0, 0.1), (2.0, 0.2), (3.0, 0.3))), curves[0])
    
    # input compatible to the shaml writer
    
    def test_an_empty_model_produces_an_empty_curve_set(self):
        self.python_client.set("KEY", EMPTY_MODEL)
        self.assertEqual(0, len(self.reader.for_shaml("KEY")))
    
    def test_an_error_is_raised_if_no_model_cached(self):
        self.assertRaises(ValueError, self.reader.for_shaml, "KEY")
    
    def test_reads_one_curve(self):
        self.python_client.set("KEY", ONE_CURVE_MODEL)
        shamls = self.reader.for_shaml("KEY")

        data = {shapes.Site(0.03490658503988659, 0.017453292519943295): {
                    "IMT": "IMT",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label",
                    "IML": [1.0, 2.0, 3.0],
                    "maxProb": 0.3,
                    "minProb": 0.1,
                    "Values": [0.1,0.2,0.3],
                    "vs30": 0.0}}

        self.assertEqual(1, len(shamls.items()))
        self.assertEquals(data, shamls)

    def test_reads_multiple_curves_in_one_branch(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_ONE_BRANCH)
        shamls = self.reader.for_shaml("KEY")

        data = {shapes.Site(0.03490658503988659, 0.017453292519943295): {
                    "IMT": "IMT",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label",
                    "IML": [1.0, 2.0, 3.0],
                    "maxProb": 5.3,
                    "minProb": 5.1,
                    "Values": [5.1,5.2,5.3],
                    "vs30": 0.0},
                shapes.Site(0.06981317007977318, 0.06981317007977318): {
                    "IMT": "IMT",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label",
                    "IML": [1.0, 2.0, 3.0],
                    "maxProb": 6.3,
                    "minProb": 6.1,
                    "Values": [6.1,6.2,6.3],
                    "vs30": 0.0} 
                }

        self.assertEqual(2, len(shamls.items()))
        self.assertEquals(data, shamls)

    def test_reads_multiple_curves_in_one_branch(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_MULTIPLE_BRANCHES)
        shamls = self.reader.for_shaml("KEY")

        data = {shapes.Site(0.06981317007977318, 0.06981317007977318): {
                    "IMT": "IMT",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label1",
                    "IML": [1.0, 2.0, 3.0],
                    "maxProb": 3.8,
                    "minProb": 1.8,
                    "Values": [1.8,2.8,3.8],
                    "vs30": 0.0},
                shapes.Site(0.06981317007977318, 0.017453292519943295): {
                    "IMT": "IMT",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label2",
                    "IML": [1.0, 2.0, 3.0],
                    "maxProb": 3.5,
                    "minProb": 1.5,
                    "Values": [1.5,2.5,3.5],
                    "vs30": 0.0} 
                }

        self.assertEqual(2, len(shamls.items()))
        self.assertEquals(data, shamls)

    def test_end_to_end_from_memcached_to_shaml(self):
        # storing in memcached from java side
        self.java_client.set("KEY", ONE_CURVE_MODEL)
        
        time.sleep(0.3)
        
        # reading in python side
        shamls = self.reader.for_shaml("KEY")
        
        # writing result
        writer = shaml.HazardCurveXMLWriter(
                os.path.join(test.DATA_DIR, TEST_FILE))

        writer.serialize(shamls)
        
        # reading and checking
        constraint = shapes.RegionConstraint.from_simple(
                (0.01, 0.02), (0.04, 0.01))

        reader = shaml_output.ShamlOutputFile(
                os.path.join(test.DATA_DIR, TEST_FILE))
        
        number_of_curves = 0

        data = {shapes.Site(0.03490658503988659, 0.017453292519943295): {
            "IMT": "IMT",
            "IDmodel": "FIXED",
            "timeSpanDuration": 50.0,
            "endBranchLabel": "label",
            "IML": [1.0, 2.0, 3.0],
            "maxProb": 0.3,
            "minProb": 0.1,
            "Values": [0.1,0.2,0.3],
            "vs30": 0.0}}

        for shaml_point, shaml_values in reader.filter(constraint):
            number_of_curves += 1

            self.assertTrue(shaml_point in data.keys())
            self.assertTrue(shaml_values in data.values())

        self.assertEqual(1, number_of_curves)
