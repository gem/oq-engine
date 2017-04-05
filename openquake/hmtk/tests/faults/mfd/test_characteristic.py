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
Module to test :openquake.hmtk.faults.mfd.characterisric.Characteristic class
'''

import unittest
import numpy as np
from openquake.hazardlib.scalerel import WC1994
from openquake.hmtk.faults.mfd.characteristic import Characteristic

aaae = np.testing.assert_array_almost_equal


class TestSimpleCharacteristic(unittest.TestCase):
    '''
    Implements the basic set of tests for the simple estimator of the
    characteristic earthquake for a fault
    :class openquake.hmtk.faults.mfd.characteristic.Characteristic
    '''
    def setUp(self):
        '''
        '''
        self.model = Characteristic()
        self.config = {'MFD_spacing': 0.1,
                       'Model_Weight': 1.0,
                       'Maximum_Magnitude': None,
                       'Maximum_Uncertainty': None,
                       'Lower_Bound': -2.,
                       'Upper_Bound': 2.,
                       'Sigma': None}
        self.msr = WC1994()

    def test_model_setup(self):
        '''
        Simple test to ensure model sets up correctly
        '''
        self.model.setUp(self.config)
        expected_dict = {'bin_width': 0.1,
                         'lower_bound': -2.0,
                         'mfd_model': 'Characteristic',
                         'mfd_weight': 1.0,
                         'mmax': None,
                         'mmax_sigma': None,
                         'mmin': None,
                         'occurrence_rate': None,
                         'sigma': None,
                         'upper_bound': 2.0}
        self.assertDictEqual(self.model.__dict__, expected_dict)


    def test_get_mmax(self):
        '''
        Tests the function to get Mmax
        Values come from WC1994 (tested in openquake.hazardlib) - only
        functionality is tested for here!
        '''
        # Case 1 MMmax and uncertainty specified in config
        self.config['Maximum_Magnitude'] = 8.0
        self.config['Maximum_Magnitude_Uncertainty'] = 0.2

        self.model = Characteristic()
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 8500.)
        self.assertAlmostEqual(self.model.mmax, 8.0)
        self.assertAlmostEqual(self.model.mmax_sigma, 0.2)

        # Case 2: Mmax and uncertainty not specified in config
        self.config['Maximum_Magnitude'] = None
        self.config['Maximum_Magnitude_Uncertainty'] = None

        self.model = Characteristic()
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 8500.)
        self.assertAlmostEqual(self.model.mmax, 7.9880073)
        self.assertAlmostEqual(self.model.mmax_sigma, 0.23)

    def test_get_mfd(self):
        '''
        Tests the calculation of activity rates for the simple
        characteristic earthquake distribution.

        '''

        # Test case 1: Ordinatry fault with Area 8500 km ** 2 (Mmax ~ 8.0),
        # and a slip rate of 5 mm/yr. Double truncated Gaussian between [-2, 2]
        # standard deviations with sigma = 0.12
        self.config = {'MFD_spacing': 0.1,
                       'Model_Weight': 1.0,
                       'Maximum_Magnitude': None,
                       'Maximum_Uncertainty': None,
                       'Lower_Bound': -2.,
                       'Upper_Bound': 2.,
                       'Sigma': 0.12}
        self.model = Characteristic()
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 8500.)
        _, _, _ = self.model.get_mfd(5.0, 8500.)
        aaae(self.model.occurrence_rate,
             np.array([4.20932867e-05, 2.10890168e-04, 3.80422666e-04,
                       3.56294331e-04, 1.73223702e-04, 2.14781079e-05]))
        expected_rate = np.sum(self.model.occurrence_rate)
        # Test case 2: Same fault with no standard deviation
        self.config['Sigma'] = None
        self.model.setUp(self.config)
        self.model.get_mmax(self.config, self.msr, 0., 8500.)
        _, _, _ = self.model.get_mfd(5.0, 8500.)
        aaae(0.0011844, self.model.occurrence_rate)
        # As a final check - ensure that the sum of the activity rates from the
        # truncated Gaussian model is equal to the rate from the model with no
        # variance
        aaae(expected_rate, self.model.occurrence_rate, 3)
