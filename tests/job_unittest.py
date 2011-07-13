# -*- coding: utf-8 -*-

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

from openquake import shapes
from tests.utils import helpers
from openquake import job
from openquake import kvs
from openquake import flags
from openquake.job import Job, LOG
from openquake.job import config
from openquake.job.mixins import Mixin
from openquake.kvs import tokens
from openquake.risk.job.general import RiskJobMixin
from openquake.risk.job.probabilistic import ProbabilisticEventMixin
from openquake.risk.job.classical_psha import ClassicalPSHABasedMixin


CONFIG_FILE = "config.gem"
CONFIG_WITH_INCLUDES = "config_with_includes.gem"
HAZARD_ONLY = "hazard-config.gem"

SITE = shapes.Site(1.0, 1.0)
EXPOSURE_TEST_FILE = "exposure-portfolio.xml"
REGION_EXPOSURE_TEST_FILE = "ExposurePortfolioFile-helpers.region"
BLOCK_SPLIT_TEST_FILE = "block_split.gem"
REGION_TEST_FILE = "small.region"

FLAGS = flags.FLAGS


class JobTestCase(unittest.TestCase):

    def setUp(self):
        client = kvs.get_client()

        # delete managed job id info so we can predict the job key
        # which will be allocated for us
        client.delete(tokens.CURRENT_JOBS)
        client.delete(tokens.NEXT_JOB_ID)

        self.generated_files = []
        self.job = Job.from_file(helpers.get_data_path(CONFIG_FILE), 'xml')
        self.job_with_includes = \
            Job.from_file(helpers.get_data_path(CONFIG_WITH_INCLUDES), 'xml')

        self.generated_files.append(self.job.super_config_path)
        self.generated_files.append(self.job_with_includes.super_config_path)

    def tearDown(self):
        for cfg in self.generated_files:
            try:
                os.remove(cfg)
            except OSError:
                pass

    def test_logs_a_warning_if_none_of_the_default_configs_exist(self):

        class call_logger(object):

            def __init__(self, method):
                self.called = False
                self.method = method

            def __call__(self, *args, **kwargs):
                try:
                    return self.method(*args, **kwargs)
                finally:
                    self.called = True

        good_defaults = Job._Job__defaults
        Job._Job__defaults = ["/tmp/sbfalds"]
        LOG.warning = call_logger(LOG.warning)
        self.assertFalse(LOG.warning.called)
        Job.default_configs()
        self.assertTrue(LOG.warning.called)
        good_defaults = Job._Job__defaults
        Job.__defaults = good_defaults

    def test_job_has_the_correct_sections(self):
        self.assertEqual(["RISK", "HAZARD", "general"], self.job.sections)
        self.assertEqual(self.job.sections, self.job_with_includes.sections)

    def test_job_with_only_hazard_config_only_has_hazard_section(self):
        FLAGS.include_defaults = False
        job_with_only_hazard = \
            Job.from_file(helpers.get_data_path(HAZARD_ONLY), 'xml')
        self.assertEqual(["HAZARD"], job_with_only_hazard.sections)
        FLAGS.include_defaults = True

    def test_job_writes_to_super_config(self):
        for each_job in [self.job, self.job_with_includes]:
            self.assertTrue(os.path.isfile(each_job.super_config_path))

    def test_configuration_is_the_same_no_matter_which_way_its_provided(self):
        sha_from_file_key = lambda params, key: params[key].split('!')[1]

        # A unique job key is prepended to these file hashes
        # to enable garabage collection.
        # Thus, we have to do a little voodoo to make this test work.
        src_model = 'SOURCE_MODEL_LOGIC_TREE_FILE'
        gmpe = 'GMPE_LOGIC_TREE_FILE'

        job1_src_model_sha = sha_from_file_key(self.job.params, src_model)
        job2_src_model_sha = sha_from_file_key(
            self.job_with_includes.params, src_model)
        self.assertEqual(job1_src_model_sha, job2_src_model_sha)

        del self.job.params[src_model]
        del self.job_with_includes.params[src_model]

        job1_gmpe_sha = sha_from_file_key(self.job.params, gmpe)
        job2_gmpe_sha = sha_from_file_key(self.job_with_includes.params, gmpe)
        self.assertEqual(job1_gmpe_sha, job2_gmpe_sha)

        del self.job.params[gmpe]
        del self.job_with_includes.params[gmpe]

        self.assertEqual(self.job.params, self.job_with_includes.params)

    def test_classical_psha_based_job_mixes_in_properly(self):
        with Mixin(self.job, RiskJobMixin):
            self.assertTrue(RiskJobMixin in self.job.__class__.__bases__)

        with Mixin(self.job, ClassicalPSHABasedMixin):
            self.assertTrue(
                ClassicalPSHABasedMixin in self.job.__class__.__bases__)

    def test_job_mixes_in_properly(self):
        with Mixin(self.job, RiskJobMixin):
            self.assertTrue(RiskJobMixin in self.job.__class__.__bases__)
            self.assertTrue(
                ProbabilisticEventMixin in self.job.__class__.__bases__)

        with Mixin(self.job, ProbabilisticEventMixin):
            self.assertTrue(
                ProbabilisticEventMixin in self.job.__class__.__bases__)

    def test_a_job_has_an_identifier(self):
        """
        Test that the :py:class:`openquake.job.Job` constructor automatically
        assigns a proper job ID.
        """
        client = kvs.get_client()

        client.delete(tokens.CURRENT_JOBS)
        client.delete(tokens.NEXT_JOB_ID)

        self.assertEqual(tokens.JOB_KEY_FMT % 1, Job({}).job_id)

    def test_can_store_and_read_jobs_from_kvs(self):
        self.job = Job.from_file(
            os.path.join(helpers.DATA_DIR, CONFIG_FILE), 'xml')
        self.generated_files.append(self.job.super_config_path)
        self.assertEqual(self.job, Job.from_kvs(self.job.id))

    def test_prepares_blocks_using_the_exposure(self):
        a_job = Job({config.EXPOSURE: os.path.join(helpers.SCHEMA_EXAMPLES_DIR,
                                            EXPOSURE_TEST_FILE)})
        a_job._partition()
        blocks_keys = a_job.blocks_keys

        expected_block = job.Block((shapes.Site(9.15000, 45.16667),
            shapes.Site(9.15333, 45.12200), shapes.Site(9.14777, 45.17999)))

        self.assertEqual(1, len(blocks_keys))
        self.assertEqual(expected_block, job.Block.from_kvs(blocks_keys[0]))

    def test_prepares_blocks_using_the_exposure_and_filtering(self):
        args = {
            config.EXPOSURE: os.path.join(
                helpers.SCHEMA_EXAMPLES_DIR, EXPOSURE_TEST_FILE),
            config.INPUT_REGION: helpers.get_data_path(
            REGION_EXPOSURE_TEST_FILE)}
        a_job = Job(args)
        self.generated_files.append(a_job.super_config_path)
        a_job._partition()
        blocks_keys = a_job.blocks_keys

        expected_block = job.Block((shapes.Site(9.15, 45.16667),
                                    shapes.Site(9.15333, 45.122),
                                    shapes.Site(9.14777, 45.17999)))

        self.assertEqual(1, len(blocks_keys))
        self.assertEqual(expected_block, job.Block.from_kvs(blocks_keys[0]))

    def test_with_no_partition_we_just_process_a_single_block(self):
        job.SITES_PER_BLOCK = 1

        # test exposure has 6 assets
        a_job = Job({config.EXPOSURE: os.path.join(
                helpers.SCHEMA_EXAMPLES_DIR, EXPOSURE_TEST_FILE)})

        self.generated_files.append(a_job.super_config_path)

        a_job._partition()
        blocks_keys = a_job.blocks_keys

        # but we have 1 block instead of 6
        self.assertEqual(1, len(blocks_keys))

    def test_job_calls_cleanup(self):
        """
        This test ensures that jobs call
        :py:method:`openquake.job.Job.cleanup`.

        The test job file defines an Event-Based calculation; the Event-Based
        mixins are mocked in this test (so the entire calculation isn't
        actually run).
        """
        haz_exec_path = 'openquake.hazard.opensha.EventBasedMixin.execute'
        risk_exec_path = \
            'openquake.risk.job.probabilistic.ProbabilisticEventMixin.execute'

        with mock.patch('openquake.job.Job._partition'):
            with mock.patch(haz_exec_path) as haz_exec:
                haz_exec.return_value = []

                with mock.patch(risk_exec_path) as risk_exec:
                    risk_exec.return_value = []

                    with mock.patch('openquake.job.Job.cleanup') as clean_mock:
                        self.job.launch()

                        self.assertEqual(1, clean_mock.call_count)

    def test_cleanup_calls_cache_gc(self):
        """
        This ensures that the job cleanup method
        :py:method:`openquake.job.Job.cleanup` properly initiates KVS
        garbage collection.
        """
        expected_args = (['python', 'bin/cache_gc.py', '--job=1'],)

        with mock.patch('subprocess.Popen') as popen_mock:
            self.job.cleanup()

            self.assertEqual(1, popen_mock.call_count)

            actual_args, actual_kwargs = popen_mock.call_args

            self.assertEqual(expected_args, actual_args)

            # testing the kwargs is slight more complex, since stdout is
            # directed to /dev/null
            popen_stdout = actual_kwargs['stdout']
            self.assertTrue(isinstance(popen_stdout, file))
            self.assertEqual('/dev/null', popen_stdout.name)
            self.assertEqual('w', popen_stdout.mode)

            self.assertEqual(os.environ, actual_kwargs['env'])

    def test_cleanup_raises_on_bad_job_id(self):
        """
        If the ID of a job is somehow corrupted, verify that a RuntimeError is
        raised by :py:method:`openquake.job.Job.cleanup`.
        """
        self.job.job_id = 'this-is-invalid'

        self.assertRaises(RuntimeError, self.job.cleanup)

    def test_job_init_assigns_unique_id(self):
        """
        This test ensures that unique job IDs are assigned to each Job object.
        """
        job1 = Job({})
        job2 = Job({})

        self.assertTrue(job1.job_id is not None)
        self.assertTrue(job2.job_id is not None)

        self.assertNotEqual(job1.job_id, job2.job_id)


