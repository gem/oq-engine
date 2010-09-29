# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest
from opengem.parser import exposure
from opengem.parser import nrml
from opengem import shapes
from opengem import test

TEST_FILE = 'hazard-curves.xml'

data_dir = os.path.join(os.path.dirname(__file__), 'data')

class NrmlFileTestCase(unittest.TestCase):

    def test_filter_region_constraint_known_to_fail(self):

        # set region in which no site is found in input file
        region_constraint = shapes.RegionConstraint.from_simple((170.0, -80.0),
                                                                (175.0, -85.0))
        nrml_element = nrml.NrmlFile(os.path.join(test.DATA_DIR, TEST_FILE))

        ctr = None

        # this loop is not expected to be entered - generator should
        # not yield any item
        for ctr, nrml_item in enumerate(nrml_element.filter(region_constraint)):
            pass

        # ensure that generator didn't yield an item
        self.assertTrue(ctr is None, 
            "filter yielded item(s) although no items were expected")
            
    @test.skipit
    def test_filter_region_constraint_one_site(self):

        # look for sites within specified rectangle
        # constraint is met by one and only one site in the example file 
        # -122.5000, 37.5000
        region_constraint = shapes.RegionConstraint.from_simple(
            (-122.4500, 37.5000), (-122.5500, 37.5000))
           
        nrml_element = nrml.NrmlFile(os.path.join(data_dir, TEST_FILE))
        
        expected_result = [
            (shapes.Point(-122.5000, 37.5000),
            {'Values': [9.8728e-01, 9.8266e-01, 9.4957e-01, 9.0326e-01, 
                8.1956e-01, 6.9192e-01, 5.2866e-01, 3.6143e-01, 2.4231e-01, 
                2.2452e-01, 1.2831e-01, 7.0352e-02, 3.6060e-02, 1.6579e-02, 
                6.4213e-03, 2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]
            })]

        ctr = None
        for ctr, (nrml_point, nrml_attr) in enumerate(
            nrml_element.filter(region_constraint)):

            # check topological equality for points
            self.assertTrue(nrml_point.equals(expected_result[ctr][0]),
                "filter yielded unexpected point at position %s: %s, %s" % (
                ctr, nrml_point, expected_result[ctr][0]))

            self.assertTrue(nrml_attr == expected_result[ctr][1],
                "filter yielded unexpected attribute values at position " \
                "%s: %s, %s" % (ctr, nrml_attr, expected_result[ctr][1]))

        # ensure that generator yielded at least one item
        self.assertTrue(ctr is not None, 
            "filter yielded nothing although %s item(s) were expected" % \
            len(expected_result))

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertTrue(ctr == len(expected_result)-1, 
            "filter yielded wrong number of items (%s), expected were %s" % (
                ctr+1, len(expected_result)))
    @test.skipit
    def test_filter_region_constraint_all_sites(self):

        # specified rectangle contains all sites in example file 
        region_constraint = shapes.RegionConstraint.from_simple((-121, 36),
                                                                (-123, 38))
        nrml_element = nrml.NrmlFile(os.path.join(data_dir, TEST_FILE))

        expected_result_ctr = 6
        ctr = None

        # just loop through iterator in order to count items
        for ctr, (nrml_point, nrml_attr) in enumerate(
            nrml_element.filter(region_constraint)):
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
