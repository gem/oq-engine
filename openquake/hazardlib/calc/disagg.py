# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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
from functools import partial
import numpy
import scipy.stats

from openquake.baselib.general import AccumDict, groupby, pprod
from openquake.hazardlib.calc import filters
from openquake.hazardlib.stats import truncnorm_sf
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.utils import (angular_distance, KM_TO_DEGREES,
                                           cross_idl)
from openquake.hazardlib.tom import get_pnes
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.gsim.base import to_distribution_values
from openquake.hazardlib.contexts import ContextMaker

BIN_NAMES = 'mag', 'dist', 'lon', 'lat', 'eps', 'trt'
BinData = collections.namedtuple('BinData', 'dists, lons, lats, pnes')


def assert_same_shape(arrays):
    """
    Raises an AssertionError if the shapes are not consistent
    """
    shape = arrays[0].shape
    for arr in arrays[1:]:
        assert arr.shape == shape, (arr.shape, shape)


def get_edges_shapedic(oq, sitecol, mags_by_trt, num_tot_rlzs):
    """
    :returns: (mag dist lon lat eps trt) edges and shape dictionary
    """
    assert mags_by_trt
    tl = oq.truncation_level
    if oq.rlz_index is None:
        Z = oq.num_rlzs_disagg or num_tot_rlzs
    else:
        Z = len(oq.rlz_index)

    # build mag_edges
    mags = set()
    trts = []
    for trt, _mags in mags_by_trt.items():
        mags.update(float(mag) for mag in _mags)
        trts.append(trt)
    mags = sorted(mags)
    min_mag = mags[0]
    max_mag = mags[-1]

    # build _edges
    if 'mag' in oq.disagg_bin_edges:
        mag_edges = oq.disagg_bin_edges.get('mag')
    else:
        n1 = int(numpy.floor(min_mag / oq.mag_bin_width))
        n2 = int(numpy.ceil(max_mag / oq.mag_bin_width))
        if n2 == n1 or max_mag >= round((oq.mag_bin_width * n2), 3):
            n2 += 1
        mag_edges = oq.mag_bin_width * numpy.arange(n1, n2+1)

    # build dist_edges
    maxdist = max(oq.maximum_distance.max().values())
    if 'dist' in oq.disagg_bin_edges:
        dist_edges = oq.disagg_bin_edges['dist']
    else:
        dist_edges = oq.distance_bin_width * numpy.arange(
            0, int(numpy.ceil(maxdist / oq.distance_bin_width) + 1))

    # build eps_edges
    if 'eps' in oq.disagg_bin_edges:
        eps_edges = oq.disagg_bin_edges['eps']
    else:
        eps_edges = numpy.linspace(-tl, tl, oq.num_epsilon_bins + 1)

    # build lon_edges, lat_edges per sid
    lon_edges, lat_edges = {}, {}  # by sid
    for site in sitecol:
        if 'lon' in oq.disagg_bin_edges and 'lat' in oq.disagg_bin_edges:
            lon_edges[site.id] = oq.disagg_bin_edges['lon']
            lat_edges[site.id] = oq.disagg_bin_edges['lat']
        else:
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


def _eps3(truncation_level, eps):
    # NB: instantiating truncnorm is slow and calls the infamous "doccer"
    tn = scipy.stats.truncnorm(-truncation_level, truncation_level)
    eps_bands = tn.cdf(eps[1:]) - tn.cdf(eps[:-1])
    return tn, eps, eps_bands


DEBUG = AccumDict(accum=[])  # sid -> pnes.mean(), useful for debugging


