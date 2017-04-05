#!/usr/bin/env python
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani, D. Monelli
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein is released as
# a prototype implementation on behalf of scientists and engineers working
# within the GEM Foundation (Global Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the hope that
# it will be useful to the scientific, engineering, disaster risk and software
# design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software developers,
# as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be directed to
# the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# The GEM Foundation, and the authors of the software, assume no liability for
# use of the software.

'''Prototype unittest code for mmax module'''

import os
import warnings
import unittest
import numpy as np
from openquake.hmtk.parsers.catalogue import CsvCatalogueParser
from openquake.hmtk.seismicity.max_magnitude.base import (_get_observed_mmax,
                                              _get_magnitude_vector_properties)
from openquake.hmtk.seismicity.max_magnitude.cumulative_moment_release import \
    CumulativeMoment
from openquake.hmtk.seismicity.max_magnitude.kijko_sellevol_fixed_b import \
    KijkoSellevolFixedb
from openquake.hmtk.seismicity.max_magnitude.kijko_sellevol_bayes import \
    KijkoSellevolBayes
from openquake.hmtk.seismicity.max_magnitude.kijko_nonparametric_gaussian import \
    KijkoNonParametricGaussian, _get_exponential_spaced_values


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__),
                              './../completeness/data')

class MmaxTestCase(unittest.TestCase):
    '''Testing class for Mmax functions'''
    def setUp(self):
        '''Set up the test class'''
        self.config = {'algorithm': None,
                       'input_mmax': None,
                       'input_mmax_uncertainty': None,
                       'maximum_iterations': None,
                       'tolerance': None,
                       'input_mmin': None,
                       'b-value': 1.0,
                       'sigma-b': 0.1,
                       'number_samples': 51,
                       'number_earthquakes': 100,
                       'number_bootstraps': None }
        #self.completeness = np.array([])

    def test_get_observed_mmax_good_data(self):
        # Asserts that the observed Mmax and corresponding sigma MMax are
        # returned when data are availavle
        test_catalogue = {
            'magnitude': np.array([3.4, 4.5, 7.6, 5.4, 4.3]),
            'sigmaMagnitude': np.array([0.1, 0.2, 0.3, 0.2, 0.1])
            }
        # Test 1: Finds the mmax from the catalogue with defined sigma
        mmax, mmax_sig = _get_observed_mmax(test_catalogue, self.config)
        self.assertAlmostEqual(mmax, 7.6)
        self.assertAlmostEqual(mmax_sig, 0.3)

    def test_get_observed_mmax_from_input(self):
        # Tests that the input mmax and its uncertainty are returned when
        # specified in the config
        # Test 3: Finds the mmax from the input file
        self.config['input_mmax'] = 8.5
        self.config['input_mmax_uncertainty'] = 0.35
        test_catalogue = {
            'magnitude': np.array([3.4, 4.5, 7.6, 5.4, 4.3]),
            'sigmaMagnitude': None
            }
        mmax, mmax_sig = _get_observed_mmax(test_catalogue, self.config)
        self.assertAlmostEqual(mmax, 8.5)
        self.assertAlmostEqual(mmax_sig, 0.35)

    def test_get_observed_max_no_sigma_error(self):
        """
        When an input mmax is given in the config, but no uncertainty is 
        specified assert that this raises an error
        """
        self.config['input_mmax'] = 8.5
        self.config['input_mmax_uncertainty'] = None
        test_catalogue = {
            'magnitude': np.array([3.4, 4.5, 7.6, 5.4, 4.3]),
            'sigmaMagnitude': None
            }
        self._get_observed_mmax_error(test_catalogue, self.config)

    def test_bad_sigma_magnitude_mmax_error(self):
        """
        If reading mmax from the catalogue, three criteria must be met
        in order to retreive the uncertainty. sigmaMagnitude must be a
        numpy.ndarray, have the same length as magnitude and not consist
        entirely of NaNs
        """
        self.config['input_mmax'] = None
        self.config['input_mmax_uncertainty'] = None
        # 1st case - sigmaMagnitude is not an np.ndarray
        test_catalogue = {
            'magnitude': np.array([3.4, 4.5, 7.6, 5.4, 4.3]),
            'sigmaMagnitude': None
            }
        self._get_observed_mmax_error(test_catalogue, self.config)
        # 2nd case - sigmaMagnitude is different from that of magnitude
        test_catalogue = {
            'magnitude': np.array([3.4, 4.5, 7.6, 5.4, 4.3]),
            'sigmaMagnitude': np.array([])
            }
        self._get_observed_mmax_error(test_catalogue, self.config)

        # 3rd case, is np.ndarray of equal length to magnitude but entirely
        # NaNs
        test_catalogue = {
            'magnitude': np.array([3.4, 4.5, 7.6, 5.4, 4.3]),
            'sigmaMagnitude': np.array([np.nan] * 5)
            }
        self._get_observed_mmax_error(test_catalogue, self.config)

    def test_observed_mmax_catalogue_uncertainty_config(self):
        # Tests the case when the observed Mmax must be read from the catalogue
        # but the uncertainty is specified in the config
        self.config['input_mmax'] = None
        self.config['input_mmax_uncertainty'] = 0.5
        test_catalogue = {
            'magnitude': np.array([3.4, 4.5, 7.6, 5.4, 4.3]),
            'sigmaMagnitude': np.array([])
            }
        mmax, mmax_sig = _get_observed_mmax(test_catalogue, self.config)
        self.assertAlmostEqual(mmax, 7.6)
        self.assertAlmostEqual(mmax_sig, 0.5)

    def test_mmax_uncertainty_largest_in_catalogue(self):
        # When largest mmax has a NaN sigmaMagnitude, take the largest
        # sigmaMagnitude found in catalogue
        self.config['input_mmax'] = None
        self.config['input_mmax_uncertainty'] = None
        test_catalogue = {
            'magnitude': np.array([3.4, 4.5, 7.6, 5.4, 4.3]),
            'sigmaMagnitude': np.array([0.1, 0.4, np.nan, 0.2, 0.1])
            }
        mmax, mmax_sig = _get_observed_mmax(test_catalogue, self.config)
        self.assertAlmostEqual(mmax, 7.6)
        self.assertAlmostEqual(mmax_sig, 0.4)

    def _get_observed_mmax_error(self, test_catalogue, test_config):
        # Tests the get_observed_mmax exceptions are raised
        with self.assertRaises(ValueError) as ae:
            mmax, mmax_sig = _get_observed_mmax(test_catalogue, self.config)
        self.assertEqual(str(ae.exception),
                         'Input mmax uncertainty must be specified!')

