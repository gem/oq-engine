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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

#!/usr/bin/env python
'''Tests for revised Stepp (1971) completeness analysis procedure'''
import os
import unittest
import numpy as np
from math import fabs
from openquake.hmtk.seismicity.utils import piecewise_linear_scalar
from openquake.hmtk.seismicity.completeness.comp_stepp_1971 import (
    get_bilinear_residuals_stepp, Stepp1971)
from openquake.hmtk.parsers.catalogue import CsvCatalogueParser


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

INPUT_FILE_1 = os.path.join(BASE_DATA_PATH, 'completeness_test_cat.csv')

#INPUT_FILE_1 = 'tests/seismicity/completeness/data/completeness_test_cat.csv'

class TestBilinearResiduals(unittest.TestCase):
    '''
    Class to test the function to calculate bilinear residuals
    '''
    def setUp(self):
        self.xdata = np.arange(0., 11., 1.)
        self.params = [2.0, -1.0, 5.0, 1.0]
        self.ydata = np.zeros(11, dtype=float)
        for ival in range(0, 11):
            self.ydata[ival] = piecewise_linear_scalar(self.params,
                                                       self.xdata[ival])

    def test_bilinear_residuals_stepp(self):
        '''
        Calculates residual sum of squares (RSS) for two test cases
        i) RSS > 0 (alternating +/- residuals)
        ii) RSS = 0
        '''
        # Offset = +/- 0.1
        offset1 = np.array([0.1, -0.1, 0.1, -0.1, 0.1, -0.1, 0.1, -0.1, 0.1,
                            -0.1, 0.1])
        y_offset1 = self.ydata + offset1
        self.assertAlmostEqual(np.sum(offset1 ** 2.),
            get_bilinear_residuals_stepp(self.params[1:], self.xdata,
                                         y_offset1, self.params[0]))

        # Zero offset
        y_offset0 = self.ydata + np.zeros(11, dtype=float)
        self.assertAlmostEqual(0.0, get_bilinear_residuals_stepp(
            self.params[1:],
            self.xdata,
            y_offset0,
            self.params[0]))


