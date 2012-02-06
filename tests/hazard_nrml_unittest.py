# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
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

from openquake import shapes
from openquake import xml

from openquake.output import hazard_disagg
from openquake.output import hazard as hazard_output
from openquake.parser import hazard as hazard_parser

from tests.utils import helpers

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
        self.read_curves = None

    def _initialize_writer(self, path):
        if os.path.isfile(path):
            os.remove(path)

        self.writer = hazard_output.HazardCurveXMLWriter(path)
        self.writer.initialize()

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

        self.assertTrue(xml.validates_against_xml_schema(path))
        self.assertTrue(XML_METADATA in self._result_as_string(path))

        self.read_curves = self._read_curves(
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

        self.assertTrue(xml.validates_against_xml_schema(path))

        self.read_curves = self._read_curves(
                (-123.0, 38.0), (-120.0, 35.0),
                TEST_FILE_MULTIPLE_ONE_BRANCH)

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
        self.assertTrue(xml.validates_against_xml_schema(path))

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

        self.assertTrue(xml.validates_against_xml_schema(path))

        self.read_curves = self._read_curves(
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

        for nrml_point, nrml_values in self.read_curves:
            number_of_curves += 1

        self.assertEqual(expected_number, number_of_curves)

    def _assert_curves_are(self, curves):
        expected_sites = [site_and_curve[0] for site_and_curve in curves]
        expected_curves = [site_and_curve[1] for site_and_curve in curves]

        for nrml_point, nrml_values in self.read_curves:
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


class DisaggregationBinaryMatrixXMLWriterTestCase(unittest.TestCase):

    NAMESPACES = {"nrml": xml.NRML_NS, "gml": xml.GML_NS}
    FILENAME = "dbinary.xml"
    POE = 0.1
    IMT = "PGA"
    SUBSETS = [
        'MagPMF',
        'MagDistPMF',
        'MagDistEpsPMF',
        'LatLonMagEpsPMF',
        'FullDisaggMatrix',
    ]
    END_BRANCH_LABEL = "1"
    STATISTICS = "mean"
    QUANTILE_VALUE = 0.1

    def setUp(self):
        try:
            os.remove(self.FILENAME)
        except OSError:
            pass

        self.writer = hazard_disagg.DisaggregationBinaryMatrixXMLWriter(
            self.FILENAME, self.POE, self.IMT, self.SUBSETS,
            self.END_BRANCH_LABEL, self.STATISTICS, self.QUANTILE_VALUE)

    def test_result_field_attrs(self):
        """Test that the various disaggregationResultField attrs are written
        correctly (including all of the optional attributes)."""
        # write a single node just to create a valid document
        self.writer.open()
        self.writer.write(shapes.Site(0.0, 0.0),
                          {"groundMotionValue": 0.25, "path": "filea"})
        self.writer.close()

        [disagg_field] = self._xpath(
            "/nrml:nrml/nrml:disaggregationResultField")

        attrib = disagg_field.attrib

        self.assertEquals(str(self.POE), attrib['poE'])
        self.assertEquals(self.IMT, attrib['IMT'])
        self.assertEquals(self.END_BRANCH_LABEL, attrib['endBranchLabel'])
        self.assertEquals(self.STATISTICS, attrib['statistics'])
        self.assertEquals(str(self.QUANTILE_VALUE), attrib['quantileValue'])

        self.assertTrue(xml.validates_against_xml_schema(self.FILENAME))

    def test_write_single_result_node(self):
        result_data = dict(groundMotionValue=0.25, path="filea")
        expected_result_attrib = dict(groundMotionValue="0.25", path="filea")

        self.writer.open()
        self.writer.write(shapes.Site(1.0, 2.0), result_data)
        self.writer.close()

        [site_node] = self._xpath("//gml:pos")
        disagg_nodes = self._xpath("//nrml:disaggregationResultNode")
        [result] = self._xpath("//nrml:disaggregationResult")

        self.assertEquals("1.0 2.0", site_node.text)
        self.assertEquals(1, len(disagg_nodes))
        self.assertEquals(expected_result_attrib, result.attrib)

        self.assertTrue(xml.validates_against_xml_schema(self.FILENAME))

    def test_write_multiple_result_nodes(self):
        result_data = [
            dict(groundMotionValue=0.25, path="filea"),
            dict(groundMotionValue=0.76, path="fileb"),
            dict(groundMotionValue=0.11, path="filec"),
        ]

        expected_result_attrib = [
            dict(groundMotionValue="0.25", path="filea"),
            dict(groundMotionValue="0.76", path="fileb"),
            dict(groundMotionValue="0.11", path="filec"),
        ]

        self.writer.open()
        self.writer.write(shapes.Site(1.0, 2.0), result_data[0])
        self.writer.write(shapes.Site(2.0, 3.0), result_data[1])
        self.writer.write(shapes.Site(3.0, 4.0), result_data[2])
        self.writer.close()

        site_nodes = self._xpath("//gml:pos")
        disagg_nodes = self._xpath("//nrml:disaggregationResultNode")
        results = self._xpath("//nrml:disaggregationResult")

        self.assertEquals(3, len(site_nodes))
        self.assertEquals(3, len(disagg_nodes))
        self.assertEquals(3, len(results))

        self.assertEquals("1.0 2.0", site_nodes[0].text)
        self.assertEquals("2.0 3.0", site_nodes[1].text)
        self.assertEquals("3.0 4.0", site_nodes[2].text)

        for i, res in enumerate(results):
            self.assertEquals(expected_result_attrib[i], res.attrib)

        self.assertTrue(xml.validates_against_xml_schema(self.FILENAME))

    def test_serialize(self):
        data = [(shapes.Site(1.0, 1.0),
                {"groundMotionValue": 0.25, "path": "filea"}),
                (shapes.Site(1.0, 2.0),
                {"groundMotionValue": 0.35, "path": "fileb"})]

        self.writer.serialize(data)

        self.assertTrue(xml.validates_against_xml_schema(self.FILENAME))

    def _xpath(self, exp):
        doc = etree.parse(self.FILENAME)
        return doc.xpath(exp, namespaces=self.NAMESPACES)
