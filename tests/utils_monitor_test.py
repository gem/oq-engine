# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


"""
Unit tests for the utils.stats module.
"""


import unittest

from django.test import TestCase as DjangoTestCase

from openquake.engine import engine
from openquake.engine.db import models
from openquake.engine.utils import monitor

from tests.utils.helpers import patch


class DbCnodeStatusTestCase(unittest.TestCase):
    """Tests the behaviour of utils.monitor._db_cnode_status()."""

    def test__db_cnode_status(self):
        job = engine.prepare_job()
        expected = {}
        for node, status in [("N1", "up"), ("N2", "down"), ("N3", "down")]:
            ns = models.CNodeStats(oq_job=job, node=node,
                                   current_status=status)
            ns.save(using="job_init")
            expected[node] = ns
        self.assertEqual(expected, monitor._db_cnode_status(job.id))

    def test__db_cnode_status_and_wrong_job_id(self):
        job = engine.prepare_job()
        expected = {}
        for node, status in [("O1", "up"), ("O2", "down"), ("O3", "down")]:
            ns = models.CNodeStats(oq_job=job, node=node,
                                   current_status=status)
            ns.save(using="job_init")
        self.assertEqual(expected, monitor._db_cnode_status(-1))

    def test__db_cnode_status_and_two_jobs(self):
        job1 = engine.prepare_job()
        for node, status in [("P1", "up"), ("P2", "down"), ("P3", "down")]:
            ns = models.CNodeStats(oq_job=job1, node=node,
                                   current_status=status)
            ns.save(using="job_init")
        job2 = engine.prepare_job()
        expected = {}
        for node, status in [("Q2", "down"), ("Q3", "down")]:
            ns = models.CNodeStats(oq_job=job2, node=node,
                                   current_status=status)
            ns.save(using="job_init")
            expected[node] = ns
        self.assertEqual(expected, monitor._db_cnode_status(job2.id))


class CNodeStatsTestCase(DjangoTestCase, unittest.TestCase):
    """Test the cnode_stats database constraints."""

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = engine.prepare_job()

    def test_cnode_stats_with_correct_data(self):
        # The db record is saved w/o triggering an exception
        cs = models.CNodeStats(oq_job=self.job, node="N1", current_status="up")
        cs.save(using="job_init")

    def test_cnode_stats_failure_counter_with_up_down_transition(self):
        # The failures counter is incremented in case of a
        #   up -> down transition
        cs = models.CNodeStats(oq_job=self.job, node="N3", current_status="up")
        cs.save(using="job_init")
        cs.current_status = "down"
        cs.save(using="job_init")
        cs = models.CNodeStats.objects.get(id=cs.id)

        self.assertEqual(1, cs.failures)

    def test_cnode_stats_failure_counter_with_down_up_transition(self):
        # The failures counter is only stepped in case of a
        #   up -> down transition
        # and will remain unchanged here.
        cs = models.CNodeStats(oq_job=self.job, node="N6",
                               current_status="down")
        cs.save(using="job_init")
        cs.current_status = "up"
        cs.save(using="job_init")
        cs = models.CNodeStats.objects.get(id=cs.id)

        self.assertEqual(0, cs.failures)

    def test_cnode_stats_with_state_transition_and_managed_timestamps(self):
        # The `previous_ts` and `current_ts` time stamps are managed properly
        # in case of a state transition
        cs = models.CNodeStats(oq_job=self.job, node="N7",
                               current_status="down")
        cs.save(using="job_init")
        old_current_ts = cs.current_ts

        cs.current_status = "up"
        cs.save(using="job_init")
        cs = models.CNodeStats.objects.get(id=cs.id)

        self.assertIsNot(None, cs.previous_ts)
        self.assertEqual(old_current_ts, cs.previous_ts)

    def test_cnode_stats_without_state_transition_and_same_timestamps(self):
        # The `previous_ts` and `current_ts` time stamps are untouched
        # if the compute node status did not change
        cs = models.CNodeStats(oq_job=self.job, node="N8",
                               current_status="down")
        cs.save(using="job_init")
        old_current_ts = cs.current_ts

        cs.node = "N8+1"
        cs.save(using="job_init")
        cs = models.CNodeStats.objects.get(id=cs.id)

        self.assertIs(None, cs.previous_ts)
        self.assertEqual(old_current_ts, cs.current_ts)


