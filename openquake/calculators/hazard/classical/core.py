# Copyright (c) 2010-2012, GEM Foundation.
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

import nhlib
import nhlib.calc
import nhlib.imt

from django.db import transaction

from openquake import logs
from openquake.calculators.hazard import general as haz_general
from openquake.db import models
from openquake.input import logictree
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks

from openquake.db.aggregate_result_writer import (MeanCurveWriter,
                                                  QuantileCurveWriter)
from openquake.calculators.hazard.classical import post_processing


@utils_tasks.oqtask
@stats.count_progress('h')
def hazard_curves(job_id, src_ids, lt_rlz_id):
    """
    A celery task wrapper function around :func:`compute_hazard_curves`.
    See :func:`compute_hazard_curves` for parameter definitions.
    """
    logs.LOG.debug('> starting task: job_id=%s, lt_realization_id=%s'
                   % (job_id, lt_rlz_id))

    compute_hazard_curves(job_id, src_ids, lt_rlz_id)
    # Last thing, signal back the control node to indicate the completion of
    # task. The control node needs this to manage the task distribution and
    # keep track of progress.
    logs.LOG.debug('< task complete, signalling completion')
    haz_general.signal_task_complete(job_id=job_id, num_items=len(src_ids))


# Silencing 'Too many local variables'
# pylint: disable=R0914
def compute_hazard_curves(job_id, src_ids, lt_rlz_id):
    """
    Celery task for hazard curve calculator.

    Samples logic trees, gathers site parameters, and calls the hazard curve
    calculator.

    Once hazard curve data is computed, result progress updated (within a
    transaction, to prevent race conditions) in the
    `htemp.hazard_curve_progress` table.

    Once all of this work is complete, a signal will be sent via AMQP to let
    the control node know that the work is complete. (If there is any work left
    to be dispatched, this signal will indicate to the control node that more
    work can be enqueued.)

    :param int job_id:
        ID of the currently running job.
    :param src_ids:
        List of ids of parsed source models to take into account.
    :param lt_rlz_id:
        Id of logic tree realization model to calculate for.
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)

    lt_rlz = models.LtRealization.objects.get(id=lt_rlz_id)
    ltp = logictree.LogicTreeProcessor(hc.id)

    apply_uncertainties = ltp.parse_source_model_logictree_path(
            lt_rlz.sm_lt_path)
    gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)

    sources = haz_general.gen_sources(
        src_ids, apply_uncertainties, hc.rupture_mesh_spacing,
        hc.width_of_mfd_bin, hc.area_source_discretization)

    imts = haz_general.im_dict_to_nhlib(hc.intensity_measure_types_and_levels)

    # Now initialize the site collection for use in the calculation.
    # If there is no site model defined, we will use the same reference
    # parameters (defined in the HazardCalculation) for every site.

    # TODO: We could just create the SiteCollection once, pickle it, and store
    # it in the DB (in SiteData). Creating the SiteCollection isn't an
    # expensive operation (at least for small calculations), but this is
    # wasted work.
    logs.LOG.debug('> creating site collection')
    site_coll = haz_general.get_site_collection(hc)
    logs.LOG.debug('< done creating site collection')

    # Prepare args for the calculator.
    calc_kwargs = {'gsims': gsims,
                   'truncation_level': hc.truncation_level,
                   'time_span': hc.investigation_time,
                   'sources': sources,
                   'imts': imts,
                   'sites': site_coll}

    if hc.maximum_distance:
        dist = hc.maximum_distance
        calc_kwargs['source_site_filter'] = (
                nhlib.calc.filters.source_site_distance_filter(dist))
        calc_kwargs['rupture_site_filter'] = (
                nhlib.calc.filters.rupture_site_distance_filter(dist))

    # mapping "imt" to 2d array of hazard curves: first dimension -- sites,
    # second -- IMLs
    logs.LOG.debug('> computing hazard matrices')
    matrices = nhlib.calc.hazard_curve.hazard_curves_poissonian(**calc_kwargs)
    logs.LOG.debug('< done computing hazard matrices')

    logs.LOG.debug('> starting transaction')
    with transaction.commit_on_success():
        logs.LOG.debug('looping over IMTs')

        for imt in hc.intensity_measure_types_and_levels.keys():
            logs.LOG.debug('> updating hazard for IMT=%s' % imt)
            nhlib_imt = haz_general.imt_to_nhlib(imt)
            query = """
            SELECT * FROM htemp.hazard_curve_progress
            WHERE lt_realization_id = %s
            AND imt = %s
            FOR UPDATE"""
            [hc_progress] = models.HazardCurveProgress.objects.raw(
                query, [lt_rlz.id, imt])

            hc_progress.result_matrix = update_result_matrix(
                hc_progress.result_matrix, matrices[nhlib_imt])
            hc_progress.save()

            logs.LOG.debug('< done updating hazard for IMT=%s' % imt)

        # Before the transaction completes:

        # Check here if any of records in source progress model
        # with parsed_source_id from src_ids are marked as complete,
        # and rollback and abort if there is at least one
        src_prog = models.SourceProgress.objects.filter(
            lt_realization=lt_rlz, parsed_source__in=src_ids)

        if any(x.is_complete for x in src_prog):
            msg = (
                'One or more `source_progress` records were marked as '
                'complete. This was unexpected and probably means that the'
                ' calculation workload was not distributed properly.'
            )
            logs.LOG.critical(msg)
            transaction.rollback()
            raise RuntimeError(msg)

        # Mark source_progress records as complete
        src_prog.update(is_complete=True)

        # Update realiation progress,
        # mark realization as complete if it is done
        haz_general.update_realization(lt_rlz.id, len(src_ids))

    logs.LOG.debug('< transaction complete')


class ClassicalHazardCalculator(haz_general.BaseHazardCalculatorNext):
    """
    Classical PSHA hazard calculator. Computes hazard curves for a given set of
    points.

    For each realization of the calculation, we randomly sample source models
    and GMPEs (Ground Motion Prediction Equations) from logic trees.
    """

    #: The core calculation Celery task function, which accepts the arguments
    #: generated by :func:`task_arg_gen`.
    core_calc_task = hazard_curves

    def task_arg_gen(self, block_size):
        """
        Loop through realizations and sources to generate a sequence of
        task arg tuples. Each tuple of args applies to a single task.

        Yielded results are triples of (job_id, realization_id,
        source_id_list).

        :param int block_size:
            The (max) number of work items for each each task. In this case,
            sources.
        """
        realizations = models.LtRealization.objects.filter(
                hazard_calculation=self.hc, is_complete=False)

        for lt_rlz in realizations:
            source_progress = models.SourceProgress.objects.filter(
                    is_complete=False, lt_realization=lt_rlz).order_by('id')
            source_ids = source_progress.values_list('parsed_source_id',
                                                     flat=True)

            for offset in xrange(0, len(source_ids), block_size):
                task_args = (
                    self.job.id,
                    source_ids[offset:offset + block_size],
                    lt_rlz.id
                )
                yield task_args

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails: parsing and
        initializing sources, parsing and initializing the site model (if there
        is one), and generating logic tree realizations. (The latter piece
        basically defines the work to be done in the `execute` phase.)
        """

        # Parse logic trees and create source Inputs.
        self.initialize_sources()

        # Deal with the site model and compute site data for the calculation
        # (if a site model was specified, that is).
        self.initialize_site_model()

        # Now bootstrap the logic tree realizations and related data.
        # This defines for us the "work" that needs to be done when we reach
        # the `execute` phase.
        # This will also stub out hazard curve result records. Workers will
        # update these periodically with partial results (partial meaning,
        # result curves for just a subset of the overall sources) when some
        # work is complete.
        self.initialize_realizations(
            rlz_callbacks=[self.initialize_hazard_curve_progress])

        self.record_init_stats()

        # Set the progress counters:
        num_sources = models.SourceProgress.objects.filter(
            is_complete=False,
            lt_realization__hazard_calculation=self.hc).count()
        self.progress['total'] = num_sources

        self.initialize_pr_data()

    def post_execute(self):
        """
        Post-execution actions. At the moment, all we do is finalize the hazard
        curve results. See
        :meth:`openquake.calculators.hazard.general.BaseHazardCalculatorNext.finalize_hazard_curves`
        for more info.
        """
        self.finalize_hazard_curves()

    def clean_up(self):
        """
        Delete temporary database records. These records represent intermediate
        copies of final calculation results and are no longer needed.

        In this case, this includes all of the data for this calculation in the
        tables found in the `htemp` schema space.
        """
        logs.LOG.debug('> cleaning up temporary DB data')
        models.HazardCurveProgress.objects.filter(
            lt_realization__hazard_calculation=self.hc.id).delete()
        models.SourceProgress.objects.filter(
            lt_realization__hazard_calculation=self.hc.id).delete()
        models.SiteData.objects.filter(hazard_calculation=self.hc.id).delete()
        logs.LOG.debug('< done cleaning up temporary DB data')

    def post_process(self):
        logs.LOG.debug('> starting post processing')

        # If `mean_hazard_curves` is True and/or `quantile_hazard_curves`
        # has some value (not an empty list), do post processing.
        # Otherwise, just skip it altogether.
        if self.hc.mean_hazard_curves or self.hc.quantile_hazard_curves:
            tasks = post_processing.setup_tasks(
                self.job, self.job.hazard_calculation,
                curve_finder=models.HazardCurveData.objects,
                writers=dict(mean_curves=MeanCurveWriter,
                             quantile_curves=QuantileCurveWriter))

            utils_tasks.distribute(
                    post_processing.do_post_process,
                    ("post_processing_task", tasks),
                    tf_args=dict(job_id=self.job.id))

        if len(self.hc.poes_hazard_maps) > 0:
            post_processing.do_hazard_map_post_process(self.job)

        logs.LOG.debug('< done with post processing')


def update_result_matrix(current, new):
    """
    Use the following formula to combine multiple iterations of results:

    `result = 1 - (1 - current) * (1 - new)`

    This is used to incrementally update hazard curve results by combining an
    initial value with some new results. (Each set of new results is computed
    over only a subset of seismic sources defined in the calculation model.)

    Parameters are expected to be multi-dimensional numpy arrays, but the
    formula will also work with scalars.

    :param current:
        Numpy array representing the current result matrix value.
    :param new:
        Numpy array representing the new results which need to be combined with
        the current value. This should be the same shape as `current`.
    """
    return 1 - (1 - current) * (1 - new)
