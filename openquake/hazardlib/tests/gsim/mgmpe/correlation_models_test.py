# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from unittest.mock import MagicMock

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from openquake.hazardlib.gsim.mgmpe.generic_gmpe_avgsa import (
    BaseAvgSACorrelationModel,
    EmpiricalAvgSACorrelationModel,
    ClemettCorrelationModelAsc,
    ClemettCorrelationModelSInter,
    ClemettCorrelationModelSSlab,
    ClemettCorrelationModelVrancea
)

class BaseAvgSACorrelationModelTestCase(unittest.TestCase):
    """
    Testing instantiation of the BaseAvgSACorrelationModel class
    """

    def test_init_with_periods(self):
        avg_periods = np.array([1, 2, 3])
        corr_model = BaseAvgSACorrelationModel(avg_periods)

        # Assertions:
        np.testing.assert_array_almost_equal(corr_model.avg_periods, avg_periods)
        with self.assertRaises(AttributeError):
            # it goes into build_correlation_matrix nothing happens 
            corr_model.rho      
        

    def test_init_without_periods(self):
        corr_model = BaseAvgSACorrelationModel()

        # Assertions:
        assert corr_model.rho is None
        assert corr_model.avg_periods is None
        with self.assertRaises(RuntimeError) as e:
            # it goes into build_correlation_matrix nothing happens 
            corr_model(0, 0)

        assert str(e.exception) == \
            "Correlation Matrix not built. Provide 'avg_periods' at init."

TEST_ARRAY = np.array([[1.00, 0.50, 0.25],
                      [0.50, 1.00, 0.60],
                      [0.25, 0.60, 1.00]])

TEST_PERIODS = np.array([1, 2, 3])

TEST_RHO_ARRAYS = {
    "total": TEST_ARRAY,
    "dB_e": TEST_ARRAY,
    "dS2S_s": TEST_ARRAY,
    "dWS_es": TEST_ARRAY
    }

INTERPER = RegularGridInterpolator(
                points=(TEST_PERIODS, TEST_PERIODS),
                values=TEST_ARRAY,
                method="linear"
                )

