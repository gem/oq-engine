# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2020 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
:mod:`openquake.hazardlib.calc.disagg` contains
:func:`disaggregation` as well as several aggregation functions for
extracting a specific PMF from the result of :func:`disaggregation`.
"""
import warnings
import operator
import collections
import numpy
import scipy.stats

from openquake.hazardlib import pmf, contexts
from openquake.baselib import hdf5, performance
from openquake.baselib.general import groupby
from openquake.hazardlib.calc import filters
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.utils import (angular_distance, KM_TO_DEGREES,
                                           cross_idl)
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.gsim.base import (
    ContextMaker, get_mean_std, to_distribution_values)

BIN_NAMES = 'mag', 'dist', 'lon', 'lat', 'eps', 'trt'
BinData = collections.namedtuple('BinData', 'mags, dists, lons, lats, pnes')


def assert_same_shape(arrays):
    """
    Raises an AssertionError if the shapes are not consistent
    """
    shape = arrays[0].shape
    for arr in arrays[1:]:
        assert arr.shape == shape, (arr.shape, shape)


def get_edges_shapedic(oq, sitecol, mags_by_trt):
    """
    :returns: (mag dist lon lat eps trt) edges and shape dictionary
    """
    tl = oq.truncation_level
    Z = oq.num_rlzs_disagg if oq.rlz_index is None else len(oq.rlz_index)
    eps_edges = numpy.linspace(-tl, tl, oq.num_epsilon_bins + 1)

    # build mag_edges
    mags = set()
    trts = []
    for trt, _mags in mags_by_trt.items():
        mags.update(float(mag) for mag in _mags)
        trts.append(trt)
    mags = sorted(mags)
    mag_edges = oq.mag_bin_width * numpy.arange(
        int(numpy.floor(min(mags) / oq.mag_bin_width)),
        int(numpy.ceil(max(mags) / oq.mag_bin_width) + 1))

    # build dist_edges
    maxdist = max(filters.getdefault(oq.maximum_distance, trt) for trt in trts)
    dist_edges = oq.distance_bin_width * numpy.arange(
        0, int(numpy.ceil(maxdist / oq.distance_bin_width) + 1))

    # build eps_edges
    eps_edges = numpy.linspace(-tl, tl, oq.num_epsilon_bins + 1)

    # build lon_edges, lat_edges per sid
    lon_edges, lat_edges = {}, {}  # by sid
    for site in sitecol:
        loc = site.location
        lon_edges[site.id], lat_edges[site.id] = lon_lat_bins(
            loc.x, loc.y, maxdist, oq.coordinate_bin_width)

    # sanity check: the shapes of the lon lat edges are consistent
    assert_same_shape(list(lon_edges.values()))
    assert_same_shape(list(lat_edges.values()))

    bin_edges = [mag_edges, dist_edges, lon_edges, lat_edges, eps_edges]
    shape = [len(bin) - 1 for bin in get_bins(bin_edges, 0)] + [len(trts)]
    shapedic = dict(zip(BIN_NAMES, shape))
    shapedic['N'] = len(sitecol)
    shapedic['M'] = M = len(oq.imtls)
    shapedic['P'] = len(oq.poes_disagg or (None,))
    shapedic['Z'] = Z
    shapedic['tasks_per_IMT'] = numpy.ceil(oq.concurrent_tasks / M) or 1
    return bin_edges + [trts], shapedic


def _eps3(truncation_level, n_epsilons):
    # NB: instantiating truncnorm is slow and calls the infamous "doccer"
    tn = scipy.stats.truncnorm(-truncation_level, truncation_level)
    eps = numpy.linspace(-truncation_level, truncation_level, n_epsilons + 1)
    eps_bands = tn.cdf(eps[1:]) - tn.cdf(eps[:-1])
    return tn, eps, eps_bands


# this is inside an inner loop
def _disaggregate(cmaker, site1, ctxs, iml1, eps3,
                  pne_mon=performance.Monitor(),
                  gmf_mon=performance.Monitor()):
    # disaggregate (separate) PoE in different contributions
    U, P, E = len(ctxs), len(iml1), len(eps3[1]) - 1
    try:
        gsim = cmaker.gsim_by_rlzi[iml1.rlzi]
    except KeyError:
        U = 0
    bdata = BinData(mags=numpy.zeros(U), dists=numpy.zeros(U),
                    lons=numpy.zeros(U), lats=numpy.zeros(U),
                    pnes=numpy.zeros((U, P, E)))
    if U == 0:
        return bdata
    mean_std = numpy.zeros((2, U))
    with gmf_mon:
        for u, (rctx, dctx) in enumerate(ctxs):
            [dist] = dctx.rrup
            if gsim.minimum_distance and dist < gsim.minimum_distance:
                dist = gsim.minimum_distance
            bdata.mags[u] = rctx.mag
            bdata.lons[u] = dctx.lon
            bdata.lats[u] = dctx.lat
            bdata.dists[u] = dist
            mean_std[:, u] = get_mean_std(
                site1, rctx, dctx, [iml1.imt], [gsim]).reshape(2)
    with pne_mon:
        truncnorm, epsilons, eps_bands = eps3
        cum_bands = [eps_bands[e:].sum() for e in range(len(eps_bands))] + [0]
        imls = to_distribution_values(iml1, iml1.imt)  # shape P
        for p, iml in enumerate(imls):
            lvls = (iml - mean_std[0]) / mean_std[1]
            tn = truncnorm.sf(lvls)
            bins = numpy.searchsorted(epsilons, lvls)
            for u, (rctx, _) in enumerate(ctxs):
                poes = _disagg_eps(tn[u], bins[u], eps_bands, cum_bands)
                bdata.pnes[u, p] = rctx.get_probability_no_exceedance(poes)
    return bdata


def _disagg_eps(truncnorm, bin, eps_bands, cum_bands):
    # disaggregate PoE of `iml` in different contributions,
    # each coming from ``epsilons`` distribution bins
    res = numpy.zeros(len(eps_bands))
    for e in range(len(res)):
        if e == bin - 1:
            res[e] = truncnorm - cum_bands[bin]
        elif e >= bin:
            res[e] = eps_bands[e]
    return res


# used in calculators/disaggregation
def lon_lat_bins(lon, lat, size_km, coord_bin_width):
    """
    Define lon, lat bin edges for disaggregation histograms.

    :param lon: longitude of the site
    :param lat: latitude of the site
    :param size_km: total size of the bins in km
    :param coord_bin_width: bin width in degrees
    :returns: two arrays lon bins, lat bins
    """
    nbins = numpy.ceil(size_km * KM_TO_DEGREES / coord_bin_width)
    delta_lon = min(angular_distance(size_km, lat), 180)
    delta_lat = min(size_km * KM_TO_DEGREES, 90)
    EPS = .001  # avoid discarding the last edge
    lon_bins = lon + numpy.arange(-delta_lon, delta_lon + EPS,
                                  delta_lon / nbins)
    lat_bins = lat + numpy.arange(-delta_lat, delta_lat + EPS,
                                  delta_lat / nbins)
    if cross_idl(*lon_bins):
        lon_bins %= 360
    return lon_bins, lat_bins


def get_bins(bin_edges, sid):
    """
    :returns: mags, dists, lons, lats, eps for the given sid
    """
    mag_bins, dist_bins, lon_bins, lat_bins, eps_bins = bin_edges
    return mag_bins, dist_bins, lon_bins[sid], lat_bins[sid], eps_bins


# this is fast
def _build_disagg_matrix(bdata, bins):
    """
    :param bdata: a dictionary of probabilities of no exceedence
    :param bins: bin edges
    :returns: a 6D-matrix of shape (#magbins, #distbins, #lonbins,
                                    #latbins, #epsbins, #poes)
    """
    mag_bins, dist_bins, lon_bins, lat_bins, eps_bins = bins
    dim1, dim2, dim3, dim4, dim5 = shape = [len(b)-1 for b in bins]

    # find bin indexes of rupture attributes; bins are assumed closed
    # on the lower bound, and open on the upper bound, that is [ )
    # longitude values need an ad-hoc method to take into account
    # the 'international date line' issue
    # the 'minus 1' is needed because the digitize method returns the
    # index of the upper bound of the bin
    mags_idx = numpy.digitize(bdata.mags+pmf.PRECISION, mag_bins) - 1
    dists_idx = numpy.digitize(bdata.dists, dist_bins) - 1
    lons_idx = _digitize_lons(bdata.lons, lon_bins)
    lats_idx = numpy.digitize(bdata.lats, lat_bins) - 1

    # because of the way numpy.digitize works, values equal to the last bin
    # edge are associated to an index equal to len(bins) which is not a
    # valid index for the disaggregation matrix. Such values are assumed
    # to fall in the last bin
    mags_idx[mags_idx == dim1] = dim1 - 1
    dists_idx[dists_idx == dim2] = dim2 - 1
    lons_idx[lons_idx == dim3] = dim3 - 1
    lats_idx[lats_idx == dim4] = dim4 - 1
    U, P, E = bdata.pnes.shape
    mat6D = numpy.ones(shape + [P])
    for i_mag, i_dist, i_lon, i_lat, pne in zip(
            mags_idx, dists_idx, lons_idx, lats_idx, bdata.pnes):
        mat6D[i_mag, i_dist, i_lon, i_lat] *= pne.T  # shape E, P
    return 1. - mat6D


# called by the engine
def build_matrix(cmaker, singlesite, ctxs, imt, iml2, rlzs,
                 num_epsilon_bins, bins, pne_mon, mat_mon, gmf_mon):
    """
    :param cmaker: a ContextMaker
    :param singlesite: a site collection with a single site
    :param ctxs: a list of pairs (rctx, dctx)
    :param imt: an intensity measure type
    :param iml2: an array of shape (P, Z)
    :param rlzs: Z realizations for the given site
    :param num_epsilon_bins: number of epsilons bins
    :param bins: bin edges for the given site
    :returns:
        7D disaggregation matrix of shape (#magbins, #distbins, #lonbins,
                                           #latbins, #epsbins, P, Z)
    """
    eps3 = _eps3(cmaker.trunclevel, num_epsilon_bins)
    arr = numpy.zeros([len(b) - 1 for b in bins] + list(iml2.shape))
    for z, rlz in enumerate(rlzs):
        iml1 = hdf5.ArrayWrapper(iml2[:, z], dict(rlzi=rlz, imt=imt))
        bdata = _disaggregate(cmaker, singlesite, ctxs, iml1, eps3,
                              pne_mon, gmf_mon)
        if bdata.pnes.sum():
            with mat_mon:
                arr[..., z] = _build_disagg_matrix(bdata, bins)
    return arr


def _digitize_lons(lons, lon_bins):
    """
    Return indices of the bins to which each value in lons belongs.
    Takes into account the case in which longitude values cross the
    international date line.

    :parameter lons:
        An instance of `numpy.ndarray`.
    :parameter lons_bins:
        An instance of `numpy.ndarray`.
    """
    if cross_idl(lon_bins[0], lon_bins[-1]):
        idx = numpy.zeros_like(lons, dtype=numpy.int)
        for i_lon in range(len(lon_bins) - 1):
            extents = get_longitudinal_extent(lons, lon_bins[i_lon + 1])
            lon_idx = extents > 0
            if i_lon != 0:
                extents = get_longitudinal_extent(lon_bins[i_lon], lons)
                lon_idx &= extents >= 0
            idx[lon_idx] = i_lon
        return numpy.array(idx)
    else:
        return numpy.digitize(lons, lon_bins) - 1


# this is used in the hazardlib tests, not in the engine
def disaggregation(
        sources, site, imt, iml, gsim_by_trt, truncation_level,
        n_epsilons, mag_bin_width, dist_bin_width, coord_bin_width,
        source_filter=filters.nofilter, **kwargs):
    """
    Compute "Disaggregation" matrix representing conditional probability of an
    intensity mesaure type ``imt`` exceeding, at least once, an intensity
    measure level ``iml`` at a geographical location ``site``, given rupture
    scenarios classified in terms of:

    - rupture magnitude
    - Joyner-Boore distance from rupture surface to site
    - longitude and latitude of the surface projection of a rupture's point
      closest to ``site``
    - epsilon: number of standard deviations by which an intensity measure
      level deviates from the median value predicted by a GSIM, given the
      rupture parameters
    - rupture tectonic region type

    In other words, the disaggregation matrix allows to compute the probability
    of each scenario with the specified properties (e.g., magnitude, or the
    magnitude and distance) to cause one or more exceedences of a given hazard
    level.

    For more detailed information about the disaggregation, see for instance
    "Disaggregation of Seismic Hazard", Paolo Bazzurro, C. Allin Cornell,
    Bulletin of the Seismological Society of America, Vol. 89, pp. 501-520,
    April 1999.

    :param sources:
        Seismic source model, as for
        :mod:`PSHA <openquake.hazardlib.calc.hazard_curve>` calculator it
        should be an iterator of seismic sources.
    :param site:
        :class:`~openquake.hazardlib.site.Site` of interest to calculate
        disaggregation matrix for.
    :param imt:
        Instance of :mod:`intensity measure type <openquake.hazardlib.imt>`
        class.
    :param iml:
        Intensity measure level. A float value in units of ``imt``.
    :param gsim_by_trt:
        Tectonic region type to GSIM objects mapping.
    :param truncation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution.
    :param n_epsilons:
        Integer number of epsilon histogram bins in the result matrix.
    :param mag_bin_width:
        Magnitude discretization step, width of one magnitude histogram bin.
    :param dist_bin_width:
        Distance histogram discretization step, in km.
    :param coord_bin_width:
        Longitude and latitude histograms discretization step,
        in decimal degrees.
    :param source_filter:
        Optional source-site filter function. See
        :mod:`openquake.hazardlib.calc.filters`.

    :returns:
        A tuple of two items. First is itself a tuple of bin edges information
        for (in specified order) magnitude, distance, longitude, latitude,
        epsilon and tectonic region types.

        Second item is 6d-array representing the full disaggregation matrix.
        Dimensions are in the same order as bin edges in the first item
        of the result tuple. The matrix can be used directly by pmf-extractor
        functions.
    """
    trts = sorted(set(src.tectonic_region_type for src in sources))
    trt_num = dict((trt, i) for i, trt in enumerate(trts))
    rlzs_by_gsim = {gsim_by_trt[trt]: [0] for trt in trts}
    by_trt = groupby(sources, operator.attrgetter('tectonic_region_type'))
    bdata = {}
    sitecol = SiteCollection([site])
    imls = hdf5.ArrayWrapper(
        numpy.array([iml]), dict(imt=imt, poes_disagg=[None], rlzi=0))
    eps3 = _eps3(truncation_level, n_epsilons)
    for trt, srcs in by_trt.items():
        cmaker = ContextMaker(
            trt, rlzs_by_gsim,
            {'truncation_level': truncation_level,
             'maximum_distance': source_filter.integration_distance,
             'imtls': {str(imt): [iml]}})
        contexts.RuptureContext.temporal_occurrence_model = (
            srcs[0].temporal_occurrence_model)
        ctxs = cmaker.from_srcs(srcs, sitecol)
        bdata[trt] = _disaggregate(cmaker, sitecol, ctxs, imls, eps3)

    if sum(len(bd.mags) for bd in bdata.values()) == 0:
        warnings.warn(
            'No ruptures have contributed to the hazard at site %s'
            % site, RuntimeWarning)
        return None, None

    min_mag = min(bd.mags.min() for bd in bdata.values())
    max_mag = max(bd.mags.max() for bd in bdata.values())
    mag_bins = mag_bin_width * numpy.arange(
        int(numpy.floor(min_mag / mag_bin_width)),
        int(numpy.ceil(max_mag / mag_bin_width) + 1))

    min_dist = min(bd.dists.min() for bd in bdata.values())
    max_dist = max(bd.dists.max() for bd in bdata.values())
    dist_bins = dist_bin_width * numpy.arange(
        int(numpy.floor(min_dist / dist_bin_width)),
        int(numpy.ceil(max_dist / dist_bin_width) + 1))
    lon_bins, lat_bins = lon_lat_bins(site.location.x, site.location.y,
                                      max_dist, coord_bin_width)
    eps_bins = numpy.linspace(-truncation_level, truncation_level,
                              n_epsilons + 1)
    bin_edges = (mag_bins, dist_bins, lon_bins, lat_bins, eps_bins)
    matrix = numpy.zeros((len(mag_bins) - 1, len(dist_bins) - 1,
                          len(lon_bins) - 1, len(lat_bins) - 1,
                          len(eps_bins) - 1, len(trts)))
    for trt in bdata:
        mat6 = _build_disagg_matrix(bdata[trt], bin_edges)  # shape (..., P)
        matrix[..., trt_num[trt]] = mat6[..., 0]
    return bin_edges + (trts,), matrix


def mag_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude PMF.

    :returns:
        1d array, a histogram representing magnitude PMF.
    """
    nmags, ndists, nlons, nlats, neps = matrix.shape
    mag_pmf = numpy.zeros(nmags)
    for i in range(nmags):
        mag_pmf[i] = numpy.prod(
            [1. - matrix[i, j, k, l, m]
             for j in range(ndists)
             for k in range(nlons)
             for l in range(nlats)
             for m in range(neps)])
    return 1. - mag_pmf


def dist_pmf(matrix):
    """
    Fold full disaggregation matrix to distance PMF.

    :returns:
        1d array, a histogram representing distance PMF.
    """
    nmags, ndists, nlons, nlats, neps = matrix.shape
    dist_pmf = numpy.zeros(ndists)
    for j in range(ndists):
        dist_pmf[j] = numpy.prod(
            [1. - matrix[i, j, k, l, m]
             for i in range(nmags)
             for k in range(nlons)
             for l in range(nlats)
             for m in range(neps)])
    return 1. - dist_pmf


def trt_pmf(matrices):
    """
    Fold full disaggregation matrix to tectonic region type PMF.

    :param matrices:
        a matrix with T submatrices
    :returns:
        an array of T probabilities one per each tectonic region type
    """
    ntrts, nmags, ndists, nlons, nlats, neps = matrices.shape
    pmf = numpy.zeros(ntrts)
    for t in range(ntrts):
        pmf[t] = 1. - numpy.prod(
            [1. - matrices[t, i, j, k, l, m]
             for i in range(nmags)
             for j in range(ndists)
             for k in range(nlons)
             for l in range(nlats)
             for m in range(neps)])
    return pmf


def mag_dist_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / distance PMF.

    :returns:
        2d array. First dimension represents magnitude histogram bins,
        second one -- distance histogram bins.
    """
    nmags, ndists, nlons, nlats, neps = matrix.shape
    mag_dist_pmf = numpy.zeros((nmags, ndists))
    for i in range(nmags):
        for j in range(ndists):
            mag_dist_pmf[i, j] = numpy.prod(
                [1. - matrix[i, j, k, l, m]
                 for k in range(nlons)
                 for l in range(nlats)
                 for m in range(neps)])
    return 1. - mag_dist_pmf


def mag_dist_eps_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / distance / epsilon PMF.

    :returns:
        3d array. First dimension represents magnitude histogram bins,
        second one -- distance histogram bins, third one -- epsilon
        histogram bins.
    """
    nmags, ndists, nlons, nlats, neps = matrix.shape
    mag_dist_eps_pmf = numpy.zeros((nmags, ndists, neps))
    for i in range(nmags):
        for j in range(ndists):
            for m in range(neps):
                mag_dist_eps_pmf[i, j, m] = numpy.prod(
                    [1. - matrix[i, j, k, l, m]
                     for k in range(nlons)
                     for l in range(nlats)])
    return 1. - mag_dist_eps_pmf


def lon_lat_pmf(matrix):
    """
    Fold full disaggregation matrix to longitude / latitude PMF.

    :returns:
        2d array. First dimension represents longitude histogram bins,
        second one -- latitude histogram bins.
    """
    nmags, ndists, nlons, nlats, neps = matrix.shape
    lon_lat_pmf = numpy.zeros((nlons, nlats))
    for k in range(nlons):
        for l in range(nlats):
            lon_lat_pmf[k, l] = numpy.prod(
                [1. - matrix[i, j, k, l, m]
                 for i in range(nmags)
                 for j in range(ndists)
                 for m in range(neps)])
    return 1. - lon_lat_pmf


def lon_lat_trt_pmf(matrices):
    """
    Fold full disaggregation matrices to lon / lat / TRT PMF.

    :param matrices:
        a matrix with T submatrices
    :returns:
        3d array. First dimension represents longitude histogram bins,
        second one latitude histogram bins, third one trt histogram bins.
    """
    res = numpy.array([lon_lat_pmf(mat) for mat in matrices])
    return res.transpose(1, 2, 0)


def mag_lon_lat_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / longitude / latitude PMF.

    :returns:
        3d array. First dimension represents magnitude histogram bins,
        second one -- longitude histogram bins, third one -- latitude
        histogram bins.
    """
    nmags, ndists, nlons, nlats, neps = matrix.shape
    mag_lon_lat_pmf = numpy.zeros((nmags, nlons, nlats))
    for i in range(nmags):
        for k in range(nlons):
            for l in range(nlats):
                mag_lon_lat_pmf[i, k, l] = numpy.prod(
                    [1. - matrix[i, j, k, l, m]
                     for j in range(ndists)
                     for m in range(neps)])
    return 1. - mag_lon_lat_pmf


# this dictionary is useful to extract a fixed set of
# submatrices from the full disaggregation matrix
pmf_map = dict([
    ('Mag', mag_pmf),
    ('Dist', dist_pmf),
    ('TRT', trt_pmf),
    ('Mag_Dist', mag_dist_pmf),
    ('Mag_Dist_Eps', mag_dist_eps_pmf),
    ('Lon_Lat', lon_lat_pmf),
    ('Mag_Lon_Lat', mag_lon_lat_pmf),
    ('Lon_Lat_TRT', lon_lat_trt_pmf),
])
