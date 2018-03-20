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
import math
import numpy
from scipy.stats import truncnorm
from scipy import interpolate

from openquake.hazardlib import geo, site
from openquake.hazardlib.shakemapconverter import get_shakemap_array

F32 = numpy.float32
SHAKEMAP_URL = 'http://shakemap.rm.ingv.it/shake/{}/download/{}.xml'
PCTG = 100  # percent of g, the gravity acceleration


def get_sitecol_shakemap(array_or_id, sitecol=None, assoc_dist=None):
    """
    :param array_or_id: shakemap ID or full shakemap array
    :param sitecol: SiteCollection used to reduce the shakemap
    :param assoc_dist: association distance
    :returns: a pair (filtered site collection, filtered shakemap)
    """
    if isinstance(array_or_id, int):
        with urlopen(SHAKEMAP_URL.format(array_or_id, 'grid')) as f1, \
             urlopen(SHAKEMAP_URL.format(array_or_id, 'uncertainty')) as f2:
            array = get_shakemap_array(f1, f2)
    else:
        array = array_or_id
    if sitecol is None:  # extract the sites from the shakemap
        return site.SiteCollection.from_shakemap(array), array

    # associate the shakemap to the site collection
    # TODO: forbid IDL crossing
    bbox = (array['lon'].min(), array['lat'].min(),
            array['lon'].max(), array['lat'].max())
    sitecol = sitecol.within_bb(bbox)
    data = geo.utils.GeographicObjects(array)
    dic = data.assoc(sitecol, assoc_dist)
    sids = sorted(dic)
    return sitecol.filtered(sids), numpy.array([dic[sid] for sid in sids])


# Here is the explanation of USGS for the units they are using:
# PGA = peak ground acceleration (percent-g)
# PSA03 = spectral acceleration at 0.3 s period, 5% damping (percent-g)
# PSA10 = spectral acceleration at 1.0 s period, 5% damping (percent-g)
# PSA30 = spectral acceleration at 3.0 s period, 5% damping (percent-g)
# STDPGA = the standard deviation of PGA (natural log of percent-g)

def spatial_length_scale(imt, vs30clustered):
    """
    :param imt: intensity measure type
    :param vs30clustered: boolean
    :returns: the `b` parameter in the correlation matrix
    """
    if imt == 'PGA':
        T = 0.0
    elif imt[:2] == 'SA':
        T = float(imt.replace("SA(", "").replace(")", ""))

    if T < 1:
        b = 40.7 - 15.0 * T if vs30clustered else 8.5 + 17.2 * T
    elif T >= 1:
        b = 22.0 + 3.7 * T

    return b


def spatial_correlation_array(dmatrix, imts, correl):
    """
    :param dmatrix: distance matrix of shape (N, N)
    :param imts: M intensity measure types
    :param correl: 'no correlation', 'full correlation', 'spatial'
    :returns: array of shape (M, N, N)
    """
    n = len(dmatrix)
    corr = numpy.zeros((len(imts), n, n))
    for imti, imt in enumerate(imts):
        if correl == 'no correlation':
            corr[imti] = numpy.zeros((n, n))
        if correl == 'full correlation':
            corr[imti] = numpy.eye(n)
        elif correl == 'spatial':
            b = spatial_length_scale(imt, vs30clustered=True)
            corr[imti] = numpy.exp(-3 * dmatrix / b)
    return corr


def spatial_covariance_array(stddev, imts, corrmatrices):
    """
    :param stddev: array of shape (N, M)
    :param imts: M intensity measure types
    :param corrmatrices: array of shape (M, N, N)
    :returns: an array of shape (M, N, N)
    """
    # this depends on sPGA, sSa03, sSa10, sSa30
    M, N = corrmatrices.shape[:2]
    matrices = []
    for i, imt in enumerate(imts):
        std = stddev[imt]
        covmatrix = numpy.zeros((N, N))
        for j in range(N):
            for k in range(N):
                covmatrix[j, k] = corrmatrices[i, j, k] * std[j] * std[k]
        matrices.append(covmatrix)
    return numpy.array(matrices)


