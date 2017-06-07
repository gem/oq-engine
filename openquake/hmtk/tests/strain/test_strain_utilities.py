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
Test suite for openquake.hmtk.strain.strain_utils a set of utility functions for the
strain module
'''
import os
import unittest
import numpy as np
from math import log, log10
from openquake.hmtk.strain.strain_utils import (moment_function,
                                      moment_magnitude_function,
                                      calculate_taper_function,
                                      tapered_gutenberg_richter_cdf,
                                      tapered_gutenberg_richter_pdf)


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'strain_data')
TAPER_FUNCTION_DATA = np.genfromtxt(
    os.path.join(BASE_DATA_PATH, 'taper_function_log_data.txt'),
    delimiter=',')



class TestStrainUtils(unittest.TestCase):
    '''
    Class to test funtions in the strain utilities module
    '''
    def setUp(self):
        '''
        '''
        self.beta = log(10.)

    def test_moment_function(self):
        '''
        Tests the simple function to implement the Hanks & Kanamori (1979)
        formula for an input magnitude
        '''
        expected_value = 18.05
        self.assertAlmostEqual(expected_value,
                               log10(moment_function(6.0)))

    def test_moment_magnitude_function(self):
        '''
        Tests the Hanks & Kanamori (1979) formula  for an input moment
        '''
        self.assertAlmostEqual(6.0,
                               moment_magnitude_function(moment_function(6.0)))

    def test_calculate_taper_function(self):
        '''
        Tests the function to calculate the taper part of the Tapered
        Gutenberg & Richter model with exhaustive data set
        '''

        obs_mo = moment_function(np.arange(5.0, 9.5, 1.0))
        sel_mo = moment_function(np.arange(5.0, 9.5, 1.0))
        obs_data = np.zeros([len(obs_mo), len(sel_mo)], dtype=float)
        corner_mo = moment_function(8.5)
        for iloc, obs in enumerate(obs_mo):
            for jloc, sel in enumerate(sel_mo):
                obs_data[iloc, jloc] = calculate_taper_function(obs,
                                                                sel,
                                                                corner_mo,
                                                                self.beta)
        np.testing.assert_array_almost_equal(TAPER_FUNCTION_DATA,
                                             np.log10(obs_data))

    def test_calculate_taper_function_zero_case(self):
        '''
        Test case when g_function is 0.0.
        g_function is 0 when (obs - sel) < -100.0 * corner_mo
        This scenario seems to occur when the selected moment is
        significantly greater than the corner magnitude
        '''
        self.assertAlmostEqual(0.0, calculate_taper_function(
            moment_function(5.0),
            moment_function(8.0),
            moment_function(6.0),
            self.beta))
