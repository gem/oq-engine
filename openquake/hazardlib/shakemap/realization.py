# Helpers for reconstructing the posterior covariance of a ShakeMap.
import logging
import numpy
import scipy.linalg
from scipy.linalg import solve_triangular

from openquake.hazardlib import geo, imt
from openquake.hazardlib.correlation_models.spatial_cross_imt import (
    loth_baker_2013)

F64 = numpy.float64
# the stations conditioning each output IMT of a shake_result.hdf product,
# in degrees and with the period of each observation; their correlation
# with the sites is computed only when sampling, for the needed sites
STATION_DT = numpy.dtype([
    ('imt', 'S16'), ('lon', F64), ('lat', F64), ('period', F64),
    ('phi', F64), ('add_uncertainty', F64)])

# relative mismatches (with respect to the prior phi^2) between the
# reconstructed and the stored conditional within-event variances: the
# float32 products agree within 3E-4, larger values signal a problem
VARIANCE_RTOL_WARN = 1E-3
VARIANCE_RTOL_FAIL = 1E-2


def with_metadata(array, stations=None, note=None):
    """
    :param array: a ShakeMap array
    :param stations: a STATION_DT array or None
    :param note: why the posterior components are missing, if any
    :returns: a view of the array carrying the stations and the note in
              its dtype; they survive indexing and association, but not
              the construction of new dtypes and numpy.save
    """
    meta = {key: val for key, val in [('stations', stations), ('note', note)]
            if val is not None}
    if meta:
        return array.view(numpy.dtype(array.dtype, metadata=meta))
    elif array.dtype.metadata is None:
        return array
    # the same layout without metadata, which numpy.save does not accept
    dt = array.dtype
    return array.view(numpy.dtype({
        'names': dt.names, 'formats': [dt.fields[n][0] for n in dt.names],
        'offsets': [dt.fields[n][1] for n in dt.names],
        'itemsize': dt.itemsize}))


def get_metadata(array, key):
    """
    :returns: the 'stations' or 'note' carried by a ShakeMap array, or None
    """
    return (array.dtype.metadata or {}).get(key)


def psd_factor(matrix, overwrite=False):
    # Return F such that F @ F.T is the positive semidefinite matrix.
    # Only numerical negative eigenvalues may be clipped: silently fixing
    # an indefinite covariance would change the requested distribution.
    if overwrite:
        # destroy the C-ordered matrix and store the eigenvectors in its
        # memory, with the LAPACK workspace (about one matrix) as the only
        # extra memory, while numpy.linalg.eigh needs about three more:
        # the transpose is the same matrix in Fortran order, lower=True
        # reads the same triangle and 'evd' is the same LAPACK driver as
        # numpy.linalg.eigh, which is as fast and agrees within 1E-13
        vals, vecs = scipy.linalg.eigh(
            matrix.T, lower=True, overwrite_a=True, check_finite=False,
            driver='evd')
    else:
        vals, vecs = numpy.linalg.eigh(matrix)
    if vals.size and vals.min() < -1E-6 * max(1., abs(vals).max()):
        raise ValueError('The ShakeMap covariance is not '
                         'positive semidefinite')
    vecs *= numpy.sqrt(numpy.clip(vals, 0, None))
    return vecs


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

    :param lons: longitudes of the sites, shape N
    :param lats: latitudes of the sites, shape N
    :param period: correlation period of the output IMT
    :param phi: prior within-event sigma of the sites, shape N
    :param stations: STATION_DT array of the stations of the output IMT
    :returns: K of shape (N, D), D being the number of stations
    """
    slons, slats = stations['lon'], stations['lat']
    sphi, extra = stations['phi'], stations['add_uncertainty']
    points = slons, slats, stations['period']
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
    To save memory, the correlation matrix is overwritten.
    """
    white = solve_triangular(
        numpy.linalg.cholesky(correlation), prior, lower=True)
    # phi[:, None] * correlation * phi - K @ K.T, in place
    covariance = correlation
    covariance *= phi[:, None]
    covariance *= phi
    covariance -= K @ K.T
    # The saved marginal sigmas are authoritative; small differences arise
    # from the float32 coordinates and sigmas of the ShakeMap products.
    variance = conditional_phi ** 2
    # ShakeMap clips negative conditional variances to zero. This also
    # handles its rounded raw correlation exceeding one at an observation.
    gap = numpy.abs(numpy.maximum(numpy.diag(covariance), 0) - variance)
    rel = (gap / numpy.maximum(phi ** 2, 1E-12)).max(initial=0)
    if rel > VARIANCE_RTOL_FAIL:
        raise ValueError(
            'Station conditioning does not reproduce the ShakeMap '
            f'conditional within-event variance (relative gap {rel:.1E})')
    elif rel > VARIANCE_RTOL_WARN:
        logging.warning(
            'The station conditioning reproduces the ShakeMap conditional '
            'within-event variance only within %.1E', rel)
    numpy.fill_diagonal(covariance, variance)
    factor = psd_factor(covariance, overwrite=True)
    norm = numpy.sqrt((factor ** 2).sum(axis=1))
    factor *= numpy.divide(conditional_phi, norm,
                           out=numpy.zeros_like(norm), where=norm > 0)[:, None]
    return factor @ white


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
