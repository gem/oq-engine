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


import unittest

from bin import cache_gc
from openquake import kvs
from tests.utils.helpers import patch

from tests.utils.helpers import cleanup_loggers


class CacheGCTestCase(unittest.TestCase):
    """
    Tests for the various functions in the bin/cache_gc.py script.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = kvs.get_client()

        cls.client.delete(kvs.tokens.CURRENT_JOBS)

    @classmethod
    def tearDownClass(cls):
        cls.client.delete(kvs.tokens.CURRENT_JOBS)

    def setUp(self):
        cleanup_loggers()

    def tearDown(self):
        cleanup_loggers()

    def test_get_current_job_ids(self):
        """
        Given the test data, make sure that
        :py:function:`bin.cache_gc._get_current_job_ids` returns the correct
        IDs.
        """
        # create 3 jobs
        # this will add job keys to CURRENT_JOBS
        for job_id in range(1, 4):
            kvs.mark_job_as_current(job_id)

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
                ((1, ), {}), gc_mock.call_args)

            # same thing, but this time with a str for the ID
            cache_gc.clear_job_data('2')
            self.assertEqual(2, gc_mock.call_count)
            self.assertEqual(
                ((2, ), {}), gc_mock.call_args)
