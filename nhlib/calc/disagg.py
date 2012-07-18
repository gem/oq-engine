# nhlib: A New Hazard Library
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
:mod:`nhlib.calc.disagg` contains :func:`disaggregation`.
"""
import numpy

from nhlib.site import SiteCollection
# TODO: this shouldn't be imported from a geo package's private module
from nhlib.geo._utils import get_spherical_bounding_box, \
                             get_longitudinal_extent
from nhlib.geo.geodetic import npoints_between


def disaggregation():
    """
    """



def _collect_bins_data(sources, site, iml, imt, gsims, tom,
                       truncation_level, n_epsilons,
                       source_site_filter, rupture_site_filter):
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
    """
    mags, dists, lons, lats, _joint_probs, tect_reg_types, trt_bins = bins_data

    mag_bins = numpy.arange(
        numpy.floor(mags.min() / mag_bin_width) * mag_bin_width,
        numpy.ceil(mags.max() / mag_bin_width) * mag_bin_width,
        mag_bin_width
    )

    dist_bins = numpy.arange(
        numpy.floor(dists.min() / dist_bin_width) * dist_bin_width,
        numpy.ceil(dists.max() / dist_bin_width) * dist_bin_width,
        dist_bin_width
    )

    west, east, north, south = get_spherical_bounding_box(lons, lats)
    west = numpy.floor(west / coord_bin_width) * coord_bin_width
    east = numpy.ceil(east / coord_bin_width) * coord_bin_width
    lon_extent = get_longitudinal_extent(west, east)
    lon_bins, _, _ = npoints_between(west, 0, 0, east, 0, 0,
                                     numpy.round(lon_extent) / coord_bin_width)

    lat_bins = numpy.arange(
        numpy.floor(south / coord_bin_width) * coord_bin_width,
        numpy.ceil(north / coord_bin_width) * coord_bin_width,
        coord_bin_width
    )

    eps_bins = numpy.linspace(-truncation_level, truncation_level, n_epsilons)

    return mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins


def _arange_data_in_bins(bins_data, bin_edges):
    mags, dists, lons, lats, joint_probs, tect_reg_types = bins_data
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
                            trt_idx = trt_bins == i_trt

                            prob_idx = mag_idx & dist_idx & lon_idx \
                                       & lat_idx & trt_idx
                            diss_idx = i_mag, i_dist, i_lon, \
                                       i_lat, i_eps, i_trt

                            diss_matrix[diss_idx] = numpy.sum(
                                joint_probs[prob_idx, i_eps]
                            )

    diss_matrix /= numpy.sum(diss_matrix)

    return diss_matrix
