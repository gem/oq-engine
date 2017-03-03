# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
from __future__ import division
import sys
import numpy
import warnings
import collections

from openquake.baselib.python3compat import raise_, range
from openquake.hazardlib.calc import filters
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.geo.geodetic import npoints_between
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.utils import get_spherical_bounding_box, cross_idl
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.gsim.base import ContextMaker

# a 6-uple containing float 4 arrays mags, dists, lons, lats,
# 1 int array trts and a list of dictionaries pnes
BinData = collections.namedtuple(
    'BinData', 'mags, dists, lons, lats, trts, pnes')


# yield (rlzi, poe, imt), (iml, pne)
def _disagg(iml, poes, curve_poes, imls, gsim, rupture, rlzi, imt, imt_str,
            sctx, rctx, dctx, truncation_level, n_epsilons, disagg_poe):
    if iml is None:  # compute the IMLs from the given poes
        for poe in poes:
            iml = numpy.interp(poe, curve_poes, imls)
            with disagg_poe:
                [poes_given_rup_eps] = gsim.disaggregate_poe(
                    sctx, rctx, dctx, imt, iml, truncation_level, n_epsilons)
            pne = rupture.get_probability_no_exceedance(poes_given_rup_eps)
            yield (rlzi, poe, imt_str), (iml, pne)
    else:  # there is a single IML provided by the user; compute the poe
        poe = numpy.interp(iml, imls, curve_poes)
        with disagg_poe:
            [poes_given_rup_eps] = gsim.disaggregate_poe(
                sctx, rctx, dctx, imt, iml, truncation_level, n_epsilons)
        pne = rupture.get_probability_no_exceedance(poes_given_rup_eps)
        yield (rlzi, round(poe, 4), imt_str), (iml, pne)


def _collect_bins_data(trt_num, sources, site, curves, src_group_id,
                       rlzs_assoc, gsims, imtls, poes, truncation_level,
                       n_epsilons, iml_disagg, mon):
    # returns a BinData instance
    sitecol = SiteCollection([site])
    mags = []
    dists = []
    lons = []
    lats = []
    trts = []
    pnes = collections.defaultdict(list)
    sitemesh = sitecol.mesh
    make_ctxt = mon('making contexts', measuremem=False)
    disagg_poe = mon('disaggregate_poe', measuremem=False)
    cmaker = ContextMaker(gsims)
    for source in sources:
        try:
            tect_reg = trt_num[source.tectonic_region_type]
            for rupture in source.iter_ruptures():
                with make_ctxt:
                    try:
                        sctx, rctx, dctx = cmaker.make_contexts(
                            sitecol, rupture)
                    except filters.FarAwayRupture:
                        continue
                # extract rupture parameters of interest
                mags.append(rupture.mag)
                dists.append(dctx.rjb[0])  # single site => single distance
                [closest_point] = rupture.surface.get_closest_points(sitemesh)
                lons.append(closest_point.longitude)
                lats.append(closest_point.latitude)
                trts.append(tect_reg)
                # a dictionary rlz.id, poe, imt_str -> (iml, prob_no_exceed)
                for gsim in gsims:
                    gs = str(gsim)
                    for imt_str, imls in imtls.items():
                        imt = from_string(imt_str)
                        imls = numpy.array(imls[::-1])
                        for rlz in rlzs_assoc[src_group_id, gs]:
                            rlzi = rlz.ordinal
                            iml = iml_disagg.get(imt_str)
                            curve_poes = curves[rlzi, imt_str][::-1]
                            for k, v in _disagg(
                                    iml, poes, curve_poes, imls, gsim, rupture,
                                    rlzi, imt, imt_str, sctx, rctx, dctx,
                                    truncation_level, n_epsilons, disagg_poe):
                                pnes[k].append(v)
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, err)
            raise_(etype, msg, tb)

    return BinData(numpy.array(mags, float),
                   numpy.array(dists, float),
                   numpy.array(lons, float),
                   numpy.array(lats, float),
                   numpy.array(trts, int),
                   pnes)


