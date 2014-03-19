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
import cPickle
from collections import OrderedDict, namedtuple, defaultdict

import numpy

from openquake.hazardlib.calc import disagg
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.utils import get_spherical_bounding_box
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.geo.geodetic import npoints_between

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine.performance import EnginePerformanceMonitor, LightMonitor
from openquake.engine.calculators.hazard.classical.core import \
    ClassicalHazardCalculator


# a pair (vals, iml) where vals is a list of arrays of poes
# with num_epsilon_bins elements each
ProbNoExceed = namedtuple('ProbNoExceed', 'vals iml')


def dist_lon_lat_bins(dists, lons, lats, dist_bin_width, coord_bin_width):
    """
    Define bin edges for disaggregation histograms.
    """
    dist_bins = dist_bin_width * numpy.arange(
        int(numpy.floor(min(dists) / dist_bin_width)),
        int(numpy.ceil(max(dists) / dist_bin_width) + 1)
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

    return dist_bins, lon_bins, lat_bins


def merge_prob_no_exceed(prob_no_exceed_list):
    """
    Merge a list containing ProbNoExceed objects with the same .iml
    attribute. Raise an error if the list is empty. Return a
    ProbNoExceed object with the merged list and the given iml.
    """
    assert prob_no_exceed_list
    prob_no_exceed = prob_no_exceed_list[0]
    iml = prob_no_exceed.iml
    vals = []
    for el in prob_no_exceed_list:
        assert el.iml == iml
        vals.extend(el.vals)
    return ProbNoExceed(vals, iml)


def pmf_dict(matrix):
    """
    Return an OrderedDict of matrices with the key in the dictionary
    `openquake.hazardlib.calc.disagg.pmf_map`.

    :param matrix: an :class:`openquake.engine.db.models.
    """
    return OrderedDict((key, pmf_fn(matrix))
                       for key, pmf_fn in disagg.pmf_map.iteritems())


# returns mags, dists, lons, lats, tect_reg_types, probs_no_exceed
def _collect_bins_data(mon, trt_num, source_ruptures, site, curves,
                       gsims_by_rlz, imtls, poes, truncation_level,
                       n_epsilons):
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

                pne_dict = {}
                # a dictionary rlz.id, poe, imt_str -> prob_no_exceed
                for rlz, gsims in gsims_by_rlz.items():
                    gsim = gsims[source.tectonic_region_type]
                    with mon2:
                        sctx, rctx, dctx = gsim.make_contexts(sitecol, rupture)
                    for imt_str, imls in imtls.iteritems():
                        imt = from_string(imt_str)
                        imls = numpy.array(imls[::-1])
                        curve_poes = curves[rlz.id, imt_str].poes[::-1]

                        for poe in poes:
                            iml = numpy.interp(poe, curve_poes, imls)
                            # compute probability of exceeding iml given
                            # the current rupture and epsilon level, that is
                            # ``P(IMT >= iml | rup, epsilon_bin)``
                            # for each of the epsilon bins
                            with mon3:
                                [poes_given_rup_eps] = gsim.disaggregate_poe(
                                    sctx, rctx, dctx, imt, iml,
                                    truncation_level, n_epsilons)
                            pne = rupture.get_probability_no_exceedance(
                                poes_given_rup_eps)
                            pne_dict[rlz.id, poe, imt_str] = \
                                ProbNoExceed([pne], iml)

                pnes.append(pne_dict)
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, err.message)
            raise etype, msg, tb

    mon1.flush()
    mon2.flush()
    mon3.flush()

    return [mags, dists, lons, lats, trts, pnes]


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
    return diss_matrix


_DISAGG_RES_NAME_FMT = 'disagg(%(poe)s)-rlz-%(rlz)s-%(imt)s-%(wkt)s'


@tasks.oqtask
def save_disagg_matrix(job_id, site_id, bin_edges, trt_names, pmf_dict,
                       rlz_id, investigation_time, imt_str, iml, poe):
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
        poe=poe, rlz=rlz_id, imt=imt_str, wkt=site_wkt)

    output = models.Output.objects.create_output(
        job, disp_name, 'disagg_matrix')

    imt, sa_period, sa_damping = from_string(imt_str)
    mag, dist, lon, lat, eps = bin_edges
    models.DisaggResult.objects.create(
        output=output,
        lt_realization_id=rlz_id,
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
        matrix=pmf_dict,
    )


