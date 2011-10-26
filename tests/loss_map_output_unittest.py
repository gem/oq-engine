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

"""
Tests for the serialization of loss maps to NRML format.
"""

import os
import unittest

from lxml import etree

from openquake import nrml
from openquake import shapes
from openquake import xml
from tests.utils import helpers

from openquake.output import risk as risk_output

TEST_LOSS_MAP_XML_OUTPUT_PATH = helpers.get_output_path('test-loss-map.xml')
TEST_NON_DET_LOSS_MAP_XML_OUTPUT_PATH = helpers.get_output_path(
    'test-non-det-loss-map.xml')
EXPECTED_TEST_LOSS_MAP = helpers.get_data_path('expected-test-loss-map.xml')
EXPECTED_TEST_NON_DET_LOSS_MAP = helpers.get_data_path(
    'expected-non-det-test-loss-map.xml')

NRML_SCHEMA_PATH = nrml.nrml_schema_file()

LOSS_MAP_METADATA = {
    'nrmlID': 'test_nrml_id',
    'riskResultID': 'test_rr_id',
    'lossMapID': 'test_lm_id',
    'endBranchLabel': 'test_ebl',
    'lossCategory': 'economic_loss',
    'unit': 'EUR'}


LOSS_MAP_NON_DET_METADATA = {
    'nrmlID': 'test_nrml_id',
    'riskResultID': 'test_rr_id',
    'lossMapID': 'test_lm_id',
    'endBranchLabel': 'test_ebl',
    'lossCategory': 'economic_loss',
    'unit': 'EUR',
    'timeSpan': '1.5',
    'poE': '0.5'}

SITE_A = shapes.Site(-117.0, 38.0)
SITE_A_ASSET_ONE = {'assetID': 'a1711'}
SITE_A_LOSS_ONE = {'mean_loss': 0, 'stddev_loss': 100}
SITE_A_NON_DET_LOSS_ONE = {'value': 12621260.1168}

SITE_A_ASSET_TWO = {'assetID': 'a1712'}
SITE_A_LOSS_TWO = {'mean_loss': 5, 'stddev_loss': 2000.0}
SITE_A_NON_DET_LOSS_TWO = {'value': 1913748.91617}

SITE_B = shapes.Site(-118.0, 39.0)
SITE_B_ASSET_ONE = {'assetID': 'a1713'}
SITE_B_LOSS_ONE = {'mean_loss': 120000.0, 'stddev_loss': 2000.0}
SITE_B_NON_DET_LOSS_ONE = {'value': 13223148.4443}

SAMPLE_LOSS_MAP_DATA = [
    LOSS_MAP_METADATA,
    (SITE_A, [(SITE_A_LOSS_ONE, SITE_A_ASSET_ONE),
    (SITE_A_LOSS_TWO, SITE_A_ASSET_TWO)]),
    (SITE_B, [(SITE_B_LOSS_ONE, SITE_B_ASSET_ONE)])]

SAMPLE_LOSS_MAP_NON_DET_DATA = [
    LOSS_MAP_NON_DET_METADATA,
    (SITE_A, [(SITE_A_NON_DET_LOSS_ONE, SITE_A_ASSET_ONE),
    (SITE_A_NON_DET_LOSS_TWO, SITE_A_ASSET_TWO)]),
    (SITE_B, [(SITE_B_NON_DET_LOSS_ONE, SITE_B_ASSET_ONE)])]

GML_ID_KEY = '{%s}id' % xml.GML_NS

DEFAULT_METADATA = risk_output.LossMapXMLWriter.DEFAULT_METADATA

DEFAULT_NON_DET_METADATA = \
        risk_output.LossMapNonDeterministicXMLWriter.DEFAULT_METADATA

LOSS_MAP_NODE_ATTRS = ('endBranchLabel', 'lossCategory', 'unit')
LOSS_MAP_NON_DET_NODE_ATTRS = ('endBranchLabel', 'lossCategory', 'unit',
    'timeSpan', 'poE')


