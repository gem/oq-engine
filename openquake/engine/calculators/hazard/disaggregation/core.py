# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013, GEM Foundation.
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
from collections import OrderedDict
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


def pmf_dict(matrix):
    """
    Return an OrderedDict of matrices with the key in the dictionary
    `openquake.hazardlib.calc.disagg.pmf_map` .
    """
    return OrderedDict((key, pmf_fn(matrix))
                       for key, pmf_fn in disagg.pmf_map.iteritems())


def _collect_bins_data(mon, trt_num, source_rupture_sites, site, imt, iml,
                       gsims, truncation_level, n_epsilons):
    """
    Extract values of magnitude, distance, closest point, tectonic region
    types and PoE distribution.

    This method processes the source model (generates ruptures) and collects
    all needed parameters to arrays. It also defines tectonic region type
    bins sequence.

    :returns: mags, dists, lons, lats, tect_reg_types, probs_no_exceed
    """
    mags = []
    dists = []
    lons = []
    lats = []
    tect_reg_types = []
    probs_no_exceed = []
    sitecol = SiteCollection([site])
    sitemesh = sitecol.mesh
    mon1 = mon.copy('calc distances')
    mon2 = mon.copy('making contexts')
    mon3 = mon.copy('disaggregate_poe')
    for source, rupture, r_sites in source_rupture_sites:
        try:
            gsim = gsims[source.tectonic_region_type]
            tect_reg = trt_num[source.tectonic_region_type]
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
            tect_reg_types.append(tect_reg)

            # compute conditional probability of exceeding iml given
            # the current rupture, and different epsilon level, that is
            # ``P(IMT >= iml | rup, epsilon_bin)`` for each of epsilon bins
            with mon2:
                sctx, rctx, dctx = gsim.make_contexts(sitecol, rupture)
            with mon3:
                [poes_given_rup_eps] = gsim.disaggregate_poe(
                    sctx, rctx, dctx, imt, iml, truncation_level,
                    n_epsilons)

            # collect probability of a rupture causing no exceedances
            probs_no_exceed.append(
                rupture.get_probability_no_exceedance(poes_given_rup_eps)
            )
        except Exception, err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, err.message)
            raise etype, msg, tb

    mon1.flush()
    mon2.flush()
    mon3.flush()
    return mags, dists, lons, lats, tect_reg_types, probs_no_exceed


