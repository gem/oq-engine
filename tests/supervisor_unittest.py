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

from tests.utils.helpers import patch

from openquake import supervisor

class SupervisorTestCase(unittest.TestCase):
    def setUp(self):
        self.patchers = []

        def patch_(attr_path):
            _, attr = attr_path.rsplit('.', 1)
            patcher = patch(attr_path)
            self.patchers.append(patcher)
            setattr(self, attr, patcher.start())

        patch_('openquake.supervisor.is_pid_running')

        # patch the actions taken by the supervisor
        patch_('openquake.supervisor.cleanup_after_job')
        patch_('openquake.supervisor.terminate_job')

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def test_a_critical_message_terminates_the_job(self):
        # the job process is running
        self.is_pid_running.return_value = True

        with patch('openquake.supervisor.SupervisorLogMessageConsumer.run')\
             as run:
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

        with patch('openquake.supervisor.SupervisorLogMessageConsumer.run')\
             as run:
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
