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

from django.db import transaction
from django.db.utils import DatabaseError
from django.test import TestCase as DjangoTestCase

from openquake import engine
from openquake.db import models
from openquake.utils import monitor

from tests.utils.helpers import patch


class GetCnodeStatusTestCase(unittest.TestCase):
    """Tests the behaviour of utils.monitor._get_cnode_status()."""

    def test__get_cnode_status(self):
        with patch('subprocess.check_output') as mock:
            mock.return_value = "\n".join(
                ["gemsun02: OK", "gemsun01: OK", "gemsun03: OK", "",
                 "3 nodes online."])
            actual = monitor._get_cnode_status()
            expected = {"gemsun01": "OK", "gemsun02": "OK", "gemsun03": "OK"}
            self.assertEqual(expected, actual)

    def test__get_cnode_status_with_one(self):
        with patch('subprocess.check_output') as mock:
            mock.return_value = "\n".join(["usc: OK", "", "1 node online."])
            actual = monitor._get_cnode_status()
            expected = {"usc": "OK"}
            self.assertEqual(expected, actual)

    def test__get_cnode_status_with_mixed(self):
        with patch('subprocess.check_output') as mock:
            mock.return_value = "\n".join(
                ["oqt: OK", "usc: ERROR", "", "2 nodes online."])
            actual = monitor._get_cnode_status()
            expected = {"oqt": "OK", "usc": "ERROR"}
            self.assertEqual(expected, actual)


class GetCnodeStatusInDbTestCase(unittest.TestCase):
    """Tests the behaviour of utils.monitor._get_cnode_status_in_db()."""

    def test__get_cnode_status_in_db(self):
        job = engine.prepare_job()
        expected = {}
        for node, status in [("N1", "up"), ("N2", "down"), ("N3", "error")]:
            ns = models.CNodeStats(oq_job=job, node=node,
                                   current_status=status)
            ns.save(using="job_superv")
            expected[node] = ns
        self.assertEqual(expected, monitor._get_cnode_status_in_db(job.id))

    def test__get_cnode_status_in_db_and_wrong_job_id(self):
        job = engine.prepare_job()
        expected = {}
        for node, status in [("O1", "up"), ("O2", "down"), ("O3", "error")]:
            ns = models.CNodeStats(oq_job=job, node=node,
                                   current_status=status)
            ns.save(using="job_superv")
        self.assertEqual(expected, monitor._get_cnode_status_in_db(-1))

    def test__get_cnode_status_in_db_and_two_jobs(self):
        job1 = engine.prepare_job()
        for node, status in [("P1", "up"), ("P2", "down"), ("P3", "error")]:
            ns = models.CNodeStats(oq_job=job1, node=node,
                                   current_status=status)
            ns.save(using="job_superv")
        job2 = engine.prepare_job()
        expected = {}
        for node, status in [("Q2", "down"), ("Q3", "error")]:
            ns = models.CNodeStats(oq_job=job2, node=node,
                                   current_status=status)
            ns.save(using="job_superv")
            expected[node] = ns
        self.assertEqual(expected, monitor._get_cnode_status_in_db(job2.id))


class CNodeStatsTestCase(DjangoTestCase, unittest.TestCase):
    """Test the cnode_stats database constraints."""

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = engine.prepare_job()

    def test_cnode_stats_with_correct_data(self):
        # The db record is saved w/o triggering an exception
        cs = models.CNodeStats(oq_job=self.job, node="N1", current_status="up")
        cs.save(using="job_superv")

    def test_cnode_stats_with_equal_statuses(self):
        # The previous and the current status must not be the same.
        cs = models.CNodeStats(oq_job=self.job, node="N2", current_status="up")
        cs.previous_status = "up"
        try:
            cs.save(using="job_superv")
        except DatabaseError, de:
            self.assertTrue (
                'violates check constraint "valid_status"' in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_cnode_stats_failure_counter_with_up_down_transition(self):
        # The failures counter is incremented in case of a
        #   up -> down transition
        cs = models.CNodeStats(oq_job=self.job, node="N3", current_status="up")
        cs.save(using="job_superv")
        cs.current_status = "down"
        cs.previous_status = "up"
        cs.save(using="job_superv")
        cs = models.CNodeStats.objects.get(id=cs.id)

        self.assertEqual(1, cs.failures)

    def test_cnode_stats_failure_counter_with_up_error_transition(self):
        # The failures counter is incremented in case of a
        #   up -> error transition
        cs = models.CNodeStats(oq_job=self.job, node="N4", current_status="up")
        cs.save(using="job_superv")
        cs.current_status = "error"
        cs.previous_status = "up"
        cs.save(using="job_superv")
        cs = models.CNodeStats.objects.get(id=cs.id)

        self.assertEqual(1, cs.failures)

    def test_cnode_stats_failure_counter_with_down_error_transition(self):
        # The failures counter is only stepped in case of a
        #   up -> down/error transition
        # and will remain unchanged here.
        cs = models.CNodeStats(oq_job=self.job, node="N5",
                               current_status="down")
        cs.save(using="job_superv")
        cs.current_status = "error"
        cs.previous_status = "down"
        cs.save(using="job_superv")
        cs = models.CNodeStats.objects.get(id=cs.id)

        self.assertEqual(0, cs.failures)

    def test_cnode_stats_failure_counter_with_down_up_transition(self):
        # The failures counter is only stepped in case of a
        #   up -> down/error transition
        # and will remain unchanged here.
        cs = models.CNodeStats(oq_job=self.job, node="N6",
                               current_status="down")
        cs.save(using="job_superv")
        cs.current_status = "up"
        cs.previous_status = "down"
        cs.save(using="job_superv")
        cs = models.CNodeStats.objects.get(id=cs.id)

        self.assertEqual(0, cs.failures)

    def test_cnode_stats_with_state_transition_and_managed_timestamps(self):
        # The `previous_ts` and `current_ts` time stamps are managed properly
        # in case of a state transition
        cs = models.CNodeStats(oq_job=self.job, node="N7",
                               current_status="down")
        cs.save(using="job_superv")
        old_current_ts = cs.current_ts

        cs.current_status = "up"
        cs.previous_status = "down"
        cs.save(using="job_superv")
        cs = models.CNodeStats.objects.get(id=cs.id)

        self.assertIsNot(None, cs.previous_ts)
        self.assertEqual(old_current_ts, cs.previous_ts)

    def test_cnode_stats_without_state_transition_and_same_timestamps(self):
        # The `previous_ts` and `current_ts` time stamps are untouched
        # if the compute node status did not change
        cs = models.CNodeStats(oq_job=self.job, node="N8",
                               current_status="down")
        cs.save(using="job_superv")
        old_current_ts = cs.current_ts

        cs.node = "N8+1"
        cs.save(using="job_superv")
        cs = models.CNodeStats.objects.get(id=cs.id)

        self.assertIs(None, cs.previous_ts)
        self.assertEqual(old_current_ts, cs.current_ts)
