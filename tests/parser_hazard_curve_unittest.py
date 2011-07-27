# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


import os
import unittest

from openquake import shapes
from tests.utils import helpers
from openquake import producer
from openquake.parser import hazard as hazard_parser

FILES_KNOWN_TO_FAIL = [
    'Nrml-fail-missing_required_attribute.xml',
    'Nrml-fail-attribute_type_mismatch.xml',
    'Nrml-fail-IML_type_mismatch.xml',
    'Nrml-fail-missing_IML.xml',
    'Nrml-fail-illegal_gml_pos.xml',
    'Nrml-fail-curve_values_type_mismatch.xml']

FILE_FLAVOUR_NOT_IMPLEMENTED = 'hazard-map.xml'

EXAMPLE_DIR = os.path.join(helpers.SCHEMA_DIR, 'examples')
FAIL_EXAMPLE_DIR = os.path.join(EXAMPLE_DIR, 'failures')
TEST_FILE = os.path.join(EXAMPLE_DIR,
                         'hazard-curves.xml')


class NrmlFileTestCase(unittest.TestCase):

    def setUp(self):
        self.nrml_element = hazard_parser.NrmlFile(TEST_FILE)

    def test_nrml_files_known_to_fail(self):
        for testfile in FILES_KNOWN_TO_FAIL:
            nrml_element = hazard_parser.NrmlFile(os.path.join(
                FAIL_EXAMPLE_DIR, testfile))

            self.assertRaises(ValueError, map, None, nrml_element)

    def test_filter_region_constraint_known_to_fail(self):
        # set region in which no site is found in input file
        region_constraint = shapes.RegionConstraint.from_simple(
            (170.0, -80.0), (175.0, -85.0))
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
        region_constraint = shapes.RegionConstraint.from_simple(
            (-123.0, 38.0), (-122.0, 37.0))
        expected_result = [
            (shapes.Site(-122.5, 37.5),
            {'IMT': 'PGA',
             'IDmodel': 'PGA_1_1',
             'investigationTimeSpan': 50.0,
             'endBranchLabel': '1_1',
             'saDamping': 0.2,
             'saPeriod': 0.1,
             'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02],
             'PoEValues': [9.8728e-01, 9.8266e-01, 9.4957e-01]})]

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
        self.assertEqual(counter, len(expected_result) - 1,
            "filter yielded wrong number of items (%s), expected were %s" % (
                counter + 1, len(expected_result)))

    def test_filter_region_constraint_all_sites(self):

        # specified rectangle contains all sites in example file
        region_constraint = shapes.RegionConstraint.from_simple(
            (-126.0, 40.0), (-120.0, 20.0))

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
        self.assertEqual(counter, expected_result_counter - 1,
            "filter yielded wrong number of items (%s), expected were %s" % (
                counter + 1, expected_result_counter))

    def test_filter_attribute_constraint(self):
        """ This test uses the attribute constraint filter to select items
        from the input file. We assume here that the parser yields the
        items in the same order as specified in the example XML file. In
        a general case it would be better not to assume the order of
        yielded items to be known, but to locate each yielded result
        item in a set of expected results.
        """

        test_filters = [
            {'IMT': 'PGA'},
            {'IMT': 'FAKE'},
            {'IMLValues': [0.0001, 0.0002, 0.0003]},
            {'PoEValues': [9.2e-01, 9.15e-01, 9.05e-01]}]

        # this is the structure of the test NRML file
        # we'll use this to construct an 'expected results' list
        nrml_data = [
                     # first hazardCurveField
                     (shapes.Site(-122.5000, 37.5000),
                      {'IMT': 'PGA',
                       'IDmodel': 'PGA_1_1',
                       'investigationTimeSpan': 50.0,
                       'endBranchLabel': '1_1',
                       'saDamping': 0.2,
                       'saPeriod': 0.1,
                       'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02],
                       'PoEValues': [9.8728e-01, 9.8266e-01, 9.4957e-01]}),
                     (shapes.Site(-123.5000, 37.5000),
                      {'IMT': 'PGA',
                       'IDmodel': 'PGA_1_1',
                       'investigationTimeSpan': 50.0,
                       'endBranchLabel': '1_1',
                       'saDamping': 0.2,
                       'saPeriod': 0.1,
                       'IMLValues': [5.0000e-03, 7.0000e-03, 1.3700e-02],
                       'PoEValues': [9.8728e-02, 9.8266e-02, 9.4957e-02]}),
                     # second hazardCurveField
                     (shapes.Site(-125.5000, 37.5000),
                      {'IMT': 'PGA',
                       'IDmodel': 'PGA_1_1',
                       'investigationTimeSpan': 50.0,
                       'endBranchLabel': '1_1',
                       'saDamping': 0.2,
                       'saPeriod': 0.1,
                       'IMLValues': [0.0001, 0.0002, 0.0003],
                       'PoEValues': [9.3e-01, 9.2e-01, 9.1e-01]}),
                     # third hazardCurveField
                     (shapes.Site(-125.5000, 37.5000),
                      {'IMT': 'PGA',
                       'IDmodel': 'PGA_1_1',
                       'investigationTimeSpan': 50.0,
                       'endBranchLabel': '1_1',
                       'saDamping': 0.2,
                       'saPeriod': 0.1,
                       'IMLValues': [0.0001, 0.0002, 0.0003],
                       'PoEValues': [9.2e-01, 9.15e-01, 9.05e-01]})]

        # one list of results for each test_filter
        expected_results = [
            nrml_data,
            [],
            [nrml_data[2], nrml_data[3]],
            [nrml_data[3]]]

        # set a region constraint that inlcudes all points
        region_constraint = shapes.RegionConstraint.from_simple(
            (-126.0, 40.0), (-120.0, 30.0))

        for filter_counter, filter_dict in enumerate(
            test_filters):
            attribute_constraint = producer.AttributeConstraint(
                    filter_dict)

            counter = None
            for counter, (nrml_point, nrml_attr) in enumerate(
                            self.nrml_element.filter(region_constraint,
                                    attribute_constraint)):
                if expected_results[filter_counter]:
                    # only perform the following tests if the expected
                    # result item is not empty

                    expected_nrml_point = \
                        expected_results[filter_counter][counter][0]
                    expected_nrml_attr = \
                        expected_results[filter_counter][counter][1]
                    # check topological equality for points
                    self.assertTrue(nrml_point.equals(expected_nrml_point),
                        "filter yielded unexpected point at position" \
                        " %s: \n Got: %s, \n Expected: %s " \
                        % (counter, nrml_point,
                        expected_nrml_point))

                    self.assertEqual(nrml_attr, expected_nrml_attr,
                        "filter yielded unexpected attribute values at " \
                        "position %s: \n Got: %s, \n Expected: %s " \
                        % (counter, nrml_attr, expected_nrml_attr))

            if expected_results[filter_counter]:
                # ensure that generator yielded at least one item
                self.assertTrue(counter is not None,
                    "filter yielded nothing although %s item(s) were expected \
                    for attribute check of %s" % \
                    (len(expected_results[filter_counter]),
                        attribute_constraint.attribute))

                # ensure that the generator returns _exactly_ the number of
                # items in the expected result list
                self.assertEqual(len(expected_results[filter_counter]),
                                 counter + 1,
                                 "filter yielded incorrect number of items \
                                 \n Got: %s \n Expected: %s" \
                                 % (counter,
                                    len(expected_results[filter_counter])))
            else:
                # verify that 0 elements were received
                self.assertTrue(counter is None)

            self.nrml_element.reset()


class GMFReaderTestCase(unittest.TestCase):

    def test_gmf_reader_yields_correct_parsed_values(self):
        test_file = os.path.join(EXAMPLE_DIR, 'gmf-simple-fault.xml')
        expected_output = [(shapes.Site(-116.0, 41.0),
                            {'groundMotion': 0.2}),
                           (shapes.Site(-118.0, 41.0),
                            {'groundMotion': 0.3})]

        reader = hazard_parser.GMFReader(test_file)

        for (counter, (site, ground_motion)) in enumerate(reader):
            # verify that each result matches what is expected
            # order matters here
            expected_site = expected_output[counter][0]
            expected_gm = expected_output[counter][1]
            self.assertEqual(expected_site, site)
            self.assertEqual(expected_gm, ground_motion)

        # verify that we have the correct number of results
        self.assertEqual(len(expected_output), counter + 1)
