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
from openquake.baselib.performance import split_array
from openquake.hazardlib.calc import filters
from openquake.hazardlib.stats import truncnorm_sf
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.utils import (angular_distance, KM_TO_DEGREES,
                                           cross_idl)
from openquake.hazardlib.tom import get_pnes
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.gsim.base import to_distribution_values
from openquake.hazardlib.contexts import ContextMaker, FarAwayRupture

BIN_NAMES = 'mag', 'dist', 'lon', 'lat', 'eps', 'trt'
BinData = collections.namedtuple('BinData', 'dists, lons, lats, pnes')


def assert_same_shape(arrays):
    """
    Raises an AssertionError if the shapes are not consistent
    """
    shape = arrays[0].shape
    for arr in arrays[1:]:
        assert arr.shape == shape, (arr.shape, shape)


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


def build_bin_edges(oq, sitecol):
    """
    :returns: dictionary with (mag, dist, lon, lat, eps) edges
    """
    mag_bin_width = oq.mag_bin_width
    distance_bin_width = oq.distance_bin_width
    coordinate_bin_width = oq.coordinate_bin_width
    maximum_distance = oq.maximum_distance
    num_epsilon_bins = oq.num_epsilon_bins
    truncation_level = oq.truncation_level
    mags_by_trt = oq.mags_by_trt
    
    # build mag_edges
    mags = set()
    trts = []
    for trt, _mags in mags_by_trt.items():
        mags.update(float(mag) for mag in _mags)
        trts.append(trt)
    mags = sorted(mags)
    min_mag = mags[0]
    max_mag = mags[-1]
    n1 = int(numpy.floor(min_mag / mag_bin_width))
    n2 = int(numpy.ceil(max_mag / mag_bin_width))
    if n2 == n1 or max_mag >= round((mag_bin_width * n2), 3):
        n2 += 1
    mag_edges = mag_bin_width * numpy.arange(n1, n2+1)

    # build dist_edges
    maxdist = max(maximum_distance.max().values())
    dist_edges = distance_bin_width * numpy.arange(
        0, int(numpy.ceil(maxdist / distance_bin_width) + 1))

    # build lon_edges, lat_edges per sid
    lon_edges, lat_edges = {}, {}  # by sid
    for site in sitecol:
        loc = site.location
        lon_edges[site.id], lat_edges[site.id] = lon_lat_bins(
            loc.x, loc.y, maxdist, coordinate_bin_width)

    # sanity check: the shapes of the lon lat edges are consistent
    assert_same_shape(list(lon_edges.values()))
    assert_same_shape(list(lat_edges.values()))

    # build eps_edges
    eps_edges = numpy.linspace(
        -truncation_level, truncation_level, num_epsilon_bins + 1)

    return dict(mag=mag_edges, dist=dist_edges, lon=lon_edges, lat=lat_edges,
                eps=eps_edges)
    

def get_edges_shapedic(oq, sitecol, num_tot_rlzs):
    """
    :returns: (mag dist lon lat eps trt) edges and shape dictionary
    """
    assert oq.mags_by_trt
    trts = list(oq.mags_by_trt)

    if oq.rlz_index is None:
        Z = oq.num_rlzs_disagg or num_tot_rlzs
    else:
        Z = len(oq.rlz_index)

    edges = build_bin_edges(oq, sitecol)
    # override the computed edges with the explicit disagg_bin_edges
    for key, val in oq.disagg_bin_edges.items():
        if key in ('lon', 'lat'):
            edges[key] = {0: val}
        else:
            edges[key] = val
    shapedic = {}
    for name in BIN_NAMES:
        if name in ('lon', 'lat'):
            # taking the first, since the shape is the same for all sites
            shapedic[name] = len(edges[name][0]) - 1
        elif name == 'trt':
            shapedic[name] = len(trts)
        else:
            shapedic[name] = len(edges[name]) - 1
    shapedic['N'] = len(sitecol)
    shapedic['M'] = len(oq.imtls)
    shapedic['P'] = len(oq.poes_disagg or (None,))
    shapedic['Z'] = Z
    all_edges = [edges['mag'], edges['dist'], edges['lon'], edges['lat'],
                 edges['eps'], trts]
    return all_edges, shapedic