class EmpiricalAvgSACorrelationModelTestCase(unittest.TestCase):
    
    def setUp(self):
        # Fresh mock for every test
        self.mock_self = MagicMock(spec=EmpiricalAvgSACorrelationModel)

    def test_init_with_large_period(self):
        avg_periods = np.array([1, 2, 4])
        # Assertions:
        with self.assertRaises(ValueError) as e:
            corr_model = EmpiricalAvgSACorrelationModel(
            avg_periods, TEST_RHO_ARRAYS, TEST_PERIODS
            )

        assert (f"Period (4.000) is greater than the maximum allowable "
                f"period for the correlation model (3.000).") == \
                str(e.exception)

    def test_init_with_small_period(self):
        avg_periods = np.array([0.5, 2, 2.5])
        # Assertions:
        with self.assertRaises(ValueError) as e:
            corr_model = EmpiricalAvgSACorrelationModel(
            avg_periods, TEST_RHO_ARRAYS, TEST_PERIODS
            )

        assert (f"Period (0.500) is less than the minimum allowable "
                f"period for the correlation model (1.000).") == \
                str(e.exception)

    def test_init_with_no_periods(self):
        # make sure the base functionality is maintained
        corr_model = EmpiricalAvgSACorrelationModel(
            None, TEST_RHO_ARRAYS, TEST_PERIODS
            )
        
        assert corr_model.rho is None
        assert corr_model.avg_periods is None
        with self.assertRaises(RuntimeError) as e:
            # it goes into build_correlation_matrix nothing happens 
            corr_model(0, 0)

        assert str(e.exception) == \
            "Correlation Matrix not built. Provide 'avg_periods' at init."

    def test_init_with_empty_rho_array(self):
        # make sure the base functionality is maintained
        avg_periods = np.array([1.0, 2, 2.5])

        with self.assertRaises(ValueError) as e:
            # it goes into build_correlation_matrix nothing happens 
            corr_model = EmpiricalAvgSACorrelationModel(
            avg_periods, {}, TEST_PERIODS
            )
        assert str(e.exception) == \
            "rho_arrays must contain the key 'total'"

    def test_init_with_wrong_type_rho_array(self):
        # make sure the base functionality is maintained
        avg_periods = np.array([1.0, 2, 2.5])
        
        with self.assertRaises(TypeError) as e:
            # it goes into build_correlation_matrix nothing happens 
            corr_model = EmpiricalAvgSACorrelationModel(
            avg_periods, 1.0, TEST_PERIODS
            )
        assert str(e.exception) == \
            "rho_arrays must be of type dict"        

    def test_2d_interpolation(self):
        # Create a mock instance without calling __init__
        new_periods = np.array([1.25, 2, 2.5])

        expected_result = np.array([[1.00000, 0.6250, 0.48125],
                                    [0.62500, 1.0000, 0.80000],
                                    [0.48125, 0.8000, 1.00000]]) 

        result = EmpiricalAvgSACorrelationModel._interpolate_matrix(
            self.mock_self, INTERPER, new_periods
        )
        
        # Assertions:
        np.testing.assert_array_almost_equal(result, expected_result)

    def test__get_correlation_with_valid_t1t2(self):
        # both t values are within the allowable range of periods
        self.mock_self.raw_Ts = TEST_PERIODS
        t1 = 1.25
        t2 = 2.5

        expected_result = 0.48125 

        result = EmpiricalAvgSACorrelationModel._get_correlation(
            self.mock_self, INTERPER, t1, t2
        )
        
        # Assertions:
        assert result == expected_result

    def test__get_correlation_with_same_t1t2(self):
        # the t values are the same
        self.mock_self.raw_Ts = TEST_PERIODS
        t1 = 1.25
        t2 = 1.25

        expected_result = 1.0

        result = EmpiricalAvgSACorrelationModel._get_correlation(
            self.mock_self, INTERPER, t1, t2
        )
        
        # Assertions:
        assert result == expected_result

    def test__get_correlation_valueerror_with_short_period(self):
        # the t1 is lower the the minimum allowable period
        self.mock_self.raw_Ts = TEST_PERIODS
        t1 = 0.001
        t2 = 1.25

        # Assertions:
        with self.assertRaises(ValueError) as e:
            EmpiricalAvgSACorrelationModel._get_correlation(
                self.mock_self, INTERPER, t1, t2
            )
        min_t = min(t1, t2)
        self.assertIn(f"Period {min_t:.2f} is outside the allowable range.", 
                      str(e.exception))

    def test__get_correlation_valueerror_with_long_period(self):
        # the t1 is lower the the minimum allowable period
        self.mock_self.raw_Ts = TEST_PERIODS
        t1 = 1.25
        t2 = 11

        # Assertions:
        with self.assertRaises(ValueError) as e:
            EmpiricalAvgSACorrelationModel._get_correlation(
                self.mock_self, INTERPER, t1, t2
            )
        max_t = max(t1, t2)
        self.assertIn(f"Period {max_t:.2f} is outside the allowable range.", 
                      str(e.exception))
        
    def test_get_correlations(self):
        avg_periods = np.array([1.25, 2, 2.5])
        
        corr_model = EmpiricalAvgSACorrelationModel(
            avg_periods, TEST_RHO_ARRAYS, TEST_PERIODS
            )
        
        reduced_test_arrays = {k:v for k,v in TEST_RHO_ARRAYS.items()}
        reduced_test_arrays.pop("dB_e")
        reduced_corr_model = EmpiricalAvgSACorrelationModel(
            avg_periods, reduced_test_arrays, TEST_PERIODS
            )
        
        # testing the formation of the rho matrix
        np.testing.assert_almost_equal(corr_model(0, 0), 1.0)
        np.testing.assert_almost_equal(corr_model(0, 2), 0.48125)
        
        # testing the different correlation functions
        np.testing.assert_almost_equal(
            corr_model.get_correlation(1.5, 2), 0.75)
        np.testing.assert_almost_equal(
            corr_model.get_between_event_correlation(2.25, 3), 0.7)
        np.testing.assert_almost_equal(
            corr_model.get_between_site_correlation(3, 1.75), 0.5125)
        np.testing.assert_almost_equal(
            corr_model.get_within_event_correlation(2.5, 3), 0.8)
        
        with self.assertRaises(ValueError) as e:
            reduced_corr_model.get_between_event_correlation(2.25, 3)
        assert str(e.exception) == \
            "Invalid type of residual (dB_e) for correlation model."