#    def test_get_observed_mmax(self):
#        test_catalogue = {
#            'magnitude': np.array([3.4, 4.5, 7.6, 5.4, 4.3]),
#            'sigmaMagnitude': np.array([0.1, 0.2, 0.3, 0.2, 0.1])
#            }
#        # Test 1: Finds the mmax from the catalogue with defined sigma
#        mmax, mmax_sig = _get_observed_mmax(test_catalogue, self.config)
#        self.assertAlmostEqual(mmax, 7.6)
#        self.assertAlmostEqual(mmax_sig, 0.3)
#
#        # Test 2: Finds the mmax from the catalogue with default sigma (0.2)
#        test_catalogue['sigmaMagnitude'] = None
#        mmax, mmax_sig = _get_observed_mmax(test_catalogue, self.config)
#        self.assertAlmostEqual(mmax, 7.6)
#        self.assertAlmostEqual(mmax_sig, 0.2)
#
#        # Test 3: Finds the mmax from the input file
#        self.config['input_mmax'] = 8.5
#        self.config['input_mmax_uncertainty'] = 0.35
#        mmax, mmax_sig = _get_observed_mmax(test_catalogue, self.config)
#        self.assertAlmostEqual(mmax, 8.5)
#        self.assertAlmostEqual(mmax_sig, 0.35)

    def test_get_magnitude_vector_properties(self):
        # Tests the function to retreive mmin and number of earthquakes if
        # required for certain functions
        test_catalogue = {
            'magnitude': np.array([3.4, 4.5, 7.6, 5.4, 3.8]),
            'sigmaMagnitude': np.array([0.1, 0.2, 0.3, 0.2, 0.1])
            }
        self.config['input_mmin'] = 4.0
        # Test 1: Finds the number of events from the catalogue with defined
        # minimum magnitude
        neq, mmin = _get_magnitude_vector_properties(test_catalogue,
                                                     self.config)
        self.assertAlmostEqual(neq, 3.0)
        self.assertAlmostEqual(mmin, 4.0)
        # Test 2 Finds the number of events from the catalogue with an
        # unspecified minimum magnitude
        del self.config['input_mmin']
        neq, mmin = _get_magnitude_vector_properties(test_catalogue,
                                                     self.config)
        self.assertAlmostEqual(neq, 5.0)
        self.assertAlmostEqual(mmin, 3.4)


