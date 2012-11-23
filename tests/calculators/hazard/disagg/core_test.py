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


import mock
import unittest

from openquake import engine2
from openquake.calculators.hazard.disagg import core as disagg_core
from openquake.calculators.hazard import general as haz_general

from tests.utils import helpers


class TaskCompleteCallbackTest(unittest.TestCase):
    """
    Tests for the callback which is called to respond to task completion in the
    disaggregation calculator.
    """
    class FakeMessage(object):
        """
        Fake AMQP message, to test message acking.
        """

        def __init__(self):
            self.acks = 0

        def ack(self):
            self.acks += 1


    def setUp(self):
        self.job = engine2.prepare_job()
        self.calc = disagg_core.DisaggHazardCalculator(self.job)

        # Mock `disagg_task_arg_gen`
        disagg_path = 'openquake.calculators.hazard.disagg'
        self.disagg_tag_patch = helpers.patch(
            '%s.core.DisaggHazardCalculator.disagg_task_arg_gen'
            % disagg_path)
        self.disagg_tag_mock = self.disagg_tag_patch.start()
        # fake disagg task arg generator:
        disagg_tag = iter(xrange(3))
        self.disagg_tag_mock.return_value = disagg_tag

        # Mock `haz_general.queue_next`
        general_path = 'openquake.calculators.hazard.general'
        self.queue_next_patch = helpers.patch('%s.queue_next' % general_path)
        self.queue_next_mock = self.queue_next_patch.start()

    def tearDown(self):
        self.disagg_tag_mock.stop()
        self.disagg_tag_patch.stop()

        self.queue_next_mock.stop()
        self.queue_next_patch.stop()

    def test_task_complete_call_back(self):
        # Test the workflow of the task complete callback.

        # Fake task arg generator:
        hc_tag = iter(xrange(3))

        self.calc.progress['total'] = 6
        self.calc.progress['hc_total'] = 3

        callback = self.calc.get_task_complete_callback(
            hc_tag, block_size=1, concurrent_tasks=2)

        message = self.__class__.FakeMessage()

        # "pre-queue" a single hazard curve task
        # use a fake function
        haz_general.queue_next(lambda x: x, hc_tag.next())
        self.assertEqual(1, self.queue_next_mock.call_count)

        # message body:
        body = dict(job_id=self.job.id)

        # First call:
        body['num_items'] = 1
        body['calc_type'] = 'hazard_curve'
        callback(body, message)

        self.assertEqual(1, message.acks)
        self.assertFalse(self.calc.disagg_phase)
        self.assertEqual(1, self.calc.progress['computed'])
        self.assertEqual(1, self.calc.progress['hc_computed'])
        self.assertEqual(2, self.queue_next_mock.call_count)

        # Second call:
        callback(body, message)
        self.assertEqual(2, message.acks)
        self.assertFalse(self.calc.disagg_phase)
        self.assertEqual(2, self.calc.progress['computed'])
        self.assertEqual(2, self.calc.progress['hc_computed'])
        self.assertEqual(3, self.queue_next_mock.call_count)

        # Test that an exception is thrown when we receive a non-hazard_curve
        # completion message during the hazard curve phase.
        # This exception case is meant to test for invalid calculator workflow.
        body['calc_type'] = 'disagg'  # could be any fake value as well
        self.assertRaises(RuntimeError, callback, body, message)

        # Third call:
        body['calc_type'] = 'hazard_curve'
        callback(body, message)
        self.assertEqual(3, message.acks)
        # Hazard curves are done, so here we should switch to the disagg phase
        self.assertTrue(self.calc.disagg_phase)
        self.assertEqual(3, self.calc.progress['computed'])
        self.assertEqual(3, self.calc.progress['hc_computed'])
        # We should have queued 2 disagg tasks here (given concurrent_tasks=2)
        self.assertEqual(5, self.queue_next_mock.call_count)

        # Fourth call:
        body['calc_type'] = 'disagg'
        callback(body, message)
        self.assertEqual(4, message.acks)
        self.assertTrue(self.calc.disagg_phase)
        self.assertEqual(4, self.calc.progress['computed'])
        self.assertEqual(3, self.calc.progress['hc_computed'])
        self.assertEqual(6, self.queue_next_mock.call_count)

        # Fifth call:
        callback(body, message)
        self.assertEqual(5, message.acks)
        self.assertTrue(self.calc.disagg_phase)
        self.assertEqual(5, self.calc.progress['computed'])
        self.assertEqual(3, self.calc.progress['hc_computed'])
        # Nothing else should be queued; there are no more items to enque.
        self.assertEqual(6, self.queue_next_mock.call_count)

        # Sixth (final) call:
        # This simulates the message from the last task. The only expected
        # effects here are:
        #   - message ack
        #   - updated 'computed' counter
        callback(body, message)
        self.assertEqual(6, message.acks)
        self.assertEqual(6, self.calc.progress['computed'])
        # Hazard curves computed counter remains at 3
        self.assertEqual(3, self.calc.progress['hc_computed'])
