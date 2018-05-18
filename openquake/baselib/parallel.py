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

You can of course override the defaults, so if you really want to
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
import os
import sys
import mock
import time
import socket
import signal
import pickle
import inspect
import logging
import operator
import functools
import itertools
import traceback
import multiprocessing.dummy
import numpy
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"

from openquake.baselib import hdf5, config
from openquake.baselib.zeromq import zmq, Socket
from openquake.baselib.performance import Monitor, virtual_memory
from openquake.baselib.general import (
    split_in_blocks, block_splitter, AccumDict, humansize)

cpu_count = multiprocessing.cpu_count()
OQ_DISTRIBUTE = os.environ.get('OQ_DISTRIBUTE', 'processpool').lower()
if OQ_DISTRIBUTE == 'futures':  # legacy name
    print('Warning: OQ_DISTRIBUTE=futures is deprecated', file=sys.stderr)
    OQ_DISTRIBUTE = os.environ['OQ_DISTRIBUTE'] = 'processpool'
if OQ_DISTRIBUTE not in ('no', 'processpool', 'threadpool', 'celery', 'zmq'):
    raise ValueError('Invalid oq_distribute=%s' % OQ_DISTRIBUTE)


def oq_distribute(task=None):
    """
    :returns: the value of OQ_DISTRIBUTE or 'processpool'
    """
    dist = os.environ.get('OQ_DISTRIBUTE', 'processpool').lower()
    read_access = getattr(task, 'read_access', True)
    if dist.startswith('celery') and not read_access:
        raise ValueError('You must configure the shared_dir in openquake.cfg '
                         'in order to be able to run %s with celery' %
                         task.__name__)
    return dist


def check_mem_usage(monitor=Monitor(),
                    soft_percent=None, hard_percent=None):
    """
    Display a warning if we are running out of memory

    :param int mem_percent: the memory limit as a percentage
    """
    soft_percent = soft_percent or config.memory.soft_mem_limit
    hard_percent = hard_percent or config.memory.hard_mem_limit
    used_mem_percent = virtual_memory().percent
    if used_mem_percent > hard_percent:
        raise MemoryError('Using more memory than allowed by configuration '
                          '(Used: %d%% / Allowed: %d%%)! Shutting down.' %
                          (used_mem_percent, hard_percent))
    elif used_mem_percent > soft_percent:
        hostname = socket.gethostname()
        logging.warn('Using over %d%% of the memory in %s!',
                     used_mem_percent, hostname)


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


class Result(object):
    """
    :param val: value to return or exception instance
    :param mon: Monitor instance
    :param tb_str: traceback string (empty if there was no exception)
    """
    def __init__(self, val, mon, tb_str=''):
        self.pik = Pickled(val)
        self.mon = mon
        self.tb_str = tb_str

    def get(self):
        """
        Returns the underlying value or raise the underlying exception
        """
        with self.mon('unpickling %s' % self.mon.operation):
            val = self.pik.unpickle()
        if self.tb_str:
            etype = val.__class__
            msg = '\n%s%s: %s' % (self.tb_str, etype.__name__, val)
            if issubclass(etype, KeyError):
                raise RuntimeError(msg)  # nicer message
            else:
                raise etype(msg)
        return val


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
    with Monitor('total ' + func.__name__, measuremem=True) as child:
        if args and hasattr(args[0], 'unpickle'):
            # args is a list of Pickled objects
            args = [a.unpickle() for a in args]
        if args and isinstance(args[-1], Monitor):
            mon = args[-1]
            mon.operation = func.__name__
            mon.children.append(child)  # child is a child of mon
            child.hdf5path = mon.hdf5path
        else:
            mon = child
        try:
            res = Result(func(*args), mon)
        except:
            _etype, exc, tb = sys.exc_info()
            res = Result(exc, mon, ''.join(traceback.format_tb(tb)))
    # FIXME: check_mem_usage is disabled here because it's causing
    # dead locks in threads when log messages are raised.
    # Check is done anyway in other parts of the code
    # further investigation is needed
    # check_mem_usage(mon)  # check if too much memory is used
    backurl = getattr(mon, 'backurl', None)
    zsocket = (Socket(backurl, zmq.PUSH, 'connect') if backurl
               else mock.MagicMock())  # do nothing
    with zsocket:
        zsocket.send(res)
    return zsocket.num_sent if backurl else res


if OQ_DISTRIBUTE.startswith('celery'):
    from celery.result import ResultSet
    from celery import Celery
    from celery.task import task
    app = Celery('openquake')
    app.config_from_object('openquake.engine.celeryconfig')
    safetask = task(safely_call, queue='celery')  # has to be global


