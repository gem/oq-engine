import unittest
import numpy
from openquake.hazardlib.shakemap.realization import (
    conditional_within_residuals, between_event_terms,
    approximate_residuals)


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

    def test_between_event_covariance(self):
        rng = numpy.random.default_rng(1)
        nY, k, E = 50, 3, 200_000
        C = rng.standard_normal((nY, k))
        A = rng.standard_normal((k, k))
        sigma = A @ A.T
        Z = rng.standard_normal((k, E))
        dev = between_event_terms(Z, C, sigma)
        expected = C @ sigma @ C.T
        numpy.testing.assert_allclose(
            numpy.cov(dev), expected,
            atol=0.03 * numpy.abs(expected).max())

    def test_approximate_residuals_variance(self):
        # per-point variance must be phi^2 + C Sigma C^T, as in ShakeMap
        rng = numpy.random.default_rng(3)
        M, nY, E = 2, 6, 100_000
        R = _correlation(rng, M * nY)
        phi = rng.uniform(0.2, 0.5, M * nY)
        Z = rng.standard_normal((M * nY, E))
        Cs = [rng.standard_normal((nY, k)) for k in (1, 3)]
        sigmas = []
        for k in (1, 3):
            A = rng.standard_normal((k, k))
            sigmas.append(A @ A.T / k)
        Zb = [rng.standard_normal((k, E)) for k in (1, 3)]
        res = approximate_residuals(Z, R, phi, Zb, Cs, sigmas)
        tau2 = numpy.concatenate([numpy.diag(C @ s @ C.T)
                                  for C, s in zip(Cs, sigmas)])
        expected = numpy.diag(numpy.cov(res))
        numpy.testing.assert_allclose(
            expected, phi ** 2 + tau2,
            atol=0.03 * (phi ** 2 + tau2).max())

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
