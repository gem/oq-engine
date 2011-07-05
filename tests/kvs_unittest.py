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


import os
import time
import unittest

from openquake import java
from openquake import logs
from openquake import kvs
from openquake import settings
from openquake import shapes
from tests.utils import helpers
from openquake import settings

from openquake.kvs import reader
from openquake.kvs import tokens
from openquake.parser import vulnerability

from openquake.output import hazard as hazard_output
from openquake.parser import hazard as hazard_parser

LOG = logs.LOG

TEST_FILE = "nrml_test_result.xml"

EMPTY_MODEL = '{"modelName":"","hcRepList":[],"endBranchLabels":[]}'

read_one_line = lambda path: open(path, 'r').readline().strip('\n')

ONE_CURVE_MODEL = read_one_line(helpers.get_data_path('one-curve-model.json'))
MULTIPLE_CURVES_ONE_BRANCH = \
    read_one_line(helpers.get_data_path('multi-curves-one-branch.json'))
MULTIPLE_CURVES_MULTIPLE_BRANCHES = \
    read_one_line(helpers.get_data_path('multi-curves-multi-branches.json'))

JOB_KEY_FMT = '::JOB::%s::'


class KVSTestCase(unittest.TestCase):

    def setUp(self):
        # starting the jvm...
        print "About to start the jvm..."
        jpype = java.jvm()
        java_class = jpype.JClass("org.gem.engine.hazard.redis.Cache")
        print ("Not dead yet, and found the class...")
        self.java_client = java_class(settings.KVS_HOST, settings.KVS_PORT)

        self.python_client = kvs.get_client(binary=False)

        self.reader = reader.Reader(self.python_client)
        self._delete_test_file()

    def tearDown(self):
        self._delete_test_file()
        self.python_client.flushdb()

    def _delete_test_file(self):
        try:
            os.remove(os.path.join(helpers.DATA_DIR, TEST_FILE))
        except OSError:
            pass

    def test_can_wrap_the_java_client(self):
        self.java_client.set("KEY", "VALUE")
        result = self.java_client.get("KEY")
        self.assertEqual("VALUE", self.java_client.get("KEY"))

    def test_can_write_in_java_and_read_in_python(self):
        self.java_client.set("KEY", "VALUE")
        self.assertEqual("VALUE", self.python_client.get("KEY"))

    def test_can_write_in_python_and_read_in_java(self):
        self.python_client.set("KEY", "VALUE")
        self.assertEqual("VALUE", self.java_client.get("KEY"))

    def test_an_empty_model_produces_an_empty_curve_set(self):
        self.python_client.set("KEY", EMPTY_MODEL)
        self.assertEqual(0, len(self.reader.as_curve("KEY")))

    def test_an_error_is_raised_if_no_model_cached(self):
        self.assertRaises(ValueError, self.reader.as_curve, "KEY")

    def test_reads_one_curve(self):
        self.python_client.set("KEY", ONE_CURVE_MODEL)
        curves = self.reader.as_curve("KEY")

        self.assertEqual(1, len(curves))
        self.assertEqual(shapes.Curve(
                ((1.0, 0.1), (2.0, 0.2), (3.0, 0.3))), curves[0])

    def test_reads_multiple_curves_in_one_branch(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_ONE_BRANCH)
        curves = self.reader.as_curve("KEY")

        self.assertEqual(2, len(curves))
        self.assertEqual(shapes.Curve(
                ((1.0, 5.1), (2.0, 5.2), (3.0, 5.3))), curves[0])

        self.assertEqual(shapes.Curve(
                ((1.0, 6.1), (2.0, 6.2), (3.0, 6.3))), curves[1])

    def test_reads_multiple_curves_in_multiple_branches(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_MULTIPLE_BRANCHES)
        curves = self.reader.as_curve("KEY")

        self.assertEqual(2, len(curves))
        self.assertEqual(shapes.Curve(
                ((1.0, 1.8), (2.0, 2.8), (3.0, 3.8))), curves[0])

        self.assertEqual(shapes.Curve(
                ((1.0, 1.5), (2.0, 2.5), (3.0, 3.5))), curves[1])

    def test_end_to_end_curves_reading(self):
        # Hazard object model serialization in JSON is tested in the Java side
        self.java_client.set("KEY", ONE_CURVE_MODEL)

        time.sleep(0.3)

        curves = self.reader.as_curve("KEY")

        self.assertEqual(1, len(curves))
        self.assertEqual(shapes.Curve(
                ((1.0, 0.1), (2.0, 0.2), (3.0, 0.3))), curves[0])

    def test_an_empty_model_produces_an_empty_curve_set_nrml(self):
        self.python_client.set("KEY", EMPTY_MODEL)
        self.assertEqual(0, len(self.reader.for_nrml("KEY")))

    def test_an_error_is_raised_if_no_model_cached_nrml(self):
        self.assertRaises(ValueError, self.reader.for_nrml, "KEY")

    def test_reads_one_curve_nrml(self):
        self.python_client.set("KEY", ONE_CURVE_MODEL)
        nrmls = self.reader.for_nrml("KEY")

        data = {shapes.Site(2.0, 1.0): {
                    "IMT": "IMT",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label",
                    "IMLValues": [1.0, 2.0, 3.0],
                    "Values": [0.1, 0.2, 0.3]}}

        self.assertEqual(1, len(nrmls.items()))
        self.assertEquals(data, nrmls)

    def test_reads_multiple_curves_in_one_branch_nrml(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_ONE_BRANCH)
        nrmls = self.reader.for_nrml("KEY")

        data = {shapes.Site(2.0, 1.0): {
                    "IMT": "PGA",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label",
                    "IMLValues": [1.0, 2.0, 3.0],
                    "Values": [5.1, 5.2, 5.3]},
                shapes.Site(4.0, 4.0): {
                    "IMT": "PGA",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label",
                    "IMLValues": [1.0, 2.0, 3.0],
                    "Values": [6.1, 6.2, 6.3]}}

        self.assertEqual(2, len(nrmls.items()))
        self.assertEquals(data, nrmls)

    def test_reads_multiple_curves_in_multiple_branches_nrml(self):
        self.python_client.set("KEY", MULTIPLE_CURVES_MULTIPLE_BRANCHES)
        nrmls = self.reader.for_nrml("KEY")

        data = {shapes.Site(4.0, 4.0): {
                    "IMT": "PGA",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label1",
                    "IMLValues": [1.0, 2.0, 3.0],
                    "Values": [1.8, 2.8, 3.8]},
                shapes.Site(4.0, 1.0): {
                    "IMT": "PGA",
                    "IDmodel": "FIXED",
                    "timeSpanDuration": 50.0,
                    "endBranchLabel": "label2",
                    "IMLValues": [1.0, 2.0, 3.0],
                    "Values": [1.5, 2.5, 3.5]}}

        self.assertEqual(2, len(nrmls.items()))
        self.assertEquals(data, nrmls)