class ClemettCorrelationModelAscTestCase(unittest.TestCase):
    def setUp(self):
        self.corr_model = ClemettCorrelationModelAsc(np.array([1, 1.1, 2.0]))

    def test_total_correlations(self):
        # testing the creation of the total correlation matrix
        np.testing.assert_almost_equal(self.corr_model(0, 0), 1.0)
        np.testing.assert_almost_equal(self.corr_model(0, 1), 0.9845)
        
        actual = self.corr_model.get_correlation(0.025, 0.06)
        np.testing.assert_almost_equal(actual, 0.972)
        
    def test_between_event_correlation(self):
        actual = self.corr_model.get_between_event_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.988)

    def test_between_site_correlation(self):
        actual = self.corr_model.get_between_site_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.9755)

    def test_within_event_correlation(self):
        actual = self.corr_model.get_within_event_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.953)


class ClemettCorrelationModelSInterTestCase(unittest.TestCase):
    def setUp(self):
        self.corr_model = ClemettCorrelationModelSInter(np.array([1, 1.1, 2.0]))

    def test_total_correlations(self):
        # testing the creation of the total correlation matrix
        np.testing.assert_almost_equal(self.corr_model(0, 0), 1.0)
        np.testing.assert_almost_equal(self.corr_model(0, 1), 0.992)
        
        actual = self.corr_model.get_correlation(0.025, 0.06)
        np.testing.assert_almost_equal(actual, 0.9795)
        
    def test_between_event_correlation(self):
        actual = self.corr_model.get_between_event_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.9775)

    def test_between_site_correlation(self):
        actual = self.corr_model.get_between_site_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.985)

    def test_within_event_correlation(self):
        actual = self.corr_model.get_within_event_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.9375)


class ClemettCorrelationModelSSlabTestCase(unittest.TestCase):
    def setUp(self):
        self.corr_model = ClemettCorrelationModelSSlab(np.array([1, 1.1, 2.0]))

    def test_total_correlations(self):
        # testing the creation of the total correlation matrix
        np.testing.assert_almost_equal(self.corr_model(0, 0), 1.0)
        np.testing.assert_almost_equal(self.corr_model(0, 1), 0.993)
        
        actual = self.corr_model.get_correlation(0.025, 0.06)
        np.testing.assert_almost_equal(actual, 0.977)
        
    def test_between_event_correlation(self):
        actual = self.corr_model.get_between_event_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.9815)

    def test_between_site_correlation(self):
        actual = self.corr_model.get_between_site_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.983)

    def test_within_event_correlation(self):
        actual = self.corr_model.get_within_event_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.954)


class ClemettCorrelationModelVranceaTestCase(unittest.TestCase):
    def setUp(self):
        self.corr_model = ClemettCorrelationModelVrancea(np.array([1, 1.1, 2.0]))

    def test_total_correlations(self):
        # testing the creation of the total correlation matrix
        np.testing.assert_almost_equal(self.corr_model(0, 0), 1.0)
        np.testing.assert_almost_equal(self.corr_model(0, 1), 0.995)
        
        actual = self.corr_model.get_correlation(0.025, 0.06)
        np.testing.assert_almost_equal(actual, 0.9765)
        
    def test_between_event_correlation(self):
        actual = self.corr_model.get_between_event_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.9895)

    def test_between_site_correlation(self):
        actual = self.corr_model.get_between_site_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.988)

    def test_within_event_correlation(self):
        actual = self.corr_model.get_within_event_correlation(0.06, 0.025)
        np.testing.assert_almost_equal(actual, 0.9325)
