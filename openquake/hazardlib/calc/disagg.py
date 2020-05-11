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

from openquake.hazardlib import contexts
from openquake.baselib import hdf5, performance
from openquake.baselib.general import AccumDict, groupby
from openquake.hazardlib.calc import filters
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.utils import (angular_distance, KM_TO_DEGREES,
                                           cross_idl)
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.gsim.base import (
    ContextMaker, get_mean_std, to_distribution_values)

BIN_NAMES = 'mag', 'dist', 'lon', 'lat', 'eps', 'trt'
BinData = collections.namedtuple('BinData', 'dists, lons, lats, pnes')


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
    edges = [mag_edges, dist_edges, lon_edges[0], lat_edges[0], eps_edges]
    shape = [len(edge) - 1 for edge in edges] + [len(trts)]
    shapedic = dict(zip(BIN_NAMES, shape))
    shapedic['N'] = len(sitecol)
    shapedic['M'] = len(oq.imtls)
    shapedic['P'] = len(oq.poes_disagg or (None,))
    shapedic['Z'] = Z
    return bin_edges + [trts], shapedic


def _eps3(truncation_level, n_epsilons):
    # NB: instantiating truncnorm is slow and calls the infamous "doccer"
    tn = scipy.stats.truncnorm(-truncation_level, truncation_level)
    eps = numpy.linspace(-truncation_level, truncation_level, n_epsilons + 1)
    eps_bands = tn.cdf(eps[1:]) - tn.cdf(eps[:-1])
    return tn, eps, eps_bands


# this is inside an inner loop
def disaggregate(mean_std, rups, imt, imls, eps3,
                 pne_mon=performance.Monitor()):
    # disaggregate (separate) PoE in different contributions
    U, P, E = len(rups), len(imls), len(eps3[2])
    bdata = BinData(dists=numpy.zeros(U), lons=numpy.zeros(U),
                    lats=numpy.zeros(U),  pnes=numpy.zeros((U, P, E)))
    with pne_mon:
        truncnorm, epsilons, eps_bands = eps3
        cum_bands = numpy.array([eps_bands[e:].sum() for e in range(E)] + [0])
        imls = to_distribution_values(imls, imt)  # shape P
        for u, rup in enumerate(rups):
            bdata.lons[u] = rup.lon
            bdata.lats[u] = rup.lat
            bdata.dists[u] = rup.rrup[0]
        for p, iml in enumerate(imls):
            lvls = (iml - mean_std[0]) / mean_std[1]
            survival = truncnorm.sf(lvls)
            bins = numpy.searchsorted(epsilons, lvls)
            for e, eps_band in enumerate(eps_bands):
                poes = _disagg_eps(survival, bins, e, eps_band, cum_bands)
                for u, rup in enumerate(rups):
                    bdata.pnes[u, p, e] = rup.get_probability_no_exceedance(
                        poes[u])
    return bdata


def _disagg_eps(survival, bins, e, eps_band, cum_bands):
    # disaggregate PoE of `iml` in different contributions,
    # each coming from ``epsilons`` distribution bins
    res = numpy.zeros(len(bins))
    res[bins <= e] = eps_band  # left bins
    inside = bins == e + 1  # inside bins
    res[inside] = survival[inside] - cum_bands[bins[inside]]
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