# this is inside an inner loop
def disaggregate(ctx, cmaker, g_by_z, iml2dict, eps3, sid=0, bin_edges=(),
                 epsstar=False):
    """
    :param ctx: a recarray of size U for a single site and magnitude bin
    :param cmaker: a ContextMaker instance
    :param g_by_z: an array of gsim indices
    :param iml2dict: a dictionary of arrays imt -> (P, Z)
    :param eps3: a triplet (truncnorm, epsilons, eps_bands)
    :param sid: the site ID
    :param bin_edges: a tuple of bin edges
    :param epsstar: a boolean. When True, disaggregation contains eps* results
    """
    # disaggregate (separate) PoE in different contributions
    # U - Number of contexts (i.e. ruptures)
    # E - Number of epsilon bins between lower and upper truncation
    # M - Number of IMTs
    # P - Number of PoEs in poes_disagg
    # Z - Number of realizations to consider
    U, E, M = len(ctx), len(eps3[2]), len(iml2dict)
    iml2 = next(iter(iml2dict.values()))
    P, Z = iml2.shape

    # switch to logarithmic intensities
    iml3 = numpy.zeros((M, P, Z))
    for m, (imt, iml2) in enumerate(iml2dict.items()):
        # 0 values are converted into -inf
        iml3[m] = to_distribution_values(iml2, imt)

    phi_b = cmaker.phi_b
    truncnorm, epsilons, eps_bands = eps3
    cum_bands = numpy.array([eps_bands[e:].sum() for e in range(E)] + [0])
    # Array with mean and total std values. Shape of this is:
    # U - Number of contexts (i.e. ruptures if there is a single site)
    # M - Number of IMTs
    # G - Number of gsims
    mean_std = cmaker.get_mean_stds([ctx], split_by_mag=True)[:2]
    # shape (2, G, M, U)
    poes = numpy.zeros((U, E, M, P, Z))
    pnes = numpy.ones((U, E, M, P, Z))
    # Multi-dimensional iteration
    min_eps, max_eps = epsilons.min(), epsilons.max()
    for (m, p, z), iml in numpy.ndenumerate(iml3):
        if iml == -numpy.inf:  # zero hazard
            continue
        # discard the z contributions coming from wrong realizations: see
        # the test disagg/case_2
        try:
            g = g_by_z[z]
        except KeyError:
            continue
        lvls = (iml - mean_std[0, g, m]) / mean_std[1, g, m]
        # Find the index in the epsilons-bins vector where lvls (which are
        # epsilons) should be included.
        idxs = numpy.searchsorted(epsilons, lvls)
        # Now we split the epsilon into parts (one for each epsilon-bin larger
        # than lvls)
        if epsstar:
            iii = (lvls >= min_eps) & (lvls < max_eps)
            # The leftmost indexes are ruptures and epsilons
            poes[iii, idxs[iii]-1, m, p, z] = truncnorm_sf(phi_b, lvls[iii])
        else:
            poes[:, :, m, p, z] = _disagg_eps(
                truncnorm_sf(phi_b, lvls), idxs, eps_bands, cum_bands)
    z0 = numpy.zeros(0)
    time_span = cmaker.tom.time_span
    for u, rec in enumerate(ctx):
        pnes[u] *= get_pnes(rec.occurrence_rate,
                            getattr(rec, 'probs_occur', z0),
                            poes[u], time_span)
    bindata = BinData(ctx.rrup, ctx.clon, ctx.clat, pnes)
    if not bin_edges:
        return bindata
    return _build_disagg_matrix(bindata, bin_edges)


def _disagg_eps(survival, bins, eps_bands, cum_bands):
    # disaggregate PoE of `iml` in different contributions,
    # each coming from ``epsilons`` distribution bins
    res = numpy.zeros((len(bins), len(eps_bands)))
    for e, eps_band in enumerate(eps_bands):
        res[bins <= e, e] = eps_band  # left bins
        inside = bins == e + 1  # inside bins
        res[inside, e] = survival[inside] - cum_bands[bins[inside]]
    return res  # shape (U, E)


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
    EPS = .001  # avoid discarding the last edgebdata.pnes.shape
    lon_bins = lon + numpy.arange(-delta_lon, delta_lon + EPS,
                                  delta_lon / nbins)
    lat_bins = lat + numpy.arange(-delta_lat, delta_lat + EPS,
                                  delta_lat / nbins)
    if cross_idl(*lon_bins):
        lon_bins %= 360
    return lon_bins, lat_bins


