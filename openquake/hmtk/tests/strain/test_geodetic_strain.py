# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
#License as published by the Free Software Foundation, either version
#3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
#DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
#is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
#Earthquake Model).
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
#ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
#for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.
'''
Test suite for openquake.hmtk.strain.geodetic_strain.GeodeticStrain a set of utility
functions for the main geodetic strain class
'''
import unittest
import numpy as np
from openquake.hmtk.strain.geodetic_strain import GeodeticStrain


class TestGeodeticStrain(unittest.TestCase):
    '''
    Tests the :class: openquake.hmtk.strain.geodetic_strain.GeodeticStrain
    '''
    def setUp(self):
        '''
        '''
        self.data = {}
        self.model = GeodeticStrain()

    def test_instantiation(self):
        '''
        Tests the basic instantiation of the class
        '''

        expected_dict = {'data': None,
                         'regions': None,
                         'seismicity_rate': None,
                         'regionalisation': None,
                         'target_magnitudes': None,
                         'data_variables': []}
        self.assertDictEqual(expected_dict, self.model.__dict__)

    def test_secondary_strain_data_input_error(self):
        '''
        Tests to ensure correct error are raised when
        i) strain data is missing
        ii) Strain data lacks critical attribute
        '''
        # No strain data
        with self.assertRaises(ValueError) as ae:
            self.model.get_secondary_strain_data()
        self.assertEqual(str(ae.exception),
                         'Strain data not input or incorrectly formatted')

        # Strain data missing critical attribute - e.g. exy
        self.data = {'longitude': np.array([10., 20., 30.]),
                     'latitude': np.array([10., 20., 30.]),
                     'exx': np.array([1E-9, 20E-9, 25E-9]),
                     'eyy': np.array([1E-9, 20E-9, 25E-9])}
        with self.assertRaises(ValueError) as ae:
            self.model.get_secondary_strain_data(self.data)
        self.assertEqual(str(ae.exception),
                         'Essential strain information exy missing!')

    def test_secondary_strain_data_with_input(self):
        '''
        Test to verify correct calculation of
        i)
        i)   Second Invarient
        ii)  err
        iii) dilatation
        iv)  e1h & e2h
        '''

        self.data = {'longitude': np.array([10., 20., 30.]),
                     'latitude': np.array([10., 20., 30.]),
                     'exx': 1E-9 * np.array([100., 10.0, 1.0]),
                     'eyy': 1E-9 * np.array([50., 5.0, 0.5]),
                     'exy': 1E-9 * np.array([10., 1.0, 0.1])}
        self.model.get_secondary_strain_data(self.data)
        # Check that all expected keys are present
        expected_keys = ['longitude', 'latitude', 'exx', 'eyy', 'exy',
                         '2nd_inv', 'dilatation', 'err', 'e1h', 'e2h']
        for key in expected_keys:
            self.assertTrue(key in self.model.data.keys())

        # Test second invariant
        np.testing.assert_array_almost_equal(
            np.log10(self.model.data['2nd_inv']),
            np.array([-6.94809814, -7.94809814, -8.94809814]))
        # Test dilatation
        np.testing.assert_array_almost_equal(
            np.log10(self.model.data['dilatation']),
            np.array([-6.82390874, -7.82390874, -8.82390874]))
        # Test err
        np.testing.assert_array_almost_equal(
            self.model.data['dilatation'] + self.model.data['err'],
            np.zeros(3, dtype=float),
            14)
        # Test e1h
        np.testing.assert_array_almost_equal(
            np.log10(self.model.data['e1h']),
            np.array([-7.31808815, -8.31808815, -9.31808815]))
        # Test e2h
        np.testing.assert_array_almost_equal(
            np.log10(self.model.data['e2h']),
            np.array([-6.99171577, -7.99171577, -8.99171577]))

    def test_get_number_observations(self):
        '''
        Tests the count of the number of observations
        '''
        self.data = {'longitude': np.array([10., 20., 30.]),
                     'latitude': np.array([10., 20., 30.]),
                     'exx': np.array([1E-9, 20E-9, 25E-9]),
                     'eyy': np.array([1E-9, 20E-9, 25E-9]),
                     'exy': np.array([1E-9, 20E-9, 25E-9])}
        self.model = GeodeticStrain()
        # Test when no data is input (should equal 0)
        self.assertEqual(self.model.get_number_observations(), 0)
        # Test with data
        self.model.data = self.data
        self.assertEqual(self.model.get_number_observations(), 3)
