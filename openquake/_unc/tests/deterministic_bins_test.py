"""Regression tests for uncertainty propagation."""
import unittest
import numpy as np
from openquake._unc.convolution import HistoGroup
from openquake._unc.bins import get_bins_data, get_bins_from_params


class HistogramRegressionTest(unittest.TestCase):
    def test_exact_power_of_ten(self):
        values = np.array([0.1, 0.1])
        minp, nump = get_bins_data(values)
        bins = get_bins_from_params(minp, 10, nump)
        self.assertLessEqual(bins[0], values.min())
        self.assertGreaterEqual(bins[-1], values.max())
        h = HistoGroup.new(values[:, None], np.array([0.5, 0.5]), 10)
        self.assertAlmostEqual(h.pmfs[0].sum(), 1.)
