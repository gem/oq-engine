# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from openquake import shapes
from openquake import test
from openquake import producer
from openquake.parser import hazard as hazard_parser

FILES_KNOWN_TO_FAIL = ['Nrml-fail-missing_required_attribute.xml',
                       'Nrml-fail-attribute_type_mismatch.xml',
                       'Nrml-fail-IML_type_mismatch.xml',
                       'Nrml-fail-missing_IML.xml',
                       'Nrml-fail-illegal_gml_pos.xml',
                       'Nrml-fail-curve_values_type_mismatch.xml']

FILE_FLAVOUR_NOT_IMPLEMENTED = 'Nrml-HazardMap-PASS.xml'

EXAMPLE_DIR = os.path.join(test.SCHEMA_DIR, 'examples/failures')
TEST_FILE = os.path.join(test.SCHEMA_DIR, 'examples/hazard-curves.xml')

class NrmlFileTestCase(unittest.TestCase):
    
    def setUp(self):
        self.nrml_element = hazard_parser.NrmlFile(TEST_FILE)

    def test_nrml_files_known_to_fail(self):
        for testfile in FILES_KNOWN_TO_FAIL:
            nrml_element = hazard_parser.NrmlFile(os.path.join(EXAMPLE_DIR, 
                                                              testfile))

            self.assertRaises(ValueError, map, None, nrml_element)
            
    @test.skipit
    # Not yet implemented
    def test_nrml_files_hazardmap_not_implemented(self):
        nrml_element = hazard_parser.NrmlFile(os.path.join(EXAMPLE_DIR, 
            FILE_FLAVOUR_NOT_IMPLEMENTED))

        self.assertRaises(NotImplementedError, map, None, nrml_element)
    
    def test_filter_region_constraint_known_to_fail(self):
        # set region in which no site is found in input file
        region_constraint = shapes.RegionConstraint.from_simple((170.0, -80.0),
                                                                (175.0, -85.0))
        counter = None

        # this loop is not expected to be entered - generator should
        # not yield any item
        for counter, nrml_item in enumerate(self.nrml_element.filter
            (region_constraint)):
            pass

        # ensure that generator didn't yield an item
        self.assertTrue(counter is None, 
            "filter yielded item(s) although no items were expected")
    
    def test_filter_region_constraint_one_site(self):

        # look for sites within specified rectangle
        # constraint is met by one and only one site in the example file 
        # (lon=16.35/lat=48.25)
        region_constraint = shapes.RegionConstraint.from_simple((-122.45, 38.0),
                                                                (-122.35, 37.0))
        expected_result = [(shapes.Point(-122.40, 37.50),
                           {'IMT': 'PGA',
                            'IDmodel': 'PGA_1_1',
                            'timeSpanDuration': 50.0,
                            'endBranchLabel': 'Foo',
                            'saDamping': 0.2,
                            'saPeriod': 0.1,
                            'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02,
                            1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                            7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                            2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                            7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                            'Values': [9.8784e-01, 9.8405e-01, 9.5719e-01,
                            9.1955e-01, 8.5019e-01, 7.4038e-01, 5.9153e-01,
                            4.2626e-01, 2.9755e-01, 2.7731e-01, 1.6218e-01,
                            8.8035e-02, 4.3499e-02, 1.9065e-02, 7.0442e-03,
                            2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]})]

        counter = None
        for counter, (nrml_point, nrml_attr) in enumerate(
            self.nrml_element.filter(region_constraint)):

            # check topological equality for points
            self.assertTrue(nrml_point.equals(expected_result[counter][0]),
                "filter yielded unexpected point at position %s: %s, %s" % (
                counter, nrml_point, expected_result[counter][0]))

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
    
    def test_filter_region_constraint_all_sites(self):

        # specified rectangle contains all sites in example file 
        region_constraint = shapes.RegionConstraint.from_simple((-125.0, 40.0),
                                                                (-120.0, 20.0))

        expected_result_counter = 4
        counter = None

        # just loop through iterator in order to count items
        for counter, (nrml_point, nrml_attr) in enumerate(
            self.nrml_element.filter(region_constraint)):
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
    
    def test_reads_from_different_branch_labels(self):
        pass
        
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
            {'endBranchLabel': 'Foo'},
            {'IMT': 'PGA', 'Values': [9.8728e-01, 9.8266e-01, 9.4957e-01,
            9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01,
            3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01,
            7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03,
            2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]}
        ]

        expected_results = [ 
                            [(shapes.Point(-122.5000, 37.5000),
                            {'IMT': 'PGA',
                            'IDmodel': 'PGA_1_1',
                            'timeSpanDuration': 50.0,
                            'endBranchLabel': 'Foo',
                            'saDamping': 0.2,
                            'saPeriod': 0.1,
                            'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02,
                            1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                            7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                            2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                            7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                            'Values': [9.8728e-01, 9.8266e-01, 9.4957e-01,
                            9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01,
                            3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01,
                            7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03,
                            2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]}),
                            (shapes.Point(-122.4000, 37.5000),
                            {'IMT': 'PGA',
                            'IDmodel': 'PGA_1_1',
                            'timeSpanDuration': 50.0,
                            'endBranchLabel': 'Foo',
                            'saDamping': 0.2,
                            'saPeriod': 0.1,
                            'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02,
                            1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                            7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                            2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                            7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                            'Values': [9.8784e-01, 9.8405e-01, 9.5719e-01,
                            9.1955e-01, 8.5019e-01, 7.4038e-01, 5.9153e-01,
                            4.2626e-01, 2.9755e-01, 2.7731e-01, 1.6218e-01,
                            8.8035e-02, 4.3499e-02, 1.9065e-02, 7.0442e-03,
                            2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]}),
                            (shapes.Point(-122.3000, 37.5000),
                            {'IMT': 'PGA',
                            'IDmodel': 'PGA_1_1',
                            'timeSpanDuration': 50.0,
                            'endBranchLabel': 'Foo',
                            'saDamping': 0.2,
                            'saPeriod': 0.1,
                            'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02,
                            1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                            7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                            2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                            7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                            'Values': [9.8822e-01, 9.8499e-01, 9.6243e-01,
                            9.3086e-01, 8.7155e-01, 7.7398e-01, 6.3413e-01,
                            4.6796e-01, 3.3025e-01, 3.0795e-01, 1.7852e-01,
                            9.4528e-02, 4.5402e-02, 1.9435e-02, 7.0961e-03,
                            2.1325e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]})
                           ],
                           [(shapes.Point(-122.5000, 37.5000),
                           {'IMT': 'PGA',
                           'IDmodel': 'PGA_1_1',
                           'timeSpanDuration': 50.0,
                           'endBranchLabel': 'Foo',
                           'saDamping': 0.2,
                           'saPeriod': 0.1,
                           'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02,
                           1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                           7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                           2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                           7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                           'Values': [9.8728e-01, 9.8266e-01, 9.4957e-01,
                           9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01,
                           3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01,
                           7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03,
                           2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]}),
                           (shapes.Point(-122.4000, 37.5000),
                           {'IMT': 'PGA',
                           'IDmodel': 'PGA_1_1',
                           'timeSpanDuration': 50.0,
                           'endBranchLabel': 'Foo',
                           'saDamping': 0.2,
                           'saPeriod': 0.1,
                           'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02,
                           1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                           7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                           2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                           7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                           'Values': [9.8784e-01, 9.8405e-01, 9.5719e-01,
                           9.1955e-01, 8.5019e-01, 7.4038e-01, 5.9153e-01,
                           4.2626e-01, 2.9755e-01, 2.7731e-01, 1.6218e-01,
                           8.8035e-02, 4.3499e-02, 1.9065e-02, 7.0442e-03,
                           2.1300e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]}),
                           (shapes.Point(-122.3000, 37.5000),
                           {'IMT': 'PGA',
                           'IDmodel': 'PGA_1_1',
                           'timeSpanDuration': 50.0,
                           'endBranchLabel': 'Foo',
                           'saDamping': 0.2,
                           'saPeriod': 0.1,
                           'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02,
                           1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                           7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                           2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                           7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                           'Values': [9.8822e-01, 9.8499e-01, 9.6243e-01,
                           9.3086e-01, 8.7155e-01, 7.7398e-01, 6.3413e-01,
                           4.6796e-01, 3.3025e-01, 3.0795e-01, 1.7852e-01,
                           9.4528e-02, 4.5402e-02, 1.9435e-02, 7.0961e-03,
                           2.1325e-03, 4.9498e-04, 8.1768e-05, 7.3425e-06]})
                          ],[ (shapes.Point(-122.5000, 37.5000),
                           {'IMT': 'PGA',
                           'IDmodel': 'PGA_1_1',
                           'timeSpanDuration': 50.0,
                           'endBranchLabel': 'Foo',
                           'saDamping': 0.2,
                           'saPeriod': 0.1,
                           'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02,
                           1.9200e-02, 2.6900e-02, 3.7600e-02, 5.2700e-02,
                           7.3800e-02, 9.8000e-02, 1.0300e-01, 1.4500e-01,
                           2.0300e-01, 2.8400e-01, 3.9700e-01, 5.5600e-01,
                           7.7800e-01, 1.0900e+00, 1.5200e+00, 2.1300e+00],
                           'Values': [9.8728e-01, 9.8266e-01, 9.4957e-01,
                           9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01,
                           3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01,
                           7.0352e-02, 3.6060e-02, 1.6579e-02, 6.4213e-03,
                           2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06]})]]

        # set a region constraint that inlcudes all points 
        region_constraint = shapes.RegionConstraint.from_simple((-125.0, 40.0),
                                                                (-120.0, 20.0))
      
        for attr_test_counter, curr_attribute_dict in enumerate(
            test_attribute_dicts):
            attribute_constraint = producer.AttributeConstraint(
                    curr_attribute_dict)

            counter = None
            for counter, (nrml_point, nrml_attr) in enumerate(
                            self.nrml_element.filter(region_constraint, 
                                    attribute_constraint)):

                # check topological equality for points
                self.assertTrue(nrml_point.equals(
                    expected_results[attr_test_counter][counter][0]),
                    "filter yielded unexpected point at position %s: %s, %s" \
                    % (counter, nrml_point, 
                       expected_results[attr_test_counter][counter][0]))

                self.assertEqual(nrml_attr, expected_results[
                    attr_test_counter][counter][1],
                    "filter yielded unexpected attribute values at position" \
                    " %s: %s, %s" % (counter, nrml_attr, 
                        expected_results[attr_test_counter][counter][1]))
            
            # ensure that generator yielded at least one item
            self.assertTrue(counter is not None, 
                "filter yielded nothing although %s item(s) were expected \
                 for attribute check of %s" % \
                (len(expected_results[attr_test_counter]),
                    attribute_constraint.attribute))

            # ensure that generator returns exactly the number of items of the
            # expected result list
            self.assertEqual(counter, 
                len(expected_results[attr_test_counter])-1,
                "filter yielded wrong number of items (%s), expected were %s" \
                % (counter+1, len(expected_results[attr_test_counter])))
            
            self.nrml_element.reset()
