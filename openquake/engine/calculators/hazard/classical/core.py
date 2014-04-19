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
Core functionality for the classical PSHA hazard calculator.
"""
import time
import operator
import itertools
import collections

import numpy

from openquake.hazardlib.imt import from_string
from openquake.hazardlib.geo.utils import get_spherical_bounding_box
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.geodetic import npoints_between

from openquake.engine import logs, writer
from openquake.engine.calculators.hazard import general
from openquake.engine.calculators.hazard.classical import (
    post_processing as post_proc)
from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine.performance import EnginePerformanceMonitor, LightMonitor


class BoundingBox(object):
    """
    A class to store the bounding box in distances, longitudes and magnitudes,
    given a source model and a site. This is used for disaggregation
    calculations. The goal is to determine the minimum and maximum
    distances of the ruptures generated from the model from the site;
    moreover the maximum and minimum longitudes and magnitudes are stored, by
    taking in account the international date line.
    """
    def __init__(self, lt_model_id, site_id):
        self.lt_model_id = lt_model_id
        self.site_id = site_id
        self.min_dist = self.max_dist = None
        self.east = self.west = self.south = self.north = None

    def update(self, dists, lons, lats):
        """
        Compare the current bounding box with the value in the arrays
        dists, lons, lats and enlarge it if needed.

        :param dists:
            a sequence of distances
        :param lons:
            a sequence of longitudes
        :param lats:
            a sequence of latitudes
        """
        if self.min_dist is not None:
            dists = [self.min_dist, self.max_dist] + dists
        if self.west is not None:
            lons = [self.west, self.east] + lons
        if self.south is not None:
            lats = [self.south, self.north] + lats
        self.min_dist, self.max_dist = min(dists), max(dists)
        self.west, self.east, self.north, self.south = \
            get_spherical_bounding_box(lons, lats)

    def update_bb(self, bb):
        """
        Compare the current bounding box with the given bounding box
        and enlarge it if needed.

        :param bb:
            an instance of :class:
            `openquake.engine.calculators.hazard.classical.core.BoundingBox`
        """
        if bb:  # the given bounding box must be non-empty
            self.update([bb.min_dist, bb.max_dist], [bb.west, bb.east],
                        [bb.south, bb.north])

    def bins_edges(self, dist_bin_width, coord_bin_width):
        """
        Define bin edges for disaggregation histograms, from the bin data
        collected from the ruptures.

        :param dists:
            array of distances from the ruptures
        :param lons:
            array of longitudes from the ruptures
        :param lats:
            array of latitudes from the ruptures
        :param dist_bin_width:
            distance_bin_width from job.ini
        :param coord_bin_width:
            coordinate_bin_width from job.ini
        """
        dist_edges = dist_bin_width * numpy.arange(
            int(self.min_dist / dist_bin_width),
            int(numpy.ceil(self.max_dist / dist_bin_width) + 1))

        west = numpy.floor(self.west / coord_bin_width) * coord_bin_width
        east = numpy.ceil(self.east / coord_bin_width) * coord_bin_width
        lon_extent = get_longitudinal_extent(west, east)

        lon_edges, _, _ = npoints_between(
            west, 0, 0, east, 0, 0,
            numpy.round(lon_extent / coord_bin_width) + 1)

        lat_edges = coord_bin_width * numpy.arange(
            int(numpy.floor(self.south / coord_bin_width)),
            int(numpy.ceil(self.north / coord_bin_width) + 1))

        return dist_edges, lon_edges, lat_edges

    def __nonzero__(self):
        """
        True if the bounding box is non empty.
        """
        return (self.min_dist is not None and self.west is not None
                and self.south is not None)


@tasks.oqtask
def compute_hazard_curves(
        job_id, sitecol, sources, lt_model, gsim_by_rlz, task_no):
    """
    This task computes R2 * I hazard curves (each one is a
    numpy array of S * L floats) from the given source_ruptures
    pairs.

    :param job_id:
        ID of the currently running job
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :param sources:
        a block of source objects
    :param lt_model:
        a :class:`openquake.engine.db.LtSourceModel` instance
    :param gsim_by_rlz:
        a dictionary of gsims, one for each realization
    :param int task_no:
        the ordinal number of the current task
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    total_sites = len(sitecol)
    sitemesh = sitecol.mesh
    imts = general.im_dict_to_hazardlib(
        hc.intensity_measure_types_and_levels)
    sorted_imts = sorted(imts)
    curves = dict((rlz, [numpy.ones([total_sites, len(imts[imt])])
                         for imt in sorted_imts])
                  for rlz in gsim_by_rlz)
    if hc.poes_disagg:  # doing disaggregation
        bbs = [BoundingBox(lt_model.id, site_id) for site_id in sitecol.sids]
    else:
        bbs = []
    mon = LightMonitor(
        'getting ruptures', job_id, compute_hazard_curves)
    make_ctxt_mon = LightMonitor(
        'making contexts', job_id, compute_hazard_curves)
    calc_poes_mon = LightMonitor(
        'computing poes', job_id, compute_hazard_curves)

    # NB: rows are a namedtuples with fields (source, rupture, rupture_sites)
    for source, rows in itertools.groupby(
            hc.gen_ruptures(sources, mon, sitecol),
            key=operator.attrgetter('source')):
        t0 = time.time()
        num_ruptures = 0
        for _source, rupture, r_sites in rows:
            num_ruptures += 1
            if hc.poes_disagg:  # doing disaggregation
                jb_dists = rupture.surface.get_joyner_boore_distance(sitemesh)
                closest_points = rupture.surface.get_closest_points(sitemesh)
                for bb, dist, point in zip(bbs, jb_dists, closest_points):
                    if dist < hc.maximum_distance:
                        # ruptures too far away are ignored
                        bb.update([dist], [point.longitude], [point.latitude])

            # compute probabilities for all realizations
            for rlz, curv in curves.iteritems():
                gsim = gsim_by_rlz[rlz]
                with make_ctxt_mon:
                    sctx, rctx, dctx = gsim.make_contexts(r_sites, rupture)
                with calc_poes_mon:
                    for i, imt in enumerate(sorted_imts):
                        poes = gsim.get_poes(sctx, rctx, dctx, imt, imts[imt],
                                             hc.truncation_level)
                        pno = rupture.get_probability_no_exceedance(poes)
                        curv[i] *= r_sites.expand(pno, placeholder=1)

        logs.LOG.info('job=%d, src=%s:%s, num_ruptures=%d, calc_time=%fs',
                      job_id, source.source_id, source.__class__.__name__,
                      num_ruptures, time.time() - t0)

    make_ctxt_mon.flush()
    calc_poes_mon.flush()

    # the 0 here is a shortcut for filtered sources giving no contribution;
    # this is essential for performance, we want to avoid returning
    # big arrays of zeros (MS)
    curve_dict = dict((rlz, [0 if (c == 1.0).all() else 1. - c for c in curv])
                      for rlz, curv in curves.iteritems())
    return curve_dict, bbs