def _define_bins(bins_data, mag_bin_width, dist_bin_width,
                 coord_bin_width, truncation_level, n_epsilons):
    """
    Define bin edges for disaggregation histograms.

    Given bins data as provided by :func:`_collect_bins_data`, this function
    finds edges of histograms, taking into account maximum and minimum values
    of magnitude, distance and coordinates as well as requested sizes/numbers
    of bins.
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


def _arrange_data_in_bins(bins_data, bin_edges):
    """
    Given bins data, as it comes from :func:`_collect_bins_data`, and bin edges
    from :func:`_define_bins`, create a normalized 6d disaggregation matrix.
    """
    (mags, dists, lons, lats, tect_reg_types, probs_no_exceed) = bins_data
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

                            diss_idx = (i_mag, i_dist, i_lon,
                                        i_lat, i_eps, i_trt)

                            prob_idx = (mag_idx & dist_idx & lon_idx
                                        & lat_idx & trt_idx)

                            poe = numpy.prod(
                                probs_no_exceed[prob_idx, i_eps]
                                )
                            poe = 1 - poe

                            diss_matrix[diss_idx] = poe

    return diss_matrix


@tasks.oqtask
def collect_bins(job_id, sources, gsims_by_rlz, site, trt_num):
    """
    Here is the basic calculation workflow:

    1. Get the hazard curve for each point, IMT, and realization
    2. For each `poes_disagg`, interpolate the IML for each curve.
    3. Collect bins data into a result dictionary

    (rlz_id, site, poe, iml, im_type, sa_period, sa_damping) ->
    (mags, dists, lons, lats, tect_reg_types, probs_no_exceed)

    :param int job_id:
        ID of the currently running :class:`openquake.engine.db.models.OqJob`
    :param list sources:
        `list` of hazardlib source objects
    :param gsims_by_rlz:
        XXX
    :param trt_num:
        a dictionary Tectonic Region Type -> incremental number
    """
    mon = LightMonitor('disagg', job_id, collect_bins)
    hc = models.OqJob.objects.get(id=job_id).hazard_calculation
    source_rupture_sites = list(hc.gen_ruptures(sources, mon))

    result = {}
    for rlz, gsims in gsims_by_rlz.items():
        for imt, imls in hc.intensity_measure_types_and_levels.iteritems():
            im_type, sa_period, sa_damping = imt = from_string(imt)
            imls = numpy.array(imls[::-1])

            # get curve for this point/IMT/realization
            [curve] = models.HazardCurveData.objects.filter(
                location=site.location.wkt2d,
                hazard_curve__lt_realization=rlz,
                hazard_curve__imt=im_type,
                hazard_curve__sa_period=sa_period,
                hazard_curve__sa_damping=sa_damping)

            # If the hazard curve is all zeros, don't even do the
            # disagg calculation.
            if all(x == 0.0 for x in curve.poes):
                logs.LOG.warn(
                    '* hazard curve contained all 0 probability values; '
                    'skipping rlz=%d, IMT=%s', rlz.id, im_type)
                continue

            for poe in hc.poes_disagg:
                iml = numpy.interp(poe, curve.poes[::-1], imls)
                result[rlz.id, site.id, poe, iml,
                       im_type, sa_period, sa_damping] = _collect_bins_data(
                    mon, trt_num, source_rupture_sites, site,
                    imt, iml, gsims, hc.truncation_level, hc.num_epsilon_bins)
    return result


_DISAGG_RES_NAME_FMT = 'disagg(%(poe)s)-rlz-%(rlz)s-%(imt)s-%(wkt)s'


def _save_disagg_matrix(job_id, site_id, bin_edges, diss_matrix, rlz,
                        investigation_time, imt, iml, poe, sa_period,
                        sa_damping):
    """
    Save a computed disaggregation matrix to `hzrdr.disagg_result` (see
    :class:`~openquake.engine.db.models.DisaggResult`).

    :param int job_id:
        id of the current job.
    :param int site_id:
        id of the current site
    :param bin_edges, diss_matrix
        The outputs of :func:
        `openquake.hazardlib.calc.disagg.disaggregation`.
    :param rlz:
        :class:`openquake.engine.db.models.LtRealization` to which these
        results belong.
    :param float investigation_time:
        Investigation time (years) for the calculation.
    :param imt:
        Intensity measure type (PGA, SA, etc.)
    :param float iml:
        Intensity measure level interpolated (using ``poe``) from the hazard
        curve at the ``site``.
    :param float poe:
        Disaggregation probability of exceedance value for this result.
    :param float sa_period:
        Spectral Acceleration period; only relevant when ``imt`` is 'SA'.
    :param float sa_damping:
        Spectral Acceleration damping; only relevant when ``imt`` is 'SA'.
    """
    job = models.OqJob.objects.get(id=job_id)

    site_wkt = models.HazardSite.objects.get(pk=site_id).location.wkt

    disp_name = _DISAGG_RES_NAME_FMT
    disp_imt = imt
    if disp_imt == 'SA':
        disp_imt = 'SA(%s)' % sa_period
    disp_name_args = dict(poe=poe, rlz=rlz.id, imt=disp_imt,
                          wkt=site_wkt)
    disp_name %= disp_name_args

    output = models.Output.objects.create_output(
        job, disp_name, 'disagg_matrix')

    mag, dist, lon, lat, eps, trts = bin_edges
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
        trts=trts,
        location=site_wkt,
        matrix=pmf_dict(diss_matrix),
    )


@tasks.oqtask
def arrange_and_save_disagg_matrix(
        job_id, trt_bins, bins, rlz_id, site_id, poe, iml,
        im_type, sa_period, sa_damping):
    """
    Arrange the data in the bins into a disaggregation matrix
    and save it.

    :param trt_bins: a list of names of Tectonic Region Types

    """
    hc = models.OqJob.objects.get(id=job_id).hazard_calculation
    rlz = models.LtRealization.objects.get(id=rlz_id)
    mags = numpy.array(bins[0], float)
    dists = numpy.array(bins[1], float)
    lons = numpy.array(bins[2], float)
    lats = numpy.array(bins[3], float)
    tect_reg_types = numpy.array(bins[4], int)
    probs_no_exceed = numpy.array(bins[5], float)
    bdata = (mags, dists, lons, lats, tect_reg_types, probs_no_exceed)
    bin_edges = _define_bins(
        bdata,
        hc.mag_bin_width,
        hc.distance_bin_width,
        hc.coordinate_bin_width,
        hc.truncation_level,
        hc.num_epsilon_bins) + (trt_bins, )
    if not bin_edges:  # no bins populated
        return

    with EnginePerformanceMonitor('arrange data', job_id,
                                  arrange_and_save_disagg_matrix):
        diss_matrix = _arrange_data_in_bins(bdata, bin_edges)

    with EnginePerformanceMonitor('saving disaggregation', job_id,
                                  arrange_and_save_disagg_matrix):
        _save_disagg_matrix(
            job_id, site_id, bin_edges, diss_matrix, rlz,
            hc.investigation_time, im_type, iml, poe, sa_period,
            sa_damping)


class DisaggHazardCalculator(ClassicalHazardCalculator):
    """
    A calculator which performs disaggregation calculations in a distributed /
    parallelized fashion.

    See :func:`openquake.hazardlib.calc.disagg.disaggregation` for more
    details about the nature of this type of calculation.
    """

    def disagg_task_arg_gen(self):
        """
        Generate task args for the second phase of disaggregation calculations.
        This phase is concerned with computing the disaggregation histograms.
        """
        self.trt_num = dict((trt, i) for i, trt in enumerate(
                            self.tectonic_region_types))
        for job_id, sources, gsims_by_rlz in self.task_arg_gen():
            for site in self.hc.site_collection:
                yield self.job.id, sources, gsims_by_rlz, site, self.trt_num

    def post_execute(self):
        """
        Start the disaggregation phase after hazard curve finalization.
        """
        super(DisaggHazardCalculator, self).post_execute()

        self.result = {}  # dictionary {key: bins} where key is the tuple
        # rlz_id, site, poe, iml, im_type, sa_period, sa_damping
        self.parallelize(
            collect_bins, self.disagg_task_arg_gen(), self.collect_result)

        trt_bins = [trt for (num, trt) in sorted(
                    (num, trt) for (trt, num) in self.trt_num.items())]
        arglist = [(self.job.id, trt_bins, bins) + key
                   for key, bins in self.result.iteritems()]
        self.parallelize(
            arrange_and_save_disagg_matrix, arglist, self.log_percent)

    @EnginePerformanceMonitor.monitor
    def collect_result(self, result):
        """
        Collect the results coming from collect_bins into self.results,
        a dictionary with key (rlz_id, site, poe, iml, im_type, sa_period,
        sa_damping) and values (mag_bins, dist_bins, lon_bins, lat_bins,
        eps_bins, trt_bins).

        """
        for rlz_id, site_id, poe, iml, imtype, sa_period, sa_damping in result:
            # mag_bins, dist_bins, lon_bins, lat_bins, tect_reg_types, eps_bins
            try:
                bins = self.result[
                    rlz_id, site_id, poe, iml, imtype, sa_period, sa_damping]
            except KeyError:
                bins = self.result[
                    rlz_id, site_id, poe, iml, imtype, sa_period, sa_damping
                    ] = ([], [], [], [], [], [])
            bins_data = result[
                rlz_id, site_id, poe, iml, imtype, sa_period, sa_damping]
            for acc, ls in zip(bins, bins_data):
                acc.extend(ls)
        self.log_percent()
