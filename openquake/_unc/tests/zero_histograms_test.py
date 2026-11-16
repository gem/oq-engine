"""Regression tests for uncertainty propagation."""
import unittest
import numpy as np
from openquake._unc.convolution import HistoGroup
from openquake._unc.hazard_pmf import mixture


class HistogramRegressionTest(unittest.TestCase):
    def test_all_zero_group(self):
        h = HistoGroup.new(np.zeros((2, 3)), np.array([0.5, 0.5]), 10)
        self.assertEqual(h.res, 10)
        self.assertEqual(h.pmfs, [None] * 3)
        self.assertEqual(h.get_stats([-1, 0.5]).shape, (0, 2))
        mat, afes = h.to_matrix()
        self.assertEqual(mat.shape, (0, 3))
        self.assertEqual(afes.shape, (0,))
        self.assertEqual((h * h).pmfs, h.pmfs)
        other = HistoGroup.new(np.full((2, 3), 0.12),
                              np.array([0.5, 0.5]), 10)
        for result in [h * other, other * h]:
            np.testing.assert_allclose(result.pmfs, other.pmfs)
        self.assertEqual(mixture([h, h]).pmfs, h.pmfs)
