import os

from openquake.baselib.performance import PerformanceMonitor
from openquake.engine import logs
from openquake.engine.db import models


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

    @classmethod
    def monitor(cls, method):
        """
        A decorator to add monitoring to calculator methods. The only
        constraints are:
        1) the method has no keyword arguments
        2) there is an attribute self.job.id
        """
        def newmeth(self, *args):
            with cls(method.__name__, self.job.id, autoflush=True):
                return method(self, *args)
        newmeth.__name__ = method.__name__
        return newmeth

    def __init__(self, operation, job_id, task=None, tracing=False,
                 measuremem=True, autoflush=False):
        self.measuremem = measuremem
        pid = os.getpid() if measuremem else None
        super(EnginePerformanceMonitor, self).__init__(
            operation, pid, autoflush=autoflush)
        self.job_id = job_id
        if task:
            self.task = task
        else:
            self.task = None
        self.tracing = tracing
        if tracing:
            self.tracer = logs.tracing(operation)

    @property
    def task_id(self):
        """Return the celery task ID or None"""
        return None if self.task is None else self.task.request.id

    def __call__(self, operation, task=None, **kw):
        """
        Return a copy of the monitor usable for a different operation
        in the same task.
        """
        new = self.__class__(operation, self.job_id, task or self.task,
                             self.tracing, self.measuremem, self.autoflush)
        vars(new).update(kw)
        return new

    def __enter__(self):
        # start measuring time and memory
        super(EnginePerformanceMonitor, self).__enter__()
        if self.tracing:
            self.tracer.__enter__()
        return self

    def __exit__(self, etype, exc, tb):
        # measuring time and memory
        super(EnginePerformanceMonitor, self).__exit__(etype, exc, tb)
        if self.tracing:
            self.tracer.__exit__(etype, exc, tb)

    def on_exit(self):
        """
        Save the memory consumption on the uiapi.performance table.
        """
        if self.autoflush and self.exc is None:  # save only valid measures
            self.flush()

    def flush(self):
        """Save a row in the performance table"""
        models.Performance.objects.create(
            oq_job_id=self.job_id,
            task_id=self.task_id,
            task=getattr(self.task, '__name__', None),
            operation=self.operation,
            start_time=self.start_time,
            duration=self.duration,
            pymemory=self.mem if self.measuremem else None,
            pgmemory=None)
        self.mem = 0
        self.duration = 0

    def collect_performance(self):
        """For compatibility with oq-lite"""