def calc_eps_bands(truncation_level, eps):
    # NB: instantiating truncnorm is slow and calls the infamous "doccer"
    tn = scipy.stats.truncnorm(-truncation_level, truncation_level)
    return tn.cdf(eps[1:]) - tn.cdf(eps[:-1])


DEBUG = AccumDict(accum=[])  # sid -> pnes.mean(), useful for debugging


# this is inside an inner loop
def _disaggregate(ctx, mea, std, cmaker, g, iml2dict, eps_bands,
                  bin_edges, epsstar=False):
    """
    :param ctx: a recarray of size U for a single site and magnitude bin
    :param mea: array of shape (G, M, U)
    :param std: array of shape (G, M, U)
    :param cmaker: a ContextMaker instance
    :param g: a gsim index
    :param iml2dict: a dictionary of arrays imt -> P
    :param eps_bands: an array of E elements obtained from the E+1 eps_edges
    :param bin_edges: a tuple of 5 bin edges (mag, dist, lon, lat, eps)
    :param epsstar: a boolean. When True, disaggregation contains eps* results
    :returns: a 7D-array of shape (D, Lo, La, E, M, P, Z)
    """
    # disaggregate (separate) PoE in different contributions
    # U - Number of contexts (i.e. ruptures)
    # E - Number of epsilon bins between lower and upper truncation
    # M - Number of IMTs
    # P - Number of PoEs in poes_disagg
    # Z - Number of realizations to consider
    epsilons = bin_edges[-1]
    U, E, M = len(ctx), len(eps_bands), len(iml2dict)
    imls = next(iter(iml2dict.values()))
    P = len(imls)

    # switch to logarithmic intensities
    iml2 = numpy.zeros((M, P))
    for m, (imt, imls) in enumerate(iml2dict.items()):
        # 0 values are converted into -inf
        iml2[m] = to_distribution_values(imls, imt)

    phi_b = cmaker.phi_b
    cum_bands = numpy.array([eps_bands[e:].sum() for e in range(E)] + [0])
    # Array with mean and total std values. Shape of this is:
    # U - Number of contexts (i.e. ruptures if there is a single site)
    # M - Number of IMTs
    # G - Number of gsims
    poes = numpy.zeros((U, E, M, P))
    pnes = numpy.ones((U, E, M, P))
    # Multi-dimensional iteration
    min_eps, max_eps = epsilons.min(), epsilons.max()
    for (m, p), iml in numpy.ndenumerate(iml2):
        if iml == -numpy.inf:  # zero hazard
            continue
        lvls = (iml - mea[g, m]) / std[g, m]
        # Find the index in the epsilons-bins vector where lvls (which are
        # epsilons) should be included.
        idxs = numpy.searchsorted(epsilons, lvls)
        # Now we split the epsilons into parts (one for each epsilon-bin larger
        # than lvls)
        if epsstar:
            ok = (lvls >= min_eps) & (lvls < max_eps)
            # The leftmost indexes are ruptures and epsilons
            poes[ok, idxs[ok] - 1, m, p] = truncnorm_sf(phi_b, lvls[ok])
        else:
            poes[:, :, m, p] = _disagg_eps(
                truncnorm_sf(phi_b, lvls), idxs, eps_bands, cum_bands)
    z0 = numpy.zeros(0)
    time_span = cmaker.tom.time_span
    for u, rec in enumerate(ctx):
        pnes[u] *= get_pnes(rec.occurrence_rate,
                            getattr(rec, 'probs_occur', z0),
                            poes[u], time_span)
    bindata = BinData(ctx.rrup, ctx.clon, ctx.clat, pnes)
    if len(bin_edges) == 1:  # disagg.disaggregation passes only eps_edges
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
    U, E, M, P = bdata.pnes.shape
    mat6D = numpy.ones(shape + [M, P])
    for i_dist, i_lon, i_lat, pne in zip(
            dists_idx, lons_idx, lats_idx, bdata.pnes):
        mat6D[i_dist, i_lon, i_lat] *= pne  # shape E, M, P
    return 1. - mat6D


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
    trts = sorted(set(src.tectonic_region_type for src in sources))
    trt_num = dict((trt, i) for i, trt in enumerate(trts))
    rlzs_by_gsim = {gsim_by_trt[trt]: [0] for trt in trts}
    by_trt = groupby(sources, operator.attrgetter('tectonic_region_type'))
    bdata = {}  # by trt, magi
    sitecol = SiteCollection([site])
    imls = numpy.array([iml])

    # Epsilon bins
    if 'eps' in bin_edges:
        eps_bins = bin_edges['eps']
        n_epsilons = len(eps_bins) - 1
    else:
        eps_bins = numpy.linspace(-truncation_level, truncation_level,
                                  n_epsilons + 1)
    eps_bands = calc_eps_bands(truncation_level, eps_bins)

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
    if 'mag' in bin_edges:
        mag_bins = bin_edges['mag']
    else:
        mags = numpy.array([r.mag for rs in rups.values() for r in rs])
        mag_bins = uniform_bins(mags.min(), mags.max(), mag_bin_width)

    # Compute disaggregation per TRT
    for trt, cm in cmaker.items():
        [ctx] = rups[trt]
        ctx.magi = numpy.searchsorted(mag_bins, ctx.mag) - 1
        for magi in numpy.unique(ctx.magi):
            ctxt = ctx[ctx.magi == magi]
            mea, std, _, _ = cm.get_mean_stds([ctxt], split_by_mag=True)
            bdata[trt, magi] = _disaggregate(
                ctxt, mea, std, cm, {imt: imls}, eps_bands, 0,
                [eps_bins], epsstar)

    if sum(len(bd.dists) for bd in bdata.values()) == 0:
        warnings.warn(
            f'No ruptures have contributed to the hazard at site {site}',
            RuntimeWarning)
        return None, None

    # Distance bins
    min_dist = min(bd.dists.min() for bd in bdata.values())
    max_dist = max(bd.dists.max() for bd in bdata.values())
    if 'dist' in bin_edges:
        dist_bins = bin_edges['dist']
    else:
        dist_bins = uniform_bins(min_dist, max_dist, dist_bin_width)

    # Lon, Lat bins
    if 'lon' in bin_edges and 'lat' in bin_edges:
        lon_bins = bin_edges['lon']
        lat_bins = bin_edges['lat']
    else:
        lon_bins, lat_bins = lon_lat_bins(site.location.x, site.location.y,
                                          max_dist, coord_bin_width)

    # Bin edges
    bin_edges = (mag_bins, dist_bins, lon_bins, lat_bins, eps_bins)
    matrix = numpy.zeros((len(mag_bins) - 1, len(dist_bins) - 1,
                          len(lon_bins) - 1, len(lat_bins) - 1,
                          len(eps_bins) - 1, len(trts)))  # 6D
    for trt, magi in bdata:
        mat6 = _build_disagg_matrix(bdata[trt, magi], bin_edges[1:])
        matrix[magi, ..., trt_num[trt]] = mat6[..., 0, 0]
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

