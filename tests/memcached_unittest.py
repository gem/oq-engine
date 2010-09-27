# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Quick tests to demonstrate that we can serialize into
memcached in Python and deserialize in Java and viceversa.

To run these tests you need to:

* Install Pylibmc
* Install Jpype
* A memcached server running somewhere

"""

import os
import time
import jpype
import pylibmc
import unittest

from opengem import memcached
from opengem import shapes

MEMCACHED_PORT = 11211
MEMCACHED_HOST = "localhost"

# starting the jvm...
jarpath = os.path.join(os.path.abspath("."), "lib")
jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.ext.dirs=%s" % jarpath)

# TODO Format this stuff!

EMPTY_MODEL = '{"modelName":"","hcRepList":[],"endBranchLabels":[]}'
ONE_CURVE_MODEL = '{"modelName":"","hcRepList":[{"gridNode":[{"location":{"lat":0.017453292519943295,"lon":0.03490658503988659,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[0.1,0.2,0.3]],"unitsMeas":"","intensityMeasureType":"IMT","timeSpan":50.0}],"endBranchLabels":["label"]}'
MULTIPLE_CURVES_ONE_BRANCH = '{"modelName":"","hcRepList":[{"gridNode":[{"location":{"lat":0.017453292519943295,"lon":0.03490658503988659,"depth":0.0},"params":[],"constraintNameMap":{}},{"location":{"lat":0.06981317007977318,"lon":0.06981317007977318,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[5.1,5.2,5.3],[6.1,6.2,6.3]],"unitsMeas":"","intensityMeasureType":"IMT","timeSpan":50.0}],"endBranchLabels":["label"]}'
MULTIPLE_CURVES_MULTIPLE_BRANCHES = '{"modelName":"NAME","hcRepList":[{"gridNode":[{"location":{"lat":0.06981317007977318,"lon":0.06981317007977318,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[1.8,2.8,3.8]],"unitsMeas":"","intensityMeasureType":"IMT","timeSpan":50.0},{"gridNode":[{"location":{"lat":0.06981317007977318,"lon":0.06981317007977318,"depth":0.0},"params":[],"constraintNameMap":{}}],"gmLevels":[1.0,2.0,3.0],"probExList":[[1.5,2.5,3.5]],"unitsMeas":"","intensityMeasureType":"IMT","timeSpan":50.0}],"endBranchLabels":["label1","label2"]}'

class MemcachedTestCase(unittest.TestCase):
    
    def setUp(self):
        java_class = jpype.JClass("org.gem.engine.hazard.memcached.Cache")
        self.java_client = java_class(MEMCACHED_HOST, MEMCACHED_PORT)
        
        self.python_client = pylibmc.Client([
                MEMCACHED_HOST + ":%d" % MEMCACHED_PORT], binary=False)
        
        # clean server side cache
        self.python_client.flush_all()
        
        self.reader = memcached.Reader(self.python_client)
        
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
        self.assertEqual(shapes.FastCurve(((1.0, 0.1), (2.0, 0.2), (3.0, 0.3))), curves[0])
    
    def test_reads_multiple_curves_in_one_branch(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_ONE_BRANCH)
        curves = self.reader.as_curve("KEY")

        self.assertEqual(2, len(curves))
        self.assertEqual(shapes.FastCurve(((1.0, 5.1), (2.0, 5.2), (3.0, 5.3))), curves[0])
        self.assertEqual(shapes.FastCurve(((1.0, 6.1), (2.0, 6.2), (3.0, 6.3))), curves[1])
    
    def test_reads_multiple_curves_in_multiple_branches(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_MULTIPLE_BRANCHES)
        curves = self.reader.as_curve("KEY")
        
        self.assertEqual(2, len(curves))
        self.assertEqual(shapes.FastCurve(((1.0, 1.8), (2.0, 2.8), (3.0, 3.8))), curves[0])
        self.assertEqual(shapes.FastCurve(((1.0, 1.5), (2.0, 2.5), (3.0, 3.5))), curves[1])

    def test_end_to_end_curves_reading(self):
        # Hazard object model serialization in JSON is tested in the Java side
        self.java_client.set("KEY", ONE_CURVE_MODEL)
        
        time.sleep(0.3)
        
        curves = self.reader.as_curve("KEY")
        
        self.assertEqual(1, len(curves))
        self.assertEqual(shapes.FastCurve(((1.0, 0.1), (2.0, 0.2), (3.0, 0.3))), curves[0])