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
import os

import unittest

from openquake import java
from openquake import logs
from openquake import kvs
from openquake import settings
from tests.utils import helpers


from openquake.kvs import tokens


LOG = logs.LOG

TEST_FILE = "nrml_test_result.xml"

EMPTY_MODEL = '{"modelName":"","hcRepList":[],"endBranchLabels":[]}'


def read_one_line(path):
    """
    Read and return a single line from the given file.

    :param path: path to a (text) file
    :type path: str

    :returns: first line from the file
    """
    return open(path, 'r').readline().strip('\n')


ONE_CURVE_MODEL = read_one_line(helpers.get_data_path('one-curve-model.json'))


class KVSTestCase(unittest.TestCase):
    """
    Tests for various KVS storage operations.
    """

    def setUp(self):
        # starting the jvm...
        print "About to start the jvm..."
        jpype = java.jvm()
        java_class = jpype.JClass("org.gem.engine.hazard.redis.Cache")
        print "Not dead yet, and found the class..."
        self.java_client = java_class(settings.KVS_HOST, settings.KVS_PORT)

        self.python_client = kvs.get_client(binary=False)

        self._delete_test_file()

    def tearDown(self):
        self._delete_test_file()
        self.python_client.flushdb()

    @staticmethod
    def _delete_test_file():
        try:
            os.remove(os.path.join(helpers.DATA_DIR, TEST_FILE))
        except OSError:
            pass

    def test_can_wrap_the_java_client(self):
        self.java_client.set("KEY", "VALUE")
        self.assertEqual("VALUE", self.java_client.get("KEY"))

    def test_can_write_in_java_and_read_in_python(self):
        self.java_client.set("KEY", "VALUE")
        self.assertEqual("VALUE", self.python_client.get("KEY"))

    def test_can_write_in_python_and_read_in_java(self):
        self.python_client.set("KEY", "VALUE")
        self.assertEqual("VALUE", self.java_client.get("KEY"))


class TokensTestCase(unittest.TestCase):
    """
    Tests for functions related to generation/allocation of KVS keys.
    """

    def setUp(self):
        self.job_id = 123456
        self.product = "TestProduct"
        self.block_id = 8801
        self.site = "Testville,TestLand"

    def test_generate_product_key_with_only_job_id_and_product(self):
        key = kvs.generate_product_key(self.job_id, self.product)

        ev = "%s!%s!!" % (self.job_id, self.product)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_job_id_product_and_block_id(self):
        key = kvs.generate_product_key(
            self.job_id, self.product, self.block_id)

        ev = "%s!%s!%s!" % (self.job_id, self.product, self.block_id)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_job_id_product_and_site(self):
        key = kvs.generate_product_key(self.job_id, self.product,
            site=self.site)

        ev = "%s!%s!!%s" % (self.job_id, self.product, self.site)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_all_test_data(self):
        key = kvs.generate_product_key(
            self.job_id, self.product, self.block_id, self.site)

        ev = "%s!%s!%s!%s" % (
                self.job_id, self.product, self.block_id, self.site)
        self.assertEqual(key, ev)

    def test_generate_product_key_with_tokens_from_kvs(self):
        products = [
            tokens.ERF_KEY_TOKEN,
            tokens.MGM_KEY_TOKEN,
            tokens.HAZARD_CURVE_KEY_TOKEN,
            tokens.EXPOSURE_KEY_TOKEN,
            tokens.GMF_KEY_TOKEN,
            tokens.LOSS_RATIO_CURVE_KEY_TOKEN,
            tokens.LOSS_CURVE_KEY_TOKEN,
            tokens.loss_token(0.01),
            tokens.VULNERABILITY_CURVE_KEY_TOKEN,
        ]

        for product in products:
            key = kvs.generate_product_key(self.job_id, product,
                self.block_id, self.site)

            ev = "%s!%s!%s!%s" % (self.job_id, product,
                    self.block_id, self.site)
            self.assertEqual(key, ev)

    def test_kvs_doesnt_support_spaces_in_keys(self):
        self.product = "A TestProduct"
        self.site = "Testville, TestLand"
        key = kvs.generate_product_key(self.job_id, self.product,
            site=self.site)

        ev = "%s!ATestProduct!!Testville,TestLand" % self.job_id
        self.assertEqual(key, ev)


