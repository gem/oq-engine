# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

'''
Tests of the parser module openquake.hmtk.parsers.fault.fault_yaml_parser,
to parser the fault from a Yaml format to a fault source
'''
import os
import unittest
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hmtk.faults.fault_geometries import (SimpleFaultGeometry,
                                          ComplexFaultGeometry)
from openquake.hmtk.parsers.faults.fault_yaml_parser import (
    weight_list_to_tuple,
    parse_tect_region_dict_to_tuples,
    get_scaling_relation_tuple,
    FaultYmltoSource)


BASE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'yaml_examples')
BAD_INPUT_FILE = os.path.join(BASE_FILE_PATH, 'bad_input_fault_example.yml')
BAD_GEOMETRY_FILE = os.path.join(BASE_FILE_PATH,
                                 'bad_geometry_fault_example.yml')
SIMPLE_GEOMETRY_FILE = os.path.join(BASE_FILE_PATH,
                                    'simple_fault_example.yml')
COMPLEX_GEOMETRY_FILE = os.path.join(BASE_FILE_PATH,
                                     'complex_fault_example.yml')


class TestYamlParserPeripherals(unittest.TestCase):
    '''
    Class to test all the peripherical functions to the Yaml parser
    '''
    def setUp(self):
        self.data = None

    def test_weight_list_to_tuple(self):
        # Test weight list to tuple function

        # Test 1 - number of values not equal to number of weights
        self.data = {'Value': [1.0, 2.0, 3.0],
                     'Weight': [0.5, 0.5]}
        with self.assertRaises(ValueError) as ae:
            weight_list_to_tuple(self.data, 'Test Values')
        self.assertEqual(str(ae.exception),
                         'Number of weights do not correspond to number of '
                         'attributes in Test Values')

        # Test 2 - Weights do not sum to 1.0
        self.data = {'Value': [1.0, 2.0, 3.0],
                     'Weight': [0.3, 0.3, 0.3]}
        with self.assertRaises(ValueError) as ae:
            weight_list_to_tuple(self.data, 'Test Values')
        self.assertEqual(str(ae.exception),
                         'Weights do not sum to 1.0 in Test Values')

        # Test good output
        expected_output = [(1.0, 0.5), (2.0, 0.5)]
        self.data = {'Value': [1.0, 2.0],
                     'Weight': [0.5, 0.5]}
        self.assertListEqual(expected_output,
                             weight_list_to_tuple(self.data, 'Test Values'))

    def test_parse_region_list_to_tuples(self):
        # Tests the function to parse a region list to a set of tuples
        self.data = {
            'Shear_Modulus': {'Value': [30.], 'Weight': [1.0]},
            'Displacement_Length_Ratio': {'Value': [1.25E-5], 'Weight': [1.0]},
            'Magnitude_Scaling_Relation': {'Value': [WC1994()],
                                           'Weight': [1.0]}}
        expected_output = {'Shear_Modulus': [(30., 1.0)],
                           'Displacement_Length_Ratio': [(1.25E-5, 1.0)],
                           'Magnitude_Scaling_Relation': [(WC1994(), 1.0)]}
        output = parse_tect_region_dict_to_tuples([self.data])
        self.assertAlmostEqual(expected_output['Shear_Modulus'][0][0],
                                output[0]['Shear_Modulus'][0][0])
        self.assertAlmostEqual(expected_output['Shear_Modulus'][0][1],
                                output[0]['Shear_Modulus'][0][1])
        self.assertAlmostEqual(
            expected_output['Displacement_Length_Ratio'][0][0],
            output[0]['Displacement_Length_Ratio'][0][0])
        self.assertAlmostEqual(
            expected_output['Displacement_Length_Ratio'][0][1],
            output[0]['Displacement_Length_Ratio'][0][1])

        self.assertTrue(isinstance(
            output[0]['Magnitude_Scaling_Relation'][0][0],
            WC1994))
        self.assertAlmostEqual(
            expected_output['Magnitude_Scaling_Relation'][0][1],
            output[0]['Shear_Modulus'][0][1])

    def test_get_scaling_relation_tuple(self):
        # Tests the function to get the scaling relation tuple
        # Test with an unsupported MSR
        self.data = {'Value': ['BadMSR'],
                     'Weight': [1.0]}
        with self.assertRaises(ValueError) as ae:
            get_scaling_relation_tuple(self.data)
        self.assertEqual(str(ae.exception),
                         'Scaling relation BadMSR not supported!')

        # Test with both supported MSRs
        self.data = {'Value': ['WC1994', 'PeerMSR'],
                     'Weight': [0.5, 0.5]}
        result = get_scaling_relation_tuple(self.data)
        self.assertTrue(isinstance(result[0][0], WC1994))
        self.assertTrue(isinstance(result[1][0], PeerMSR))
        self.assertAlmostEqual(result[0][1], 0.5)
        self.assertAlmostEqual(result[1][1], 0.5)


class TestFaultYamlParser(unittest.TestCase):
    '''
    Main test class of the Fault Yaml Parser function
    '''
    def setUp(self):
        self.parser = None
        self.fault_geometry = None

    def test_bad_input_fault_model(self):
        # Test that when Yaml is missing 'Fault_Model' atribute an error is
        # raised
        with self.assertRaises(ValueError) as ae:
            self.parser = FaultYmltoSource(BAD_INPUT_FILE)
        self.assertEqual(str(ae.exception),
                         'Fault Model not defined in input file!')

    def test_bad_geometry_input(self):
        # Tests that an unknown geomtry error is raised when not recognised
        self.parser = FaultYmltoSource(BAD_GEOMETRY_FILE)
        with self.assertRaises(ValueError) as ae:
            self.parser.read_file()
        self.assertEqual(str(ae.exception),
                         'Unrecognised or unsupported fault geometry!')

    def test_simple_fault_input(self):
        # Tests a simple fault input
        self.parser = FaultYmltoSource(SIMPLE_GEOMETRY_FILE)
        fault_model, tect_reg = self.parser.read_file()
        # Test that the area is correct and the slip rate
        self.assertAlmostEqual(fault_model.faults[0].area,
                               3851.9052498454062)
        expected_slip = [(18.0, 0.3), (20.0, 0.5), (23.0, 0.2)]
        for iloc, slip in enumerate(expected_slip):
            self.assertAlmostEqual(
                slip[0], fault_model.faults[0].slip[iloc][0])
            self.assertAlmostEqual(
                slip[1], fault_model.faults[0].slip[iloc][1])

        self.assertTrue(isinstance(fault_model.faults[0].geometry,
                                   SimpleFaultGeometry))

    def test_complex_fault_input(self):
        # Tests a complex fault input
        # Quick test - just ensure that the area and the slip rate are expected
        self.parser = FaultYmltoSource(COMPLEX_GEOMETRY_FILE)
        fault_model, tect_reg = self.parser.read_file(2.0)
        # Test that the area is correct and the slip rate
        self.assertAlmostEqual(fault_model.faults[0].area,
                               13745.614848626545)
        expected_slip = [(18.0, 0.3), (20.0, 0.5), (23.0, 0.2)]
        for iloc, slip in enumerate(expected_slip):
            self.assertAlmostEqual(
                slip[0], fault_model.faults[0].slip[iloc][0])
            self.assertAlmostEqual(
                slip[1], fault_model.faults[0].slip[iloc][1])

        self.assertTrue(isinstance(fault_model.faults[0].geometry,
                                   ComplexFaultGeometry))
