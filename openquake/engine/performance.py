import time
import atexit
from datetime import datetime

from openquake.commonlib.parallel import PerformanceMonitor
from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.writer import CacheInserter


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
    it is also called at the end of the main engine process.
    """
    # the monitor can also be used to measure the memory in postgres;
    # to that aim extract the pid with
    # connections['job_init'].cursor().connection.get_backend_pid()

    # globals per process
    cache = CacheInserter(models.Performance, 1000)  # store at most 1k objects

    @classmethod
    def store_task_id(cls, job_id, task):
        with cls('storing task id', job_id, task, flush=True):
            pass

    @classmethod
    def monitor(cls, method):
        """
        A decorator to add monitoring to calculator methods. The only
        constraints are:
        1) the method has no keyword arguments
        2) there is an attribute self.job.id
        """
        def newmeth(self, *args):
            with cls(method.__name__, self.job.id, flush=True):
                return method(self, *args)
        newmeth.__name__ = method.__name__
        return newmeth

    def __init__(self, operation, job_id, task=None, tracing=False,
                 flush=False):
        self.operation = operation
        self.job_id = job_id
        if task:
            self.task = task
            self.task_id = task.request.id
        else:
            self.task = None
            self.task_id = None
        self.tracing = tracing
        self.flush = flush
        if tracing:
            self.tracer = logs.tracing(operation)

        super(EnginePerformanceMonitor, self).__init__(operation)

    def __call__(self, operation):
        """
        Return a copy of the monitor usable for a different operation
        in the same task.
        """
        return self.__class__(operation, self.job_id, self.task,
                              self.tracing, self.flush)

    def on_exit(self):
        """
        Save the memory consumption on the uiapi.performance table.
        """
        if self.exc is None:  # save only valid calculations
            perf = models.Performance(
                oq_job_id=self.job_id,
                task_id=self.task_id,
                task=getattr(self.task, '__name__', None),
                operation=self.operation,
                start_time=self.start_time,
                duration=self.duration,
                pymemory=self.mem,
                pgmemory=None)
            self.cache.add(perf)
            if self.flush:
                self.cache.flush()

    def __enter__(self):
        super(EnginePerformanceMonitor, self).__enter__()
        if self.tracing:
            self.tracer.__enter__()
        return self

    def __exit__(self, etype, exc, tb):
        super(EnginePerformanceMonitor, self).__exit__(etype, exc, tb)
        if self.tracing:
            self.tracer.__exit__(etype, exc, tb)

## makes sure the performance results are flushed in the db at the end
atexit.register(EnginePerformanceMonitor.cache.flush)


class LightMonitor(object):
    """
    in situations where a `PerformanceMonitor` is overkill or affects
    the performance (as in short loops), this helper can aid in
    measuring roughly the performance of a small piece of code. Please
    note that it does not prevent the common traps in measuring the
    performance as stated in the "Algorithms" chapter in the Python
    Cookbook.
    """
    def __init__(self, operation, job_id, task=None):
        self.operation = operation
        self.job_id = job_id
        if task is not None:
            self.task = task
            self.task_id = task.request.id
        else:
            self.task = None
            self.task_id = None
        self.t0 = time.time()
        self.start_time = datetime.fromtimestamp(self.t0)
        self.duration = 0

    def __enter__(self):
        self.t0 = time.time()
        return self

    def __exit__(self, etype, exc, tb):
        self.duration += time.time() - self.t0

    def copy(self, operation):
        return self.__class__(operation, self.job_id, self.task)

    def flush(self):
        models.Performance.objects.create(
            oq_job_id=self.job_id,
            task_id=self.task_id,
            task=getattr(self.task, '__name__', None),
            operation=self.operation,
            start_time=self.start_time,
            duration=self.duration)
        self.__init__(self.operation, self.job_id, self.task)
