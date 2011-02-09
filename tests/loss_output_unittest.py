# -*- coding: utf-8 -*-
"""
Tests for the serialization of loss/loss ratio curves to NRML format.
"""

import os
import unittest

from lxml import etree

from openquake import logs
from openquake import shapes
from openquake import test
from openquake import xml

from openquake.output import risk as risk_output
from openquake.risk import engines

log = logs.RISK_LOG

LOSS_XML_OUTPUT_FILE = 'loss-curves.xml'
LOSS_RATIO_XML_OUTPUT_FILE = 'loss-ratio-curves.xml'

LOSS_XML_FAIL_OUTPUT_FILE = 'loss-curves-fail.xml'

NRML_SCHEMA_PATH = os.path.join(test.SCHEMA_DIR, xml.NRML_SCHEMA_FILE)
NRML_SCHEMA_PATH_OLD = os.path.join(test.SCHEMA_DIR, xml.NRML_SCHEMA_FILE_OLD)

TEST_LOSS_CURVE = shapes.Curve(
    [(0.0, 0.44), (256.0, 0.23), (512.0, 0.2), (832.0, 0.16), (1216.0, 0.06)])

TEST_LOSS_RATIO_CURVE = shapes.Curve(
    [(0.0, 0.89), (0.2, 0.72), (0.4, 0.45), (0.6, 0.22), (0.8, 0.17), 
     (1.0, 0.03)])

class LossOutputTestCase(unittest.TestCase):
    """Confirm that XML output from risk engine is valid against schema,
    as well as correct given the inputs."""
    
    def setUp(self):
        self.loss_curve_path = test.test_output_file(LOSS_XML_OUTPUT_FILE)
        self.loss_ratio_curve_path = test.test_output_file(
            LOSS_RATIO_XML_OUTPUT_FILE)
        self.schema_path = NRML_SCHEMA_PATH

        # Build up some sample loss/loss ratio curves here
        first_site = shapes.Site(-117.0, 38.0)
        second_site = shapes.Site(-118.0, 39.0)

        first_asset_a = {"assetID" : "a1711", "endBranchLabel": "A"}
        first_asset_b = {"assetID" : "a1711", "endBranchLabel": "B"}
        second_asset_a = {"assetID" : "a1712", "endBranchLabel": "A"}
        second_asset_b = {"assetID" : "a1712", "endBranchLabel": "B"}

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

        # loss curve that fails with inconsistent sites for an asset
        self.loss_curves_fail = [
            (first_site, (TEST_LOSS_CURVE, first_asset_a)),
            (second_site, (TEST_LOSS_CURVE, first_asset_a))] 

    def test_loss_is_serialized_to_file_and_validates(self):

        xml_writer = risk_output.LossCurveXMLWriter(self.loss_curve_path)
        xml_writer.serialize(self.loss_curves)

        self.assertTrue(xml.validatesAgainstXMLSchema(self.loss_curve_path,
            NRML_SCHEMA_PATH),
            "NRML instance file %s does not validate against schema" % \
            self.loss_curve_path)

    def test_loss_ratio_is_serialized_to_file_and_validates(self):

        xml_writer = risk_output.LossRatioCurveXMLWriter(
            self.loss_ratio_curve_path)
        xml_writer.serialize(self.loss_ratio_curves)

        self.assertTrue(xml.validatesAgainstXMLSchema(
            self.loss_ratio_curve_path, NRML_SCHEMA_PATH),
            "NRML instance file %s does not validate against schema" % \
            self.loss_ratio_curve_path)

    def test_loss_serialization_with_inconsistent_site_fails(self):

        xml_writer = risk_output.LossCurveXMLWriter(
            test.test_output_file(LOSS_XML_FAIL_OUTPUT_FILE))
        self.assertRaises(ValueError, xml_writer.serialize, 
            self.loss_curves_fail)

    # http://www.devcomments.com/error-restricting-complexType-list-parsing-official-GML-schema-at108628.htm
    # skip unless we have the parser for new risk NRML
    @test.skipit
    def test_xml_is_valid(self):
        # save the xml, and run schema validation on it
        xml_doc = etree.parse(self.loss_curve_path)
        loaded_xml = xml_doc.getroot()

        # Test that the doc matches the schema
        xmlschema = etree.XMLSchema(etree.parse(self.schema_path))
        xmlschema.assertValid(xml_doc)
    
    # skip unless we have the parser for new risk NRML
    @test.skipit
    def test_loss_xml_is_correct(self):
        xml_doc = etree.parse(self.loss_curve_path)
        loaded_xml = xml_doc.getroot()

        xml_curve_pe = map(float, loaded_xml.find(".//"
                + xml.NRML_OLD + "LossCurvePE//"
                + xml.NRML_OLD + "Values").text.strip().split())
        xml_first_curve_value = loaded_xml.find(
                xml.NRML_OLD + "LossCurveList//" 
                + xml.NRML_OLD + "LossCurve//"
                + xml.NRML_OLD + "Values").text.strip().split()

        for idx, val in enumerate(TEST_CURVE.abscissae):
            self.assertAlmostEqual(val, float(xml_curve_pe[idx]), 6)
        for idx, val in enumerate(TEST_CURVE.ordinates):
            self.assertAlmostEqual(val, float(xml_first_curve_value[idx]), 6)

    # TODO(jmc): Test that the lat and lon are correct for each curve
    # Optionally, compare it to another XML file.

    # skip unless we have the parser for new risk NRML
    @test.skipit
    def test_ratio_xml_is_correct(self):
        xml_doc = etree.parse(self.loss_ratio_curve_path)
        loaded_xml = xml_doc.getroot()

        xml_curve_pe = map(float, loaded_xml.find(".//"
                + xml.NRML_OLD + "LossRatioCurvePE//"
                + xml.NRML_OLD + "Values").text.strip().split())
        xml_first_curve_value = loaded_xml.find(
                xml.NRML_OLD + "LossRatioCurveList//" 
                + xml.NRML_OLD + "LossRatioCurve//"
                + xml.NRML_OLD + "Values").text.strip().split()

        for idx, val in enumerate(TEST_CURVE.abscissae):
            self.assertAlmostEqual(val, float(xml_curve_pe[idx]), 6)
        for idx, val in enumerate(TEST_CURVE.ordinates):
            self.assertAlmostEqual(val, float(xml_first_curve_value[idx]), 6)