class ClassicalHazardCalculator(general.BaseHazardCalculator):
    """
    Classical PSHA hazard calculator. Computes hazard curves for a given set of
    points.

    For each realization of the calculation, we randomly sample source models
    and GMPEs (Ground Motion Prediction Equations) from logic trees.
    """

    core_calc_task = compute_hazard_curves

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails:
        parsing and initializing sources, parsing and initializing the
        site model (if there is one), parsing vulnerability and
        exposure files and generating logic tree realizations. (The
        latter piece basically defines the work to be done in the
        `execute` phase.).
        """
        super(ClassicalHazardCalculator, self).pre_execute()
        self.imtls = self.hc.intensity_measure_types_and_levels
        realizations = self._get_realizations()
        n_rlz = len(realizations)
        n_levels = sum(len(lvls) for lvls in self.imtls.itervalues()
                       ) / float(len(self.imtls))
        n_sites = len(self.hc.site_collection)
        total = n_rlz * len(self.imtls) * n_levels * n_sites
        logs.LOG.info('Considering %d realization(s), %d IMT(s), %d level(s) '
                      'and %d sites, total %d', n_rlz, len(self.imtls),
                      n_levels, n_sites, total)
        self.curves_by_rlz = collections.OrderedDict(
            (rlz, [numpy.zeros((n_sites, len(self.imtls[imt])))
                   for imt in sorted(self.imtls)])
            for rlz in realizations)
        lt_models = models.LtSourceModel.objects.filter(
            hazard_calculation=self.hc)

        # a dictionary with the bounding boxes for earch source
        # model and each site, defined only for disaggregation
        # calculations:
        if self.hc.poes_disagg:
            self.bb_dict = dict(
                ((lt_model.id, site.id), BoundingBox(lt_model.id, site.id))
                for site in self.hc.site_collection
                for lt_model in lt_models)

    @EnginePerformanceMonitor.monitor
    def task_completed(self, (result, bbs)):
        """
        This is used to incrementally update hazard curve results by combining
        an initial value with some new results. (Each set of new results is
        computed over only a subset of seismic sources defined in the
        calculation model.)

        :param task_result:
            A dictionary rlz -> curves_by_imt where curves_by_imt is a
            list of 2-D numpy arrays representing the new results which need
            to be combined with the current value. These should be the same
            shape as self.curves_by_rlz[rlz][j] where rlz is the realization
            and j is the IMT ordinal.
        """
        for rlz, curves_by_imt in result.iteritems():
            for j, curves in enumerate(curves_by_imt):
                # j is the IMT index
                self.curves_by_rlz[rlz][j] = 1. - (
                    1. - self.curves_by_rlz[rlz][j]) * (1. - curves)
        if self.hc.poes_disagg:
            for bb in bbs:
                self.bb_dict[bb.lt_model_id, bb.site_id].update_bb(bb)
        self.log_percent()

    # this could be parallelized in the future, however in all the cases
    # I have seen until now, the serialized approach is fast enough (MS)
    @EnginePerformanceMonitor.monitor
    def save_hazard_curves(self):
        """
        Post-execution actions. At the moment, all we do is finalize the hazard
        curve results.
        """
        imtls = self.hc.intensity_measure_types_and_levels
        for rlz, curves_by_imt in self.curves_by_rlz.iteritems():
            # create a new `HazardCurve` 'container' record for each
            # realization (virtual container for multiple imts)
            models.HazardCurve.objects.create(
                output=models.Output.objects.create_output(
                    self.job, "hc-multi-imt-rlz-%s" % rlz.id,
                    "hazard_curve_multi"),
                lt_realization=rlz,
                imt=None,
                investigation_time=self.hc.investigation_time)

            # create a new `HazardCurve` 'container' record for each
            # realization for each intensity measure type
            for imt, curves in zip(sorted(imtls), curves_by_imt):
                hc_im_type, sa_period, sa_damping = from_string(imt)

                # save output
                hco = models.Output.objects.create(
                    oq_job=self.job,
                    display_name="Hazard Curve rlz-%s" % rlz.id,
                    output_type='hazard_curve',
                )

                # save hazard_curve
                haz_curve = models.HazardCurve.objects.create(
                    output=hco,
                    lt_realization=rlz,
                    investigation_time=self.hc.investigation_time,
                    imt=hc_im_type,
                    imls=imtls[imt],
                    sa_period=sa_period,
                    sa_damping=sa_damping,
                )

                # save hazard_curve_data
                points = self.hc.points_to_compute()
                logs.LOG.info('saving %d hazard curves for %s, imt=%s',
                              len(points), hco, imt)
                writer.CacheInserter.saveall([
                    models.HazardCurveData(
                        hazard_curve=haz_curve,
                        poes=list(poes),
                        location='POINT(%s %s)' % (p.longitude, p.latitude),
                        weight=rlz.weight)
                    for p, poes in zip(points, curves)])
        del self.curves_by_rlz  # save memory for the post_processing phase

    post_execute = save_hazard_curves

    def post_process(self):
        """
        Optionally generates aggregate curves, hazard maps and
        uniform_hazard_spectra.
        """
        logs.LOG.debug('> starting post processing')

        # means/quantiles:
        if self.hc.mean_hazard_curves or self.hc.quantile_hazard_curves:
            self.do_aggregate_post_proc()

        # hazard maps:
        # required for computing UHS
        # if `hazard_maps` is false but `uniform_hazard_spectra` is true,
        # just don't export the maps
        if self.hc.hazard_maps or self.hc.uniform_hazard_spectra:
            self.parallelize(
                post_proc.hazard_curves_to_hazard_map_task,
                post_proc.hazard_curves_to_hazard_map_task_arg_gen(self.job),
                self.log_percent)

        if self.hc.uniform_hazard_spectra:
            post_proc.do_uhs_post_proc(self.job)

        logs.LOG.debug('< done with post processing')
