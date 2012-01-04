# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


"""
Unit tests for the utils.stats module.
"""

import sys
import unittest

from openquake.utils import stats

from tests.utils import helpers


class ProgressIndicatorTestCase(helpers.RedisTestMixin, unittest.TestCase):
    """Tests the behaviour of utils.stats.progress_indicator()."""

    def test_success_stats(self):
        """
        The success counter is incremented when the wrapped function
        terminates without raising an exception.
        """

        @stats.progress_indicator
        def no_exception(job_id):
            return 999

        kvs = self.connect()
        key = stats.key_name(11, no_exception.__name__)
        previous_value = kvs.get(key)
        previous_value = int(previous_value) if previous_value else 0

        # Call the wrapped function.
        self.assertEqual(999, no_exception(11))

        value = int(kvs.get(key))
        self.assertEqual(1, (value - previous_value))

    def test_failure_stats(self):
        """
        The failure counter is incremented when the wrapped function
        terminates raises an exception.
        """

        @stats.progress_indicator
        def raise_exception(job_id):
            raise NotImplementedError

        kvs = self.connect()
        key = stats.key_name(22, raise_exception.__name__) + ":f"
        previous_value = kvs.get(key)
        previous_value = int(previous_value) if previous_value else 0

        # Call the wrapped function.
        self.assertRaises(NotImplementedError, raise_exception, 22)

        value = int(kvs.get(key))
        self.assertEqual(1, (value - previous_value))


class SetTotalTestCase(helpers.RedisTestMixin, unittest.TestCase):
    """Tests the behaviour of utils.stats.set_total()."""

    def test_set_total(self):
        """
        The total value is set for the given key
        """
        kvs = self.connect()
        # Specify a 'totals' counter type.
        key = stats.key_name(33, "a/b/c", counter_type="t")
        stats.set_total(33, "a/b/c", 123)
        self.assertEqual("123", kvs.get(key))


class IncrCounterTestCase(helpers.RedisTestMixin, unittest.TestCase):
    """Tests the behaviour of utils.stats.incr_counter()."""

    def test_incr_counter(self):
        """
        The counter is incremented for the given key
        """
        args = (44, "d/x/z")
        kvs = self.connect()
        key = stats.key_name(*args)
        previous_value = kvs.get(key)
        previous_value = int(previous_value) if previous_value else 0
        stats.incr_counter(*args)
        value = int(kvs.get(key))
        self.assertEqual(1, (value - previous_value))


class GetCounterTestCase(helpers.RedisTestMixin, unittest.TestCase):
    """Tests the behaviour of utils.stats.get_counter()."""

    def test_get_value_with_non_existent_incremental(self):
        """`None` is returned for a non-existent incremental counter."""
        args = (55, "d/a/z")
        key = stats.key_name(*args)
        kvs = self.connect()
        self.assertIs(None, kvs.get(key))
        self.assertIs(None, stats.get_counter(*args))

    def test_get_value_with_existent_incremental(self):
        """
        The expected value is returned for an existent incremental counter.
        """
        value = "561"
        args = (56, "d/b/z")
        key = stats.key_name(*args)
        kvs = self.connect()
        kvs.set(key, value)
        self.assertEqual(int(value), stats.get_counter(*args))

    def test_get_value_with_non_existent_total(self):
        """`None` is returned for a non-existent total counter."""
        args = (57, "d/c/z")
        key = stats.key_name(*args, counter_type="t")
        kvs = self.connect()
        self.assertIs(None, kvs.get(key))
        self.assertIs(None, stats.get_counter(*args, counter_type="t"))

    def test_get_value_with_existent_total(self):
        """The expected value is returned for an existent total counter."""
        value = "582"
        args = (58, "d/d/z")
        key = stats.key_name(*args, counter_type="t")
        kvs = self.connect()
        kvs.set(key, value)
        self.assertEqual(
            int(value), stats.get_counter(*args, counter_type="t"))


class DeleteJobCountersTestCase(helpers.RedisTestMixin, unittest.TestCase):
    """Tests the behaviour of utils.stats.delete_job_counters()."""

    def test_delete_job_counters_deletes_counters_for_job(self):
        """
        The progress indication counters for a given job are deleted.
        """
        kvs = self.connect()
        args = [(55, "a/b/c"), (55, "d/e/f")]
        for data in args:
            stats.incr_counter(*data)
        stats.delete_job_counters(55)
        self.assertEqual(0, len(kvs.keys("oqs:55:*")))

    def test_delete_job_counters_resets_counters(self):
        """
        The progress indication counters for a given job are reset.
        """
        kvs = self.connect()
        args = [(66, "g/h/i"), (66, "j/k/l")]
        for data in args:
            stats.incr_counter(*data)
        stats.delete_job_counters(66)
        # The counters have been reset, after incrementing we expect them all
        # to have a value of "1".
        for data in args:
            stats.incr_counter(*data)
            self.assertEqual("1", kvs.get(stats.key_name(*data)))

    def test_delete_job_counters_copes_with_nonexistent_counters(self):
        """
        stats.delete_job_counters() copes with jobs without progress indication
        counters.
        """
        stats.delete_job_counters(sys.maxint)
