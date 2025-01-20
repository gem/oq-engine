# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2015-2025 GEM Foundation

# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import time
import pstats
import pickle
import signal
import logging
import getpass
import tempfile
import operator
import itertools
import subprocess
import collections
from datetime import datetime
from contextlib import contextmanager
from decorator import decorator
import psutil
import numpy
import pandas
import numba

from openquake.baselib.general import humansize, fast_agg
from openquake.baselib import hdf5

# NB: one can use vstr fields in extensible datasets, but then reading
# them on-the-fly in SWMR mode will fail with an OSError:
# Can't read data (address of object past end of allocation)
# this is why below I am using '<S50' byte strings
perf_dt = numpy.dtype([('operation', '<S50'), ('time_sec', float),
                       ('memory_mb', float), ('counts', int),
                       ('task_no', numpy.int16)])
task_info_dt = numpy.dtype(
    [('taskname', '<S50'), ('task_no', numpy.uint32),
     ('weight', numpy.float32), ('duration', numpy.float32),
     ('received', numpy.int64), ('mem_gb', numpy.float32)])

F16= numpy.float16
F64= numpy.float64
I64 = numpy.int64

PStatData = collections.namedtuple(
    'PStatData', 'ncalls tottime percall cumtime percall2 path')


@contextmanager
def perf_stat():
    """
    Profile the current process by using the linux `perf` command
    """
    p = subprocess.Popen(["perf", "stat", "-p", str(os.getpid())])
    time.sleep(0.5)
    yield
    p.send_signal(signal.SIGINT)


def print_stats(pr, fname):
    """
    Print the stats of a Profile instance
    """
    with open(fname, 'w') as f:
        ps = pstats.Stats(pr, stream=f).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats()


def get_pstats(pstatfile, n):
    """
    Return profiling information as a list [(ncalls, cumtime, path), ...]

    :param pstatfile: path to a .pstat file
    :param n: the maximum number of stats to retrieve
    """
    with tempfile.TemporaryFile(mode='w+') as stream:
        ps = pstats.Stats(pstatfile, stream=stream)
        ps.sort_stats('cumtime')
        ps.print_stats(n)
        stream.seek(0)
        lines = list(stream)
    for i, line in enumerate(lines):
        if line.startswith('   ncalls'):
            break
    data = []
    for line in lines[i + 2:]:
        columns = line.split()
        if len(columns) == 6:
            columns[-1] = os.path.basename(columns[-1])
            data.append(PStatData(*columns))
    rows = [(rec.ncalls, rec.cumtime, rec.path) for rec in data]
    return rows


def init_performance(hdf5file, swmr=False):
    """
    :param hdf5file: file name of hdf5.File instance
    """
    fname = isinstance(hdf5file, str)
    h5 = hdf5.File(hdf5file, 'a') if fname else hdf5file
    if 'performance_data' not in h5:
        hdf5.create(h5, 'performance_data', perf_dt)
    if 'task_info' not in h5:
        hdf5.create(h5, 'task_info', task_info_dt)
    if 'task_sent' not in h5:
        h5['task_sent'] = '{}'
    if swmr:
        try:
            h5.swmr_mode = True
        except ValueError as exc:
            raise ValueError('%s: %s' % (hdf5file, exc))
    if fname:
        h5.close()


def performance_view(dstore):
    """
    Returns the performance view as a numpy array.
    """
    pdata = dstore['performance_data']
    pdata.refresh()
    data = sorted(pdata[()], key=operator.itemgetter(0))
    out = []
    for operation, group in itertools.groupby(data, operator.itemgetter(0)):
        counts = 0
        time = 0
        mem = 0
        for rec in group:
            counts += rec['counts']
            time += rec['time_sec']
            mem = max(mem, rec['memory_mb'])
        out.append((operation, time, mem, counts))
    out.sort(key=operator.itemgetter(1), reverse=True)  # sort by time
    mems = dstore['task_info']['mem_gb']
    maxmem = ', maxmem=%.1f GB' % mems.max() if len(mems) else ''
    if hasattr(dstore, 'calc_id'):
        operation = 'calc_%d%s' % (dstore.calc_id, maxmem)
    else:
        operation = 'operation'
    dtlist = [(operation, perf_dt['operation'])]
    dtlist.extend((n, perf_dt[n]) for n in perf_dt.names[1:-1])
    return numpy.array(out, dtlist)


