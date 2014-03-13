# -*- coding: utf-8 -*-
# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Disaggregation calculator core functionality
"""
import sys
from collections import OrderedDict, defaultdict
import numpy

from openquake.hazardlib.calc import disagg
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.geo.geodetic import npoints_between
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.utils import get_spherical_bounding_box
from openquake.hazardlib.site import SiteCollection

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine.performance import EnginePerformanceMonitor, LightMonitor
from openquake.engine.calculators.hazard.classical.core import \
    ClassicalHazardCalculator
from openquake.engine.calculators.base import log_percent_gen


def pmf_dict(matrix):
    """
    Return an OrderedDict of matrices with the key in the dictionary
    `openquake.hazardlib.calc.disagg.pmf_map`.

    :param matrix: an :class:`openquake.engine.db.models.
    """
    return OrderedDict((key, pmf_fn(matrix))
                       for key, pmf_fn in disagg.pmf_map.iteritems())


def _collect_bins_data(mon, trt_num, source_ruptures, site,
                       gsims_by_rlz, imtls, poes, truncation_level,
                       n_epsilons):
    """
    Extract values of magnitude, distance, closest point, tectonic region
    types and PoE distribution.

    This method processes the source model (generates ruptures) and collects
    all needed parameters to arrays. It also defines tectonic region type
    bins sequence.

    :returns: mags, dists, lons, lats, tect_reg_types, probs_no_exceed
    """
    sitecol = SiteCollection([site])
    mags = []
    dists = []
    lons = []
    lats = []
    trts = []
    pnes = []
    sitemesh = sitecol.mesh
    mon1 = mon.copy('calc distances')
    mon2 = mon.copy('making contexts')
    mon3 = mon.copy('disaggregate_poe')

    for source, ruptures in source_ruptures:
        try:
            tect_reg = trt_num[source.tectonic_region_type]
            for rupture in ruptures:
                # extract rupture parameters of interest
                mags.append(rupture.mag)
                with mon1:
                    [jb_dist] = rupture.surface.get_joyner_boore_distance(
                        sitemesh)
                    dists.append(jb_dist)
                    [closest_point] = rupture.surface.get_closest_points(
                        sitemesh)
                lons.append(closest_point.longitude)
                lats.append(closest_point.latitude)
                trts.append(tect_reg)

                pne_dict = defaultdict(list)
                # a dictionary rlz.id, poe, iml, imt_str -> prob_no_exceed
                for rlz, gsims in gsims_by_rlz.items():
                    gsim = gsims[source.tectonic_region_type]
                    with mon2:
                        sctx, rctx, dctx = gsim.make_contexts(sitecol, rupture)
                    for imt_str, imls in imtls.iteritems():
                        imt = from_string(imt_str)
                        imls = numpy.array(imls[::-1])
                        [curve] = models.HazardCurveData.objects.filter(
                            location=site.location.wkt2d,
                            hazard_curve__lt_realization=rlz,
                            hazard_curve__imt=imt[0],
                            hazard_curve__sa_period=imt[1],
                            hazard_curve__sa_damping=imt[2])
                        if all(x == 0.0 for x in curve.poes):
                            logs.LOG.warn(
                                '* hazard curve contained all 0 probability '
                                'values; skipping rlz=%d, IMT=%s',
                                rlz.id, imt_str)
                            continue

                        for poe in poes:
                            iml = numpy.interp(poe, curve.poes[::-1], imls)
                            # compute conditional probability of exceeding iml given
                            # the current rupture, and different epsilon level, that is
                            # ``P(IMT >= iml | rup, epsilon_bin)`` for each of the epsilon bins
                            probs_no_exceed = pne_dict[
                                rlz.id, poe, iml, imt_str]
                            with mon3:
                                [poes_given_rup_eps] = gsim.disaggregate_poe(
                                    sctx, rctx, dctx, imt, iml,
                                    truncation_level, n_epsilons)

                            probs_no_exceed.append(
                                rupture.get_probability_no_exceedance(
                                    poes_given_rup_eps)
                            )
                pnes.append(pne_dict)
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, err.message)
            raise etype, msg, tb

    mon1.flush()
    mon2.flush()
    mon3.flush()
    return mags, dists, lons, lats, trts, pnes


def _define_bins(bins_data, mag_bin_width, dist_bin_width,
                 coord_bin_width, truncation_level, n_epsilons):
    """
    Define bin edges for disaggregation histograms.

    Given bins data as provided by :func:`_collect_bins_data`, this function
    finds edges of histograms, taking into account maximum and minimum values
    of magnitude, distance and coordinates as well as requested sizes/numbers
    of bins.

    :returns: mag_bins, dist_bins, lon_bins, lat_bins, eps_bins
    """
    mags, dists, lons, lats, tect_reg_types, _no_exceed = bins_data

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
    return mag_bins, dist_bins, lon_bins, lat_bins, eps_bins


def _arrange_data_in_bins(bins_data, bin_edges, num_trt):
    """
    Given bins data, as it comes from :func:`_collect_bins_data`, and bin edges
    from :func:`_define_bins`, create a normalized 6d disaggregation matrix.
    """
    mags, dists, lons, lats, tect_reg_types, probs_no_exceed = bins_data
    mag_bins, dist_bins, lon_bins, lat_bins, eps_bins = bin_edges
    shape = (len(mag_bins) - 1, len(dist_bins) - 1, len(lon_bins) - 1,
             len(lat_bins) - 1, len(eps_bins) - 1, num_trt)
    todo = numpy.prod(shape)  # number of matrix elements to compute
    log_percent = log_percent_gen('arrange data', todo)
    diss_matrix = numpy.zeros(shape)
    logs.LOG.info('Populating disaggregation matrix of size %d, %s',
                  todo, shape)

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

                        for i_trt in xrange(num_trt):
                            trt_idx = tect_reg_types == i_trt

                            diss_idx = (i_mag, i_dist, i_lon,
                                        i_lat, i_eps, i_trt)

                            prob_idx = (mag_idx & dist_idx & lon_idx
                                        & lat_idx & trt_idx)

                            poe = 1 - numpy.prod(
                                probs_no_exceed[prob_idx, i_eps])

                            diss_matrix[diss_idx] = poe

                            log_percent.next()
    return diss_matrix


_DISAGG_RES_NAME_FMT = 'disagg(%(poe)s)-rlz-%(rlz)s-%(imt)s-%(wkt)s'


def _save_disagg_matrix(job_id, site_id, bin_edges, trt_names, diss_matrix,
                        rlz, investigation_time, imt_str, iml, poe):
    """
    Save a computed disaggregation matrix to `hzrdr.disagg_result` (see
    :class:`~openquake.engine.db.models.DisaggResult`).

    :param int job_id:
        id of the current job.
    :param int site_id:
        id of the current site
    :param bin_edges:
        The 5-uple mag, dist, lon, lat, eps
    :param trt_names:
        The list of Tectonic Region Types
    :param diss_matrix:
        The diseggregation matrix as a 6-dimensional numpy array
    :param rlz:
        :class:`openquake.engine.db.models.LtRealization` to which these
        results belong.
    :param float investigation_time:
        Investigation time (years) for the calculation.
    :param imt_str:
        Intensity measure type (PGA, SA, etc.)
    :param float iml:
        Intensity measure level interpolated (using ``poe``) from the hazard
        curve at the ``site``.
    :param float poe:
        Disaggregation probability of exceedance value for this result.
    """
    job = models.OqJob.objects.get(id=job_id)

    site_wkt = models.HazardSite.objects.get(pk=site_id).location.wkt

    disp_name = _DISAGG_RES_NAME_FMT % dict(
        poe=poe, rlz=rlz.id, imt=imt_str, wkt=site_wkt)

    output = models.Output.objects.create_output(
        job, disp_name, 'disagg_matrix')

    imt, sa_period, sa_damping = from_string(imt_str)
    mag, dist, lon, lat, eps = bin_edges
    models.DisaggResult.objects.create(
        output=output,
        lt_realization=rlz,
        investigation_time=investigation_time,
        imt=imt,
        sa_period=sa_period,
        sa_damping=sa_damping,
        iml=iml,
        poe=poe,
        mag_bin_edges=mag,
        dist_bin_edges=dist,
        lon_bin_edges=lon,
        lat_bin_edges=lat,
        eps_bin_edges=eps,
        trts=trt_names,
        location=site_wkt,
        matrix=pmf_dict(diss_matrix),
    )


@tasks.oqtask
def collect_bins(job_id, sources, gsims_by_rlz, trt_num, site):
    """
    Here is the basic calculation workflow:

    1. Get the hazard curve for each point, IMT, and realization
    2. For each `poes_disagg`, interpolate the IML for each curve.
    3. Collect bins data into a result dictionary of the form
       (rlz_id, site, poe, iml, im_type, sa_period, sa_damping) ->
       (mags, dists, lons, lats, tect_reg_types, probs_no_exceed)

    :param int job_id:
        ID of the currently running :class:`openquake.engine.db.models.OqJob`
    :param list sources:
        list of hazardlib source objects
    :param dict gsims_by_rlz:
        a dictionary of gsim dictionaries, one for each realization
    :param dict trt_num:
        a dictionary Tectonic Region Type -> incremental number
    """
    mon = LightMonitor('disagg', job_id, collect_bins)
    hc = models.OqJob.objects.get(id=job_id).hazard_calculation

    # generate source, rupture, sites once per site
    source_ruptures = list(hc.gen_ruptures_for_site(site, sources, mon))
    if not source_ruptures:
        return [], [], [], [], [], []

    logs.LOG.info('Considering %d ruptures close to %s',
                  sum(len(rupts) for src, rupts in source_ruptures), site)

    return _collect_bins_data(
        mon, trt_num, source_ruptures, site,
        gsims_by_rlz, hc.intensity_measure_types_and_levels,
        hc.poes_disagg, hc.truncation_level,
        hc.num_epsilon_bins)


@tasks.oqtask
def arrange_and_save_disagg_matrix(
        job_id, trt_names, bins, site_id, rlz_id, poe, iml, imt_str):
    """
    Arrange the data in the bins into a disaggregation matrix
    and save it.

    :param int job_id:
        ID of the currently running :class:`openquake.engine.db.models.OqJob`
    :param trt_names:
        a list of names of Tectonic Region Types
    :param bins:
        a 6-uple of lists (mag_bins, dist_bins, lon_bins, lat_bins,
        trt_bins, eps_bins)
    :param int rlz_id:
        ID of the current realization
    :param int site_id:
        ID of the current site
    :param poe:
        One of the PoE in disagg_poes in the job.ini file
    :param iml:
        The IML corresponding to that PoE
    :param imt_str:
         The Intensity Measure Type of the result
    """
    hc = models.OqJob.objects.get(id=job_id).hazard_calculation
    rlz = models.LtRealization.objects.get(id=rlz_id)

    # define bins
    bin_edges = _define_bins(
        bins,
        hc.mag_bin_width,
        hc.distance_bin_width,
        hc.coordinate_bin_width,
        hc.truncation_level,
        hc.num_epsilon_bins)

    with EnginePerformanceMonitor('arrange data', job_id,
                                  arrange_and_save_disagg_matrix):
        diss_matrix = _arrange_data_in_bins(bins, bin_edges, len(trt_names))

    with EnginePerformanceMonitor('saving disaggregation', job_id,
                                  arrange_and_save_disagg_matrix):
        _save_disagg_matrix(
            job_id, site_id, bin_edges, trt_names, diss_matrix, rlz,
            hc.investigation_time, imt_str, iml, poe)


class DisaggHazardCalculator(ClassicalHazardCalculator):
    """
    A calculator which performs disaggregation calculations in a distributed /
    parallelized fashion.

    See :func:`openquake.hazardlib.calc.disagg.disaggregation` for more
    details about the nature of this type of calculation.
    """
    def full_disaggregation(self):
        """
        Run the disaggregation phase after hazard curve finalization.
        """
        super(DisaggHazardCalculator, self).post_execute()

        # we are working sequentially on sites to save memory
        for site in self.hc.site_collection:
            trt_num = dict((trt, i) for i, trt in enumerate(
                           self.tectonic_region_types))
            arglist = [(self.job.id, srcs, gsims_by_rlz, trt_num, site)
                       for job_id, srcs, gsims_by_rlz in self.task_arg_gen()]

            self.result = [], [], [], [], [], []
            with self.monitor('collect results'):
                self.parallelize(collect_bins, arglist, self.collect_result)
            if not self.result[5]:  # no contributions for this site
                continue

            trt_names = [trt for (num, trt) in sorted(
                         (num, trt) for (trt, num) in trt_num.items())]

            mags = numpy.array(self.result[0], float)
            dists = numpy.array(self.result[1], float)
            lons = numpy.array(self.result[2], float)
            lats = numpy.array(self.result[3], float)
            trts = numpy.array(self.result[4], int)
            pnes = self.result[5]
            keys = pnes[0].keys()
            alist = []
            for key in keys:
                # key = rlz_id, poe, iml, imt
                probs = numpy.array([pne[key][0] for pne in pnes], float)
                bins = (mags, dists, lons, lats, trts, probs)
                args = (self.job.id, trt_names, bins, site.id) + key
                alist.append(args)
                
            self.parallelize(
                arrange_and_save_disagg_matrix, alist, self.log_percent)

    post_execute = full_disaggregation

    def collect_result(self, result):
        """
        Collect the results coming from collect_bins into self.results,
        a dictionary with key (rlz_id, site, poe, iml, im_type, sa_period,
        sa_damping) and values (mag_bins, dist_bins, lon_bins, lat_bins,
        trt_bins, eps_bins).
        """
        for resbins, bins in zip(self.result, result):
            resbins.extend(bins)
        self.log_percent()
