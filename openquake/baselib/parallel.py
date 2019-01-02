# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2018 GEM Foundation
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

There are several good libraries to manage parallel programming, both
in the standard library and in third party packages. Since we are not
interested in reinventing the wheel, OpenQuake does not offer any new
parallel library; however, it does offer some glue code so that you
can use your library of choice. Currently threading, multiprocessing,
zmq and celery are supported. Moreover,
:mod:`openquake.baselib.parallel` offers some additional facilities
that make it easier to parallelize scientific computations,
i.e. embarrassing parallel problems.

Typically one wants to apply a callable to a list of arguments in
parallel rather then sequentially, and then combine together the
results. This is known as a `MapReduce` problem. As a simple example,
we will consider the problem of counting the letters in a text. Here is
how you can solve the problem in parallel by using
:class:`openquake.baselib.parallel.Starmap`:

>>> from functools import reduce  # reduce an iterable with a binary operator
>>> from operator import add  # addition function
>>> from openquake.baselib.performance import Monitor
>>> mon = Monitor('count')
>>> arglist = [('hello',), ('world',)]  # list of arguments
>>> results = Starmap(count, arglist, mon)  # iterator over the results
>>> res = reduce(add, results, collections.Counter())  # aggregated counts
>>> sorted(res.items())  # counts per letter
[('d', 1), ('e', 1), ('h', 1), ('l', 3), ('o', 2), ('r', 1), ('w', 1)]

As you see there are some notational advantages with respect to use
`itertools.starmap`. First of all, `Starmap` has a `reduce` method, so
there is no need to import `functools.reduce`; secondly, the `reduce`
method has sensible defaults:

1. the default aggregation function is `add`, so there is no need to specify it
2. the default accumulator is an empty accumulation dictionary (see
   :class:`openquake.baselib.AccumDict`) working as a `Counter`, so there
   is no need to specify it.

You can of course override the defaults, so if you really want to
return a `Counter` you can do

>>> res = Starmap(count, arglist).reduce(acc=collections.Counter())

In the engine we use nearly always callables that return dictionaries
and we aggregate nearly always with the addition operator, so such
defaults are very convenient. You are encouraged to do the same, since we
found that approach to be very flexible. Typically in a scientific
application you will return a dictionary of numpy arrays.

The parallelization algorithm used by `Starmap` will depend on the
environment variable `OQ_DISTRIBUTE`. Here are the possibilities
available at the moment:

`OQ_DISTRIBUTE` not set or set to "processpool":
  use multiprocessing
`OQ_DISTRIBUTE` set to "no":
  disable the parallelization, useful for debugging
`OQ_DISTRIBUTE` set to "celery":
   use celery, useful if you have multiple machines in a cluster
`OQ_DISTRIBUTE` set tp "zmq"
   use the zmq concurrency mechanism (experimental)

There is also an `OQ_DISTRIBUTE` = "threadpool"; however the
performance of using threads instead of processes is normally bad for the
kind of applications we are interested in (CPU-dominated, which large
tasks such that the time to spawn a new process is negligible with
respect to the time to perform the task), so it is not recommended.

If you are using a pool, is always a good idea to cleanup resources at the end
with

>>> Starmap.shutdown()

`Starmap.shutdown` is always defined. It does nothing if there is
no pool, but it is still better to call it: in the future, you may change
idea and use another parallelization strategy requiring cleanup. In this
way your code is future-proof.

The Starmap.apply API
====================================

The `Starmap` class has a very convenient classmethod `Starmap.apply`
which is used in several places in the engine. `Starmap.apply` is useful
when you have a sequence of objects that you want to split in homogenous chunks
and then apply a callable to each chunk (in parallel). For instance, in the
letter counting example discussed before, `Starmap.apply` could
be used as follows:

>>> text = 'helloworld'  # sequence of characters
>>> res3 = Starmap.apply(count, (text, mon)).reduce()
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
import os
import sys
import time
import socket
import signal
import pickle
import inspect
import logging
import operator
import itertools
import traceback
import collections
import multiprocessing.dummy
import psutil
import numpy
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"

from openquake.baselib import hdf5, config
from openquake.baselib.zeromq import zmq, Socket
from openquake.baselib.performance import Monitor, memory_rss, perf_dt

from openquake.baselib.general import (
    split_in_blocks, block_splitter, AccumDict, humansize)