class TokensTestCase(unittest.TestCase):

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

    def test_next_job_key(self):
        """
        Test the generation of job keys using
        :py:function:`openquake.kvs.tokens.next_job_key`.
        """

        job_key_1 = JOB_KEY_FMT % 1
        job_key_2 = JOB_KEY_FMT % 2
        
        kvs.get_client().delete(tokens.NEXT_JOB_ID)

        # it should be empty to start with
        self.assertTrue(kvs.get(tokens.NEXT_JOB_ID) is None)

        self.assertEqual(job_key_1, tokens.next_job_key())

        # verify that the IDs are incrementing properly
        self.assertEqual(job_key_2, tokens.next_job_key())

        # now verify that these keys have been added to the CURRENT_JOBS set
        self.assertTrue(self.client.sismember(tokens.CURRENT_JOBS, job_key_1))
        self.assertTrue(self.client.sismember(tokens.CURRENT_JOBS, job_key_2))

    def test_next_job_key_raises_on_duplicate(self):
        """
        Test that :py:function:`openquake.kvs.tokens.next_job_key` raises an
        AssertionError if there is somehow there is a duplicate job key.
        """
        self.assertEqual(0, len(self.client.smembers(tokens.CURRENT_JOBS)))

        self.client.sadd(tokens.CURRENT_JOBS, JOB_KEY_FMT % 1)

        self.assertRaises(AssertionError, tokens.next_job_key)

    def test_current_jobs(self):
        """
        Test the retrieval of the current jobs from the CURRENT_JOBS set.
        Exercises :py:function:`openquake.kvs.tokens.current_jobs`.
        """
        self.assertFalse(self.client.exists(tokens.CURRENT_JOBS))

        # load some sample jobs into the CURRENT_JOBS set
        jobs = [JOB_KEY_FMT % x for x in range(1, 4)]

        for job in jobs:
            self.client.sadd(tokens.CURRENT_JOBS, job)

        current_jobs = tokens.current_jobs()

        self.assertEqual(jobs, current_jobs)


class GarbageCollectionTestCase(unittest.TestCase):
    """
    Tests for KVS garbage collection.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = kvs.get_client()

        cls.client.delete(tokens.CURRENT_JOBS)
        cls.client.delete(tokens.NEXT_JOB_ID)

        cls.test_job = tokens.next_job_key()

        # create some keys to hold fake data for test_job
        cls.gmf1_key = tokens.gmfs_key(cls.test_job, 0, 0)
        cls.gmf2_key = tokens.gmfs_key(cls.test_job, 0, 1)
        cls.vuln_key = tokens.vuln_key(cls.test_job)

        # now create the fake data for test_job
        cls.client.set(cls.gmf1_key, 'fake gmf data 1')
        cls.client.set(cls.gmf2_key, 'fake gmf data 2')
        cls.client.set(cls.vuln_key, 'fake vuln curve data')

        # this job will have no data
        cls.dataless_job = tokens.next_job_key()


    @classmethod
    def tearDownClass(cls):
        cls.client.delete(tokens.CURRENT_JOBS)
        cls.client.delete(tokens.NEXT_JOB_ID)

    def test_gc_some_job_data(self):
        """
        Test that all job data is cleared and the job key is removed from
        CURRENT_JOBS.
        """
        keys_exist = lambda: [self.client.exists(x) for x in \
            (self.gmf1_key, self.gmf2_key, self.vuln_key)]

        self.assertTrue(all(keys_exist()))

        result = kvs.cache_gc(self.test_job)

        # 3 things be deleted
        self.assertEqual(3, result)

        for x in keys_exist():
            self.assertFalse(x)

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
        nonexist_job = JOB_KEY_FMT % '1234nonexistent'

        result = kvs.cache_gc(nonexist_job)

        self.assertTrue(result is None)

        job_key_fmt = '::JOB::%s::'

        self.assertEqual(job_key_fmt % 1, tokens.next_job_key())

        # verify that the IDs are incrementing properly
        self.assertEqual(job_key_fmt % 2, tokens.next_job_key())
