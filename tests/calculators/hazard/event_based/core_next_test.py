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
            [ses] = models.SES.objects.filter(
                ses_collection__lt_realization=rlz)

            # The only metadata in in the SES is investigation time.
            self.assertEqual(hc.investigation_time, ses.investigation_time)

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
            [gmf_set] = models.GmfSet.objects.filter(
                gmf_collection__lt_realization=rlz)

            # The only metadata in a GmfSet is investigation time.
            self.assertEqual(hc.investigation_time, gmf_set.investigation_time)

    @attr('slow')
    def test_stochastic_event_sets_task(self):
        # Execute the the `stochastic_event_sets` task as a normal function.

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

        rlz1_src_prog = models.SourceProgress.objects.filter(
            lt_realization=rlz1.id)
        rlz1_src_ids = [src.parsed_source.id for src in rlz1_src_prog]

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
        self.assertEqual(22, len(ruptures1))

        ruptures2 = models.SESRupture.objects.filter(
            ses__ses_collection__lt_realization=rlz2)
        self.assertEqual(17, len(ruptures2))

        # Check that we saved the right number of GMFs to the DB.
        # The correct number of GMFs for each realization is
        # num_ruptures * num_sites * num_imts

        expected_gmfs1 = 22 * num_sites * 2  # we have 2 imts: PGA and SA(0.1)
        gmfs1 = models.GmfNode.objects.filter(
            gmf__gmf_set__gmf_collection__lt_realization=rlz1)
        self.assertEqual(expected_gmfs1, len(gmfs1))

        expected_gmfs2 = 17 * num_sites * 2
        gmfs2 = models.GmfNode.objects.filter(
            gmf__gmf_set__gmf_collection__lt_realization=rlz2)
        self.assertEqual(expected_gmfs2, len(gmfs2))

        # TODO: At some point, we'll need to test the actual values of these
        # ruptures. We'll need to collect QA test data for this.
