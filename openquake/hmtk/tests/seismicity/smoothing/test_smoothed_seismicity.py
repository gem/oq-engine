# -*- coding: utf-8 -*-
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
# 
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.
# -*- coding: utf-8 -*-
'''
Test suite for smoothed seismicity class
'''
import os
import unittest
import numpy as np
from math import fabs
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.smoothing import utils
from openquake.hmtk.seismicity.smoothing.smoothed_seismicity import (
    SmoothedSeismicity, _get_adjustment, Grid)

from openquake.hmtk.seismicity.smoothing.kernels.isotropic_gaussian import \
    IsotropicGaussian


BASE_PATH = os.path.join(os.path.dirname(__file__), 'data')
OUTPUT_FILE = 'test_smoothing_csv_data.csv'
FRANKEL_OUTPUT_FILE = 'agridc_trial.out'
FRANKEL_TEST_CATALOGUE = 'test.cc'


class TestSmoothingUtils(unittest.TestCase):
    '''
    Tests the utility functions of the smoothed seismicity tools
    '''

    def setUp(self):
        '''
        '''
        self.catalogue = Catalogue()

    def test_check_completeness_table_numpy_array(self):
        '''
        Tests behaviour when data input as numpy array
        '''
        # When valid data is input
        simple_array = np.array([[1990., 4.0],
                                 [1960., 5.0]])
        np.testing.assert_array_almost_equal(
            simple_array, utils.check_completeness_table(simple_array, None))
        # When invalid data is input
        bad_array = np.array([[1990., 4.0, 23.4],
                               [1960., 5.0, 2.1]])

        with self.assertRaises(AssertionError) as aer:
            utils.check_completeness_table(bad_array, None)


    def test_check_completeness_table_list(self):
        '''
        Tests behaviour when data input as two-element list
        '''
        # When valid data is input
        simple_list = [1990., 4.0]
        np.testing.assert_array_almost_equal(np.array([simple_list]),
                             utils.check_completeness_table(simple_list, None))
        # When invalid data is input
        bad_list = [1990.]

        with self.assertRaises(AssertionError) as aer:
            utils.check_completeness_table(bad_list, None)


    def test_check_completeness_table_none(self):
        '''
        Checks any other instance - completeness from catalogue
        '''
        self.catalogue.data['year'] = np.array([1991., 1992., 1990., 2005.])
        self.catalogue.data['magnitude'] = np.array([4.1, 4.5, 4.0, 7.5])
        np.testing.assert_array_almost_equal(np.array([[1990., 4.0]]),
            utils.check_completeness_table(None, self.catalogue))


    def test_get_even_magnitude_completeness(self):
        '''
        Tests the function to render an evenly spaced completeness table at
        0.1 interval spacing
        '''
        # Common case - many rows
        self.catalogue = Catalogue()
        self.catalogue.data['magnitude'] = np.array([4.5, 5.0])
        comp_table = np.array([[1990., 4.0],
                               [1960., 4.5],
                               [1900., 4.8]])
        expected_table = np.array([[1990., 4.0],
                                   [1990., 4.1],
                                   [1990., 4.2],
                                   [1990., 4.3],
                                   [1990., 4.4],
                                   [1960., 4.5],
                                   [1960., 4.6],
                                   [1960., 4.7],
                                   [1900., 4.8],
                                   [1900., 4.9],
                                   [1900., 5.0]])
        np.testing.assert_array_almost_equal(expected_table,
            utils.get_even_magnitude_completeness(comp_table,
                                                  self.catalogue)[0])

        # Common case - only one value
        comp_table = np.array([[1990., 4.0]])
        np.testing.assert_array_almost_equal(np.array([[1990., 4.0]]),
            utils.get_even_magnitude_completeness(comp_table,
                                                  self.catalogue)[0])


    def test_get_adjustment_factor(self):
        '''
        Tests the function that should return an input adjustment factor if
        the magnitude is from a "complete" event - and a zero otherwise
        '''
        # Good case - when event is in the first completeness period
        comp_table = np.array([[1990., 4.0],
                               [1960., 4.5],
                               [1900., 5.5]])
        self.catalogue.data['magnitude'] = np.array([4.5, 5.7])
        comp_table = utils.get_even_magnitude_completeness(comp_table,
                                                           self.catalogue)[0]

        tfact = 0.5
        self.assertAlmostEqual(tfact,
            _get_adjustment(4.2, 1995., comp_table[0, 1], comp_table[:, 0],
                            tfact))

        # Good case - when event is in a previous completeness period
        self.assertAlmostEqual(tfact,
            _get_adjustment(4.7, 1985., comp_table[0, 1], comp_table[:, 0],
                            tfact))

        # Bad case - below minimum completeness in file
        self.assertFalse(_get_adjustment(3.8, 1990., comp_table[0, 1],
                                         comp_table[:, 0], tfact))

        # Bad case - below an earlier completeness threshold
        self.assertFalse(_get_adjustment(4.8, 1950., comp_table[0, 1],
                                         comp_table[:, 0], tfact))

        # Good case when only one completeness period is needed
        comp_table = np.array([[1960., 4.5]])
        self.assertAlmostEqual(1.0,
            _get_adjustment(5.0, 1990., comp_table[0, 1], comp_table[:, 0],
                            tfact))
        # Bad case when only one completeness period is needed
        self.assertFalse(_get_adjustment(4.0, 1990., comp_table[0, 1],
                                         comp_table[:, 0], tfact))


    def test_hermann_factor(self):
        '''
        Tests the Hermann (1977) correction factor
        Simple check - no parameter test set
        '''
        # Simple case bval = 0.1, mmin = 5.0, mag_inc = 0.1
        fval, fival = utils.hermann_adjustment_factors(1.0, 5.0, 0.1)
        self.assertAlmostEqual(fval, 100000.0)
        self.assertAlmostEqual(fival, 0.2307675)

    def test_incremental_avalue(self):
        '''
        Tests the Incremental a-value function. Notionally equivalent to the
        Hermann factor
        '''
        # Simple case (again no variation in parameter behaviour!)
        ainc = utils.incremental_a_value(1.0, 5.0, 0.1)
        self.assertAlmostEqual(ainc, 99999.6670766, 3)


    def test_weichert_factor(self):
        '''
        Tests the Weichert adjustment factor to compensate for time varying
        completeness
        '''
        # Test 1: Comparison against the USGS Implementation
        beta = 0.8 * np.log(10.)
        end_year = 2006.
        comp_table = np.array([[1933., 4.0],
                               [1900., 5.0],
                               [1850., 6.0],
                               [1850., 7.0]])
        self.assertAlmostEqual(0.0124319686,
            utils.get_weichert_factor(beta, comp_table[:, 1], comp_table[:, 0],
                                      end_year)[0])

        # Test 2: Single value of completeness
        comp_table = np.array([[1960., 4.0]])
        self.assertAlmostEqual(1. / (2006. - 1960. + 1.),
            utils.get_weichert_factor(beta, comp_table[:, 1], comp_table[:, 0],
                                      end_year)[0])



