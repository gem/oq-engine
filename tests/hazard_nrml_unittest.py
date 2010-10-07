# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest
from lxml import etree

from opengem import test
from opengem import shapes
from opengem.output import hazard as hazard_output
from opengem.parser import hazard as hazard_parser

TEST_FILE = "hazard-curves.xml"
XML_METADATA = "<?xml version='1.0' encoding='UTF-8'?>"


class HazardCurveXMLWriterTestCase(unittest.TestCase):
    
    def setUp(self):
        self._delete_test_file()
        self.writer = hazard_output.HazardCurveXMLWriter(
                os.path.join(test.DATA_DIR, TEST_FILE))
    @test.skipit
    def tearDown(self):
        self._delete_test_file()

    def _is_xml_valid(self):
        xml_doc = etree.parse(os.path.join(test.DATA_DIR, TEST_FILE))

        # test that the doc matches the schema
        schema_path = os.path.join(test.SCHEMA_DIR, "nrml.xsd")
        xmlschema = etree.XMLSchema(etree.parse(schema_path))
        xmlschema.assertValid(xml_doc)

    def test_raises_an_error_if_no_curve_is_serialized(self):
        # invalid schema <nrml:Result> [1..*]
        self.assertRaises(RuntimeError, self.writer.close)

    def test_writes_a_single_result(self):
        data = {shapes.Site(-122.5000, 37.5000): {
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "Values": [9.8728e-01, 9.8266e-01, 9.4957e-01, 
                    9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01, 
                    3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01, 
                    7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03, 
                    2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]}}

        self.writer.serialize(data)
        self._is_xml_valid()
        
        self.assertTrue(XML_METADATA in self._result_as_string())
        
        # reading
        curves = self._read_curves_inside_region((-123.0, 38.0), (-122.0, 35.0))
        self._count_and_check_readed_data(data, curves, 1)

    def test_writes_multiple_results_with_one_branch_level(self):
        data = {shapes.Site(-122.5000, 37.5000): {
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "Values": [9.8728e-01, 9.8266e-01, 9.4957e-01, 
                    9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01, 
                    3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01, 
                    7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03, 
                    2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]},
                shapes.Site(-122.4000, 37.5000): {
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "Values": [9.8784e-01, 9.8405e-01, 9.5719e-01, 
                    9.1955e-01, 8.5019e-01, 7.4038e-01, 5.9153e-01, 
                    4.2626e-01, 2.9755e-01, 2.7731e-01, 1.6218e-01, 
                    8.8035e-02, 4.3499e-02, 1.9065e-02, 7.0442e-03, 
                    2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]}}

        self.writer.serialize(data)
        self._is_xml_valid()

        curves = self._read_curves_inside_region((-123, 38.0), (-120, 35.0))
        self._count_and_check_readed_data(data, curves, 2)
    
    def test_writes_the_config_only_once(self):
        data = {shapes.Site(-122.5000, 37.5000): {
                        "IDmodel": "MMI_3_1",
                        "timeSpanDuration": 50.0,
                        "endBranchLabel": "3_1",
                        "IMLValues": [5.0, 6.0, 7.0],
                        "saPeriod": 0.1,
                        "saDamping": 1.0,
                        "IMT": "PGA",
                        "Values": [0.1, 0.2, 0.3]},
                shapes.Site(-122.4000, 37.5000): {
                        "IDmodel": "MMI_3_1",
                        "timeSpanDuration": 50.0,
                        "endBranchLabel": "3_2",
                        "IMLValues": [5.0, 6.0, 7.0],
                        "saPeriod": 0.1,
                        "saDamping": 1.0,
                        "IMT": "PGA",
                        "Values": [0.4, 0.5, 0.6]}
                }
        
        self.writer.serialize(data)
        self._is_xml_valid()

    def test_writes_multiple_results_with_different_branch_levels(self):
        data = {shapes.Site(-122.5000, 37.5000): {
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [5.0, 6.0, 7.0],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "Values": [0.1, 0.2, 0.3]},
                shapes.Site(-122.4000, 37.5000): {
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_2",
                    "IMLValues": [8.0, 9.0, 10.0],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "Values": [0.1, 0.2, 0.3]}}

        self.writer.serialize(data)
        self._is_xml_valid()

        curves = self._read_curves_inside_region((-123, 38.0), (-120, 35.0))
        self._count_and_check_readed_data(data, curves, 2)
        
    @test.skipit
    def _delete_test_file(self):
        try:
            os.remove(os.path.join(test.DATA_DIR, TEST_FILE))
        except OSError:
            pass
    
    def _count_and_check_readed_data(self, data, curves, expected_number):
        number_of_curves = 0
        
        for nrml_point, nrml_values in curves:
            number_of_curves += 1
            
            self.assertTrue(nrml_point in data.keys())
            self.assertTrue(nrml_values in data.values())

        self.assertEqual(expected_number, number_of_curves,
                "the number of readed curves is not as expected!")
    
    def _read_curves_inside_region(self, upper_left_cor, lower_right_cor):
        constraint = shapes.RegionConstraint.from_simple(
                upper_left_cor, lower_right_cor)

        reader = hazard_parser.NrmlFile(
                os.path.join(test.DATA_DIR, TEST_FILE))
        
        return reader.filter(constraint)

    def _result_as_string(self):
        try:
            result = open(os.path.join(test.DATA_DIR, TEST_FILE))
            return result.read()
        finally:
            result.close()
