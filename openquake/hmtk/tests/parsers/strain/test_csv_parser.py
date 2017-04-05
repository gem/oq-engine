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
Test suite for openquake.hmtk.parsers.strain.strain_csv_parser - the reader and writer of
the strain model in csv format
'''
import os
import csv
import unittest
import numpy as np
from collections import OrderedDict
from openquake.hmtk.strain.geodetic_strain import GeodeticStrain
from openquake.hmtk.parsers.strain.strain_csv_parser import (ReadStrainCsv,
                                                   WriteStrainCsv)


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'strain_files')
IN_FILE = os.path.join(BASE_DATA_PATH, 'simple_strain_values.csv')


class TestStrainCsvReader(unittest.TestCase):
    '''
    Test suite for the strain csv reader
    '''
    def setUp(self):
        '''
        '''
        self.model = None
        self.filename = None

    def test_basic_instantiation(self):
        '''
        Tests the instantiation of the reader class (trivial)
        '''
        self.model = ReadStrainCsv('some_random_file')
        self.assertEqual(self.model.filename, 'some_random_file')

    def test_check_invalid_longitude(self):
        '''
        Tests to ensure longitudes greater than 180.0 are returned in the
        range (-180. to 180.)
        '''
        self.model = ReadStrainCsv('some_random_file')
        self.model.strain.data = {'longitude': np.array([30., 180., 270.])}
        self.model._check_invalid_longitudes()
        np.testing.assert_array_almost_equal(
            self.model.strain.data['longitude'],
            np.array([30., 180., -90.]))

    def test_read_file(self):
        '''
        Tests the reader on a simple strain file
        '''
        self.model = ReadStrainCsv(IN_FILE)
        strain = self.model.read_data()
        # First test - check longitude and latitude
        exp_longitude = np.array(
            [-74.2, -74.1, -74., -73.9, -72.9, -72.8, 46.2, 46.3, 46.4, 176.9,
             177., 177.1, -74.1,  -74., -73.9, -73.8, -112.2, -112.1, -112.,
             -111.9, -111.8])
        exp_latitude = np.array(
            [-55.7, -55.7, -55.7, -55.7, -55.7, -55.7, -38.2, -38.2, -38.2,
             -38.2, -38.2, -38.2, -38.1, -38.1, -38.1,
             -38.1, -24.8, -24.8, -24.8, -24.8, -24.8])
        region = np.array([b'IPL', b'IPL', b'IPL', b'IPL', b'R', b'R', b'O',
                           b'O', b'O', b'C', b'C', b'C', b'S', b'S', b'S',
                           b'S', b'R', b'R', b'R', b'R', b'R'])
        str_2nd_inv = np.array(
            [0., 0.,   0., 0.0, 6.97660913e-07,
             4.64676812e-07, 3.51209339e-08, 3.59874978e-08, 3.69339952e-08,
             9.96827969e-08, 8.17414827e-08, 5.58344876e-08, 3.42756721e-07,
             3.42576969e-07, 3.55996685e-07, 3.35017194e-07, 1.11642096e-06,
             2.39838312e-06, 2.73038946e-06, 2.46489650e-06, 1.14653444e-06])

        np.testing.assert_array_almost_equal(exp_longitude,
                                             strain.data['longitude'])

        np.testing.assert_array_almost_equal(exp_latitude,
                                             strain.data['latitude'])

        np.testing.assert_array_equal(region, strain.data['region'])

        # Take from 4th value to avoid log10(0.) for IPL regions
        np.testing.assert_array_almost_equal(
            np.log10(str_2nd_inv[4:]),
            np.log10(strain.data['2nd_inv'][4:]))

        self.assertListEqual(
            strain.data_variables,
            ['longitude', 'latitude', 'exx', 'eyy', 'exy', '2nd_inv',
             'dilatation', 'err', 'e1h', 'e2h'])


class TestStrainCsvWriter(unittest.TestCase):
    '''
    Class to test strain model writer to csv
    '''
    def setUp(self):
        '''
        '''
        self.writer = None
        self.model = GeodeticStrain()
        self.model.data = OrderedDict([
            ('longitude', np.array([30., 30., 30.])),
            ('latitude', np.array([30., 30., 30.])),
            ('exx', np.array([1., 2., 3.])),
            ('eyy', np.array([1., 2., 3.])),
            ('exy', np.array([1., 2., 3.]))])
        self.filename = None

    def test_instantiation(self):
        '''
        Test basic instantiation with a filename
        '''
        self.writer = WriteStrainCsv('some_random_file')
        self.assertEqual(self.writer.filename, 'some_random_file')

    def test_slice_rates_to_data_as_array(self):
        '''
        Test the function to slice some magnitude rate and add to dictionary
        '''
        self.writer = WriteStrainCsv('some_random_file')
        self.model.seismicity_rate = np.array([[1., 2.],
                                                [1., 2.],
                                                [1., 2.]])
        self.model.target_magnitudes = np.array([5.5, 6.6])
        self.model, output_variables = self.writer.slice_rates_to_data(
            self.model)

        self.assertListEqual(output_variables,
            ['longitude', 'latitude', 'exx', 'eyy', 'exy', '5.500', '6.600'])
        np.testing.assert_array_almost_equal(self.model.data['5.500'],
                                             np.array([1., 1., 1.]))

        np.testing.assert_array_almost_equal(self.model.data['6.600'],
                                             np.array([2., 2., 2.]))


    def test_write_to_file(self):
        '''
        Tests the writer to a file
        '''
        self.writer = WriteStrainCsv('a_test_file.csv')
        self.model.seismicity_rate = np.array([[1., 2.],
                                                [1., 2.],
                                                [1., 2.]])
        self.model.target_magnitudes = np.array([5.5, 6.6])


        expected = [['longitude', 'latitude', 'exx', 'eyy', 'exy', '5.500',
                     '6.600'], ['30.0', '30.0', '1.0', '1.0', '1.0', '1.0',
                     '2.0'], ['30.0', '30.0', '2.0', '2.0', '2.0', '1.0',
                     '2.0'], ['30.0', '30.0', '3.0', '3.0', '3.0', '1.0',
                     '2.0']]
        self.writer.write_file(self.model)
        f = open('a_test_file.csv')
        data = csv.reader(f)
        for iloc, row in enumerate(data):
            self.assertListEqual(expected[iloc], row)

        os.system('rm a_test_file.csv')
