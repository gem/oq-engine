# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
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
import numpy
import scipy.stats

from openquake.hazardlib import pmf, contexts, const
from openquake.baselib.performance import Monitor
from openquake.baselib.hdf5 import ArrayWrapper
from openquake.baselib.general import pack, groupby, AccumDict
from openquake.hazardlib.calc import filters
from openquake.hazardlib.geo.geodetic import npoints_between
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.utils import cross_idl
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.gsim.base import ContextMaker


def disaggregate(cmaker, sitecol, rupdata, iml2, truncnorm, epsilons,
                 monitor=Monitor()):
    """
    Disaggregate (separate) PoE in different contributions.

    :param cmaker: a ContextMaker instance
    :param sitecol: a SiteCollection with N=1 site
    :param ruptures: an iterator over ruptures with the same TRT
    :param iml2: a 2D array of IMLs of shape (M, P)
    :param truncnorm: an instance of scipy.stats.truncnorm
    :param epsilons: the epsilon bins
    :param monitor: a Monitor instance
    :returns:
        an AccumDict with keys (poe, imt, rlzi) and mags, dists, lons, lats
    """
    assert len(sitecol) == 1, sitecol
    acc = AccumDict(accum=[], mags=[], dists=[], lons=[], lats=[])
    try:
        gsim = cmaker.gsim_by_rlzi[iml2.rlzi]
    except KeyError:
        return acc
    pne_mon = monitor('disaggregate_pne', measuremem=False)
    [sid] = sitecol.sids
    acc['mags'] = rupdata['mag']
    acc['lons'] = rupdata['lon'][:, sid]
    acc['lats'] = rupdata['lat'][:, sid]
    acc['dists'] = dists = rupdata[cmaker.filter_distance][:, sid]
    if gsim.minimum_distance:
        dists[dists < gsim.minimum_distance] = gsim.minimum_distance
    # compute epsilon bin contributions only once
    eps_bands = truncnorm.cdf(epsilons[1:]) - truncnorm.cdf(epsilons[:-1])
    for rec in rupdata:
        rctx = contexts.RuptureContext(rec)
        dctx = contexts.DistancesContext(
            (param, rec[param][[sid]])
            for param in cmaker.REQUIRES_DISTANCES
        ).roundup(gsim.minimum_distance)
        for m, imt in enumerate(iml2.imts):
            for p, poe in enumerate(iml2.poes_disagg):
                iml = iml2[m, p]
                with pne_mon:
                    pne = disaggregate_pne(
                        gsim, rctx, sitecol, dctx, imt, iml,
                        truncnorm, epsilons, eps_bands)
                acc[poe, str(imt), iml2.rlzi].append(pne)
    return acc


# in practice this is always called with a single site
def disaggregate_pne(gsim, rupture, sctx, dctx, imt, iml, truncnorm,
                     epsilons, eps_bands):
    """
    Disaggregate (separate) PoE of ``iml`` in different contributions
    each coming from ``epsilons`` distribution bins.

    Other parameters are the same as for `gsim.get_poes`, with
    differences that ``truncation_level`` is required to be positive.

    :returns:
        Contribution to probability of exceedance of ``iml`` coming
        from different sigma bands in the form of a 2D numpy array of
        probabilities with shape (n_sites, n_epsilons)
    """
    # compute mean and standard deviations
    mean, [stddev] = gsim.get_mean_and_stddevs(sctx, rupture, dctx, imt,
                                               [const.StdDev.TOTAL])

    # compute iml value with respect to standard (mean=0, std=1)
    # normal distributions
    [lvl] = (gsim.to_distribution_values(iml) - mean) / stddev

    # take the minimum epsilon larger than standard_iml
    bin = numpy.searchsorted(epsilons, lvl)
    n_epsilons = len(epsilons) - 1
    if bin == 0:
        poes = eps_bands
    elif bin > n_epsilons:
        poes = numpy.zeros(n_epsilons)
    else:
        # for other cases (when ``lvl`` falls somewhere in the
        # histogram):
        poes = numpy.concatenate([
            # take zeros for bins that are on the left hand side
            # from the bin ``lvl`` falls into,
            numpy.zeros(bin - 1),
            # ... area of the portion of the bin containing ``lvl``
            # (the portion is limited on the left hand side by
            # ``lvl`` and on the right hand side by the bin edge),
            [truncnorm.sf(lvl) - eps_bands[bin:].sum()],
            # ... and all bins on the right go unchanged.
            eps_bands[bin:]])
    return rupture.get_probability_no_exceedance(poes)


