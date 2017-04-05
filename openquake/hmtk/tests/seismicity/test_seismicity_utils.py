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
# The software Hazard Modeller's Toolkit (hmtk) provided herein
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
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

#/usr/bin/env/python

'''Tests set of seismicity utility functions including:
i) decimal_year
ii) decimal_time
iii) haversine
iv) greg2julian
v) piecewise_linear_scalar
'''

import unittest
import numpy as np
from openquake.hmtk.seismicity import utils

class TestSeismicityUtilities(unittest.TestCase):
    '''Class for testing seismicity utilities'''
    def setUp(self):
        '''Sets up the test class'''
        self.year = []
        self.month = []
        self.day = []
        self.hour = []
        self.minute = []
        self.second = []
        self.longitude = []
        self.latitude = []

    def test_leap_year_check(self):
        '''Tests the leap year check'''
        # 1900 - Not leap year
        # 1995 - Not leap year
        # 2000 - Leap year
        # 2012 - Leap year
        test_years = np.array([1900, 1995, 2000, 2012])
        leap_values = utils.leap_check(test_years)
        self.assertFalse(leap_values[0])
        self.assertFalse(leap_values[1])
        self.assertTrue(leap_values[2])
        self.assertTrue(leap_values[3])

    def test_decimal_year(self):
        '''Tests the function utils.decimal_year'''
        self.year = np.array([1990., 1995., 2000.])
        self.month = np.array([1., 6., 12.])
        self.day = np.array([1., 30., 31.])
        self.assertTrue(np.allclose(
            utils.decimal_year(self.year, self.month, self.day),
            np.array([1990., 1995.49315068, 2000.99726027])))

    def test_decimal_time(self):
        '''Tests the function utils.decimal_time'''
        self.year = np.array([1990, 1995, 2000])
        self.month = np.array([1, 6, 12])
        self.day = np.array([1, 30, 31])
        self.hour = np.array([0, 12, 23])
        self.minute = np.array([0, 30, 59])
        self.second = np.array([0.0, 30.0, 59.0])
        self.assertTrue(np.allclose(
            utils.decimal_time(self.year, self.month, self.day, self.hour,
            self.minute, self.second),
            np.array([1990., 1995.49457858, 2000.99999997])))

    def test_decimal_time1(self):
        '''Tests the function utils.decimal_time'''
        self.year = np.array([1990])
        self.month = np.array([1])
        self.day = np.array([1])
        self.hour = np.array([0])
        self.minute = np.array([0])
        self.second = np.array([0.0, 30.0, 59.0])
        self.assertTrue(np.allclose(
            utils.decimal_time(self.year, self.month, self.day, self.hour,
            self.minute, self.second),
            np.array([1990.])))

    def test_decimal_time2(self):
        '''Tests the function utils.decimal_time'''
        self.year = np.array([1990])
        self.assertTrue(np.allclose(
            utils.decimal_time(self.year, [], [], [], [], []),
            np.array([1990.])))

    def test_haversine(self):
        '''Tests the function utils.haversine
        Distances tested against i) Matlab implementation of the haversine
                                    formula
                                ii) Matlab "distance" function (also based on
                                    the haversine formula (assumes
                                    Earth Radius = 6371.0 not 6371.227 as
                                    assumed here!)
        '''
        # Simple test
        self.longitude = np.arange(30., 40., 1.)
        self.latitude = np.arange(30., 40., 1.)
        distance = utils.haversine(self.longitude, self.latitude, 35.0, 35.0)
        expected_distance = np.array([[727.09474718],
                                      [580.39194024],
                                      [434.3102452],
                                      [288.87035021],
                                      [144.09319874],
                                      [0.],
                                      [143.38776088],
                                      [286.04831311],
                                      [427.95959077],
                                      [569.09922383]])
        self.assertTrue(np.allclose(distance, expected_distance))

        # 2-D test
        self.longitude = np.array([30., 35., 40.])
        self.latitude = np.array([30., 35., 40.])
        distance = utils.haversine(self.longitude, self.latitude,
                                    self.longitude, self.latitude)
        expected_distance = np.array([[ 0., 727.09474718, 1435.38402047],
                                      [727.09474718, 0., 709.44452948],
                                      [1435.38402047, 709.44452948, 0.]])
        self.assertTrue(np.allclose(distance, expected_distance))
        # Crossing International Dateline
        self.longitude = np.array([179.5, 180.0, -179.5])
        self.latitude = np.array([45., 45., 45.])
        distance = utils.haversine(self.longitude, self.latitude, 179.9, 45.)
        expected_distance = np.array([[31.45176332],
                                      [7.86294832],
                                      [47.1775851]])
        self.assertTrue(np.allclose(distance, expected_distance))

    def test_piecewise_linear_function(self):
        '''Test the piecewise linear calculator'''
        # Good parameter set - 2 segments
        params = [2.0, -1.0, 5.0, 0.0]
        values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
        expected = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 9.0, 8.0, 7.0, 6.0]
        for iloc, xval in enumerate(values):
            self.assertAlmostEqual(expected[iloc],
                                   utils.piecewise_linear_scalar(params, xval))
        # Odd-number of values in parameters - raise value error
        params = [2.0, -1.0, 5.0, 0.0, 3.4]
        with self.assertRaises(ValueError):
            utils.piecewise_linear_scalar(params, 1.0)
        # Single segment test
        params1seg = [2.0, 0.0]
        self.assertAlmostEqual(2.0,
                               utils.piecewise_linear_scalar(params1seg, 1.0))
        # 3- segment test
        params = np.array([2.0, -1.0, 3.0, 4.0, 8.0, 0.0])
        expected = [0.0, 2.0, 4.0, 6.0, 8.0, 7.0, 6.0, 5.0, 4.0, 7.0]
        for iloc, xval in enumerate(values):
            self.assertAlmostEqual(expected[iloc],
                                   utils.piecewise_linear_scalar(params, xval))


    def _tester_for_truncated_gaussian(self, data, uncertainties, low_limit,
                                       high_limit, number_samples=1000):
        """
        Tests that for a given data set and uncertainties that no values
        exceed the data limits
        """
        xlow = []
        xhigh = []
        for iloc in range(0, number_samples):
            xval = utils.sample_truncated_gaussian_vector(
                data,
                uncertainties,
                (low_limit, high_limit))
            xlow.append(np.min(xval))
            xhigh.append(np.max(xval))

        self.assertTrue(np.max(np.array(xhigh)) <= high_limit)
        self.assertTrue(np.min(np.array(xlow)) >= low_limit)


    def test_sample_truncated_gaussian_distribution_with_bounds(self):
        """
        Tests the function to sample a truncated Gaussian distribution
        """
        data = 10.0 * np.ones(100)
        uncertainties = np.random.uniform(0., 2., 100)
        # Add bounds between 5.0 and 15.0
        self._tester_for_truncated_gaussian(data, uncertainties, 5., 15.)

        # Test case with infinite bounds
        self._tester_for_truncated_gaussian(data,
                                            uncertainties,
                                            -np.inf,
                                            np.inf)




