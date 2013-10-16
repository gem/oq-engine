# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


"""Utility functions related to splitting work into tasks."""

from functools import wraps
from datetime import datetime

from celery.task.sets import TaskSet
from celery.task import task

from openquake.engine import logs, no_distribute
from openquake.engine.db import models
from openquake.engine.utils import config
from openquake.engine.writer import CacheInserter
from openquake.engine.performance import EnginePerformanceMonitor, LightMonitor


def _map_reduce(task_func, task_args, agg, acc):
    """
    Given a callable and an iterable of positional arguments, apply the
    callable to the arguments in parallel and return an aggregate
    result depending on the initial value of the accumulator
    and on the aggregation function. To save memory, the order is
    not preserved and there is no list with the intermediated results:
    the accumulator is incremented as soon as a task result comes.

    :param task_func: a `celery` task callable.
    :param task_args: an iterable over positional arguments
    :param agg: the aggregation function, (acc, val) -> new acc
    :param acc: the initial value of the accumulator
    :returns: the final value of the accumulator

    NB: if the environment variable OQ_NO_DISTRIBUTE is set the
    tasks are run sequentially in the current process and then
    map_reduce(task_func, task_args, agg, acc) is the same as
    reduce(agg, itertools.starmap(task_func, task_args), acc).
    Users of map_reduce should be aware of the fact that when
    thousands of tasks are spawned and large arguments are passed
    or large results are returned they may incur in memory issue:
    this is way the calculators limit the queue with the
    `concurrent_task` concept.
    """
    if no_distribute():
        for the_args in task_args:
            acc = agg(acc, task_func(*the_args))
    else:
        taskset = TaskSet(tasks=map(task_func.subtask, task_args))
        for result in taskset.apply_async():
            if isinstance(result, Exception):
                # TODO: kill all the other tasks
                raise result
            acc = agg(acc, result)
    return acc


# used to implement BaseCalculator.parallelize, which takes in account
# the `concurrent_task` concept to avoid filling the Celery queue
def parallelize(task_func, task_args, side_effect=lambda val: None):
    """
    Given a callable and an iterable of positional arguments, apply the
    callable to the arguments in parallel. It is possible to pass a
    function side_effect(val) which takes the return value of the
    callable and does something with it (such as saving or printing
    it). Notice that the order is not preserved. parallelize returns None.

    :param task_func: a `celery` task callable.
    :param task_args: an iterable over positional arguments
    :param side_effect: a function val -> None

    NB: if the environment variable OQ_NO_DISTRIBUTE is set the
    tasks are run sequentially in the current process.
    """
    def noagg(acc, val):
        side_effect(val)

    _map_reduce(task_func, task_args, noagg, None)


class JobCompletedError(Exception):
    """
    Exception to be thrown by :func:`oqtask` in case of dealing with already
    completed job.
    """


def oqtask(task_func):
    """
    Task function decorator which sets up logging and catches (and logs) any
    errors which occur inside the task. Also checks to make sure the job is
    actually still running. If it is not running, raise a
    :exc:`JobCompletedError`. (This also means that the task doesn't get
    executed, so we don't do useless computation.)
    """
    @wraps(task_func)
    def wrapped(*args, **kwargs):
        """
        Initialize logs, make sure the job is still running, and run the task
        code surrounded by a try-except. If any error occurs, log it as a
        critical failure.
        """
        # job_id is always assumed to be the first argument passed to
        # the task, or a keyword argument
        # this is the only required argument
        job_id = kwargs.get('job_id') or args[0]

        with EnginePerformanceMonitor(
                'totals per task', job_id, tsk, flush=True):
            job = models.OqJob.objects.get(id=job_id)

            # it is important to save the task ids soon, so that
            # the revoke functionality implemented in supervisor.py can work
            EnginePerformanceMonitor.store_task_id(job_id, tsk)

            with EnginePerformanceMonitor(
                    'loading calculation object', job_id, tsk, flush=True):
                calculation = job.calculation

            # Set up logging via amqp.
            if isinstance(calculation, models.HazardCalculation):
                logs.init_logs_amqp_send(level=job.log_level,
                                         calc_domain='hazard',
                                         calc_id=calculation.id)
            else:
                logs.init_logs_amqp_send(level=job.log_level,
                                         calc_domain='risk',
                                         calc_id=calculation.id)

            try:
                # Tasks can be used in the `execute` or `post-process` phase
                if job.is_running is False:
                    raise JobCompletedError('Job %d was killed' % job_id)
                elif job.status not in ('executing', 'post_processing'):
                    raise JobCompletedError(
                        'The status of job %d is %s, should be executing or '
                        'post_processing' % (job_id, job.status))
                # else continue with task execution
                res = task_func(*args, **kwargs)
            # TODO: should we do something different with JobCompletedError?
            except Exception, err:
                logs.LOG.critical('Error occurred in task: %s', err)
                logs.LOG.exception(err)
                raise
            else:
                return res
            finally:
                CacheInserter.flushall()
    celery_queue = config.get('amqp', 'celery_queue')
    tsk = task(wrapped, ignore_result=True, queue=celery_queue)
    return tsk


# NB: the plan is to remove oqtask eventually, and to use montask instead
# this will require replace the distribution with parallelize everywhere
def montask(task_func):
    """
    Monitoring task decorator: it calls the task_func several times,
    by passing to it a LightMonitor instance and then the arguments.
    At the end the monitoring information is saved in the performance
    table.
    """
    @wraps(task_func)
    def wrapped(*chunks):
        """
        The arguments of the wrapped function are collected in chunks;
        each chunk has the form (job_id, src_id, ...). The wrapped function
        calls the task_func several times, by passing to it a task_mon
        and a chunk of arguments.
        """
        job_id = chunks[0][0]
        # job_id is always assumed to be the first argument passed to the task
        # this is the only required argument
        with LightMonitor({}, 'totals per task') as task_mon:
            job = models.OqJob.objects.get(id=job_id)
            if not job.is_running:
                return  # don't run the task

            # it is important to save the task ids soon, so that
            # the revoke functionality implemented in supervisor.py can work
            EnginePerformanceMonitor.store_task_id(job_id, tsk)

            with EnginePerformanceMonitor(
                    'loading calculation object', job_id, tsk, flush=True):
                calculation = job.calculation

            # Set up logging via amqp.
            if isinstance(calculation, models.HazardCalculation):
                logs.init_logs_amqp_send(level=job.log_level,
                                         calc_domain='hazard',
                                         calc_id=calculation.id)
            else:
                logs.init_logs_amqp_send(level=job.log_level,
                                         calc_domain='risk',
                                         calc_id=calculation.id)
            try:
                # run the task with the created monitor
                for args in chunks:
                    task_func(task_mon, *args)
            finally:
                # save the performance information
                for operation in task_mon.counter:
                    start_time, duration = task_mon.counter[operation]
                    models.Performance.objects.create(
                        oq_job_id=job_id,
                        task_id=tsk.request.id,
                        task=tsk.__name__,
                        operation=operation,
                        start_time=datetime.fromtimestamp(start_time),
                        duration=duration)
                CacheInserter.flushall()
    celery_queue = config.get('amqp', 'celery_queue')
    tsk = task(wrapped, queue=celery_queue)
    return tsk