class TestCumulativeMoment(unittest.TestCase):
    '''
    Test suite for the
    :class: openquake.hmtk.seismicity.max_magnitude.cumulative_moment_release
    module
    '''
    def setUp(self):
        filename = os.path.join(BASE_DATA_PATH, 'completeness_test_cat.csv')
        parser0 = CsvCatalogueParser(filename)
        self.catalogue = parser0.read_file()

        self.config = {'algorithm': None,
                       'number_bootstraps': None}
        self.model = CumulativeMoment()

    def test_check_config(self):
        # Tests the configuration checker
        # Test 1: No bootstraps specified
        self.config['number_bootstraps'] = None
        fixed_config = self.model.check_config(self.config)
        self.assertEqual(1, fixed_config['number_bootstraps'])
        # Test 2: Invalid number of bootstraps specified
        self.config['number_bootstraps'] = 0
        fixed_config = self.model.check_config(self.config)
        self.assertEqual(1, fixed_config['number_bootstraps'])
        # Test 3: Valid number of bootstraps
        self.config['number_bootstraps'] = 1000
        fixed_config = self.model.check_config(self.config)
        self.assertEqual(1000, fixed_config['number_bootstraps'])

    def test_cumulative_moment(self):
        # Tests the cumulative moment function

        # Test 1: Ordinary behaviour using the completeness_test_cat.csv
        self.assertAlmostEqual(7.5, self.model.cumulative_moment(
            self.catalogue.data['year'],
            self.catalogue.data['magnitude']), 1)

        # Test 2: If catalogue is less than or equal to 1 year duration
        id0 = self.catalogue.data['year'].astype(int) == 1990
        self.assertTrue(np.isinf(self.model.cumulative_moment(
            self.catalogue.data['year'][id0],
            self.catalogue.data['magnitude'][id0])))

    def test_get_mmax_cumulative_moment(self):
        # Tests the cumulative moment function sampled with uncertainty

        # Test 1: Case when no sigma is found on magnitude
        self.catalogue.data['backup'] = np.copy(
            self.catalogue.data['sigmaMagnitude'])
        self.catalogue.data['sigmaMagnitude'] = None

        mmax, sigma_mmax = self.model.get_mmax(self.catalogue, self.config)
        self.assertAlmostEqual(7.4847335589, mmax, 1)
        self.assertAlmostEqual(0.0, sigma_mmax)
        # Test 2: Case when one or no bootstraps are specified
        self.catalogue.data['sigmaMagnitude'] = self.catalogue.data['backup']
        self.config['number_bootstraps'] = 0

        mmax, sigma_mmax = self.model.get_mmax(self.catalogue, self.config)
        self.assertAlmostEqual(7.4847335589, mmax, 1)
        self.assertAlmostEqual(0.0, sigma_mmax)

        # Test 3: Ordinary test case with uncertainty - seeded random generator
        self.config['number_bootstraps'] = 1000
        # Can fix the seed (used for testing!)
        np.random.seed(123456)
        mmax, sigma_mmax = self.model.get_mmax(self.catalogue, self.config)
        self.assertAlmostEqual(7.518906927, mmax)
        self.assertAlmostEqual(0.058204597, sigma_mmax)


