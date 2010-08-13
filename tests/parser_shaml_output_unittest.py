# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from opengem import region
from opengem.parser import shaml_output

FILES_KNOWN_TO_FAIL = ['ShamlOutputFile-fail-missing_required_attribute.xml',
                       'ShamlOutputFile-fail-attribute_type_mismatch.xml',
                       'ShamlOutputFile-fail-ambiguous_descriptor.xml',
                       'ShamlOutputFile-fail-missing_descriptor.xml',
                       'ShamlOutputFile-fail-IML_type_mismatch.xml',
                       'ShamlOutputFile-fail-missing_IML.xml',
                       'ShamlOutputFile-fail-illegal_gml_pos.xml',
                       'ShamlOutputFile-fail-curve_values_type_mismatch.xml',
                       'ShamlOutputFile-fail-missing_curve_vs30.xml']

TEST_FILE = 'ShamlOutputFile-test.xml'

data_dir = os.path.join(os.path.dirname(__file__), 'data')

class ShamlOutputFileTestCase(unittest.TestCase):

    def test_shamlfiles_known_to_fail(self):
        for testfile in FILES_KNOWN_TO_FAIL:
            shaml = shaml_output.ShamlOutputFile(os.path.join(data_dir, 
                                                              testfile))

            value_error_found = False
            try:
                # just loop through generator, in order to trigger exception
                for point, attributes in shaml:
                    pass
            except ValueError:
                # this is the exception we are expecting
                value_error_found = True
            except Exception, e:
                raise RuntimeError, "unexpected exception: %s" % e

            self.assertTrue(value_error_found, 
                "expected ValueError not raised in test file %s" % testfile)

    def test_filter_region_constraint_known_to_fail(self):

        # set region in which no site is found in input file
        region_constraint = region.RegionConstraint.from_simple((170.0, -80.0),
                                                                (175.0, -85.0))
        shaml = shaml_output.ShamlOutputFile(os.path.join(data_dir, 
                                                          TEST_FILE))

        ctr = None
        for ctr, shaml_item in enumerate(shaml.filter(region_constraint)):
            pass

        # ensure that generator didn't yield an item
        self.assertTrue(ctr is None, 
            "filter yielded item(s) although no items were expected")

    def test_filter_region_constraint(self):

        # look for sites within specified rectangle
        # constraint is met by one site in the example file 
        # (lon=16.35/lat=48.25)
        region_constraint = region.RegionConstraint.from_simple((16.0, 49.0),
                                                                (17.0, 48.0))
        shaml = shaml_output.ShamlOutputFile(os.path.join(data_dir, 
                                                          TEST_FILE))

        expected_result = [(region.Point(16.35, 48.25),
                           {'IMT': 'MMI',
                            'IDmodel': 'MMI_3_1',
                            'timeSpanDuration': 50.0,
                            'endBranchLabel': '3_1',
                            'IML': [10.0, 20.0, 30.0],
                            'maxProb': 0.9,
                            'minProb': 0.1,
                            'Values': [0.005, 0.007, 0.009],
                            'vs30': 760.0})]

        ctr = None
        for ctr, (shaml_point, shaml_attr) in enumerate(
            shaml.filter(region_constraint)):

            # check topological equality for points
            self.assertTrue(shaml_point.equals(expected_result[ctr][0]),
                "filter yielded unexpected point at position %s: %s, %s" % (
                ctr, shaml_point, expected_result[ctr][0]))

            self.assertTrue(shaml_attr == expected_result[ctr][1],
                "filter yielded unexpected attribute values at position " \
                "%s: %s, %s" % (ctr, shaml_attr, expected_result[ctr][1]))

        # ensure that generator yielded at least one item
        self.assertTrue(ctr is not None, 
            "filter yielded nothing although %s item(s) were expected" % \
            len(expected_result))

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertTrue(ctr == len(expected_result)-1, 
            "filter yielded wrong number of items (%s), expected were %s" % (
                ctr+1, len(expected_result)))