class TestBootstrapHistograms(unittest.TestCase):
    """
    Class to test bootstrapped histogram functions
    openquake.hmtk.seismicity.utils.bootstrap_histogram_1D
    openquake.hmtk.seismicity.utils.bootstrap_histogram_2D
    """
    def setUp(self):
        """
        """
        [x, y] = np.meshgrid(np.arange(5., 50., 5.),
                             np.arange(5.5, 9.0, 0.5))
        nx, ny = np.shape(x)
        x.reshape([nx * ny, 1])
        y.reshape([nx * ny, 1])
        self.x = x.flatten()
        self.y = y.flatten()
        self.x_sigma = None
        self.y_sigma = None

    def test_hmtk_histogram_1D_general(self):
        """
        Tests the 1D hmtk histogram with the general case (i.e. no edge-cases)
        Should be exactly equivalent to numpy's histogram function
        """
        xdata = np.random.uniform(0., 10., 100)
        xbins = np.arange(0., 11., 1.)
        np.testing.assert_array_almost_equal(
            utils.hmtk_histogram_1D(xdata, xbins),
            np.histogram(xdata, bins=xbins)[0].astype(float))
    
    def test_hmtk_histogram_1D_edgecase(self):
        """
        Tests the 1D hmtk histogram with edge cases
        Should be exactly equivalent to numpy's histogram function
        """
        xdata = np.array([3.1, 4.1, 4.56, 4.8, 5.2])
        xbins = np.arange(3.0, 5.35, 0.1)
        expected_counter = np.array([0., 1., 0., 0., 0., 0., 0., 0., 0., 0.,
                                      0., 1., 0., 0., 0., 1., 0., 0., 1., 0.,
                                      0., 0., 1.])
        np.testing.assert_array_almost_equal(
            utils.hmtk_histogram_1D(xdata, xbins),
            expected_counter)
    
    
    def test_hmtk_histogram_2D_general(self):
        """
        Tests the 2D hmtk histogram with the general case (i.e. no edge-cases)
        Should be exactly equivalent to numpy's histogram function
        """
        xdata = np.random.uniform(0., 10., 100)
        ydata = np.random.uniform(10., 20., 100)
        xbins = np.arange(0., 11., 1.)
        ybins = np.arange(10., 21., 1.)
        np.testing.assert_array_almost_equal(
            utils.hmtk_histogram_2D(xdata, ydata, (xbins, ybins)),
            np.histogram2d(xdata, ydata, bins=(xbins, ybins))[0].astype(float))

    def test_hmtk_histogram_2D_edgecase(self):
        """
        Tests the 2D hmtk histogram with edge cases
        Should be exactly equivalent to numpy's histogram function
        """
        xdata = np.array([3.1, 4.1, 4.56, 4.8, 5.2])
        ydata = np.array([1990., 1991.2, 1994., 1997., 1998.2])

        xbins = np.arange(3.0, 5.35, 0.1)
        ybins = np.arange(1990., 2001.5, 1.)
        
        expected_counter = np.array(
        #     90   91   92   93   94   95   96   97    98  99    00    
            [[0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #3.0-3.1 
             [1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #3.1-3.2 
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #3.2-3.3 
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #3.3-3.4
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #3.4-3.5
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #3.5-3.6
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #3.6-3.7
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #3.7-3.8
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #3.8-3.9
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #3.9-4.0
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #4.0-4.1
             [0.,  1.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #4.1-4.2
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #4.2-4.3
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #4.3-4.4
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #4.4-4.5
             [0.,  0.,  0.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,  0.], #4.5-4.6
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #4.6-4.7
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #4.7-4.8
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.,  0.], #4.8-4.9
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #4.9-5.0
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #5.0-5.1
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.], #5.1-5.2
             [0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  1.,  0.,  0.]])#5.2-5.3
        
        np.testing.assert_array_almost_equal(
            utils.hmtk_histogram_2D(xdata, ydata, bins=(xbins, ybins)),
            expected_counter)

    def test_1D_bootstrap_no_uncertainty(self):
        """
        Tests the bootstrap 1D histrogram function with no uncertainties
        """
        # Without normalisation
        x_range = np.arange(0., 60., 10.)
        expected_array = np.array([7., 14., 14., 14., 14.])
        np.testing.assert_array_almost_equal(
            expected_array,
            utils.bootstrap_histogram_1D(self.x, x_range))

        # Now with normalisaton
        expected_array = expected_array / np.sum(expected_array)
        np.testing.assert_array_almost_equal(expected_array,
            utils.bootstrap_histogram_1D(self.x, x_range, normalisation=True))


    def test_1D_bootstrap_with_uncertainty(self):
        """
        Tests the bootstrap 1D histrogram function with uncertainties
        """
        self.x_sigma = 1.0 * np.ones(len(self.x), dtype=float)
        expected_array = np.array([0.17, 0.22, 0.22, 0.22, 0.17])
        x_range = np.arange(0., 60., 10.)
        hist_values = utils.bootstrap_histogram_1D(
            self.x,
            x_range,
            uncertainties=self.x_sigma,
            number_bootstraps=1000,
            normalisation=True)
        np.testing.assert_array_almost_equal(np.round(hist_values, 2),
                                             expected_array)



    def test_2D_bootstrap_no_uncertainty(self):
        """
        Tests the bootstrap 1D histrogram function with no uncertainties
        """
        # Without normalisation
        x_range = np.arange(0., 60., 10.)
        y_range = np.arange(5., 10., 1.0)
        expected_array = np.array([[1., 2., 2., 2.],
                                   [2., 4., 4., 4.],
                                   [2., 4., 4., 4.],
                                   [2., 4., 4., 4.],
                                   [2., 4., 4., 4.]])
        np.testing.assert_array_almost_equal(expected_array,
            utils.bootstrap_histogram_2D(self.x, self.y, x_range, y_range))
        # With normalisation
        expected_array = expected_array / np.sum(expected_array)
        np.testing.assert_array_almost_equal(expected_array,
            utils.bootstrap_histogram_2D(self.x, self.y, x_range, y_range,
                                         normalisation=True))

    def test_2D_bootstrap_with_uncertainty(self):
        """
        Tests the bootstrap 1D histrogram function with uncertainties
        """
        # Without normalisation
        self.y_sigma = 0.1 * np.ones(len(self.y), dtype=float)
        x_range = np.arange(0., 60., 10.)
        y_range = np.arange(5., 10., 1.0)
        expected_array = np.array([[1.5, 2.0, 2.0, 1.5],
                                   [3.0, 4.0, 4.0, 3.0],
                                   [3.0, 4.0, 4.0, 3.0],
                                   [3.0, 4.0, 4.0, 3.0],
                                   [3.0, 4.0, 4.0, 3.0]])

        hist_values = utils.bootstrap_histogram_2D(
            self.x,
            self.y,
            x_range,
            y_range,
            normalisation=False,
            xsigma=self.x_sigma,
            ysigma=self.y_sigma,
            number_bootstraps=1000)

        array_diff = expected_array - np.round(hist_values, 1)
        print(expected_array, hist_values, array_diff)
        self.assertTrue(np.all(np.fabs(array_diff) < 0.2))
        # With normalisation
        expected_array = np.array([[0.04, 0.05, 0.05, 0.04],
                                  [0.05, 0.06, 0.06, 0.05],
                                  [0.05, 0.06, 0.06, 0.05],
                                  [0.05, 0.06, 0.06, 0.05],
                                  [0.04, 0.05, 0.05, 0.04]])

        hist_values = utils.bootstrap_histogram_2D(
            self.x,
            self.y,
            x_range,
            y_range,
            normalisation=True,
            xsigma=self.x_sigma,
            ysigma=self.y_sigma,
            number_bootstraps=1000)
        array_diff = expected_array - hist_values
        self.assertTrue(np.all(np.fabs(array_diff) < 0.02))

class Testlonlat2laea(unittest.TestCase):
    """
    Tests the converter from longitude and latitude to lambert azimuthal
    equal area coordinates
    """
    def test_conversion(self):
        """
        Tests lonlat to lambert equal area
        Data from pyproj conversion taken from reference test case
        """
        expected_x, expected_y = (-286700.13595616777, -325847.4698447622)
        calc_x, calc_y = utils.lonlat_to_laea(5.0, 50.0, 9.0, 53.0)
        self.assertAlmostEqual(calc_x, expected_x / 1000.0)
        self.assertAlmostEqual(calc_y, expected_y / 1000.0)

