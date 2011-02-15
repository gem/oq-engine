# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from lxml import etree

from openquake import logs
from utils import test
from openquake import shapes
from openquake import xml

from openquake.output import hazard as hazard_output
from openquake.parser import hazard as hazard_parser

LOG = logs.LOG

TEST_FILE = "hazard-curves.xml"
TEST_FILE_SINGLE_RESULT = "hazard-curves-single.xml"
TEST_FILE_MULTIPLE_ONE_BRANCH = "hazard-curves-multiple-one-branch.xml"
TEST_FILE_STATISTICS = "hazard-curves-statistics.xml"
TEST_FILE_CONFIG_ONCE = "hazard-curves-config-only-once.xml"
TEST_FILE_MULTIPLE_DIFFERENT_BRANCHES = \
    "hazard-curves-multiple-different-branches.xml"


XML_METADATA = "<?xml version='1.0' encoding='UTF-8'?>"

GMF_NORUPTURE_TEST_FILE = "gmf.xml"
GMF_NORUPTURE_TEST_DATA = {
    shapes.Site(-117, 40): {'groundMotion': 0.0}, 
    shapes.Site(-116, 40): {'groundMotion': 0.1},
    shapes.Site(-116, 41): {'groundMotion': 0.2},
    shapes.Site(-117, 41): {'groundMotion': 0.3}}

class GMFXMLWriterTestCase(unittest.TestCase):
    """Unit tests for the GMFXMLWriter class, which serializes
    ground motion fields to NRML."""

    # TODO (LB): this is a bad unit test.
    # it requires both the hazard parser and serializer
    # and will break if we update one of those pieces independently
    @test.skipit
    def test_serializes_gmf(self):
        path = test.do_test_output_file(GMF_NORUPTURE_TEST_FILE)
        writer = hazard_output.GMFXMLWriter(path)
        writer.serialize(GMF_NORUPTURE_TEST_DATA)

        check_data = {}
        reader = hazard_parser.GMFReader(path)
        for curr_site, curr_attribute in reader:
            check_data[curr_site] = curr_attribute

        self.assertEqual(check_data, GMF_NORUPTURE_TEST_DATA)