# this is fast
def _build_disagg_matrix(bdata, bins):
    """
    :param bdata: a dictionary of probabilities of no exceedence
    :param bins: bin edges
    :returns:
        a 7D-matrix of shape (#distbins, #lonbins, #latbins, #epsbins, M, P, Z)
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
    U, E, M, P, Z = bdata.pnes.shape
    mat7D = numpy.ones(shape + [M, P, Z])
    for i_dist, i_lon, i_lat, pne in zip(
            dists_idx, lons_idx, lats_idx, bdata.pnes):
        mat7D[i_dist, i_lon, i_lat] *= pne  # shape E, M, P, Z
    return 1. - mat7D


def uniform_bins(min_value, max_value, bin_width):
    """
    Returns an array of bins including all values:

    >>> uniform_bins(1, 10, 1.)
    array([ 1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10.])
    >>> uniform_bins(1, 10, 1.1)
    array([ 0. ,  1.1,  2.2,  3.3,  4.4,  5.5,  6.6,  7.7,  8.8,  9.9, 11. ])
    """
    return bin_width * numpy.arange(
        int(numpy.floor(min_value/ bin_width)),
        int(numpy.ceil(max_value / bin_width) + 1))


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
        idx = numpy.zeros_like(lons, dtype=int)
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
        n_epsilons=None, mag_bin_width=None, dist_bin_width=None,
        coord_bin_width=None, source_filter=filters.nofilter,
        epsstar=False, bin_edges={}, **kwargs):
    """
    Compute "Disaggregation" matrix representing conditional probability of an
    intensity measure type ``imt`` exceeding, at least once, an intensity
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
    :param epsstar:
        A boolean. When true disaggregations results including epsilon are
        in terms of epsilon star rather then epsilon.
    :param bin_edges:
        Bin edges provided by the users. These override the ones automatically
        computed by the OQ Engine.
    :returns:
        A tuple of two items. First is itself a tuple of bin edges information
        for (in specified order) magnitude, distance, longitude, latitude,
        epsilon and tectonic region types.

        Second item is 6d-array representing the full disaggregation matrix.
        Dimensions are in the same order as bin edges in the first item
        of the result tuple. The matrix can be used directly by pmf-extractor
        functions.
    """
    bine = bin_edges
    trts = sorted(set(src.tectonic_region_type for src in sources))
    trt_num = dict((trt, i) for i, trt in enumerate(trts))
    rlzs_by_gsim = {gsim_by_trt[trt]: [0] for trt in trts}
    by_trt = groupby(sources, operator.attrgetter('tectonic_region_type'))
    bdata = {}  # by trt, magi
    sitecol = SiteCollection([site])
    iml2 = numpy.array([[iml]])

    # Epsilon bins
    if 'eps' in bine:
        eps_bins = bine['eps']
        n_epsilons = len(eps_bins) - 1
    else:
        eps_bins = numpy.linspace(-truncation_level, truncation_level,
                                  n_epsilons + 1)
    eps3 = _eps3(truncation_level, eps_bins)

    # Create contexts
    rups = AccumDict(accum=[])
    cmaker = {}  # trt -> cmaker
    for trt, srcs in by_trt.items():
        cmaker[trt] = cm = ContextMaker(
            trt, rlzs_by_gsim,
            {'truncation_level': truncation_level,
             'maximum_distance': source_filter.integration_distance(trt),
             'imtls': {str(imt): [iml]}})
        cm.tom = srcs[0].temporal_occurrence_model
        rups[trt].extend(cm.from_srcs(srcs, sitecol))

    # Set the magnitude bins
    if 'mag' in bine:
        mag_bins = bine['mag']
    else:
        mags = numpy.array([r.mag for rs in rups.values() for r in rs])
        mag_bins = uniform_bins(mags.min(), mags.max(), mag_bin_width)

    # Compute disaggregation per TRT
    for trt, cm in cmaker.items():
        [ctx] = rups[trt]
        ctx.magi = numpy.searchsorted(mag_bins, ctx.mag) - 1
        for magi in numpy.unique(ctx.magi):
            bdata[trt, magi] = disaggregate(
                ctx[ctx.magi == magi], cm, [0],
                {imt: iml2}, eps3, epsstar=epsstar)

    if sum(len(bd.dists) for bd in bdata.values()) == 0:
        warnings.warn(
            f'No ruptures have contributed to the hazard at site {site}',
            RuntimeWarning)
        return None, None

    # Distance bins
    min_dist = min(bd.dists.min() for bd in bdata.values())
    max_dist = max(bd.dists.max() for bd in bdata.values())
    if 'dist' in bine:
        dist_bins = bine['dist']
    else:
        dist_bins = uniform_bins(min_dist, max_dist, dist_bin_width)

    # Lon, Lat bins
    if 'lon' in bine and 'lat' in bine:
        lon_bins = bine['lon']
        lat_bins = bine['lat']
    else:
        lon_bins, lat_bins = lon_lat_bins(site.location.x, site.location.y,
                                          max_dist, coord_bin_width)

    # Bin edges
    bin_edges = (mag_bins, dist_bins, lon_bins, lat_bins, eps_bins)
    matrix = numpy.zeros((len(mag_bins) - 1, len(dist_bins) - 1,
                          len(lon_bins) - 1, len(lat_bins) - 1,
                          len(eps_bins) - 1, len(trts)))  # 6D
    for trt, magi in bdata:
        mat7 = _build_disagg_matrix(bdata[trt, magi], bin_edges[1:])
        matrix[magi, ..., trt_num[trt]] = mat7[..., 0, 0, 0]
    return bin_edges + (trts,), matrix


MAG, DIS, LON, LAT, EPS = 0, 1, 2, 3, 4

mag_pmf = partial(pprod, axis=(DIS, LON, LAT, EPS))
dist_pmf = partial(pprod, axis=(MAG, LON, LAT, EPS))
mag_dist_pmf = partial(pprod, axis=(LON, LAT, EPS))
mag_dist_eps_pmf = partial(pprod, axis=(LON, LAT))
lon_lat_pmf = partial(pprod, axis=(DIS, MAG, EPS))
mag_lon_lat_pmf = partial(pprod, axis=(DIS, EPS))
trt_pmf = partial(pprod, axis=(1, 2, 3, 4, 5))
mag_dist_trt_pmf = partial(pprod, axis=(3, 4, 5))
mag_dist_trt_eps_pmf = partial(pprod, axis=(3, 4))
# applied on matrix TRT MAG DIS LON LAT EPS


def lon_lat_trt_pmf(matrices):
    """
    Fold full disaggregation matrices to lon / lat / TRT PMF.

    :param matrices:
        a matrix with T submatrices
    :returns:
        4d array. First dimension represents longitude histogram bins,
        second one latitude histogram bins, third one trt histogram bins,
        last dimension is the z index, associatd to the realization.
    """
    res = numpy.array([lon_lat_pmf(mat) for mat in matrices])
    return res.transpose(1, 2, 0, 3)


# this dictionary is useful to extract a fixed set of
# submatrices from the full disaggregation matrix
pmf_map = dict([
    ('Mag', mag_pmf),
    ('Dist', dist_pmf),
    ('TRT', trt_pmf),
    ('Mag_Dist', mag_dist_pmf),
    ('Mag_Dist_Eps', mag_dist_eps_pmf),
    ('Mag_Dist_TRT', mag_dist_trt_pmf),
    ('Mag_Dist_TRT_Eps', mag_dist_trt_eps_pmf),
    ('Lon_Lat', lon_lat_pmf),
    ('Mag_Lon_Lat', mag_lon_lat_pmf),
    ('Lon_Lat_TRT', lon_lat_trt_pmf),
])
