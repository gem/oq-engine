# The Hazard Library
# Copyright (C) 2012 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
:mod:`openquake.hazardlib.calc.disagg` contains :func:`disaggregation` as well as several
aggregation functions for extracting a specific PMF from the result of
:func:`disaggregation`.
"""
import numpy
import warnings

from openquake.hazardlib.calc import filters
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.geo.utils import get_spherical_bounding_box, \
                            get_longitudinal_extent
from openquake.hazardlib.geo.geodetic import npoints_between


def disaggregation(sources, site, imt, iml, gsims, tom,
                   truncation_level, n_epsilons,
                   mag_bin_width, dist_bin_width, coord_bin_width,
                   source_site_filter=filters.source_site_noop_filter,
                   rupture_site_filter=filters.rupture_site_noop_filter):
    """
    Compute "Disaggregation" matrix representing conditional probability
    distribution of

    - rupture magnitude,
    - joyner-boore distance from rupture surface to site,
    - longitude and latitude of surface projection of rupture closest point
      to site,
    - epsilon: number of standard deviations by which an intensity measure
      level deviates from the median value predicted by a gsim, given
      the rupture parameters.
    - rupture tectonic region type,

    given the event that an intensity measure type ``imt`` exceeds an intensity
    measure level ``iml`` at a geographical location ``site``.

    In other words, the disaggregation matrix allows to identify the most
    likely scenarios (classified in terms of the above mentioned parameters)
    that contribute to a given level of hazard (as specified by an intensity
    measure level). Note that the disaggregation matrix is computed assuming
    each rupture to occur only once in the given time span.

    For more detailed information about disaggregation see for instance
    "Disaggregation of seismic hazard', Paolo Bazzurro, C. Allin Cornell,
    Bulletin of the Seismological Society of America, Vol.89, pp.501-520,
    April 1999".

    :param sources:
        Seismic source model, as for :mod:`PSHA <openquake.hazardlib.calc.hazard_curve>`
        calculator it should be an iterator of seismic sources.
    :param site:
        :class:`~openquake.hazardlib.site.Site` of interest to calculate disaggregation
        matrix for.
    :param imt:
        Instance of :mod:`intensity measure type <openquake.hazardlib.imt>` class.
    :param iml:
        Intensity measure level. A float value in units of ``imt``.
    :param gsims:
        Tectonic region type to GSIM objects mapping.
    :param tom:
        Instance of temporal occurrence model object,
        such as :class:`~openquake.hazardlib.tom.PoissonTOM`. It is used for calculation
        of rupture occurrence probability.
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
        Optional source-site filter function. See :mod:`openquake.hazardlib.calc.filters`.
    :param rupture_site_filter:
        Optional rupture-site filter function. See :mod:`openquake.hazardlib.calc.filters`.

    :returns:
        A tuple of two items. First is itself a tuple of bin edges information
        for (in specified order) magnitude, distance, longitude, latitude,
        epsilon and tectonic region types.

        Second item is 6d-array representing the full disaggregation matrix.
        Dimensions are in the same order as bin edges in the first item
        of the result tuple. The matrix can be used directly by pmf-extractor
        functions.
    """
    bins_data = _collect_bins_data(sources, site, imt, iml, gsims, tom,
                                   truncation_level, n_epsilons,
                                   source_site_filter, rupture_site_filter)
    if all([len(x) == 0 for x in bins_data]):
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


def _collect_bins_data(sources, site, imt, iml, gsims, tom,
                       truncation_level, n_epsilons,
                       source_site_filter, rupture_site_filter):
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
    joint_probs = []
    sitecol = SiteCollection([site])
    sitemesh = sitecol.mesh

    _next_trt_num = 0
    trt_nums = {}

    sources_sites = ((source, sitecol) for source in sources)
    # here we ignore filtered site collection because either it is the same
    # as the original one (with one site), or the source/rupture is filtered
    # out and doesn't show up in the filter's output
    for source, s_sites in source_site_filter(sources_sites):
        tect_reg = source.tectonic_region_type
        gsim = gsims[tect_reg]

        if not tect_reg in trt_nums:
            trt_nums[tect_reg] = _next_trt_num
            _next_trt_num += 1
        tect_reg = trt_nums[tect_reg]

        ruptures_sites = ((rupture, s_sites)
                          for rupture in source.iter_ruptures(tom))
        for rupture, r_sites in rupture_site_filter(ruptures_sites):
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
            sctx, rctx, dctx = gsim.make_contexts(sitecol, rupture)
            [poes_given_rup_eps] = gsim.disaggregate_poe(
                sctx, rctx, dctx, imt, iml, truncation_level, n_epsilons
            )
            # compute the probability of the rupture occurring once,
            # that is ``P(rup)``
            p_rup = rupture.get_probability_one_occurrence()

            # compute joint probability of rupture occurrence and
            # iml exceedance for the different epsilon levels
            joint_probs.append(poes_given_rup_eps * p_rup)

    mags = numpy.array(mags, float)
    dists = numpy.array(dists, float)
    lons = numpy.array(lons, float)
    lats = numpy.array(lats, float)
    tect_reg_types = numpy.array(tect_reg_types, int)
    joint_probs = numpy.array(joint_probs, float)

    trt_bins = [
        trt for (num, trt) in sorted((num, trt)
                                     for (trt, num) in trt_nums.items())
    ]

    return mags, dists, lons, lats, joint_probs, tect_reg_types, trt_bins


def _define_bins(bins_data, mag_bin_width, dist_bin_width,
                 coord_bin_width, truncation_level, n_epsilons):
    """
    Define bin edges for disaggregation histograms.

    Given bins data as provided by :func:`_collect_bins_data`, this function
    finds edges of histograms, taking into account maximum and minimum values
    of magnitude, distance and coordinates as well as requested sizes/numbers
    of bins.
    """
    mags, dists, lons, lats, _joint_probs, tect_reg_types, trt_bins = bins_data

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
        numpy.round(lon_extent / coord_bin_width) + 1
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
    mags, dists, lons, lats, joint_probs, tect_reg_types, trt_bins = bins_data
    mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins = bin_edges
    shape = (len(mag_bins) - 1, len(dist_bins) - 1, len(lon_bins) - 1,
             len(lat_bins) - 1, len(eps_bins) - 1, len(trt_bins))
    diss_matrix = numpy.zeros(shape)

    for i_mag in xrange(len(mag_bins) - 1):
        mag_idx = mags <= mag_bins[i_mag + 1]
        if i_mag != 0:
            mag_idx &= mags > mag_bins[i_mag]

        for i_dist in xrange(len(dist_bins) - 1):
            dist_idx = dists <= dist_bins[i_dist + 1]
            if i_dist != 0:
                dist_idx &= dists > dist_bins[i_dist]

            for i_lon in xrange(len(lon_bins) - 1):
                extents = get_longitudinal_extent(lons, lon_bins[i_lon + 1])
                lon_idx = extents >= 0
                if i_lon != 0:
                    extents = get_longitudinal_extent(lon_bins[i_lon], lons)
                    lon_idx &= extents > 0

                for i_lat in xrange(len(lat_bins) - 1):
                    lat_idx = lats <= lat_bins[i_lat + 1]
                    if i_lat != 0:
                        lat_idx &= lats > lat_bins[i_lat]

                    for i_eps in xrange(len(eps_bins) - 1):

                        for i_trt in xrange(len(trt_bins)):
                            trt_idx = tect_reg_types == i_trt

                            prob_idx = mag_idx & dist_idx & lon_idx \
                                       & lat_idx & trt_idx
                            diss_idx = i_mag, i_dist, i_lon, \
                                       i_lat, i_eps, i_trt

                            diss_matrix[diss_idx] = numpy.sum(
                                joint_probs[prob_idx, i_eps]
                            )

    diss_matrix /= numpy.sum(diss_matrix)

    return diss_matrix


def mag_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude PMF.

    :returns:
        1d array, a histogram representing magnitude PMF.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_pmf = numpy.zeros(nmags)
    for i in xrange(nmags):
        mag_pmf[i] = sum(matrix[i][j][k][l][m][n]
                         for j in xrange(ndists)
                         for k in xrange(nlons)
                         for l in xrange(nlats)
                         for m in xrange(neps)
                         for n in xrange(ntrts))
    return mag_pmf


def dist_pmf(matrix):
    """
    Fold full disaggregation matrix to distance PMF.

    :returns:
        1d array, a histogram representing distance PMF.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    dist_pmf = numpy.zeros(ndists)
    for j in xrange(ndists):
        dist_pmf[j] = sum(matrix[i][j][k][l][m][n]
                          for i in xrange(nmags)
                          for k in xrange(nlons)
                          for l in xrange(nlats)
                          for m in xrange(neps)
                          for n in xrange(ntrts))
    return dist_pmf


