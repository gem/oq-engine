# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2017 GEM Foundation
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
"""\
The Starmap API
====================================

There are several good libraries to manage parallel programming,
both in the standard library and in third party packages. Since we are
not interested in reinventing the wheel, OpenQuake does not offer any
new parallel library; however, it does offer some glue code so that
you can use your library of choice. Currently multiprocessing,
concurrent.futures, celery and ipython-parallel are
supported. Moreover, :mod:`openquake.baselib.parallel` offers some
additional facilities that make it easier to parallelize
scientific computations, i.e. embarrassing parallel problems.

Typically one wants to apply a callable to a list of arguments in
parallel rather then sequentially, and then combine together the
results. This is known as a `MapReduce` problem. As a simple example,
we will consider the problem of counting the letters in a text. Here is
how you can solve the problem sequentially:

>>> from itertools import starmap  # map a function with multiple arguments
>>> from functools import reduce  # reduce an iterable with a binary operator
>>> from operator import add  # addition function
>>> from collections import Counter  # callable doing the counting

>>> arglist = [('hello',), ('world',)]  # list of arguments
>>> results = starmap(Counter, arglist)  # iterator over the results
>>> res = reduce(add, results, Counter())  # aggregated counts

>>> sorted(res.items())  # counts per letter
[('d', 1), ('e', 1), ('h', 1), ('l', 3), ('o', 2), ('r', 1), ('w', 1)]

Here is how you can solve the problem in parallel by using
:class:`openquake.baselib.parallel.Starmap`:

>>> res2 = Starmap(Counter, arglist).reduce()
>>> assert res2 == res  # the same as before

As you see there are some notational advantages with respect to use
`itertools.starmap`. First of all, `Starmap` has a `reduce` method, so
there is no need to import `functools.reduce`; secondly, the `reduce`
method has sensible defaults:

1. the default aggregation function is `add`, so there is no need to specify it
2. the default accumulator is an empty accumulation dictionary (see
   :class:`openquake.baselib.AccumDict`) working as a `Counter`, so there
   is no need to specify it.

You can of course ovverride the defaults, so if you really want to
return a `Counter` you can do

>>> res3 = Starmap(Counter, arglist).reduce(acc=Counter())

In the engine we use nearly always callables that return dictionaries
and we aggregate nearly always with the addition operator, so such
defaults are very convenient. You are encouraged to do the same, since we
found that approach to be very flexible. Typically in a scientific
application you will return a dictionary of numpy arrays.

The parallelization algorithm used by `Starmap` will depend on the
environment variable `OQ_DISTRIBUTE`. Here are the possibilities
available at the moment:

`OQ_DISTRIBUTE` not set or set to "futures":
  use multiprocessing via the concurrent.futures interface
`OQ_DISTRIBUTE` set to "no":
  disable the parallelization, useful for debugging
`OQ_DISTRIBUTE` set to "celery":
   use celery, useful if you have multiple machines in a cluster
`OQ_DISTRIBUTE` set tp "ipython"
   use the ipyparallel concurrency mechanism (experimental)

There is no such a thing as OQ_DISTRIBUTE="threading"; it would be trivial
to do, but the performance of using threads instead of processes is terrible
for the kind of applications we are interested in (CPU-dominated, which large
tasks such that the time to spawn a new process is negligible with respect
to the time to perform the task).

The Starmap.apply API
====================================

The `Starmap` class has a very convenient classmethod `Starmap.apply`
which is used in several places in the engine. `Starmap.apply` is useful
when you have a sequence of objects that you want to split in homogenous chunks
and then apply a callable to each chunk (in parallel). For instance, in the
letter counting example discussed before, `Starmap.apply` could
be used as follows:

>>> text = 'helloworld'  # sequence of characters
>>> res3 = Starmap.apply(Counter, (text,)).reduce()
>>> assert res3 == res

The API of `Starmap.apply` is designed to extend the one of `apply`,
a builtin of Python 2; the second argument is the tuple of arguments
passed to the first argument. The difference with `apply` is that
`Starmap.apply` returns a :class:`Starmap` object so that nothing is
actually done until you iterate on it (`reduce` is doing that).

How many chunks will be produced? That depends on the parameter
`concurrent_tasks`; it it is not passed, it has a default of 5 times
the number of cores in your machine - as returned by `os.cpu_count()` -
and `Starmap.apply` will try to produce a number of chunks close to
that number. The nice thing is that it is also possible to pass a
`weight` function. Suppose for instance that instead of a list of
letters you have a list of seismic sources: some sources requires a
long computation time (such as `ComplexFaultSources`), some requires a
short computation time (such as `PointSources`). By giving an heuristic
weight to the different sources it is possible to produce chunks with
nearly homogeneous weight; in particular `PointSource` tasks will
contain a lot more sources than tasks with `ComplexFaultSources`.

It is *essential* in large computations to have a homogeneous task
distribution, otherwise you will end up having a big task dominating
the computation time (i.e. you may have 1000 cores of which 999 are free,
having finished all the short tasks, but you have to wait for days for
the single core processing the slow task). The OpenQuake engine does
a great deal of work trying to split slow sources in more manageable
fast sources.
"""
from __future__ import print_function
import os
import sys
import time
import signal
import socket
import inspect
import logging
import operator
import traceback
import functools
import subprocess
import multiprocessing.dummy
from multiprocessing.connection import Client, Listener
from concurrent.futures import as_completed, ProcessPoolExecutor, Future
import numpy
from openquake.baselib import hdf5
from openquake.baselib.python3compat import pickle
from openquake.baselib.performance import Monitor, virtual_memory
from openquake.baselib.general import (
    block_splitter, split_in_blocks, AccumDict, humansize)