cpu_count = multiprocessing.cpu_count()
GB = 1024 ** 3
OQ_DISTRIBUTE = os.environ.get('OQ_DISTRIBUTE', 'processpool').lower()
if OQ_DISTRIBUTE == 'futures':  # legacy name
    print('Warning: OQ_DISTRIBUTE=futures is deprecated', file=sys.stderr)
    OQ_DISTRIBUTE = os.environ['OQ_DISTRIBUTE'] = 'processpool'
if OQ_DISTRIBUTE not in ('no', 'processpool', 'threadpool', 'celery', 'zmq',
                         'dask'):
    raise ValueError('Invalid oq_distribute=%s' % OQ_DISTRIBUTE)

# data type for storing the performance information
task_info_dt = numpy.dtype(
    [('taskno', numpy.uint32), ('weight', numpy.float32),
     ('duration', numpy.float32), ('received', numpy.int64),
     ('mem_gb', numpy.float32)])


def oq_distribute(task=None):
    """
    :returns: the value of OQ_DISTRIBUTE or 'processpool'
    """
    return os.environ.get('OQ_DISTRIBUTE', 'processpool').lower()


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
        try:
            self.pik = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
        except TypeError as exc:  # can't pickle, show the obj in the message
            raise TypeError('%s: %s' % (exc, obj))

    def __repr__(self):
        """String representation of the pickled object"""
        return '<Pickled %s #%s %s>' % (
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


class Result(object):
    """
    :param val: value to return or exception instance
    :param mon: Monitor instance
    :param tb_str: traceback string (empty if there was no exception)
    :param msg: message string (default empty)
    """
    def __init__(self, val, mon, tb_str='', msg='', count=0):
        if isinstance(val, dict):
            # store the size in bytes of the content
            self.nbytes = {k: len(Pickled(v)) for k, v in val.items()}
        self.pik = Pickled(val)
        self.mon = mon
        self.tb_str = tb_str
        self.msg = msg
        self.count = count

    def get(self):
        """
        Returns the underlying value or raise the underlying exception
        """
        val = self.pik.unpickle()
        if self.tb_str:
            etype = val.__class__
            msg = '\n%s%s: %s' % (self.tb_str, etype.__name__, val)
            if issubclass(etype, KeyError):
                raise RuntimeError(msg)  # nicer message
            else:
                raise etype(msg)
        return val

    @classmethod
    def new(cls, func, args, mon, count=0):
        """
        :returns: a new Result instance
        """
        try:
            with mon:
                val = func(*args)
        except StopIteration:
            res = Result(None, mon, msg='TASK_ENDED')
        except Exception:
            _etype, exc, tb = sys.exc_info()
            res = Result(exc, mon, ''.join(traceback.format_tb(tb)),
                         count=count)
        else:
            res = Result(val, mon, count=count)
        return res


def check_mem_usage(soft_percent=None, hard_percent=None):
    """
    Display a warning if we are running out of memory
    """
    soft_percent = soft_percent or config.memory.soft_mem_limit
    hard_percent = hard_percent or config.memory.hard_mem_limit
    used_mem_percent = psutil.virtual_memory().percent
    if used_mem_percent > hard_percent:
        raise MemoryError('Using more memory than allowed by configuration '
                          '(Used: %d%% / Allowed: %d%%)! Shutting down.' %
                          (used_mem_percent, hard_percent))
    elif used_mem_percent > soft_percent:
        msg = 'Using over %d%% of the memory in %s!'
        return msg % (used_mem_percent, socket.gethostname())


dummy_mon = Monitor()
dummy_mon.backurl = None


def safely_call(func, args, mon=dummy_mon):
    """
    Call the given function with the given arguments safely, i.e.
    by trapping the exceptions. Return a pair (result, exc_type)
    where exc_type is None if no exceptions occur, otherwise it
    is the exception class and the result is a string containing
    error message and traceback.

    :param func: the function to call
    :param args: the arguments
    """
    isgenfunc = inspect.isgeneratorfunction(func)
    mon.operation = 'total ' + func.__name__
    if hasattr(args[0], 'unpickle'):
        # args is a list of Pickled objects
        args = [a.unpickle() for a in args]
    if mon is dummy_mon:  # in the DbServer
        assert not isgenfunc, func
        return Result.new(func, args, mon)

    mon.operation = 'total ' + func.__name__
    mon.measuremem = True
    mon.weight = getattr(args[0], 'weight', 1.)  # used in task_info
    args += (mon,)
    with Socket(mon.backurl, zmq.PUSH, 'connect') as zsocket:
        msg = check_mem_usage()  # warn if too much memory is used
        if msg:
            zsocket.send(Result(None, mon, msg=msg))
        if inspect.isgeneratorfunction(func):
            gfunc = func
        else:
            def gfunc(*args):
                yield func(*args)
        gobj = gfunc(*args)
        for count in itertools.count():
            res = Result.new(next, (gobj,), mon, count=count)
            # StopIteration -> TASK_ENDED
            try:
                zsocket.send(res)
            except Exception:  # like OverflowError
                _etype, exc, tb = sys.exc_info()
                err = Result(exc, mon, ''.join(traceback.format_tb(tb)),
                             count=count)
                zsocket.send(err)
            mon.duration = 0
            mon.counts = 0
            mon.children.clear()
            if res.msg == 'TASK_ENDED':
                break


if OQ_DISTRIBUTE.startswith('celery'):
    from celery import Celery
    from celery.task import task

    app = Celery('openquake')
    app.config_from_object('openquake.engine.celeryconfig')
    safetask = task(safely_call, queue='celery')  # has to be global

elif OQ_DISTRIBUTE == 'dask':
    from dask.distributed import Client


class IterResult(object):
    """
    :param iresults:
        an iterator over Result objects
    :param taskname:
        the name of the task
    :param done_total:
        a function returning the number of done tasks and the total
    :param sent:
        the number of bytes sent (0 if OQ_DISTRIBUTE=no)
    :param progress:
        a logging function for the progress report
    :param hdf5:
        if given, hdf5 file where to append the performance information
    """
    def __init__(self, iresults, taskname, argnames, sent, hdf5=None):
        self.iresults = iresults
        self.name = taskname
        self.argnames = ' '.join(argnames)
        self.sent = sent
        self.hdf5 = hdf5
        self.received = []

    def __iter__(self):
        if self.iresults == ():
            return ()
        t0 = time.time()
        self.received = []
        first_time = True
        nbytes = AccumDict()
        for result in self.iresults:
            msg = check_mem_usage()  # log a warning if too much memory is used
            if msg and first_time:
                logging.warn(msg)
                first_time = False  # warn only once
            if isinstance(result, BaseException):
                # this happens with WorkerLostError with celery
                raise result
            elif isinstance(result, Result):
                val = result.get()
                self.received.append(len(result.pik))
                if hasattr(result, 'nbytes'):
                    nbytes += result.nbytes
            else:  # this should never happen
                raise ValueError(result)
            if OQ_DISTRIBUTE == 'processpool' and sys.platform != 'darwin':
                # it normally works on macOS, but not in notebooks calling
                # notebooks, which is the case relevant for Marco Pagani
                mem_gb = (memory_rss(os.getpid()) + sum(
                    memory_rss(pid) for pid in Starmap.pids)) / GB
            else:
                # measure only the memory used by the main process
                mem_gb = memory_rss(os.getpid()) / GB
            self.save_task_info(result.mon, mem_gb)
            yield val
        if self.received:
            tot = sum(self.received)
            max_per_output = max(self.received)
            logging.info(
                'Received %s from %d %s outputs in %d seconds, biggest '
                'output=%s', humansize(tot), len(self.received),
                self.name, time.time() - t0, humansize(max_per_output))
            if nbytes:
                logging.info('Received %s',
                             {k: humansize(v) for k, v in nbytes.items()})

    def save_task_info(self, mon, mem_gb):
        if self.hdf5:
            mon.hdf5 = self.hdf5
            duration = mon.duration
            t = (mon.task_no, mon.weight, duration, self.received[-1], mem_gb)
            data = numpy.array([t], task_info_dt)
            hdf5.extend(self.hdf5['task_info/' + self.name], data,
                        argnames=self.argnames, sent=self.sent)
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


def init_workers():
    """Waiting function, used to wake up the process pool"""
    setproctitle('oq-worker')
    # unregister raiseMasterKilled in oq-workers to avoid deadlock
    # since processes are terminated via pool.terminate()
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    # prctl is still useful (on Linux) to terminate all spawned processes
    # when master is killed via SIGKILL
    try:
        import prctl
    except ImportError:
        pass
    else:
        # if the parent dies, the children die
        prctl.set_pdeathsig(signal.SIGKILL)


running_tasks = []  # currently running tasks


class Starmap(object):
    calc_id = None
    hdf5 = None
    pids = ()

    @classmethod
    def init(cls, poolsize=None, distribute=OQ_DISTRIBUTE):
        if distribute == 'processpool' and not hasattr(cls, 'pool'):
            orig_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
            # we use spawn here to avoid deadlocks with logging, see
            # https://github.com/gem/oq-engine/pull/3923 and
            # https://codewithoutrules.com/2018/09/04/python-multiprocessing/
            cls.pool = multiprocessing.get_context('spawn').Pool(
                poolsize, init_workers)
            signal.signal(signal.SIGINT, orig_handler)
            cls.pids = [proc.pid for proc in cls.pool._pool]
        elif distribute == 'threadpool' and not hasattr(cls, 'pool'):
            cls.pool = multiprocessing.dummy.Pool(poolsize)
        elif distribute == 'no' and hasattr(cls, 'pool'):
            cls.shutdown()
        elif distribute == 'dask':
            cls.dask_client = Client(config.distribution.dask_scheduler)

    @classmethod
    def shutdown(cls):
        if hasattr(cls, 'pool'):
            cls.pool.close()
            cls.pool.terminate()
            cls.pool.join()
            del cls.pool
            cls.pids = []
        if hasattr(cls, 'dask_client'):
            del cls.dask_client

    @classmethod
    def apply(cls, task, args, concurrent_tasks=cpu_count * 3,
              maxweight=None, weight=lambda item: 1,
              key=lambda item: 'Unspecified',
              distribute=None, progress=logging.info):
        """
        Apply a task to a tuple of the form (sequence, \*other_args)
        by first splitting the sequence in chunks, according to the weight
        of the elements and possibly to a key (see :func:
        `openquake.baselib.general.split_in_blocks`).

        :param task: a task to run in parallel
        :param args: the arguments to be passed to the task function
        :param concurrent_tasks: hint about how many tasks to generate
        :param maxweight: if not None, used to split the tasks
        :param weight: function to extract the weight of an item in arg0
        :param key: function to extract the kind of an item in arg0
        :param distribute: if not given, inferred from OQ_DISTRIBUTE
        :param progress: logging function to use (default logging.info)
        :returns: an :class:`IterResult` object
        """
        arg0 = args[0]  # this is assumed to be a sequence
        mon = args[-1]
        args = args[1:-1]
        if maxweight:  # block_splitter is lazy
            task_args = ((blk,) + args for blk in block_splitter(
                arg0, maxweight, weight, key))
        else:  # split_in_blocks is eager
            task_args = [(blk,) + args for blk in split_in_blocks(
                arg0, concurrent_tasks or 1, weight, key)]
        return cls(task, task_args, mon, distribute, progress).submit_all()

    def __init__(self, task_func, task_args=(), monitor=None, distribute=None,
                 progress=logging.info):
        self.__class__.init(distribute=distribute or OQ_DISTRIBUTE)
        self.task_func = task_func
        self.monitor = monitor or Monitor(task_func.__name__)
        self.calc_id = getattr(self.monitor, 'calc_id', None)
        self.name = self.monitor.operation or task_func.__name__
        self.task_args = task_args
        self.distribute = distribute or oq_distribute(task_func)
        self.progress = progress
        try:
            self.num_tasks = len(self.task_args)
        except TypeError:  # generators have no len
            self.num_tasks = None
        # a task can be a function, a class or an instance with a __call__
        if inspect.isfunction(task_func):
            self.argnames = inspect.getargspec(task_func).args
        elif inspect.isclass(task_func):
            self.argnames = inspect.getargspec(task_func.__init__).args[1:]
        else:  # instance with a __call__ method
            self.argnames = inspect.getargspec(task_func.__call__).args[1:]
        self.receiver = 'tcp://%s:%s' % (
            config.dbserver.listen, config.dbserver.receiver_ports)
        self.sent = numpy.zeros(len(self.argnames) - 1)
        self.monitor.backurl = None  # overridden later
        self.tasks = []  # populated by .submit
        h5 = self.monitor.hdf5
        task_info = 'task_info/' + self.name
        if h5 and task_info not in h5:  # first time
            # task_info and performance_data should be generated in advance
            hdf5.create(h5, task_info, task_info_dt)
        if h5 and 'performance_data' not in h5:
            hdf5.create(h5, 'performance_data', perf_dt)

    def log_percent(self):
        """
        Log the progress of the computation in percentage
        """
        done = self.total - self.todo
        percent = int(float(done) / self.total * 100)
        if not hasattr(self, 'prev_percent'):  # first time
            self.prev_percent = 0
            self.progress('Sent %s of data in %d %s task(s)',
                          humansize(self.sent.sum()), self.total, self.name)
        elif percent > self.prev_percent:
            self.progress('%s %3d%%', self.name, percent)
            self.prev_percent = percent
        return done

    def submit(self, *args):
        """
        Submit the given arguments to the underlying task
        """
        global running_tasks
        if not hasattr(self, 'socket'):  # first time
            running_tasks = self.tasks
            self.socket = Socket(self.receiver, zmq.PULL, 'bind').__enter__()
            self.monitor.backurl = 'tcp://%s:%s' % (
                config.dbserver.host, self.socket.port)
        assert not isinstance(args[-1], Monitor)  # sanity check
        # add incremental task number and task weight
        self.monitor.task_no = len(self.tasks) + 1
        dist = 'no' if self.num_tasks == 1 else self.distribute
        if dist != 'no':
            args = pickle_sequence(args)
            self.sent += numpy.array([len(p) for p in args])
        res = getattr(self, dist + '_submit')(args)
        self.tasks.append(res)

    def submit_all(self):
        """
        :returns: an IterResult object
        """
        for args in self.task_args:
            self.submit(*args)
        return self.get_results()

    def get_results(self):
        """
        :returns: an :class:`IterResult` instance
        """
        return IterResult(self._loop(), self.name, self.argnames,
                          self.sent, self.monitor.hdf5)

    def reduce(self, agg=operator.add, acc=None):
        """
        Submit all tasks and reduce the results
        """
        return self.submit_all().reduce(agg, acc)

    def __iter__(self):
        return iter(self.submit_all())

    def no_submit(self, args):
        return safely_call(self.task_func, args, self.monitor)

    def processpool_submit(self, args):
        return self.pool.apply_async(
            safely_call, (self.task_func, args, self.monitor))

    threadpool_submit = processpool_submit

    def celery_submit(self, args):
        return safetask.delay(self.task_func, args, self.monitor)

    def zmq_submit(self, args):
        if not hasattr(self, 'sender'):
            task_in_url = 'tcp://%s:%s' % (config.dbserver.host,
                                           config.zworkers.task_in_port)
            self.sender = Socket(task_in_url, zmq.PUSH, 'connect').__enter__()
        return self.sender.send((self.task_func, args, self.monitor))

    def dask_submit(self, args):
        return self.dask_client.submit(safely_call, self.task_func, args,
                                       self.monitor)

    def _loop(self):
        if not hasattr(self, 'socket'):  # no submit was ever made
            return ()
        if hasattr(self, 'sender'):
            self.sender.__exit__(None, None, None)
        isocket = iter(self.socket)
        self.total = self.todo = len(self.tasks)
        while self.todo:
            res = next(isocket)
            if self.calc_id and self.calc_id != res.mon.calc_id:
                logging.warn('Discarding a result from job %s, since this '
                             'is job %d', res.mon.calc_id, self.calc_id)
                continue
            elif res.msg == 'TASK_ENDED':
                self.log_percent()
                self.todo -= 1
            elif res.msg:
                logging.warn(res.msg)
            else:
                yield res
        self.log_percent()
        self.socket.__exit__(None, None, None)
        self.tasks.clear()


def sequential_apply(task, args, concurrent_tasks=cpu_count * 3,
                     weight=lambda item: 1, key=lambda item: 'Unspecified'):
    """
    Apply sequentially task to args by splitting args[0] in blocks
    """
    chunks = split_in_blocks(args[0], concurrent_tasks or 1, weight, key)
    task_args = [(ch,) + args[1:] for ch in chunks]
    return itertools.starmap(task, task_args)


def count(word, mon):
    """
    Used as example in the documentation
    """
    return collections.Counter(word)