class TestKijkoSellevolFixedb(unittest.TestCase):
    '''
    Test suite for the Kijko & Sellevol fixed b-value estimator of Mmax
    '''
    def setUp(self):
        '''
        Set up test class
        '''
        filename = os.path.join(BASE_DATA_PATH, 'completeness_test_cat.csv')
        parser0 = CsvCatalogueParser(filename)
        self.catalogue = parser0.read_file()
        self.config = {'b-value': 1.0,
                       'input_mmin': 5.0,
                       'input_mmax': None,
                       'tolerance': 0.001,
                       'maximum_iterations': 1000}
        self.model = KijkoSellevolFixedb()

    def test_integral_function(self):
        # Tests the integral of the Kijko & Sellevol fixed-b estimator
        # define in Equation 6 of Kijko  (2004)
        # Simple test case 1 - all good parameters
        mmax = 8.5
        mmin = 5.0
        mval = 6.5
        beta = np.log(10.)
        neq = 100.
        self.assertAlmostEqual(self.model._ks_intfunc(mval, neq, mmax, mmin,
                               beta), 0.04151379)

        # Test case 4 - Number of earthquakes is 0
        mmax = 8.5
        mmin = 5.0
        neq = 0.
        self.assertAlmostEqual(1.0, self.model._ks_intfunc(mval, neq, mmax,
                                                           mmin, beta))

        # Test case 5 - beta is negative
        neq = 100.
        self.assertAlmostEqual(
            0.0, self.model._ks_intfunc(mval, neq, mmax, mmin, -0.5))

    def test_get_mmin(self):
        # Tests the main method to calculate Mmax

        # BEHAVIOUR NOTE 1: the estimator of mmax is dependent on the mmin
        # If mmin < mmin_observed then the integral will not reach stability
        # (or give rubbish) therefore if the mmin specified in the config
        # is less than mmin_obs it will be overwritten by mmin_observed

        # BEHAVIOUR NOTE 2: Negative or very small b-values (< 1E-16) will
        # result in immediate stability of the integral, thus giving
        # mmax == mmax_obs.
        # If b-value == 0 then will give a divide by zero warning

        # Test good working case b = 1, mmin = 5.0
        mmax, sigma_mmax = self.model.get_mmax(self.catalogue, self.config)
        self.assertAlmostEqual(mmax, 7.6994981)
        self.assertAlmostEqual(sigma_mmax, 0.31575163)

        # Test case with mmin < min(magnitude)  (b = 1)
        # Gives very high value of mmax
        self.config['input_mmin'] = 4.0
        mmax_1, sigma_mmax_1 = self.model.get_mmax(self.catalogue, self.config)
        self.assertAlmostEqual(mmax_1, 8.35453605)
        self.assertAlmostEqual(sigma_mmax_1, 0.959759906)

        self.config['input_mmin'] = 3.0
        mmax_2, sigma_mmax_2 = self.model.get_mmax(self.catalogue, self.config)
        self.assertAlmostEqual(mmax_1, mmax_2)

        # Case where the maximum magnitude is overriden
        # self.config['input_mmax'] = 7.6
        # self.config['b-value'] = 1.0
        # self.config['input_mmax_uncertainty'] = 0.2
        # mmax_1, sigma_mmax_1 = self.model.get_mmax(self.catalogue, self.config)
        # self.assertAlmostEqual(mmax_1, 8.1380422)
        # self.assertAlmostEqual(sigma_mmax_1, 0.57401164)

    def test_raise_runTimeWarning(self):
        """Test case with b-value = 0
        """
        self.config['input_mmin'] = 5.0
        self.config['b-value'] = 0.0
        with warnings.catch_warnings(record=True) as cm:
            self.model.get_mmax(self.catalogue, self.config)
            assert len(cm) > 0

    def test_raise_valueError(self):
        # Simple test case 2 - Mmin == Mmax (returns inf)
        mmin = 6.0
        mmax = 6.0
        mval = 6.5
        beta = np.log(10.)
        neq = 100.
        with self.assertRaises(ValueError) as cm:
            self.model._ks_intfunc(mval, neq, mmax, mmin, beta)
        self.assertEqual(str(cm.exception),
                         'Maximum magnitude smaller than minimum magnitude'
                         ' in Kijko & Sellevol (Fixed-b) integral')

    def test_raise_valueError_1(self):
        # Test case 3 - Mmin > MMax (raises value Error)
        mmin = 6.2
        mmax = 6.0
        mval = 6.5
        beta = np.log(10.)
        neq = 100.
        with self.assertRaises(ValueError) as ae:
            self.model._ks_intfunc(mval, neq, mmax, mmin, beta)
        exception = ae.exception
        self.assertEqual(str(exception),
                         'Maximum magnitude smaller than minimum magnitude'
                         ' in Kijko & Sellevol (Fixed-b) integral')