# ####################### SourceSiteDisaggregator ############################ #

class SiteDisaggregator(object):
    """
    A class to perform single-site disaggregation
    """
    def __init__(self, ctx, sid, cmaker, bin_edges, g_by_z):
        self.ctx = ctx  # assume all in the same mag bin
        self.cmaker = cmaker
        # dist_bins, lon_bins, lat_bins, eps_bins
        self.bin_edges = (bin_edges[1],
                          bin_edges[2][sid],
                          bin_edges[3][sid],
                          bin_edges[4])
        self.g_by_z = g_by_z
        self.eps_bands = calc_eps_bands(
            cmaker.truncation_level, self.bin_edges[-1])
        mea, std, _, _ = cmaker.get_mean_stds([ctx], split_by_mag=True)
        if self.cmaker.src_mutex:
            # getting a context array and a weight for each source
            # NB: relies on ctx.weight having all equal weights, being
            # built as ctx['weight'] = src.mutex_weight in contexts.py
            self.ctxs = split_array(ctx, ctx.src_id)
            self.meas = split_array(mea, ctx.src_id)
            self.stds = split_array(std, ctx.src_id)
            self.weights = [ctx.weight[0] for ctx in self.ctxs]
        else:
            self.ctxs = [ctx]
            self.meas = [mea]
            self.stds = [std]
            self.weights = [1.]

    def disagg(self, iml3, epsstar):
        M, P, Z = iml3.shape
        shp = [len(b)-1 for b in self.bin_edges[:4]] + [M, P, Z]
        # 7D-matrix #disbins, #lonbins, #latbins, #epsbins, M, P, Z
        matrix = numpy.zeros(shp)
        for z in range(Z):
            # discard the z contributions coming from wrong
            # realizations: see the test disagg/case_2
            try:
                g = self.g_by_z[z]
            except KeyError:
                continue
            iml2 = dict(zip(self.cmaker.imts, iml3[:, :, z]))
            matrix[..., z] = self.disagg6D(g, iml2, epsstar)
        return matrix

    def disagg6D(self, g, imls_by_imt, epsstar):
        mats = []
        for ctx, mea, std in zip(self.ctxs, self.meas, self.stds):
            mat = _disaggregate(ctx, mea, std, self.cmaker, g, imls_by_imt,
                                self.eps_bands, self.bin_edges, epsstar)
            mats.append(mat)
        if len(mats) == 1:
            return mat
        return numpy.average(mats, weights=self.weights, axis=0)


