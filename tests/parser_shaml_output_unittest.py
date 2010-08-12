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

    def test_filter_region_constraint(self):

        # find site with lon=16.35/lat=48.25
        region_constraint = region.RegionConstraint.from_simple((16.0, 48.0), (17.0, 49.0))
        shaml = shaml_output.ShamlOutputFile(os.path.join(data_dir, 
                                                          TEST_FILE))

        for cell, value in shaml.filter(region_constraint):
            pass