def _pairs(items):
    lst = []
    for name, value in items:
        if isinstance(value, dict):
            for k, v in value.items():
                lst.append(('%s.%s' % (name, k), repr(v)))
        else:
            lst.append((name, repr(value)))
    return sorted(lst)


def memory_rss(pid):
    """
    :returns: the RSS memory allocated by a process
    """
    try:
        return psutil.Process(pid).memory_info().rss
    except psutil.NoSuchProcess:
        return 0


def memory_gb(pids=()):
    """
    :params pids: a list or PIDs running on the same machine
    :returns: the total memory allocated by the current process and all the PIDs
    """
    return sum(map(memory_rss, [os.getpid()] + list(pids))) / 1024**3


# this is not thread-safe
class Monitor(object):
    """
    Measure the resident memory occupied by a list of processes during
    the execution of a block of code. Should be used as a context manager,
    as follows::

     with Monitor('do_something') as mon:
         do_something()
     print mon.mem

    At the end of the block the Monitor object will have the
    following 5 public attributes:

    .start_time: when the monitor started (a datetime object)
    .duration: time elapsed between start and stop (in seconds)
    .exc: usually None; otherwise the exception happened in the `with` block
    .mem: the memory delta in bytes

    The behaviour of the Monitor can be customized by subclassing it
    and by overriding the method on_exit(), called at end and used to display
    or store the results of the analysis.

    NB: if the .address attribute is set, it is possible for the monitor to
    send commands to that address, assuming there is a
    :class:`multiprocessing.connection.Listener` listening.
    """
    address = None
    authkey = None
    calc_id = None
    inject = None
    #config = config

    def __init__(self, operation='', measuremem=False, inner_loop=False,
                 h5=None, version=None, dbserver_host='127.0.0.1'):
        self.operation = operation
        self.measuremem = measuremem
        self.inner_loop = inner_loop
        self.h5 = h5
        self.version = version
        self._mem = 0
        self.duration = 0
        self._start_time = self._stop_time = time.time()
        self.children = []
        self.counts = 0
        self.address = None
        self.username = getpass.getuser()
        self.task_no = -1  # overridden in parallel
        self.dbserver_host = dbserver_host

    @property
    def mem(self):
        """Mean memory allocation"""
        return self._mem / (self.counts or 1)

    @property
    def dt(self):
        """Last time interval measured"""
        return self._stop_time - self._start_time

    def measure_mem(self):
        """A memory measurement (in bytes)"""
        try:
            return memory_rss(os.getpid())
        except psutil.AccessDenied:
            # no access to information about this process
            pass

    @property
    def start_time(self):
        """
        Datetime instance recording when the monitoring started
        """
        return datetime.fromtimestamp(self._start_time)

    def _get_data(self):
        data = []
        if self.counts:
            time_sec = self.duration
            memory_mb = self.mem / 1024. / 1024. if self.measuremem else 0
            data.append((self.operation, time_sec, memory_mb, self.counts,
                         self.task_no))
        return numpy.array(data, perf_dt)

    def get_data(self):
        """
        :returns:
            an array of dtype perf_dt, with the information
            of the monitor (operation, time_sec, memory_mb, counts);
            the lenght of the array can be 0 (for counts=0) or 1 (otherwise).
        """
        if not self.children:
            data = self._get_data()
        else:
            lst = [self._get_data()]
            for child in self.children:
                lst.append(child.get_data())
                child.reset()
            data = numpy.concatenate(lst, dtype=perf_dt)
        return data

    def log_data(self):
        data = self.get_data()[['operation', 'time_sec']]
        data.sort(order='time_sec')
        if len(data):
            for row in data:
                op = row['operation'].decode('utf8')
                logging.info(f"{op} = {round(row['time_sec'], 3)} seconds")

    def __enter__(self):
        self.exc = None  # exception
        self._start_time = time.time()
        if self.measuremem:
            self.start_mem = self.measure_mem()
        return self

    def __exit__(self, etype, exc, tb):
        self.exc = exc
        if self.measuremem:
            self.stop_mem = self.measure_mem()
            self._mem += self.stop_mem - self.start_mem
        self._stop_time = time.time()
        self.duration += self._stop_time - self._start_time
        self.counts += 1
        if self.h5:
            self.flush(self.h5)

    def save_task_info(self, h5, res, name, mem_gb=0):
        """
        Called by parallel.IterResult.

        :param h5: where to save the info
        :param res: a :class:`Result` object
        :param name: name of the task function
        :param mem_gb: memory consumption at the saving time (optional)
        """
        t = (name, self.task_no, self.weight, self.duration, len(res.pik),
             mem_gb)
        data = numpy.array([t], task_info_dt)
        hdf5.extend(h5['task_info'], data)
        h5['task_info'].flush()  # notify the reader

    def reset(self):
        """
        Reset duration, mem, counts
        """
        self.duration = 0
        self._mem = 0
        self.counts = 0

    def flush(self, h5):
        """
        Save the measurements on the performance file
        """
        data = self.get_data()
        if len(data):
            hdf5.extend(h5['performance_data'], data)
            h5['performance_data'].flush()  # notify the reader
            self.reset()

    # TODO: rename this as spawn; see what will break
    def __call__(self, operation='no operation', **kw):
        """
        Return a child of the monitor usable for a different operation.
        """
        child = self.new(operation, **kw)
        self.children.append(child)
        return child

    def new(self, operation='no operation', **kw):
        """
        Return a copy of the monitor usable for a different operation.
        """
        new = object.__new__(self.__class__)
        vars(new).update(vars(self), operation=operation, children=[],
                         counts=0, mem=0, duration=0)
        vars(new).update(kw)
        return new

    def save(self, key, obj):
        """
        :param key: key in the _tmp.hdf5 file
        :param obj: big object to store in pickle format
        :returns: True is saved, False if not because the key was taken
        """
        tmp = self.filename[:-5] + '_tmp.hdf5'
        f = hdf5.File(tmp, 'a') if os.path.exists(tmp) else hdf5.File(tmp, 'w')
        with f:
            if key in f:  # already saved
                return False
            if isinstance(obj, numpy.ndarray):
                f[key] = obj
            elif isinstance(obj, pandas.DataFrame):
                f.create_df(key, obj)
            else:
                f[key] = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        return True

    def read(self, key, slc=slice(None)):
        """
        :param key: key in the _tmp.hdf5 file
        :param slc: slice to read (default all)
        :return: unpickled object
        """
        tmp = self.filename[:-5] + '_tmp.hdf5'
        with hdf5.File(tmp, 'r') as f:
            dset = f[key]
            if '__pdcolumns__' in dset.attrs:
                return f.read_df(key, slc=slc)
            elif dset.shape:
                return dset[slc]
            return pickle.loads(dset[()])

    def iter(self, genobj, atstop=lambda: None):
        """
        :param genobj: a generator object
        :param atstop: optional thunk to call at StopIteration
        :yields: the elements of the generator object
        """
        while True:
            try:
                self._mem = 0
                with self:
                    obj = next(genobj)
            except StopIteration:
                atstop()
                return
            else:
                yield obj

    def __repr__(self):
        calc_id = ' #%s ' % self.calc_id if self.calc_id else ' '
        msg = '%s%s%s[%s]' % (self.__class__.__name__, calc_id,
                              self.operation, self.username)
        if self.measuremem:
            return '<%s, duration=%ss, memory=%s>' % (
                msg, self.duration, humansize(self.mem))
        elif self.duration:
            return '<%s, duration=%ss, counts=%s>' % (
                msg, self.duration, self.counts)
        else:
            return '<%s>' % msg


