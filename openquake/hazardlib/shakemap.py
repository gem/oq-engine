# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2021 GEM Foundation
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
import math
import logging
import numpy
from scipy.stats import truncnorm, norm
from scipy import interpolate

from openquake.hazardlib import geo, imt, correlation

PCTG = 100  # percent of g, the gravity acceleration
MAX_GMV = 5.  # 5 g


def spatial_correlation_array(dmatrix, imts, correl='yes',
                              vs30clustered=True):
    """
    :param dmatrix: distance matrix of shape (N, N)
    :param imts: M intensity measure types
    :param correl: 'yes', 'no' or 'full'
    :param vs30clustered: flag, True by default
    :returns: array of shape (M, N, N)
    """
    assert correl in 'yes no full', correl
    n = len(dmatrix)
    corr = numpy.zeros((len(imts), n, n))
    for imti, im in enumerate(imts):
        if correl == 'no':
            corr[imti] = numpy.eye(n)
        if correl == 'full':
            corr[imti] = numpy.ones((n, n))
        elif correl == 'yes':
            corr[imti] = correlation.jbcorrelation(dmatrix, im, vs30clustered)
    return corr


def spatial_covariance_array(stddev, corrmatrices):
    """
    :param stddev: array of shape (M, N)
    :param corrmatrices: array of shape (M, N, N)
    :returns: an array of shape (M, N, N)
    """
    # this depends on sPGA, sSa03, sSa10, sSa30
    M, N = corrmatrices.shape[:2]
    matrices = []

    for i, std in enumerate(stddev):
        covmatrix = numpy.multiply(corrmatrices[i], numpy.outer(std, std))
        matrices.append(covmatrix)

    return numpy.array(matrices)


def cross_correlation_matrix(imts, corr='yes'):
    """
    :param imts: M intensity measure types
    :param corr: 'yes', 'no' or 'full'
    :returns: an array of shape (M, M)
    """
    assert corr in 'yes no full', corr
    # if there is only PGA this is a 1x1 identity matrix
    M = len(imts)
    cross_matrix = numpy.eye(M)
    if corr == 'full':
        cross_matrix = numpy.full((M, M), 0.99999)
        numpy.fill_diagonal(cross_matrix, 1)
    elif corr == 'yes':
        for i, im in enumerate(imts):
            T1 = im.period or 0.05

            for j in range(M):
                if i == j:
                    continue
                T2 = imts[j].period or 0.05
                Tmax = max(T1, T2)
                Tmin = min(T1, T2)
                II = 1 if Tmin < 0.189 else 0
                cross_matrix[i, j] = 1 - math.cos(math.pi / 2 - (
                    0.359 + 0.163 * II * math.log(Tmin / 0.189)
                ) * math.log(Tmax / Tmin))
    return cross_matrix


def amplify_gmfs(imts, vs30s, gmfs):
    """
    Amplify the ground shaking depending on the vs30s
    """
    n = len(vs30s)
    out = [amplify_ground_shaking(im.period, vs30s[i], gmfs[m * n + i])
           for m, im in enumerate(imts) for i in range(n)]
    return numpy.array(out)


def amplify_ground_shaking(T, vs30, gmvs):
    """
    :param T: period
    :param vs30: velocity
    :param gmvs: ground motion values for the current site in units of g
    """
    gmvs[gmvs > MAX_GMV] = MAX_GMV  # accelerations > 5g are absurd
    interpolator = interpolate.interp1d(
        [0, 0.1, 0.2, 0.3, 0.4, 5],
        [(760 / vs30)**0.35,
         (760 / vs30)**0.35,
         (760 / vs30)**0.25,
         (760 / vs30)**0.10,
         (760 / vs30)**-0.05,
         (760 / vs30)**-0.05],
    ) if T <= 0.3 else interpolate.interp1d(
        [0, 0.1, 0.2, 0.3, 0.4, 5],
        [(760 / vs30)**0.65,
         (760 / vs30)**0.65,
         (760 / vs30)**0.60,
         (760 / vs30)**0.53,
         (760 / vs30)**0.45,
         (760 / vs30)**0.45],
    )
    return interpolator(gmvs) * gmvs


def cholesky(spatial_cov, cross_corr):
    """
    Decompose the spatial covariance and cross correlation matrices.

    :param spatial_cov: array of shape (M, N, N)
    :param cross_corr: array of shape (M, M)
    :returns: a triangular matrix of shape (M * N, M * N)
    """
    M, N = spatial_cov.shape[:2]
    L = numpy.array([numpy.linalg.cholesky(spatial_cov[i]) for i in range(M)])
    LLT = []
    for i in range(M):
        row = [L[i] @ L[j].T * cross_corr[i, j] for j in range(M)]
        LLT.extend(numpy.array(row).transpose(1, 0, 2).reshape(N, M*N))
    return numpy.linalg.cholesky(numpy.array(LLT))


def to_gmfs(shakemap, spatialcorr, crosscorr, site_effects, trunclevel,
            num_gmfs, seed, imts=None):
    """
    :returns: (IMT-strings, array of GMFs of shape (R, N, E, M)
    """
    N = len(shakemap)  # number of sites
    std = shakemap['std']
    if imts is None or len(imts) == 0:
        imts = std.dtype.names
    else:
        imts = [imt for imt in imts if imt in std.dtype.names]
    val = {imt: numpy.log(shakemap['val'][imt]) for imt in imts}
    imts_ = [imt.from_string(name) for name in imts]
    M = len(imts_)
    cross_corr = cross_correlation_matrix(imts_, crosscorr)
    mu = numpy.array([numpy.ones(num_gmfs) * val[str(imt)][j]
                      for imt in imts_ for j in range(N)])
    dmatrix = geo.geodetic.distance_matrix(shakemap['lon'], shakemap['lat'])
    spatial_corr = spatial_correlation_array(dmatrix, imts_, spatialcorr)
    stddev = [std[str(imt)] for imt in imts_]
    for im, std in zip(imts_, stddev):
        if std.sum() == 0:
            raise ValueError('Cannot decompose the spatial covariance '
                             'because stddev==0 for IMT=%s' % im)
    spatial_cov = spatial_covariance_array(stddev, spatial_corr)
    L = cholesky(spatial_cov, cross_corr)  # shape (M * N, M * N)
    if trunclevel:
        Z = truncnorm.rvs(-trunclevel, trunclevel, loc=0, scale=1,
                          size=(M * N, num_gmfs), random_state=seed)
    else:
        Z = norm.rvs(loc=0, scale=1, size=(M * N, num_gmfs), random_state=seed)
    # Z has shape (M * N, E)
    gmfs = numpy.exp(L @ Z + mu) / PCTG
    if site_effects:
        gmfs = amplify_gmfs(imts_, shakemap['vs30'], gmfs)
    if gmfs.max() > MAX_GMV:
        logging.warning('There are suspiciously large GMVs of %.2fg',
                        gmfs.max())
    return imts, gmfs.reshape((M, N, num_gmfs)).transpose(1, 2, 0)