class HazardCurveXMLWriterTestCase(unittest.TestCase):
    """Unit tests for the HazardCurveXMLWriter class, which serializes
    hazard curves to NRML."""

    def _remove_and_write_file(self, path):
        if os.path.isfile(path):
            os.remove(path)
        self.writer = hazard_output.HazardCurveXMLWriter(path)

    def _is_xml_valid(self, path):
        xml_doc = etree.parse(path)

        # test that the doc matches the schema
        schema_path = os.path.join(test.SCHEMA_DIR, xml.NRML_SCHEMA_FILE)
        print "schema_path is %s" % schema_path
        xmlschema = etree.XMLSchema(etree.parse(schema_path))
        xmlschema.assertValid(xml_doc)

    def test_raises_an_error_if_no_curve_is_serialized(self):
        path = test.do_test_output_file(TEST_FILE)
        self._remove_and_write_file(path)
        self.assertRaises(RuntimeError, self.writer.close)

    def test_writes_a_single_result(self):
        data = [(shapes.Site(-122.5000, 37.5000), 
                {   "IDmodel": "MMI_3_1",
                    "investigationTimeSpan": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "poE": [9.8728e-01, 9.8266e-01, 9.4957e-01, 
                    9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01, 
                    3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01, 
                    7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03, 
                    2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]})]

        path = test.do_test_output_file(TEST_FILE_SINGLE_RESULT)
        self._remove_and_write_file(path)

        self.writer.serialize(data)
        self._is_xml_valid(path)
        
        self.assertTrue(XML_METADATA in self._result_as_string(path))
        
        # reading
        # TODO(fab): restore this as soon as the parsers are updated
        #curves = self._read_curves_inside_region((-123.0, 38.0), (-122.0, 35.0))
        #self._count_and_check_readed_data(data, curves, 1)

    def test_writes_multiple_results_with_one_branch_level(self):
        data = [(shapes.Site(-122.5000, 37.5000), 
                 {  "IDmodel": "MMI_3_1",
                    "investigationTimeSpan": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "poE": [9.8728e-01, 9.8266e-01, 9.4957e-01, 
                    9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01, 
                    3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01, 
                    7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03, 
                    2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]}),
                (shapes.Site(-122.4000, 37.5000), 
                 {  "IDmodel": "MMI_3_1",
                    "investigationTimeSpan": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "poE": [9.8784e-01, 9.8405e-01, 9.5719e-01, 
                    9.1955e-01, 8.5019e-01, 7.4038e-01, 5.9153e-01, 
                    4.2626e-01, 2.9755e-01, 2.7731e-01, 1.6218e-01, 
                    8.8035e-02, 4.3499e-02, 1.9065e-02, 7.0442e-03, 
                    2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]})]

        path = test.do_test_output_file(TEST_FILE_MULTIPLE_ONE_BRANCH)
        self._remove_and_write_file(path)

        self.writer.serialize(data)
        self._is_xml_valid(path)

        # TODO(fab): restore this as soon as the parsers are updated
        #curves = self._read_curves_inside_region((-123, 38.0), (-120, 35.0))
        #self._count_and_check_readed_data(data, curves, 2)

    def test_writes_multiple_results_with_statistics(self):
        data = [(shapes.Site(-122.5000, 37.5000), 
                 {
                    "nrml_id": "nrml_instance_1",
                    "hazres_id": "hazard_result_0001",
                    "hcfield_id": "hazard_field_one",
                    "hcnode_id": "the_hazard_node_1000",
                    "IDmodel": "foo",
                    "investigationTimeSpan": 50.0,
                    "statistics": "quantile",
                    "quantileValue": "0.5",
                    "IML": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "poE": [9.8728e-01, 9.8266e-01, 9.4957e-01, 
                    9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01, 
                    3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01, 
                    7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03, 
                    2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]}),
                (shapes.Site(-122.4000, 37.5000), 
                 {  "IDmodel": "foo",
                    "investigationTimeSpan": 50.0,
                    "statistics": "quantile",
                    "quantileValue": "0.5",
                    "IML": [5.0000e-03, 7.0000e-03, 1.3700e-02, 
                    1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02, 
                    7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01, 
                    2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01, 
                    7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "poE": [9.8784e-01, 9.8405e-01, 9.5719e-01, 
                    9.1955e-01, 8.5019e-01, 7.4038e-01, 5.9153e-01, 
                    4.2626e-01, 2.9755e-01, 2.7731e-01, 1.6218e-01, 
                    8.8035e-02, 4.3499e-02, 1.9065e-02, 7.0442e-03, 
                    2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]})]

        path = test.do_test_output_file(TEST_FILE_STATISTICS)
        self._remove_and_write_file(path)

        self.writer.serialize(data)
        self._is_xml_valid(path)

        # TODO(fab): restore this as soon as the parsers are updated
        #curves = self._read_curves_inside_region((-123, 38.0), (-120, 35.0))
        #self._count_and_check_readed_data(data, curves, 2)

    def test_writes_the_config_only_once(self):
        data = [(shapes.Site(-122.5000, 37.5000), 
                 {      "IDmodel": "MMI_3_1",
                        "investigationTimeSpan": 50.0,
                        "endBranchLabel": "3_1",
                        "IML": [5.0, 6.0, 7.0],
                        "saPeriod": 0.1,
                        "saDamping": 1.0,
                        "IMT": "PGA",
                        "poE": [0.1, 0.2, 0.3]}),
                (shapes.Site(-122.4000, 37.5000), 
                 {      "IDmodel": "MMI_3_1",
                        "investigationTimeSpan": 50.0,
                        "endBranchLabel": "3_2",
                        "IML": [5.0, 6.0, 7.0],
                        "saPeriod": 0.1,
                        "saDamping": 1.0,
                        "IMT": "PGA",
                        "poE": [0.4, 0.5, 0.6]})
                ]
        
        path = test.do_test_output_file(TEST_FILE_CONFIG_ONCE)
        self._remove_and_write_file(path)

        self.writer.serialize(data)
        self._is_xml_valid(path)

    def test_writes_multiple_results_with_different_branch_levels(self):
        data = [(shapes.Site(-122.5000, 37.5000), 
                 {  "IDmodel": "MMI_3_1",
                    "investigationTimeSpan": 50.0,
                    "endBranchLabel": "3_1",
                    "IML": [5.0, 6.0, 7.0],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "poE": [0.1, 0.2, 0.3]}),
                (shapes.Site(-122.5000, 37.5000), 
                 {  "IDmodel": "MMI_3_1",
                    "investigationTimeSpan": 50.0,
                    "endBranchLabel": "3_2",
                    "IML": [5.0, 6.0, 7.0],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "poE": [0.1, 0.2, 0.3]}),
                (shapes.Site(-122.4000, 37.5000), 
                 {  "IDmodel": "MMI_3_1",
                    "investigationTimeSpan": 50.0,
                    "endBranchLabel": "3_2",
                    "IML": [8.0, 9.0, 10.0],
                    "saPeriod": 0.1,
                    "saDamping": 1.0,
                    "IMT": "PGA",
                    "poE": [0.1, 0.2, 0.3]})]

        path = test.do_test_output_file(TEST_FILE_MULTIPLE_DIFFERENT_BRANCHES)
        self._remove_and_write_file(path)

        self.writer.serialize(data)
        self._is_xml_valid(path)

        # TODO(fab): restore this as soon as the parsers are updated
        #curves = self._read_curves_inside_region((-123, 38.0), (-120, 35.0))
        #self._count_and_check_readed_data(data, curves, 2)
        
    #@test.skipit
    def _delete_test_file(self, path):
        try:
            os.remove(path)
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

        reader = hazard_parser.NrmlFile(test.do_test_output_file(TEST_FILE))
        return reader.filter(constraint)

    def _result_as_string(self, path):
        try:
            result = open(path)
            return result.read()
        finally:
            result.close()
