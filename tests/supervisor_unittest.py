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

from tests.utils.helpers import patch, job_from_file, get_data_path
from openquake.db.models import OqJob

from openquake.supervising import supervisor
from openquake.supervising import supersupervisor


CONFIG_FILE = "config.gem"


class SupervisorTestCase(unittest.TestCase):
    def setUp(self):
        # Patch a few methods here and restore them in the tearDown to avoid
        # too many nested with
        # See http://www.voidspace.org.uk/python/mock/patch.html \
        #     #patch-methods-start-and-stop
        self.patchers = []

        def patch_(attr_path):
            _, attr = attr_path.rsplit('.', 1)
            patcher = patch(attr_path)
            self.patchers.append(patcher)
            setattr(self, attr, patcher.start())

        patch_('openquake.supervising.is_pid_running')

        # patch the actions taken by the supervisor
        patch_('openquake.supervising.supervisor.cleanup_after_job')
        patch_('openquake.supervising.supervisor.terminate_job')

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def test_a_critical_message_terminates_the_job(self):
        # the job process is running
        self.is_pid_running.return_value = True

        with patch('openquake.supervising.' \
                   'supervisor.SupervisorLogMessageConsumer.run') as run:

            def run_(mc):
                while True:
                    try:
                        mc.message_callback('a msg')
                    except StopIteration:
                        break

            # the supervisor will receive a msg
            run.side_effect = run_

            supervisor.supervise(1000, 1)

            self.assertEqual(1, self.terminate_job.call_count)
            self.assertEqual(((1000,), {}), self.terminate_job.call_args)

    def test_a_critical_message_triggers_cleanup(self):
        # the job process is running
        self.is_pid_running.return_value = True

        with patch('openquake.supervising.' \
                   'supervisor.SupervisorLogMessageConsumer.run') as run:

            def run_(mc):
                while True:
                    try:
                        mc.message_callback('a msg')
                    except StopIteration:
                        break

            # the supervisor will receive a msg
            run.side_effect = run_

            supervisor.supervise(1000, 1)

            self.assertEqual(1, self.cleanup_after_job.call_count)
            self.assertEqual(((1,), {}), self.cleanup_after_job.call_args)

    def test_job_process_termination_triggers_cleanup(self):
        # the job process is *not* running
        self.is_pid_running.return_value = False

        supervisor.supervise(1000, 1)

        self.assertEqual(1, self.cleanup_after_job.call_count)
        self.assertEqual(((1,), {}), self.cleanup_after_job.call_args)


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
