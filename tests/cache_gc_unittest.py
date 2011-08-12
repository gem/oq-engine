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


import mock
import sys
import unittest

from bin import cache_gc
from openquake import kvs
from openquake.kvs import tokens
from tests.utils.helpers import patch


class CacheGCTestCase(unittest.TestCase):
    """
    Tests for the various functions in the bin/cache_gc.py script.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = kvs.get_client()

        cls.client.delete(tokens.CURRENT_JOBS)
        cls.client.delete(tokens.NEXT_JOB_ID)

    @classmethod
    def tearDownClass(cls):
        cls.client.delete(tokens.NEXT_JOB_ID)
        cls.client.delete(tokens.CURRENT_JOBS)

    def test_get_current_job_ids(self):
        """
        Given the test data, make sure that
        :py:function:`bin.cache_gc._get_current_job_ids` returns the correct
        IDs.
        """
        # create 3 jobs
        # this will add job keys to CURRENT_JOBS
        for _ in range(1, 4):
            tokens.alloc_job_id()

        job_ids = cache_gc._get_current_job_ids()
        self.assertEqual([1, 2, 3], job_ids)

    def test_clear_job_data_raises(self):
        """
        Test that :py:function:`bin.cache_gc.clear_job_data` raises
        a ValueError on invalid input.
        """
        self.assertRaises(ValueError, cache_gc.clear_job_data, '1234bad')

    def test_clear_job_data(self):
        """
        Verify that :py:function:`openquake.kvs.cache_gc` is called.

        :py:function:`openquake.kvs.cache_gc` will be mocked in this test
        since the actual code is exercised in a separate.
        """
        with patch('openquake.kvs.cache_gc') as gc_mock:
            # we don't really care what the return val is
            gc_mock.return_value = 3

            # make sure cache_gc was called and the args are correct
            cache_gc.clear_job_data(1)
            self.assertEqual(1, gc_mock.call_count)
            self.assertEqual(
                ((kvs.JOB_KEY_FMT % 1, ), {}), gc_mock.call_args)

            # same thing, but this time with a str for the ID
            cache_gc.clear_job_data('2')
            self.assertEqual(2, gc_mock.call_count)
            self.assertEqual(
                ((kvs.JOB_KEY_FMT % 2, ), {}), gc_mock.call_args)
