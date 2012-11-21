# -*- coding: utf-8 -*-
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
Disaggregation calculator core functionality
"""

from openquake import logs
from openquake.calculators.hazard import general as haz_general
from openquake.calculators.hazard.classical import core as classical
from openquake.db import models
from openquake.utils import config
from openquake.utils import general as general_utils
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks


@utils_tasks.oqtask
@stats.count_progress('h')
def disagg_task(job_id, calc_type, block, lt_rlz_id):
    """
    Task wrapper around core hazard curve/disaggregation computation functions.

    :param int job_id:
        ID of the currently running job.
    :param calc_type:
        'hazard_curve' or 'disagg'. This indicates more or less the calculation
        phase; first we must computed all of the hazard curves, then we can
        compute the disaggregation histograms.
    :param block:
        A sequence of work items for this task to process. In the case of
        hazard curve computation, this is a sequence of source IDs. In the case
        of disaggregation, this is a list of points.

        For more info, see
        :func:`openquake.calculators.hazard.classical.core.compute_hazard_curves`
        if ``calc_type`` is 'hazard_curve' and :func:`compute_disagg` if
        ``calc_type`` is 'disagg'.
    :param lt_rlz_id:
        ID of the :class:`openquake.db.models.LtRealization` for this part of
        the computation.
    """
    result = None
    if calc_type == 'hazard_curve':
        result = classical.compute_hazard_curves(job_id, block, lt_rlz_id)
    elif calc_type == 'disagg':
        result = compute_disagg(job_id, block, lt_rlz_id)
    else:
        msg = ('Invalid calculation type "%s";'
               ' expected "hazard_curve" or "disagg"')
        msg %= calc_type
        raise RuntimeError(msg)

    haz_general.signal_task_complete(
        job_id=job_id, num_items=None, calc_type=calc_type)

    return result


def compute_disagg(job_id, points, lt_rlz_id):
    return None


class DisaggHazardCalculator(haz_general.BaseHazardCalculatorNext):

    core_calc_task = disagg_task

    def __init__(self, *args, **kwargs):
        super(DisaggHazardCalculator, self).__init__(*args, **kwargs)

        # Progress counter for hazard curve computation:
        self.progress['hc_total'] = 0
        self.progress['hc_computed'] = 0

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
        self.initialize_pr_data()

        self.record_init_stats()

    def task_arg_gen(self, block_size):
        """
        Generate task args for disaggregation calculations.

        First, args are generated for hazard curve computation. Once those are
        through, args are generated for disagg histogram computation.

        :param int block_size:
            The number of items per task. In this case, this the number of
            sources for hazard curve calc task, or number of sites for disagg
            calc tasks.
        """
        realizations = models.LtRealization.objects.filter(
            hazard_calculation=self.hc, is_complete=False)

        # first, distribute tasks for hazard curve computation
        for lt_rlz in realizations:
            source_progress = models.SourceProgress.objects.filter(
                is_complete=False, lt_realization=lt_rlz).order_by('id')
            source_ids = source_progress.values_list(
                'parsed_source_id', flat=True)

            self.progress['total'] += len(source_ids)
            # keep track of hazard curves separately, so we can know when the
            # hazard curve phase is completed
            self.progress['hc_total'] += len(source_ids)
            for block in general_utils.block_splitter(source_ids, block_size):
                # job_id, calc type, source id block, lt rlz
                yield (self.job.id, 'hazard_curve', block, lt_rlz.id)

        # then distribute tasks for disaggregation histogram computation
        all_points = list(self.hc.points_to_compute())
        for lt_rlz in realizations:
            for block in general_utils.block_splitter(all_points, block_size):
                # job_id, calc type, point block, lt rlz
                yield (self.job.id, 'disagg', block, lt_rlz.id)
