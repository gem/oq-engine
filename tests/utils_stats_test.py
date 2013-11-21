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

from datetime import datetime
from datetime import timedelta
import itertools
import string
import sys
import unittest

from openquake.engine import engine
from openquake.engine.db.models import HazardCalculation
from openquake.engine.utils import stats

from tests.utils import helpers


class SetTotalTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of utils.stats.set_total()."""

    def test_set_total(self):
        """
        The total value is set for the given key
        """
        kvs = self.connect()
        # Specify a 'totals' counter type.
        key = stats.key_name(33, "h", "a/b/c", "t")
        stats.set_total(33, "h", "a/b/c", 123)
        self.assertEqual("123", kvs.get(key))


class IncrCounterTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of utils.stats.incr_counter()."""

    def test_incr_counter(self):
        """
        The counter is incremented for the given key
        """
        args = (44, "h", "d/x/z", "i")
        kvs = self.connect()
        key = stats.key_name(*args)
        previous_value = kvs.get(key)
        previous_value = int(previous_value) if previous_value else 0
        stats.incr_counter(*args[:-1])
        value = int(kvs.get(key))
        self.assertEqual(1, (value - previous_value))


class GetCounterTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of utils.stats.get_counter()."""

    def test_get_value_with_non_existent_incremental(self):
        """`None` is returned for a non-existent incremental counter."""
        args = (55, "h", "d/a/z", "i")
        key = stats.key_name(*args)
        kvs = self.connect()
        self.assertIs(None, kvs.get(key))
        self.assertIs(None, stats.get_counter(*args))

    def test_get_value_with_existent_incremental(self):
        """
        The expected value is returned for an existent incremental counter.
        """
        value = "561"
        args = (56, "h", "d/b/z", "i")
        key = stats.key_name(*args)
        kvs = self.connect()
        kvs.set(key, value)
        self.assertEqual(int(value), stats.get_counter(*args))

    def test_get_value_with_non_existent_total(self):
        """`None` is returned for a non-existent total counter."""
        args = (57, "h", "d/c/z", "t")
        key = stats.key_name(*args)
        kvs = self.connect()
        self.assertIs(None, kvs.get(key))
        self.assertIs(None, stats.get_counter(*args))

    def test_get_value_with_existent_total(self):
        """The expected value is returned for an existent total counter."""
        value = "582"
        args = (58, "h", "d/d/z", "t")
        key = stats.key_name(*args)
        kvs = self.connect()
        kvs.set(key, value)
        self.assertEqual(int(value), stats.get_counter(*args))


class DeleteJobCountersTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of utils.stats.delete_job_counters()."""

    def test_delete_job_counters_deletes_counters_for_job(self):
        """
        The progress indication counters for a given job are deleted.
        """
        kvs = self.connect()
        args = [(55, "h", "a/b/c"), (55, "h", "d/e/f")]
        for data in args:
            stats.incr_counter(*data)
        stats.delete_job_counters(55)
        self.assertEqual(0, len(kvs.keys("oqs:55:*")))

    def test_delete_job_counters_resets_counters(self):
        """
        The progress indication counters for a given job are reset.
        """
        kvs = self.connect()
        args = [(66, "h", "g/h/i", "i"), (66, "h", "j/k/l", "i")]
        for data in args:
            stats.incr_counter(*data[:-1])
        stats.delete_job_counters(66)
        # The counters have been reset, after incrementing we expect them all
        # to have a value of "1".
        for data in args:
            stats.incr_counter(*data[:-1])
            self.assertEqual("1", kvs.get(stats.key_name(*data)))

    def test_delete_job_counters_copes_with_nonexistent_counters(self):
        """
        stats.delete_job_counters() copes with jobs without progress indication
        counters.
        """
        stats.delete_job_counters(sys.maxint)


class PkSetTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of utils.stats.pk_set()."""

    def test_pk_set_with_existing_total(self):
        """The value is set correctly for an existing predefined key."""
        job_id = 71
        pkey = "blocks"
        key = stats.key_name(job_id, *stats.STATS_KEYS[pkey])

        stats.delete_job_counters(job_id)
        kvs = self.connect()
        stats.pk_set(job_id, pkey, 717)
        self.assertEqual("717", kvs.get(key))

    def test_pk_set_with_existing_incremental(self):
        """The value is set correctly for an existing predefined key."""
        job_id = 72
        pkey = "cblock"
        key = stats.key_name(job_id, *stats.STATS_KEYS[pkey])

        stats.delete_job_counters(job_id)
        kvs = self.connect()
        stats.pk_set(job_id, pkey, 727)
        self.assertEqual("727", kvs.get(key))

    def test_pk_set_with_non_existent_predef_key(self):
        """`KeyError` is raised for keys that do not exist in `STATS_KEYS`."""
        job_id = 73
        pkey = "To be or not to be!?"
        stats.delete_job_counters(job_id)

        self.assertRaises(KeyError, stats.pk_set, job_id, pkey, 737)


class PkIncTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of utils.stats.pk_inc()."""

    def test_pk_inc_with_existing_total(self):
        """The value is incremented for an existing predefined key."""
        job_id = 81
        pkey = "blocks"
        key = stats.key_name(job_id, *stats.STATS_KEYS[pkey])

        stats.delete_job_counters(job_id)
        kvs = self.connect()
        stats.pk_inc(job_id, pkey)
        self.assertEqual("1", kvs.get(key))

    def test_pk_inc_with_existing_incremental(self):
        """The value is incremented for an existing predefined key."""
        job_id = 82
        pkey = "cblock"
        key = stats.key_name(job_id, *stats.STATS_KEYS[pkey])

        stats.delete_job_counters(job_id)
        kvs = self.connect()
        stats.pk_inc(job_id, pkey)
        self.assertEqual("1", kvs.get(key))

    def test_pk_inc_with_non_existent_predef_key(self):
        """`KeyError` is raised for keys that do not exist in `STATS_KEYS`."""
        job_id = 83
        pkey = "That is the question.."
        stats.delete_job_counters(job_id)

        self.assertRaises(KeyError, stats.pk_inc, job_id, pkey)


class PkGetTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of utils.stats.pk_get()."""

    def test_pk_get_with_existing_total(self):
        """The correct value is obtained for an existing predefined key."""
        job_id = 91
        pkey = "blocks"
        key = stats.key_name(job_id, *stats.STATS_KEYS[pkey])

        stats.delete_job_counters(job_id)
        kvs = self.connect()
        kvs.set(key, 919)
        stats.pk_get(job_id, pkey)
        self.assertEqual("919", kvs.get(key))

    def test_pk_get_with_existing_incremental(self):
        """The correct value is obtained for an existing predefined key."""
        job_id = 92
        pkey = "cblock"
        key = stats.key_name(job_id, *stats.STATS_KEYS[pkey])

        stats.delete_job_counters(job_id)
        kvs = self.connect()
        kvs.set(key, 929)
        stats.pk_get(job_id, pkey)
        self.assertEqual("929", kvs.get(key))

    def test_pk_get_with_non_existent_predef_key(self):
        """`KeyError` is raised for keys that do not exist in `STATS_KEYS`."""
        job_id = 93
        pkey = "This is unlikely to exist"
        stats.delete_job_counters(job_id)
        self.assertRaises(KeyError, stats.pk_get, job_id, pkey)


class KvsOpTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of utils.stats.pk_kvs_op()."""

    def test_kvs_op_with_invalid_op(self):
        """An `AttributeError` is raised for unknown kvs operations"""
        self.assertRaises(AttributeError, stats.kvs_op, "no-such-op",
                          "any-key-will-do")


class FailureCountersTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of utils.stats.failure_counters()."""

    def test_failure_counters_with_valid_area(self):
        # Failure counters are returned for valid computation areas.
        stats.delete_job_counters(123)
        fcname = itertools.cycle(string.ascii_lowercase)
        for cidx, carea in enumerate(["g", "h", "r"]):
            stats.incr_counter(123, carea, "%s:failed" % fcname.next())
            if not (cidx % 2):
                stats.incr_counter(123, carea, "%s:failed" % fcname.next())

        self.assertEqual(
            [('oqs/123/g/a:failed/i', 1), ('oqs/123/g/b:failed/i', 1)],
            sorted(stats.failure_counters(123, "g")))
        self.assertEqual([('oqs/123/h/c:failed/i', 1)],
                         sorted(stats.failure_counters(123, "h")))
        self.assertEqual(
            [('oqs/123/r/d:failed/i', 1), ('oqs/123/r/e:failed/i', 1)],
            sorted(stats.failure_counters(123, "r")))

    def test_failure_counters_with_invalid_area(self):
        # An exception is raised for invalid computation areas.
        self.assertRaises(AssertionError, stats.failure_counters, 123, "x")

    def test_failure_counters_with_no_area(self):
        # Failure counters are returned for all computation areas if the
        # 'area' parameter is omitted.
        stats.delete_job_counters(123)
        fcname = itertools.cycle(string.ascii_lowercase)
        for cidx, carea in enumerate(["g", "h", "r"]):
            stats.incr_counter(123, carea, "%s:failed" % fcname.next())
            if not (cidx % 2):
                stats.incr_counter(123, carea, "%s:failed" % fcname.next())

        self.assertEqual(
            [('oqs/123/g/a:failed/i', 1), ('oqs/123/g/b:failed/i', 1),
             ('oqs/123/h/c:failed/i', 1), ('oqs/123/r/d:failed/i', 1),
             ('oqs/123/r/e:failed/i', 1)],
            sorted(stats.failure_counters(123)))

    def test_failure_counters_with_no_failures(self):
        # An empty list is returned in the absence of any failure counters
        stats.delete_job_counters(123)
        self.assertEqual([], stats.failure_counters(123))


class CountProgressTestCase(helpers.RedisTestCase, unittest.TestCase):
    """Tests the behaviour of utils.stats.count_progress()."""

    def test_wrong_arguments(self):
        @stats.count_progress('h')
        def wrong_args(job_id, non_sequence):
            pass
        self.assertRaises(TypeError, wrong_args, 1, 2)

    def test_success_stats(self):
        """
        The success counter is incremented when the wrapped function
        terminates without raising an exception.
        """
        area = "h"

        @stats.count_progress(area)
        def no_exception(job_id, items):
            return 999

        previous_value = stats.pk_get(11, "nhzrd_done")
        self.assertIsNone(previous_value)

        # Call the wrapped function.
        self.assertEqual(999, no_exception(11, range(5)))

        value = stats.pk_get(11, "nhzrd_done")
        self.assertEqual(5, value)

    def test_failure_stats(self):
        """
        The failure counter is incremented when the wrapped function
        terminates raises an exception.
        """
        area = "r"

        @stats.count_progress(area)
        def raise_exception(job_id, items):
            raise NotImplementedError

        previous_value = stats.pk_get(22, "nrisk_failed")
        self.assertIsNone(previous_value)

        # Call the wrapped function.
        self.assertRaises(NotImplementedError, raise_exception, 22, range(6))

        value = stats.pk_get(22, "nrisk_failed")
        self.assertEqual(6, value)
