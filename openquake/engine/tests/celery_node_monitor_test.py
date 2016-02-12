# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import time
import mock
import unittest
from openquake.engine.celery_node_monitor import CeleryNodeMonitor


class CeleryNodeMonitorTestCase(unittest.TestCase):
    def setUp(self):
        self.patch = mock.patch('celery.task.control.inspect')
        self.inspect = self.patch.start()

    def test_all_nodes_were_down(self):
        stats = self.inspect().stats
        stats.return_value = {}
        mon = CeleryNodeMonitor(no_distribute=False, interval=1, use_celery=1)
        with self.assertRaises(SystemExit):
            mon.__enter__()
        self.assertEqual(stats.call_count, 1)  # called only once

    def test_all_nodes_are_up(self):
        stats = self.inspect().stats
        ping = self.inspect().ping
        stats.return_value = {'node1': {'pool': {'max-concurrency': 32}}}
        mon = CeleryNodeMonitor(no_distribute=False, interval=1, use_celery=1)
        with mon:
            time.sleep(1.1)
        # one ping was done in the thread
        self.assertEqual(ping.call_count, 1)

    def test_one_node_went_down(self):
        stats = self.inspect().stats
        ping = self.inspect().ping
        stats.return_value = {'node1': {'pool': {'max-concurrency': 32}}}
        ping.return_value = {'node1': []}
        mon = CeleryNodeMonitor(no_distribute=False, interval=1, use_celery=1)
        with mon, mock.patch('openquake.engine.logs.LOG') as log:
            time.sleep(1.1)
            ping.return_value = {}
            time.sleep(1)
            # two pings were done in the thread
            self.assertEqual(ping.call_count, 2)

            # check that LOG.warn was called
            self.assertTrue(log.warn.called)

    def test_AMQPException(self):
        ping = self.inspect().ping
        ping.side_effect = Exception(0, 'fake error', '')
        mon = CeleryNodeMonitor(no_distribute=False, interval=1, use_celery=1)
        with mock.patch('openquake.engine.logs.LOG') as log:
            mon.ping(timeout=0.1)
            self.assertTrue(log.warn.called)

    def test_no_distribute(self):
        with CeleryNodeMonitor(no_distribute=True, interval=0.1, use_celery=1):
            time.sleep(0.5)
        self.assertIsNone(self.inspect.call_args)

    def tearDown(self):
        self.patch.stop()
