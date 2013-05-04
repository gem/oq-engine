import os
import time
import atexit
from datetime import datetime
import psutil

import numpy
from django.db import connections

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.writer import CacheInserter


# I did not make any attempt to make this class thread-safe,
# since it is intended to be used in single-threaded programs, as
# in the engine
class PerformanceMonitor(object):
    """
    Measure the resident memory occupied by a list of processes during
    the execution of a block of code. Should be used as a context manager,
    as follows::

     with PerformanceMonitor([os.getpid()]) as mm:
         do_something()
     maxmemory, = mm.mem

    At the end of the block the PerformanceMonitor object will have the
    following 5 public attributes:

    .start_time: when the monitor started (a datetime object)
    .duration: time elapsed between start and stop (in seconds)
    .exc: None unless an exception happened inside the block of code
    .mem: an array with the memory deltas (in megabytes)

    The memory tuples have the same length as the number of processes.
    The behaviour of the PerformanceMonitor can be customized by subclassing it
    and by overriding the method on_exit(), called at end and used to display
    or store the results of the analysis; the on_running() method is
    called while the analysis is running and can be used to display
    or store the partial results.
    """

    def __init__(self, pids):
        self._procs = [psutil.Process(pid) for pid in pids]
        self._start_time = None  # seconds from the epoch
        self.start_time = None  # datetime object
        self.duration = None  # seconds
        self.mem = None  # megabytes
        self.exc = None  # exception

    def measure_mem(self):
        "An array of memory measurements (in bytes), one per process"
        mem = []
        for proc in list(self._procs):
            try:
                rss = proc.get_memory_info().rss
            except psutil.AccessDenied:
                # no access to information about this process
                # don't not try to check it anymore
                self._procs.remove(proc)
            else:
                mem.append(rss)
        return numpy.array(mem)

    def start(self):
        "Start the monitor thread"
        self._start_time = time.time()
        self.start_time = datetime.fromtimestamp(self._start_time)
        self.start_mem = self.measure_mem()

    def stop(self):
        "Stop the monitor thread and call on_exit"
        self.stop_mem = self.measure_mem()
        self.mem = self.stop_mem - self.start_mem
        self.duration = time.time() - self._start_time
        self.on_exit()

    def __enter__(self):
        "Call .start"
        self.exc = None
        self.start()
        return self

    def __exit__(self, etype, exc, tb):
        "Call .stop"
        self.exc = exc
        self.stop()

    def on_exit(self):
        "Save the results: to be overridden in subclasses"
        print 'start_time =', self.start_time
        print 'duration =', self.duration
        print 'mem =', self.mem
        print 'exc =', self.exc


class EnginePerformanceMonitor(PerformanceMonitor):
    """
    Performance monitor specialized for the engine. It takes in input a
    string, a job_id, and a celery task; the on_exit method
    send the relevant info to the uiapi.performance table.
    For efficiency reasons the saving on the database is delayed and
    done in chunks of 1,000 rows each. That means that hundreds of
    concurrents task can log simultaneously on the uiapi.performance table
    without problems. You can save more often by calling the .cache.flush()
    method; it is automatically called for you by the oqtask decorator;
    it is also called automatically at the end of the main process.
    """

    # globals per process
    cache = CacheInserter(1000)  # store at most 1,000 objects
    pg_pid = None
    py_pid = None

    def __init__(self, operation, job_id, task=None, tracing=False,
                 profile_mem=True):
        self.operation = operation
        self.job_id = job_id
        if task:
            self.task = task.__name__
            self.task_id = task.request.id
        else:
            self.task = None
            self.task_id = None
        self.tracing = tracing
        self.profile_mem = profile_mem
        if self.profile_mem:  # NB: this may be slow
            if self.py_pid is None:
                self.__class__.py_pid = os.getpid()
            if self.pg_pid is None:
                self.__class__.pg_pid = connections['job_init'].cursor().\
                    connection.get_backend_pid()
            try:
                psutil.Process(self.pg_pid)
            except psutil.error.NoSuchProcess:  # db on a different machine
                pids = [self.py_pid]
            else:
                pids = [self.py_pid, self.pg_pid]
        else:
            pids = []

        if tracing:
            self.tracer = logs.tracing(operation)

        super(EnginePerformanceMonitor, self).__init__(pids)

    def __enter__(self):
        super(EnginePerformanceMonitor, self).__enter__()
        if self.tracing:
            self.tracer.__enter__()
        return self

    def on_exit(self):
        """
        Save the memory consumption on the uiapi.performance table.
        """
        n_measures = len(self.mem)
        if n_measures == 2:
            pymemory, pgmemory = self.mem
        elif n_measures == 1:
            pymemory, = self.mem
            pgmemory = None
        elif n_measures == 0:  # profile_mem was False
            pymemory = pgmemory = None
        else:
            raise ValueError(
                'Got %d memory measurements, must be <= 2' % n_measures)
        if self.exc is None:  # save only valid calculations
            perf = models.Performance(
                oq_job_id=self.job_id,
                task_id=self.task_id,
                task=self.task,
                operation=self.operation,
                start_time=self.start_time,
                duration=self.duration,
                pymemory=pymemory,
                pgmemory=pgmemory)
            self.cache.add(perf)

    def __exit__(self, etype, exc, tb):
        super(EnginePerformanceMonitor, self).__exit__(etype, exc, tb)
        if self.tracing:
            self.tracer.__exit__(etype, exc, tb)

## makes sure the performance results are flushed in the db at the end
atexit.register(EnginePerformanceMonitor.cache.flush)


class DummyMonitor(object):
    """
    This class makes it easy to disable the monitoring
    in client code, by simply changing an import statement:

    from openquake.engine.performance import DummyMonitor as EnginePerformanceMonitor
    Disabling the monitor can improve the performance.
    """
    def __init__(self, *args, **kw):
        pass

    def __enter__(self):
        return self

    def __exit__(self, etype, exc, tb):
        pass
