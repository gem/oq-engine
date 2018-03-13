#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
from urllib.request import urlopen
import numpy
from scipy.stats import truncnorm
from scipy import interpolate

from openquake.hazardlib import geo
from openquake.hazardlib.shapemapconverter import get_shakemap_array

F32 = numpy.float32
SHAKEMAP_URL = 'http://shakemap.rm.ingv.it/shake/{}/download/grid.xml'


def get_shakemap(shakemap_id_or_fname, sitecol, assoc_dist):
    """
    :param shakemap_id_or_fname: shakemap ID or shakemap file

    :returns: a dictionary site_id -> shakemap record
    """
    if isinstance(shakemap_id_or_fname, int):
        with urlopen(SHAKEMAP_URL.format(shakemap_id_or_fname)) as f1:
            array = get_shakemap_array(f1)
    else:
        array = get_shakemap_array(shakemap_id_or_fname)
    bbox = (array['lon'].min(), array['lat'].min(),
            array['lon'].max(), array['lat'].max())
    sitecol = sitecol.within_bb(bbox)
    data = geo.utils.GeographicObjects(array)
    return data.assoc(sitecol, assoc_dist)


def to_shaking(shakemap, imts):
    """
    >>> imts = ['PGA']
    >>> dt = numpy.dtype([(imt, F32) for imt in imts])
    >>> arr = numpy.zeros(1, [('val', dt), ('std', dt)])
    >>> arr['val']['PGA'] = 0.44
    >>> arr['std']['PGA'] = 0.53
    >>> to_shaking({0: arr}, imts)
    array([[-5.5666008]], dtype=float32)
    """
    sids = numpy.array(list(shakemap))
    data = numpy.array(list(shakemap.values()))
    val = data['val']
    std = data['std']
    arr = numpy.zeros((len(val), len(imts)), F32)
    for imti, imt_ in enumerate(imts):
        arr[:, imti] = numpy.log(val[imt_] / 100) - std[imt_] ** 2 / 2.
    return arr


def calculate_spatial_correlation_matrix(dmatrix, imts, correl):
    """
    :returns: array of shape (M, N, N)
    """
    n = len(dmatrix)
    out = []
    for imt in imts:
        if correl == 'no correlation':
            corr = numpy.zeros((n, n))
        if correl == 'full correlation':
            corr = numpy.eye(n)
        elif correl == 'spatial':
            b = calculate_spatial_length_scale(imt, 'vs30clustered')
            corr = numpy.eye(n) + numpy.exp(-3 * dmatrix / b)
        out.append(corr)
    return numpy.array(corr)


def calculate_spatial_covariance_matrices(groundShaking, spatialCorrMatrices):
    # this depends on sPGA, sSa03, sSa10, sSa30
    M = len(spatialCorrMatrices)
    N = len(spatialCorrMatrices[0])
    matrices = []
    for i in range(M):
        covmatrix = numpy.zeros((N, N))
        for j in range(N):
            for k in range(N):
                covmatrix[j, k] = (spatialCorrMatrices[i, j, k] *
                                   groundShaking[j, 2 + M + i] *
                                   groundShaking[k, 2 + M + i])
        matrices.append(covmatrix)
    return numpy.array(matrices)


def generate_random_fields_ground_motion(
        imts, groundShaking, spatialCovMatrices, crossCorrMatrix,
        site_effects, trunclevel, noGMFs):
    # groundShaking has shape (N, 11) where
    # 11 = lon lat mPGA mSa03 mSa10 mSa30 sPGA sSa03 sSa10 sSa30 Vs30
    n = spatialCovMatrices.shape[1]
    M = crossCorrMatrix.shape[0]
    L = []
    LLT = []
    Z = []

    for i in range(M):
        L.append(numpy.linalg.cholesky(spatialCovMatrices[i]))

    L = numpy.array(L)

    for i in range(M):
        LLTrow = []
        for j in range(M):
            LLTrow.append(
                numpy.dot(L[i], numpy.transpose(L[j])) * crossCorrMatrix[i, j])
        for irow in range(len(LLTrow[0])):
            singleLLTrow = numpy.zeros((int(len(LLTrow) * len(LLTrow[0]))))
            for iL in range(len(LLTrow)):
                singleLLTrow[
                    iL * len(LLTrow[0]):(iL + 1) * len(LLTrow[0])
                ] = LLTrow[iL][irow]
            LLT.append(singleLLTrow)
    LLT = numpy.array(LLT)

    mu = []
    for i in range(M):
        for j in range(n):
            mu.append(numpy.ones(noGMFs) * groundShaking[j][i + 2])
    mu = numpy.array(mu)
    L = (numpy.linalg.cholesky(LLT))
    Z = truncnorm.rvs(-trunclevel, trunclevel, loc=0, scale=1,
                      size=(n * M, noGMFs))

    gmfs = numpy.exp(numpy.dot(L, Z) + mu)

    if site_effects:  # use vs30 which is the last field
        gmfs = amplify_gmfs(imts, groundShaking[:, -1], gmfs) * 0.8

    return gmfs


def amplify_gmfs(imts, vs30s, gmfs):
    """
    Amplify the ground shaking depending on the vs30s
    """
    n = len(vs30s)
    for i in range(4):
        if imts[i] == 'PGA':
            T = 0.0
        elif imts[0:2] == 'SA':
            IMT = imts[i]
            T = float(IMT.replace("SA(", "").replace(")", ""))
        for iloc in range(n):
            gmfs[i * n + iloc] = amplify_ground_shaking(
                T, vs30s[iloc], gmfs[i * n + iloc])

    return gmfs


def calculate_spatial_length_scale(imt, vs30case):
    if imt == 'PGA':
        T = 0.0
    elif imt[0:2] == 'SA':
        T = float(imt.replace("SA(", "").replace(")", ""))

    if T < 1:
        if vs30case != 'vs30clustered':
            b = 8.5 + 17.2 * T
        elif vs30case == 'vs30clustered':
            b = 40.7 - 15.0 * T
    elif T >= 1:
        b = 22.0 + 3.7 * T

    return b


def amplify_ground_shaking(T, vs30, imls):
    """
    :param T: period
    :param vs30: velocity
    :param imls: intensity measure levels
    """
    if T <= 0.3:
        interpolator = interpolate.interp1d(
            [-1, 0.1, 0.2, 0.3, 0.4, 100],
            [(760 / vs30)**0.35,
             (760 / vs30)**0.35,
             (760 / vs30)**0.25,
             (760 / vs30)**0.10,
             (760 / vs30)**-0.05,
             (760 / vs30)**-0.05], kind='linear')
    else:
        interpolator = interpolate.interp1d(
            [-1, 0.1, 0.2, 0.3, 0.4, 100],
            [(760 / vs30)**0.65,
             (760 / vs30)**0.65,
             (760 / vs30)**0.60,
             (760 / vs30)**0.53,
             (760 / vs30)**0.45,
             (760 / vs30)**0.45], kind='linear')
    return interpolator(imls) * imls

"""
here is an example for Tanzania:
https://earthquake.usgs.gov/archive/product/shakemap/us10006nkx/us/1480920466172/download/grid.xml
"""
