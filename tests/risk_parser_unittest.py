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
Tests for the NRML parser of loss/loss ratio curves.
"""

import os
import unittest

from openquake import shapes
from openquake import xml

from openquake.parser import risk as risk_parser

from tests.utils import helpers


EXAMPLE_DIR = os.path.join(helpers.SCHEMA_DIR, 'examples')
LOSS_CURVE_TEST_FILE = os.path.join(EXAMPLE_DIR, 'loss-curves.xml')
LOSS_CURVE_BAD_TEST_FILE = os.path.join(helpers.DATA_DIR,
    'simplecase-loss-block-BLOCK:2.bad.xml')
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

    def test_loss_curve_is_parsed_correcly(self):
        """
            This test is a bit "unusual", if _parse() will raise an exception
            the test will fail, this is due to the previous not correct
            behaviour described in https://github.com/gem/openquake/issues/130

            the "bug" is listed on https://bugs.launchpad.net/lxml/+bug/589805
        """
        loss_curve_reader = risk_parser.LossCurveXMLReader(
            LOSS_CURVE_BAD_TEST_FILE)

        list(loss_curve_reader._parse())

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
        self.assertEqual(counter, len(expected_result) - 1,
            "filter yielded wrong number of items (%s), expected were %s" % (
                counter + 1, len(expected_result)))

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
        self.assertEqual(counter, len(expected_result) - 1,
            "filter yielded wrong number of items (%s), expected were %s" % (
                counter + 1, len(expected_result)))