class TestSmoothedSeismicity(unittest.TestCase):
    '''
    Class to test the implementation of the smoothed seismicity algorithm
    '''
    def setUp(self):
        self.grid_limits = []
        self.model = None

    def test_instantiation(self):
        '''
        Tests the instantiation of the class
        '''
        # Test 1: Good Grid Limits
        self.grid_limits = Grid.make_from_list(
            [35.0, 40., 0.5, 40., 45.0, 0.5, 0., 40., 20.])
        expected_dict = {'beta': None,
                         'bval': None,
                         'catalogue': None,
                         'data': None,
                         'grid': None,
                         'grid_limits': {'xmax': 40.0,
                                         'xmin': 35.0,
                                         'xspc': 0.5,
                                         'ymax': 45.0,
                                         'ymin': 40.0,
                                         'yspc': 0.5,
                                         'zmax': 40.0,
                                         'zmin': 0.0,
                                         'zspc': 20.0},
                         'kernel': None,
                         'use_3d': False}

        self.model = SmoothedSeismicity(self.grid_limits)
        self.assertDictEqual(self.model.__dict__, expected_dict)
        # Test 2 - with b-value set
        self.model = SmoothedSeismicity(self.grid_limits, bvalue=1.0)
        expected_dict['bval'] = 1.0
        expected_dict['beta'] = np.log(10.)
        self.assertDictEqual(self.model.__dict__, expected_dict)

    def test_get_2d_grid(self):
        '''
        Tests the module to count the events across a grid
        '''
        self.grid_limits = Grid.make_from_list(
            [35.0, 40., 0.5, 40., 45.0, 0.5, 0., 40., 20.])
        self.model = SmoothedSeismicity(self.grid_limits, bvalue=1.0)
        # Case 1 - all events in grid (including borderline cases)
        comp_table = np.array([[1960., 4.0]])
        lons = np.arange(35.0, 41.0, 1.0)
        lats = np.arange(40.0, 46.0, 1.0)
        mags = 5.0 * np.ones(6)
        years = 2000. * np.ones(6)
        expected_result = np.zeros(100, dtype=int)
        expected_result[[9, 28, 46, 64, 82, 90]] = 1
        np.testing.assert_array_almost_equal(expected_result,
            self.model.create_2D_grid_simple(lons, lats, years, mags,
                                             comp_table))
        self.assertEqual(np.sum(expected_result), 6)

        # Case 2 - some events outside grid
        lons = np.arange(35.0, 42.0, 1.0)
        lats = np.arange(40.0, 47.0, 1.0)
        mags = 5.0 * np.ones(7)
        years = 2000. * np.ones(7)
        np.testing.assert_array_almost_equal(expected_result,
            self.model.create_2D_grid_simple(lons, lats, years, mags,
                                             comp_table))
        self.assertEqual(np.sum(expected_result), 6)

    def test_get_3d_grid(self):
        '''
        Tests the module to count the events in a 3D grid
        '''
        comp_table = np.array([[1960., 4.0]])
        self.catalogue = Catalogue()
        self.catalogue.data['longitude'] = np.hstack([
            np.arange(35., 41.0, 1.0),
            np.arange(35., 41.0, 1.0)])
        self.catalogue.data['latitude'] = np.hstack([
            np.arange(40., 46.0, 1.0),
            np.arange(40., 46.0, 1.0)])
        self.catalogue.data['depth'] = np.hstack([10.0 * np.ones(6),
                                                  30.0 * np.ones(6)])
        self.catalogue.data['magnitude'] = 4.5 * np.ones(12)
        self.catalogue.data['year'] = 1990. * np.ones(12)


        # Case 1 - one depth layer
        self.grid_limits = Grid.make_from_list(
            [35.0, 40., 0.5, 40.0, 45., 0.5, 0., 40., 40.])
        self.model = SmoothedSeismicity(self.grid_limits, bvalue=1.0)
        [gx, gy] = np.meshgrid(np.arange(35.25, 40., 0.5),
                               np.arange(40.25, 45., 0.5))
        ngp = np.shape(gx)[0]  * np.shape(gy)[1]
        gx = np.reshape(gx, [ngp, 1])
        gy = np.reshape(gy, [ngp, 1])
        gz = 20. * np.ones(ngp)
        expected_count = np.zeros(ngp, dtype=float)
        expected_count[[9, 28, 46, 64, 82, 90]] = 2.0
        expected_result = np.column_stack([gx, np.flipud(gy), gz,
                                           expected_count])
        self.model.create_3D_grid(self.catalogue, comp_table)
        np.testing.assert_array_almost_equal(expected_result, self.model.data)

        # Case 2 - multiple depth layers
        self.grid_limits = Grid.make_from_list(
            [35.0, 40., 0.5, 40., 45., 0.5, 0., 40., 20.])
        self.model = SmoothedSeismicity(self.grid_limits, bvalue=1.0)
        expected_result = np.vstack([expected_result, expected_result])
        expected_count = np.zeros(200)
        expected_count[[9, 28, 46, 64, 82, 90,
            109, 128, 146, 164, 182, 190]] = 1.0
        expected_result[:, -1] = expected_count
        expected_result[:, 2] = np.hstack([10. * np.ones(100),
                                           30. * np.ones(100)])
        self.model.create_3D_grid(self.catalogue, comp_table)
        np.testing.assert_array_almost_equal(expected_result, self.model.data)

    def test_csv_writer(self):
        '''
        Short test of consistency of the csv writer
        '''

        self.grid_limits = [35.0, 40., 0.5, 40., 45.0, 0.5, 0., 40., 20.]
        self.model = SmoothedSeismicity(self.grid_limits, bvalue=1.0)
        self.model.data = np.array([[1.0, 1.0, 10.0, 4.0, 4.0, 1.0],
                                    [2.0, 2.0, 20.0, 8.0, 8.0, 1.0]])
        self.model.write_to_csv(OUTPUT_FILE)
        return_data = np.genfromtxt(OUTPUT_FILE, delimiter=',', skip_header=1)
        np.testing.assert_array_almost_equal(return_data, self.model.data)
        os.system('rm ' + OUTPUT_FILE)


    def test_analysis_Frankel_comparison(self):
        '''
        To test the run_analysis function we compare test results with those
        from Frankel's fortran implementation, under the same conditions
        '''
        self.grid_limits = [-128., -113.0, 0.2, 30., 43.0, 0.2, 0., 100., 100.]
        comp_table = np.array([[1933., 4.0],
                               [1900., 5.0],
                               [1850., 6.0],
                               [1850., 7.0]])
        config = {'Length_Limit': 3., 'BandWidth': 50., 'increment': 0.1}
        self.model = SmoothedSeismicity(self.grid_limits, bvalue=0.8)
        self.catalogue = Catalogue()
        frankel_catalogue = np.genfromtxt(os.path.join(BASE_PATH,
                                                       FRANKEL_TEST_CATALOGUE))
        self.catalogue.data['magnitude'] = frankel_catalogue[:, 0]
        self.catalogue.data['longitude'] = frankel_catalogue[:, 1]
        self.catalogue.data['latitude'] = frankel_catalogue[:, 2]
        self.catalogue.data['depth'] = frankel_catalogue[:, 3]
        self.catalogue.data['year'] = frankel_catalogue[:, 4]
        self.catalogue.end_year = 2006
        frankel_results = np.genfromtxt(os.path.join(BASE_PATH,
                                                     FRANKEL_OUTPUT_FILE))
        # Run analysis
        output_data = self.model.run_analysis(
            self.catalogue,
            config,
            completeness_table=comp_table,
            smoothing_kernel = IsotropicGaussian())

        self.assertTrue(fabs(np.sum(output_data[:, -1]) -
                             np.sum(output_data[:, -2])) < 1.0)
        self.assertTrue(fabs(np.sum(output_data[:, -1]) - 390.) < 1.0)
