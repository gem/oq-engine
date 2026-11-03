import unittest
import numpy
from openquake.hazardlib.shakemap.realization import (
    conditional_within_residuals, psd_factor)


def _correlation(rng, n):
    # random positive definite correlation matrix with unit diagonal
    A = rng.standard_normal((n, n + 2))
    R = A @ A.T
    d = numpy.sqrt(numpy.diag(R))
    return R / d[:, None] / d[None, :]


class RealizationTestCase(unittest.TestCase):
    def test_within_posterior_covariance(self):
        rng = numpy.random.default_rng(0)
        nY, nD, E = 4, 3, 200_000
        R = _correlation(rng, nY + nD)
        R_YY, R_YD, R_DD = R[:nY, :nY], R[:nY, nY:], R[nY:, nY:]
        phi_Y = rng.uniform(0.2, 0.5, nY)
        phi_D = rng.uniform(0.2, 0.5, nD)
        add = rng.uniform(0.05, 0.1, nD)
        Z = rng.standard_normal((nY + nD, E))
        res = conditional_within_residuals(
            Z, R_YY, R_YD, R_DD, phi_Y, phi_D, add)
        # the covariance of the posterior residuals must be
        # W_YY - W_YD W_DD^-1 W_DY, as in ShakeMap
        W_YY = phi_Y[:, None] * R_YY * phi_Y
        W_YD = phi_Y[:, None] * R_YD * phi_D
        W_DD = phi_D[:, None] * R_DD * phi_D + numpy.diag(add ** 2)
        expected = W_YY - W_YD @ numpy.linalg.solve(W_DD, W_YD.T)
        numpy.testing.assert_allclose(
            numpy.cov(res), expected, atol=0.01)

    def test_psd_factor(self):
        # F @ F.T reproduces a positive semidefinite matrix, also a
        # singular one, as the Sigma_HH_YD used for the CL field
        rng = numpy.random.default_rng(1)
        A = rng.standard_normal((4, 2))
        sigma = A @ A.T  # rank 2
        F = psd_factor(sigma)
        numpy.testing.assert_allclose(F @ F.T, sigma, atol=1E-12)

    def test_no_stations_gives_unconditioned_field(self):
        # without stations the posterior is the prior of the points
        rng = numpy.random.default_rng(2)
        nY, E = 5, 100_000
        R = _correlation(rng, nY)
        phi = rng.uniform(0.2, 0.5, nY)
        Z = rng.standard_normal((nY, E))
        res = conditional_within_residuals(
            Z, R, numpy.empty((nY, 0)), numpy.empty((0, 0)),
            phi, numpy.empty(0), numpy.empty(0))
        expected = phi[:, None] * R * phi
        numpy.testing.assert_allclose(numpy.cov(res), expected, atol=0.01)
