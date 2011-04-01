# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.




import os
import unittest

from lxml import etree

from tests.utils import helpers
from openquake import shapes
from openquake import xml

from openquake.output import hazard as hazard_output
from openquake.parser import hazard as hazard_parser

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

    def test_serializes_gmf(self):
        path = helpers.get_output_path(GMF_NORUPTURE_TEST_FILE)
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

    def setUp(self):
        self.writer = None
        self.readed_curves = None

    def _initialize_writer(self, path):
        if os.path.isfile(path):
            os.remove(path)

        self.writer = hazard_output.HazardCurveXMLWriter(path)

    def _is_xml_valid(self, path):
        xml_doc = etree.parse(path)

        # test that the doc matches the schema
        schema_path = os.path.join(helpers.SCHEMA_DIR, xml.NRML_SCHEMA_FILE)
        xmlschema = etree.XMLSchema(etree.parse(schema_path))
        xmlschema.assertValid(xml_doc)

    def test_raises_an_error_if_no_curve_is_serialized(self):
        path = helpers.get_output_path(TEST_FILE)
        self._initialize_writer(path)
        self.assertRaises(RuntimeError, self.writer.close)

    def test_writes_a_single_result(self):
        data = [(shapes.Site(-122.5000, 37.5000),
                {"IDmodel": "MMI_3_1",
                "investigationTimeSpan": 50.0,
                "endBranchLabel": "3_1",
                "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02,
                1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                "saPeriod": 0.1,
                "saDamping": 1.0,
                "IMT": "PGA",
                "PoEValues": [9.8728e-01, 9.8266e-01, 9.4957e-01,
                9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01,
                3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01,
                7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03,
                2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]})]

        path = helpers.get_output_path(TEST_FILE_SINGLE_RESULT)
        self._initialize_writer(path)

        self.writer.serialize(data)
        self._is_xml_valid(path)

        self.assertTrue(XML_METADATA in self._result_as_string(path))

        self.readed_curves = self._read_curves(
                (-123.0, 38.0), (-122.0, 35.0),
                TEST_FILE_SINGLE_RESULT)

        self._assert_number_of_curves_is(1)
        self._assert_curves_are(data)

    def test_writes_multiple_results_with_one_branch_level(self):
        data = [(shapes.Site(-122.5000, 37.5000),
                {"IDmodel": "MMI_3_1",
                "investigationTimeSpan": 50.0,
                "endBranchLabel": "3_1",
                "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02,
                1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                "saPeriod": 0.1,
                "saDamping": 1.0,
                "IMT": "PGA",
                "PoEValues": [9.8728e-01, 9.8266e-01, 9.4957e-01,
                9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01,
                3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01,
                7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03,
                2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]}),
                (shapes.Site(-122.4000, 37.5000),
                {"IDmodel": "MMI_3_1",
                "investigationTimeSpan": 50.0,
                "endBranchLabel": "3_1",
                "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02,
                1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                "saPeriod": 0.1,
                "saDamping": 1.0,
                "IMT": "PGA",
                "PoEValues": [9.8784e-01, 9.8405e-01, 9.5719e-01,
                9.1955e-01, 8.5019e-01, 7.4038e-01, 5.9153e-01,
                4.2626e-01, 2.9755e-01, 2.7731e-01, 1.6218e-01,
                8.8035e-02, 4.3499e-02, 1.9065e-02, 7.0442e-03,
                2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]})]

        path = helpers.get_output_path(TEST_FILE_MULTIPLE_ONE_BRANCH)
        self._initialize_writer(path)

        self.writer.serialize(data)
        self._is_xml_valid(path)

        self.readed_curves = self._read_curves(
                (-123.0, 38.0), (-120.0, 35.0),
                TEST_FILE_MULTIPLE_ONE_BRANCH)

        self._assert_number_of_curves_is(2)
        self._assert_curves_are(data)

    @helpers.skipit # re-enable this when the parser will support statistics
    def test_writes_multiple_results_with_statistics(self):
        data = [(shapes.Site(-122.5000, 37.5000),
                {"nrml_id": "nrml_instance_1",
                "hazres_id": "hazard_result_0001",
                "hcfield_id": "hazard_field_one",
                "hcnode_id": "the_hazard_node_1000",
                "IDmodel": "foo",
                "investigationTimeSpan": 50.0,
                "statistics": "quantile",
                "quantileValue": "0.5",
                "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02,
                1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                "saPeriod": 0.1,
                "saDamping": 1.0,
                "IMT": "PGA",
                "PoEValues": [9.8728e-01, 9.8266e-01, 9.4957e-01,
                9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01,
                3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01,
                7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03,
                2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]}),
                (shapes.Site(-122.4000, 37.5000),
                {"IDmodel": "foo",
                "investigationTimeSpan": 50.0,
                "statistics": "quantile",
                "quantileValue": "0.5",
                "IMLValues": [5.0000e-03, 7.0000e-03, 1.3700e-02,
                1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                "saPeriod": 0.1,
                "saDamping": 1.0,
                "IMT": "PGA",
                "PoEValues": [9.8784e-01, 9.8405e-01, 9.5719e-01,
                9.1955e-01, 8.5019e-01, 7.4038e-01, 5.9153e-01,
                4.2626e-01, 2.9755e-01, 2.7731e-01, 1.6218e-01,
                8.8035e-02, 4.3499e-02, 1.9065e-02, 7.0442e-03,
                2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]})]

        path = helpers.get_output_path(TEST_FILE_STATISTICS)
        self._initialize_writer(path)

        self.writer.serialize(data)
        self._is_xml_valid(path)

        self.readed_curves = self._read_curves(
                (-123.0, 38.0), (-120.0, 35.0),
                TEST_FILE_STATISTICS)

        self._assert_number_of_curves_is(2)
        self._assert_curves_are(data)

    def test_writes_the_config_only_once(self):
        data = [(shapes.Site(-122.5000, 37.5000),
                {"IDmodel": "MMI_3_1",
                "investigationTimeSpan": 50.0,
                "endBranchLabel": "3_1",
                "IMLValues": [5.0, 6.0, 7.0],
                "saPeriod": 0.1,
                "saDamping": 1.0,
                "IMT": "PGA",
                "PoEValues": [0.1, 0.2, 0.3]}),
                (shapes.Site(-122.4000, 37.5000),
                {"IDmodel": "MMI_3_1",
                "investigationTimeSpan": 50.0,
                "endBranchLabel": "3_2",
                "IMLValues": [5.0, 6.0, 7.0],
                "saPeriod": 0.1,
                "saDamping": 1.0,
                "IMT": "PGA",
                "PoEValues": [0.4, 0.5, 0.6]})]

        path = helpers.get_output_path(TEST_FILE_CONFIG_ONCE)
        self._initialize_writer(path)

        self.writer.serialize(data)
        self._is_xml_valid(path)

    def test_writes_multiple_results_with_different_branch_levels(self):
        data = [(shapes.Site(-122.5000, 37.5000),
                {"IDmodel": "MMI_3_1",
                "investigationTimeSpan": 50.0,
                "endBranchLabel": "3_1",
                "IMLValues": [5.0, 6.0, 7.0],
                "saPeriod": 0.1,
                "saDamping": 1.0,
                "IMT": "PGA",
                "PoEValues": [0.1, 0.2, 0.3]}),
                (shapes.Site(-122.5000, 37.5000),
                {"IDmodel": "MMI_3_1",
                "investigationTimeSpan": 50.0,
                "endBranchLabel": "3_2",
                "IMLValues": [5.0, 6.0, 7.0],
                "saPeriod": 0.1,
                "saDamping": 1.0,
                "IMT": "PGA",
                "PoEValues": [0.1, 0.2, 0.3]}),
                (shapes.Site(-122.4000, 37.5000),
                {"IDmodel": "MMI_3_1",
                "investigationTimeSpan": 50.0,
                "endBranchLabel": "3_2",
                "IMLValues": [8.0, 9.0, 10.0],
                "saPeriod": 0.1,
                "saDamping": 1.0,
                "IMT": "PGA",
                "PoEValues": [0.1, 0.2, 0.3]})]

        path = helpers.get_output_path(
                TEST_FILE_MULTIPLE_DIFFERENT_BRANCHES)

        self._initialize_writer(path)

        self.writer.serialize(data)
        self._is_xml_valid(path)

        self.readed_curves = self._read_curves(
                (-123.0, 38.0), (-120.0, 35.0),
                TEST_FILE_MULTIPLE_DIFFERENT_BRANCHES)

        self._assert_number_of_curves_is(3)
        self._assert_curves_are(data)

    def _delete_test_file(self, path):
        try:
            os.remove(path)
        except OSError:
            pass

    def _assert_number_of_curves_is(self, expected_number):
        number_of_curves = 0

        for nrml_point, nrml_values in self.readed_curves:
            number_of_curves += 1

        self.assertEqual(expected_number, number_of_curves)

    def _assert_curves_are(self, curves):
        expected_sites = [site_and_curve[0] for site_and_curve in curves]
        expected_curves = [site_and_curve[1] for site_and_curve in curves]

        for nrml_point, nrml_values in self.readed_curves:
            self.assertTrue(nrml_point in expected_sites)
            self.assertTrue(nrml_values in expected_curves)

    def _read_curves(self, upper_left_cor, lower_right_cor, test_file):
        constraint = shapes.RegionConstraint.from_simple(
                upper_left_cor, lower_right_cor)

        reader = hazard_parser.NrmlFile(
                helpers.get_output_path(test_file))

        return reader.filter(constraint)

    def _result_as_string(self, path):
        try:
            result = open(path)
            return result.read()
        finally:
            result.close()