# this is fast
def build_disagg_matrix(bdata, bins):
    """
    :param bdata: a dictionary of probabilities of no exceedence
    :param bins: bin edges
    :returns:
        a 5D-matrix of shape (#distbins, #lonbins, #latbins, #epsbins, #poes)
    """
    dist_bins, lon_bins, lat_bins, eps_bins = bins
    dim1, dim2, dim3, dim4 = shape = [len(b) - 1 for b in bins]

    # find bin indexes of rupture attributes; bins are assumed closed
    # on the lower bound, and open on the upper bound, that is [ )
    # longitude values need an ad-hoc method to take into account
    # the 'international date line' issue
    # the 'minus 1' is needed because the digitize method returns the
    # index of the upper bound of the bin
    dists_idx = numpy.digitize(bdata.dists, dist_bins) - 1
    lons_idx = _digitize_lons(bdata.lons, lon_bins)
    lats_idx = numpy.digitize(bdata.lats, lat_bins) - 1

    # because of the way numpy.digitize works, values equal to the last bin
    # edge are associated to an index equal to len(bins) which is not a
    # valid index for the disaggregation matrix. Such values are assumed
    # to fall in the last bin
    dists_idx[dists_idx == dim1] = dim1 - 1
    lons_idx[lons_idx == dim2] = dim2 - 1
    lats_idx[lats_idx == dim3] = dim3 - 1
    U, P, E = bdata.pnes.shape
    mat5D = numpy.ones(shape + [P])
    for i_dist, i_lon, i_lat, pne in zip(
            dists_idx, lons_idx, lats_idx, bdata.pnes):
        mat5D[i_dist, i_lon, i_lat] *= pne.T  # shape E, P
    return 1. - mat5D


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


def get_mean_stdv(site1, ctxs, imt, gsim):
    """
    :param site1: site collection with a single site
    :param ctxs: a list of RuptureContexts with distances
    :param imt: Intensity Measure Type
    :param gsim: GMPE instance
    """
    U = len(ctxs)
    ms = numpy.zeros((2, U), numpy.float32)
    for u, ctx in enumerate(ctxs):
        if gsim.minimum_distance and ctx.rrup[0] < gsim.minimum_distance:
            ctx.rrup = numpy.float32([gsim.minimum_distance])
        ms[:, u] = get_mean_std(site1, ctx, ctx, [imt], [gsim]).reshape(2)
    return ms


def magbin_groups(rups, mag_bins):
    groups = [[] for _ in mag_bins[1:]]
    for rup in rups:
        magi = numpy.searchsorted(mag_bins, rup.mag) - 1
        groups[magi].append(rup)
    return groups


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
    bdata = {}  # by TRT
    sitecol = SiteCollection([site])
    imls = hdf5.ArrayWrapper(
        numpy.array([iml]), dict(imt=imt, poes_disagg=[None], rlzi=0))
    eps3 = _eps3(truncation_level, n_epsilons)

    rups = AccumDict(accum=[])
    cmaker = {}  # trt -> cmaker
    for trt, srcs in by_trt.items():
        contexts.RuptureContext.temporal_occurrence_model = (
            srcs[0].temporal_occurrence_model)
        cmaker[trt] = ContextMaker(
            trt, rlzs_by_gsim,
            {'truncation_level': truncation_level,
             'maximum_distance': source_filter.integration_distance,
             'imtls': {str(imt): [iml]}})
        rups[trt].extend(cmaker[trt].from_srcs(srcs, sitecol))
    min_mag = min(r.mag for rs in rups.values() for r in rs)
    max_mag = max(r.mag for rs in rups.values() for r in rs)
    mag_bins = mag_bin_width * numpy.arange(
        int(numpy.floor(min_mag / mag_bin_width)),
        int(numpy.ceil(max_mag / mag_bin_width) + 1))

    for trt in cmaker:
        gsim = gsim_by_trt[trt]
        for magi, ctxs in enumerate(magbin_groups(rups[trt], mag_bins)):
            mean_std = get_mean_stdv(sitecol, ctxs, imt, gsim)
            bdata[trt, magi] = disaggregate(mean_std, ctxs, imt, imls, eps3)

    if sum(len(bd.dists) for bd in bdata.values()) == 0:
        warnings.warn(
            'No ruptures have contributed to the hazard at site %s'
            % site, RuntimeWarning)
        return None, None

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
    for trt, magi in bdata:
        mat5 = build_disagg_matrix(bdata[trt, magi], bin_edges[1:])
        matrix[magi, ..., trt_num[trt]] = mat5[..., 0]  # shape (..., P)
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
