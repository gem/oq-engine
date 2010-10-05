# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest
from lxml import etree

from opengem import test
from opengem import shapes
from opengem.output import hazard_nrml
from opengem.parser import nrml

TEST_FILE = "hazard-curves.xml"
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

    #@test.skipit
    def _is_xml_valid(self):
        xml_doc = etree.parse(os.path.join(test.DATA_DIR, TEST_FILE))

        # test that the doc matches the schema
        schema_path = os.path.join(schema_dir, "nrml.xsd")
        xmlschema = etree.XMLSchema(etree.parse(schema_path))
        xmlschema.assertValid(xml_doc)

    @test.skipit
    def test_raises_an_error_if_no_curve_is_serialized(self):
        # invalid schema <nrml:Result> [1..*]
        self.assertRaises(RuntimeError, self.writer.close)
    
    #@test.skipit
    def test_writes_a_single_result_in_a_single_model(self):
        data = {shapes.Site(-122.5000, 37.5000): {"IMT": "MMI",
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": "foo",
                    "saDamping": "bar",
                    "IMT": "PGA",
                    "Values": [9.8728e-01, 9.8266e-01, 9.4957e-01, 
                    9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01, 
                    3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01, 
                    7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03, 
                    2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]}}

        self.writer.serialize(data)
        
        self._is_xml_valid()
        #self.assertTrue(XML_METADATA in self._result_as_string())
        
        # reading
        curves = self._read_curves_inside_region((-120, 35.0), (-123, 38.0))
        self._count_and_check_readed_data(data, curves, 1)
    
    #@test.skipit
    def test_writes_multiple_results_in_a_single_model_with_same_IML(self):
        data = {shapes.Site(-122.5000, 37.5000): {"IMT": "MMI",
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": "foo",
                    "saDamping": "bar",
                    "IMT": "PGA",
                    "Values": [9.8728e-01, 9.8266e-01, 9.4957e-01, 
                    9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01, 
                    3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01, 
                    7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03, 
                    2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]},
                shapes.Site(-122.4000, 37.5000): {"IMT": "MMI",
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": "foo",
                    "saDamping": "bar",
                    "IMT": "PGA",
                    "Values": [9.8784e-01, 9.8405e-01, 9.5719e-01, 
                    9.1955e-01, 8.5019e-01, 7.4038e-01, 5.9153e-01, 
                    4.2626e-01, 2.9755e-01, 2.7731e-01, 1.6218e-01, 
                    8.8035e-02, 4.3499e-02, 1.9065e-02, 7.0442e-03, 
                    2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]}}

        self.writer.serialize(data)
        self._is_xml_valid()

        curves = self._read_curves_inside_region((-120, 35.0), (-123, 38.0))
        self._count_and_check_readed_data(data, curves, 2)
    
    @test.skipit
    def test_writes_multiple_results_in_a_single_model_with_different_IML(self):
        data = {shapes.Site(-122.5000, 37.5000): {"IMT": "MMI",
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": "foo",
                    "saDamping": "bar",
                    "IMT": "PGA",
                    "Values": [9.8728e-01, 9.8266e-01, 9.4957e-01, 
                    9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01, 
                    3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01, 
                    7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03, 
                    2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]},
                shapes.Site(-122.4000, 37.5000): {"IMT": "MMI",
                    "IDmodel": "MMI_3_1",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [5.0000e-03, 5.0000e-03, 1.3700e-02, 
                    1.9200e-02, 3.6900e-02, 4.7600e-02, 5.2700e-02, 
                    6.3800e-02, 9.8000e-02, 2.0300e-01, 1.4500e-01, 
                    1.0300e-01, 1.8400e-01, 3.9700e-01, 2.5600e-01, 
                    7.7800e-01, 2.0900e+00, 1.5200e+00, 4.1300e+00],
                    "saPeriod": "foo",
                    "saDamping": "bar",
                    "IMT": "PGA",
                    "Values": [9.8784e-01, 9.8405e-01, 9.5719e-01, 
                    9.1955e-01, 8.5019e-01, 7.4038e-01, 5.9153e-01, 
                    4.2626e-01, 2.9755e-01, 2.7731e-01, 1.6218e-01, 
                    8.8035e-02, 4.3499e-02, 1.9065e-02, 7.0442e-03, 
                    2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]}}

        self.writer.serialize(data)
        self._is_xml_valid()

        curves = self._read_curves_inside_region((-120, 35.0), (-123, 38.0))
        self._count_and_check_readed_data(data, curves, 2)
    
    """ this is no longer an applicable test
    @test.skipit
    def test_writes_multiple_results_in_multiple_model(self):
        data = {shapes.Site(16.35, 48.25): {"IMT": "MMI",
                    "IDmodel": "A_MODEL",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [10.0, 20.0, 30.0],
                    "maxProb": 0.9,
                    "minProb": 0.1,
                    "Values": [0.005, 0.007, 0.009],
                    "vs30": 760.0},
                shapes.Site(17.35, 38.25): {"IMT": "MMI",
                    "IDmodel": "A_DIFFERENT_MODEL",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "3_1",
                    "IMLValues": [30.0, 40.0, 50.0],
                    "maxProb": 0.9,
                    "minProb": 0.1,
                    "Values": [1.005, 1.007, 1.009],
                    "vs30": 760.0}}

        self.writer.serialize(data)
        self._is_xml_valid()

        curves = self._read_curves_inside_region((16.0, 49.0), (18.0, 38.0))
        self._count_and_check_readed_data(data, curves, 2)
    """
    @test.skipit
    def _delete_test_file(self):
        try:
            os.remove(os.path.join(test.DATA_DIR, TEST_FILE))
        except OSError:
            pass
    
    @test.skipit
    def _count_and_check_readed_data(self, data, curves, expected_number):
        number_of_curves = 0
        
        for nrml_point, nrml_values in curves:
            number_of_curves += 1

            self.assertTrue(nrml_point in data.keys())
            self.assertTrue(nrml_values in data.values())

        self.assertEqual(expected_number, number_of_curves,
                "the number of readed curves is not as expected!")
    
    @test.skipit
    def _read_curves_inside_region(self, upper_left_cor, lower_right_cor):
        constraint = shapes.RegionConstraint.from_simple(
                upper_left_cor, lower_right_cor)

        reader = nrml.NrmlFile(
                os.path.join(test.DATA_DIR, TEST_FILE))
        
        return reader.filter(constraint)
    
    @test.skipit
    def _result_as_string(self):
        try:
            result = open(os.path.join(test.DATA_DIR, TEST_FILE))
            return result.read()
        finally:
            result.close()