def vectorize_arg(idx):
    """
    Vectorize a function efficiently, if the argument with index `idx` contains
    many repetitions.
    """
    def caller(func, *args):
        args = list(args)
        uniq, inv = numpy.unique(args[idx], return_inverse=True)
        res = []
        for arg in uniq:
            args[idx] = arg
            res.append(func(*args))
        return numpy.array(res)[inv]

    return decorator(caller)


# numba helpers
# NB: without cache=True the tests would take hours!!

def jittable(func):
    """Calls numba.njit with a cache"""
    jitfunc = numba.njit(func, error_model='numpy', cache=True)
    jitfunc.jittable = True
    return jitfunc

def compile(sigstr):
    """
    Compile a function Ahead-Of-Time using the given signature string
    """
    return numba.njit(sigstr, error_model='numpy', cache=True)


# used when reading _rates/sid
@compile(["int64[:, :](uint8[:])",
          "int64[:, :](uint16[:])",
          "int64[:, :](uint32[:])",
          "int64[:, :](int32[:])",
          "int64[:, :](int64[:])"])
def idx_start_stop(integers):
    # given an array of integers returns an array int64 of shape (n, 3)
    out = []
    start = i = 0
    prev = integers[0]
    for i, val in enumerate(integers[1:], 1):
        if val != prev:
            out.append((I64(prev), start, i))
            start = i
        prev = val
    out.append((I64(prev), start, i + 1))
    return numpy.array(out, I64)


