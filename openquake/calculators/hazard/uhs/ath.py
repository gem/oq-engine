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


"""Asynchronous task handler functions. See
:function:`openquake.utils.tasks.distribute` for more information.
"""

import time

from openquake import logs
from openquake.utils import stats


def completed_task_count(job_id):
    """Given the ID of a currently running calculation, query the stats
    counters in Redis to get the number of completed
    :function:`compute_uhs_task` task executions.

    Successful and failed executions are included in the count.

    :param int job_id:
        ID of the current job.
    :returns:
        Number of completed :function:`compute_uhs_task` task executions so
        far.
    """
    success_count = stats.pk_get(job_id, "nhzrd_done")
    fail_count = stats.pk_get(job_id, "nhzrd_failed")

    return (success_count or 0) + (fail_count or 0)


def remaining_tasks_in_block(job_id, num_tasks, start_count):
    """Figures out the numbers of remaining tasks in the current block. This
    should only be called during an active job.

    Given the ID of a currently running calculation, query the stats
    counters in Redis and determine when N :function:`compute_uhs_task` tasks
    have been completed (where N is ``num_tasks``).

    The count includes successful task executions as well as failures.

    This function is implemented as a generator which yields the remaining
    number of tasks to be execute in this block. When the target number of
    tasks is reached, a :exception:`StopIteration` is raised.

    :param int job_id:
        ID of the current job.
    :param int num_tasks:
        Number of :function:`compute_uhs_task` tasks in this block.
    :param int start_count:
        The starting total of :function:`compute_uhs_task` tasks completed.

        At the beginning of the calculation, this will be 0 of course. At the
        beginning of subsequent blocks, it needs to be computed _before_
        starting both the block calculation and the async task handler (to
        avoid a possible race condition with the task counters).
    :yields:
        The remaining number of tasks to be executed in this block.
    :raises:
        :exception:`StopIteration` when all block tasks are complete
        (successful or not).
    """
    target = start_count + num_tasks
    while completed_task_count(job_id) < target:
        yield target - completed_task_count(job_id)  # number remaining


def uhs_task_handler(job_id, num_tasks, start_count):
    """Async task handler for counting calculation results and determining when
    a batch of tasks is complete.

    This function periodically polls the task counters in Redis and blocks
    until the current block of tasks is finished.

    :param int job_id:
        The ID of the currently running job.
    :param int num_tasks:
        The number of tasks in the current block.
    :param int start_count:
        The number of tasks completed so far in the job.
    """
    remaining_gen = remaining_tasks_in_block(job_id, num_tasks, start_count)

    while True:
        time.sleep(0.5)
        try:
            remaining_gen.next()
        except StopIteration:
            # No more tasks remaining in this batch.
            break
        logs.log_percent_complete(job_id, "hazard")
