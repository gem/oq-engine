# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

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

from openquake.db.models import ExposureData
from openquake.output import risk as risk_output

TEST_LOSS_MAP_XML_OUTPUT_PATH = helpers.get_output_path('test-loss-map.xml')
TEST_NON_SCN_LOSS_MAP_XML_OUTPUT_PATH = helpers.get_output_path(
    'test-non-det-loss-map.xml')
EXPECTED_TEST_LOSS_MAP = helpers.get_data_path('expected-test-loss-map.xml')
EXPECTED_TEST_NON_SCN_LOSS_MAP = helpers.get_data_path(
    'expected-non-det-test-loss-map.xml')

NRML_SCHEMA_PATH = nrml.nrml_schema_file()

LOSS_MAP_METADATA = {
    'nrmlID': 'test_nrml_id',
    'riskResultID': 'test_rr_id',
    'lossMapID': 'test_lm_id',
    'endBranchLabel': 'test_ebl',
    'lossCategory': 'economic_loss',
    'unit': 'EUR'}

SITE_A = shapes.Site(-117.0, 38.0)
SITE_A_ASSET_ONE = {'assetID': 'a1711'}
SITE_A_LOSS_ONE = {'mean_loss': 0, 'stddev_loss': 100}

SITE_A_ASSET_TWO = {'assetID': 'a1712'}
SITE_A_LOSS_TWO = {'mean_loss': 5, 'stddev_loss': 2000.0}

SITE_B = shapes.Site(-118.0, 39.0)
SITE_B_ASSET_ONE = {'assetID': 'a1713'}
SITE_B_LOSS_ONE = {'mean_loss': 120000.0, 'stddev_loss': 2000.0}

SAMPLE_LOSS_MAP_DATA = [
    LOSS_MAP_METADATA,
    (SITE_A, [(SITE_A_LOSS_ONE, SITE_A_ASSET_ONE),
    (SITE_A_LOSS_TWO, SITE_A_ASSET_TWO)]),
    (SITE_B, [(SITE_B_LOSS_ONE, SITE_B_ASSET_ONE)])]

GML_ID_KEY = '{%s}id' % xml.GML_NS

LOSS_MAP_NODE_ATTRS = ('endBranchLabel', 'lossCategory', 'unit')
LOSS_MAP_NON_SCN_NODE_ATTRS = ('endBranchLabel', 'lossCategory', 'unit',
    'timeSpan', 'poE')


