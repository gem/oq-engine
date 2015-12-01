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

    def __init__(self, operation, job_id=None, task=None, tracing=False,
                 measuremem=True, autoflush=False):
        super(EnginePerformanceMonitor, self).__init__(
            operation, autoflush=autoflush, measuremem=measuremem)
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
        """Save a row in the performance table for each child"""
        monitors = [self] + self.children
        for mon in monitors:
            if mon.duration:  # the monitor has been used
                models.Performance.objects.create(
                    oq_job_id=mon.job_id,
                    task_id=mon.task_id,
                    task=getattr(mon.task, '__name__', None),
                    operation=mon.operation,
                    start_time=mon.start_time,
                    duration=mon.duration,
                    pymemory=mon.mem if mon.measuremem else None,
                    pgmemory=None)
            mon.mem = 0
            mon.duration = 0

    def collect_performance(self):
        """For compatibility with oq-lite"""