class LossMapOutputTestCase(unittest.TestCase):
    """Confirm that XML output (Deterministic/Non Deterministic) from risk
    engine is valid against schema, as well as correct given the inputs."""

    def setUp(self):
        self.xml_writer = \
            risk_output.LossMapXMLWriter(TEST_LOSS_MAP_XML_OUTPUT_PATH)
        self.xml_non_det_writer = \
            risk_output.LossMapNonDeterministicXMLWriter(
                    TEST_NON_DET_LOSS_MAP_XML_OUTPUT_PATH)

    def tearDown(self):
        self.xml_writer = None
        self.xml_non_det_writer = None
        os.remove(TEST_LOSS_MAP_XML_OUTPUT_PATH)
        #os.remove(TEST_NON_DET_LOSS_MAP_XML_OUTPUT_PATH)

    def test_loss_map_output_writes_and_validates(self):
        xml_writer = \
            risk_output.LossMapXMLWriter(TEST_LOSS_MAP_XML_OUTPUT_PATH)
        xml_writer.serialize(SAMPLE_LOSS_MAP_DATA)
        self.assertTrue(
            xml.validates_against_xml_schema(TEST_LOSS_MAP_XML_OUTPUT_PATH,
            NRML_SCHEMA_PATH),
            "NRML instance file %s does not validate against schema" % \
            TEST_LOSS_MAP_XML_OUTPUT_PATH)

        xml_non_det_writer = \
            risk_output.LossMapNonDeterministicXMLWriter(
                    TEST_NON_DET_LOSS_MAP_XML_OUTPUT_PATH)
        xml_non_det_writer.serialize(SAMPLE_LOSS_MAP_NON_DET_DATA)
        self.assertTrue(
            xml.validates_against_xml_schema(
                TEST_NON_DET_LOSS_MAP_XML_OUTPUT_PATH, NRML_SCHEMA_PATH),
            "NRML instance file %s does not validate against schema" % \
            TEST_NON_DET_LOSS_MAP_XML_OUTPUT_PATH)

    def test_write_metadata(self):
        """
        Tests the :py:meth:`risk_output.LossMapXMLWriter.write_metadata`
        method using a normal use case.
        """
        for xml_writer, loss_map_data in ((self.xml_writer, LOSS_MAP_METADATA),
                (self.xml_non_det_writer, LOSS_MAP_NON_DET_METADATA)):
            xml_writer.write_metadata(loss_map_data)

            # Check the gml:ids first
            for key, node in (
                ('nrmlID', xml_writer.root_node),
                ('riskResultID', xml_writer.risk_result_node),
                ('lossMapID', xml_writer.loss_map_node)):

                self.assertEqual(
                    loss_map_data[key],
                    node.attrib[GML_ID_KEY])

            if isinstance(xml_writer,
                    risk_output.LossMapNonDeterministicXMLWriter):
                loss_map_node_attrs = LOSS_MAP_NON_DET_NODE_ATTRS
            else:
                loss_map_node_attrs = LOSS_MAP_NODE_ATTRS

            # Verify the <lossMap> attributes
            for key in loss_map_node_attrs:
                self.assertEqual(
                    loss_map_data[key],
                    xml_writer.loss_map_node.attrib[key])

    def test_write_metadata_with_some_defaults(self):
        """
        Tests the :py:meth:`risk_output.LossMapXMLWriter.write_metadata`
        method using only partial metadata. For the metadata items not
        specified, this test ensures that defaults are used.
        """
        partial_meta = {
            'lossMapID': 'test_lm_id',
            'endBranchLabel': 'test_ebl',
            'lossCategory': 'economic_loss'}

        for xml_writer, loss_map_data in ((self.xml_writer, LOSS_MAP_METADATA),
                (self.xml_non_det_writer, LOSS_MAP_NON_DET_METADATA)):

            xml_writer.write_metadata(loss_map_data)
            xml_writer.write_metadata(partial_meta)

            self.assertEqual(
                DEFAULT_METADATA['nrmlID'],
                xml_writer.root_node.attrib[GML_ID_KEY])

            self.assertEqual(
                DEFAULT_METADATA['riskResultID'],
                xml_writer.risk_result_node.attrib[GML_ID_KEY])

            self.assertEqual(
                DEFAULT_METADATA['unit'],
                xml_writer.loss_map_node.attrib['unit'])

    def test_serialize_with_no_meta(self):
        """
        This test serializes some sample data to an XML file. The sample data
        does not include metadata. This test will verify that defaults are used
        for all metadata.
        """
        for xml_writer, loss_map_data in ((self.xml_writer, LOSS_MAP_METADATA),
                (self.xml_non_det_writer, LOSS_MAP_NON_DET_METADATA)):

            if isinstance(xml_writer,
                    risk_output.LossMapNonDeterministicXMLWriter):
                loss_map_node_attrs = LOSS_MAP_NON_DET_NODE_ATTRS
                # everything but metadata
                test_data = SAMPLE_LOSS_MAP_NON_DET_DATA[1:]
                default_metadata = DEFAULT_NON_DET_METADATA
            else:
                loss_map_node_attrs = LOSS_MAP_NODE_ATTRS
                # everything but metadata
                test_data = SAMPLE_LOSS_MAP_DATA[1:]
                default_metadata = DEFAULT_METADATA

            xml_writer.serialize(test_data)

            for key, node, in (
                ('nrmlID', xml_writer.root_node),
                ('riskResultID', xml_writer.risk_result_node),
                ('lossMapID', xml_writer.loss_map_node)):
                self.assertEqual(
                    default_metadata[key],
                    node.attrib[GML_ID_KEY])

            for key in loss_map_node_attrs:
                self.assertEqual(
                    default_metadata[key],
                    xml_writer.loss_map_node.attrib[key])

    def test_loss_map_xml_content_is_correct(self):
        """
        This tests writes some sample data to an xml file, then verifies the
        contents.

        In particular, we want to make sure the site and loss data is correct.
        """

        def get_xml_elems_list(path, events=('start', 'end')):
            """
            Use :py:function:`lxml.etree.iterparse` to build a list of the
            elements in the given xml file.

            Note: This function will hold element data in a single list. This
            should work fine for small files, but may not perform well for
            large files.

            :param path: Path to an xml file, including file name
            :param events: Specify open tags ('start',), close tags ('end',),
                or both ('start', 'end'). Default is both.

            :returns: A list of 2-tuples.
                The first tuple item will be 'start' or 'end'.
                The second will be a :py:class:`lxml.etree._Element` object
            """
            elems = []

            for event, elem in etree.iterparse(path, events=events):
                elems.append((event, elem))

            return elems

        for xml_writer, loss_map_data in (
                (self.xml_writer, SAMPLE_LOSS_MAP_DATA),
                (self.xml_non_det_writer, SAMPLE_LOSS_MAP_NON_DET_DATA)):
            xml_writer.serialize(loss_map_data)

            if isinstance(xml_writer,
                    risk_output.LossMapNonDeterministicXMLWriter):
                expected_loss_map = EXPECTED_TEST_NON_DET_LOSS_MAP
                test_loss_map_xml_output_path = \
                        TEST_NON_DET_LOSS_MAP_XML_OUTPUT_PATH
            else:
                expected_loss_map = EXPECTED_TEST_LOSS_MAP
                test_loss_map_xml_output_path = TEST_LOSS_MAP_XML_OUTPUT_PATH

            expected_elems = get_xml_elems_list(expected_loss_map)
            actual_elems = get_xml_elems_list(test_loss_map_xml_output_path)

            # first, make sure out elem list from the expected data
            # is _not_ empty (otherwise, this would be an epic test fail)
            self.assertTrue(len(expected_elems) > 0)

            # then verify the lengths of the elem lists are same
            self.assertEqual(len(expected_elems), len(actual_elems))

            # and finally, verify the actual contents are correct
            for i, (event, elem) in enumerate(expected_elems):
                actual_event, actual_elem = actual_elems[i]
                self.assertEqual(event, actual_event)
                self.assertEqual(elem.items(), actual_elem.items())