class IterResult(object):
    """
    :param iresults:
        an iterator over Result objects
    :param taskname:
        the name of the task
    :param num_tasks:
        the total number of expected tasks
    :param progress:
        a logging function for the progress report
    :param sent:
        the number of bytes sent (0 if OQ_DISTRIBUTE=no)
    """
    def __init__(self, iresults, taskname, argnames, num_tasks, sent,
                 progress=logging.info):
        self.iresults = iresults
        self.name = taskname
        self.argnames = ' '.join(argnames)
        self.num_tasks = num_tasks
        self.sent = sent
        self.progress = progress
        self.received = []
        if self.num_tasks:
            self.log_percent = self._log_percent()
            next(self.log_percent)
        else:
            self.progress('No %s tasks were submitted', self.name)
        self.task_data_dt = numpy.dtype(
            [('taskno', numpy.uint32), ('weight', numpy.float32),
             ('duration', numpy.float32), ('received', numpy.int64)])
        self.progress('Sent %s of data in %s task(s)',
                      humansize(sent.sum()), num_tasks)

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
        if self.num_tasks == 0:
            return
        for result in self.iresults:
            check_mem_usage()  # log a warning if too much memory is used
            if isinstance(result, BaseException):
                # this happens with WorkerLostError with celery
                raise result
            elif isinstance(result, Result):
                val = result.get()
                self.received.append(len(result.pik))
            else:  # this should never happen
                raise ValueError(result)
            next(self.log_percent)
            if not self.name.startswith('_'):  # no info for private tasks
                self.save_task_info(result.mon)
            yield val

        if self.received:
            tot = sum(self.received)
            max_per_task = max(self.received)
            self.progress('Received %s of data, maximum per task %s',
                          humansize(tot), humansize(max_per_task))

    def save_task_info(self, mon):
        if mon.hdf5path:
            duration = mon.children[0].duration  # the task is the first child
            tup = (mon.task_no, mon.weight, duration, self.received[-1])
            data = numpy.array([tup], self.task_data_dt)
            hdf5.extend3(mon.hdf5path, 'task_info/' + self.name, data,
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
    return os.getpid()


def _wakeup(sec, mon):
    """Waiting function, used to wake up the process pool"""
    time.sleep(sec)
    return os.getpid()


class Starmap(object):
    task_ids = []
    calc_id = None

    @classmethod
    def init(cls, poolsize=None, distribute=OQ_DISTRIBUTE):
        if distribute == 'processpool' and not hasattr(cls, 'pool'):
            cls.pool = multiprocessing.Pool(poolsize, init_workers)
            m = Monitor('wakeup')
            cls(_wakeup, [(.2, m) for _ in range(cls.pool._processes)])
        elif distribute == 'threadpool' and not hasattr(cls, 'pool'):
            cls.pool = multiprocessing.dummy.Pool(poolsize)

    @classmethod
    def shutdown(cls, poolsize=None):
        if hasattr(cls, 'pool'):
            cls.pool.close()
            cls.pool.terminate()
            cls.pool.join()
            delattr(cls, 'pool')

    @classmethod
    def apply(cls, task, args, concurrent_tasks=cpu_count * 3,
              maxweight=None, weight=lambda item: 1,
              key=lambda item: 'Unspecified', name=None, distribute=None):
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
        :param name: name of the task to be used in the log
        :param distribute: if not given, inferred from OQ_DISTRIBUTE
        :returns: an :class:`IterResult` object
        """
        arg0 = args[0]  # this is assumed to be a sequence
        args = args[1:]
        if maxweight:
            chunks = block_splitter(arg0, maxweight, weight, key)
        else:
            chunks = split_in_blocks(arg0, concurrent_tasks or 1, weight, key)
        task_args = [(ch,) + args for ch in chunks]
        return cls(task, task_args, name, distribute).submit_all()

    def __init__(self, task_func, task_args, name=None, distribute=None):
        self.__class__.init(distribute=distribute or OQ_DISTRIBUTE)
        self.task_func = task_func
        self.name = name or task_func.__name__
        self.task_args = task_args
        if self.name.startswith('_'):  # secret task
            self.progress = lambda *args: None
        else:
            self.progress = logging.info
        self.distribute = distribute or oq_distribute(task_func)
        # a task can be a function, a class or an instance with a __call__
        if inspect.isfunction(task_func):
            self.argnames = inspect.getargspec(task_func).args
        elif inspect.isclass(task_func):
            self.argnames = inspect.getargspec(task_func.__init__).args[1:]
        else:  # instance with a __call__ method
            self.argnames = inspect.getargspec(task_func.__call__).args[1:]
        self.receiver = 'tcp://%s:%s' % (
            config.dbserver.host, config.zworkers.receiver_ports)
        self.sent = numpy.zeros(len(self.argnames))

    @property
    def num_tasks(self):
        """
        The number of tasks, if known, or the empty string otherwise.
        """
        try:
            return len(self.task_args)
        except TypeError:  # generators have no len
            return ''
        # NB: returning -1 breaks openquake.hazardlib.tests.calc.
        # hazard_curve_new_test.HazardCurvesTestCase02 :-(

    def _genargs(self, backurl=None, pickle=True):
        """
        Add .task_no and .weight to the monitor and yield back
        the arguments by pickling them.
        """
        for task_no, args in enumerate(self.task_args, 1):
            mon = args[-1]
            if isinstance(mon, Monitor):
                # add incremental task number and task weight
                mon.task_no = task_no
                mon.weight = getattr(args[0], 'weight', 1.)
                mon.backurl = backurl
                self.calc_id = getattr(mon, 'calc_id', None)
            if pickle:
                args = pickle_sequence(args)
                self.sent += numpy.array([len(p) for p in args])
            if task_no == 1:  # first time
                self.progress('Submitting %s "%s" tasks', self.num_tasks,
                              self.name)
            yield args

    def submit_all(self):
        """
        :returns: an IterResult object
        """
        if self.num_tasks == 1 or self.distribute == 'no':
            it = self._iter_sequential()
        elif self.distribute in ('processpool', 'threadpool'):
            it = self._iter_pool()
        elif self.distribute == 'celery':
            it = self._iter_celery()
        elif self.distribute == 'zmq':
            it = self._iter_zmq()
        num_tasks = next(it)
        return IterResult(it, self.name, self.argnames, num_tasks,
                          self.sent, self.progress)

    def reduce(self, agg=operator.add, acc=None):
        """
        Submit all tasks and reduce the results
        """
        return self.submit_all().reduce(agg, acc)

    def __iter__(self):
        return iter(self.submit_all())

    def _iter_sequential(self):
        self.progress('Executing "%s" in process', self.name)
        allargs = list(self._genargs(pickle=False))
        yield len(allargs)
        for args in allargs:
            yield safely_call(self.task_func, args)

    def _iter_pool(self):
        safefunc = functools.partial(safely_call, self.task_func)
        allargs = list(self._genargs())
        yield len(allargs)
        for res in self.pool.imap_unordered(safefunc, allargs):
            yield res

    def iter_native(self, results):
        for task_id, result_dict in ResultSet(results).iter_native():
            self.task_ids.remove(task_id)
            yield result_dict['result']

    def _iter_celery(self):
        with Socket(self.receiver, zmq.PULL, 'bind') as socket:
            logging.info('Using receiver %s', socket.backurl)
            results = []
            for piks in self._genargs(socket.backurl):
                res = safetask.delay(self.task_func, piks)
                # populating Starmap.task_ids, used in celery_cleanup
                self.task_ids.append(res.task_id)
                results.append(res)
            num_results = len(results)
            yield num_results
            it = self.iter_native(results)
            isocket = iter(socket)
            while num_results:
                res = next(isocket)
                if self.calc_id and self.calc_id != res.mon.calc_id:
                    logging.warn('Discarding a result from job %d, since this '
                                 'is job %d', res.mon.calc_id, self.calc_id)
                    continue
                err = next(it)
                if isinstance(err, Exception):  # TaskRevokedError
                    raise err
                num_results -= 1
                yield res

    def _iter_zmq(self):
        with Socket(self.receiver, zmq.PULL, 'bind') as socket:
            task_in_url = ('tcp://%(master_host)s:%(task_in_port)s' %
                           config.zworkers)
            with Socket(task_in_url, zmq.PUSH, 'connect') as sender:
                num_results = 0
                for args in self._genargs(socket.backurl):
                    sender.send((self.task_func, args))
                    num_results += 1
            yield num_results
            isocket = iter(socket)
            while num_results:
                res = next(isocket)
                if self.calc_id and self.calc_id != res.mon.calc_id:
                    logging.warn('Discarding a result from job %d, since this '
                                 'is job %d', res.mon.calc_id, self.calc_id)
                    continue
                num_results -= 1
                yield res


def sequential_apply(task, args, concurrent_tasks=cpu_count * 3,
                     weight=lambda item: 1, key=lambda item: 'Unspecified'):
    """
    Apply sequentially task to args by splitting args[0] in blocks
    """
    chunks = split_in_blocks(args[0], concurrent_tasks or 1, weight, key)
    task_args = [(ch,) + args[1:] for ch in chunks]
    return itertools.starmap(task, task_args)