class TestSteppCompleteness(unittest.TestCase):
    '''Class to test the revised Stepp completeness function'''

    def setUp(self):
        '''Set up the test class'''
        self.catalogue = None
        self.process = Stepp1971()
        self.config = {'time_bin': None}

    def test_stepp_get_windows(self):
        '''
        Tests the Stepp private function to generate the time bins from the
        config file
        '''
        # Test 1: Simple catalogue and single time step
        decimal_years = np.array([1950., 1970., 1990., 2010.])
        self.config['time_bin'] = 20.
        start_year_1, time_bins_1 = self.process._get_time_limits_from_config(
            self.config,
            decimal_years)
        self.assertAlmostEqual(start_year_1, 1950.)
        self.assertTrue(np.allclose(time_bins_1,
                                    np.array([1990., 1970., 1950.])))
        self.assertAlmostEqual(self.process.end_year, 2010.0)
        # Test 2: Time step larger than catalogue duration
        decimal_years = np.array([2000., 2010.])
        with self.assertRaises(ValueError) as ae:
            _, _ = self.process._get_time_limits_from_config(self.config,
                                                             decimal_years)
            self.assertEqual(str(ae.exception),
                'Catalogue duration smaller than time bin width - '
                'change time window size!')
        # Test 3:  Time input as bins
        decimal_years = np.array([1950., 2010.])
        self.config['time_bin'] = [2010., 1990., 1970., 1950]
        start_year_1, time_bins_1 = self.process._get_time_limits_from_config(
            self.config,
            decimal_years)
        self.assertAlmostEqual(start_year_1, 1950.)
        self.assertTrue(np.allclose(time_bins_1,
                                    np.array([2010., 1990., 1970., 1950.])))
        self.assertAlmostEqual(self.process.end_year, 2010.0)
        # Test 4: Incorrect time input as bins
        self.config['time_bin'] = [2010., 1970., 1990., 1950]
        with self.assertRaises(ValueError) as ae:
            _, _ = self.process._get_time_limits_from_config(self.config,
                                                             decimal_years)
            self.assertEqual(str(ae.exception),
                'Configuration time windows must be ordered from '
                'recent to oldest')


    def test_stepp_get_magnitudes(self):
        '''
        Tests the stepp private function _get_magnitudes_from_spacing
        '''
        magnitudes = np.arange(3.7, 7.8, 0.5)
        expected = np.arange(3.5, 8.0, 0.5)
        self.assertTrue(np.allclose(expected,
            self.process._get_magnitudes_from_spacing(magnitudes, 0.5)))
        expected = np.arange(3.6, 8.0, 0.2)
        self.assertTrue(np.allclose(expected,
            self.process._get_magnitudes_from_spacing(magnitudes, 0.2)))
        # Test case where magnitude spacing is greater than magnitude range
        bad_magnitudes = np.arange(4.1, 4.5, 0.1)
        with self.assertRaises(ValueError) as ae:
            _ = self.process._get_magnitudes_from_spacing(bad_magnitudes, 0.5)
            self.assertEqual(str(ae.exception),
                'Bin width greater than magnitude range!')


    def test_stepp_count_magnitudes(self):
        '''
        Tests the stepp private function _count_magnitudes which counts
        the number of magnitudes above.
        Creates a simple catalogue containing a fixed set of magnitudes
        for each year
        '''
        test_mags, test_times, time_bin = self._setup_data_for_count_test()
        expected_sigma = np.tile(
            np.array([[0.15811388], [0.18257419], [0.2236068], [0.31622777]]),
            [1, 7])
        expected_counter = np.tile(np.array([[40], [30], [20], [10]]), [1, 7])

        test_sigma, test_counter, n_mags, n_times, n_years = \
            self.process._count_magnitudes(test_mags, test_times, time_bin)

        self.assertTrue(np.allclose(expected_sigma, test_sigma))
        self.assertTrue(np.all(expected_counter == test_counter))
        self.assertEqual(n_mags, 7)
        self.assertEqual(n_times, 4)
        self.assertTrue(np.allclose(n_years, np.array([40., 30., 20., 10.])))


    def _setup_data_for_count_test(self):
        '''
        Sets up a simple test catalogue for the counting test
        '''
        time_bin = np.arange(1960., 2000., 10.)
        self.process.magnitude_bin = np.arange(4.75, 8.75, 0.5)
        mag_vals = np.arange(5.0, 8.5, 0.5)
        time_vals = np.arange(1960., 2001., 1.)
        magnitudes = mag_vals[0] * np.ones(len(time_vals))
        event_times = np.copy(time_vals)
        for ival in range(1, len(mag_vals)):
            event_times = np.column_stack([event_times, time_vals])
            magnitudes = np.column_stack([magnitudes,
                mag_vals[ival] * np.ones(len(time_vals))])
        event_times = np.reshape(event_times, len(mag_vals) * len(time_vals))
        magnitudes = np.reshape(magnitudes, len(mag_vals) * len(time_vals))
        return magnitudes, event_times, time_bin

    def test_fit_bilinear_function(self):
        '''
        Tests the function to fit a bilinear model to a data set with a
        known set of coefficients
        '''
        self.xdata = np.arange(0., 21., 1.)
        self.params = [-0.5, -1.0, 8.0, 10.0]
        self.ydata = np.zeros(len(self.xdata), dtype=float)
        for ival in range(0, len(self.xdata)):
            self.ydata[ival] = piecewise_linear_scalar(self.params,
                                                       self.xdata[ival])
        # Run analysis
        comp_time, gradient, model_line = self.process._fit_bilinear_to_stepp(
            self.xdata,
            self.ydata,
            initial_values = [-0.75, 10.0, 0.0])
        # Number of decimal places lowered to allow for uncertainty in
        # optimisation results
        self.assertAlmostEqual(np.log10(comp_time),
                               np.log10(100000219.8145678),
                               places=3)
        self.assertAlmostEqual(gradient, -1.000, places=3)
        expected_model_line = 10.0 ** (-0.5 * self.xdata + 10.)
        for ival in range(0, len(model_line)):
            self.assertAlmostEqual(np.log10(model_line[ival]),
                                   np.log10(expected_model_line[ival]),
                                   places=3)

    def test_get_completeness_points(self):
        '''
        Tests the function get_completeness_points using a synthetic
        set of "sigma" derived from a bilinear function with known gradients
        and crossover points
        '''
        crossovers = [20., 50., 80.]
        params1 = [-0.5, -1.0, np.log10(crossovers[0]), 1.5]
        params2 = [-0.5, -1.3, np.log10(crossovers[1]), 1.0]
        params3 = [-0.5, -0.8, np.log10(crossovers[2]), 0.7]

        n_years = np.hstack([1., 5., np.arange(10., 110., 10.)])
        number_values = len(n_years)
        yvals_1 = np.zeros(number_values, dtype=float)
        yvals_2 = np.zeros(number_values, dtype=float)
        yvals_3 = np.zeros(number_values, dtype=float)
        for ival in range(0, number_values):
            yvals_1[ival] = 10. ** piecewise_linear_scalar(params1,
                np.log10(n_years[ival]))
            yvals_2[ival] = 10. ** piecewise_linear_scalar(params2,
                np.log10(n_years[ival]))
            yvals_3[ival] = 10. ** piecewise_linear_scalar(params3,
                np.log10(n_years[ival]))

        test_sigma = np.column_stack([yvals_1, yvals_2, yvals_3])
        (ntime, nmags) = np.shape(test_sigma)
        completeness_time, gradients, _ = \
            self.process.get_completeness_points(n_years, test_sigma, nmags,
                                                 ntime)
        self.assertTrue(fabs(completeness_time[0] - crossovers[0]) < 1.0)
        self.assertTrue(fabs(completeness_time[1] - crossovers[1]) < 1.0)
        self.assertTrue(fabs(completeness_time[2] - crossovers[2]) < 1.0)
        self.assertTrue(fabs(gradients[0] - -1.0) < 0.1)
        self.assertTrue(fabs(gradients[1] - -1.3) < 0.1)
        self.assertTrue(fabs(gradients[2] - -0.8) < 0.1)

    def test_complete_stepp_analysis_basic(self):
        '''
        Basic test of the entire completeness analysis using a synthetic
        test catalogue with in-built completeness periods
        '''
        parser0 = CsvCatalogueParser(INPUT_FILE_1)
        self.catalogue = parser0.read_file()

        self.config = {'magnitude_bin': 0.5,
                       'time_bin': 5.0,
                       'increment_lock': True,
                       'filename': None}

        expected_completeness_table = np.array([[1990., 4.0],
                                                [1962., 4.5],
                                                [1959., 5.0],
                                                [1906., 5.5],
                                                [1906., 6.0],
                                                [1904., 6.5],
                                                [1904., 7.0]])


        np.testing.assert_array_almost_equal(
            expected_completeness_table,
            self.process.completeness(self.catalogue, self.config))
