# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
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


"""
Utility functions related to splitting work into tasks.
"""

import itertools
import math
import time

from celery.task.sets import TaskSet

from openquake.job import Job
from openquake import logs
from openquake.utils import config


# Do not create batches of more than DEFAULT_BLOCK_SIZE celery subtasks.
# Celery cannot cope with these and dies.
DEFAULT_BLOCK_SIZE = 4096


def distribute(cardinality, the_task, (name, data), other_args=None,
               flatten_results=False):
    """Runs `the_task` in a task set with the given `cardinality`.

    The given `data` is portioned across the subtasks in the task set.
    The results returned by the subtasks are returned in a list e.g.:
        [result1, result2, ..]
    If each subtask returns a list that will result in list of lists. Please
    set `flatten_results` to `True` if you want the results to be returned in a
    single list.

    :param int cardinality: The size of the task set.
    :param the_task: A `celery` task callable.
    :param str name: The parameter name under which the portioned `data` is to
        be passed to `the_task`.
    :param data: The `data` that is to be portioned and passed to the subtasks
        for processing.
    :param dict other_args: The remaining (keyword) parameters that are to be
        passed to the subtasks.
    :param bool flatten_results: If set, the results will be returned as a
        single list (as opposed to [[results1], [results2], ..]).
    :returns: A list where each element is a result returned by a subtask.
        The result order is the same as the subtask order.
    """
    logs.HAZARD_LOG.info("cardinality: %s" % cardinality)

    block_size = config.get("tasks", "block_size")
    block_size = int(block_size) if block_size else DEFAULT_BLOCK_SIZE

    logs.HAZARD_LOG.info("block_size: %s" % block_size)

    data_length = len(data)
    logs.HAZARD_LOG.info("data_length: %s" % data_length)

    results = []

    for start in xrange(0, data_length, block_size):
        end = start + block_size
        iresults = _distribute(cardinality, the_task, name, data[start:end],
                               other_args, flatten_results)
        results.extend(iresults)

    return results


def _distribute(cardinality, a_task, name, data, other_args, flatten_results):
    """Runs `a_task` in a task set with the given `cardinality`.

    The given `data` is portioned across the subtasks in the task set.
    The results returned by the subtasks are returned in a list e.g.:
        [result1, result2, ..]
    If each subtask returns a list that will result in list of lists. Please
    set `flatten_results` to `True` if you want the results to be returned in a
    single list.

    :param int cardinality: The size of the task set.
    :param a_task: A `celery` task callable.
    :param str name: The parameter name under which the portioned `data` is to
        be passed to `a_task`.
    :param data: The `data` that is to be portioned and passed to the subtasks
        for processing.
    :param dict other_args: The remaining (keyword) parameters that are to be
        passed to the subtasks.
    :param bool flatten_results: If set, the results will be returned as a
        single list (as opposed to [[results1], [results2], ..]).
    :returns: A list where each element is a result returned by a subtask.
        The result order is the same as the subtask order.
    """
    # Too many local variables
    # pylint: disable=R0914

    def kwargs(data_portion):
        """
        Construct the full set of keyword parameters for the task to be
        invoked.
        """
        params = {name: data_portion}
        if other_args:
            params.update(other_args)
        return params

    data_length = len(data)
    logs.HAZARD_LOG.info("data_length: %s" % data_length)

    subtasks = []
    start = 0
    end = chunk_size = int(data_length / float(cardinality))
    if chunk_size == 0:
        # We were given less data items than the number of subtasks
        # specified.  Spawn at least on subtask even if the data to be
        # processed is empty.
        cardinality = data_length if data_length > 0 else 1
        end = chunk_size = 1

    logs.HAZARD_LOG.info("chunk_size: %s" % chunk_size)

    for _ in xrange(cardinality - 1):
        data_portion = data[start:end]
        subtask = a_task.subtask(**kwargs(data_portion))
        subtasks.append(subtask)
        start = end
        end += chunk_size
    # The last subtask takes the rest of the data.
    data_portion = data[start:]
    subtask = a_task.subtask(**kwargs(data_portion))
    subtasks.append(subtask)

    # At this point we have created all the subtasks and each one got
    # a portion of the data that is to be processed. Now we will create
    # and run the task set.
    the_results = _handle_subtasks(subtasks, flatten_results)
    return the_results


def parallelize(
    cardinality, the_task, kwargs, flatten_results=False, index_tasks=True):
    """Runs `the_task` in a task set with the given `cardinality`.

    All subtasks receive the *same* parameters i.e. whatever was passed via
    `kwargs`.

    :param int cardinality: The size of the task set.
    :param the_task: A `celery` task callable.
    :param dict kwargs: The (keyword) parameters that are to be passed
        to *all* subtasks.
    :param bool flatten_results: If set, the results will be returned as a
        single list (as opposed to [[results1], [results2], ..]).
    :param bool index_tasks: If set, each subtask will receive an additional
        `task_index` parameter it can use for the purpose of diversification.
    :returns: A list where each element is a result returned by a subtask.
        The result order is the same as the subtask order.
    :raises WrongTaskParameters: When a task receives a parameter it does not
        know.
    :raises TaskFailed: When at least one subtask fails (raises an exception).
    """
    logs.HAZARD_LOG.info("cardinality: %s" % cardinality)

    assert isinstance(kwargs, dict), "Parameters must be passed in a dict."
    subtasks = []
    for tidx in xrange(cardinality):
        task_args = kwargs
        if index_tasks:
            task_args["task_index"] = tidx
        subtask = the_task.subtask(**task_args)
        subtasks.append(subtask)

    logs.HAZARD_LOG.info("#subtasks: %s" % len(subtasks))

    # At this point we have created all the subtasks.
    the_results = _handle_subtasks(subtasks, flatten_results)
    return the_results


def _handle_subtasks(subtasks, flatten_results):
    """Start a `TaskSet` with the given `subtasks` and wait for it to finish.

    :param subtasks: The subtasks to run
    :type subtasks: [celery_subtask]
    :param bool flatten_results: If set, the results will be returned as a
        single list (as opposed to [[results1], [results2], ..]).
    :returns: A list where each element is a result returned by a subtask.
        The result order is the same as the subtask order.
    :raises WrongTaskParameters: When a task receives a parameter it does not
        know.
    :raises TaskFailed: When at least one subtask fails (raises an exception).
    """
    result = TaskSet(tasks=subtasks).apply_async()

    # Wait for all subtasks to complete.
    while not result.ready():
        time.sleep(0.25)

    the_results = result.join()

    if flatten_results and the_results:
        if isinstance(the_results, list) or isinstance(the_results, tuple):
            the_results = list(itertools.chain(*the_results))

    return the_results


class JobCompletedError(Exception):
    """
    Exception to be thrown by :func:`check_job_status`
    in case of dealing with already completed job.
    """


def check_job_status(job_id):
    """
    Helper function which is intended to be run by celery task functions.

    :raises JobCompletedError:
        If :meth:`~openquake.job.Job.is_job_completed` returns ``True``
        for ``job_id``.
    """
    job = Job.from_kvs(job_id)
    level = job.params.get('debug') if job and job.params else 'warn'
    logs.init_logs_amqp_send(level=level, job_id=job_id)
    if Job.is_job_completed(job_id):
        raise JobCompletedError(job_id)