@tasks.oqtask
def collect_bins(job_id, sources, lt_model, gsims_by_rlz,
                 trt_num, site, curves, bin_edges):
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
    :param site:
        the current site
    :param curves:
        a dictionary with the hazard curves for the given site, for
        all realizations and IMTs
    """
    mon = LightMonitor('disagg', job_id, collect_bins)
    hc = models.OqJob.objects.get(id=job_id).hazard_calculation
    trt_names = tuple(lt_model.tectonic_region_types)

    # generate source, rupture, sites once per site
    source_ruptures = list(hc.gen_ruptures_for_site(site, sources, mon))
    if not source_ruptures:
        return
    logs.LOG.info('Collecting bins from %d ruptures close to %s',
                  sum(len(rupts) for src, rupts in source_ruptures),
                  site.location)

    bins = _collect_bins_data(
        mon, trt_num, source_ruptures, site, curves,
        gsims_by_rlz, hc.intensity_measure_types_and_levels,
        hc.poes_disagg, hc.truncation_level,
        hc.num_epsilon_bins)

    if not bins[0]:  # no contributions for this site
        return

    bins[0] = numpy.array(bins[0], float)
    bins[1] = numpy.array(bins[1], float)
    bins[2] = numpy.array(bins[2], float)
    bins[3] = numpy.array(bins[3], float)
    bins[4] = numpy.array(bins[4], int)

    dic = {}
    for poe in hc.poes_disagg:
        for imt in hc.intensity_measure_types_and_levels:
            for rlz in gsims_by_rlz:
                key = rlz.id, poe, imt
                probs = merge_prob_no_exceed(
                    [pne[key] for pne in bins[5]])
                iml, newbins = probs.iml, [
                    bins[0], bins[1], bins[2], bins[3],
                    bins[4], numpy.array(probs.vals, float)
                    ]
                dic[site.id, rlz.id, poe, imt, iml, trt_names] =\
                    pmf_dict(_arrange_data_in_bins(
                        newbins, bin_edges, len(trt_names)))

    return cPickle.dumps(dic, cPickle.HIGHEST_PROTOCOL)


class DisaggHazardCalculator(ClassicalHazardCalculator):
    """
    A calculator which performs disaggregation calculations in a distributed /
    parallelized fashion.

    See :func:`openquake.hazardlib.calc.disagg.disaggregation` for more
    details about the nature of this type of calculation.
    """
    def get_curves(self, site):
        """
        Get all the relevant hazard curves for the given site.
        Returns a dictionary {(rlz_id, imt) -> curve}.
        """
        dic = {}
        wkt = site.location.wkt2d
        for rlz in self._get_realizations():
            for imt_str in self.hc.intensity_measure_types_and_levels:
                imt = from_string(imt_str)
                [curve] = models.HazardCurveData.objects.filter(
                    location=wkt,
                    hazard_curve__lt_realization=rlz,
                    hazard_curve__imt=imt[0],
                    hazard_curve__sa_period=imt[1],
                    hazard_curve__sa_damping=imt[2])
                if all(x == 0.0 for x in curve.poes):
                    logs.LOG.warn(
                        '* hazard curve %d contains all zero '
                        'probabilities; skipping SRID=4326;%s, rlz=%d, IMT=%s',
                        curve.id, wkt, rlz.id, imt_str)
                    continue
                dic[rlz.id, imt_str] = curve
        return dic

    @EnginePerformanceMonitor.monitor
    def full_disaggregation(self):
        """
        Run the disaggregation phase after hazard curve finalization.
        """
        super(DisaggHazardCalculator, self).post_execute()
        hc = self.hc
        tl = self.hc.truncation_level
        mag_bin_width = self.hc.mag_bin_width
        eps_bins = numpy.linspace(-tl, tl, self.hc.num_epsilon_bins + 1)

        lt_model_ids = []

        arglist = []
        bin_edges = {}
        for site in self.hc.site_collection:
            curves = self.get_curves(site)
            if not curves:
                logs.LOG.warn('* only zero-valued hazard curves found '
                              'for site %s, skipping disaggregation', site)
                continue

            for job_id, srcs, lt_model, gsims_by_rlz, task_no in \
                    self.task_arg_gen():
                lt_model_ids.append(lt_model.id)

                dists, lons, lats = self.bin_dict[lt_model.id, site.id]
                if not dists:
                    logs.LOG.info(
                        'location %s was too far, skipping disaggregation',
                        site.location)
                    continue

                dist_bins, lon_bins, lat_bins = dist_lon_lat_bins(
                    dists, lons, lats, hc.distance_bin_width,
                    hc.coordinate_bin_width)

                trt_num = dict((trt, i) for i, trt in enumerate(
                               lt_model.tectonic_region_types))
                infos = list(models.LtModelInfo.objects.filter(
                             lt_model=lt_model))

                max_mag = max(i.max_mag for i in infos)
                min_mag = min(i.min_mag for i in infos)
                mag_bins = mag_bin_width * numpy.arange(
                    int(numpy.floor(min_mag / mag_bin_width)),
                    int(numpy.ceil(max_mag / mag_bin_width) + 1))

                bin_edges[lt_model.id, site.id] = bins = (
                    mag_bins, dist_bins, lon_bins, lat_bins, eps_bins)

                arglist.append((self.job.id, srcs, lt_model, gsims_by_rlz,
                                trt_num, site, curves, bins))

        # the memory goes in the population of the dictionary below
        with self.monitor('compute disagg matrices'):
            self.result = defaultdict(lambda: defaultdict(float))
            self.parallelize(collect_bins, arglist, self.collect_result)

        with self.monitor('save disagg matrices'):
            alist = []
            for key, dic in self.result.iteritems():
                site_id, rlz_id, poe, imt, iml, trt_names = key
                lt_model = models.LtRealization.objects.get(pk=rlz_id).lt_model
                bins = bin_edges[lt_model.id, site_id]
                alist.append(
                    (job_id, site_id, bins, trt_names, dic,
                     rlz_id, hc.investigation_time, imt, iml, poe))
            self.parallelize(save_disagg_matrix, alist, self.log_percent)

    post_execute = full_disaggregation

    def collect_result(self, result_pik):
        """
        Collect the results coming from collect_bins into self.results,
        a dictionary with key (rlz_id, site, poe, imt) and values
        (mag_bins, dist_bins, lon_bins, lat_bins, trt_bins, eps_bins).
        """
        if result_pik is None:
            return
        with self.monitor('unpickling bins'):
            logs.LOG.debug('Unpickling %dK', len(result_pik) / 1024)
            result = cPickle.loads(result_pik)
        for key, dic in result.iteritems():
            for k, v in dic.iteritems():
                res = self.result[key]
                res[k] = 1. - (1. - res[k]) * (1. - v)
        self.log_percent()
