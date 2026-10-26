"""Regression tests for uncertainty propagation."""
import unittest
import numpy as np
from openquake._unc.convolution import HistoGroup
from openquake._unc.hazard_pmf import mixture


class HistogramRegressionTest(unittest.TestCase):
    def test_mixture_preserves_later_nonzero_column(self):
        first = HistoGroup([np.array([1., 0.]), None],
                           [-2, None], [1, None], weight=0.5)
        second = HistoGroup([np.array([1., 0.]), np.array([0., 1.])],
                            [-2, -2], [1, 1], weight=0.5)
        forward = mixture([first, second])
        reverse = mixture([second, first])
        np.testing.assert_equal(forward.idxs, [0, 1])
        np.testing.assert_equal(forward.pmfs[1], [0., 0.5])
        for a, b in zip(forward.pmfs, reverse.pmfs):
            np.testing.assert_allclose(a, b)
