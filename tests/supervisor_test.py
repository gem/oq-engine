# -*- coding: utf-8 -*-

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import logging
import unittest

from datetime import datetime

from openquake.engine import engine
from openquake.engine.db.models import JobStats
from openquake.engine.supervising import supervisor
from openquake.engine.utils import stats

from tests.utils.helpers import cleanup_loggers
from tests.utils.helpers import get_data_path
from tests.utils.helpers import get_hazard_job
from tests.utils.helpers import patch


class SupervisorHelpersTestCase(unittest.TestCase):

    def setUp(self):
        self.job = engine.prepare_job()

    def test_record_job_stop_time(self):
        """
        Test that job stop time is recorded properly.
        """
        cstats = JobStats(
            oq_job=self.job, start_time=datetime.utcnow(),
            num_sites=10)
        cstats.save(using='job_superv')

        supervisor.record_job_stop_time(self.job.id)

        # Fetch the stats and check for the stop_time
        cstats = JobStats.objects.get(oq_job=self.job.id)
        self.assertTrue(cstats.stop_time is not None)

    def test_cleanup_after_job(self):
        with patch('openquake.engine.kvs.cache_gc') as cache_gc:
            with patch('openquake.engine.supervising.supervisor.'
                       '_get_task_ids') as gti:
                with patch('celery.task.control.revoke') as revoke:
                    gti.return_value = ['task-id-1', 'task-id-2']

                    supervisor.cleanup_after_job(self.job.id)

                    self.assertEqual(1, cache_gc.call_count)
                    self.assertEqual(((self.job.id, ), {}), cache_gc.call_args)

                    self.assertEqual(1, gti.call_count)
                    self.assertEqual(((self.job.id, ), {}), gti.call_args)

                    self.assertEqual(2, revoke.call_count)
                    exp_revoke_args = [(('task-id-1',), {'terminate': True}),
                                       (('task-id-2',), {'terminate': True})]
                    self.assertEqual(exp_revoke_args, revoke.call_args_list)

    def test_update_job_status(self):
        supervisor.update_job_status(self.job.id)


class SupervisorTestCase(unittest.TestCase):
    def setUp(self):
        # Patch a few methods here and restore them in the tearDown to avoid
        # too many nested with
        # See http://www.voidspace.org.uk/python/mock/patch.html \
        #     #patch-methods-start-and-stop
        self.patchers = []

        def start_patch(attr_path):
            _, attr = attr_path.rsplit('.', 1)
            patcher = patch(attr_path)
            self.patchers.append(patcher)
            setattr(self, attr, patcher.start())

        start_patch('openquake.engine.supervising.is_pid_running')

        # Patch the actions taken by the supervisor
        start_patch('openquake.engine.supervising.supervisor.\
record_job_stop_time')
        start_patch(
            'openquake.engine.supervising.supervisor.cleanup_after_job')
        start_patch('openquake.engine.supervising.supervisor.terminate_job')
        start_patch('openquake.engine.supervising.supervisor.get_job_status')
        start_patch('openquake.engine.supervising.supervisor'
                    '.update_job_status')

        logging.root.setLevel(logging.CRITICAL)

        cfg = get_data_path('end-to-end-hazard-risk/job_haz_classical.ini')
        self.job = get_hazard_job(cfg)

    def tearDown(self):
        # Stop all the started patches
        for patcher in self.patchers:
            patcher.stop()
        cleanup_loggers()

    def test_actions_after_a_critical_message(self):
        # the job process is running
        self.is_pid_running.return_value = True

        with patch('openquake.engine.supervising.'
                   'supervisor.SupervisorLogMessageConsumer.run') as run:

            def run_(mc):
                record = logging.LogRecord(
                    'oq.job.%s' % self.job.id,
                    logging.CRITICAL,
                    'path',
                    42,
                    'a msg',
                    (),
                    None)
                mc.log_callback(record)
                assert mc._stopped

            # the supervisor will receive a msg
            run.side_effect = run_

            supervisor.supervise(1, self.job.id, timeout=0.1)

            # the job process is terminated
            self.assertEqual(1, self.terminate_job.call_count)
            self.assertEqual(((1,), {}), self.terminate_job.call_args)

            # stop time is recorded
            self.assertEqual(1, self.record_job_stop_time.call_count)
            self.assertEqual(
                ((self.job.id,), {}),
                self.record_job_stop_time.call_args)

            # the cleanup is triggered
            self.assertEqual(1, self.cleanup_after_job.call_count)
            self.assertEqual(
                ((self.job.id,), {}),
                self.cleanup_after_job.call_args)

            # the status in the job record is updated
            self.assertEqual(
                1,
                self.update_job_status.call_count)
            self.assertEqual(
                ((self.job.id,), {}),
                self.update_job_status.call_args)

    def test_actions_after_job_process_termination(self):
        # the job process is *not* running
        self.is_pid_running.return_value = False
        self.get_job_status.return_value = 'succeeded'

        supervisor.supervise(1, self.job.id, timeout=0.1)

        # stop time is recorded
        self.assertEqual(1, self.record_job_stop_time.call_count)
        self.assertEqual(
            ((self.job.id,), {}),
            self.record_job_stop_time.call_args)

        # the cleanup is triggered
        self.assertEqual(1, self.cleanup_after_job.call_count)
        self.assertEqual(
            ((self.job.id,), {}),
            self.cleanup_after_job.call_args)

    def test_actions_after_job_process_failures(self):
        # the job process is running but has some failure counters above zero
        # shorten the delay to checking failure counters
        supervisor.SupervisorLogMessageConsumer.FCC_DELAY = 2
        self.is_pid_running.return_value = True
        self.get_job_status.return_value = 'running'

        stats.delete_job_counters(self.job.id)
        stats.incr_counter(self.job.id, "h", "a:failed")
        stats.incr_counter(self.job.id, "r", "b:failed")
        stats.incr_counter(self.job.id, "r", "b:failed")
        supervisor.supervise(1, self.job.id, timeout=0.1)

        # the job process is terminated
        self.assertEqual(1, self.terminate_job.call_count)
        self.assertEqual(((1,), {}), self.terminate_job.call_args)

        # stop time is recorded
        self.assertEqual(1, self.record_job_stop_time.call_count)
        self.assertEqual(
            ((self.job.id,), {}),
            self.record_job_stop_time.call_args)

        # the cleanup is triggered
        self.assertEqual(1, self.cleanup_after_job.call_count)
        self.assertEqual(
            ((self.job.id,), {}),
            self.cleanup_after_job.call_args)

    def test_actions_after_job_process_crash(self):
        # the job process is *not* running
        self.is_pid_running.return_value = False
        # but the database record says it is
        self.get_job_status.return_value = 'running'

        supervisor.supervise(1, self.job.id, timeout=0.1)

        # stop time is recorded
        self.assertEqual(1, self.record_job_stop_time.call_count)
        self.assertEqual(
            ((self.job.id,), {}),
            self.record_job_stop_time.call_args)

        # the cleanup is triggered
        self.assertEqual(1, self.cleanup_after_job.call_count)
        self.assertEqual(
            ((self.job.id,), {}),
            self.cleanup_after_job.call_args)

        # the status in the job record is updated
        self.assertEqual(1, self.update_job_status.call_count)
        self.assertEqual(
            ((self.job.id,), {}),
            self.update_job_status.call_args)