class BlockTestCase(unittest.TestCase):

    def test_a_block_has_a_unique_id(self):
        self.assertTrue(job.Block(()).id)
        self.assertTrue(job.Block(()).id != job.Block(()).id)

    def test_can_serialize_a_block_into_kvs(self):
        block = job.Block((SITE, SITE))
        block.to_kvs()

        self.assertEqual(block, job.Block.from_kvs(block.id))


class BlockSplitterTestCase(unittest.TestCase):

    def setUp(self):
        self.splitter = None

    def test_an_empty_set_produces_no_blocks(self):
        self.splitter = job.BlockSplitter(())
        self._assert_number_of_blocks_is(0)

    def test_splits_the_set_into_a_single_block(self):
        self.splitter = job.BlockSplitter((SITE, ), 3)
        self._assert_number_of_blocks_is(1)

        self.splitter = job.BlockSplitter((SITE, SITE), 3)
        self._assert_number_of_blocks_is(1)

        self.splitter = job.BlockSplitter((SITE, SITE, SITE), 3)
        self._assert_number_of_blocks_is(1)

    def test_splits_the_set_into_multiple_blocks(self):
        self.splitter = job.BlockSplitter((SITE, SITE), 1)
        self._assert_number_of_blocks_is(2)

        self.splitter = job.BlockSplitter((SITE, SITE, SITE), 2)
        self._assert_number_of_blocks_is(2)

    def test_generates_the_correct_blocks(self):
        self.splitter = job.BlockSplitter((SITE, SITE, SITE), 3)
        expected_blocks = (job.Block((SITE, SITE, SITE)), )
        self._assert_blocks_are(expected_blocks)

        self.splitter = job.BlockSplitter((SITE, SITE, SITE), 2)
        expected_blocks = (job.Block((SITE, SITE)), job.Block((SITE, )))
        self._assert_blocks_are(expected_blocks)

    def test_splitting_with_region_intersection(self):
        region_constraint = shapes.RegionConstraint.from_simple(
                (0.0, 0.0), (2.0, 2.0))

        sites = (shapes.Site(1.0, 1.0), shapes.Site(1.5, 1.5),
            shapes.Site(2.0, 2.0), shapes.Site(3.0, 3.0))

        expected_blocks = (
                job.Block((shapes.Site(1.0, 1.0), shapes.Site(1.5, 1.5))),
                job.Block((shapes.Site(2.0, 2.0), )))

        self.splitter = job.BlockSplitter(sites, 2,
                                            constraint=region_constraint)
        self._assert_blocks_are(expected_blocks)

    def _assert_blocks_are(self, expected_blocks):
        for idx, block in enumerate(self.splitter):
            self.assertEqual(expected_blocks[idx], block)

    def _assert_number_of_blocks_is(self, number):
        counter = 0

        for _block in self.splitter:
            counter += 1

        self.assertEqual(number, counter)
