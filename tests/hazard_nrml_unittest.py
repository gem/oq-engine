# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest
from lxml import etree

from opengem import test
from opengem import shapes
from opengem.output import hazard_nrml
from opengem.parser import nrml

TEST_FILE = "shaml_test_result.xml"
XML_METADATA = "<?xml version='1.0' encoding='UTF-8'?>"

schema_dir = os.path.join(os.path.dirname(__file__), "../docs/schema")

class HazardCurveXMLWriterTestCase(unittest.TestCase):
    
    def setUp(self):
        self._delete_test_file()
        self.writer = hazard_nrml.HazardCurveXMLWriter(
                os.path.join(test.DATA_DIR, TEST_FILE))

    @test.skipit
    def tearDown(self):
        self._delete_test_file()

    def _is_xml_valid(self):
        xml_doc = etree.parse(os.path.join(test.DATA_DIR, TEST_FILE))

        # test that the doc matches the schema
        schema_path = os.path.join(schema_dir, "nrml.xsd")
        xmlschema = etree.XMLSchema(etree.parse(schema_path))
        xmlschema.assertValid(xml_doc)

    def test_raises_an_error_if_no_curve_is_serialized(self):
        # invalid schema <shaml:Result> [1..*]
        self.assertRaises(RuntimeError, self.writer.close)
    
    def test_writes_a_single_result_in_a_single_model(self):
        data = {shapes.Site(16.35, 48.25): {"IMT": "MMI",
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [10.0, 20.0, 30.0],
                    "maxProb": 0.9,
                    "minProb": 0.1,
                    "Values": [0.005, 0.007, 0.009],
                    "vs30": 760.0}}

        self.writer.serialize(data)
        
        self._is_xml_valid()
        self.assertTrue(XML_METADATA in self._result_as_string())
        
        # reading
        curves = self._read_curves_inside_region((16.0, 49.0), (17.0, 48.0))
        self._count_and_check_readed_data(data, curves, 1)
    
    @test.skipit
    def test_writes_multiple_results_in_a_single_model_with_same_IML(self):
        data = {shapes.Site(16.35, 48.25): {"IMT": "MMI",
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [10.0, 20.0, 30.0],
                    "maxProb": 0.9,
                    "minProb": 0.1,
                    "Values": [0.005, 0.007, 0.009],
                    "vs30": 760.0},
                shapes.Site(17.35, 38.25): {"IMT": "MMI",
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [10.0, 20.0, 30.0],
                    "maxProb": 0.9,
                    "minProb": 0.1,
                    "Values": [1.005, 1.007, 1.009],
                    "vs30": 760.0}}

        self.writer.serialize(data)
        self._is_xml_valid()

        curves = self._read_curves_inside_region((16.0, 49.0), (18.0, 38.0))
        self._count_and_check_readed_data(data, curves, 2)
    
    @test.skipit
    def test_writes_multiple_results_in_a_single_model_with_different_IML(self):
        data = {shapes.Site(16.35, 48.25): {"IMT": "MMI",
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [10.0, 20.0, 30.0],
                    "maxProb": 0.9,
                    "minProb": 0.1,
                    "Values": [0.005, 0.007, 0.009],
                    "vs30": 760.0},
                shapes.Site(17.35, 38.25): {"IMT": "MMI",
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [30.0, 40.0, 50.0],
                    "maxProb": 0.9,
                    "minProb": 0.1,
                    "Values": [1.005, 1.007, 1.009],
                    "vs30": 760.0}}

        self.writer.serialize(data)
        self._is_xml_valid()

        curves = self._read_curves_inside_region((16.0, 49.0), (18.0, 38.0))
        self._count_and_check_readed_data(data, curves, 2)
    
    @test.skipit
    def test_writes_multiple_results_in_multiple_model(self):
        data = {shapes.Site(16.35, 48.25): {"IMT": "MMI",
                    "IDmodel": "A_MODEL",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [10.0, 20.0, 30.0],
                    "maxProb": 0.9,
                    "minProb": 0.1,
                    "Values": [0.005, 0.007, 0.009],
                    "vs30": 760.0},
                shapes.Site(17.35, 38.25): {"IMT": "MMI",
                    "IDmodel": "A_DIFFERENT_MODEL",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [30.0, 40.0, 50.0],
                    "maxProb": 0.9,
                    "minProb": 0.1,
                    "Values": [1.005, 1.007, 1.009],
                    "vs30": 760.0}}

        self.writer.serialize(data)
        self._is_xml_valid()

        curves = self._read_curves_inside_region((16.0, 49.0), (18.0, 38.0))
        self._count_and_check_readed_data(data, curves, 2)
    
    @test.skipit
    def _delete_test_file(self):
        try:
            os.remove(os.path.join(test.DATA_DIR, TEST_FILE))
        except OSError:
            pass
    
    @test.skipit
    def _count_and_check_readed_data(self, data, curves, expected_number):
        number_of_curves = 0
        
        for shaml_point, shaml_values in curves:
            number_of_curves += 1

            self.assertTrue(shaml_point in data.keys())
            self.assertTrue(shaml_values in data.values())

        self.assertEqual(expected_number, number_of_curves,
                "the number of readed curves is not as expected!")
    
    @test.skipit
    def _read_curves_inside_region(self, upper_left_cor, lower_right_cor):
        constraint = shapes.RegionConstraint.from_simple(
                upper_left_cor, lower_right_cor)

        reader = shaml_output.ShamlOutputFile(
                os.path.join(test.DATA_DIR, TEST_FILE))
        
        return reader.filter(constraint)
    
    @test.skipit
    def _result_as_string(self):
        try:
            result = open(os.path.join(test.DATA_DIR, TEST_FILE))
            return result.read()
        finally:
            result.close()