class AbortDueToFailedNodesTestCase(unittest.TestCase):
    """Exercise supervising.supervisor.abort_due_to_failed_nodes()"""

    job = monitor_patch = stats_patch = monitor_mock = stats_mock = None

    @classmethod
    def setUpClass(cls):
        cls.job = engine.prepare_job()

    def setUp(self):
        self.monitor_patch = patch(
            "openquake.engine.utils.monitor.count_failed_nodes")
        self.stats_patch = patch(
            "openquake.engine.utils.stats.get_progress_timing_data")
        self.monitor_mock = self.monitor_patch.start()
        self.stats_mock = self.stats_patch.start()

    def tearDown(self):
        self.monitor_patch.stop()
        self.stats_patch.stop()

    def test_abort_due_to_failed_nodes_with_zero_failures_and_no_timeout(self):
        # the "no progress" timeout has not been exceeded and no node failures
        # have been detected -> return 0
        self.monitor_mock.return_value = 0
        self.stats_mock.return_value = (361, 3600)
        self.assertEqual(0, supervisor.abort_due_to_failed_nodes(self.job.id))

    def test_abort_due_to_failed_nodes_with_zero_failures_and_timeout(self):
        # the "no progress" timeout is exceeded but no node failures have been
        # detected -> return 0
        self.monitor_mock.return_value = 0
        self.stats_mock.return_value = (3610, 3600)
        self.assertEqual(0, supervisor.abort_due_to_failed_nodes(self.job.id))

    def test_abort_due_to_failed_nodes_with_failures_and_no_timeout(self):
        # the "no progress" timeout has not been exceeded but there are node
        # failures  -> return 0
        self.monitor_mock.return_value = 5
        self.stats_mock.return_value = (362, 3600)
        self.assertEqual(0, supervisor.abort_due_to_failed_nodes(self.job.id))

    def test_abort_due_to_failed_nodes_with_failures_and_timeout(self):
        # the "no progress" timeout has been exceeded *and* there are node
        # failures -> (return value > 0)
        self.monitor_mock.return_value = 7
        self.stats_mock.return_value = (4000, 3600)
        self.assertEqual(7, supervisor.abort_due_to_failed_nodes(self.job.id))
