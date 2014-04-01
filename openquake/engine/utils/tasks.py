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

import sys
import cPickle
import traceback

from celery.task.sets import TaskSet
from celery.app import current_app
from celery.task import task

from openquake.engine import logs, no_distribute
from openquake.engine.db import models
from openquake.engine.utils import config
from openquake.engine.writer import CacheInserter
from openquake.engine.performance import EnginePerformanceMonitor, \
    LightMonitor


ONE_MB = 1024 * 1024


class Pickled(object):
    """
    An utility to manually pickling/unpickling objects.
    The reason is that celery does not use the HIGHEST_PROTOCOL,
    so relying on celery is slower. Moreover Pickled instances
    have a nice string representation and length giving the size
    of the pickled bytestring.

    :param obj: the object to pickle
    """
    def __init__(self, obj):
        self.clsname = obj.__class__.__name__
        self.pik = cPickle.dumps(obj, cPickle.HIGHEST_PROTOCOL)

    def __repr__(self):
        """String representation of the pickled object"""
        return '<Pickled %s %dK>' % (self.clsname, len(self) / 1024)

    def __len__(self):
        """Length of the pickled bytestring"""
        return len(self.pik)

    def unpickle(self):
        """Unpickle the underlying object"""
        return cPickle.loads(self.pik)


def pickle_sequence(objects):
    """
    Convert an iterable of objects into a list of pickled objects.
    If the iterable contains copies, the pickling will be done only once.
    If the iterable contains objects already pickled, they will not be
    pickled again.

    :param objects: a sequence of objects to pickle
    """
    cache = {}
    out = []
    for obj in objects:
        obj_id = id(obj)
        if obj_id not in cache:
            if isinstance(obj, Pickled):  # already pickled
                cache[obj_id] = obj
            else:  # pickle the object
                cache[obj_id] = Pickled(obj)
        out.append(cache[obj_id])
    return out


def safely_call(func, args):
    """
    Call the given function with the given arguments safely, i.e.
    by trapping the exceptions. Return a pair (result, exc_type)
    where exc_type is None if no exceptions occur, otherwise it
    is the exception class and the result is a string containing
    error message and traceback.

    :param func: the function to call
    :param args: the arguments
    """
    try:
        return func(*args), None
    except:
        etype, exc, tb = sys.exc_info()
        tb_str = ''.join(traceback.format_tb(tb))
        return '\n%s%s: %s' % (tb_str, etype.__name__, exc), etype


def map_reduce(task, task_args, agg, acc):
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
    if no_distribute():
        for the_args in task_args:
            result, exctype = safely_call(task.task_func, the_args)
            if exctype:
                raise exctype(result)
            acc = agg(acc, result)
    else:
        backend = current_app().backend
        unpik = 0
        job_id = task_args[0][0]
        taskname = task.__name__
        mon = LightMonitor('unpickling %s' % taskname, job_id, task)
        to_send = 0
        pickled_args = []
        for args in task_args:
            piks = pickle_sequence(args)
            pickled_args.append(piks)
            to_send += sum(len(p) for p in piks)
        logs.LOG.info('Sending %dM', to_send / ONE_MB)
        taskset = TaskSet(tasks=map(task.subtask, pickled_args))
        for task_id, result_dict in taskset.apply_async().iter_native():
            result_pik = result_dict['result']
            with mon:
                result, exctype = result_pik.unpickle()
            if exctype:
                raise exctype(result)
            unpik += len(result_pik)
            acc = agg(acc, result)
            del backend._cache[task_id]  # work around a celery bug
        logs.LOG.info('Unpickled %dM of received data in %s seconds',
                      unpik / ONE_MB, mon.duration)
    return acc


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
            return

        # it is important to save the task id soon, so that
        # the revoke functionality can work
        EnginePerformanceMonitor.store_task_id(job_id, tsk)

        with EnginePerformanceMonitor(
                'total ' + task_func.__name__, job_id, tsk, flush=True):
            # tasks write on the celery log file
            logs.set_level(job.log_level)
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
    f = lambda *args: Pickled(
        safely_call(wrapped, [a.unpickle() for a in args]))
    f.__name__ = task_func.__name__
    tsk = task(f, queue=celery_queue)
    tsk.task_func = task_func
    return tsk
