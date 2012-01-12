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

import inspect
import itertools

from celery.task.sets import TaskSet

from openquake import logs


def _prepare_kwargs(name, data, other_args, func=None):
    """
    Construct the (full) set of keyword parameters for the task to be
    invoked and/or its associated asynchronous task handler function.

    If a `func` is passed it will be inspected and only parameters it is
    prepared to receive will be included in the resulting `dict`.

    """
    params = dict(other_args, **{name: data}) if other_args else {name: data}
    if func:
        # A function was passed, remove params it is not prepared to receive.
        func_params = inspect.getargspec(func).args
        filtered_params = [(k, params[k]) for k in params if k in func_params]
        params = dict(filtered_params)
    return params


# Too many local variables
# pylint: disable=R0914
def distribute(cardinality, a_task, (name, data), other_args=None,
               flatten_results=False, ath=None):
    """Runs `a_task` in a task set with the given `cardinality`.

    The given `data` is portioned across the subtasks in the task set.
    The results returned by the subtasks are returned in a list e.g.:
        [result1, result2, ..]

    If each subtask returns a list that will result in list of lists. Please
    set `flatten_results` to `True` if you want the results to be returned in a
    single list.

    Please note that for tasks with ignore_result=True
        - no results are returned
        - the control flow returns to the caller immediately i.e. this
          function does *not* block while the tasks are running unless
          the caller specifies an asynchronous task handler function.
        - if specified, an asynchronous task handler function (`ath`)
          will be run as soon as the tasks have been started.
          It can be used to check/wait for task results as appropriate
          and is likely to execute in parallel with longer running tasks.

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
    :param ath: an asynchronous task handler function, may only be specified
        for a task whose results are ignored.
    :returns: A list where each element is a result returned by a subtask.
        If an `ath` function is passed we return whatever it returns.
    """
    data_length = len(data)
    logs.HAZARD_LOG.debug("-data_length: %s" % data_length)

    subtasks = []
    start = 0
    end = chunk_size = int(data_length / float(cardinality))
    if chunk_size == 0:
        # We were given less data items than the number of subtasks
        # specified.  Spawn at least on subtask even if the data to be
        # processed is empty.
        cardinality = data_length if data_length > 0 else 1
        end = chunk_size = 1

    logs.HAZARD_LOG.debug("-chunk_size: %s" % chunk_size)

    for _ in xrange(cardinality - 1):
        data_portion = data[start:end]
        subtask = a_task.subtask(**_prepare_kwargs(name, data_portion,
                                                   other_args))
        subtasks.append(subtask)
        start = end
        end += chunk_size
    # The last subtask takes the rest of the data.
    data_portion = data[start:]
    subtask = a_task.subtask(**_prepare_kwargs(name, data_portion, other_args))
    subtasks.append(subtask)

    # At this point we have created all the subtasks and each one got
    # a portion of the data that is to be processed. Now we will create
    # and run the task set.
    logs.HAZARD_LOG.debug("-#subtasks: %s" % len(subtasks))
    if a_task.ignore_result:
        TaskSet(tasks=subtasks).apply_async()
        # Did the user specify a asynchronous task handler function?
        if ath:
            params = _prepare_kwargs(name, data, other_args, ath)
            return ath(**params)
    else:
        # Only called when we expect result messages to come back.
        return _handle_subtasks(subtasks, flatten_results)


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
    logs.HAZARD_LOG.debug("cardinality: %s" % cardinality)

    assert isinstance(kwargs, dict), "Parameters must be passed in a dict."
    subtasks = []
    for tidx in xrange(cardinality):
        task_args = kwargs
        if index_tasks:
            task_args["task_index"] = tidx
        subtask = the_task.subtask(**task_args)
        subtasks.append(subtask)

    logs.HAZARD_LOG.debug("#subtasks: %s" % len(subtasks))

    # At this point we have created all the subtasks.
    the_results = _handle_subtasks(subtasks, flatten_results)
    return the_results


def _check_exception(results):
    """If any of the results is an exception, raise it."""
    for result in results:
        if isinstance(result, Exception):
            raise result


def _handle_subtasks(subtasks, flatten_results):
    """Start a `TaskSet` with the given `subtasks` and wait for it to finish.

    :param subtasks: The subtasks to run
    :type subtasks: [celery_subtask]
    :param bool flatten_results: If set, the results will be returned as a
        single list (as opposed to [[results1], [results2], ..]).
    :returns: A list where each element is a result returned by a subtask
        or `None` if the task's results are ignored.
    :raises WrongTaskParameters: When a task receives a parameter it does not
        know.
    :raises TaskFailed: When at least one subtask fails (raises an exception).
    """
    result = TaskSet(tasks=subtasks).apply_async()

    the_results = result.join_native()
    _check_exception(the_results)

    if flatten_results and the_results:
        if isinstance(the_results, list) or isinstance(the_results, tuple):
            the_results = list(itertools.chain(*the_results))

    return the_results


class JobCompletedError(Exception):
    """
    Exception to be thrown by :func:`check_job_status`
    in case of dealing with already completed job.
    """


def get_running_calculation(calculation_id):
    """Helper function which is intended to be run by celery task functions.

    Given the id of an in-progress calculation
    (:class:`openquake.db.models.OqCalculation`), load all of the calculation
    data from the database and KVS and return a
    :class:`openquake.engine.CalculationProxy` object.

    If the calculation is not currently running, a
    :exception:`JobCompletedError` is raised.

    :returns:
        :class:`openquake.engine.CalculationProxy` object, representing an
        in-progress calculation. This object is created from cached data in the
        KVS as well as data stored in the relational database.
    :raises JobCompletedError:
        If :meth:`~openquake.engine.CalculationProxy.is_job_completed` returns
        ``True`` for ``calculation_id``.
    """
    # pylint: disable=W0404
    from openquake.engine import CalculationProxy

    if CalculationProxy.is_job_completed(calculation_id):
        raise JobCompletedError(calculation_id)

    calc_proxy = CalculationProxy.from_kvs(calculation_id)
    if calc_proxy and calc_proxy.params:
        level = calc_proxy.params.get('debug')
    else:
        level = 'warn'
    logs.init_logs_amqp_send(level=level, job_id=calculation_id)

    return calc_proxy


def calculator_for_task(calculation_id):
    """Given the id of an in-progress calculation
    (:class:`openquake.db.models.OqCalculation`), load all of the calculation
    data from the database and KVS and instantiate the calculator required for
    a task's computation.

    :returns:
        An instance of a calculator classed. The type of calculator depends on
        the job type (hazard or risk) and the calculation mode (classical,
        event based, etc.).
    :rtype:
        Subclass of :class:`openquake.calculators.base.Calculator`.
    :raises JobCompletedError:
        If the specified calculation is not currently running.
    """
    # pylint: disable=W0404
    from openquake.engine import CalculationProxy
    from openquake.calculators.hazard import CALCULATORS

    calc_proxy = get_running_calculation(calculation_id)
    calc_mode = calc_proxy.oq_job_profile.calc_mode
    calculator = CALCULATORS[calc_mode](calc_proxy)

    return calculator
