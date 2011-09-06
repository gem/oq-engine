# -*- coding: utf-8 -*-


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
Tests for the serialization of loss/loss ratio curves to NRML format.
"""

import os
import unittest

from lxml import etree

from openquake import logs
from openquake import nrml
from openquake import shapes
from openquake import xml
from tests.utils import helpers

from openquake.output import risk as risk_output

log = logs.RISK_LOG

LOSS_XML_OUTPUT_FILE = 'loss-curves.xml'
LOSS_RATIO_XML_OUTPUT_FILE = 'loss-ratio-curves.xml'

SINGLE_LOSS_XML_OUTPUT_FILE = 'loss-curves-single.xml'
SINGLE_LOSS_RATIO_XML_OUTPUT_FILE = 'loss-ratio-curves-single.xml'

LOSS_XML_FAIL_OUTPUT_FILE = 'loss-curves-fail.xml'

NRML_SCHEMA_PATH = nrml.nrml_schema_file()

TEST_LOSS_CURVE = shapes.Curve(
    [(0.0, 0.44), (256.0, 0.23), (512.0, 0.2), (832.0, 0.16), (1216.0, 0.06)])

TEST_LOSS_RATIO_CURVE = shapes.Curve(
    [(0.0, 0.89), (0.2, 0.72), (0.4, 0.45), (0.6, 0.22), (0.8, 0.17),
     (1.0, 0.03)])


class LossOutputTestCase(unittest.TestCase):
    """Confirm that XML output from risk engine is valid against schema,
    as well as correct given the inputs."""

    def setUp(self):
        self.loss_curve_path = helpers.get_output_path(LOSS_XML_OUTPUT_FILE)
        self.loss_ratio_curve_path = helpers.get_output_path(
            LOSS_RATIO_XML_OUTPUT_FILE)

        self.single_loss_curve_path = helpers.get_output_path(
            SINGLE_LOSS_XML_OUTPUT_FILE)
        self.single_loss_ratio_curve_path = helpers.get_output_path(
            SINGLE_LOSS_RATIO_XML_OUTPUT_FILE)

        self.schema_path = NRML_SCHEMA_PATH

        # Build up some sample loss/loss ratio curves here
        first_site = shapes.Site(-117.0, 38.0)
        second_site = shapes.Site(-118.0, 39.0)

        first_asset_a = {"assetID": "a1711", "endBranchLabel": "A"}
        first_asset_b = {"assetID": "a1711", "endBranchLabel": "B"}
        second_asset_a = {"assetID": "a1712", "endBranchLabel": "A"}
        second_asset_b = {"assetID": "a1712", "endBranchLabel": "B"}

        self.loss_curves = [
            (first_site, (TEST_LOSS_CURVE, first_asset_a)),
            (first_site, (TEST_LOSS_CURVE, first_asset_b)),
            (second_site, (TEST_LOSS_CURVE, second_asset_a)),
            (second_site, (TEST_LOSS_CURVE, second_asset_b))]

        self.loss_ratio_curves = [
            (first_site, (TEST_LOSS_RATIO_CURVE, first_asset_a)),
            (first_site, (TEST_LOSS_RATIO_CURVE, first_asset_b)),
            (second_site, (TEST_LOSS_RATIO_CURVE, second_asset_a)),
            (second_site, (TEST_LOSS_RATIO_CURVE, second_asset_b))]

        self.single_loss_curve = [
            (first_site, (TEST_LOSS_CURVE, first_asset_a))]

        self.single_loss_ratio_curve = [
            (first_site, (TEST_LOSS_RATIO_CURVE, first_asset_a))]

        # loss curve that fails with inconsistent sites for an asset
        self.loss_curves_fail = [
            (first_site, (TEST_LOSS_CURVE, first_asset_a)),
            (second_site, (TEST_LOSS_CURVE, first_asset_a))]

    def test_loss_is_serialized_to_file_and_validates(self):
        """Serialize loss curve to NRML and validate against schema."""
        xml_writer = risk_output.LossCurveXMLWriter(self.loss_curve_path)
        xml_writer.serialize(self.loss_curves)

        self.assertTrue(xml.validates_against_xml_schema(self.loss_curve_path,
            NRML_SCHEMA_PATH),
            "NRML instance file %s does not validate against schema" % \
            self.loss_curve_path)

    def test_loss_ratio_is_serialized_to_file_and_validates(self):
        """Serialize loss ratio curve to NRML and validate against schema."""
        xml_writer = risk_output.LossRatioCurveXMLWriter(
            self.loss_ratio_curve_path)
        xml_writer.serialize(self.loss_ratio_curves)

        self.assertTrue(xml.validates_against_xml_schema(
            self.loss_ratio_curve_path, NRML_SCHEMA_PATH),
            "NRML instance file %s does not validate against schema" % \
            self.loss_ratio_curve_path)

    def test_loss_serialization_with_inconsistent_site_fails(self):
        """Assert that serialization of illegal loss curve data
        raises error."""
        xml_writer = risk_output.LossCurveXMLWriter(
            helpers.get_output_path(LOSS_XML_FAIL_OUTPUT_FILE))
        self.assertRaises(ValueError, xml_writer.serialize,
            self.loss_curves_fail)

    def test_loss_xml_is_correct(self):
        """Assert that content of serialized loss curve data
        is correct."""

        # serialize curves
        xml_writer = risk_output.LossCurveXMLWriter(
            self.single_loss_curve_path)
        xml_writer.serialize(self.single_loss_curve)

        # parse curves DOM-style
        xml_doc = etree.parse(self.single_loss_curve_path)
        loaded_xml = xml_doc.getroot()

        poe_el_txt = loaded_xml.findtext(".//%s" % xml.RISK_POE_TAG)
        poe_values = [float(x) for x in poe_el_txt.strip().split()]

        loss_el_txt = loaded_xml.findtext(
            ".//%s" % xml.RISK_LOSS_ABSCISSA_TAG)
        loss_values = [float(x) \
            for x in loss_el_txt.strip().split()]

        self.assertEqual(len(loss_values), len(TEST_LOSS_CURVE.abscissae),
            "curve length mismatch")

        for idx, val in enumerate(TEST_LOSS_CURVE.abscissae):
            self.assertAlmostEqual(val, float(loss_values[idx]), 6)
        for idx, val in enumerate(TEST_LOSS_CURVE.ordinates):
            self.assertAlmostEqual(val, float(poe_values[idx]), 6)

    # TODO(jmc): Test that the lat and lon are correct for each curve
    # Optionally, compare it to another XML file.
    def test_loss_ratio_xml_is_correct(self):
        """Assert that content of serialized loss ratio curve data
        is correct."""

        # serialize curves
        xml_writer = risk_output.LossRatioCurveXMLWriter(
            self.single_loss_ratio_curve_path)
        xml_writer.serialize(self.single_loss_ratio_curve)

        # parse curves DOM-style
        xml_doc = etree.parse(self.single_loss_ratio_curve_path)
        loaded_xml = xml_doc.getroot()

        poe_el_txt = loaded_xml.findtext(".//%s" % xml.RISK_POE_TAG)
        poe_values = [float(x) for x in poe_el_txt.strip().split()]

        loss_ratio_el_txt = loaded_xml.findtext(
            ".//%s" % xml.RISK_LOSS_RATIO_ABSCISSA_TAG)
        loss_ratio_values = [
            float(x) for x in loss_ratio_el_txt.strip().split()]

        self.assertEqual(len(loss_ratio_values),
            len(TEST_LOSS_RATIO_CURVE.abscissae),
            "curve length mismatch")

        for idx, val in enumerate(TEST_LOSS_RATIO_CURVE.abscissae):
            self.assertAlmostEqual(val, float(loss_ratio_values[idx]), 6)
        for idx, val in enumerate(TEST_LOSS_RATIO_CURVE.ordinates):
            self.assertAlmostEqual(val, float(poe_values[idx]), 6)
