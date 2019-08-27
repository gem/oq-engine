# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2015-2019 GEM Foundation

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
import getpass
from datetime import datetime
import psutil
import numpy

from openquake.baselib.general import humansize
from openquake.baselib import hdf5

perf_dt = numpy.dtype([('operation', (bytes, 50)), ('time_sec', float),
                       ('memory_mb', float), ('counts', int)])
task_info_dt = numpy.dtype(
    [('taskno', numpy.uint32), ('weight', numpy.float32),
     ('duration', numpy.float32), ('received', numpy.int64),
     ('mem_gb', numpy.float32)])


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
    return psutil.Process(pid).memory_info().rss


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

    def __init__(self, operation='', measuremem=False, inner_loop=False):
        self.operation = operation
        self.measuremem = measuremem
        self.inner_loop = inner_loop
        self.mem = 0
        self.duration = 0
        self._start_time = self._stop_time = time.time()
        self.children = []
        self.counts = 0
        self.address = None
        self.username = getpass.getuser()

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

    def get_data(self):
        """
        :returns:
            an array of dtype perf_dt, with the information
            of the monitor (operation, time_sec, memory_mb, counts);
            the lenght of the array can be 0 (for counts=0) or 1 (otherwise).
        """
        data = []
        if self.counts:
            time_sec = self.duration
            memory_mb = self.mem / 1024. / 1024. if self.measuremem else 0
            data.append((self.operation, time_sec, memory_mb, self.counts))
        return numpy.array(data, perf_dt)

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
            self.mem += self.stop_mem - self.start_mem
        self._stop_time = time.time()
        self.duration += self._stop_time - self._start_time
        self.counts += 1
        self.on_exit()

    def on_exit(self):
        "To be overridden in subclasses"
        if hasattr(self, 'hdf5path'):
            self.flush(self.hdf5path)

    def save_task_info(self, hdf5path, res, name, sent, mem_gb=0):
        """
        Called by parallel.IterResult.

        :param hdf5path: where to save the info
        :param res: a :class:`Result` object
        :param name: name of the task function
        :param sent: number of bytes sent
        :param mem_gb: memory consumption at the saving time (optional)
        """
        t = (self.task_no, self.weight, self.duration, len(res.pik), mem_gb)
        data = numpy.array([t], task_info_dt)
        hdf5.extend3(hdf5path, 'task_info/' + name, data, sent=str(sent))

    def reset(self):
        """
        Reset duration, mem, counts
        """
        self.duration = 0
        self.mem = 0
        self.counts = 0

    def flush(self, hdf5path):
        """
        Save the measurements on the performance file
        """
        if not self.children:
            data = self.get_data()
        else:
            lst = [self.get_data()]
            for child in self.children:
                lst.append(child.get_data())
                child.reset()
            data = numpy.concatenate(lst)
        if len(data) == 0:  # no information
            return
        elif not os.path.exists(hdf5path):
            with hdf5.File(hdf5path, 'w') as h5:
                hdf5.create(h5, 'performance_data', perf_dt)
                hdf5.create(h5, 'task_info', task_info_dt)
        hdf5.extend3(hdf5path, 'performance_data', data)
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


def dump(temppath, perspath):
    """
    Dump the performance info into a persistent file,
    then remove the temporary file.

    :param temppath: the temporary file
    :param perspath: the persistent file
    """
    with hdf5.File(temppath, 'r') as h, hdf5.File(perspath, 'r+') as h5:
        if 'performance_data' not in h5:
            hdf5.create(h5, 'performance_data', perf_dt)
        hdf5.extend(h5['performance_data'], h['performance_data'][()])
        for name, dset in h['task_info'].items():
            fullname = 'task_info/' + name
            if fullname not in h5:
                hdf5.create(h5, fullname, task_info_dt)
            hdf5.extend(h5[fullname], dset[()])
            for k, v in dset.attrs.items():
                h5[fullname].attrs[k] = v
    os.remove(temppath)
