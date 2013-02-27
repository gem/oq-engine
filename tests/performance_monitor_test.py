import os
import mock
import unittest
import uuid
from datetime import datetime
from openquake.engine.performance import \
    PerformanceMonitor, EnginePerformanceMonitor
from openquake.engine.db.models import Performance
from openquake.engine import engine


class TestCase(unittest.TestCase):

    def check_result(self, pmon, nproc):
        # check that the attributes start_time, duration and mem_peaks
        # are populated
        self.assert_(pmon.start_time < datetime.now())
        self.assert_(pmon.duration > 0)
        self.assert_(pmon.mem_peaks[0] > 0)
        self.assertEqual(len(pmon.mem_peaks), nproc)

    def testPerformanceMonitor(self):
        ls = []
        with PerformanceMonitor([os.getpid()]) as pmon:
            for i in range(1000 * 1000):
                ls.append(range(50))  # 50 million of integers
        self.check_result(pmon, nproc=1)

    def testEnginePerformanceMonitor(self):
        job = engine.prepare_job()
        mock_task = mock.Mock()
        mock_task.__name__ = 'mock_task'
        mock_task.request.id = task_id = uuid.uuid1()
        with EnginePerformanceMonitor('test', job.id, mock_task) as pmon:
            pass
        self.check_result(pmon, nproc=2)
        # check that one record was stored on the db, as it should
        self.assertEqual(len(Performance.objects.filter(task_id=task_id)), 1)

    def testEnginePerformanceMonitorNoTask(self):
        job = engine.prepare_job()
        operation = uuid.uuid1()
        with EnginePerformanceMonitor(operation, job.id) as pmon:
            pass
        self.check_result(pmon, nproc=2)
        records = Performance.objects.filter(operation=operation)
        self.assertEqual(len(records), 1)
