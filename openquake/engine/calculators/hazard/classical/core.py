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

import openquake.hazardlib
import openquake.hazardlib.calc
import openquake.hazardlib.imt

from django.db import transaction

from openquake.engine import logs
from openquake.engine.calculators import base
from openquake.engine.calculators.hazard import general as haz_general
from openquake.engine.calculators.hazard.classical import (
    post_processing as post_proc)
from openquake.engine.db import models
from openquake.engine.utils import stats
from openquake.engine.utils import tasks as utils_tasks
from openquake.engine.performance import EnginePerformanceMonitor


@utils_tasks.oqtask
@stats.count_progress('h')
def hazard_curves(job_id, src_ids, lt_rlz_id, ltp):
    """
    A celery task wrapper function around :func:`compute_hazard_curves`.
    See :func:`compute_hazard_curves` for parameter definitions.

    :param ltp:
        a :class:`openquake.engine.input.LogicTreeProcessor` instance
    """
    logs.LOG.debug('> starting task: job_id=%s, lt_realization_id=%s'
                   % (job_id, lt_rlz_id))

    compute_hazard_curves(job_id, src_ids, lt_rlz_id, ltp)
    # Last thing, signal back the control node to indicate the completion of
    # task. The control node needs this to manage the task distribution and
    # keep track of progress.
    logs.LOG.debug('< task complete, signalling completion')
    base.signal_task_complete(job_id=job_id, num_items=len(src_ids))


