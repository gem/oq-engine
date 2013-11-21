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

from celery.task.sets import TaskSet
from celery.task import task

from openquake.engine import logs, no_distribute
from openquake.engine.db import models
from openquake.engine.utils import config
from openquake.engine.writer import CacheInserter
from openquake.engine.performance import EnginePerformanceMonitor


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


def oqtask(task_func):
    """
    Task function decorator which sets up logging and catches (and logs) any
    errors which occur inside the task. Also checks to make sure the job is
    actually still running. If it is not running, the task doesn't get
    executed, so we don't do useless computation.
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
        job = models.OqJob.objects.get(id=job_id)
        if job.is_running is False:
            # the job was killed, it is useless to run the task
            return

        # it is important to save the task id soon, so that
        # the revoke functionality can work
        EnginePerformanceMonitor.store_task_id(job_id, tsk)

        with EnginePerformanceMonitor(
                'total ' + task_func.__name__, job_id, tsk, flush=True):

            with EnginePerformanceMonitor(
                    'loading calculation object', job_id, tsk, flush=True):
                calculation = job.calculation

            # tasks write on the celery log file
            logs.init_logs(
                level=job.log_level,
                calc_domain='hazard' if isinstance(
                    calculation, models.HazardCalculation) else'risk',
                calc_id=calculation.id)
            try:
                return task_func(*args, **kwargs)
            finally:
                CacheInserter.flushall()
                # the task finished, we can remove from the performance
                # table the associated row 'storing task id', then the
                # supervisor will not try revoke it without need
                models.Performance.objects.filter(
                    oq_job=job,
                    operation='storing task id',
                    task_id=tsk.request.id).delete()
    celery_queue = config.get('amqp', 'celery_queue')
    tsk = task(wrapped, queue=celery_queue)
    return tsk
