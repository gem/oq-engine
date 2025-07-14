
import unittest
import numpy as np
from openquake._unc.bins import get_bins_data, get_bins_from_params


class BinsDataTest(unittest.TestCase):
    """
    Tests the calculation of bins data
    """
    def test_get_data1(self):
        # bins for simple case
        vals = np.array([0.011, 0.051, 0.052, 0.83])
        min_power, num_powers = get_bins_data(vals)
        np.testing.assert_equal(min_power, -2)
        np.testing.assert_equal(num_powers, 2)

    def test_get_data2(self):
        # bins for small values and negative zeros
        vals = np.array([
            -0.000000e+00, -0.000000e+00, +1.870947e-11, -0.000000e+00,
            -0.000000e+00, -0.000000e+00, +7.486355e-11, -0.000000e+00,
            -0.000000e+00, -0.000000e+00, +2.965895e-10, -0.000000e+00])
        min_power, num_powers = get_bins_data(vals)
        np.testing.assert_equal(min_power, -20)
        np.testing.assert_equal(num_powers, 11)


class GetBinsTest(unittest.TestCase):
    """
    Tests the calculation of bins i.e. edges of the intervals considered
    starting from bins data
    """
    def test_pmf_01(self):
        # simple bins calculation
        min_power = -2
        num_powers = 2
        nsampl_per_power = 5
        bins = get_bins_from_params(min_power, nsampl_per_power, num_powers)
        expected = np.array([0.01, 0.01584893, 0.02511886, 0.03981072,
                             0.06309573, 0.1, 0.15848932, 0.25118864,
                             0.39810717, 0.63095734, 1.])
        np.testing.assert_almost_equal(bins, expected, decimal=6)

    def test_pmf_02(self):
        # bins calculation - 3 powers
        min_power = -2
        num_powers = 3
        nsampl_per_power = 5
        bins = get_bins_from_params(min_power, nsampl_per_power, num_powers)
        np.testing.assert_equal(len(bins), num_powers*nsampl_per_power+1)
