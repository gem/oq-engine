# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
TODO: write documentation.
"""
from __future__ import print_function
import os
import sys
import socket
import inspect
import logging
import operator
import traceback
import functools
import multiprocessing.dummy
from concurrent.futures import as_completed, ProcessPoolExecutor, Future

from openquake.baselib.python3compat import pickle
from openquake.baselib.performance import Monitor, virtual_memory
from openquake.baselib.general import split_in_blocks, AccumDict, humansize

executor = ProcessPoolExecutor()
# the num_tasks_hint is chosen to be 2 times bigger than the name of
# cores; it is a heuristic number to get a good distribution;
# it has no more significance than that
executor.num_tasks_hint = executor._max_workers * 2

OQ_DISTRIBUTE = os.environ.get('OQ_DISTRIBUTE', 'futures').lower()

if OQ_DISTRIBUTE == 'celery':
    from celery.result import ResultSet
    from celery import Celery
    from celery.task import task
    from openquake.engine.celeryconfig import BROKER_URL
    app = Celery('openquake', backend='amqp://', broker=BROKER_URL)

elif OQ_DISTRIBUTE == 'ipython':
    import ipyparallel as ipp


def oq_distribute():
    """
    Return the current value of the variable OQ_DISTRIBUTE; if undefined,
    return 'futures'.
    """
    return os.environ.get('OQ_DISTRIBUTE', 'futures').lower()


def check_mem_usage(monitor=Monitor(),
                    soft_percent=90, hard_percent=100):
    """
    Display a warning if we are running out of memory

    :param int mem_percent: the memory limit as a percentage
    """
    used_mem_percent = virtual_memory().percent
    if used_mem_percent > hard_percent:
        raise MemoryError('Using more memory than allowed by configuration '
                          '(Used: %d%% / Allowed: %d%%)! Shutting down.' %
                          (used_mem_percent, hard_percent))
    elif used_mem_percent > soft_percent:
        hostname = socket.gethostname()
        monitor.send('warn', 'Using over %d%% of the memory in %s!',
                     used_mem_percent, hostname)


def safely_call(func, args, pickle=False):
    """
    Call the given function with the given arguments safely, i.e.
    by trapping the exceptions. Return a pair (result, exc_type)
    where exc_type is None if no exceptions occur, otherwise it
    is the exception class and the result is a string containing
    error message and traceback.

    :param func: the function to call
    :param args: the arguments
    :param pickle:
        if set, the input arguments are unpickled and the return value
        is pickled; otherwise they are left unchanged
    """
    with Monitor('total ' + func.__name__, measuremem=True) as child:
        if pickle:  # measure the unpickling time too
            args = [a.unpickle() for a in args]
        if args and isinstance(args[-1], Monitor):
            mon = args[-1]
            mon.children.append(child)  # child is a child of mon
            child.hdf5path = mon.hdf5path
        else:
            mon = child
        check_mem_usage(mon)  # check if too much memory is used
        mon.flush = NoFlush(mon, func.__name__)
        try:
            got = func(*args)
            if inspect.isgenerator(got):
                got = list(got)
            res = got, None, mon
        except:
            etype, exc, tb = sys.exc_info()
            tb_str = ''.join(traceback.format_tb(tb))
            res = ('\n%s%s: %s' % (tb_str, etype.__name__, exc), etype, mon)

        # NB: flush must not be called in the workers - they must not
        # have access to the datastore - so we remove it
        rec_delattr(mon, 'flush')

    if pickle:  # it is impossible to measure the pickling time :-(
        res = Pickled(res)
    return res


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
        self.calc_id = str(getattr(obj, 'calc_id', ''))  # for monitors
        self.pik = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)

    def __repr__(self):
        """String representation of the pickled object"""
        return '<Pickled %s %s %s>' % (
            self.clsname, self.calc_id, humansize(len(self)))

    def __len__(self):
        """Length of the pickled bytestring"""
        return len(self.pik)

    def unpickle(self):
        """Unpickle the underlying object"""
        return pickle.loads(self.pik)


def get_pickled_sizes(obj):
    """
    Return the pickled sizes of an object and its direct attributes,
    ordered by decreasing size. Here is an example:

    >> total_size, partial_sizes = get_pickled_sizes(Monitor(''))
    >> total_size
    345
    >> partial_sizes
    [('_procs', 214), ('exc', 4), ('mem', 4), ('start_time', 4),
    ('_start_time', 4), ('duration', 4)]

    Notice that the sizes depend on the operating system and the machine.
    """
    sizes = []
    attrs = getattr(obj, '__dict__',  {})
    for name, value in attrs.items():
        sizes.append((name, len(Pickled(value))))
    return len(Pickled(obj)), sorted(
        sizes, key=lambda pair: pair[1], reverse=True)


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


class IterResult(object):
    """
    :param futures:
        an iterator over futures
    :param taskname:
        the name of the task
    :param num_tasks
        the total number of expected futures (None if unknown)
    :param progress:
        a logging function for the progress report
    """
    def __init__(self, futures, taskname, num_tasks=None,
                 progress=logging.info):
        self.futures = futures
        self.name = taskname
        self.num_tasks = num_tasks
        self.progress = progress
        self.received = []
        if self.num_tasks:
            self.log_percent = self._log_percent()
            next(self.log_percent)

    def _log_percent(self):
        yield 0
        done = 1
        prev_percent = 0
        while done < self.num_tasks:
            percent = int(float(done) / self.num_tasks * 100)
            if percent > prev_percent:
                self.progress('%s %3d%%', self.name, percent)
                prev_percent = percent
            yield done
            done += 1
        self.progress('%s 100%%', self.name)
        yield done

    def __iter__(self):
        self.received = []
        for fut in self.futures:
            check_mem_usage()  # log a warning if too much memory is used
            if hasattr(fut, 'result'):
                result = fut.result()
            else:
                result = fut
            if hasattr(result, 'unpickle'):
                self.received.append(len(result))
                val, etype, mon = result.unpickle()
            else:
                val, etype, mon = result
            if etype:
                raise etype(val)
            if self.num_tasks:
                next(self.log_percent)
            mon.flush()
            yield val


class TaskManager(object):
    """
    A manager to submit several tasks of the same type.
    The usage is::

      tm = TaskManager(do_something, logging.info)
      tm.send(arg1, arg2)
      tm.send(arg3, arg4)
      print tm.reduce()

    Progress report is built-in.
    """
    executor = executor
    progress = staticmethod(logging.info)
    task_ids = []

    @classmethod
    def restart(cls):
        cls.executor.shutdown()
        cls.executor = ProcessPoolExecutor()

    @classmethod
    def starmap(cls, task, task_args, name=None):
        """
        Spawn a bunch of tasks with the given list of arguments

        :returns: a TaskManager object with a .result method.
        """
        self = cls(task, name)
        self.task_args = task_args
        return self

    @classmethod
    def apply(cls, task, task_args,
              concurrent_tasks=executor.num_tasks_hint,
              weight=lambda item: 1,
              key=lambda item: 'Unspecified',
              name=None):
        """
        Apply a task to a tuple of the form (sequence, \*other_args)
        by first splitting the sequence in chunks, according to the weight
        of the elements and possibly to a key (see :function:
        `openquake.baselib.general.split_in_blocks`).
        Then reduce the results with an aggregation function.
        The chunks which are generated internally can be seen directly (
        useful for debugging purposes) by looking at the attribute `._chunks`,
        right after the `apply` function has been called.

        :param task: a task to run in parallel
        :param task_args: the arguments to be passed to the task function
        :param agg: the aggregation function
        :param acc: initial value of the accumulator (default empty AccumDict)
        :param concurrent_tasks: hint about how many tasks to generate
        :param weight: function to extract the weight of an item in arg0
        :param key: function to extract the kind of an item in arg0
        """
        arg0 = task_args[0]  # this is assumed to be a sequence
        args = task_args[1:]
        chunks = list(split_in_blocks(
            arg0, concurrent_tasks or 1, weight, key))
        cls.apply.__func__._chunks = chunks
        logging.info('Starting %d tasks', len(chunks))
        return cls.starmap(task, [(chunk,) + args for chunk in chunks], name)

    def __init__(self, oqtask, name=None):
        self.task_func = oqtask
        self.name = name or oqtask.__name__
        self.results = []
        self.sent = AccumDict()
        self.received = []
        self.distribute = oq_distribute()
        self.argnames = inspect.getargspec(self.task_func).args

        if self.distribute == 'ipython' and isinstance(
                self.executor, ProcessPoolExecutor):
            client = ipp.Client()
            self.__class__.executor = client.executor()

    def submit(self, *args):
        """
        Submit a function with the given arguments to the process pool
        and add a Future to the list `.results`. If the attribute
        distribute is set, the function is run in process and the
        result is returned.
        """
        check_mem_usage()
        # log a warning if too much memory is used
        if self.distribute == 'no':
            sent = {}
            res = (self.task_func(*args), None, args[-1])
        else:
            piks = pickle_sequence(args)
            sent = {arg: len(p) for arg, p in zip(self.argnames, piks)}
            res = self._submit(piks)
        self.sent += sent
        self.results.append(res)
        return sent

    def _submit(self, piks):
        if self.distribute == 'celery':
            res = safe_task.delay(self.task_func, piks, True)
            self.task_ids.append(res.task_id)
            return res
        else:  # submit tasks by using the ProcessPoolExecutor or ipyparallel
            return self.executor.submit(
                safely_call, self.task_func, piks, True)

    def _iter_futures(self):
        # compatibility wrapper for different concurrency frameworks

        if self.distribute == 'no':
            for result in self.results:
                fut = Future()
                fut.set_result(result)
                yield fut

        elif self.distribute == 'celery':
            rset = ResultSet(self.results)
            for task_id, result_dict in rset.iter_native():
                idx = self.task_ids.index(task_id)
                self.task_ids.pop(idx)
                fut = Future()
                fut.set_result(result_dict['result'])
                # work around a celery bug
                del app.backend._cache[task_id]
                yield fut

        else:  # future interface
            for fut in as_completed(self.results):
                yield fut

    def reduce(self, agg=operator.add, acc=None):
        """
        Loop on a set of results and update the accumulator
        by using the aggregation function.

        :param agg: the aggregation function, (acc, val) -> new acc
        :param acc: the initial value of the accumulator
        :returns: the final value of the accumulator
        """
        if acc is None:
            acc = AccumDict()
        results = self.submit_all()
        if self.sent:
            self.progress('Sent %s of data in %d task(s)',
                          humansize(sum(self.sent.values())),
                          results.num_tasks)
        for res in results:
            acc = agg(acc, res)
        if results.received:
            self.progress('Received %s of data, maximum per task %s',
                          humansize(sum(results.received)),
                          humansize(max(results.received)))
        self.results = []
        return acc

    def wait(self):
        """
        Wait until all the task terminate. Discard the results.

        :returns: the total number of tasks that were spawned
        """
        return self.reduce(self, lambda acc, res: acc + 1, 0)

    def submit_all(self):
        """
        :returns: an IterResult object
        """
        try:
            nargs = len(self.task_args)
        except TypeError:  # generators have no len
            nargs = ''
        if nargs == 1:
            [args] = self.task_args
            return IterResult([safely_call(self.task_func, args)], self.name)
        task_no = 0
        for args in self.task_args:
            task_no += 1
            if task_no == 1:  # first time
                self.progress('Submitting %s "%s" tasks', nargs, self.name)
            if isinstance(args[-1], Monitor):  # add incremental task number
                args[-1].task_no = task_no
            self.submit(*args)
        if not task_no:
            logging.warn('No tasks were submitted')
        ir = IterResult(self.results, self.name, task_no, self.progress)
        ir.sent = self.sent  # for information purposes
        return ir

    def __iter__(self):
        return iter(self.submit_all())


# convenient aliases
starmap = TaskManager.starmap
apply = TaskManager.apply


def do_not_aggregate(acc, value):
    """
    Do nothing aggregation function.

    :param acc: the accumulator
    :param value: the value to accumulate
    :returns: the accumulator unchanged
    """
    return acc


class NoFlush(object):
    # this is instantiated by safely_call
    def __init__(self, monitor, taskname):
        self.monitor = monitor
        self.taskname = taskname

    def __call__(self):
        raise RuntimeError('Monitor(%r).flush() must not be called '
                           'by %s!' % (self.monitor.operation, self.taskname))


def rec_delattr(mon, name):
    """
    Delete attribute from a monitor recursively
    """
    for child in mon.children:
        rec_delattr(child, name)
    if name in vars(mon):
        delattr(mon, name)


if OQ_DISTRIBUTE == 'celery':
    safe_task = task(safely_call,  queue='celery')


class Starmap(object):
    poolfactory = None  # to be overridden
    pool = None  # to be overridden

    @classmethod
    def apply(cls, func, args, concurrent_tasks=executor._max_workers * 5,
              weight=lambda item: 1, key=lambda item: 'Unspecified'):
        chunks = split_in_blocks(args[0], concurrent_tasks, weight, key)
        return cls(func, (((chunk,) + args[1:]) for chunk in chunks))

    def __init__(self, func, iterargs):
        # build the pool at first instantiation only
        if self.__class__.pool is None:
            self.__class__.pool = self.poolfactory()
        self.func = func
        allargs = list(iterargs)
        self.num_tasks = len(allargs)
        logging.info('Starting %d tasks', self.num_tasks)
        self.imap = self.pool.imap_unordered(
            functools.partial(safely_call, func), allargs)

    def reduce(self, agg=operator.add, acc=None, progress=logging.info):
        if acc is None:
            acc = AccumDict()
        for res in IterResult(
                self.imap, self.func.__name__, self.num_tasks, progress):
            acc = agg(acc, res)
        return acc


class Serialmap(Starmap):
    """
    A sequential Starmap, useful for debugging purpose.
    """
    def __init__(self, func, iterargs):
        self.func = func
        allargs = list(iterargs)
        self.num_tasks = len(allargs)
        logging.info('Starting %d tasks', self.num_tasks)
        self.imap = [safely_call(func, args) for args in allargs]


class Threadmap(Starmap):
    """
    MapReduce implementation based on threads. For instance

    >>> from collections import Counter
    >>> c = Threadmap(Counter, [('hello',), ('world',)]).reduce(acc=Counter())
    """
    poolfactory = staticmethod(
        # following the same convention of the standard library, num_proc * 5
        lambda: multiprocessing.dummy.Pool(executor._max_workers * 5))
    pool = None  # built at instantiation time


class Processmap(Starmap):
    """
    MapReduce implementation based on processes. For instance

    >>> from collections import Counter
    >>> c = Processmap(Counter, [('hello',), ('world',)]).reduce(acc=Counter())
    """
    poolfactory = staticmethod(multiprocessing.Pool)
    pool = None  # built at instantiation time
