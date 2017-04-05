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
Module to test :openquake.hmtk.faults.tectonic_regionalisation class
'''
import unittest
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hmtk.faults.tectonic_regionalisation import (_check_list_weights,
                                                  TectonicRegion,
                                                  TectonicRegionalisation)


class TestCheckUtil(unittest.TestCase):
    '''
    Simply tests the openquake.hmtk.faults.tectonic_regionalisation._check_list_weights
    function
    '''
    def test_correct_instance(self):
        # Tests the instance when the list of parameters is entered correctly
        # as a tuple with weights summing to 1.0

        # Single entry
        params = [('Something', 1.0)]
        self.assertListEqual(params, _check_list_weights(params, 'Test 0'))

        # Multiple entry
        params = [('Something', 0.5), ('Something Else', 0.5)]
        self.assertListEqual(params, _check_list_weights(params, 'Test 1'))

    def test_error_weights_not_1(self):
        # Tests that an error is raised when the weights do not sum to 1.0
        params = [('Something', 0.5), ('Something Else', 0.4)]
        with self.assertRaises(ValueError) as ae:
            _check_list_weights(params, 'Bad Test 1')
        self.assertEqual(str(ae.exception),
                         'Bad Test 1 weights do not sum to 1.0!')

    def test_incorrect_format(self):
        # Tests that an error is raised if the input is not iterable
        params = None
        with self.assertRaises(ValueError) as ae:
            _check_list_weights(params, 'Bad Test 2')
        self.assertEqual(str(ae.exception),
                         'Bad Test 2 must be formatted with a list of tuples')


class TestTectonicRegion(unittest.TestCase):
    '''
    Tests that a openquake.hmtk.faults.tectonic_regionalistion.TectonicRegion class
    has been raised correctly
    '''
    def setUp(self):
        self.tect_reg = None

    def test_all_defaults(self):
        # Tests correct instantiation with default values
        self.tect_reg = TectonicRegion('001', 'Test 0')
        self.assertEqual(self.tect_reg.id, '001')
        self.assertEqual(self.tect_reg.region_name, 'Test 0')
        self.assertAlmostEqual(self.tect_reg.shear_modulus[0][0], 30.0)
        self.assertAlmostEqual(self.tect_reg.shear_modulus[0][1], 1.0)
        self.assertAlmostEqual(self.tect_reg.disp_length_ratio[0][0],
                               1.25E-5)
        self.assertAlmostEqual(self.tect_reg.disp_length_ratio[0][1], 1.0)
        self.assertTrue(isinstance(self.tect_reg.scaling_rel[0][0], WC1994))
        self.assertAlmostEqual(self.tect_reg.scaling_rel[0][1], 1.0)


    def test_input_values(self):
        '''
        Tests correct instantiation with input values
        '''
        expected_dict = {'id': '001',
                         'region_name': 'Test 0',
                         'shear_modulus': [(28., 0.5), (32., 0.5)],
                         'disp_length_ratio': [(1.0E-4, 1.0)],
                         'scaling_rel': [(WC1994, 1.0)]}

        shear_mod = [(28., 0.5), (32., 0.5)]
        dlr = [(1.0E-4, 1.0)]
        msr = [(WC1994, 1.0)]
        self.tect_reg = TectonicRegion('001',
                                       'Test 0',
                                       shear_modulus=shear_mod,
                                       disp_length_ratio=dlr,
                                       scaling_rel=msr)
        self.assertDictEqual(expected_dict, self.tect_reg.__dict__)


class TestTectonicRegionalisation(unittest.TestCase):
    '''
    Class to test the module
    openquake.hmtk.faults.tectonic_regionalisation.TectonicRegionalisation
    '''
    def setUp(self):
        '''
        '''
        self.tect_reg = None

    def test_basic_instantiation(self):
        '''
        Test simple setup
        '''
        # Test setup
        self.tect_reg = TectonicRegionalisation()
        self.assertDictEqual({'regionalisation': [], 'key_list': []},
                             self.tect_reg.__dict__)
        # Check number of regions is 0
        self.assertEqual(0, self.tect_reg.get_number_regions())

    def test_populate_region_accepting_defaults(self):
        '''
        Tests the population of the tectonic regions with default values
        '''
        region_dict = [{'Code': '001', 'Name': 'Active Shallow'}]
        expected_key_list = ['Active Shallow']
        self.tect_reg = TectonicRegionalisation()
        self.tect_reg.populate_regions(region_dict)
        trg = self.tect_reg.regionalisation[0]
        self.assertEqual(trg.id, '001')
        self.assertEqual(trg.region_name, 'Active Shallow')
        self.assertAlmostEqual(trg.shear_modulus[0][0], 30.0)
        self.assertAlmostEqual(trg.shear_modulus[0][1], 1.0)
        self.assertAlmostEqual(trg.disp_length_ratio[0][0], 1.25E-5)
        self.assertAlmostEqual(trg.disp_length_ratio[0][1], 1.0)
        self.assertTrue(isinstance(trg.scaling_rel[0][0], WC1994))
        self.assertAlmostEqual(trg.scaling_rel[0][1], 1.0)
        self.assertListEqual(expected_key_list, self.tect_reg.key_list)
        self.assertEqual(1, self.tect_reg.get_number_regions())

    def test_poplate_region_with_inputs(self):
        '''
        Tests the population of the tectonic regions with input values
        '''
        region_dict = [{'Code': '001',
                        'Name': 'Active Shallow',
                        'Shear_Modulus': [(20., 0.3), (30., 0.7)],
                        'Displacement_Length_Ratio': [(1.5E-5, 1.0)],
                        'Magnitude_Scaling_Relation': [(WC1994, 1.0)]},
                        {'Code': '002',
                        'Name': 'Stable Continental',
                        'Shear_Modulus': [(30., 1.0)],
                        'Displacement_Length_Ratio': [(1.0E-4, 1.0)],
                        'Magnitude_Scaling_Relation': [(WC1994, 1.0)]}
                        ]

        expected_key_list = ['Active Shallow', 'Stable Continental']
        expected_regions = [{'id': '001',
                             'region_name': 'Active Shallow',
                             'shear_modulus': [(20., 0.3), (30., 0.7)],
                             'disp_length_ratio': [(1.5E-5, 1.0)],
                             'scaling_rel': [(WC1994, 1.0)]},
                            {'id': '002',
                             'region_name': 'Stable Continental',
                             'shear_modulus': [(30., 1.0)],
                             'disp_length_ratio': [(1.0E-4, 1.0)],
                             'scaling_rel': [(WC1994, 1.0)]}]
        self.tect_reg = TectonicRegionalisation()
        self.tect_reg.populate_regions(region_dict)
        for ival, test_reg in enumerate(self.tect_reg.regionalisation):
            self.assertDictEqual(expected_regions[ival],
                                 test_reg.__dict__)
        self.assertListEqual(expected_key_list, self.tect_reg.key_list)
        self.assertEqual(2, self.tect_reg.get_number_regions())
