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


import os
import unittest

from openquake.parser import exposure
from openquake import shapes
from openquake import xml
from tests.utils import helpers


TEST_FILE = 'exposure-portfolio.xml'
INVALID_TEST_FILE = helpers.get_data_path("invalid/small_exposure.xml")
MISMATCHED_TEST_FILE = "examples/source-model.xml"


class ExposureModelFileTestCase(unittest.TestCase):

    def test_schema_validation(self):
        def _parse_exposure(path):
            ep = exposure.ExposureModelFile(path)

            # force parsing the whole file
            for e in ep:
                pass

        self.assertRaises(xml.XMLValidationError,
                          _parse_exposure, INVALID_TEST_FILE)

        self.assertRaises(xml.XMLMismatchError, _parse_exposure,
                          os.path.join(helpers.SCHEMA_DIR,
                                       MISMATCHED_TEST_FILE))

    def test_filter_region_constraint_known_to_fail(self):

        # set region in which no site is found in input file
        region_constraint = shapes.RegionConstraint.from_simple((170.0, -80.0),
                                                                (175.0, -85.0))
        ep = exposure.ExposureModelFile(
            os.path.join(helpers.SCHEMA_EXAMPLES_DIR, TEST_FILE))
        ctr = None

        # this loop is not expected to be entered - generator should
        # not yield any item
        for ctr, exposure_item in enumerate(ep.filter(
            region_constraint)):
            pass

        # ensure that generator didn't yield an item
        self.assertTrue(ctr is None,
            "filter yielded item(s) although no items were expected")

    def test_filter_region_constraint_one_site(self):

        # look for sites within specified rectangle
        # constraint is met by one and only one site in the example file
        # 9.15333 45.12200
        region_constraint = shapes.RegionConstraint.from_simple(
            (9.15332, 45.12201), (9.15334, 45.12199))
        ep = exposure.ExposureModelFile(
            os.path.join(helpers.SCHEMA_EXAMPLES_DIR, TEST_FILE))

        expected_result = [
            (shapes.Site(9.15333, 45.12200),
             [exposure.OCCUPANCY(12, "day"), exposure.OCCUPANCY(50, "night")],
             {"area": 119.0,
              "areaType": "per_asset",
              "areaUnit": "GBP",
              "assetCategory": "buildings",
              "assetID": "asset_02",
              "coco": 21.95,
              "cocoType": "per_area",
              "cocoUnit": "CHF",
              "deductible": 66.0,
              "limit": 1999.0,
              "listDescription": "Collection of existing building in "
                                 "downtown Pavia",
              "listID": "PAV01",
              "number": 6.0,
              "reco": 205432.0,
              "recoType": "aggregated",
              "recoUnit": "EUR",
              "stco": 250000.0,
              "stcoType": "aggregated",
              "stcoUnit": "USD",
              "taxonomy": "RC/DMRF-D/HR",
              "taxonomySource": "Pavia taxonomy",
              "unitType": "economic_value"}
            )]

        ctr = None
        for ctr, (exposure_point, occupancy_data, exposure_data) in enumerate(
            ep.filter(region_constraint)):

            # check topological equality for points
            self.assertEqual(expected_result[ctr][0], exposure_point)
            self.assertEqual(expected_result[ctr][1], occupancy_data)
            self.assertEqual(expected_result[ctr][2], exposure_data)

        # ensure that generator yielded at least one item
        self.assertTrue(ctr is not None,
            "filter yielded nothing although %s item(s) were expected" % \
            len(expected_result))

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertTrue(ctr == len(expected_result) - 1,
            "filter yielded wrong number of items (%s), expected were %s" % (
                ctr + 1, len(expected_result)))

    def test_filter_region_constraint_all_sites(self):

        # specified rectangle contains all sites in example file
        region_constraint = shapes.RegionConstraint.from_simple(
            (9.14776, 45.18000), (9.15334, 45.12199))
        ep = exposure.ExposureModelFile(
            os.path.join(helpers.SCHEMA_EXAMPLES_DIR, TEST_FILE))

        expected_result_ctr = 3
        ctr = None

        # just loop through iterator in order to count items
        for ctr, _ in enumerate(ep.filter(region_constraint)):
            pass

        # ensure that generator yielded at least one item
        self.assertTrue(ctr is not None,
            "filter yielded nothing although %s item(s) were expected" % \
            expected_result_ctr)

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertTrue(ctr == expected_result_ctr - 1,
            "filter yielded wrong number of items (%s), expected were %s" % (
                ctr + 1, expected_result_ctr))
