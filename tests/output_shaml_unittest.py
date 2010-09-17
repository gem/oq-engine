# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from opengem import test
from opengem import shapes
from opengem.output import shaml
from opengem.parser import shaml_output

TEST_FILE = "shaml_test_result.xml"

XML_METADATA = "<?xml version='1.0' encoding='UTF-8'?>"
EMPTY_RESULT = '<shaml:HazardResultList xmlns:shaml="http://opengem.org/xmlns/shaml/0.1" xmlns:gml="http://www.opengis.net/gml"/>'

class OutputShamlTestCase(unittest.TestCase):

    def setUp(self):
        self.writer = shaml.ShamlWriter(os.path.join(test.DATA_DIR, TEST_FILE))

    def tearDown(self):
        try:
            os.remove(os.path.join(test.DATA_DIR, TEST_FILE))
        except OSError:
            pass

    # quick learning test
    def test_string_matching(self):
        self.assertTrue("<test>" in "<a><test></a>")
        self.assertFalse("#test>" in "<a><test></a>")
    
    def test_writes_the_file_when_closed(self):
        self.writer.close()
    
        # with no written file we would have an IOError
        result = open(os.path.join(test.DATA_DIR, TEST_FILE))
        result.close()

    def test_writes_the_xml_metadata(self):
        self.writer.close()
        self.assertTrue(XML_METADATA in self._result_as_string())

    def test_writes_an_empty_list_with_no_output(self):
        self.writer.close()
        self.assertTrue(EMPTY_RESULT in self._result_as_string())

    def test_writes_a_single_result_in_a_single_model(self):
        point = shapes.Site(16.35, 48.25)
        values = {"IMT": "MMI",
                "IDmodel": "MMI_3_1",
                "timeSpanDuration": 50.0,
                "endBranchLabel": "3_1",
                "IML": [10.0, 20.0, 30.0],
                "maxProb": 0.9,
                "minProb": 0.1,
                "Values": [0.005, 0.007, 0.009],
                "vs30": 760.0}

        self.writer.write(point, values)
        self.writer.close()
        
        # reading
        constraint = shapes.RegionConstraint.from_simple(
                (16.0, 49.0), (17.0, 48.0))
        
        reader = shaml_output.ShamlOutputFile(
                os.path.join(test.DATA_DIR, TEST_FILE))

        counter = None

        # checking againts readed values
        for counter, (shaml_point, shaml_values) in enumerate(reader.filter(constraint)):
            counter += 1
            
            self.assertEqual(point, shaml_point)
            self.assertEqual(values, shaml_values)

        self.assertEqual(1, counter, "one element should be readed!")

    def test_writes_multiple_results(self):
        pass

    def _result_as_string(self):
        try:
            result = open(os.path.join(test.DATA_DIR, TEST_FILE))
            return result.read()
        finally:
            result.close()
