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
import numpy

import openquake.hazardlib
import openquake.hazardlib.calc
from openquake.hazardlib.imt import from_string

from openquake.engine import logs, writer
from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.calculators.hazard.classical import (
    post_processing as post_proc)
from openquake.engine.db import models
from openquake.engine.utils import tasks as utils_tasks
from openquake.engine.performance import EnginePerformanceMonitor


@utils_tasks.oqtask
def compute_hazard_curves(job_id, sources, lt_rlz, ltp):
    """
    Celery task for hazard curve calculator.

    Samples logic trees, gathers site parameters, and calls the hazard curve
    calculator.

    Once hazard curve data is computed, result progress updated (within a
    transaction, to prevent race conditions) in the
    `htemp.hazard_curve_progress` table.

    :param int job_id:
        ID of the currently running job.
    :param sources:
        List of :class:`openquake.hazardlib.source.base.SeismicSource` objects
    :param lt_rlz:
        a :class:`openquake.engine.db.models.LtRealization` instance
    :param ltp:
        a :class:`openquake.engine.input.LogicTreeProcessor` instance
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    apply_uncertainties = ltp.parse_source_model_logictree_path(
        lt_rlz.sm_lt_path)
    gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)
    imts = haz_general.im_dict_to_hazardlib(
        hc.intensity_measure_types_and_levels)

    # Prepare args for the calculator.
    calc_kwargs = {'gsims': gsims,
                   'truncation_level': hc.truncation_level,
                   'time_span': hc.investigation_time,
                   'sources': map(apply_uncertainties, sources),
                   'imts': imts,
                   'sites': hc.site_collection}

    if hc.maximum_distance:
        calc_kwargs['source_site_filter'] = (
            openquake.hazardlib.calc.filters.source_site_distance_filter(
                hc.maximum_distance))
        calc_kwargs['rupture_site_filter'] = (
            openquake.hazardlib.calc.filters.rupture_site_distance_filter(
                hc.maximum_distance))

    # mapping "imt" to 2d array of hazard curves: first dimension -- sites,
    # second -- IMLs
    with EnginePerformanceMonitor(
            'computing hazard curves', job_id,
            compute_hazard_curves, tracing=True):
        curves = openquake.hazardlib.calc.hazard_curve.\
            hazard_curves_poissonian(**calc_kwargs)
        curves_by_imt = []
        for imt in sorted(imts):
            if (curves[imt] == 0.0).all():
                # shortcut for filtered sources giving no contribution;
                # this is essential for performance, we want to avoid
                # returning big arrays of zeros (MS)
                curves_by_imt.append(None)
            else:
                curves_by_imt.append(curves[imt])
        return curves_by_imt, lt_rlz.ordinal


def make_zeros(realizations, sites, imtls):
    """
    Returns a list of R lists containing I numpy arrays of S * L zeros, where
    R is the number of realizations, I is the number of intensity measure
    types, S the number of sites and L the number of intensity measure levels.

    :params sites: the site collection
    :param imtls: a dictionary of intensity measure types and levels
    """
    return [[numpy.zeros((len(sites), len(imtls[imt])))
             for imt in sorted(imtls)] for _ in range(len(realizations))]


class ClassicalHazardCalculator(haz_general.BaseHazardCalculator):
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
        self.parse_risk_models()
        self.initialize_site_model()
        self.initialize_sources()

        # Now bootstrap the logic tree realizations and related data.
        # This defines for us the "work" that needs to be done when we reach
        # the `execute` phase.
        self.initialize_realizations()
        imtls = self.hc.intensity_measure_types_and_levels
        self.curves_by_rlz = make_zeros(
            self.rlz_to_sm, self.hc.site_collection, imtls)

    @EnginePerformanceMonitor.monitor
    def task_completed(self, task_result):
        """
        This is used to incrementally update hazard curve results by combining
        an initial value with some new results. (Each set of new results is
        computed over only a subset of seismic sources defined in the
        calculation model.)

        :param task_result:
            A pair (curves_by_imt, ordinal) where curves_by_imt is a
            list of 2-D numpy arrays representing the new results which need
            to be combined with the current value. These should be the same
            shape as self.curves_by_rlz[i][j] where i is the realization ordinal
            and j the IMT ordinal.
        """
        curves_by_imt, i = task_result
        for j, matrix in enumerate(curves_by_imt):  # j is the IMT index
            if matrix is not None:
                self.curves_by_rlz[i][j] = 1. - (
                    1. - self.curves_by_rlz[i][j]) * (1. - matrix)
        self.log_percent(task_result)

    # this could be parallelized in the future, however in all the cases
    # I have seen until now, the serialized approach is fast enough (MS)
    @EnginePerformanceMonitor.monitor
    def save_hazard_curves(self):
        """
        Post-execution actions. At the moment, all we do is finalize the hazard
        curve results.
        """
        imtls = self.hc.intensity_measure_types_and_levels
        for i, curves_imts in enumerate(self.curves_by_rlz):
            rlz = models.LtRealization.objects.get(
                hazard_calculation=self.hc, ordinal=i)

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
            for imt, curves_by_imt in zip(sorted(imtls), curves_imts):
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
                    for p, poes in zip(points, curves_by_imt)])
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
