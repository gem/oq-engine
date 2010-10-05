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
    
    def test_filter_attribute_constraint(self):
        """ This test uses the attribute constraint filter to select items
        from the input file. We assume here that the parser yields the
        items in the same order as specified in the example XML file. In
        a general case it would be better not to assume the order of 
        yielded items to be known, but to locate each yielded result
        item in a set of expected results.
        """
        test_attribute_dicts = [
            {'endBranchLabel': '3_1'}
        ]

        expected_results = [(shapes.Point(-122.5000, 37.5000),
                {'Values': [9.8728e-01, 9.8266e-01, 9.4957e-01, 9.0326e-01, 
                8.1956e-01, 6.9192e-01, 5.2866e-01, 3.6143e-01, 2.4231e-01, 
                2.2452e-01, 1.2831e-01, 7.0352e-02, 3.6060e-02, 1.6579e-02, 
                6.4213e-03, 2.0244e-03, 4.8605e-04, 8.1752e-05, 7.3425e-06],
                'IMLValues':[0.005, 0.007, 0.0137, 0.0192, 0.0269, 0.0376, 
                0.0527, 0.0738, 0.098, 0.103, 0.145, 0.203, 0.284, 0.397, 
                0.556, 0.778, 1.09, 1.52, 2.13]
            })]
                           
        for attr_test_counter, curr_attribute_dict in enumerate(
            test_attribute_dicts):
            attr_const = nrml.HazardConstraint(curr_attribute_dict)

            nrml_element = nrml.NrmlFile(os.path.join(test.DATA_DIR, TEST_FILE))
            counter = 1
            
            for (counter, hazard_attr) in enumerate(
                nrml_element.filter(attribute_constraint=attr_const)):
                self.assertEqual(hazard_attr, expected_results
                                            [attr_test_counter][counter],
                    "filter yielded unexpected attribute values at position"
                    " %s: %s, %s" % (counter, hazard_attr, 
                        expected_results[attr_test_counter][counter]))
            
            # ensure that generator yielded at least one item
            self.assertTrue(counter is not None, 
                "filter yielded nothing although %s item(s) were expected" %
                len(expected_results[attr_test_counter]))
            
            # ensure that generator returns exactly the number of items of the
            # expected result list
            self.assertEqual(counter, 
                len(expected_results[attr_test_counter])-1,
                "filter yielded wrong number of items (%s), expected were %s"
                % (counter+1, len(expected_results[attr_test_counter])))