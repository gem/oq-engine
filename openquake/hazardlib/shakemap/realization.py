# Helpers for the posterior realizations of a ShakeMap. The GMFs of the
# shake_result.hdf products are sampled in gmfs._realization_residuals,
# without the station conditioning, because the products do not store the
# prior within-event sigma of the points; conditional_within_residuals
# implements the exact conditioning, to be used when they will.
import numpy


def psd_factor(matrix):
    # return F such that F @ F.T is the positive semidefinite matrix
    vals, vecs = numpy.linalg.eigh(matrix)
    return vecs * numpy.sqrt(numpy.clip(vals, 0, None))


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
