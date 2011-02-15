# -*- coding: utf-8 -*-
"""
Tests for the NRML parser of loss/loss ratio curves.
"""

import os
import unittest

from openquake import logs
from openquake import shapes
from openquake import xml

from openquake.parser import risk as risk_parser

from utils import test

log = logs.RISK_LOG

EXAMPLE_DIR = os.path.join(test.SCHEMA_DIR, 'examples')
LOSS_CURVE_TEST_FILE = os.path.join(EXAMPLE_DIR, 'loss-curves.xml')
LOSS_RATIO_CURVE_TEST_FILE = os.path.join(EXAMPLE_DIR, 'loss-ratio-curves.xml')


class RiskXMLReaderTestCase(unittest.TestCase):

    def setUp(self):
        self.loss_attr_name = xml.strip_namespace_from_tag(
            xml.RISK_LOSS_ABSCISSA_TAG, xml.NRML)
        self.loss_ratio_attr_name = xml.strip_namespace_from_tag(
            xml.RISK_LOSS_RATIO_ABSCISSA_TAG, xml.NRML)
        self.poe_attr_name = xml.strip_namespace_from_tag(xml.RISK_POE_TAG, 
            xml.NRML)

        self.LOSS_CURVE_REFERENCE_DATA = [
                            (shapes.Site(-117.0, 30.0), 
                             {'nrml_id': "n1",
                              'result_id': "rr1",
                              'list_id': "lossCurveList_1",
                              'assetID': 'asset_1',
                              'property': 'Loss',
                              xml.RISK_END_BRANCH_ATTR_NAME: 'vf_1',
                              self.loss_attr_name: [0.0, 100.0, 200.0],
                              self.poe_attr_name: [0.4, 0.2, 0.1]}),
                             (shapes.Site(-117.0, 30.0), 
                             {'nrml_id': "n1",
                              'result_id': "rr1",
                              'list_id': "lossCurveList_1",
                              'assetID': 'asset_1',
                              'property': 'Loss',
                              xml.RISK_END_BRANCH_ATTR_NAME: 'vf_2',
                              self.loss_attr_name: [0.0, 200.0, 400.0],
                              self.poe_attr_name: [0.2, 0.1, 0.05]}),
                             (shapes.Site(-117.0, 35.0), 
                             {'nrml_id': "n1",
                              'result_id': "rr1",
                              'list_id': "lossCurveList_1",
                              'assetID': 'asset_2',
                              'property': 'Loss',
                              xml.RISK_END_BRANCH_ATTR_NAME: 'vf_3',
                              self.loss_attr_name: [0.0, 1000.0, 2000.0],
                              self.poe_attr_name: [0.6, 0.3, 0.1]}),
                             (shapes.Site(-117.0, 35.0), 
                             {'nrml_id': "n1",
                              'result_id': "rr1",
                              'list_id': "lossCurveList_1",
                              'assetID': 'asset_2',
                              'property': 'Loss',
                              self.loss_attr_name: [0.0, 5000.0, 10000.0],
                              self.poe_attr_name: [0.1, 0.01, 0.001]})]

        self.LOSS_RATIO_CURVE_REFERENCE_DATA = [
                            (shapes.Site(-117.0, 30.0), 
                             {'nrml_id': "n1",
                              'result_id': "rr1",
                              'list_id': "lossRatioCurveList_1",
                              'assetID': 'asset_1',
                              'property': 'Loss Ratio',
                              xml.RISK_END_BRANCH_ATTR_NAME: 'vf_1',
                              self.loss_ratio_attr_name: [0.0, 0.2, 0.4],
                              self.poe_attr_name: [0.4, 0.2, 0.1]}),
                             (shapes.Site(-117.0, 30.0), 
                             {'nrml_id': "n1",
                              'result_id': "rr1",
                              'list_id': "lossRatioCurveList_1",
                              'assetID': 'asset_1',
                              'property': 'Loss Ratio',
                              xml.RISK_END_BRANCH_ATTR_NAME: 'vf_2',
                              self.loss_ratio_attr_name: [0.0, 0.5, 0.8],
                              self.poe_attr_name: [0.2, 0.1, 0.05]}),
                             (shapes.Site(-117.0, 35.0), 
                             {'nrml_id': "n1",
                              'result_id': "rr1",
                              'list_id': "lossRatioCurveList_1",
                              'assetID': 'asset_2',
                              'property': 'Loss Ratio',
                              xml.RISK_END_BRANCH_ATTR_NAME: 'vf_3',
                              self.loss_ratio_attr_name: [0.0, 0.0001, 0.0002],
                              self.poe_attr_name: [0.6, 0.3, 0.1]}),
                             (shapes.Site(-117.0, 35.0), 
                             {'nrml_id': "n1",
                              'result_id': "rr1",
                              'list_id': "lossRatioCurveList_1",
                              'assetID': 'asset_2',
                              'property': 'Loss Ratio',
                              self.loss_ratio_attr_name: [0.0, 0.0004, 0.0008],
                              self.poe_attr_name: [0.5, 0.2, 0.05]})]

    def test_loss_curve_has_correct_content(self):
        loss_element = risk_parser.LossCurveXMLReader(LOSS_CURVE_TEST_FILE)
        expected_result = self.LOSS_CURVE_REFERENCE_DATA

        counter = None
        for counter, (nrml_site, nrml_attr) in enumerate(loss_element):

            # check topological equality for points
            self.assertTrue(nrml_site.point.equals(
                expected_result[counter][0].point),
                "filter yielded unexpected site at position %s: %s, %s" % (
                counter, nrml_site.point, expected_result[counter][0].point))

            self.assertEqual(nrml_attr, expected_result[counter][1],
                "filter yielded unexpected attribute values at position " \
                "%s: %s, %s" % (counter, nrml_attr, 
                                expected_result[counter][1]))

        # ensure that generator yielded at least one item
        self.assertTrue(counter is not None, 
            "filter yielded nothing although %s item(s) were expected" % \
            len(expected_result))

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertEqual(counter, len(expected_result)-1, 
            "filter yielded wrong number of items (%s), expected were %s" % (
                counter+1, len(expected_result)))


    def test_loss_ratio_curve_has_correct_content(self):
        loss_ratio_element = risk_parser.LossRatioCurveXMLReader(
            LOSS_RATIO_CURVE_TEST_FILE)
        expected_result = self.LOSS_RATIO_CURVE_REFERENCE_DATA

        counter = None
        for counter, (nrml_site, nrml_attr) in enumerate(loss_ratio_element):

            # check topological equality for points
            self.assertTrue(nrml_site.point.equals(
                expected_result[counter][0].point),
                "filter yielded unexpected site at position %s: %s, %s" % (
                counter, nrml_site.point, expected_result[counter][0].point))

            self.assertEqual(nrml_attr, expected_result[counter][1],
                "filter yielded unexpected attribute values at position " \
                "%s: %s, %s" % (counter, nrml_attr, 
                                expected_result[counter][1]))

        # ensure that generator yielded at least one item
        self.assertTrue(counter is not None, 
            "filter yielded nothing although %s item(s) were expected" % \
            len(expected_result))

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertEqual(counter, len(expected_result)-1, 
            "filter yielded wrong number of items (%s), expected were %s" % (
                counter+1, len(expected_result)))
