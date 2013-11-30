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


@oqtask
def compute_hazard_curves(job_id, sources, lt_rlz_id, ltp):
    """
    Celery task for hazard curve calculator.

    Samples logic trees, gathers site parameters, and calls the hazard curve
    calculator.

    :param int job_id:
        ID of the currently running job.
    :param sources:
        List of :class:`openquake.hazardlib.source.base.SeismicSource` objects
    :param lt_rlz_id:
        Id of logic tree realization model to calculate for.
    :param ltp:
        a :class:`openquake.engine.input.LogicTreeProcessor` instance

    Return a sorted array of arrays, one for each IMT.
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)

    lt_rlz = models.LtRealization.objects.get(id=lt_rlz_id)

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
        dist = hc.maximum_distance
        if not hc.prefiltering:  # filter the sources in the worker
            calc_kwargs['source_site_filter'] = openquake.hazardlib.calc.\
                filters.source_site_distance_filter(dist)
        calc_kwargs['rupture_site_filter'] = openquake.hazardlib.calc.\
            filters.rupture_site_distance_filter(dist)

    # mapping "imt" to 2d array of hazard curves: first dimension -- sites,
    # second -- IMLs
    with EnginePerformanceMonitor(
            'computing hazard curves', job_id,
            compute_hazard_curves, tracing=True):
        dic = openquake.hazardlib.calc.hazard_curve.hazard_curves_poissonian(
            **calc_kwargs)
        return numpy.array([dic[imt] for imt in sorted(imts)])


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

    def execute(self):
        """
        Run the core_calc_task in parallel, by passing the arguments
        provided by the .task_arg_gen method. By default it uses the
        parallelize distribution, but it can be overridden is subclasses.
        """
        self.n_sites = len(self.hc.site_collection)
        self.num_imls = [
            len(self.hc.intensity_measure_types_and_levels[imt])
            for imt in sorted(self.hc.intensity_measure_types_and_levels)]

        ltp = logictree.LogicTreeProcessor.from_hc(self.hc)

        for lt_rlz in self._get_realizations():
            task_args = []
            sm = self.rlz_to_sm[lt_rlz]  # source model path
            sources = self.sources_per_model[sm]
            preferred_block_size = int(
                math.ceil(float(len(sources)) / self.concurrent_tasks()))
            for block in block_splitter(sources, preferred_block_size):
                task_args.append((self.job.id, block, lt_rlz.id, ltp))

            # the following line will print out the number of tasks generated
            self.initialize_percent(self.core_calc_task, task_args)

            zeros = numpy.array(
                [numpy.zeros((self.n_sites, n_imls))
                 for n_imls in self.num_imls])
            matrices = map_reduce(
                self.core_calc_task, task_args, self.aggregate, zeros)
            with self.monitor('saving curves'):
                with transaction.commit_on_success(using='job_init'):
                    self.save_curves(lt_rlz, matrices)

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
        result = 1 - (1 - current) * (1 - new)
        self.log_percent()
        return result

    def save_curves(self, rlz, matrices):
        """
        Create the final output records for hazard curves. This is done by
        copying the in-memory matrices to
        `hzrdr.hazard_curve` (for metadata) and `hzrdr.hazard_curve_data` (for
        the actual curve PoE values). Foreign keys are made from
        `hzrdr.hazard_curve` to `hzrdr.lt_realization` (realization information
        is need to export the full hazard curve results).
        """
        im = self.hc.intensity_measure_types_and_levels

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
        for imt, matrix in zip(sorted(im), matrices):
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
                imls=im[imt],
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
