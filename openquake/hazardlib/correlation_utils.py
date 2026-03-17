# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Utility functions for matrix regularization and correlation/covariance operations.
These functions are adapted from statsmodels and are used for ensuring matrices
are positive semi-definite.
"""

import numpy


class IterationLimitWarning(Warning):
    """
    Iteration limit reached without convergence
    """
    pass


def clip_evals(x, value=0):
    """
    Clip eigenvalues to ensure positive semi-definiteness.
    
    Computes eigenvalues and eigenvectors, replaces eigenvalues smaller than
    the threshold with the threshold, and reconstructs the matrix.
    
    Parameters
    ----------
    x : ndarray
        symmetric matrix
    value : float
        minimum eigenvalue threshold (default: 0)
        
    Returns
    -------
    x_new : ndarray
        matrix with clipped eigenvalues
    clipped : bool
        whether any eigenvalues were clipped
    """
    evals, evecs = numpy.linalg.eigh(x)  # totally dominates the performance
    clipped = numpy.any(evals < value)
    x_new = evecs * numpy.maximum(evals, value) @ evecs.T
    return x_new, clipped


def cov2corr(cov, return_std=False):
    """
    Function to convert a covariance matrix to a correlation matrix

    Function from statsmodels.stats.moment_helpers

    Parameters
    ----------
    cov : array_like, 2d
        covariance matrix, see Notes

    Returns
    -------
    corr : ndarray (subclass)
        correlation matrix
    return_std : bool
        If this is true then the standard deviation is also returned.
        By default only the correlation matrix is returned.

    Notes
    -----
    This function does not convert subclasses of ndarrays. This requires that
    division is defined elementwise. numpy.ma.array and numpy.matrix are
    allowed.
    """
    cov = numpy.asanyarray(cov)
    std_ = numpy.sqrt(numpy.diag(cov))
    corr = cov / numpy.outer(std_, std_)
    if return_std:
        return corr, std_
    else:
        return corr


def corr2cov(corr, std):
    """
    Convert a correlation matrix to a covariance matrix given the
    standard deviation. Function from statsmodels.stats.moment_helpers.

    Parameters
    ----------
    corr : array_like, 2d
        correlation matrix, see Notes
    std : array_like, 1d
        standard deviation

    Returns
    -------
    cov : ndarray (subclass)
        covariance matrix

    Notes
    -----
    This function does not convert subclasses of ndarrays. This requires
    that multiplication is defined elementwise. numpy.ma.array are allowed,
    but not matrices.
    """
    corr = numpy.asanyarray(corr)
    std_ = numpy.asanyarray(std)
    cov = corr * numpy.outer(std_, std_)
    return cov


def corr_nearest(corr, threshold=1e-15, n_fact=100):
    """
    Find the nearest correlation matrix that is positive semi-definite.

    The function iteratively adjust the correlation matrix by clipping the
    eigenvalues of a difference matrix. The diagonal elements are set to one.

    Function from statsmodels.stats.correlation_tools

    Parameters
    ----------
    corr : ndarray, (k, k)
        initial correlation matrix
    threshold : float
        clipping threshold for smallest eigenvalue, see Notes
    n_fact : int or float
        factor to determine the maximum number of iterations. The maximum
        number of iterations is the integer part of the number of columns in
        the correlation matrix times n_fact.

    Returns
    -------
    corr_new : ndarray, (optional)
        corrected correlation matrix

    Notes
    -----
    The smallest eigenvalue of the corrected correlation matrix is
    approximately equal to the ``threshold``.
    If the threshold=0, then the smallest eigenvalue of the correlation matrix
    might be negative, but zero within a numerical error, for example in the
    range of -1e-16.

    Assumes input correlation matrix is symmetric.

    Stops after the first step if correlation matrix is already positive
    semi-definite or positive definite, so that smallest eigenvalue is above
    threshold. In this case, the returned array is not the original, but
    is equal to it within numerical precision.

    See Also
    --------
    corr_clipped
    cov_nearest
    """
    k_vars = corr.shape[0]
    if k_vars != corr.shape[1]:
        raise ValueError("matrix is not square")

    diff = numpy.zeros(corr.shape)
    x_new = corr.copy()
    diag_idx = numpy.arange(k_vars)

    for ii in range(int(len(corr) * n_fact)):
        x_adj = x_new - diff
        x_psd, clipped = clip_evals(x_adj, value=threshold)
        if not clipped:
            x_new = x_psd
            break
        diff = x_psd - x_adj
        x_new = x_psd.copy()
        x_new[diag_idx, diag_idx] = 1
    else:
        raise IterationLimitWarning

    return x_new


def corr_clipped(corr, threshold=1e-15):
    """
    Find a near correlation matrix that is positive semi-definite

    This function clips the eigenvalues, replacing eigenvalues smaller than
    the threshold by the threshold. The new matrix is normalized, so that the
    diagonal elements are one.
    Compared to corr_nearest, the distance between the original correlation
    matrix and the positive definite correlation matrix is larger, however,
    it is much faster since it only computes eigenvalues once.

    Function from statsmodels.stats.correlation_tools

    Parameters
    ----------
    corr : ndarray, (k, k)
        initial correlation matrix
    threshold : float
        clipping threshold for smallest eigenvalue, see Notes

    Returns
    -------
    corr_new : ndarray, (optional)
        corrected correlation matrix


    Notes
    -----
    The smallest eigenvalue of the corrected correlation matrix is
    approximately equal to the ``threshold``. In examples, the
    smallest eigenvalue can be by a factor of 10 smaller than the threshold,
    e.g. threshold 1e-8 can result in smallest eigenvalue in the range
    between 1e-9 and 1e-8.
    If the threshold=0, then the smallest eigenvalue of the correlation matrix
    might be negative, but zero within a numerical error, for example in the
    range of -1e-16.

    Assumes input correlation matrix is symmetric. The diagonal elements of
    returned correlation matrix is set to ones.

    If the correlation matrix is already positive semi-definite given the
    threshold, then the original correlation matrix is returned.

    ``cov_clipped`` is 40 or more times faster than ``cov_nearest`` in simple
    example, but has a slightly larger approximation error.

    See Also
    --------
    corr_nearest
    cov_nearest
    """
    x_new, clipped = clip_evals(corr, value=threshold)
    if not clipped:
        return corr

    # cov2corr
    x_std = numpy.sqrt(numpy.diag(x_new))
    x_new = x_new / x_std / x_std[:, None]
    return x_new


def cov_nearest(cov, method="clipped", threshold=1e-15, n_fact=100,
                return_all=False):
    """
    Find the nearest covariance matrix that is positive (semi-) definite

    This leaves the diagonal, i.e. the variance, unchanged

    Function from statsmodels.stats.correlation_tools

    Parameters
    ----------
    cov : ndarray, (k,k)
        initial covariance matrix
    method : str
        if "clipped", then the faster but less accurate ``corr_clipped`` is
        used.if "nearest", then ``corr_nearest`` is used
    threshold : float
        clipping threshold for smallest eigen value, see Notes
    n_fact : int or float
        factor to determine the maximum number of iterations in
        ``corr_nearest``. See its doc string
    return_all : bool
        if False (default), then only the covariance matrix is returned.
        If True, then correlation matrix and standard deviation are
        additionally returned.

    Returns
    -------
    cov_ : ndarray
        corrected covariance matrix
    corr_ : ndarray, (optional)
        corrected correlation matrix
    std_ : ndarray, (optional)
        standard deviation


    Notes
    -----
    This converts the covariance matrix to a correlation matrix. Then, finds
    the nearest correlation matrix that is positive semidefinite and converts
    it back to a covariance matrix using the initial standard deviation.

    The smallest eigenvalue of the intermediate correlation matrix is
    approximately equal to the ``threshold``.
    If the threshold=0, then the smallest eigenvalue of the correlation matrix
    might be negative, but zero within a numerical error, for example in the
    range of -1e-16.

    Assumes input covariance matrix is symmetric.

    See Also
    --------
    corr_nearest
    corr_clipped
    """
    cov_, std_ = cov2corr(cov, return_std=True)
    if method == "clipped":
        corr_ = corr_clipped(cov_, threshold=threshold)
    else:  # method == 'nearest'
        corr_ = corr_nearest(cov_, threshold=threshold, n_fact=n_fact)

    cov_ = corr2cov(corr_, std_)

    if return_all:
        return cov_, corr_, std_
    else:
        return cov_
