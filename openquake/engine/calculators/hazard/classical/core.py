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
Core functionality for the classical PSHA hazard calculator.
"""
import time
import cPickle
import collections

import numpy

from openquake.hazardlib.imt import from_string

from openquake.engine import logs, writer
from openquake.engine.calculators.hazard import general
from openquake.engine.calculators.hazard.classical import (
    post_processing as post_proc)
from openquake.engine.db import models
from openquake.engine.utils import tasks
from openquake.engine.performance import EnginePerformanceMonitor, LightMonitor


@tasks.oqtask
def compute_hazard_curves(job_id, site_coll_pik, sources, gsims_by_rlz):
    """
    This task computes R2 * I hazard curves (each one is a
    numpy array of S * L floats) from the given source_ruptures
    pairs.

    :param job_id:
        ID of the currently running job
    :param sources:
        a block of source objects
    :param gsims_by_rlz:
        a dictionary of gsim dictionaries, one for each realization
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    site_coll = cPickle.loads(site_coll_pik)
    total_sites = len(site_coll)
    imts = general.im_dict_to_hazardlib(
        hc.intensity_measure_types_and_levels)
    curves = dict((rlz, dict((imt, numpy.ones([total_sites, len(imts[imt])]))
                             for imt in imts))
                  for rlz in gsims_by_rlz)

    mon1 = LightMonitor('filtering sources', job_id, compute_hazard_curves)
    mon2 = LightMonitor('generating ruptures', job_id, compute_hazard_curves)
    mon3 = LightMonitor('filtering ruptures', job_id, compute_hazard_curves)
    mon4 = LightMonitor('making contexts', job_id, compute_hazard_curves)
    mon5 = LightMonitor('computing poes', job_id, compute_hazard_curves)

    for source in sources:
        t0 = time.time()

        with mon1:
            s_sites = source.filter_sites_by_distance_to_source(
                hc.maximum_distance, site_coll
            ) if hc.maximum_distance else site_coll
            if s_sites is None:
                continue

        with mon2:
            ruptures = list(source.iter_ruptures())
            if not ruptures:
                continue

        for rupture in ruptures:
            with mon3:
                r_sites = rupture.source_typology.\
                    filter_sites_by_distance_to_rupture(
                        rupture, hc.maximum_distance, s_sites
                    ) if hc.maximum_distance else s_sites
                if r_sites is None:
                    continue

            for rlz, curv in curves.iteritems():
                gsim = gsims_by_rlz[rlz][rupture.tectonic_region_type]
                with mon4:
                    sctx, rctx, dctx = gsim.make_contexts(r_sites, rupture)
                with mon5:
                    for imt in imts:
                        poes = gsim.get_poes(sctx, rctx, dctx, imt, imts[imt],
                                             hc.truncation_level)
                        pno = rupture.get_probability_no_exceedance(poes)
                        curv[imt] *= r_sites.expand(pno, placeholder=1)

        logs.LOG.info('job=%d, src=%s:%s, num_ruptures=%d, calc_time=%fs',
                      job_id, source.source_id, source.__class__.__name__,
                      len(ruptures), time.time() - t0)

    mon1.flush()
    mon2.flush()
    mon3.flush()
    mon4.flush()
    mon5.flush()
    # the 0 here is a shortcut for filtered sources giving no contribution;
    # this is essential for performance, we want to avoid returning
    # big arrays of zeros (MS)
    dic = dict((rlz, [0 if (curv[imt] == 1.0).all() else 1. - curv[imt]
                      for imt in sorted(imts)])
               for rlz, curv in curves.iteritems())
    return dic


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

    @EnginePerformanceMonitor.monitor
    def task_completed(self, result):
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