# Silencing 'Too many local variables'
# pylint: disable=R0914
def compute_hazard_curves(job_id, src_ids, lt_rlz_id, ltp):
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
    :param ltp:
        a :class:`openquake.engine.input.LogicTreeProcessor` instance
    """
    hc = models.HazardCalculation.objects.get(oqjob=job_id)

    lt_rlz = models.LtRealization.objects.get(id=lt_rlz_id)

    apply_uncertainties = ltp.parse_source_model_logictree_path(
        lt_rlz.sm_lt_path)
    gsims = ltp.parse_gmpe_logictree_path(lt_rlz.gsim_lt_path)

    parsed_sources = models.ParsedSource.objects.filter(pk__in=src_ids)

    imts = haz_general.im_dict_to_hazardlib(
        hc.intensity_measure_types_and_levels)

    # Prepare args for the calculator.
    calc_kwargs = {'gsims': gsims,
                   'truncation_level': hc.truncation_level,
                   'time_span': hc.investigation_time,
                   'sources': [apply_uncertainties(s.nrml)
                               for s in parsed_sources],
                   'imts': imts,
                   'sites': hc.site_collection}

    if hc.maximum_distance:
        dist = hc.maximum_distance
        # NB: a better approach could be to filter the sources by distance
        # at the beginning and to sore into the database only the relevant
        # sources, as we do in the event based calculator: I am not doing that
        # for the classical calculators because I wonder about the performance
        # impact in in SHARE-like calculations. So at the moment we store
        # everything in the database and we filter on the workers. This
        # will probably change in the future.
        calc_kwargs['source_site_filter'] = (
            openquake.hazardlib.calc.filters.source_site_distance_filter(dist))
        calc_kwargs['rupture_site_filter'] = (
            openquake.hazardlib.calc.filters.rupture_site_distance_filter(
                dist))

    # mapping "imt" to 2d array of hazard curves: first dimension -- sites,
    # second -- IMLs
    with EnginePerformanceMonitor(
            'computing hazard curves', job_id, hazard_curves, tracing=True):
        matrices = openquake.hazardlib.calc.hazard_curve.\
            hazard_curves_poissonian(**calc_kwargs)

    with EnginePerformanceMonitor(
            'saving hazard curves', job_id, hazard_curves, tracing=True):
        _update_curves(hc, matrices, lt_rlz, src_ids)


def _update_curves(hc, matrices, lt_rlz, src_ids):
    """
    Helper function for updating source, hazard curve, and realization progress
    records in the database.

    This is intended to be used by :func:`compute_hazard_curves`.

    :param hc:
        :class:`openquake.engine.db.models.HazardCalculation` instance.
    :param lt_rlz:
        :class:`openquake.engine.db.models.LtRealization` record for the
        current realization.
    :param src_ids:
        List of source IDs considered for this calculation task.
    """
    with logs.tracing('_update_curves for all IMTs'):
        for imt in hc.intensity_measure_types_and_levels.keys():
            hazardlib_imt = haz_general.imt_to_hazardlib(imt)
            matrix = matrices[hazardlib_imt]
            if (matrix == 0.0).all():
                # The matrix for this IMT is all zeros; there's no reason to
                # update `hazard_curve_progress` records.
                logs.LOG.debug('* No hazard contribution for IMT=%s' % imt)
                continue
            else:
                # The is some contribution here to the hazard; we need to
                # update.
                with transaction.commit_on_success():
                    logs.LOG.debug('> updating hazard for IMT=%s' % imt)
                    query = """
                    SELECT * FROM htemp.hazard_curve_progress
                    WHERE lt_realization_id = %s
                    AND imt = %s
                    FOR UPDATE"""
                    [hc_progress] = models.HazardCurveProgress.objects.raw(
                        query, [lt_rlz.id, imt])

                    hc_progress.result_matrix = update_result_matrix(
                        hc_progress.result_matrix, matrix)
                    hc_progress.save()

                    logs.LOG.debug('< done updating hazard for IMT=%s' % imt)

        with transaction.commit_on_success():
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


class ClassicalHazardCalculator(haz_general.BaseHazardCalculator):
    """
    Classical PSHA hazard calculator. Computes hazard curves for a given set of
    points.

    For each realization of the calculation, we randomly sample source models
    and GMPEs (Ground Motion Prediction Equations) from logic trees.
    """

    core_calc_task = hazard_curves

    def pre_execute(self):
        """
        Do pre-execution work. At the moment, this work entails:
        parsing and initializing sources, parsing and initializing the
        site model (if there is one), parsing vulnerability and
        exposure files and generating logic tree realizations. (The
        latter piece basically defines the work to be done in the
        `execute` phase.).
        """

        # Parse vulnerability and exposure model
        self.parse_risk_models()

        # Deal with the site model and compute site data for the calculation
        # (if a site model was specified, that is).
        self.initialize_site_model()

        # Parse logic trees and create source Inputs.
        self.initialize_sources()

        # Now bootstrap the logic tree realizations and related data.
        # This defines for us the "work" that needs to be done when we reach
        # the `execute` phase.
        # This will also stub out hazard curve result records. Workers will
        # update these periodically with partial results (partial meaning,
        # result curves for just a subset of the overall sources) when some
        # work is complete.
        self.initialize_realizations(
            rlz_callbacks=[self.initialize_hazard_curve_progress])

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
        :meth:`openquake.engine.calculators.hazard.general.\
BaseHazardCalculator.finalize_hazard_curves`
        for more info.
        """
        self.finalize_hazard_curves()

    def clean_up(self):
        """
        Delete temporary database records.
        These records represent intermediate copies of final calculation
        results and are no longer needed.

        In this case, this includes all of the data for this calculation in the
        tables found in the `htemp` schema space.
        """
        logs.LOG.debug('> cleaning up temporary DB data')
        models.HazardCurveProgress.objects.filter(
            lt_realization__hazard_calculation=self.hc.id).delete()
        models.SourceProgress.objects.filter(
            lt_realization__hazard_calculation=self.hc.id).delete()
        logs.LOG.debug('< done cleaning up temporary DB data')

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
                post_proc.hazard_curves_to_hazard_map_task_arg_gen(self.job))

        if self.hc.uniform_hazard_spectra:
            post_proc.do_uhs_post_proc(self.job)

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