executor = ProcessPoolExecutor()
executor.pids = ()  # set by wakeup_pool
# the num_tasks_hint is chosen to be 5 times bigger than the name of
# cores; it is a heuristic number to get a good distribution;
# it has no more significance than that
executor.num_tasks_hint = executor._max_workers * 5

OQ_DISTRIBUTE = os.environ.get('OQ_DISTRIBUTE', 'futures').lower()

if OQ_DISTRIBUTE == 'celery':
    from celery.result import ResultSet
    from celery import Celery
    from celery.task import task
    from openquake.engine.celeryconfig import BROKER_URL, CELERY_RESULT_BACKEND
    app = Celery('openquake', backend=CELERY_RESULT_BACKEND, broker=BROKER_URL)

elif OQ_DISTRIBUTE == 'ipython':
    import ipyparallel as ipp


def oq_distribute(task=None):
    """
    If the task has an attribute `shared_dir_on` which is false,
    return 'futures' even if OQ_DISTRIBUTE is `celery`, otherwise
    return the current value of the variable OQ_DISTRIBUTE;
    if undefined, return 'futures'.
    """
    env = os.environ.get('OQ_DISTRIBUTE', 'futures').lower()
    if hasattr(task, 'shared_dir_on'):
        if env == 'celery' and not task.shared_dir_on():
            logging.warn(
                'Task `%s` will be run on the controller node only, since '
                'no `shared_dir` has been specified' % task.__name__)
            return 'futures'
    return env


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


def safely_call(func, args, pickle=False, conn=None):
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
    if conn:  # send the result via the connection
        conn.send(res)
        conn.close()
        return None
    return res


