# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2016-2017, GEM Foundation, G. Weatherill, M. Pagani,
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

"""
Unit tests for the Penalized Maximum Likelihood algorithm class which computes
seismicity occurrence parameters for instances of sparse data
"""
import os
import unittest
import numpy as np
from copy import deepcopy
from scipy.stats import norm
from openquake.hazardlib.geo import Point, Polygon
from openquake.hmtk.seismicity.utils import area_of_polygon
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.occurrence.penalized_mle import PenalizedMLE

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

def build_catalogue_from_file(filename):
    """
    Creates a "minimal" catalogue from a raw csv file
    """
    raw_data = np.genfromtxt(filename, delimiter=",")
    neq = raw_data.shape[0]
    return Catalogue.make_from_dict({"eventID": raw_data[:, 0].astype(int),
                                     "year": raw_data[:, 1].astype(int),
                                     "dtime": raw_data[:, 2],
                                     "longitude": raw_data[:, 3],
                                     "latitude": raw_data[:, 4],
                                     "magnitude": raw_data[:, 5],
                                     "depth": raw_data[:, 6]})


class PenalizedMLETestCase(unittest.TestCase):
    """
    This test verifies (partial) implementation of the Penalized Maximum
    likelihood estimation algorithm
    """
    def setUp(self):
        cat_file = os.path.join(BASE_DATA_PATH, "synthetic_test_cat1.csv")
        self.catalogue = build_catalogue_from_file(cat_file)
        self.config = {"reference_magnitude": 3.0}
        self.completeness = np.array([[1990., 3.0],
                                      [1975., 4.0],
                                      [1960., 5.0],
                                      [1930., 6.0],
                                      [1910., 7.0]])

    def test_rate_counting(self):
        """
        Tests the algorithm to determine the observed rates of events in
        the different completeness bins
        """
        pen_mle = PenalizedMLE()
        self.config["mmax"] = 8.0
        # Run counting algorithm
        delta, kval, tval, lamda, cum_rate, cum_count, nmx, nmt = \
            pen_mle._get_rate_counts(self.catalogue,
                                     self.config,
                                     self.completeness)
        # Delta is the difference in magnitude from the minimum magnitude
        # of completeness
        np.testing.assert_array_almost_equal(
            delta,
            np.array([0., -1., -2., -3., -4., -5.]))
        # K-value is the count of earthquakes in the completeness bin
        np.testing.assert_array_almost_equal(
            kval,
            np.array([1749., 391., 72., 13., 1.]))
        # T-val is the number of years for which each count applies
        np.testing.assert_array_almost_equal(
            tval,
            np.array([20., 35., 50., 80., 100.]))
        # lamda is the rate of events (count / number of years)
        np.testing.assert_array_almost_equal(
            lamda,
            np.array([1749. / 20.,
                      391. / 35.,
                      72. / 50.,
                      13. / 80, 
                      1. / 100.]))
        # Cumulative rate
        np.testing.assert_array_almost_equal(
            cum_rate,
            np.array([np.sum(lamda[i:]) for i in range(len(lamda))]))
        # Cumulative count
        np.testing.assert_array_almost_equal(
            cum_count,
            np.array([np.sum(kval[i:]) for i in range(len(kval))]))
        # Numbers of magnitude and time bins
        self.assertEqual(nmx, 5)
        self.assertEqual(nmt, 5)

    def test_controlled_execution_1(self):
        """
        For a table representing the key properties of a known catalogue
        verify the execution of the penalised MLE. The tables and expected
        results are taken from:

        Bommer, J. J., Strasser, F. O., Rathje, E., Rodriguez-Marek, A.,
        Stafford, P. J. and Hatting, E. (2013), "Verification and Validation
        Report for Calculations Performed for the Thyspunt PSHA and Compliance
        with RD-0016", Council of Geoscience Report Number 2013-0032 (Rev. 0)
        Test Case 1 - Table 4.1
        """
        pen_mle = PenalizedMLE()
        # Magnitudes from 4.0 to 8.0 in 0.5 increments
        m_data = 4.0 - np.array([4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0])
        count_data = np.array([7., 7., 2., 1., 1., 0., 0., 0.])
        cum_count = np.array([np.sum(count_data[i:])
                              for i in range(len(count_data))])
        yr_data = np.array([203., 209., 256., 303., 338., 363., 363., 363.])
        test_config = {"area": 32101.0}
        # Prior beta
        betap = 0.85 * np.log(10.)
        # Penalty weight
        wbu = 16.0 / np.log(10.)
        # a-prior and weight
        wau = 0.0
        apu = 1.0
        bval, sigmab, rate, sigma_rate, rho = pen_mle._run_penalized_mle(
            test_config, m_data, count_data, yr_data, cum_count, betap, betap,
            wbu, wau)
        self.assertAlmostEqual(bval, 0.7664, 4)
        self.assertAlmostEqual(sigmab, 0.1178, 4)
        self.assertAlmostEqual(rate, 0.0825, 4)
        self.assertAlmostEqual(sigma_rate, 0.0195, 4)
        self.assertAlmostEqual(rho, 0.0873, 4)
    
    def test_controlled_execution_2(self):
        """
        For a table representing the key properties of a known catalogue
        verify the execution of the penalised MLE. The tables and expected
        results are taken from:

        Bommer, J. J., Strasser, F. O., Rathje, E., Rodriguez-Marek, A.,
        Stafford, P. J. and Hatting, E. (2013), "Verification and Validation
        Report for Calculations Performed for the Thyspunt PSHA and Compliance
        with RD-0016", Council of Geoscience Report Number 2013-0032 (Rev. 0)
        Test Case 2 - Table 4.2
        """
        pen_mle = PenalizedMLE()
        # Magnitudes from 4.0 to 8.0 in 0.5 increments
        m_data = 4.0 - np.array([4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0])
        count_data = np.array([11., 3., 1., 0., 0., 0., 0., 0.])
        cum_count = np.array([np.sum(count_data[i:])
                              for i in range(len(count_data))])
        yr_data = np.array([105., 129., 159., 199., 236., 262., 304., 346.])
        test_config = {"area": 185657.0}
        # Prior beta
        betap = 0.85 * np.log(10.)
        # Penalty weight
        wbu = 16.0 / np.log(10.)
        # a-prior and weight
        wau = 0.0
        apu = 1.0
        bval, sigmab, rate, sigma_rate, rho = pen_mle._run_penalized_mle(
            test_config, m_data, count_data, yr_data, cum_count, betap, betap,
            wbu, wau)
        self.assertAlmostEqual(bval, 0.9921, 4)
        self.assertAlmostEqual(sigmab, 0.1335, 4)
        self.assertAlmostEqual(rate, 0.1276, 4)
        self.assertAlmostEqual(sigma_rate, 0.0331, 4)
        self.assertAlmostEqual(rho, 0.0998, 4)

    def test_end_to_end(self):
        """
        Tests PenalizedMLE with bootstrapping and increased sample size
        and asserts that the known b-value and (approx) rate
        are within a narrow range (0.4 - 0.6 quantiles)
        """
        poly1 = Polygon([Point(20.0, 30.0), Point(20.0, 40.0),
                         Point(30.0, 40.0), Point(30.0, 30.0)])
        self.config = {"b_prior": 0.9, "reference_magnitude": 3.0,
                       "b_prior_weight": 25.0, "a_prior": 0.0,
                       "a_prior_weight": 0.0,
                       "area": area_of_polygon(poly1), "mmax": 8.0}

        sample_size = [5, 10, 20, 50, 100, 200, 500, 1000]
        expected_b = 0.9
        for sample in sample_size:
            outputs = []
            expected_rate = (float(sample) /
                             float(self.catalogue.get_number_events())) * 100.
            for i in range(1000):
                idx = np.arange(self.catalogue.get_number_events())
                np.random.shuffle(idx)
                idx = idx[:sample]
                new_cat = deepcopy(self.catalogue)
                new_cat.select_catalogue_events(np.sort(idx))
                mle = PenalizedMLE()
                bval, sigmab, rate, sigma_rate = mle.calculate(
                    new_cat,
                    self.config,
                    self.completeness)
                outputs.append([bval, sigmab, rate, sigma_rate])
            outputs = np.array(outputs)
            mean_b = np.mean(outputs[:, 0])
            mean_sigmab = np.mean(outputs[:, 1])
            mean_rate = np.mean(outputs[:, 2])
            mean_sigma_rate = np.mean(outputs[:, 3])
            # Assert that b-value is in the expected range
            l_b, u_b = (norm.ppf(0.4, loc=mean_b, scale=mean_sigmab),
                        norm.ppf(0.6, loc=mean_b, scale=mean_sigmab))
            self.assertTrue((0.9 >= l_b) and (0.9 <= u_b))
            # Assert that rate is in the expected range
            l_b, u_b = (norm.ppf(0.4, loc=mean_rate, scale=mean_sigma_rate),
                        norm.ppf(0.6, loc=mean_rate, scale=mean_sigma_rate))
            self.assertTrue((expected_rate >= l_b) and (expected_rate <= u_b))