# in practice this is always called with a single site
def collect_bin_data(rupdata, sitecol, cmaker, iml3,
                     truncation_level, n_epsilons, monitor=Monitor()):
    """
    :param rupdata: array of ruptures
    :param sitecol: a SiteCollection instance with a single site
    :param cmaker: a ContextMaker instance
    :param iml3: an ArrayWrapper of intensities of shape (R, M, P)
    :param truncation_level: the truncation level
    :param n_epsilons: the number of epsilons
    :param monitor: a Monitor instance
    :returns: a dictionary (poe, imt, rlzi) -> probabilities of shape (N, E)
    """
    # NB: instantiating truncnorm is slow and calls the infamous "doccer"
    tn = scipy.stats.truncnorm(-truncation_level, truncation_level)
    eps = numpy.linspace(-truncation_level, truncation_level, n_epsilons + 1)
    acc = disaggregate(cmaker, sitecol, rupdata, iml3, tn, eps, monitor)
    return pack(acc, 'mags dists lons lats'.split())


def lon_lat_bins(bb, coord_bin_width):
    """
    Define bin edges for disaggregation histograms.

    Given bins data as provided by :func:`collect_bin_data`, this function
    finds edges of histograms, taking into account maximum and minimum values
    of magnitude, distance and coordinates as well as requested sizes/numbers
    of bins.
    """
    west, south, east, north = bb
    west = numpy.floor(west / coord_bin_width) * coord_bin_width
    east = numpy.ceil(east / coord_bin_width) * coord_bin_width
    lon_extent = get_longitudinal_extent(west, east)
    lon_bins, _, _ = npoints_between(
        west, 0, 0, east, 0, 0,
        numpy.round(lon_extent / coord_bin_width + 1))
    lat_bins = coord_bin_width * numpy.arange(
        int(numpy.floor(south / coord_bin_width)),
        int(numpy.ceil(north / coord_bin_width) + 1))
    return lon_bins, lat_bins


def get_bins(bin_edges, sid):
    """
    :returns: mags, dists, lons, lats, eps for the given sid
    """
    mag_bins, dist_bins, lon_bins, lat_bins, eps_bins = bin_edges
    return mag_bins, dist_bins, lon_bins[sid], lat_bins[sid], eps_bins


# this is fast
def build_disagg_matrix(bdata, bins, mon=Monitor):
    """
    :param bdata: a dictionary of probabilities of no exceedence
    :param bins: bin edges
    :param mon: a Monitor instance
    :returns: a dictionary key -> matrix|pmf for each key in bdata
    """
    with mon('build_disagg_matrix'):
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

        out = {}
        num_zeros = 0
        for k, pnes in bdata.items():
            # pnes has shape (U, 1, E)
            if pnes.sum() == pnes.size:  # all pnes are 1
                num_zeros += 1
                continue  # zero matrices are not transferred
            mat = numpy.ones(shape)
            for i_mag, i_dist, i_lon, i_lat, pne in zip(
                    mags_idx, dists_idx, lons_idx, lats_idx, pnes):
                mat[i_mag, i_dist, i_lon, i_lat] *= pne
            out[k] = 1. - mat
    return out


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
        source_filter=filters.nofilter, filter_distance='rjb'):
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
    iml2 = ArrayWrapper(numpy.array([[iml]]),
                        dict(imts=[imt], poes_disagg=[None], rlzi=0))
    for trt, srcs in by_trt.items():
        cmaker = ContextMaker(
            trt, rlzs_by_gsim, source_filter.integration_distance,
            {'filter_distance': filter_distance})
        contexts.RuptureContext.temporal_occurrence_model = (
            srcs[0].temporal_occurrence_model)
        rupdata = contexts.RupData(cmaker, sitecol).from_srcs(srcs)
        bdata[trt] = collect_bin_data(
            rupdata, sitecol, cmaker, iml2, truncation_level, n_epsilons)
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

    bb = (min(bd.lons.min() for bd in bdata.values()),
          min(bd.lats.min() for bd in bdata.values()),
          max(bd.lons.max() for bd in bdata.values()),
          max(bd.lats.max() for bd in bdata.values()))
    lon_bins, lat_bins = lon_lat_bins(bb, coord_bin_width)

    eps_bins = numpy.linspace(-truncation_level, truncation_level,
                              n_epsilons + 1)

    bin_edges = (mag_bins, dist_bins, lon_bins, lat_bins, eps_bins)
    matrix = numpy.zeros((len(mag_bins) - 1, len(dist_bins) - 1,
                          len(lon_bins) - 1, len(lat_bins) - 1,
                          len(eps_bins) - 1, len(trts)))
    for trt in bdata:
        dic = build_disagg_matrix(bdata[trt], bin_edges)
        if dic:  # (poe, imt, rlzi) -> matrix
            [mat] = dic.values()
            matrix[..., trt_num[trt]] = mat
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
