# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from openquake.parser import exposure
from openquake import shapes
from utils import test

TEST_FILE = 'exposure-portfolio.xml'


class ExposurePortfolioFileTestCase(unittest.TestCase):

    def test_filter_region_constraint_known_to_fail(self):

        # set region in which no site is found in input file
        region_constraint = shapes.RegionConstraint.from_simple((170.0, -80.0),
                                                                (175.0, -85.0))
        ep = exposure.ExposurePortfolioFile(
            os.path.join(test.SCHEMA_EXAMPLES_DIR, TEST_FILE))
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
        ep = exposure.ExposurePortfolioFile(
            os.path.join(test.SCHEMA_EXAMPLES_DIR, TEST_FILE))

        expected_result = [
            (shapes.Point(9.15333, 45.12200),
            {'listID': 'PAV01',
             'listDescription': 'Collection of existing building in ' \
                                'downtown Pavia',
             'assetID': 'asset_02',
             'assetDescription': 'Moment-resisting non-ductile concrete ' \
                                 'frame low rise',
             'vulnerabilityFunctionReference': 'RC/DMRF-D/LR',
             'structureCategory': 'RC-LR-PC',
             'assetValue': 250000.0,
             'assetValueUnit': 'EUR',
            })]

        ctr = None
        for ctr, (exposure_point, exposure_attr) in enumerate(
            ep.filter(region_constraint)):

            # check topological equality for points
            self.assertTrue(exposure_point.equals(expected_result[ctr][0]),
                "filter yielded unexpected point at position %s: %s, %s" % (
                ctr, exposure_point, expected_result[ctr][0]))

            self.assertTrue(exposure_attr == expected_result[ctr][1],
                "filter yielded unexpected attribute values at position " \
                "%s: %s, %s" % (ctr, exposure_attr, expected_result[ctr][1]))

        # ensure that generator yielded at least one item
        self.assertTrue(ctr is not None, 
            "filter yielded nothing although %s item(s) were expected" % \
            len(expected_result))

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertTrue(ctr == len(expected_result)-1, 
            "filter yielded wrong number of items (%s), expected were %s" % (
                ctr+1, len(expected_result)))

    def test_filter_region_constraint_all_sites(self):

        # specified rectangle contains all sites in example file 
        region_constraint = \
                shapes.RegionConstraint.from_simple((9.14776, 45.18000),
                                                    (9.15334, 45.12199))
        ep = exposure.ExposurePortfolioFile(
            os.path.join(test.SCHEMA_EXAMPLES_DIR, TEST_FILE))

        expected_result_ctr = 3
        ctr = None

        # just loop through iterator in order to count items
        for ctr, (exposure_point, exposure_attr) in enumerate(
            ep.filter(region_constraint)):
            pass

        # ensure that generator yielded at least one item
        self.assertTrue(ctr is not None, 
            "filter yielded nothing although %s item(s) were expected" % \
            expected_result_ctr)

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertTrue(ctr == expected_result_ctr-1, 
            "filter yielded wrong number of items (%s), expected were %s" % (
                ctr+1, expected_result_ctr))