class TestKijkoSellevolBayes(unittest.TestCase):
    '''
    Test the openquake.hmtk.seismicity.max_magnitude.KijkoSellevolBayes module
    '''
    def setUp(self):
        filename = os.path.join(BASE_DATA_PATH, 'completeness_test_cat.csv')
        parser0 = CsvCatalogueParser(filename)
        self.catalogue = parser0.read_file()
        self.config = {'b-value': 1.0,
                       'sigma-b': 0.05,
                       'input_mmin': 5.0,
                       'input_mmax': None,
                       'input_mmax_uncertainty': None,
                       'tolerance': 0.001,
                       'maximum_iterations': 1000}
        self.model = KijkoSellevolBayes()

    def test_ksb_intfunc(self):
        # Tests the integral function of the Kijko-Sellevol-Bayes estimator
        # of mmax
        neq = 100.
        mval = 6.0
        mmin = 5.0
        # Good case b-value is 1.0, sigma-b is 0.05
        pval, qval = self._get_pval_qval(1.0, 0.05)
        self.assertAlmostEqual(
            self.model._ksb_intfunc(mval, neq, mmin, pval, qval),
            2.4676049E-5)
        # Bad case b-value is 0.0, sigma-b is 0,05
        pval0, qval0 = self._get_pval_qval(0.0, 0.05)
        self.assertAlmostEqual(
            self.model._ksb_intfunc(mval, neq, mmin, pval0, qval0),
            0.0)
        # Bad case neq = 0.
        self.assertAlmostEqual(
            self.model._ksb_intfunc(mval, 0., mmin, pval0, qval0),
            1.0)

        # Bad case mval < mmin
        mmin = 6.0
        mval = 5.0
        self.assertAlmostEqual(
            np.log10(self.model._ksb_intfunc(mval, neq, mmin, pval, qval)),
            95.7451687)

    def test_get_mmax(self):
        # Tests the function to calculate mmax using the Kijko-Sellevol-Bayes
        # operator
        # Good case - b = 1., sigma_b = 0.05, mmin = 5.0
        mmax, mmax_sigma = self.model.get_mmax(self.catalogue, self.config)
        self.assertAlmostEqual(mmax, 7.6902450)
        self.assertAlmostEqual(mmax_sigma, 0.30698886)

        # Bad case 1 - input  mmin < catalogue mmin
        self.config['input_mmin'] = 3.5
        mmax, mmax_sigma = self.model.get_mmax(self.catalogue, self.config)
        self.assertAlmostEqual(mmax, 8.2371167)
        self.assertAlmostEqual(mmax_sigma, 0.84306841)

        self.config['input_mmin'] = 4.0
        mmax_check, _ = self.model.get_mmax(self.catalogue, self.config)
        self.assertAlmostEqual(mmax, mmax_check)

        # Good case 1 - input mmax
        self.config['input_mmin'] = 5.0
        self.config['input_mmax'] = 7.8
        self.config['input_mmax_uncertainty'] = 0.2
        mmax, mmax_sigma = self.model.get_mmax(self.catalogue, self.config)
        self.assertAlmostEqual(mmax, 8.9427386)
        self.assertAlmostEqual(mmax_sigma, 1.16010841)

        # Bad case 1 - negative b-value (should return nan)
        self.config = {'b-value': -0.5,
                       'sigma-b': 0.05,
                       'input_mmin': 5.0,
                       'input_mmax': None,
                       'input_mmax_uncertainty': None,
                       'tolerance': 0.001,
                       'maximum_iterations': 1000}
        mmax, mmax_sigma = self.model.get_mmax(self.catalogue, self.config)
        self.assertTrue(np.isnan(mmax))
        self.assertTrue(np.isnan(mmax_sigma))

    def _get_pval_qval(self, bval, sigma_b):
        '''
        Get the p-value and q-value from b and sigma b
        '''
        beta = bval * np.log(10.)
        sigma_beta = sigma_b * np.log(10.)
        pval = beta / (sigma_beta ** 2.)
        qval = (beta / sigma_beta) ** 2.
        return pval, qval