def disaggregation(
        sources, site, imt, iml, gsims, truncation_level,
        n_epsilons, mag_bin_width, dist_bin_width, coord_bin_width,
        source_site_filter=filters.source_site_noop_filter):
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
    :param gsims:
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
    :param source_site_filter:
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
    bins_data = _collect_bins_data_old(sources, site, imt, iml, gsims,
                                       truncation_level, n_epsilons,
                                       source_site_filter)
    if all(len(x) == 0 for x in bins_data):
        # No ruptures have contributed to the hazard level at this site.
        warnings.warn(
            'No ruptures have contributed to the hazard at site %s'
            % site,
            RuntimeWarning
        )
        return None, None

    bin_edges = _define_bins(bins_data, mag_bin_width, dist_bin_width,
                             coord_bin_width, truncation_level, n_epsilons)
    diss_matrix = _arrange_data_in_bins(bins_data, bin_edges)
    return bin_edges, diss_matrix


# TODO: remove the duplication
def _collect_bins_data_old(sources, site, imt, iml, gsims,
                           truncation_level, n_epsilons,
                           source_site_filter=filters.source_site_noop_filter):
    """
    Extract values of magnitude, distance, closest point, tectonic region
    types and PoE distribution.

    This method processes the source model (generates ruptures) and collects
    all needed parameters to arrays. It also defines tectonic region type
    bins sequence.
    """
    mags = []
    dists = []
    lons = []
    lats = []
    tect_reg_types = []
    probs_no_exceed = []
    sitecol = SiteCollection([site])
    sitemesh = sitecol.mesh

    _next_trt_num = 0
    trt_nums = {}
    # here we ignore filtered site collection because either it is the same
    # as the original one (with one site), or the source/rupture is filtered
    # out and doesn't show up in the filter's output
    for src_idx, (source, s_sites) in \
            enumerate(source_site_filter(sources, sitecol)):
        try:
            tect_reg = source.tectonic_region_type
            gsim = gsims[tect_reg]
            cmaker = ContextMaker([gsim])
            if tect_reg not in trt_nums:
                trt_nums[tect_reg] = _next_trt_num
                _next_trt_num += 1
            tect_reg = trt_nums[tect_reg]

            for rupture in source.iter_ruptures():
                # extract rupture parameters of interest
                mags.append(rupture.mag)
                [jb_dist] = rupture.surface.get_joyner_boore_distance(sitemesh)
                dists.append(jb_dist)
                [closest_point] = rupture.surface.get_closest_points(sitemesh)
                lons.append(closest_point.longitude)
                lats.append(closest_point.latitude)
                tect_reg_types.append(tect_reg)

                # compute conditional probability of exceeding iml given
                # the current rupture, and different epsilon level, that is
                # ``P(IMT >= iml | rup, epsilon_bin)`` for each of epsilon bins
                sctx, rctx, dctx = cmaker.make_contexts(sitecol, rupture)
                [poes_given_rup_eps] = gsim.disaggregate_poe(
                    sctx, rctx, dctx, imt, iml, truncation_level, n_epsilons
                )

                # collect probability of a rupture causing no exceedances
                probs_no_exceed.append(
                    rupture.get_probability_no_exceedance(poes_given_rup_eps)
                )
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, str(err))
            raise_(etype, msg, tb)

    mags = numpy.array(mags, float)
    dists = numpy.array(dists, float)
    lons = numpy.array(lons, float)
    lats = numpy.array(lats, float)
    tect_reg_types = numpy.array(tect_reg_types, int)
    probs_no_exceed = numpy.array(probs_no_exceed, float)

    trt_bins = [
        trt for (num, trt) in sorted((num, trt)
                                     for (trt, num) in trt_nums.items())
    ]

    return (mags, dists, lons, lats, tect_reg_types, trt_bins, probs_no_exceed)


