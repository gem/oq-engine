# Helpers for reconstructing the posterior covariance of a ShakeMap.
import numpy
from scipy.linalg import solve_triangular

from openquake.hazardlib import geo, imt
from openquake.hazardlib.correlation_models.spatial_cross_imt import (
    loth_baker_2013)


def psd_factor(matrix):
    # Return F such that F @ F.T is the positive semidefinite matrix.
    # Only numerical negative eigenvalues may be clipped: silently fixing
    # an indefinite covariance would change the requested distribution.
    vals, vecs = numpy.linalg.eigh(matrix)
    if vals.size and vals.min() < -1E-6 * max(1., abs(vals).max()):
        raise ValueError('The ShakeMap covariance is not '
                         'positive semidefinite')
    return vecs * numpy.sqrt(numpy.clip(vals, 0, None))


def _point_correlation(points, other=None):
    # Correlations between observations with possibly different periods.
    lons, lats, periods = points
    olons, olats, operiods = points if other is None else other
    unique, indices = numpy.unique(
        numpy.concatenate([periods, operiods]), return_inverse=True)
    model = loth_baker_2013.ShakeMapLothBaker2013()
    matrices = model.raw_coregionalization([imt.SA(p) for p in unique])
    rows, cols = indices[:len(periods)], indices[len(periods):]
    distances = geo.geodetic.geodetic_distance(
        lons[:, None], lats[:, None], olons, olats)
    distances[distances < 1E-7] = 0  # radians/degrees roundoff at a station
    b1, b2, b3 = (b[rows[:, None], cols] for b in matrices)
    return (b1 * numpy.exp(-3 * distances / loth_baker_2013.SHORT_RANGE) +
            b2 * numpy.exp(-3 * distances / loth_baker_2013.LONG_RANGE) +
            b3 * (distances == 0))


def station_conditioning(lons, lats, period, phi, stations):
    """Return K such that K K.T = W_YD W_DD^-1 W_DY.

    Station coordinates are converted from the radians stored by ShakeMap.
    Keeping K per grid point preserves conditioning through site filtering,
    association and NPY serialization, including repeated grid points.
    """
    slons = numpy.degrees(stations['sta_lons_rad'].reshape(-1))
    slats = numpy.degrees(stations['sta_lats_rad'].reshape(-1))
    indices = stations['sta_per_ix'].reshape(-1)
    if (numpy.any(indices < 0) or
            numpy.any(indices >= len(stations['periods']))):
        raise ValueError('Invalid ShakeMap station period indices')
    periods = stations['periods'][indices]
    sphi = stations['sta_phi'].reshape(-1)
    extra = stations['add_uncertainty'].reshape(-1)
    if not (len(slons) == len(slats) == len(periods) == len(sphi) ==
            len(extra)):
        raise ValueError('Inconsistent ShakeMap station array lengths')
    points = slons, slats, periods
    W_DD = _point_correlation(points) * sphi[:, None] * sphi
    W_DD += numpy.diag(extra ** 2)
    factor = psd_factor(W_DD)
    # Use the same eigenvalue cutoff as pinv(W_DD), rather than applying
    # pinv to its square root and retaining nearly singular station modes.
    eigenvalues = (factor ** 2).sum(axis=0)
    inverse = numpy.divide(factor, eigenvalues,
                           out=numpy.zeros_like(factor),
                           where=eigenvalues > 1E-15 * eigenvalues.max())
    K = numpy.empty((len(lons), len(slons)))
    # Bound the temporary site-to-station covariance, even for large grids.
    batch = max(1, 1_000_000 // max(1, len(slons)))
    for start in range(0, len(lons), batch):
        stop = min(start + batch, len(lons))
        out = (lons[start:stop], lats[start:stop],
               numpy.full(stop - start, period))
        W_YD = (_point_correlation(out, points) *
                phi[start:stop, None] * sphi)
        K[start:stop] = W_YD @ inverse
    return K


def posterior_within_residuals(prior, correlation, phi, K, conditional_phi):
    """Transform a shared prior field to its single-IMT posterior.

    Whitening and refactorizing each IMT preserves its posterior spatial
    covariance. Applying these linear transformations to a shared joint
    prior gives a positive semidefinite approximation to cross-IMT posterior
    dependence; ShakeMap does not supply those joint posterior blocks.
    """
    prior_factor = numpy.linalg.cholesky(correlation)
    covariance = phi[:, None] * correlation * phi - K @ K.T
    # The saved marginal sigmas are authoritative; small differences arise
    # from rounding the grid coordinates and sigmas in the ShakeMap array.
    variance = conditional_phi ** 2
    # ShakeMap clips negative conditional variances to zero. This also
    # handles its rounded raw correlation exceeding one at an observation.
    if not numpy.allclose(numpy.maximum(numpy.diag(covariance), 0), variance,
                          rtol=1E-4, atol=1E-6):
        raise ValueError('Station conditioning does not reproduce the '
                         'ShakeMap conditional within-event variance')
    numpy.fill_diagonal(covariance, variance)
    factor = psd_factor(covariance)
    norm = numpy.sqrt((factor ** 2).sum(axis=1))
    factor *= numpy.divide(conditional_phi, norm,
                           out=numpy.zeros_like(norm), where=norm > 0)[:, None]
    return factor @ solve_triangular(prior_factor, prior, lower=True)


def conditional_within_residuals(Z, R_YY, R_YD, R_DD, phi_Y, phi_D,
                                 add_uncertainty):
    """
    :param Z: standard normal samples, shape (nY + nD, E), for the joint
              prior of the points (first nY rows) and of the stations
    :param R_YY: correlation matrix of the points, shape (nY, nY)
    :param R_YD: correlation between points and stations, (nY, nD)
    :param R_DD: correlation matrix of the stations, shape (nD, nD)
    :param phi_Y: within-event sigma of the points, shape (nY,)
    :param phi_D: within-event sigma of the stations, shape (nD,)
    :param add_uncertainty: extra sigma of the stations, shape (nD,)
    :returns: posterior within-event residuals, shape (nY, E), with
              covariance W_YY - W_YD W_DD^-1 W_DY
    """
    nY = len(phi_Y)
    W_YY = phi_Y[:, None] * R_YY * phi_Y
    W_YD = phi_Y[:, None] * R_YD * phi_D
    W_DD = phi_D[:, None] * R_DD * phi_D + numpy.diag(add_uncertainty ** 2)
    # sample the joint prior of points and stations, then condition the
    # points on the sampled stations: the mean is already in ShakeMap
    prior = psd_factor(
        numpy.block([[W_YY, W_YD], [W_YD.T, W_DD]])) @ Z
    W_DD_inv = numpy.linalg.pinv(W_DD, hermitian=True)
    return prior[:nY] - W_YD @ (W_DD_inv @ prior[nY:])
