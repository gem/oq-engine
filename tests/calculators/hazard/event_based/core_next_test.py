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
import unittest

import kombu

from nose.plugins.attrib import attr

from openquake.db import models
from openquake.calculators.hazard.event_based import core_next
from openquake.calculators.hazard import general as haz_general
from openquake.utils import stats

from tests.utils import helpers


class EventBasedHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the core functionality of the event-based hazard calculator.
    """

    def setUp(self):
        cfg = helpers.get_data_path('event_based_hazard/job.ini')
        self.job = helpers.get_hazard_job(cfg, username=getpass.getuser())
        self.calc = core_next.EventBasedHazardCalculator(self.job)

    def test_initialize_ses_db_records(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_ses_db_records])

        outputs = models.Output.objects.filter(
            oq_job=self.job, output_type='ses')
        self.assertEqual(2, len(outputs))

        # With this job configuration, we have 2 logic tree realizations.
        lt_rlzs = models.LtRealization.objects.filter(hazard_calculation=hc)
        self.assertEqual(2, len(lt_rlzs))

        for rlz in lt_rlzs:
            sess = models.SES.objects.filter(
                ses_collection__lt_realization=rlz)
            self.assertEqual(hc.ses_per_logic_tree_path, len(sess))

            for ses in sess:
                # The only metadata in in the SES is investigation time.
                self.assertEqual(hc.investigation_time, ses.investigation_time)

    def test_initialize_pr_data_with_ses(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_ses_db_records])

        ltr1, ltr2 = models.LtRealization.objects.filter(
            hazard_calculation=hc).order_by("id")

        ltr1.completed_sources = 12
        ltr1.save()

        self.calc.initialize_pr_data()

        total = stats.pk_get(self.calc.job.id, "nhzrd_total")
        self.assertEqual(ltr1.total_sources + ltr2.total_sources, total)
        done = stats.pk_get(self.calc.job.id, "nhzrd_done")
        self.assertEqual(ltr1.completed_sources + ltr2.completed_sources, done)

    def test_initialize_gmf_db_records(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_gmf_db_records])

        outputs = models.Output.objects.filter(
            oq_job=self.job, output_type='gmf')
        self.assertEqual(2, len(outputs))

        lt_rlzs = models.LtRealization.objects.filter(hazard_calculation=hc)
        self.assertEqual(2, len(lt_rlzs))

        for rlz in lt_rlzs:
            gmf_sets = models.GmfSet.objects.filter(
                gmf_collection__lt_realization=rlz)
            self.assertEqual(hc.ses_per_logic_tree_path, len(gmf_sets))

            for gmf_set in gmf_sets:
                # The only metadata in a GmfSet is investigation time.
                self.assertEqual(
                    hc.investigation_time, gmf_set.investigation_time)

    def test_initialize_pr_data_with_gmf(self):
        hc = self.job.hazard_calculation

        # Initialize sources as a setup for the test:
        self.calc.initialize_sources()

        self.calc.initialize_realizations(
            rlz_callbacks=[self.calc.initialize_gmf_db_records])

        ltr1, ltr2 = models.LtRealization.objects.filter(
            hazard_calculation=hc).order_by("id")

        ltr1.completed_sources = 13
        ltr1.save()

        self.calc.initialize_pr_data()

        total = stats.pk_get(self.calc.job.id, "nhzrd_total")
        self.assertEqual(ltr1.total_sources + ltr2.total_sources, total)
        done = stats.pk_get(self.calc.job.id, "nhzrd_done")
        self.assertEqual(ltr1.completed_sources + ltr2.completed_sources, done)

    def test_initialize_complete_lt_ses_db_records_branch_enum(self):
        # Set hazard_calculation.number_of_logic_tree_samples = 0
        # This indicates that the `end-branch enumeration` method should be
        # used to carry out the calculation.

        # This test was added primarily for branch coverage (in the case of end
        # branch enum) for the method `initialize_complete_lt_ses_db_records`.
        hc = self.job.hazard_calculation
        hc.number_of_logic_tree_samples = 0

        self.calc.initialize_sources()
        self.calc.initialize_realizations()

        self.calc.initialize_complete_lt_ses_db_records()

        complete_lt_ses = models.SES.objects.get(
            ses_collection__output__oq_job=self.job.id,
            ses_collection__output__output_type='complete_lt_ses',
            complete_logic_tree_ses=True)

        self.assertEqual(250.0, complete_lt_ses.investigation_time)
        self.assertIsNone(complete_lt_ses.ordinal)

    # TODO(LB): This test is becoming a bit epic. Once QA test data is
    # we can probably refactor or replace this test.
    @attr('slow')
    def test_complete_event_based_calculation_cycle(self):
        # * Run `pre_execute()`.
        # * Execute the the `stochastic_event_sets` task as a normal function.
        # * Check that the proper results (GMF, SES) were computed.
        # * Finally, call `post_execute()` and verify that `complete logic
        #   tree` artifacts were created.

        # There 4 sources in the test input model; we can test them all with 1
        # task.
        sources_per_task = 4

        self.calc.pre_execute()
        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()

        hc = self.job.hazard_calculation
        num_sites = len(hc.points_to_compute())

        rlz1, rlz2 = models.LtRealization.objects.filter(
            hazard_calculation=hc.id)

        progress = dict(total=0, computed=0)

        task_arg_gen = self.calc.task_arg_gen(
            hc, self.job, sources_per_task, progress)
        task_arg_list = list(task_arg_gen)

        self.assertEqual(2, len(task_arg_list))

        # Now test the completion signal messaging of the task:
        def test_callback(body, message):
            self.assertEqual(
                dict(job_id=self.job.id, num_sources=sources_per_task), body)
            message.ack()

        exchange, conn_args = haz_general.exchange_and_conn_args()

        routing_key = haz_general.ROUTING_KEY_FMT % dict(job_id=self.job.id)
        task_signal_queue = kombu.Queue(
            'htasks.job.%s' % self.job.id, exchange=exchange,
            routing_key=routing_key, durable=False, auto_delete=True)

        with kombu.BrokerConnection(**conn_args) as conn:
            task_signal_queue(conn.channel()).declare()
            with conn.Consumer(task_signal_queue, callbacks=[test_callback]):
                # call the task as a normal function
                for args in task_arg_list:
                    core_next.ses_and_gmfs(*args)

                    # wait for the completion signal
                    conn.drain_events()

        # Check the 'total' counter (computed by the task arg generator):
        # 2 realizations * 4 sources = 8 total
        self.assertEqual(8, progress['total'])

        # Now check that we saved the right number of ruptures to the DB.
        ruptures1 = models.SESRupture.objects.filter(
            ses__ses_collection__lt_realization=rlz1)
        self.assertEqual(118, ruptures1.count())

        ruptures2 = models.SESRupture.objects.filter(
            ses__ses_collection__lt_realization=rlz2)
        self.assertEqual(92, ruptures2.count())

        # Check that we saved the right number of GMFs to the DB.
        # The correct number of GMFs for each realization is
        # num_ruptures * num_sites * num_imts

        expected_gmfs1 = 118 * num_sites * 2  # we have 2 imts: PGA and SA(0.1)
        gmfs1 = models.GmfNode.objects.filter(
            gmf__gmf_set__gmf_collection__lt_realization=rlz1)
        self.assertEqual(expected_gmfs1, gmfs1.count())

        expected_gmfs2 = 92 * num_sites * 2
        gmfs2 = models.GmfNode.objects.filter(
            gmf__gmf_set__gmf_collection__lt_realization=rlz2)
        self.assertEqual(expected_gmfs2, gmfs2.count())

        # TODO: At some point, we'll need to test the actual values of these
        # ruptures. We'll need to collect QA test data for this.

        # Check the complete logic tree SES and make sure it contains
        # all of the ruptures.
        complete_lt_ses = models.SES.objects.get(
            ses_collection__output__oq_job=self.job.id,
            ses_collection__output__output_type='complete_lt_ses',
            complete_logic_tree_ses=True)

        clt_ses_ruptures = models.SESRupture.objects.filter(
            ses=complete_lt_ses.id)

        self.assertEqual(210, clt_ses_ruptures.count())

        # Test the computed `investigation_time`
        # 2 lt realizations * 5 ses_per_logic_tree_path * 50.0 years
        self.assertEqual(500.0, complete_lt_ses.investigation_time)

        self.assertIsNone(complete_lt_ses.ordinal)

        # Check the complete logic tree GMF set and make sure it contains
        # all of the GMFs.
        complete_lt_gmf = models.GmfSet.objects.get(
            gmf_collection__output__oq_job=self.job.id,
            gmf_collection__output__output_type='complete_lt_gmf',
            complete_logic_tree_gmf=True)

        clt_gmfs = models.GmfNode.objects.filter(
            gmf__gmf_set=complete_lt_gmf.id)
        self.assertEqual(expected_gmfs1 + expected_gmfs2, clt_gmfs.count())

        self.assertEqual(500.0, complete_lt_gmf.investigation_time)
        self.assertIsNone(complete_lt_gmf.ses_ordinal)
