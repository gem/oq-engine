# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""Asynchronous task handler functions. See
:function:`openquake.utils.tasks.distribute` for more information.
"""

from openquake.utils import stats


def completed_task_count(job_id):
    """Given the ID of a currently running calculation, query the stats
    counters in Redis to get the number of completed
    :function:`compute_uhs_task` task executions.

    Successful and failed executions are included in the count.

    :param int job_id:
        ID of the current calculation.
    :returns:
        Number of completed :function:`compute_uhs_task` task executions so
        far.
    """
    success_count = stats.get_counter(job_id, 'h', 'compute_uhs_task', 'i')
    fail_count = stats.get_counter(
        job_id, 'h', 'compute_uhs_task-failures', 'i')

    return (success_count or 0) + (fail_count or 0)


def remaining_tasks_in_block(job_id, num_tasks, start_count):
    """Figures out the numbers of remaining tasks in the current block. This
    should only be called during an active calculation.

    Given the ID of a currently running calculation, query the stats
    counters in Redis and determine when N :function:`compute_uhs_task` tasks
    have been completed (where N is ``num_tasks``).

    The count includes successful task executions as well as failures.

    This function is implemented as a generator which yields the remainging
    number of tasks to be execute in this block. When the target number of
    tasks is reached, a :exception:`StopIteration` is raised.

    :param int job_id:
        ID of the current calculation.
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
