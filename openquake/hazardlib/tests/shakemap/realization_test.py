import unittest
import numpy
from openquake.hazardlib.shakemap.realization import psd_factor


class RealizationTestCase(unittest.TestCase):
    def test_psd_factor(self):
        # F @ F.T reproduces a positive semidefinite matrix, also a
        # singular one, as the Sigma_HH_YD used for the CL field
        rng = numpy.random.default_rng(1)
        A = rng.standard_normal((4, 2))
        sigma = A @ A.T  # rank 2
        F = psd_factor(sigma)
        numpy.testing.assert_allclose(F @ F.T, sigma, atol=1E-12)