class LossMapOutputTestCase(unittest.TestCase):
    """
    Confirm that XML output (Scenario/Non Scenario) from risk
    engine is valid against schema, as well as correct given the inputs.
    """

    def setUp(self):
        # sample data to serialize for the non scenario writer
        asset_1 = ExposureData()
        asset_1.asset_ref = "a1711"

        asset_2 = ExposureData()
        asset_2.asset_ref = "a1712"

        asset_3 = ExposureData()
        asset_3.asset_ref = "a1713"

        self.non_scenario_mdata = {
            'nrmlID': 'test_nrml_id',
            'riskResultID': 'test_rr_id',
            'lossMapID': 'test_lm_id',
            'endBranchLabel': 'test_ebl',
            'lossCategory': 'economic_loss',
            'unit': 'EUR',
            'timeSpan': 1.5,
            'poE': 0.5
        }

        self.non_scenario_data = [self.non_scenario_mdata,
            (SITE_A, [({"value": 12621260.1168}, asset_1),
            ({"value": 1913748.91617}, asset_2)]),
            (SITE_B, [({"value": 13223148.4443}, asset_3)])]

        self.xml_writer = risk_output.LossMapXMLWriter(
                TEST_LOSS_MAP_XML_OUTPUT_PATH)

        self.xml_non_scn_writer = risk_output.LossMapNonScenarioXMLWriter(
                TEST_NON_SCN_LOSS_MAP_XML_OUTPUT_PATH)

    def tearDown(self):
        self.xml_writer = None
        self.xml_non_scn_writer = None
        if os.path.exists(TEST_LOSS_MAP_XML_OUTPUT_PATH):
            os.remove(TEST_LOSS_MAP_XML_OUTPUT_PATH)

    def test_loss_map_output_writes_and_validates(self):
        xml_writer = risk_output.LossMapXMLWriter(
            TEST_LOSS_MAP_XML_OUTPUT_PATH)
        xml_writer.serialize(SAMPLE_LOSS_MAP_DATA)
        self.assertTrue(
            xml.validates_against_xml_schema(TEST_LOSS_MAP_XML_OUTPUT_PATH,
            NRML_SCHEMA_PATH),
            "NRML instance file %s does not validate against schema" %
            TEST_LOSS_MAP_XML_OUTPUT_PATH)

        xml_non_det_writer = risk_output.LossMapNonScenarioXMLWriter(
            TEST_NON_SCN_LOSS_MAP_XML_OUTPUT_PATH)
        xml_non_det_writer.serialize(self.non_scenario_data)
        self.assertTrue(
            xml.validates_against_xml_schema(
                TEST_NON_SCN_LOSS_MAP_XML_OUTPUT_PATH, NRML_SCHEMA_PATH),
            "NRML instance file %s does not validate against schema" %
            TEST_NON_SCN_LOSS_MAP_XML_OUTPUT_PATH)

    def test_write_metadata(self):
        """
        Tests the :py:meth:`risk_output.LossMapXMLWriter.write_metadata`
        method using a normal use case.
        """
        for xml_writer, loss_map_data in ((self.xml_writer, LOSS_MAP_METADATA),
                (self.xml_non_scn_writer, self.non_scenario_mdata)):
            xml_writer.write_metadata(loss_map_data)

            # Check the gml:ids first
            for key, node in (
                ('nrmlID', xml_writer.root_node),
                ('riskResultID', xml_writer.risk_result_node),
                ('lossMapID', xml_writer.map_container)):

                self.assertEqual(
                    loss_map_data[key],
                    node.attrib[GML_ID_KEY])

            if isinstance(xml_writer,
                    risk_output.LossMapNonScenarioXMLWriter):
                map_container_attrs = LOSS_MAP_NON_SCN_NODE_ATTRS
            else:
                map_container_attrs = LOSS_MAP_NODE_ATTRS

            # Verify the <lossMap> attributes
            for key in map_container_attrs:
                self.assertEqual(
                    str(loss_map_data[key]),
                    xml_writer.map_container.attrib[key])

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
                (self.xml_non_scn_writer, self.non_scenario_mdata)):

            xml_writer.write_metadata(loss_map_data)
            xml_writer.write_metadata(partial_meta)

            self.assertEqual(
                'undefined',
                xml_writer.root_node.attrib[GML_ID_KEY])

            self.assertEqual(
                'undefined',
                xml_writer.risk_result_node.attrib[GML_ID_KEY])

            self.assertEqual(
                'undefined',
                xml_writer.map_container.attrib['unit'])

    def test_serialize_with_no_meta(self):
        """
        This test serializes some sample data to an XML file. The sample data
        does not include metadata. This test will verify that defaults are used
        for all metadata.
        """
        for xml_writer, _ in ((self.xml_writer, LOSS_MAP_METADATA),
                (self.xml_non_scn_writer, self.non_scenario_mdata)):

            if isinstance(xml_writer,
                    risk_output.LossMapNonScenarioXMLWriter):
                map_container_attrs = LOSS_MAP_NON_SCN_NODE_ATTRS
                # everything but metadata
                test_data = self.non_scenario_data[1:]
            else:
                map_container_attrs = LOSS_MAP_NODE_ATTRS
                # everything but metadata
                test_data = SAMPLE_LOSS_MAP_DATA[1:]

            xml_writer.serialize(test_data)

            for key, node, in (
                ('nrmlID', xml_writer.root_node),
                ('riskResultID', xml_writer.risk_result_node),
                ('lossMapID', xml_writer.map_container)):
                self.assertEqual(
                    'undefined',
                    node.attrib[GML_ID_KEY])

            for key in map_container_attrs:
                self.assertEqual(
                    'undefined',
                    xml_writer.map_container.attrib[key])

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
                (self.xml_non_scn_writer, self.non_scenario_data)):
            xml_writer.serialize(loss_map_data)

            if isinstance(xml_writer, risk_output.LossMapNonScenarioXMLWriter):
                expected_loss_map = EXPECTED_TEST_NON_SCN_LOSS_MAP
                lossmap_xml_out_path = TEST_NON_SCN_LOSS_MAP_XML_OUTPUT_PATH
            else:
                expected_loss_map = EXPECTED_TEST_LOSS_MAP
                lossmap_xml_out_path = TEST_LOSS_MAP_XML_OUTPUT_PATH

            expected_elems = get_xml_elems_list(expected_loss_map)
            actual_elems = get_xml_elems_list(lossmap_xml_out_path)

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
