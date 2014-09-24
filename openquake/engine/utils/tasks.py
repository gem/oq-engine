# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2014, GEM Foundation.
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

from celery.result import ResultSet
from celery.app import current_app
from celery.task import task

from openquake.commonlib.general import split_in_blocks
from openquake.commonlib.parallel import \
    TaskManager, safely_call, check_mem_usage, pickle_sequence, no_distribute
from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.utils import config
from openquake.engine.writer import CacheInserter
from openquake.engine.performance import EnginePerformanceMonitor

CONCURRENT_TASKS = int(config.get('celery', 'concurrent_tasks'))


class JobNotRunning(Exception):
    pass


class OqTaskManager(TaskManager):
    """
    A celery-based task manager. The usage is::

      oqm = OqTaskManager(do_something, logs.LOG.progress)
      oqm.send(arg1, arg2)
      oqm.send(arg3, arg4)
      print oqm.aggregate_results(agg, acc)

    Progress report is built-in.
    """
    def submit(self, *args):
        """
        Submit an oqtask with the given arguments to celery and return
        an AsyncResult. If the variable OQ_NO_DISTRIBUTE is set, the
        task function is run in process and the result is returned.
        """
        check_mem_usage()  # log a warning if too much memory is used
        if no_distribute():
            res = safely_call(self.oqtask.task_func, args)
        else:
            piks = pickle_sequence(args)
            self.sent += sum(len(p) for p in piks)
            res = self.oqtask.delay(*piks)
        self.results.append(res)

    def aggregate_result_set(self, agg, acc):
        """
        Loop on a set of celery AsyncResults and update the accumulator
        by using the aggregation function.

        :param agg: the aggregation function, (acc, val) -> new acc
        :param acc: the initial value of the accumulator
        :returns: the final value of the accumulator
        """
        if not self.results:
            return acc
        backend = current_app().backend
        rset = ResultSet(self.results)
        for task_id, result_dict in rset.iter_native():
            check_mem_usage()  # log a warning if too much memory is used
            result = result_dict['result']
            if isinstance(result, BaseException):
                raise result
            self.received += len(result)
            acc = agg(acc, result.unpickle())
            del backend._cache[task_id]  # work around a celery bug
        return acc


def map_reduce(task, task_args, agg, acc, name=None):
    """
    Given a task and an iterable of positional arguments, apply the
    task function to the arguments in parallel and return an aggregate
    result depending on the initial value of the accumulator
    and on the aggregation function. To save memory, the order is
    not preserved and there is no list with the intermediated results:
    the accumulator is incremented as soon as a task result comes.

    NB: if the environment variable OQ_NO_DISTRIBUTE is set the
    tasks are run sequentially in the current process and then
    map_reduce(task, task_args, agg, acc) is the same as
    reduce(agg, itertools.starmap(task, task_args), acc).
    Users of map_reduce should be aware of the fact that when
    thousands of tasks are spawned and large arguments are passed
    or large results are returned they may incur in memory issue:
    this is way the calculators limit the queue with the
    `concurrent_task` concept.

    :param task: a `celery` task callable.
    :param task_args: an iterable over positional arguments
    :param agg: the aggregation function, (acc, val) -> new acc
    :param acc: the initial value of the accumulator
    :returns: the final value of the accumulator
    """
    oqm = OqTaskManager(task, logs.LOG.progress, name)
    for args in task_args:
        oqm.submit(*args)
    return oqm.aggregate_results(agg, acc)


def apply_reduce(task, task_args,
                 agg=lambda a, x: x,
                 acc=None,
                 concurrent_tasks=CONCURRENT_TASKS,
                 weight=lambda item: 1,
                 key=lambda item: 'Unspecified',
                 name=None):
    """
    Apply a task to a tuple of the form (job_id, data, *args)
    by splitting the data in chunks and reduce the results with an
    aggregation function.

    :param task: an oqtask
    :param task_args: the arguments to be passed to the task function
    :param agg: the aggregation function
    :param acc: initial value of the accumulator
    :param concurrent_tasks: hint about how many tasks to generate
    :param weight: function to extract the weight of an item in data
    :param key: function to extract the kind of an item in data
    """
    job_id = task_args[0]
    data = task_args[1]
    args = task_args[2:]
    if not data:
        return acc
    elif len(data) == 1 or not concurrent_tasks:
        return agg(acc, task.task_func(job_id, data, *args))
    blocks = split_in_blocks(data, concurrent_tasks, weight, key)
    alldata = [(job_id, block) + args for block in blocks]
    return map_reduce(task, alldata, agg, acc, name)


# used to implement BaseCalculator.parallelize, which takes in account
# the `concurrent_task` concept to avoid filling the Celery queue
def parallelize(task, task_args, side_effect=lambda val: None):
    """
    Given a celery task and an iterable of positional arguments, apply the
    callable to the arguments in parallel. It is possible to pass a
    function side_effect(val) which takes the return value of the
    callable and does something with it (such as saving or printing
    it). Notice that the order is not preserved. parallelize returns None.

    NB: if the environment variable OQ_NO_DISTRIBUTE is set the
    tasks are run sequentially in the current process.

    :param task: a celery task
    :param task_args: an iterable over positional arguments
    :param side_effect: a function val -> None
    """
    map_reduce(task, task_args, lambda acc, val: side_effect(val), None)


def oqtask(task_func):
    """
    Task function decorator which sets up logging and catches (and logs) any
    errors which occur inside the task. Also checks to make sure the job is
    actually still running. If it is not running, the task doesn't get
    executed, so we don't do useless computation.

    :param task_func: the function to decorate
    """
    def wrapped(*args):
        """
        Initialize logs, make sure the job is still running, and run the task
        code surrounded by a try-except. If any error occurs, log it as a
        critical failure.
        """
        # job_id is always assumed to be the first argument
        job_id = args[0]
        job = models.OqJob.objects.get(id=job_id)
        if job.is_running is False:
            # the job was killed, it is useless to run the task
            raise JobNotRunning(job_id)

        # it is important to save the task id soon, so that
        # the revoke functionality can work
        EnginePerformanceMonitor.store_task_id(job_id, tsk)

        with EnginePerformanceMonitor(
                'total ' + task_func.__name__, job_id, tsk, flush=True):
            # tasks write on the celery log file
            logs.set_level(job.log_level)
            check_mem_usage()  # log a warning if too much memory is used
            try:
                # run the task
                return task_func(*args)
            finally:
                # save on the db
                CacheInserter.flushall()
                # the task finished, we can remove from the performance
                # table the associated row 'storing task id'
                models.Performance.objects.filter(
                    oq_job=job,
                    operation='storing task id',
                    task_id=tsk.request.id).delete()
    celery_queue = config.get('amqp', 'celery_queue')
    f = lambda *args: safely_call(wrapped, args, pickle=True)
    f.__name__ = task_func.__name__
    tsk = task(f, queue=celery_queue)
    tsk.task_func = task_func
    return tsk
