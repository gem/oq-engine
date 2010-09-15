# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from opengem import shapes
from opengem import test
from opengem import producer
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

FILE_FLAVOUR_NOT_IMPLEMENTED = 'ShamlOutputFile-HazardMap-PASS.xml'

TEST_FILE = 'ShamlOutputFile-PASS.xml'

class ShamlOutputFileTestCase(unittest.TestCase):

    def test_shamlfiles_known_to_fail(self):
        for testfile in FILES_KNOWN_TO_FAIL:
            shaml = shaml_output.ShamlOutputFile(os.path.join(test.DATA_DIR, 
                                                              testfile))

            self.assertRaises(ValueError, map, None, shaml)

    def test_shamlfiles_hazardmap_not_implemented(self):
        shaml = shaml_output.ShamlOutputFile(os.path.join(test.DATA_DIR, 
            FILE_FLAVOUR_NOT_IMPLEMENTED))

        self.assertRaises(NotImplementedError, map, None, shaml)

    def test_filter_region_constraint_known_to_fail(self):

        # set region in which no site is found in input file
        region_constraint = shapes.RegionConstraint.from_simple((170.0, -80.0),
                                                                (175.0, -85.0))
        shaml = shaml_output.ShamlOutputFile(os.path.join(test.DATA_DIR, 
                                                          TEST_FILE))

        counter = None

        # this loop is not expected to be entered - generator should
        # not yield any item
        for counter, shaml_item in enumerate(shaml.filter(region_constraint)):
            pass

        # ensure that generator didn't yield an item
        self.assertTrue(counter is None, 
            "filter yielded item(s) although no items were expected")

    def test_filter_region_constraint_one_site(self):

        # look for sites within specified rectangle
        # constraint is met by one and only one site in the example file 
        # (lon=16.35/lat=48.25)
        region_constraint = shapes.RegionConstraint.from_simple((16.0, 49.0),
                                                                (17.0, 48.0))
        shaml = shaml_output.ShamlOutputFile(os.path.join(test.DATA_DIR, 
                                                          TEST_FILE))

        expected_result = [(shapes.Point(16.35, 48.25),
                           {'IMT': 'MMI',
                            'IDmodel': 'MMI_3_1',
                            'timeSpanDuration': 50.0,
                            'endBranchLabel': '3_1',
                            'IML': [10.0, 20.0, 30.0],
                            'maxProb': 0.9,
                            'minProb': 0.1,
                            'Values': [0.005, 0.007, 0.009],
                            'vs30': 760.0})]

        counter = None
        for counter, (shaml_point, shaml_attr) in enumerate(
            shaml.filter(region_constraint)):

            # check topological equality for points
            self.assertTrue(shaml_point.equals(expected_result[counter][0]),
                "filter yielded unexpected point at position %s: %s, %s" % (
                counter, shaml_point, expected_result[counter][0]))

            self.assertEqual(shaml_attr, expected_result[counter][1],
                "filter yielded unexpected attribute values at position " \
                "%s: %s, %s" % (counter, shaml_attr, 
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

    def test_filter_region_constraint_all_sites(self):

        # specified rectangle contains all sites in example file 
        region_constraint = shapes.RegionConstraint.from_simple((-20.0, 80.0),
                                                                (40.0, 0.0))
        shaml = shaml_output.ShamlOutputFile(os.path.join(test.DATA_DIR, 
                                                          TEST_FILE))

        expected_result_counter = 10
        counter = None

        # just loop through iterator in order to count items
        for counter, (shaml_point, shaml_attr) in enumerate(
            shaml.filter(region_constraint)):
            pass

        # ensure that generator yielded at least one item
        self.assertTrue(counter is not None, 
            "filter yielded nothing although %s item(s) were expected" % \
            expected_result_counter)

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertEqual(counter, expected_result_counter-1, 
            "filter yielded wrong number of items (%s), expected were %s" % (
                counter+1, expected_result_counter))

    def test_filter_attribute_constraint(self):
        """ This test uses the attribute constraint filter to select items
        from the input file. We assume here that the parser yields the
        items in the same order as specified in the example XML file. In
        a general case it would be better not to assume the order of 
        yielded items to be known, but to locate each yielded result
        item in a set of expected results.
        """

        test_attribute_dicts = [
            {'IMT': 'PGA'},
            {'endBranchLabel': '1_2'},
            {'IMT': 'PGV', 'IML': [100.0, 200.0, 300.0]}
        ]

        expected_results = [ [(shapes.Point(2.35, 48.85),
                                {'IMT': 'PGA',
                                'IDmodel': 'PGA_1_1',
                                'timeSpanDuration': 50.0,
                                'endBranchLabel': '1_1',
                                'IML': [1.0, 2.0, 3.0],
                                'maxProb': 0.9,
                                'minProb': 0.1,
                                'Values': [0.1, 0.2, 0.3],
                                'vs30': 760.0}),
                              (shapes.Point(12.45, 41.90),
                                {'IMT': 'PGA',
                                'IDmodel': 'PGA_1_1',
                                'timeSpanDuration': 50.0,
                                'endBranchLabel': '1_1',
                                'IML': [1.0, 2.0, 3.0],
                                'maxProb': 0.9,
                                'minProb': 0.1,
                                'Values': [0.1, 0.2, 0.3],
                                'vs30': 760.0}),
                              (shapes.Point(-0.2, 51.45),
                                {'IMT': 'PGA',
                                'IDmodel': 'PGA_1_2',
                                'timeSpanDuration': 50.0,
                                'endBranchLabel': '1_2',
                                'IML': [1.0, 2.0, 3.0],
                                'maxProb': 0.9,
                                'minProb': 0.1,
                                'Values': [0.01, 0.02, 0.03],
                                'vs30': 760.0}),
                              (shapes.Point(13.40, 52.50),
                                {'IMT': 'PGA',
                                'IDmodel': 'PGA_1_3',
                                'timeSpanDuration': 50.0,
                                'endBranchLabel': '1_3',
                                'IML': [1.0, 2.0, 3.0],
                                'maxProb': 0.9,
                                'minProb': 0.1,
                                'Values': [0.001, 0.002, 0.003],
                                'vs30': 760.0})],
                             [(shapes.Point(-0.2, 51.45),
                                {'IMT': 'PGA',
                                'IDmodel': 'PGA_1_2',
                                'timeSpanDuration': 50.0,
                                'endBranchLabel': '1_2',
                                'IML': [1.0, 2.0, 3.0],
                                'maxProb': 0.9,
                                'minProb': 0.1,
                                'Values': [0.01, 0.02, 0.03],
                                'vs30': 760.0}),
                              (shapes.Point(-0.2, 51.45),
                                {'IMT': 'PGV',
                                'IDmodel': 'PGV_1_2',
                                'timeSpanDuration': 50.0,
                                'endBranchLabel': '1_2',
                                'IML': [10.0, 20.0, 30.0],
                                'maxProb': 0.9,
                                'minProb': 0.1,
                                'Values': [0.01, 0.02, 0.03],
                                'vs30': 760.0})],
                             [(shapes.Point(13.40, 52.50),
                                {'IMT': 'PGV',
                                'IDmodel': 'PGV_2_1',
                                'timeSpanDuration': 20.0,
                                'endBranchLabel': '2_1',
                                'IML': [100.0, 200.0, 300.0],
                                'maxProb': 0.9,
                                'minProb': 0.1,
                                'Values': [0.005, 0.007, 0.009],
                                'vs30': 760.0})]
                           ]

        # set a region constraint that inlcudes all points 
        region_constraint = shapes.RegionConstraint.from_simple((-20.0, 80.0),
                                                                (40.0, 0.0))
        
        #print "We've made a region constraint with bounds of %s" % (str(region_constraint.bounds))
        for attr_test_counter, curr_attribute_dict in enumerate(
            test_attribute_dicts):
            attribute_constraint = \
                producer.InputConstraint(curr_attribute_dict)
            
            #print "Shaml attribute constraint is %s" % (attribute_constraint.attribute)
            
            shaml = shaml_output.ShamlOutputFile(os.path.join(test.DATA_DIR, 
                                                              TEST_FILE))

            counter = None
            for counter, (shaml_point, shaml_attr) in enumerate(
                shaml.filter(region_constraint, attribute_constraint)):

                # check topological equality for points
                self.assertTrue(shaml_point.equals(
                    expected_results[attr_test_counter][counter][0]),
                    "filter yielded unexpected point at position %s: %s, %s" \
                    % (counter, shaml_point, 
                       expected_results[attr_test_counter][counter][0]))

                self.assertEqual(shaml_attr, expected_results[
                    attr_test_counter][counter][1],
                    "filter yielded unexpected attribute values at position" \
                    " %s: %s, %s" % (counter, shaml_attr, 
                        expected_results[attr_test_counter][counter][1]))

            # ensure that generator yielded at least one item
            self.assertTrue(counter is not None, 
                "filter yielded nothing although %s item(s) were expected for attribute check of %s" % \
                (len(expected_results[attr_test_counter]), attribute_constraint.attribute))

            # ensure that generator returns exactly the number of items of the
            # expected result list
            self.assertEqual(counter, 
                len(expected_results[attr_test_counter])-1,
                "filter yielded wrong number of items (%s), expected were %s" \
                % (counter+1, len(expected_results[attr_test_counter])))