class CountFailedNodesTestCase(unittest.TestCase):
    """Tests the behaviour of utils.monitor.count_failed_nodes()."""

    job = db_patch = live_patch = db_mock = live_mock = None

    @classmethod
    def setUpClass(cls):
        cls.job = engine.prepare_job()

    def setUp(self):
        self.db_patch = patch(
            'openquake.engine.utils.monitor._db_cnode_status')
        self.live_patch = (
            patch('openquake.engine.utils.monitor._live_cnode_status'))
        self.db_mock = self.db_patch.start()
        self.live_mock = self.live_patch.start()

    def tearDown(self):
        self.db_patch.stop()
        self.live_patch.stop()

    def test_count_failed_nodes_with_zero_nodes(self):
        # Signal when there are zero live nodes at the start of the calculation
        self.db_mock.return_value = {}
        self.live_mock.return_value = set()
        actual = monitor.count_failed_nodes(self.job)
        self.assertEqual(-1, actual)

    def test_count_failed_nodes_with_a_node_that_went_offline(self):
        # Result: 1 failed nodes
        cs = models.CNodeStats(oq_job=self.job, node="N1", current_status="up")
        self.db_mock.return_value = {"N1": cs}
        self.live_mock.return_value = set()
        actual = monitor.count_failed_nodes(self.job)
        self.assertEqual(1, actual)

    def test_count_failed_nodes_with_failures_during_calculation(self):
        # Result: 2 node failures, please note that the function under test
        # counts the total number of node failures that occurred during a
        # calculation and *not* the number of currently failed nodes.
        n1 = models.CNodeStats(oq_job=self.job, node="N3",
                                current_status="up")
        n2 = models.CNodeStats(oq_job=self.job, node="N4",
                                current_status="down", failures=1)
        self.db_mock.return_value = {"N3": n1, "N4": n2}
        self.live_mock.return_value = set(["N5"])
        actual = monitor.count_failed_nodes(self.job)
        self.assertEqual(2, actual)
        # Please note also that the new node ("N5") was written to the
        # database
        [n3] = models.CNodeStats.objects.filter(oq_job=self.job, node="N5")
        self.assertEqual("up", n3.current_status)
        self.assertEqual(0, n3.failures)

    def test_count_failed_nodes_with_failures_before_calculation(self):
        # Result: 1 node failure; this simulates the situation where a
        # node has failed from the very beginning and never recovered i.e. it
        # never took on any tasks. Only nodes that were functioning at some
        # time during the calculation and *then* failed are counted.
        n1 = models.CNodeStats(oq_job=self.job, node="N6", current_status="up")
        n1.save(using="job_init")
        n2 = models.CNodeStats(oq_job=self.job, node="N7",
                               current_status="down")
        self.db_mock.return_value = {"N6": n1, "N7": n2}
        self.live_mock.return_value = set()
        actual = monitor.count_failed_nodes(self.job)
        self.assertEqual(1, actual)
        # The failed node has been updated to capture that.
        n1 = models.CNodeStats.objects.get(id=n1.id)
        self.assertEqual("down", n1.current_status)
        self.assertEqual(1, n1.failures)

    def test_count_failed_nodes_with_failed_and_recovered_node(self):
        # Result: 1 node failure; the node failed and recovered. Its failures
        # counter is unaffected by the recovery.
        n1 = models.CNodeStats(oq_job=self.job, node="N8", current_status="up")
        n1.save(using="job_init")
        self.assertEqual(0, n1.failures)

        n1.current_status = "down"
        n1.save(using="job_init")
        n1 = models.CNodeStats.objects.get(id=n1.id)
        self.assertEqual(1, n1.failures)

        self.db_mock.return_value = {"N8": n1}
        self.live_mock.return_value = set(["N8"])
        actual = monitor.count_failed_nodes(self.job)
        self.assertEqual(1, actual)
        # The failed node has been updated to capture that.
        n1 = models.CNodeStats.objects.get(id=n1.id)
        self.assertEqual("up", n1.current_status)
        self.assertEqual(1, n1.failures)