@compile("int64[:, :](uint32[:], uint32)")
def split_slices(integers, size):
    # given an array of integers returns an array int64 of shape (n, 2)
    out = []
    start = i = 0
    prev = integers[0]
    totsize = 1
    for i, val in enumerate(integers[1:], 1):
        totsize += 1
        if val != prev and totsize >= size:
            out.append((start, i))
            totsize = 0
            start = i
        prev = val
    out.append((start, i + 1))
    return numpy.array(out, I64)


# this is absurdly fast if you have numba
def get_slices(uint32s):
    """
    :param uint32s: a sequence of uint32 integers (with repetitions)
    :returns: a dict integer -> [(start, stop), ...]

    >>> from pprint import pprint
    >>> pprint(get_slices(numpy.uint32([0, 0, 3, 3, 3, 2, 2, 0])))
    {0: [(0, 2), (7, 8)], 2: [(5, 7)], 3: [(2, 5)]}
    """
    if len(uint32s) == 0:
        return {}
    indices = {}  # idx -> [(start, stop), ...]
    for idx, start, stop in idx_start_stop(uint32s):
        if idx not in indices:
            indices[idx] = []
        indices[idx].append((start, stop))
    return indices


# this is used in split_array and it may dominate the performance
# of classical calculations, so it has to be fast
@compile(["uint32[:](uint32[:], int64[:], int64[:], int64[:])",
          "uint32[:](uint16[:], int64[:], int64[:], int64[:])"])
def _split(uint32s, indices, counts, cumcounts):
    n = len(uint32s)
    assert len(indices) == n
    assert len(counts) <= n
    out = numpy.zeros(n, numpy.uint32)
    for idx, val in zip(indices, uint32s):
        cumcounts[idx] -= 1
        out[cumcounts[idx]] = val
    return out


# 3-argument version tested in SplitArrayTestCase
def split_array(arr, indices, counts=None):
    """
    :param arr: an array with N elements
    :param indices: a set of integers with repetitions
    :param counts: if None the indices MUST be ordered
    :returns: a list of K arrays, split on the integers

    >>> arr = numpy.array([.1, .2, .3, .4, .5])
    >>> idx = numpy.array([1, 1, 2, 2, 3])
    >>> split_array(arr, idx)
    [array([0.1, 0.2]), array([0.3, 0.4]), array([0.5])]
    """
    if counts is None:  # ordered indices
        return [arr[s1:s2] for i, s1, s2 in idx_start_stop(indices)]
    # indices and counts coming from numpy.unique(arr)
    # this part can be slow, but it is still 10x faster than pandas for EUR!
    cumcounts = counts.cumsum()
    out = _split(arr, indices, counts, cumcounts)
    return [out[s1:s2][::-1] for s1, s2 in zip(cumcounts, cumcounts + counts)]


def kround0(ctx, kfields):
    """
    half-precision rounding
    """
    out = numpy.zeros(len(ctx), [(k, ctx.dtype[k]) for k in kfields])
    for kfield in kfields:
        kval = ctx[kfield]
        if kval.dtype == F64:
            out[kfield] = F16(kval)
        else:
            out[kfield] = ctx[kfield]
    return out


# this is not so fast
def kollapse(array, kfields, kround=kround0, mfields=(), afield=''):
    """
    Given a structured array of N elements with a discrete kfield with
    K <= N unique values, returns a structured array of K elements
    obtained by averaging the values associated to the kfield.
    """
    k_array = kround(array, kfields)
    uniq, indices, counts = numpy.unique(
        k_array, return_inverse=True, return_counts=True)
    klist = [(k, k_array.dtype[k]) for k in kfields]
    for mfield in mfields:
        klist.append((mfield, array.dtype[mfield]))
    res = numpy.zeros(len(uniq), klist)
    for kfield in kfields:
        res[kfield] = uniq[kfield]
    for mfield in mfields:
        values = array[mfield]
        res[mfield] = fast_agg(indices, values) / (
            counts if len(values.shape) == 1 else counts.reshape(-1, 1))
    if afield:
        return res, split_array(array[afield], indices, counts)
    return res
