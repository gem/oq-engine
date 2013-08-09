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


import getpass
import mock
import unittest

from nose.plugins.attrib import attr

from openquake.engine import engine
from openquake.engine.calculators import base
from openquake.engine.calculators.hazard.disaggregation \
    import core as disagg_core
from openquake.engine.calculators.hazard.classical import core as cls_core
from openquake.engine.db import models

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
        self.job = engine.prepare_job()
        self.calc = disagg_core.DisaggHazardCalculator(self.job)

        # Mock `disagg_task_arg_gen`
        disagg_path = 'openquake.engine.calculators.hazard.disaggregation'
        self.disagg_tag_patch = helpers.patch(
            '%s.core.DisaggHazardCalculator.disagg_task_arg_gen'
            % disagg_path)
        self.disagg_tag_mock = self.disagg_tag_patch.start()
        # fake disagg task arg generator:
        disagg_tag = iter(xrange(3))
        self.disagg_tag_mock.return_value = disagg_tag

        # Mock `haz_general.queue_next`
        base_path = 'openquake.engine.calculators.base'
        self.queue_next_patch = helpers.patch('%s.queue_next' % base_path)
        self.queue_next_mock = self.queue_next_patch.start()

        # Mock `finalize_hazard_curves`
        general_path = 'openquake.engine.calculators.hazard.general'
        self.finalize_curves_patch = helpers.patch(
            '%s.BaseHazardCalculator.finalize_hazard_curves'
            % general_path)
        self.finalize_curves_mock = self.finalize_curves_patch.start()

    def tearDown(self):
        self.disagg_tag_mock.stop()
        self.disagg_tag_patch.stop()

        self.queue_next_mock.stop()
        self.queue_next_patch.stop()

        self.finalize_curves_mock.stop()
        self.finalize_curves_patch.stop()

    def test_task_complete_call_back(self):
        # Test the workflow of the task complete callback.

        block_size = 1
        concurrent_tasks = 2

        # Fake task arg generator:
        hc_tag = iter(xrange(4))

        self.calc.progress['total'] = 7
        self.calc.progress['hc_total'] = 4

        callback = self.calc.get_task_complete_callback(
            hc_tag, block_size=block_size, concurrent_tasks=concurrent_tasks)

        message = self.__class__.FakeMessage()

        # "pre-queue" two hazard curve tasks,
        # and use a fake function
        base.queue_next(lambda x: x, hc_tag.next())
        base.queue_next(lambda x: x, hc_tag.next())
        self.assertEqual(2, self.queue_next_mock.call_count)
        self.calc.progress['in_queue'] = 2

        # message body:
        body = dict(job_id=self.job.id)

        # First call:
        body['num_items'] = 1
        body['calc_type'] = 'hazard_curve'
        callback(body, message)

        self.assertEqual(1, message.acks)
        self.assertFalse(self.calc.disagg_phase)
        self.assertEqual(
            dict(total=7, computed=1, hc_total=4, hc_computed=1, in_queue=2),
            self.calc.progress)
        self.assertEqual(3, self.queue_next_mock.call_count)
        self.assertEqual(0, self.finalize_curves_mock.call_count)

        # Second call:
        callback(body, message)
        self.assertEqual(2, message.acks)
        self.assertFalse(self.calc.disagg_phase)
        self.assertEqual(
            dict(total=7, computed=2, hc_total=4, hc_computed=2, in_queue=2),
            self.calc.progress)
        self.assertEqual(4, self.queue_next_mock.call_count)
        self.assertEqual(0, self.finalize_curves_mock.call_count)

        # Test that an exception is thrown when we receive a non-hazard_curve
        # completion message during the hazard curve phase.
        # This exception case is meant to test for invalid calculator workflow.
        body['calc_type'] = 'disagg'  # could be any fake value as well
        self.assertRaises(RuntimeError, callback, body, message)

        # Third call:
        body['calc_type'] = 'hazard_curve'
        callback(body, message)
        self.assertEqual(3, message.acks)
        self.assertFalse(self.calc.disagg_phase)
        self.assertEqual(
            # There is one hazard curve task left in the queue.
            dict(total=7, computed=3, hc_total=4, hc_computed=3, in_queue=1),
            self.calc.progress)
        self.assertEqual(4, self.queue_next_mock.call_count)

        # Fourth call (the last hazard curve task):
        body['calc_type'] = 'hazard_curve'
        callback(body, message)
        self.assertEqual(4, message.acks)
        # Hazard curves are done, so here we should switch to the disagg phase
        self.assertTrue(self.calc.disagg_phase)
        self.assertEqual(
            dict(total=7, computed=4, hc_total=4, hc_computed=4, in_queue=2),
            self.calc.progress)

        # We should have queued 2 disagg tasks here (given concurrent_tasks=2)
        self.assertEqual(6, self.queue_next_mock.call_count)
        self.assertEqual(1, self.finalize_curves_mock.call_count)

        # Fourth call:
        body['calc_type'] = 'disagg'
        callback(body, message)
        self.assertEqual(5, message.acks)
        self.assertTrue(self.calc.disagg_phase)
        self.assertEqual(
            dict(total=7, computed=5, hc_total=4, hc_computed=4, in_queue=2),
            self.calc.progress)

        self.assertEqual(7, self.queue_next_mock.call_count)
        self.assertEqual(1, self.finalize_curves_mock.call_count)

        # Fifth call:
        callback(body, message)
        self.assertEqual(6, message.acks)
        self.assertTrue(self.calc.disagg_phase)
        self.assertEqual(
            dict(total=7, computed=6, hc_total=4, hc_computed=4, in_queue=1),
            self.calc.progress)

        # Nothing else should be queued; there are no more items to enque.
        self.assertEqual(7, self.queue_next_mock.call_count)
        self.assertEqual(1, self.finalize_curves_mock.call_count)

        # Sixth (final) call:
        # This simulates the message from the last task. The only expected
        # effects here are:
        #   - message ack
        #   - updated 'computed' counter
        callback(body, message)
        self.assertEqual(7, message.acks)
        # Hazard curves computed counter remains at 3
        self.assertEqual(
            dict(total=7, computed=7, hc_total=4, hc_computed=4, in_queue=0),
            self.calc.progress)

        self.assertEqual(1, self.finalize_curves_mock.call_count)


