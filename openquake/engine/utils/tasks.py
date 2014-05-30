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
import psutil

from celery.result import ResultSet
from celery.app import current_app
from celery.task import task

from openquake.engine import logs, no_distribute
from openquake.engine.db import models
from openquake.engine.utils import config
from openquake.engine.writer import CacheInserter
from openquake.engine.performance import EnginePerformanceMonitor


class JobNotRunning(Exception):
    pass


ONE_MB = 1024 * 1024


def check_mem_usage(mem_percent=80):
    """
    Display a warning if we are running out of memory

    :param int mem_percent: the memory limit as a percentage
    """
    used_mem_percent = psutil.phymem_usage().percent
    if used_mem_percent > mem_percent:
        logs.LOG.warn('Using over %d%% of the memory!', used_mem_percent)


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
        self.objrepr = repr(obj)
        self.pik = cPickle.dumps(obj, cPickle.HIGHEST_PROTOCOL)

    def __repr__(self):
        """String representation of the pickled object"""
        return '<Pickled %s %dK>' % (self.objrepr, len(self) / 1024)

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


def aggregate_result_set(rset, agg, acc):
    """
    Loop on a set of celery AsyncResults and update the accumulator
    by using the aggregation function.

    :param rset: a :class:`celery.result.ResultSet` instance
    :param agg: the aggregation function, (acc, val) -> new acc
    :param acc: the initial value of the accumulator
    :returns: the final value of the accumulator
    """
    backend = current_app().backend
    for task_id, result_dict in rset.iter_native():
        check_mem_usage()  # log a warning if too much memory is used
        result_pik = result_dict['result']
        result, exctype = result_pik.unpickle()  # this is always negligible
        if exctype:
            raise RuntimeError(result)
        acc = agg(acc, result)
        del backend._cache[task_id]  # work around a celery bug
    return acc


def log_percent_gen(taskname, todo, progress):
    """
    Generator factory. Each time the generator object is called
    log a message if the percentage is bigger than the last one.
    Yield the number of calls done at the current iteration.

    :param str taskname:
        the name of the task
    :param int todo:
        the number of times the generator object will be called
    :param progress:
        a logging function for the progress report
    """
    progress('spawned %d tasks of kind %s', todo, taskname)
    yield 0
    done = 1
    prev_percent = 0
    while done < todo:
        percent = int(float(done) / todo * 100)
        if percent > prev_percent:
            progress('%s %3d%%', taskname, percent)
            prev_percent = percent
        yield done
        done += 1
    progress('%s 100%%', taskname)
    yield done


class OqTaskManager(object):
    """
    A manager to submit several tasks of the same type.
    The usage is::

      oqm = OqTaskManager(do_something, logs.LOG.progress)
      oqm.send(arg1, arg2)
      oqm.send(arg3, arg4)
      print oqm.aggregate_results(agg, acc)

    Progress report is built-in.
    """
    def __init__(self, oqtask, progress, name=None, distribute=None):
        self.oqtask = oqtask
        self.progress = progress
        self.name = name or oqtask.__name__
        self.distribute = (not no_distribute() if distribute is None
                           else distribute)
        self.results = []
        self.sent = 0

    def aggregate_results(self, agg, acc):
        """
        Loop on a set of results and update the accumulator
        by using the aggregation function.

        :param results: a list of results
        :param agg: the aggregation function, (acc, val) -> new acc
        :param acc: the initial value of the accumulator
        :returns: the final value of the accumulator
        """
        logs.LOG.info('Sent %dM of data', self.sent / ONE_MB)
        log_percent = log_percent_gen(
            self.name, len(self.results), self.progress)
        log_percent.next()

        def agg_and_percent(acc, val):
            res = agg(acc, val)
            log_percent.next()
            return res

        if self.distribute:
            return aggregate_result_set(
                ResultSet(self.results), agg_and_percent, acc)
        return reduce(agg_and_percent, self.results, acc)

    def submit(self, *args):
        """
        Submit an oqtask with the given arguments to celery and return
        an AsyncResult. If the variable OQ_NO_DISTRIBUTE is set, the
        task function is run in process and the result is returned.
        """
        if self.distribute:
            piks = pickle_sequence(args)
            self.sent += sum(len(p) for p in piks)
            check_mem_usage()  # log a warning if too much memory is used
            res = self.oqtask.delay(*piks)
        else:
            res = self.oqtask.task_func(*args)
        self.results.append(res)


def map_reduce(task, task_args, agg, acc, name=None, distribute=None):
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
    oqm = OqTaskManager(task, logs.LOG.progress, name, distribute)
    for args in task_args:
        oqm.submit(*args)
    return oqm.aggregate_results(agg, acc)


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
    f = lambda *args: Pickled(
        safely_call(wrapped, [a.unpickle() for a in args]))
    f.__name__ = task_func.__name__
    tsk = task(f, queue=celery_queue)
    tsk.task_func = task_func
    return tsk