def trt_pmf(matrix):
    """
    Fold full disaggregation matrix to tectonic region type PMF.

    :returns:
        1d array, a histogram representing tectonic region type PMF.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    trt_pmf = numpy.zeros(ntrts)
    for n in xrange(ntrts):
        trt_pmf[n] = sum(matrix[i][j][k][l][m][n]
                         for i in xrange(nmags)
                         for j in xrange(ndists)
                         for k in xrange(nlons)
                         for l in xrange(nlats)
                         for m in xrange(neps))
    return trt_pmf


def mag_dist_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / distance PMF.

    :returns:
        2d array. First dimension represents magnitude histogram bins,
        second one -- distance histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_dist_pmf = numpy.zeros((nmags,ndists))
    for i in xrange(nmags):
        for j in xrange(ndists):
            mag_dist_pmf[i][j] = sum(matrix[i][j][k][l][m][n]
                                     for k in xrange(nlons)
                                     for l in xrange(nlats)
                                     for m in xrange(neps)
                                     for n in xrange(ntrts))
    return mag_dist_pmf


def mag_dist_eps_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / distance / epsilon PMF.

    :returns:
        3d array. First dimension represents magnitude histogram bins,
        second one -- distance histogram bins, third one -- epsilon
        histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_dist_eps_pmf = numpy.zeros((nmags,ndists,neps))
    for i in xrange(nmags):
        for j in xrange(ndists):
            for m in xrange(neps):
                mag_dist_eps_pmf[i][j][m] = sum(matrix[i][j][k][l][m][n]
                                                for k in xrange(nlons)
                                                for l in xrange(nlats)
                                                for n in xrange(ntrts))
    return mag_dist_eps_pmf


def lon_lat_pmf(matrix):
    """
    Fold full disaggregation matrix to longitude / latitude PMF.

    :returns:
        2d array. First dimension represents longitude histogram bins,
        second one -- latitude histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    lon_lat_pmf = numpy.zeros((nlons,nlats))
    for k in xrange(nlons):
        for l in xrange(nlats):
            lon_lat_pmf[k][l] = sum(matrix[i][j][k][l][m][n]
                                    for i in xrange(nmags)
                                    for j in xrange(ndists)
                                    for m in xrange(neps)
                                    for n in xrange(ntrts))
    return lon_lat_pmf


