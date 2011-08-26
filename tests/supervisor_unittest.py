# -*- coding: utf-8 -*-

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

import unittest

from amqplib import client_0_8 as amqp

from tests.utils.helpers import patch, job_from_file, get_data_path
from tests.utils.helpers import DbTestMixin
from openquake.db.models import OqJob, ErrorMsg

from openquake.supervising import supervisor
from openquake.supervising import supersupervisor


CONFIG_FILE = "config.gem"

class SupervisorHelpersTestCase(DbTestMixin, unittest.TestCase):
    def setUp(self):
        self.job = self.setup_classic_job(create_job_path=False)

    def tearDown(self):
        if self.job:
            ErrorMsg.objects.using('job_superv')\
                            .filter(oq_job=self.job.id).delete()
            self.teardown_job(self.job, filesystem_only=True)

    def test_cleanup_after_job(self):
        with patch('openquake.kvs.cache_gc') as cache_gc:
            supervisor.cleanup_after_job(123)

            self.assertEqual(1, cache_gc.call_count)
            self.assertEqual(((123, ), {}), cache_gc.call_args)

    def test_update_job_status_and_error_msg(self):
        status = 'succeeded'
        error_msg = 'a test message'
        supervisor.update_job_status_and_error_msg(self.job.id, status,
                                                   error_msg)

        self.assertEqual(status, supervisor.get_job_status(self.job.id))
        self.assertEqual(error_msg,
                         ErrorMsg.objects.get(oq_job=self.job.id).detailed)


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

        start_patch('openquake.supervising.is_pid_running')

        # Patch the actions taken by the supervisor
        start_patch('openquake.supervising.supervisor.cleanup_after_job')
        start_patch('openquake.supervising.supervisor.terminate_job')
        start_patch('openquake.supervising.supervisor.get_job_status')
        start_patch('openquake.supervising.supervisor'
               '.update_job_status_and_error_msg')
        start_patch('openquake.signalling.signal_job_outcome')

    def tearDown(self):
        # Stop all the started patches
        for patcher in self.patchers:
            patcher.stop()

    def test_actions_after_a_critical_message(self):
        # the job process is running
        self.is_pid_running.return_value = True

        with patch('openquake.supervising.' \
                   'supervisor.SupervisorLogMessageConsumer.run') as run:

            def run_(mc):
                while True:
                    try:
                        mc.message_callback(amqp.Message(body='a msg'))
                    except StopIteration:
                        break

            # the supervisor will receive a msg
            run.side_effect = run_

            supervisor.supervise(1, 123)

            # the job process is terminated
            self.assertEqual(1, self.terminate_job.call_count)
            self.assertEqual(((1,), {}), self.terminate_job.call_args)

            # the cleanup is triggered
            self.assertEqual(1, self.cleanup_after_job.call_count)
            self.assertEqual(((123,), {}), self.cleanup_after_job.call_args)

            # the outcome is signalled
            self.assertEqual(1, self.signal_job_outcome.call_count)
            self.assertEqual(((123, 'failed'), {}),
                             self.signal_job_outcome.call_args)

            # the status in the job record is updated
            self.assertEqual(1,
                             self.update_job_status_and_error_msg.call_count)
            self.assertEqual(((123, 'failed', 'a msg'), {}),
                             self.update_job_status_and_error_msg.call_args)


    def test_actions_after_job_process_termination(self):
        # the job process is *not* running
        self.is_pid_running.return_value = False
        self.get_job_status.return_value = 'succeeded'

        supervisor.supervise(1, 123)

        # the cleanup is triggered
        self.assertEqual(1, self.cleanup_after_job.call_count)
        self.assertEqual(((123,), {}), self.cleanup_after_job.call_args)

        # the outcome is signalled
        self.assertEqual(1, self.signal_job_outcome.call_count)
        self.assertEqual(((123, 'succeeded'), {}),
                            self.signal_job_outcome.call_args)


    def test_actions_after_job_process_crash(self):
        # the job process is *not* running
        self.is_pid_running.return_value = False
        # but the database record says it is
        self.get_job_status.return_value = 'running'

        supervisor.supervise(1, 123)

        # the cleanup is triggered
        self.assertEqual(1, self.cleanup_after_job.call_count)
        self.assertEqual(((123,), {}), self.cleanup_after_job.call_args)

        # the outcome is signalled
        self.assertEqual(1, self.signal_job_outcome.call_count)
        self.assertEqual(((123, 'failed'), {}),
                            self.signal_job_outcome.call_args)

        # the status in the job record is updated
        self.assertEqual(1,
                            self.update_job_status_and_error_msg.call_count)
        self.assertEqual(((123, 'failed', 'crash'), {}),
                            self.update_job_status_and_error_msg.call_args)


class SupersupervisorTestCase(unittest.TestCase):
    def setUp(self):
        self.running_pid = 1324
        self.stopped_pid = 4312
        OqJob.objects.all().update(status='succeeded')
        job_pid = 1
        for status in ('pending', 'running', 'failed', 'succeeded'):
            for supervisor_pid in (self.running_pid, self.stopped_pid):
                job = job_from_file(get_data_path(CONFIG_FILE))
                job = OqJob.objects.get(id=job.job_id)
                job.status = status
                job.supervisor_pid = supervisor_pid
                job.job_pid = job_pid
                job_pid += 1
                job.save()
                if status == 'running' and supervisor_pid == self.stopped_pid:
                    self.dead_supervisor_job_id = job.id
                    self.dead_supervisor_job_pid = job.job_pid
        self.is_pid_running = patch('openquake.supervising.is_pid_running')
        self.is_pid_running = self.is_pid_running.start()
        self.is_pid_running.side_effect = lambda pid: pid != self.stopped_pid

    def tearDown(self):
        self.is_pid_running.stop()

    def test_main(self):
        with patch('openquake.job.spawn_job_supervisor') as spawn:
            supersupervisor.main()
            self.assertEqual(spawn.call_count, 1)
            args = (self.dead_supervisor_job_id, self.dead_supervisor_job_pid)
            self.assertEqual(spawn.call_args, (args, {}))
