import time
import mock
import unittest
from openquake.engine.celery_node_monitor import CeleryNodeMonitor


class CeleryNodeMonitorTestCase(unittest.TestCase):
    def setUp(self):
        self.patch = mock.patch('celery.task.control.inspect')
        self.inspect = self.patch.start()

    def test_all_nodes_were_down(self):
        ping = self.inspect().ping
        ping.return_value = {}
        mon = CeleryNodeMonitor(no_distribute=False, interval=1, use_celery=1)
        with self.assertRaises(SystemExit):
            mon.__enter__()
        self.assertEqual(ping.call_count, 1)  # called only once

    def test_all_nodes_are_up(self):
        ping = self.inspect().ping
        ping.return_value = {'node1': []}
        mon = CeleryNodeMonitor(no_distribute=False, interval=1, use_celery=1)
        with mon:
            time.sleep(1.1)
        # one ping was done in the thread, plus one at the beginning
        self.assertEqual(ping.call_count, 2)

    def test_one_node_went_down(self):
        ping = self.inspect().ping
        ping.return_value = {'node1': []}
        mon = CeleryNodeMonitor(no_distribute=False, interval=1, use_celery=1)
        with mon, mock.patch('openquake.engine.logs.LOG') as log:
            time.sleep(1.1)
            ping.return_value = {}
            time.sleep(1)
            # two pings was done in the thread, plus 1 at the beginning
            self.assertEqual(ping.call_count, 3)

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