def mag_lon_lat_pmf(matrix):
    """
    Fold full disaggregation matrix to magnitude / longitude / latitude PMF.

    :returns:
        3d array. First dimension represents magnitude histogram bins,
        second one -- longitude histogram bins, third one -- latitude
        histogram bins.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    mag_lon_lat_pmf = numpy.zeros((nmags,nlons,nlats))
    for i in xrange(nmags):
        for k in xrange(nlons):
            for l in xrange(nlats):
                mag_lon_lat_pmf[i][k][l] = sum(matrix[i][j][k][l][m][n]
                                               for j in xrange(ndists)
                                               for m in xrange(neps)
                                               for n in xrange(ntrts))
    return mag_lon_lat_pmf


def lon_lat_trt_pmf(matrix):
    """
    Fold full disaggregation matrix to longitude / latitude / tectonic region
    type PMF.

    :returns:
        3d array. Dimension represent longitude, latitude and tectonic region
        type histogram bins respectively.
    """
    nmags, ndists, nlons, nlats, neps, ntrts = matrix.shape
    lon_lat_trt_pmf = numpy.zeros((nlons,nlats,ntrts))
    for k in xrange(nlons):
        for l in xrange(nlats):
            for n in xrange(ntrts):
                lon_lat_trt_pmf[k][l][n] = sum(matrix[i][j][k][l][m][n]
                                               for i in xrange(nmags)
                                               for j in xrange(ndists)
                                               for m in xrange(neps))
    return lon_lat_trt_pmf
