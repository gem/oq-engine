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
import math
import itertools

import numpy

import openquake.hazardlib
import openquake.hazardlib.calc
import openquake.hazardlib.imt

from openquake.engine import writer, logs
from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.calculators.hazard.classical import (
    post_processing as post_proc)
from openquake.engine.db import models
from openquake.engine.utils.tasks import oqtask, map_reduce
from openquake.engine.performance import EnginePerformanceMonitor
from openquake.engine.input import logictree
from openquake.engine.utils.general import block_splitter

from django.db import transaction


def result_list(result, zero, index, n):
    return [result if i == index else zero for i in range(n)]


@oqtask
def compute_hazard_curves(job_id, sources, lt_rlz, ltp, num_rlz):
    """
    Celery task for hazard curve calculator.

    Samples logic trees, gathers site parameters, and calls the hazard curve
    calculator.

    :param int job_id:
        ID of the currently running job.
    :param sources:
        List of :class:`openquake.hazardlib.source.base.SeismicSource` objects
    :param lt_rlz:
        Logic tree realization model to calculate for.
    :param ltp:
        a :class:`openquake.engine.input.LogicTreeProcessor` instance
    :param int num_rlz:
        the total number of realizations

    Return a list of sorted lists of arrays, one for each IMT.
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)
    apply_uncertainties = ltp.parse_source_model_logictree_path(
        lt_rlz.sm_lt_path)
    gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)
    sorted_imts = sorted(hc.intensity_measure_types_and_levels)
    imts = {}
    hazlib = {}
    for imt in sorted_imts:
        hazlib[imt] = haz_general.imt_to_hazardlib(imt)
        imts[hazlib[imt]] = hc.intensity_measure_types_and_levels[imt]

    # Prepare args for the calculator.
    calc_kwargs = {'gsims': gsims,
                   'truncation_level': hc.truncation_level,
                   'time_span': hc.investigation_time,
                   'sources': map(apply_uncertainties, sources),
                   'imts': imts,
                   'sites': hc.site_collection}

    if hc.maximum_distance:
        dist = hc.maximum_distance
        if not hc.prefiltered:  # filter the sources on the worker
            calc_kwargs['source_site_filter'] = openquake.hazardlib.calc.\
                filters.source_site_distance_filter(dist)
        calc_kwargs['rupture_site_filter'] = openquake.hazardlib.calc.\
            filters.rupture_site_distance_filter(dist)

    # mapping "imt" to 2d array of hazard curves: first dimension -- sites,
    # second -- IMLs
    with EnginePerformanceMonitor(
            'computing hazard curves', job_id, compute_hazard_curves):
        dic = openquake.hazardlib.calc.hazard_curve.hazard_curves_poissonian(
            **calc_kwargs)

        if (sum(dic.itervalues()) == 0.0).all():
            # shortcut for filtered sources giving no contribution
            return

        return result_list([dic[hazlib[imt]] for imt in sorted_imts],
                           [0 for imt in sorted_imts],
                           lt_rlz.ordinal, num_rlz)


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
        self.initialize_realizations()

    def task_arg_gen(self, blocksize=None):
        ltp = logictree.LogicTreeProcessor.from_hc(self.hc)
        num_rlz = len(self.rlz_to_sm)
        for lt_rlz in self._get_realizations():
            sm_path = self.rlz_to_sm[lt_rlz]  # source model path
            sources = self.sources_per_model[sm_path]
            preferred_block_size = int(
                math.ceil(float(len(sources)) / self.concurrent_tasks()))
            logs.LOG.info('preferred block size for %s =%d',
                          sm_path, preferred_block_size)
            for block in block_splitter(sources, preferred_block_size):
                yield self.job.id, block, lt_rlz, ltp, num_rlz

    def execute(self):
        """
        Run the core_calc_task in parallel, by passing the arguments
        provided by the .task_arg_gen method. By default it uses the
        parallelize distribution, but it can be overridden is subclasses.
        """
        imtls = self.hc.intensity_measure_types_and_levels
        zeros = make_zeros(self.rlz_to_sm, self.hc.site_collection, imtls)
        task_args = self.initialize_percent(
            self.core_calc_task, self.task_arg_gen())
        all_matrices = map_reduce(
            self.core_calc_task, task_args, self.aggregate, zeros)
        with transaction.commit_on_success(using='job_init'):
            self.save_curves(all_matrices)

    @EnginePerformanceMonitor.monitor
    def aggregate(self, current, new):
        """
        Use the following formula to combine multiple iterations of results:

        `result = 1 - (1 - current) * (1 - new)`

        This is used to incrementally update hazard curve results by combining
        an initial value with some new results. (Each set of new results is
        computed over only a subset of seismic sources defined in the
        calculation model.)

        Parameters are expected to be multi-dimensional numpy arrays, but the
        formula will also work with scalars.

        :param current:
            Numpy array representing the current result matrix value.
        :param new:
            Numpy array representing the new results which need to be
            combined with the current value. This should be the same shape
            as `current`.
        :returns: the updated array
        """
        try:
            if new is None:
                # shortcut for filtered away sources giving no contribution
                return current
            return [[1. - (1. - c) * (1. - n)
                     for c, n in itertools.izip(c1, n1)]
                    for c1, n1 in itertools.izip(current, new)]
        finally:
            self.log_percent()

    @EnginePerformanceMonitor.monitor
    def save_curves(self, all_matrices):
        """
        Create the final output records for hazard curves. This is done by
        copying the in-memory matrices to
        `hzrdr.hazard_curve` (for metadata) and `hzrdr.hazard_curve_data` (for
        the actual curve PoE values). Foreign keys are made from
        `hzrdr.hazard_curve` to `hzrdr.lt_realization` (realization information
        is need to export the full hazard curve results).
        """
        imtls = self.hc.intensity_measure_types_and_levels
        for i, matrices in enumerate(all_matrices):
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
            for imt, matrix in zip(sorted(imtls), matrices):
                hc_im_type, sa_period, sa_damping = models.parse_imt(imt)

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
                    for p, poes in zip(points, matrix)])

    def post_process(self):
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
