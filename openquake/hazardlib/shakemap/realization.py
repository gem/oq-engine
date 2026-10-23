# Posterior realizations of a ShakeMap, following the conditioning used by
# ShakeMap itself: the within-event residuals are conditioned on the
# stations, the between-event terms are driven by C and Sigma_HH_YD.
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


def approximate_residuals(Z, R, phi, Zb, C_list, sigma_list):
    """
    Approximate posterior residuals when the prior within-event sigma of
    the points is not stored in the product (see the conditioning notes
    in the ShakeMap issue). The within-event part uses the stored
    posterior phi with the joint Loth and Baker correlation R, without
    the station conditioning; the between-event part is exact for each
    IMT, but independent across IMTs.

    :param Z: standard normal samples, shape (M * nY, E), IMT-major
    :param R: joint correlation matrix of shape (M * nY, M * nY)
    :param phi: within-event sigma of shape (M * nY,), IMT-major
    :param Zb: list of M arrays, each of shape (k_m, E)
    :param C_list: list of M arrays, each of shape (nY, k_m)
    :param sigma_list: list of M arrays, each of shape (k_m, k_m)
    :returns: residuals of shape (M * nY, E), IMT-major
    """
    within = phi[:, None] * (psd_factor(R) @ Z)
    between = [between_event_terms(z, C, s)
               for z, C, s in zip(Zb, C_list, sigma_list)]
    return within + numpy.concatenate(between)


def between_event_terms(Z, C, sigma_yd):
    """
    :param Z: standard normal samples, shape (k, E)
    :param C: coefficients of the between-event terms, shape (nY, k)
    :param sigma_yd: covariance of the between-event terms, shape (k, k)
    :returns: between-event deviations from the median, shape (nY, E),
              with covariance C Sigma_HH_YD C^T
    """
    return C @ (psd_factor(sigma_yd) @ Z)