class TestKijkoNPG(unittest.TestCase):
    '''
    Class to test the Kijko Nonparametric Gaussian function
    '''
    def setUp(self):
        filename = os.path.join(BASE_DATA_PATH, 'completeness_test_cat.csv')
        parser0 = CsvCatalogueParser(filename)
        self.catalogue = parser0.read_file()
        self.config = {'maximum_iterations': 1000,
                       'number_earthquakes': 100,
                       'number_samples': 51,
                       'tolerance': 0.05}
        self.model = KijkoNonParametricGaussian()


    def test_get_exponential_values(self):
        # Tests the function to derive an exponentially spaced set of values.
        # Tested against Kijko implementation
        min_mag = 5.8
        max_mag = 7.4
        expected_output = np.array(
            [5.8, 5.87609089, 5.94679912, 6.01283617, 6.07478116, 6.13311177,
             6.18822664, 6.24046187, 6.29010351, 6.33739696, 6.38255438,
             6.42576041, 6.46717674, 6.50694576, 6.5451935, 6.58203209,
             6.61756168, 6.65187211, 6.68504428, 6.71715129, 6.74825943,
             6.77842898, 6.80771492, 6.83616754, 6.86383296, 6.89075356,
             6.9169684, 6.94251354, 6.96742235, 6.99172576, 7.0154525,
             7.0386293, 7.06128109, 7.08343111, 7.10510113, 7.1263115,
             7.14708132, 7.16742851, 7.18736994, 7.20692147, 7.22609806,
             7.24491382, 7.26338207, 7.28151542, 7.2993258, 7.31682451,
             7.33402228, 7.35092928, 7.36755517, 7.38390916, 7.4])
        np.testing.assert_almost_equal(
            expected_output,
            _get_exponential_spaced_values(min_mag, max_mag, 51))

    def test_h_smooth(self):
        # Function to test the smoothing factor functiob h_smooth

        # Test 1: Good magnitude range (4.0 - 8.0)
        mag = np.arange(4.5, 8.1, 0.1)
        self.assertAlmostEqual(self.model.h_smooth(mag), 0.46)

        # Test 2: Bad magnitude
        mag = np.array([6.5])
        self.assertAlmostEqual(self.model.h_smooth(mag), 0.0)

    def test_gauss_cdf(self):
        # Tests the Gaussian cumulative distribution function

        # Simple case where x = -3 to 3 with a step of 1.
        xvals = np.arange(-7., 8., 1.)
        yvals_expected = np.array(
            [0.00000000e+00, 0.00000000e+00, 3.01100756e-05, 8.22638484e-04,
             2.36281702e-02, 2.06039365e-01, 3.39612064e-01, 5.00000000e-01,
             6.60387936e-01, 7.93960635e-01, 9.76371830e-01, 9.99177362e-01,
             9.99969890e-01, 1.00000000e+00, 1.00000000e+00])
        self.assertTrue(np.allclose(yvals_expected,
                                    self.model._gauss_cdf_hastings(xvals)))

    def test_kijko_npg_intfunc_simps(self):
        '''
        Tests the integration function using Simpson's rule
        '''
        # Simple test using test catalogue data - verified against
        # implementation in Kijko's own code

        # Get the largest 100 events from the catalogue
        idx = np.flipud(np.argsort(self.catalogue.data['magnitude']))
        test_mag = self.catalogue.data['magnitude'][idx[:100]]
        h_fact = self.model.h_smooth(test_mag)
        mvals = _get_exponential_spaced_values(
            np.min(test_mag), np.max(test_mag),  51)
        self.assertAlmostEqual(
            0.11026752,
            self.model._kijko_npg_intfunc_simps(
                mvals, test_mag, np.max(test_mag), h_fact, 100.))

    def test_get_mmax(self):
        # Tests the main get_mmax function. These test results are derived by
        # applying Kijko's implementation to the top 100 events in the test
        # catalogue
        mmax, mmax_sig = self.model.get_mmax(self.catalogue, self.config)

        self.assertAlmostEqual(mmax, 7.5434318)
        self.assertAlmostEqual(mmax_sig, 0.17485045)
