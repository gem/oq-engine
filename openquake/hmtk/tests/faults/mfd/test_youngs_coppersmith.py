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
Module to test :class:
:openquake.hmtk.faults.mfd.youngs_coppersmith.YoungsCoppersmithExponential
and :class: openquake.hmtk.faults.mfd.youngs_coppersmith.YoungsCoppersmithExponential
'''

import os
import unittest
import numpy as np
from math import log
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.mfd.evenly_discretized import EvenlyDiscretizedMFD
from openquake.hmtk.faults.mfd.base import _scale_moment
from openquake.hmtk.faults.mfd.youngs_coppersmith import (YoungsCoppersmithExponential,
                                                YoungsCoppersmithCharacteristic)

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
YC_EXP_DATA = np.genfromtxt(os.path.join(BASE_DATA_PATH,
        'yc1985_exponential_BungumFig1.dat'))

class TestYoungsCoppersmithExponential(unittest.TestCase):
    '''
    Tests the :class: YoungsCoppersmithExponential
    '''
    def setUp(self):
        '''
        '''
        self.model = YoungsCoppersmithExponential()
        self.msr = WC1994()
        self.config = {'MFD_spacing': 0.1,
                       'Maximum_Magnitude': 8.0,
                       'Maximum_Magnitude_Uncertainty': None,
                       'Minimum_Magnitude': 5.0,
                       'Model_Weight': 1.0,
                       'b_value': [1.0, 0.1]}

    def test_class_setup(self):
        '''
        Tests the basic setup of the class
        '''
        expected_dict = {'b_value': 1.0,
                         'b_value_sigma': 0.1,
                         'bin_width': 0.1,
                         'mfd_model': 'Youngs & Coppersmith Exponential',
                         'mfd_weight': 1.0,
                         'mmax': None,
                         'mmax_sigma': None,
                         'mmin': 5.0,
                         'occurrence_rate': None}

        self.model.setUp(self.config)
        self.assertDictEqual(expected_dict, self.model.__dict__)

    def test_get_mmax(self):
        '''
        Tests the function to get Mmax
        Values come from WC1994 (tested in openquake.hazardlib) - only
        functionality is tested for here!
        '''
        # Case 1 MMmax and uncertainty specified in config
        self.config['Maximum_Magnitude'] = 8.0
        self.config['Maximum_Magnitude_Uncertainty'] = 0.2

        self.model = YoungsCoppersmithExponential()
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 8500.)
        self.assertAlmostEqual(self.model.mmax, 8.0)
        self.assertAlmostEqual(self.model.mmax_sigma, 0.2)

        # Case 2: Mmax and uncertainty not specified in config
        self.config['Maximum_Magnitude'] = None
        self.config['Maximum_Magnitude_Uncertainty'] = None

        self.model = YoungsCoppersmithExponential()
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 8500.)
        self.assertAlmostEqual(self.model.mmax, 7.9880073)
        self.assertAlmostEqual(self.model.mmax_sigma, 0.23)

    def test_cumulative_value(self):
        '''
        Tests the calculation of the cumulative rate M > Mref
        Data and tests taken from Bungum (2007). Current parameters should
        reproduce Model 4 line in Figure 1 of Bungum (2007)
        '''
        self.model = YoungsCoppersmithExponential()
        self.config = {'MFD_spacing': 0.1,
                       'Maximum_Magnitude': 8.0,
                       'Maximum_Magnitude_Uncertainty': None,
                       'Minimum_Magnitude': 5.0,
                       'Model_Weight': 1.0,
                       'b_value': [1.0, 0.1]}

        # Test case 1 - Fault of 120 km length and 60 km width (7200 km ** 2 area)
        # b-value 1, slip = 1 mm/yr
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 7200.)
        moment_rate = (30. * 1E9) * (7200. * 1E6) * (1.0 / 1000.)
        momax = _scale_moment(self.model.mmax, in_nm=True)
        beta = log(10.)
        expected_result = YC_EXP_DATA[:, 1]
        mags = np.arange(5.0, 8.1, 0.1)
        for iloc, mag in enumerate(mags):
            self.assertAlmostEqual(
                expected_result[iloc],
                self.model.cumulative_value(mag, moment_rate, beta, momax))

    def test_get_mfd(self):
        '''
        Tests the main function to get the magnitude frequency distribution
        '''
        self.model = YoungsCoppersmithExponential()
        self.config = {'MFD_spacing': 0.1,
                       'Maximum_Magnitude': 8.0,
                       'Maximum_Magnitude_Uncertainty': None,
                       'Minimum_Magnitude': 5.0,
                       'Model_Weight': 1.0,
                       'b_value': [1.0, 0.1]}
        self.model.setUp(self.config)
        # Same fault case as for test_cumulative_value - now comparing incremenetal
        # rates
        self.model.get_mmax(self.config, self.msr, 0., 7200.)
        output1 = self.model.get_mfd(1.0, 7200.)
        np.testing.assert_array_almost_equal(YC_EXP_DATA[:, 2], output1[2])

        # Test case for when b > 1.5 - should produce array of NaN
        self.model = YoungsCoppersmithExponential()
        self.config['b_value'] = [1.6, 0.1]
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 7200.)
        _, _, _ = self.model.get_mfd(1.0, 7200.)
        self.assertTrue(np.all(np.isnan(self.model.occurrence_rate)))

    def test_return_oq_mfd(self):
        """
        Tests the function to return the mfd as an instance of the openquake
        EvenlyDiscretizedMFD class
        """
        self.model = YoungsCoppersmithExponential()
        self.config = {'MFD_spacing': 0.1,
                       'Maximum_Magnitude': 8.0,
                       'Maximum_Magnitude_Uncertainty': None,
                       'Minimum_Magnitude': 5.0,
                       'Model_Weight': 1.0,
                       'b_value': [1.0, 0.1]}
        self.model.setUp(self.config)
        # Same fault case as for test_cumulative_value - now comparing incremenetal
        # rates
        self.model.get_mmax(self.config, self.msr, 0., 7200.)
        _ = self.model.get_mfd(1.0, 7200.)
        oq_mfd = self.model.to_evenly_discretized_mfd()
        self.assertTrue(isinstance(oq_mfd, EvenlyDiscretizedMFD))
        self.assertAlmostEqual(oq_mfd.min_mag, 5.05)
        self.assertAlmostEqual(oq_mfd.bin_width, 0.1)
        np.testing.assert_array_almost_equal(YC_EXP_DATA[:, 2],
                                             np.array(oq_mfd.occurrence_rates))




class TestYoungsCoppersmithCharacteristic(unittest.TestCase):
    '''
    Tests the
    :class: openquake.hmtk.faults.mfd.youngs_coppersmith.YoungsCoppersmithCharacteristic
    '''
    def setUp(self):
        '''
        '''
        self.model = YoungsCoppersmithCharacteristic()
        self.msr = WC1994()
        self.config = {'MFD_spacing': 0.1,
                       'Maximum_Magnitude': 8.0,
                       'Maximum_Magnitude_Uncertainty': None,
                       'Minimum_Magnitude': 5.0,
                       'Model_Weight': 1.0,
                       'b_value': [1.0, 0.1],
                       'delta_m': None}

    def test_class_setup(self):
        '''
        Tests the basic setup of the class
        '''
        # Test case 1 - delta not set
        expected_dict = {
            'b_value': 1.0,
            'b_value_sigma': 0.1,
            'bin_width': 0.1,
            'mfd_type': 'Youngs & Coppersmith (1985) Characteristic',
            'mfd_weight': 1.0,
            'mmax': None,
            'mmax_sigma': None,
            'mmin': 5.0,
            'occurrence_rate': None,
            'model': None}

        self.model.setUp(self.config)
        self.assertDictEqual(expected_dict, self.model.__dict__)


    def test_get_mmax(self):
        '''
        Tests the function to get Mmax
        Values come from WC1994 (tested in openquake.hazardlib) - only
        functionality is tested for here!
        '''
        # Case 1 MMmax and uncertainty specified in config
        self.config['Maximum_Magnitude'] = 8.0
        self.config['Maximum_Magnitude_Uncertainty'] = 0.2

        self.model = YoungsCoppersmithCharacteristic()
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 8500.)
        self.assertAlmostEqual(self.model.mmax, 8.0)
        self.assertAlmostEqual(self.model.mmax_sigma, 0.2)

        # Case 2: Mmax and uncertainty not specified in config
        self.config['Maximum_Magnitude'] = None
        self.config['Maximum_Magnitude_Uncertainty'] = None

        self.model = YoungsCoppersmithCharacteristic()
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 8500.)
        self.assertAlmostEqual(self.model.mmax, 7.9880073)
        self.assertAlmostEqual(self.model.mmax_sigma, 0.23)

    def test_get_mfd(self):
        '''
        Tests the function to get the magnitude frequency distribution
        This function essentially wraps the
        YoungsCoppersmith1985MFD.from_total_moment rate function, which is
        tested in the openquake.hazardlib.
        '''
        # Simple test using previously defined fault
        # Area = Length x Width (120 km x 60 km)
        # Slip = 1.0 mm/yr
        expected_rates = np.array(
            [2.14512891e-03, 1.70393646e-03, 1.35348484e-03,
             1.07511122e-03, 8.53991200e-04, 6.78349322e-04, 
             5.38832020e-04, 4.28009487e-04, 3.39980020e-04,
             2.70055729e-04, 2.14512891e-04, 1.70393646e-04,
             1.35348484e-04, 1.07511122e-04, 8.53991200e-05, 
             6.78349322e-05, 5.38832020e-05, 4.28009487e-05, 
             3.39980020e-05, 2.70055729e-05, 2.14512891e-05,
             1.70393646e-05, 1.35348484e-05, 1.07511122e-05,
             8.53991200e-06, 7.59441645e-05, 7.59441645e-05, 
             7.59441645e-05, 7.59441645e-05, 7.59441645e-05])
        self.model = YoungsCoppersmithCharacteristic()
        self.config['Maximum_Magnitude'] = 8.0
        self.config['Maximum_Magnitude_Uncertainty'] = None
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 7200.)
        output1 = self.model.get_mfd(1.0, 7200.)
        np.testing.assert_array_almost_equal(expected_rates, output1[2])
        self.assertAlmostEqual(output1[0], 5.05)
