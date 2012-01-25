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


"""Utility functions related to splitting work into tasks."""


import itertools
from celery.task.sets import TaskSet

from openquake import logs


def distribute(task_func, (name, data), tf_args=None, ath=None, ath_args=None):
    """Runs `task_func` for each of the given data items.

    Each subtask operates on a single `data` item.

    Please note that for tasks with ignore_result=True
        - no results are returned
        - the control flow returns to the caller immediately i.e. this
          function does *not* block while the tasks are running unless
          the caller specifies an asynchronous task handler function.
        - if specified, an asynchronous task handler function (`ath`)
          will be run as soon as the tasks have been started.
          It can be used to check/wait for task results as appropriate
          and is likely to execute in parallel with longer running tasks.

    :param task_func: A `celery` task callable.
    :param str name: how the data item should be passed to `task_func`
    :param data: The `data` on which the subtasks will operate
    :param dict tf_args: The remaining (keyword) parameters that are to be
        passed to the subtasks.
    :param ath: an asynchronous task handler function, may only be specified
        for a task whose results are ignored.
    :returns: A list where each element is a result returned by a subtask.
        If an `ath` function is passed we return whatever it returns.
    """
    logs.HAZARD_LOG.debug("-data_length: %s" % len(data))

    subtask = task_func.subtask
    if tf_args:
        subtasks = [subtask(**dict(tf_args.items() + [(name, [item])]))
                    for item in data]
    else:
        subtasks = [subtask(**{name: [item]}) for item in data]

    result = TaskSet(tasks=subtasks).apply_async()
    if task_func.ignore_result:
        # Did the user specify an asynchronous task handler function?
        if ath:
            return ath(**ath_args)
    else:
        # Only called when we expect result messages to come back.
        results = result.join_native()
        _check_exception(results)
        if results:
            sample = results[0]
            if (isinstance(sample, list) or isinstance(sample, tuple)
                or isinstance(sample, set)):
                results = list(itertools.chain(*results))
        return results


def _check_exception(results):
    """If any of the results is an exception, raise it."""
    for result in results:
        if isinstance(result, Exception):
            raise result


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


def calculator_for_task(calculation_id, job_type):
    """Given the id of an in-progress calculation
    (:class:`openquake.db.models.OqCalculation`), load all of the calculation
    data from the database and KVS and instantiate the calculator required for
    a task's computation.

    :param int calculation_id:
        id of a in-progress calculation.
    :params job_type:
        'hazard' or 'risk'
    :returns:
        An instance of a calculator classed. The type of calculator depends on
        the ``job_type`` (hazard or risk) and the calculation mode (classical,
        event based, etc.).
    :rtype:
        Subclass of :class:`openquake.calculators.base.Calculator`.
    :raises JobCompletedError:
        If the specified calculation is not currently running.
    """
    # pylint: disable=W0404
    from openquake.engine import CALCS

    calc_proxy = get_running_calculation(calculation_id)
    calc_mode = calc_proxy.oq_job_profile.calc_mode
    calculator = CALCS[job_type][calc_mode](calc_proxy)

    return calculator
