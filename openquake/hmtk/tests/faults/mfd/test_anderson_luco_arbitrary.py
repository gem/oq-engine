# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2018 GEM Foundation, G. Weatherill, M. Pagani,
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
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
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
Module to test :openquake.hmtk.faults.mfd.anderson_luco_arbitrary.AndersonLucoArbitrary
class
'''

import os
import unittest
import numpy as np
from math import log
from openquake.hazardlib.scalerel import WC1994
from openquake.hmtk.faults.mfd.anderson_luco_arbitrary import (Type1RecurrenceModel,
                                                               Type2RecurrenceModel, Type3RecurrenceModel, AndersonLucoArbitrary)

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
AL83_FIG2_MODEL = np.genfromtxt(os.path.join(BASE_DATA_PATH,
                                             'anderson_luco_arbitrary_results.dat'))
AL83_INC_DATA = np.genfromtxt(os.path.join(BASE_DATA_PATH,
                                           'anderson_luco_arbitrary_incremental.dat'))


class TestType1Recurrence(unittest.TestCase):
    '''
    Tests the Recurrence function of the Anderson & Luco (1983) arbitrary
    type 1 model
    '''

    def setUp(self):
        '''

        '''
        self.magnitudes = AL83_FIG2_MODEL[:, 0]
        self.model = Type1RecurrenceModel()
        self.mmax = 8.0
        self.bbar = 1.0 * log(10.)
        self.dbar = 1.5 * log(10.)

    def test_recurrence_model_type1(self):
        '''
        Tests the recurrence function
        In all cases if bbar > dbar (1.5) then models will fail!
        '''
        # Tests 1 - master case - reproduces the N1 line of Figure 2 in
        # Anderson & Luco (1983)

        # Requires setting the moment slip to 8.1E+25 dyne-cm
        moment_slip = 8.1E25
        expected_results = AL83_FIG2_MODEL[:, 1]
        for iloc, mag in enumerate(self.magnitudes):
            self.assertAlmostEqual(expected_results[iloc],
                                   self.model.cumulative_value(moment_slip, self.mmax, mag,
                                                               self.bbar, self.dbar), 7)


class TestType2Recurrence(unittest.TestCase):
    '''
    Tests the Recurrence function of the Anderson & Luco (1983) arbitrary
    type 2 model
    '''

    def setUp(self):
        '''

        '''
        self.magnitudes = AL83_FIG2_MODEL[:, 0]
        self.model = Type2RecurrenceModel()
        self.mmax = 8.0
        self.bbar = 1.0 * log(10.)
        self.dbar = 1.5 * log(10.)

    def test_recurrence_model_type1(self):
        '''
        Tests the recurrence function
        In all cases if bbar > dbar (1.5) then models will fail!
        '''
        # Tests 1 - master case - reproduces the N2 line of Figure 2 in
        # Anderson & Luco (1983)

        # Requires setting the moment slip to 8.1E+25 dyne-cm
        moment_slip = 8.1E25
        expected_results = AL83_FIG2_MODEL[:, 2]
        for iloc, mag in enumerate(self.magnitudes):
            self.assertAlmostEqual(expected_results[iloc],
                                   self.model.cumulative_value(moment_slip, self.mmax, mag,
                                                               self.bbar, self.dbar), 7)


class TestType3Recurrence(unittest.TestCase):
    '''
    Tests the Recurrence function of the Anderson & Luco (1983) arbitrary
    type 3 model
    '''

    def setUp(self):
        '''

        '''
        self.magnitudes = AL83_FIG2_MODEL[:, 0]
        self.model = Type3RecurrenceModel()
        self.mmax = 8.0
        self.bbar = 1.0 * log(10.)
        self.dbar = 1.5 * log(10.)

    def test_recurrence_model_type1(self):
        '''
        Tests the recurrence function
        In all cases if bbar > dbar (1.5) then models will fail!
        '''
        # Tests 1 - master case - reproduces the N1 line of Figure 2 in
        # Anderson & Luco (1983)

        # Requires setting the moment slip to 8.1E+25 dyne-cm
        moment_slip = 8.1E25
        expected_results = AL83_FIG2_MODEL[:, 3]
        for iloc, mag in enumerate(self.magnitudes):
            self.assertAlmostEqual(expected_results[iloc],
                                   self.model.cumulative_value(moment_slip, self.mmax, mag,
                                                               self.bbar, self.dbar), 7)


class TestAndersonLucoArbitrary(unittest.TestCase):
    '''
    Tests the Anderson & Luco Arbitrary models
    :class openquake.hmtk.faults.mfd.anderson_luco_arbitrary.AndersonLucoArbitrary
    '''

    def setUp(self):
        self.model = AndersonLucoArbitrary()
        self.config = {'Model_Type': 'First',
                       'MFD_spacing': 0.1,
                       'Model_Weight': 1.0,
                       'Minimum_Magnitude': 5.0,
                       'Maximum_Magnitude': None,
                       'b_value': [1.0, 0.1]}

        self.msr = WC1994()

    def test_case_setup(self):
        '''
        Tests the basic setup
        '''
        expected_dict = {'b_value': 1.0,
                         'b_value_sigma': 0.1,
                         'bin_width': 0.1,
                         'mfd_model': 'Anderson & Luco (Arbitrary) First',
                         'mfd_type': 'First',
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

        self.model = AndersonLucoArbitrary()
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 8500.)
        self.assertAlmostEqual(self.model.mmax, 8.0)
        self.assertAlmostEqual(self.model.mmax_sigma, 0.2)

        # Case 2: Mmax and uncertainty not specified in config
        self.config['Maximum_Magnitude'] = None
        self.config['Maximum_Magnitude_Uncertainty'] = None

        self.model = AndersonLucoArbitrary()
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 8500.)
        self.assertAlmostEqual(self.model.mmax, 7.9880073)
        self.assertAlmostEqual(self.model.mmax_sigma, 0.23)

    def test_get_mfd(self):
        '''
        Tests the function to get magnitude frequency distribution
        '''
        self.msr = WC1994()

        # Test 1: For a fault with 20 mm/yr slip, and an area of 30000 km ** 2
        self.msr = WC1994()
        # Testing all three calculators!
        for iloc, model_type in enumerate(['First', 'Second', 'Third']):
            self.model = AndersonLucoArbitrary()

            self.config = {'Model_Type': model_type,
                           'MFD_spacing': 0.1,
                           'Model_Weight': 1.0,
                           'Minimum_Magnitude': 5.0,
                           'Maximum_Magnitude': None,
                           'b_value': [1.0, 0.1]}
            self.model.setUp(self.config)
            self.model.get_mmax(self.config, self.msr, 0., 30000.)
            test_output = self.model.get_mfd(20., 30000.)
            print(AL83_INC_DATA[:, iloc], test_output[2])
            np.testing.assert_array_almost_equal(AL83_INC_DATA[:, iloc],
                                                 test_output[2])

            # Test case when b-value greater than d-value (raises warning!)
            self.model = AndersonLucoArbitrary()

            self.config = {'Model_Type': model_type,
                           'MFD_spacing': 0.1,
                           'Model_Weight': 1.0,
                           'Minimum_Magnitude': 5.0,
                           'Maximum_Magnitude': None,
                           'b_value': [2.0, 0.1]}
            self.model.setUp(self.config)
            self.model.get_mmax(self.config, self.msr, 0., 30000.)
            self.model.get_mfd(20., 30000.)
            self.assertTrue(np.all(np.isnan(self.model.occurrence_rate)))