class SourceSiteDisaggregator(object):
    """
    A class to perform disaggregations when there is a single source and
    a single site.
    """
    def __init__(self, src, site, cmaker):
        self.src = src
        if isinstance(site, Site):
            self.sitecol = SiteCollection([site])
        else:  # assume a length-1 site collection
            assert isinstance(site, SiteCollection), site
            assert len(site) == 1, site
            self.sitecol = site
        self.cmaker = cmaker
        assert cmaker.grp_id == src.grp_id, (cmaker.grp_id == src.grp_id)
        cmaker.oq.mags_by_trt = {src.tectonic_region_type: src.get_magstrs()}
        self.edges = build_bin_edges(cmaker.oq, self.sitecol)
        self.eps_bands = calc_eps_bands(
            cmaker.truncation_level, self.edges['eps'])

    def make_ctxs(self):
        """
        Build a list of contexts, one for each non-empty magnitude bin
        """
        ctxs = self.cmaker.from_srcs([self.src], self.sitecol)
        if not ctxs:
            raise FarAwayRupture
        elif len(ctxs) == 1:  # poissonian source
            ctx = ctxs[0]
        elif len(ctxs) == 2:  # nonpoissonian source
            ctx = ctxs[1]

        magi = numpy.searchsorted(self.edges['mag'], ctx.mag) - 1
        magi[magi == -1] = 0  # when the magnitude is on the edge
        idxs = numpy.argsort(magi)
        return split_array(ctx[idxs], magi[idxs])

    def disaggregate(self, ctx, imt, iml, rlz, epsstar=False):
        # for each z
        iml2dict = {imt: numpy.array([[iml]])}
        arr7D = _disaggregate(ctx, self.cmaker, self.g_by_z, iml2dict,
                              self.eps_bands, self.bin_edges, epsstar)
        return arr7D[..., 0, 0, 0]  # 4D array of shape (D, Lo, La, E)

    def disagg_dist_eps(self, ctx, imt, iml, rlz, epsstar=False):
        mat4 = self.disaggregate(ctx, imt, iml, rlz, epsstar)
        return mag_dist_eps_pmf(mat4)  # shape (D, E)
