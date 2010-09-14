# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest
from opengem import shapes
from opengem.parser import exposure

TEST_FILE = 'LossRatioCurves-test.xml'

data_dir = os.path.join(os.path.dirname(__file__), 'data')

class LossRatioCurveFileTestCase(unittest.TestCase):

    def test_filter_region_constraint_known_to_fail(self):

        # set region in which no site is found in input file
        region_constraint = shapes.RegionConstraint.from_simple((40.0, 10.0),
                                                                (42.0, 14.0))
        ep = loss_ratio_curve.LossRatioCurveFile(
            os.path.join(data_dir, TEST_FILE))

        ctr = None

        # this loop is not expected to be entered - generator should
        # not yield any item
        for ctr, loss_ratio_item in enumerate(ep.filter(
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
        ep = loss_ratio_curve.LossRatioCurveFile(
            os.path.join(data_dir, TEST_FILE))


        expected_result = [
            (shapes.Point(41.0, 12.0),
            {'CurvePointPE': [0.0, 1280.0, 2560.0, 3840.0, 5120.0, 6400.0, 
            8320.0, 10240.0, 12160.0, 14080.0, 16000.0, 21120.0, 26240.0, 
            31360.0, 36480.0, 41600.0, 49280.0, 56960.0, 64640.0, 72320.0, 
            80000.0, 90240.0, 100480.0, 110720.0, 120960.0, 131200.0, 
            140160.0, 149120.0, 158080.0, 167040.0, 176000.0, 189440.0, 
            202880.0, 216320.0, 229760.0, 243200.0],
            'CurvePointLoss': [0.241053927419, 0.234871039103, 0.22617525424,
            0.214873509183, 0.201308289741, 0.186256995833, 0.163216429503, 
            0.142564936604, 0.126054023695, 0.113487409083, 0.103636128779, 
            0.0834004937366, 0.0687486347241, 0.0592702960988, 0.0527381730611, 
            0.0471281445172, 0.0391343927742, 0.0320542714275, 0.0264304362982, 
            0.0222041239703, 0.0189554906906, 0.0154638452103, 0.0125342054434, 
            0.0100912720748, 0.00812879461076, 0.00658063765551, 
            0.00548383302716, 0.00456167335096, 0.00377234419731, 
            0.00309343920728, 0.00251405889789, 0.00181587018638, 
            0.00129697405159, 0.000921838630893, 0.000653898225625, 
            0.000462828285108]} )]

        ctr = None
        for ctr, (loss_point, loss_attr) in enumerate(
            ep.filter(region_constraint)):

            # check topological equality for points
            self.assertTrue(loss_point.equals(expected_result[ctr][0]),
                "filter yielded unexpected point at position %s: %s, %s" % (
                ctr, loss_point, expected_result[ctr][0]))

            self.assertTrue(loss_attr == expected_result[ctr][1],
                "filter yielded unexpected attribute values at position " \
                "%s: %s, %s" % (ctr, loss_attr, expected_result[ctr][1]))

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
        region_constraint = shapes.RegionConstraint.from_simple((-20.0, 80.0),
                                                                (40.0, 0.0))
        ep = loss_ratio_curve.LossRatioCurveFile(
            os.path.join(data_dir, TEST_FILE))

        expected_result_ctr = 6
        ctr = None

        # just loop through iterator in order to count items
        for ctr, (loss_point, loss_attr) in enumerate(
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
