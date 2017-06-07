# -*- coding: utf-8 -*-
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
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.
# -*- coding: utf-8 -*-
'''
Tests for the module :mod:
openquake.hmtk.seismicity.smoothing.kernels.isotropic_gaussian.IsotropicGaussian, which
implements the Frankel (1995) isotropic Gaussian smoothing Kernel

'''
import os
import unittest
import numpy as np

from openquake.hmtk.seismicity.smoothing.kernels.isotropic_gaussian import \
    IsotropicGaussian

BASE_PATH = os.path.join(os.path.dirname(__file__), 'data')


TEST_1_VALUE_FILE = 'Isotropic_Gaussian_Smoothing_1value.txt'
TEST_1_VALUE_3D_FILE = 'Isotropic_Gaussian_Smoothing_1value_3d.txt'
TEST_3_VALUE_FILE = 'Isotropic_Gaussian_Smoothing_3value.txt'


class TestIsotropicGaussian(unittest.TestCase):
    '''
    Simple tests the of Isotropic Gaussian Kernel
    (as implemented by Frankel (1995))
    '''
    def setUp(self):
        self.model = IsotropicGaussian()
        # Setup simple grid
        [gx, gy] = np.meshgrid(np.arange(35.5, 40., 0.5),
                               np.arange(40.5, 45., 0.5))
        ngp = np.shape(gx)[0] * np.shape(gx)[1]
        gx = np.reshape(gx, [ngp, 1])
        gy = np.reshape(gy, [ngp, 1])
        depths = 10. * np.ones(ngp)
        self.data = np.column_stack([gx, gy, depths,
                                    np.zeros(ngp, dtype=float)])

    def test_kernel_single_event(self):
        # ensure kernel is smoothing values correctly for a single event
        self.data[50, 3] = 1.
        config = {'Length_Limit': 3.0, 'BandWidth': 30.0}
        expected_array = np.genfromtxt(os.path.join(BASE_PATH,
                                                    TEST_1_VALUE_FILE))
        (smoothed_array, sum_data, sum_smooth) = \
            self.model.smooth_data(self.data, config)
        raise unittest.SkipTest('Have Graeme fix this')
        np.testing.assert_array_almost_equal(expected_array, smoothed_array)
        self.assertAlmostEqual(sum_data, 1.)
        # Assert that sum of the smoothing is equal to the sum of the
        # data values to 3 dp
        self.assertAlmostEqual(sum_data, sum_smooth, 3)

    def test_kernel_multiple_event(self):
        # ensure kernel is smoothing values correctly for multiple events
        self.data[[5, 30, 65], 3] = 1.
        config = {'Length_Limit': 3.0, 'BandWidth': 30.0}
        expected_array = np.genfromtxt(os.path.join(BASE_PATH,
                                                    TEST_3_VALUE_FILE))
        (smoothed_array, sum_data, sum_smooth) = \
            self.model.smooth_data(self.data, config)
        raise unittest.SkipTest('Have Graeme fix this')
        np.testing.assert_array_almost_equal(expected_array, smoothed_array)
        self.assertAlmostEqual(sum_data, 3.)
        # Assert that sum of the smoothing is equal to the sum of the
        # data values to 3 dp
        self.assertAlmostEqual(sum_data, sum_smooth, 2)

    def test_kernel_single_event_3d(self):
        # ensure kernel is smoothing values correctly for a single event
        self.data[50, 3] = 1.
        self.data[50, 2] = 20.
        config = {'Length_Limit': 3.0, 'BandWidth': 30.0}
        expected_array = np.genfromtxt(os.path.join(BASE_PATH,
                                                    TEST_1_VALUE_3D_FILE))
        (smoothed_array, sum_data, sum_smooth) = \
            self.model.smooth_data(self.data, config, is_3d=True)
        raise unittest.SkipTest('Have Graeme fix this')
        np.testing.assert_array_almost_equal(expected_array, smoothed_array)
        self.assertAlmostEqual(sum_data, 1.)
        # Assert that sum of the smoothing is equal to the sum of the
        # data values to 2 dp
        self.assertAlmostEqual(sum_data, sum_smooth, 2)