class JobTokensTestCase(unittest.TestCase):
    """
    Tests related specifically to management of job keys.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = kvs.get_client()

    @classmethod
    def tearDownClass(cls):
        cls.client.delete(tokens.CURRENT_JOBS)
        cls.client.delete(tokens.NEXT_JOB_ID)

    def setUp(self):
        self.client.delete(tokens.CURRENT_JOBS)
        self.client.delete(tokens.NEXT_JOB_ID)

    def test_alloc_job_key(self):
        """
        Test the generation of job keys using
        :py:function:`openquake.kvs.tokens.alloc_job_key`.
        """

        job_key_1 = tokens.JOB_KEY_FMT % 1
        job_key_2 = tokens.JOB_KEY_FMT % 2

        kvs.get_client().delete(tokens.NEXT_JOB_ID)

        # it should be empty to start with
        self.assertTrue(kvs.get(tokens.NEXT_JOB_ID) is None)

        self.assertEqual(job_key_1, tokens.alloc_job_key())

        # verify that the IDs are incrementing properly
        self.assertEqual(job_key_2, tokens.alloc_job_key())

        # now verify that these keys have been added to the CURRENT_JOBS set
        self.assertTrue(self.client.sismember(tokens.CURRENT_JOBS, job_key_1))
        self.assertTrue(self.client.sismember(tokens.CURRENT_JOBS, job_key_2))

    def test_alloc_job_key_raises_on_duplicate(self):
        """
        Test that :py:function:`openquake.kvs.tokens.alloc_job_key` raises an
        RuntimeError if there is somehow a duplicate job key.
        """
        self.assertEqual(0, len(self.client.smembers(tokens.CURRENT_JOBS)))

        self.client.sadd(tokens.CURRENT_JOBS, tokens.JOB_KEY_FMT % 1)

        self.assertRaises(RuntimeError, tokens.alloc_job_key)

    def test_current_jobs(self):
        """
        Test the retrieval of the current jobs from the CURRENT_JOBS set.
        Exercises :py:function:`openquake.kvs.tokens.current_jobs`.
        """
        self.assertFalse(self.client.exists(tokens.CURRENT_JOBS))

        # load some sample jobs into the CURRENT_JOBS set
        jobs = [tokens.JOB_KEY_FMT % x for x in range(1, 4)]

        for job in jobs:
            self.client.sadd(tokens.CURRENT_JOBS, job)

        current_jobs = tokens.current_jobs()

        self.assertEqual(jobs, current_jobs)


class GarbageCollectionTestCase(unittest.TestCase):
    """
    Tests for KVS garbage collection.
    """

    def setUp(self):
        self.client = kvs.get_client()

        self.client.delete(tokens.CURRENT_JOBS)
        self.client.delete(tokens.NEXT_JOB_ID)

        self.test_job = tokens.alloc_job_key()

        # create some keys to hold fake data for test_job
        self.gmf1_key = tokens.gmfs_key(self.test_job, 0, 0)
        self.gmf2_key = tokens.gmfs_key(self.test_job, 0, 1)
        self.vuln_key = tokens.vuln_key(self.test_job)

        # now create the fake data for test_job
        self.client.set(self.gmf1_key, 'fake gmf data 1')
        self.client.set(self.gmf2_key, 'fake gmf data 2')
        self.client.set(self.vuln_key, 'fake vuln curve data')

        # this job will have no data
        self.dataless_job = tokens.alloc_job_key()

    def tearDown(self):
        self.client.delete(tokens.CURRENT_JOBS)
        self.client.delete(tokens.NEXT_JOB_ID)

    def test_gc_some_job_data(self):
        """
        Test that all job data is cleared and the job key is removed from
        CURRENT_JOBS.
        """
        result = kvs.cache_gc(self.test_job)

        # 3 things should have been deleted
        self.assertEqual(3, result)

        # make sure each piece of data was deleted
        for key in (self.gmf1_key, self.gmf2_key, self.vuln_key):
            self.assertFalse(self.client.exists(key))

        # make sure the job was deleted from CURRENT_JOBS
        self.assertFalse(
            self.client.sismember(tokens.CURRENT_JOBS, self.test_job))

    def test_gc_dataless_job(self):
        """
        Test that :py:function:`openquake.kvs.cache_gc` returns 0 (to indicate
        that the job existed but there was nothing to delete).

        The job key should key should be removed from CURRENT_JOBS.
        """
        self.assertTrue(
            self.client.sismember(tokens.CURRENT_JOBS, self.dataless_job))

        result = kvs.cache_gc(self.dataless_job)

        self.assertEqual(0, result)

        # make sure the job was deleted from CURRENT_JOBS
        self.assertFalse(
            self.client.sismember(tokens.CURRENT_JOBS, self.dataless_job))

    def test_gc_nonexistent_job(self):
        """
        If we try to run garbage collection on a nonexistent job, the result of
        :py:function:`openquake.kvs.cache_gc` should be None.
        """
        nonexist_job = tokens.JOB_KEY_FMT % '1234nonexistent'

        result = kvs.cache_gc(nonexist_job)

        self.assertTrue(result is None)

    def test_gc_raises_when_redis_delete_fails(self):
        """
        If Redis fails to delete data for the given job, a RuntimeError should
        raised.

        If a Redis 'delete' does not succeed, the method will return False. The
        'delete' method will be mocked in this test to produce such an error.
        """
        with mock.patch('redis.client.Redis.delete') as delete_mock:
            delete_mock.return_value = False

            self.assertRaises(RuntimeError, kvs.cache_gc, self.test_job)