class DisaggHazardCalculatorTestcase(unittest.TestCase):

    def setUp(self):
        self.job, self.calc = self._setup_a_new_calculator()
        models.JobStats.objects.create(
            oq_job=self.job,
            num_sites=0,
            num_tasks=0,
            num_realizations=0
        )

    def _setup_a_new_calculator(self):
        cfg = helpers.get_data_path('disaggregation/job.ini')
        job = helpers.get_hazard_job(cfg, username=getpass.getuser())
        calc = disagg_core.DisaggHazardCalculator(job)
        return job, calc

    def test_pre_execute(self):
        base_path = ('openquake.engine.calculators.hazard.disaggregation.core'
                     '.DisaggHazardCalculator')
        init_src_patch = helpers.patch(
            '%s.%s' % (base_path, 'initialize_sources'))
        init_rlz_patch = helpers.patch(
            '%s.%s' % (base_path, 'initialize_realizations'))
        record_stats_patch = helpers.patch(
            '%s.%s' % (base_path, 'record_init_stats'))
        init_pr_data_patch = helpers.patch(
            '%s.%s' % (base_path, 'initialize_pr_data'))
        patches = (init_src_patch, init_rlz_patch,
                   record_stats_patch, init_pr_data_patch)

        mocks = [p.start() for p in patches]

        self.calc.pre_execute()

        # make sure the site_collection is loaded:
        self.assertIsNotNone(self.calc.hc.site_collection)

        for i, m in enumerate(mocks):
            self.assertEqual(1, m.call_count)
            m.stop()
            patches[i].stop()

    @attr('slow')
    def test_workflow(self):
        # Test `pre_execute` to ensure that all stats are properly initialized.
        # Then test the core disaggregation function.
        self.calc.pre_execute()

        job_stats = models.JobStats.objects.get(oq_job=self.job.id)
        self.assertEqual(2, job_stats.num_realizations)
        self.assertEqual(2, job_stats.num_sites)
        self.assertEqual(12, job_stats.num_tasks)

        self.assertEqual(
            {'hc_computed': 0, 'total': 12, 'hc_total': 8, 'computed': 0,
             'in_queue': 0},
            self.calc.progress
        )

        # To test the disagg function, we first need to compute the hazard
        # curves:
        for args in self.calc.task_arg_gen(1):
            # drop the calc_type from the args:
            cls_core.compute_hazard_curves(*args[0:-1])
        self.calc.finalize_hazard_curves()

        diss1, diss2, diss3, diss4 = list(self.calc.disagg_task_arg_gen(1))

        base_path = 'openquake.engine.calculators.hazard.disaggregation.core'

        disagg_calc_func = (
            'openquake.hazardlib.calc.disagg.disaggregation_poissonian'
        )
        with mock.patch(disagg_calc_func) as disagg_mock:
            disagg_mock.return_value = (None, None)
            with mock.patch('%s.%s' % (base_path, '_save_disagg_matrix')
                            ) as save_mock:
                # Some of these tasks will not compute anything, since the
                # hazard  curves for these few are all 0.0s.

                # Here's what we expect:
                # diss1: compute
                # diss2: skip
                # diss3: compute
                # diss4: skip

                disagg_core.compute_disagg(*diss1[0:-1])
                # 2 poes * 2 imts * 1 site = 4
                self.assertEqual(4, disagg_mock.call_count)
                self.assertEqual(0, save_mock.call_count)  # no rupt generated

                disagg_core.compute_disagg(*diss2[0:-1])
                self.assertEqual(4, disagg_mock.call_count)
                self.assertEqual(0, save_mock.call_count)  # no rupt generated

                disagg_core.compute_disagg(*diss3[0:-1])
                self.assertEqual(8, disagg_mock.call_count)
                self.assertEqual(0, save_mock.call_count)  # no rupt generated

                disagg_core.compute_disagg(*diss4[0:-1])
                self.assertEqual(8, disagg_mock.call_count)
                self.assertEqual(0, save_mock.call_count)  # no rupt generated

        # Finally, test that realization data is up to date and correct:
        rlzs = models.LtRealization.objects.filter(
            hazard_calculation=self.calc.hc)

        for rlz in rlzs:
            self.assertEqual(6, rlz.total_items)
            self.assertEqual(6, rlz.completed_items)
            self.assertTrue(rlz.is_complete)