def cross_correlation_matrix(imts, corr):
    # if there is only PGA this is a 1x1 identity matrix
    M = len(imts)
    cross_matrix = numpy.zeros((M, M))
    for i in range(M):
        if imts[i] == 'PGA':
            T1 = 0.05
        elif imts[i][0:2] == 'SA':
            T1 = float(imts[i].replace("SA(", "").replace(")", ""))

        for j in range(M):
            if imts[j] == 'PGA':
                T2 = 0.05
            elif imts[j][0:2] == 'SA':
                T2 = float(imts[j].replace("SA(", "").replace(")", ""))

            if i == j:
                cross_matrix[i, j] = 1
            else:
                Tmax = max([T1, T2])
                Tmin = min([T1, T2])

                if Tmin < 0.189:
                    II = 1
                else:
                    II = 0

                if corr == 'no correlation':
                    cross_matrix[i, j] = 0
                if corr == 'full correlation':
                    cross_matrix[i, j] = 0.99999
                if corr == 'cross':
                    cross_matrix[i, j] = 1 - math.cos(math.pi / 2 - (
                        0.359 + 0.163 * II * math.log(Tmin / 0.189)
                    ) * math.log(Tmax / Tmin))

    return cross_matrix


def amplify_gmfs(imts, vs30s, gmfs):
    """
    Amplify the ground shaking depending on the vs30s
    """
    n = len(vs30s)

    for i, imt in enumerate(imts):
        if imt == 'PGA':
            T = 0.0
        elif imt[0:2] == 'SA':
            T = float(imt.replace("SA(", "").replace(")", ""))

        for iloc in range(n):
            gmfs[i * n + iloc] = amplify_ground_shaking(
                T, vs30s[iloc], gmfs[i * n + iloc])

    return gmfs


def amplify_ground_shaking(T, vs30, imls):
    """
    :param T: period
    :param vs30: velocity
    :param imls: intensity measure levels
    """
    interpolator = interpolate.interp1d(
        [-1, 0.1, 0.2, 0.3, 0.4, 100],
        [(760 / vs30)**0.35,
         (760 / vs30)**0.35,
         (760 / vs30)**0.25,
         (760 / vs30)**0.10,
         (760 / vs30)**-0.05,
         (760 / vs30)**-0.05],
        kind='linear'
    ) if T <= 0.3 else interpolate.interp1d(
        [-1, 0.1, 0.2, 0.3, 0.4, 100],
        [(760 / vs30)**0.65,
         (760 / vs30)**0.65,
         (760 / vs30)**0.60,
         (760 / vs30)**0.53,
         (760 / vs30)**0.45,
         (760 / vs30)**0.45],
        kind='linear'
    )
    return interpolator(imls) * imls


def cholesky(spatial_cov, cross_corr):
    """
    Decompose the spatial covariance and cross correlation matrices
    """
    M, N = spatial_cov.shape[:2]
    L = numpy.array([numpy.linalg.cholesky(spatial_cov[i]) for i in range(M)])
    LLT = []
    for i in range(M):
        row = [numpy.dot(L[i], L[j].T) * cross_corr[i, j] for j in range(M)]
        for j in range(N):
            singlerow = numpy.zeros(M * N)
            for i in range(M):
                singlerow[i * N:(i + 1) * N] = row[i][j]
            LLT.append(singlerow)
    return numpy.linalg.cholesky(numpy.array(LLT))


def to_gmfs(shakemap, site_effects, trunclevel, num_gmfs, seed):
    """
    :returns: an array of GMFs of shape (N, G) and dtype imt_dt
    """
    std = shakemap['std']
    imts = std.dtype.names
    val = {imt: numpy.log(shakemap['val'][imt] / PCTG) - std[imt] ** 2 / 2.
           for imt in imts}
    dmatrix = geo.geodetic.distance_matrix(shakemap['lon'], shakemap['lat'])
    spatial_corr = spatial_correlation_array(dmatrix, imts, 'spatial')
    spatial_cov = spatial_covariance_array(std, imts, spatial_corr)
    cross_corr = cross_correlation_matrix(imts, 'cross')
    M, N = spatial_corr.shape[:2]
    mu = numpy.array([numpy.ones(num_gmfs) * val[imt][j]
                      for imt in imts for j in range(N)])
    L = cholesky(spatial_cov, cross_corr)
    Z = truncnorm.rvs(-trunclevel, trunclevel, loc=0, scale=1,
                      size=(M * N, num_gmfs), random_state=seed)
    gmfs = numpy.exp(numpy.dot(L, Z) + mu)
    if site_effects:
        gmfs = amplify_gmfs(imts, shakemap['vs30'], gmfs) * 0.8

    arr = numpy.zeros((N, num_gmfs), std.dtype)
    for i, imt in enumerate(imts):
        arr[imt] = gmfs[i * N:(i + 1) * N]
    return arr

"""
here is an example for Tanzania:
https://earthquake.usgs.gov/archive/product/shakemap/us10006nkx/us/1480920466172/download/grid.xml
"""
