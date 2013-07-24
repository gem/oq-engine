import os
import mock
import unittest

from nose.plugins.attrib import attr

import uuid
from datetime import datetime
from openquake.engine.performance import \
    PerformanceMonitor, EnginePerformanceMonitor
from openquake.engine.db.models import Performance
from openquake.engine import engine

flush = EnginePerformanceMonitor.cache.flush


class TestCase(unittest.TestCase):

    def _check_result(self, pmon):
        # check that the attributes start_time, duration and mem are populated
        self.assertGreater(datetime.now(), pmon.start_time)
        self.assertGreaterEqual(pmon.duration, 0)
        self.assertGreaterEqual(pmon.mem[0], 0)

    # the base monitor does not save on the engine db
    @attr('slow')
    def test_performance_monitor(self):
        ls = []
        with PerformanceMonitor([os.getpid()]) as pmon:
            for _ in range(1000 * 1000):
                ls.append(range(50))  # 50 million of integers
        self._check_result(pmon)

    # Skip the following two tests as they always fail on Mac
    @unittest.skip
    def test_engine_performance_monitor(self):
        job = engine.prepare_job()
        mock_task = mock.Mock()
        mock_task.__name__ = 'mock_task'
        mock_task.request.id = task_id = str(uuid.uuid1())
        with EnginePerformanceMonitor(
                'test', job.id, mock_task, profile_pgmem=True) as pmon:
            pass
        self._check_result(pmon)
        # check that one record was stored on the db, as it should
        flush()
        self.assertEqual(len(Performance.objects.filter(task_id=task_id)), 1)

    @unittest.skip
    def test_engine_performance_monitor_no_task(self):
        job = engine.prepare_job()
        operation = str(uuid.uuid1())
        with EnginePerformanceMonitor(
                operation, job.id, profile_pgmem=True) as pmon:
            pass
        self._check_result(pmon)
        flush()
        records = Performance.objects.filter(operation=operation)
        self.assertEqual(len(records), 1)
