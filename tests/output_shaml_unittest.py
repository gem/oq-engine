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

# TODO (ac): Test validation against the schema!
class OutputShamlTestCase(unittest.TestCase):

    def setUp(self):
        self.writer = shaml.ShamlWriter(os.path.join(test.DATA_DIR, TEST_FILE))

    def tearDown(self):
        try:
            os.remove(os.path.join(test.DATA_DIR, TEST_FILE))
        except OSError:
            pass

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
        
        # reading
        curves = self._read_curves_inside_region((16.0, 49.0), (17.0, 48.0))
        self._count_and_check_readed_data(data, curves, 1)

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

        curves = self._read_curves_inside_region((16.0, 49.0), (18.0, 38.0))
        self._count_and_check_readed_data(data, curves, 2)

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

        curves = self._read_curves_inside_region((16.0, 49.0), (18.0, 38.0))
        self._count_and_check_readed_data(data, curves, 2)

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

        curves = self._read_curves_inside_region((16.0, 49.0), (18.0, 38.0))
        self._count_and_check_readed_data(data, curves, 2)

    def _count_and_check_readed_data(self, data, curves, expected_number):
        counter = 0
        
        for shaml_point, shaml_values in curves:
            counter = counter + 1

            self.assertTrue(shaml_point in data.keys())
            self.assertTrue(shaml_values in data.values())

        self.assertEqual(expected_number, counter,
                "the number of readed curves is not as expected!")

    def _read_curves_inside_region(self, upper_left_cor, lower_right_cor):
        constraint = shapes.RegionConstraint.from_simple(
                upper_left_cor, lower_right_cor)

        reader = shaml_output.ShamlOutputFile(
                os.path.join(test.DATA_DIR, TEST_FILE))
        
        return reader.filter(constraint)

    def _result_as_string(self):
        try:
            result = open(os.path.join(test.DATA_DIR, TEST_FILE))
            return result.read()
        finally:
            result.close()