def mkfuture(result):
    fut = Future()
    fut.set_result(result)
    return fut


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
    :param num_tasks:
        the total number of expected futures (None if unknown)
    :param progress:
        a logging function for the progress report
    """
    task_data_dt = numpy.dtype(
        [('taskno', numpy.uint32), ('weight', numpy.float32),
         ('duration', numpy.float32)])

    def __init__(self, futures, taskname, num_tasks=None,
                 progress=logging.info):
        self.futures = futures
        self.name = taskname
        self.num_tasks = num_tasks
        if self.name.startswith("_"):  # private task, log only in debug
            self.progress = logging.debug
        else:
            self.progress = progress
        self.sent = 0  # set in Starmap.submit_all
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
            if isinstance(result, BaseException):
                # this happens for instance with WorkerLostError with celery
                raise result
            elif hasattr(result, 'unpickle'):
                self.received.append(len(result))
                val, etype, mon = result.unpickle()
            else:
                val, etype, mon = result
                self.received.append(len(Pickled(result)))
            if etype:
                raise RuntimeError(val)
            if self.num_tasks:
                next(self.log_percent)
            if not self.name.startswith('_'):  # no info for private tasks
                self.save_task_data(mon)
            yield val

        if self.received:
            tot = sum(self.received)
            max_per_task = max(self.received)
            self.progress('Received %s of data, maximum per task %s',
                          humansize(tot), humansize(max_per_task))
            received = {'max_per_task': max_per_task, 'tot': tot}
            tname = self.name
            dic = {tname: {'sent': self.sent, 'received': received}}
            mon.save_info(dic)

    def save_task_data(self, mon):
        if mon.hdf5path and hasattr(mon, 'weight'):
            duration = mon.children[0].duration  # the task is the first child
            tup = (mon.task_no, mon.weight, duration)
            data = numpy.array([tup], self.task_data_dt)
            hdf5.extend3(mon.hdf5path, 'task_info/' + self.name, data)
        mon.flush()

    def reduce(self, agg=operator.add, acc=None):
        if acc is None:
            acc = AccumDict()
        for result in self:
            acc = agg(acc, result)
        return acc

    @classmethod
    def sum(cls, iresults):
        """
        Sum the data transfer information of a set of results
        """
        res = object.__new__(cls)
        res.received = []
        res.sent = 0
        for iresult in iresults:
            res.received.extend(iresult.received)
            res.sent += iresult.sent
            name = iresult.name.split('#', 1)[0]
            if hasattr(res, 'name'):
                assert res.name.split('#', 1)[0] == name, (res.name, name)
            else:
                res.name = iresult.name.split('#')[0]
        return res


class Starmap(object):
    """
    A manager to submit several tasks of the same type.
    The usage is::

      tm = Starmap(do_something, logging.info)
      tm.send(arg1, arg2)
      tm.send(arg3, arg4)
      print(tm.reduce())

    Progress report is built-in.
    """
    executor = executor
    task_ids = []

    @classmethod
    def restart(cls):
        cls.executor.shutdown()
        cls.executor = ProcessPoolExecutor()

    @classmethod
    def apply(cls, task, task_args,
              concurrent_tasks=executor.num_tasks_hint,
              maxweight=None,
              weight=lambda item: 1,
              key=lambda item: 'Unspecified',
              name=None):
        """
        Apply a task to a tuple of the form (sequence, \*other_args)
        by first splitting the sequence in chunks, according to the weight
        of the elements and possibly to a key (see :func:
        `openquake.baselib.general.split_in_blocks`).

        :param task: a task to run in parallel
        :param task_args: the arguments to be passed to the task function
        :param agg: the aggregation function
        :param acc: initial value of the accumulator (default empty AccumDict)
        :param concurrent_tasks: hint about how many tasks to generate
        :param maxweight: if not None, used to split the tasks
        :param weight: function to extract the weight of an item in arg0
        :param key: function to extract the kind of an item in arg0
        """
        arg0 = task_args[0]  # this is assumed to be a sequence
        args = task_args[1:]
        if maxweight:
            chunks = block_splitter(arg0, maxweight, weight, key)
        else:
            chunks = split_in_blocks(arg0, concurrent_tasks or 1, weight, key)
        return cls(task, [(chunk,) + args for chunk in chunks], name)

    def __init__(self, oqtask, task_args, name=None):
        self.task_func = oqtask
        self.task_args = task_args
        self.name = name or oqtask.__name__
        self.results = []
        self.sent = AccumDict()
        self.distribute = oq_distribute(oqtask)
        # a task can be a function, a class or an instance with a __call__
        if inspect.isfunction(oqtask):
            self.argnames = inspect.getargspec(oqtask).args
        elif inspect.isclass(oqtask):
            self.argnames = inspect.getargspec(oqtask.__init__).args[1:]
        else:  # instance with a __call__ method
            self.argnames = inspect.getargspec(oqtask.__call__).args[1:]
        if self.distribute == 'ipython' and isinstance(
                self.executor, ProcessPoolExecutor):
            client = ipp.Client()
            self.__class__.executor = client.executor()

    def progress(self, *args):
        """
        Log in INFO mode regular tasks and in DEBUG private tasks
        """
        if self.name.startswith('_'):
            logging.debug(*args)
        else:
            logging.info(*args)

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
            res = safely_call(self.task_func, args)
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

    def _iterfutures(self):
        # compatibility wrapper for different concurrency frameworks

        if self.distribute == 'no':
            for result in self.results:
                yield mkfuture(result)

        elif self.distribute == 'celery':
            rset = ResultSet(self.results)
            for task_id, result_dict in rset.iter_native():
                idx = self.task_ids.index(task_id)
                self.task_ids.pop(idx)
                fut = mkfuture(result_dict['result'])
                # work around a celery/rabbitmq bug
                if CELERY_RESULT_BACKEND.startswith('rpc:'):
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
        acc = self.submit_all().reduce(agg, acc or AccumDict())
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
            self.progress('Executing "%s" in process', self.name)
            fut = mkfuture(safely_call(self.task_func, args))
            return IterResult([fut], self.name, nargs)

        if self.distribute == 'qsub':
            logging.warn('EXPERIMENTAL: sending tasks to the grid engine')
            allargs = list(self.task_args)
            return IterResult(qsub(self.task_func, allargs),
                              self.name, len(allargs), self.progress)

        task_no = 0
        for args in self.task_args:
            task_no += 1
            if task_no == 1:  # first time
                self.progress('Submitting %s "%s" tasks', nargs, self.name)
            if isinstance(args[-1], Monitor):
                # add incremental task number and task weight
                args[-1].task_no = task_no
                args[-1].weight = getattr(args[0], 'weight', 1.)
            self.submit(*args)
        if not task_no:
            self.progress('No %s tasks were submitted', self.name)
        # NB: keep self._iterfutures() an iterator, especially with celery!
        ir = IterResult(self._iterfutures(), self.name, task_no,
                        self.progress)
        ir.sent = self.sent  # for information purposes
        if self.sent:
            self.progress('Sent %s of data in %d task(s)',
                          humansize(sum(self.sent.values())),
                          ir.num_tasks)
        return ir

    def __iter__(self):
        return iter(self.submit_all())


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


def _wakeup(sec):
    """Waiting functions, used to wake up the process pool"""
    try:
        import prctl
    except ImportError:
        pass
    else:
        # if the parent dies, the children die
        prctl.set_pdeathsig(signal.SIGKILL)
    time.sleep(sec)
    return os.getpid()


def wakeup_pool():
    """
    This is used at startup, only when the ProcessPoolExecutor is used,
    to fork the processes before loading any big data structure. It is
    called once once, and adds the list of PIDs spawned to the executor.
    """
    if not executor.pids and oq_distribute() == 'futures':
        # when using the ProcessPoolExecutor
        pids = Starmap(_wakeup, ((.2,) for _ in range(executor._max_workers)))
        executor.pids = list(pids)


class BaseStarmap(object):
    poolfactory = staticmethod(lambda size: multiprocessing.Pool(size))

    @classmethod
    def apply(cls, func, args, concurrent_tasks=executor._max_workers * 5,
              weight=lambda item: 1, key=lambda item: 'Unspecified'):
        chunks = split_in_blocks(args[0], concurrent_tasks or 1, weight, key)
        if concurrent_tasks == 0:
            cls = Sequential
        return cls(func, (((chunk,) + args[1:]) for chunk in chunks))

    def __init__(self, func, iterargs, poolsize=None):
        self.pool = self.poolfactory(poolsize)
        self.func = func
        allargs = []
        for task_no, args in enumerate(iterargs):
            if isinstance(args[-1], Monitor):
                # add incremental task number and task weight
                args[-1].task_no = task_no
                args[-1].weight = getattr(args[0], 'weight', 1.)
            allargs.append(args)
        self.num_tasks = len(allargs)
        logging.info('Starting %d tasks', self.num_tasks)
        self.imap = self.pool.imap_unordered(
            functools.partial(safely_call, func), allargs)

    def submit_all(self, progress=logging.info):
        """
        :returns: an :class:`IterResult` instance
        """
        futs = (mkfuture(res) for res in self.imap)
        return IterResult(futs, self.func.__name__, self.num_tasks, progress)

    def __iter__(self):
        try:
            for res in self.submit_all():
                yield res
        finally:
            if self.pool:
                self.pool.close()
                self.pool.join()

    def reduce(self, agg=operator.add, acc=None, progress=logging.info):
        if acc is None:
            acc = AccumDict()
        for res in self.submit_all(progress):
            acc = agg(acc, res)
        if self.pool:
            self.pool.close()
            self.pool.join()
        return acc


class Sequential(BaseStarmap):
    """
    A sequential Starmap, useful for debugging purpose.
    """
    def __init__(self, func, iterargs, poolsize=None):
        self.pool = None
        self.func = func
        allargs = list(iterargs)
        self.num_tasks = len(allargs)
        logging.info('Starting %d sequential tasks', self.num_tasks)
        self.imap = [safely_call(func, args) for args in allargs]


class Threadmap(BaseStarmap):
    """
    MapReduce implementation based on threads. For instance

    >>> from collections import Counter
    >>> c = Threadmap(Counter, [('hello',), ('world',)], poolsize=4).reduce()
    >>> sorted(c.items())
    [('d', 1), ('e', 1), ('h', 1), ('l', 3), ('o', 2), ('r', 1), ('w', 1)]
    """
    poolfactory = staticmethod(
        lambda size: multiprocessing.dummy.Pool(size))


class Processmap(BaseStarmap):
    """
    MapReduce implementation based on processes. For instance

    >>> from collections import Counter
    >>> c = Processmap(Counter, [('hello',), ('world',)], poolsize=4).reduce()
    >>> sorted(c.items())
    [('d', 1), ('e', 1), ('h', 1), ('l', 3), ('o', 2), ('r', 1), ('w', 1)]
    """

# ######################## support for grid engine ######################## #


def qsub(func, allargs, authkey=None):
    """
    Map functions to arguments by means of the Grid Engine.

    :param func: a pickleable callable object
    :param allargs: a list of tuples of arguments
    :param authkey: authentication token used to send back the results
    :returns: an iterable over results of the form (res, etype, mon)
    """
    thisfile = os.path.abspath(__file__)
    host = socket.gethostbyname(socket.gethostname())
    listener = Listener((host, 0), backlog=5, authkey=authkey)
    try:
        hostport = listener._listener._socket.getsockname()
        subprocess.call(
            ['qsub', '-b', 'y', '-t', '1-%d' % len(allargs), '-N',
             func.__name__, sys.executable, thisfile, '%s:%d' % hostport])
        conndict = {}
        for i, args in enumerate(allargs, 1):
            monitor = args[-1]
            monitor.task_no = i
            monitor.weight = getattr(args[0], 'weight', 1.)
            conn = _getconn(listener)  # get the first connected task
            conn.send((func, args))  # send its arguments
            for data, task_no in _getdata(conndict):
                yield data  # yield the data received by other tasks, if any
                del conndict[task_no]
            conndict[i] = conn
        # yield the rest of the data
        for task_no in sorted(conndict):
            conn = conndict[task_no]
            try:
                data = conn.recv()
            finally:
                conn.close()
            yield data
    finally:
        listener.close()


def _getdata(conndict):
    for task_no in sorted(conndict):
        conn = conndict[task_no]
        if conn.poll():
            try:
                data = conn.recv()
            finally:
                conn.close()
            yield data, task_no


def _getconn(listener):
    while True:
        try:
            conn = listener.accept()
        except KeyboardInterrupt:
            return
        except:
            # unauthenticated connection, for instance by a port scanner
            continue
        return conn


def main(hostport):
    host, port = hostport.split(':')
    conn = Client((host, int(port)))
    func, args = conn.recv()
    safely_call(func, args, False, conn)

if __name__ == '__main__':
    main(sys.argv[1])