def _define_bins(bins_data, mag_bin_width, dist_bin_width,
                 coord_bin_width, truncation_level, n_epsilons):
    """
    Define bin edges for disaggregation histograms.

    Given bins data as provided by :func:`_collect_bins_data`, this function
    finds edges of histograms, taking into account maximum and minimum values
    of magnitude, distance and coordinates as well as requested sizes/numbers
    of bins.
    """
    mags, dists, lons, lats, tect_reg_types, trt_bins, _ = bins_data

    mag_bins = mag_bin_width * numpy.arange(
        int(numpy.floor(mags.min() / mag_bin_width)),
        int(numpy.ceil(mags.max() / mag_bin_width) + 1)
    )

    dist_bins = dist_bin_width * numpy.arange(
        int(numpy.floor(dists.min() / dist_bin_width)),
        int(numpy.ceil(dists.max() / dist_bin_width) + 1)
    )

    west, east, north, south = get_spherical_bounding_box(lons, lats)
    west = numpy.floor(west / coord_bin_width) * coord_bin_width
    east = numpy.ceil(east / coord_bin_width) * coord_bin_width
    lon_extent = get_longitudinal_extent(west, east)
    lon_bins, _, _ = npoints_between(
        west, 0, 0, east, 0, 0,
        numpy.round(lon_extent / coord_bin_width + 1)
    )

    lat_bins = coord_bin_width * numpy.arange(
        int(numpy.floor(south / coord_bin_width)),
        int(numpy.ceil(north / coord_bin_width) + 1)
    )

    eps_bins = numpy.linspace(-truncation_level, truncation_level,
                              n_epsilons + 1)

    return mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins


def _arrange_data_in_bins(bins_data, bin_edges):
    """
    Given bins data, as it comes from :func:`_collect_bins_data`, and bin edges
    from :func:`_define_bins`, create a normalized 6d disaggregation matrix.
    """
    (mags, dists, lons, lats, tect_reg_types, trt_bins, probs_no_exceed) = \
        bins_data
    mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins = bin_edges

    dim1 = len(mag_bins) - 1
    dim2 = len(dist_bins) - 1
    dim3 = len(lon_bins) - 1
    dim4 = len(lat_bins) - 1
    shape = (dim1, dim2, dim3, dim4, len(eps_bins) - 1, len(trt_bins))
    diss_matrix = numpy.ones(shape)

    # find bin indexes of rupture attributes; bins are assumed closed
    # on the lower bound, and open on the upper bound, that is [ )
    # longitude values need an ad-hoc method to take into account
    # the 'international date line' issue
    # the 'minus 1' is needed because the digitize method returns the index
    # of the upper bound of the bin
    mags_idx = numpy.digitize(mags, mag_bins) - 1
    dists_idx = numpy.digitize(dists, dist_bins) - 1
    lons_idx = _digitize_lons(lons, lon_bins)
    lats_idx = numpy.digitize(lats, lat_bins) - 1

    # because of the way numpy.digitize works, values equal to the last bin
    # edge are associated to an index equal to len(bins) which is not a valid
    # index for the disaggregation matrix. Such values are assumed to fall
    # in the last bin.
    mags_idx[mags_idx == dim1] = dim1 - 1
    dists_idx[dists_idx == dim2] = dim2 - 1
    lons_idx[lons_idx == dim3] = dim3 - 1
    lats_idx[lats_idx == dim4] = dim4 - 1

    for i, (i_mag, i_dist, i_lon, i_lat, i_trt) in \
        enumerate(
            zip(mags_idx, dists_idx, lons_idx, lats_idx, tect_reg_types)):

        diss_matrix[i_mag, i_dist, i_lon, i_lat, :, i_trt] *= \
            probs_no_exceed[i, :]

    return 1 - diss_matrix


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


def mag_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude PMF.

    :returns:
        1d array, a histogram representing magnitude PMF.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_pmf = numpy.zeros(nmags)
    for i in range(nmags):
        mag_pmf[i] = numpy.prod(
            [1 - matrix[i][j][k][l][m][n]
             for j in range(ndists)
             for k in range(nlons)
             for l in range(nlats)
             for m in range(neps)
             for n in range(ntrts)]
        )
    return 1 - mag_pmf


def dist_pmf(matrix):
    """
    Fold full disaggregation matrix to distance PMF.

    :returns:
        1d array, a histogram representing distance PMF.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    dist_pmf = numpy.zeros(ndists)
    for j in range(ndists):
        dist_pmf[j] = numpy.prod(
            [1 - matrix[i][j][k][l][m][n]
             for i in range(nmags)
             for k in range(nlons)
             for l in range(nlats)
             for m in range(neps)
             for n in range(ntrts)]
        )
    return 1 - dist_pmf


def trt_pmf(matrix):
    """
    Fold full disaggregation matrix to tectonic region type PMF.

    :returns:
        1d array, a histogram representing tectonic region type PMF.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    trt_pmf = numpy.zeros(ntrts)
    for n in range(ntrts):
        trt_pmf[n] = numpy.prod(
            [1 - matrix[i][j][k][l][m][n]
             for i in range(nmags)
             for j in range(ndists)
             for k in range(nlons)
             for l in range(nlats)
             for m in range(neps)]
        )
    return 1 - trt_pmf


