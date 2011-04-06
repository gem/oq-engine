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

from openquake import logs
from openquake import shapes
from openquake import xml
from tests.utils import helpers

from openquake.output import risk as risk_output

LOG = logs.RISK_LOG

SINGLE_LOSS_MAP_XML_OUTPUT_FILE = 'loss-map-single-event.xml'

NRML_SCHEMA_PATH = os.path.join(helpers.SCHEMA_DIR,
                                 xml.NRML_SCHEMA_FILE)
NRML_SCHEMA_PATH_OLD = os.path.join(helpers.SCHEMA_DIR,
                                    xml.NRML_SCHEMA_FILE_OLD)


class LossMapOutputTestCase(unittest.TestCase):
    """Confirm that XML output from risk engine is valid against schema,
    as well as correct given the inputs."""

    def setUp(self):
        self.single_loss_map_path = helpers.get_output_path(
            SINGLE_LOSS_MAP_XML_OUTPUT_FILE)

        # Build up some sample test data for loss maps
        self.first_site = shapes.Site(-117.0, 38.0)
        self.second_site = shapes.Site(-118.0, 39.0)

        self.first_asset_a = {"assetID": "a1711", "endBranchLabel": "A",
                                'lossCategory': 'economic_loss',
                                'unit': 'EUR'}
        self.second_asset_a = {"assetID": "a1712", "endBranchLabel": "A"}
        self.second_asset_b = {"assetID": "a1713", "endBranchLabel": "B"}
        self.loss_map_data = [
            (self.first_site, ({'mean_loss': 0, 'stddev': 100},
                        self.first_asset_a)),
            (self.first_site, ({'mean_loss': 5, 'stddev': 2000.0},
                        self.second_asset_a)),
            (self.second_site, ({'mean_loss': 120000.0, 'stddev': 2000.0},
                        self.second_asset_b))]

    def test_loss_map_output_writes_and_validates(self):
        xml_writer = risk_output.LossMapXMLWriter(self.single_loss_map_path)
        xml_writer.serialize(self.loss_map_data)
        self.assertTrue(
            xml.validates_against_xml_schema(self.single_loss_map_path,
            NRML_SCHEMA_PATH),
            "NRML instance file %s does not validate against schema" % \
            self.single_loss_map_path)

    def test_loss_map_xml_is_correct(self):
        """Assert that content of serialized loss map data
        is correct."""

        # serialize curves
        xml_writer = risk_output.LossMapXMLWriter(
            self.single_loss_map_path)
        xml_writer.serialize(self.loss_map_data)

        # parse curves DOM-style
        xml_doc = etree.parse(self.single_loss_map_path)

        loaded_xml = xml_doc.getroot()

        lmnodes = loaded_xml.findall(".//%s" % xml.RISK_LMNODE_TAG)

        self.assertEqual(len(lmnodes), 3)
        for lmnode in lmnodes:
            self.assertTrue(isinstance(lmnode, etree._Element))
            site_tag = lmnode.findall(".//%s" % xml.RISK_SITE_TAG)
            self.assertEqual(len(site_tag), 1)
            for site in site_tag:
                self.assertTrue(
                    len(site.findtext('.//%s' % xml.GML_POS_TAG).split()) >= 2)
                self.assertTrue(
                    len(site.findtext('.//%s' % xml.GML_POS_TAG).split()) <= 3)

            loss_container_tag = lmnode.findall('.//%s' %
                                        xml.RISK_LOSS_MAP_LOSS_CONTAINER_TAG)

            self.assertEqual(len(loss_container_tag), 1)
            for loss in loss_container_tag:
                self.assertTrue(isinstance(
                    loss.findtext('.//%s' %
                        xml.RISK_LOSS_MAP_STANDARD_DEVIATION_TAG),
                        str))
                self.assertTrue(isinstance(
                    loss.findtext('.//%s' %
                        xml.RISK_LOSS_MAP_MEAN_LOSS_TAG),
                        str))