def mag_dist_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / distance PMF.

    :returns:
        2d array. First dimension represents magnitude histogram bins,
        second one -- distance histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_dist_pmf = numpy.zeros((nmags, ndists))
    for i in range(nmags):
        for j in range(ndists):
            mag_dist_pmf[i][j] = numpy.prod(
                [1 - matrix[i][j][k][l][m][n]
                 for k in range(nlons)
                 for l in range(nlats)
                 for m in range(neps)
                 for n in range(ntrts)]
            )
    return 1 - mag_dist_pmf


def mag_dist_eps_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / distance / epsilon PMF.

    :returns:
        3d array. First dimension represents magnitude histogram bins,
        second one -- distance histogram bins, third one -- epsilon
        histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_dist_eps_pmf = numpy.zeros((nmags, ndists, neps))
    for i in range(nmags):
        for j in range(ndists):
            for m in range(neps):
                mag_dist_eps_pmf[i][j][m] = numpy.prod(
                    [1 - matrix[i][j][k][l][m][n]
                     for k in range(nlons)
                     for l in range(nlats)
                     for n in range(ntrts)]
                )
    return 1 - mag_dist_eps_pmf


def lon_lat_pmf(matrix):
    """
    Fold full disaggregation matrix to longitude / latitude PMF.

    :returns:
        2d array. First dimension represents longitude histogram bins,
        second one -- latitude histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    lon_lat_pmf = numpy.zeros((nlons, nlats))
    for k in range(nlons):
        for l in range(nlats):
            lon_lat_pmf[k][l] = numpy.prod(
                [1 - matrix[i][j][k][l][m][n]
                 for i in range(nmags)
                 for j in range(ndists)
                 for m in range(neps)
                 for n in range(ntrts)]
            )
    return 1 - lon_lat_pmf


def mag_lon_lat_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / longitude / latitude PMF.

    :returns:
        3d array. First dimension represents magnitude histogram bins,
        second one -- longitude histogram bins, third one -- latitude
        histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_lon_lat_pmf = numpy.zeros((nmags, nlons, nlats))
    for i in range(nmags):
        for k in range(nlons):
            for l in range(nlats):
                mag_lon_lat_pmf[i][k][l] = numpy.prod(
                    [1 - matrix[i][j][k][l][m][n]
                     for j in range(ndists)
                     for m in range(neps)
                     for n in range(ntrts)]
                )
    return 1 - mag_lon_lat_pmf


def lon_lat_trt_pmf(matrix):
    """
    Fold full disaggregation matrix to longitude / latitude / tectonic region
    type PMF.

    :returns:
        3d array. Dimension represent longitude, latitude and tectonic region
        type histogram bins respectively.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    lon_lat_trt_pmf = numpy.zeros((nlons, nlats, ntrts))
    for k in range(nlons):
        for l in range(nlats):
            for n in range(ntrts):
                lon_lat_trt_pmf[k][l][n] = numpy.prod(
                    [1 - matrix[i][j][k][l][m][n]
                     for i in range(nmags)
                     for j in range(ndists)
                     for m in range(neps)]
                )
    return 1 - lon_lat_trt_pmf


# this dictionary is useful to extract a fixed set of
# submatrices from the full disaggregation matrix
pmf_map = collections.OrderedDict([
    (('Mag', ), mag_pmf),
    (('Dist', ), dist_pmf),
    (('TRT', ), trt_pmf),
    (('Mag', 'Dist'), mag_dist_pmf),
    (('Mag', 'Dist', 'Eps'), mag_dist_eps_pmf),
    (('Lon', 'Lat'), lon_lat_pmf),
    (('Mag', 'Lon', 'Lat'), mag_lon_lat_pmf),
    (('Lon', 'Lat', 'TRT'), lon_lat_trt_pmf),
])
