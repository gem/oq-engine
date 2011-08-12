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

from openquake import java
from openquake import kvs
from openquake import flags
from openquake.job import Job, LOG
from openquake.job.mixins import Mixin
from openquake.risk.job import general
from openquake.kvs import tokens
from openquake.risk.job.probabilistic import ProbabilisticEventMixin
from openquake.risk.job.classical_psha import ClassicalPSHABasedMixin
from tests.utils import helpers
from tests.utils.helpers import patch


CONFIG_FILE = "config.gem"
CONFIG_WITH_INCLUDES = "config_with_includes.gem"
HAZARD_ONLY = "hazard-config.gem"

REGION_EXPOSURE_TEST_FILE = "ExposurePortfolioFile-helpers.region"
BLOCK_SPLIT_TEST_FILE = "block_split.gem"
REGION_TEST_FILE = "small.region"

FLAGS = flags.FLAGS


class JobTestCase(unittest.TestCase):

    def setUp(self):
        client = kvs.get_client()

        # Delete managed job id info so we can predict the job key
        # which will be allocated for us
        # Playing with NEXT_JOB_ID can lead to unexpected behaviour in other
        # tests, see comment in tearDown
        client.delete(tokens.CURRENT_JOBS)
        client.delete(tokens.NEXT_JOB_ID)

        self.generated_files = []
        self.job = helpers.job_from_file(helpers.get_data_path(CONFIG_FILE))
        self.job_with_includes = \
            helpers.job_from_file(helpers.get_data_path(CONFIG_WITH_INCLUDES))

        self.generated_files.append(self.job.super_config_path)
        self.generated_files.append(self.job_with_includes.super_config_path)

    def tearDown(self):
        for cfg in self.generated_files:
            try:
                os.remove(cfg)
            except OSError:
                pass

        # Playing with NEXT_JOB_ID breaks the uniqueness of the job_ids,
        # causing failures of tests in kvs_unittest.py, if they run after this
        # To avoid this we garbage collect job we know we used in this test
        # case.
        kvs.cache_gc('::JOB::1::')
        kvs.cache_gc('::JOB::2::')

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
        Job._Job__defaults = good_defaults

    def test_job_has_the_correct_sections(self):
        self.assertEqual(["RISK", "HAZARD", "general"], self.job.sections)
        self.assertEqual(self.job.sections, self.job_with_includes.sections)

    def test_job_with_only_hazard_config_only_has_hazard_section(self):
        FLAGS.include_defaults = False
        job_with_only_hazard = \
            helpers.job_from_file(helpers.get_data_path(HAZARD_ONLY))
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
        with Mixin(self.job, general.RiskJobMixin):
            self.assertTrue(
                general.RiskJobMixin in self.job.__class__.__bases__)

        with Mixin(self.job, ClassicalPSHABasedMixin):
            self.assertTrue(
                ClassicalPSHABasedMixin in self.job.__class__.__bases__)

    def test_job_mixes_in_properly(self):
        with Mixin(self.job, general.RiskJobMixin):
            self.assertTrue(
                general.RiskJobMixin in self.job.__class__.__bases__)

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

        self.assertEqual(1, Job({}).job_id)

    def test_can_store_and_read_jobs_from_kvs(self):
        self.job = helpers.job_from_file(
            os.path.join(helpers.DATA_DIR, CONFIG_FILE))
        self.generated_files.append(self.job.super_config_path)
        self.assertEqual(self.job, Job.from_kvs(self.job.job_id))

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

        with patch(haz_exec_path) as haz_exec:
            haz_exec.return_value = []

            with patch(risk_exec_path) as risk_exec:
                risk_exec.return_value = []

                with patch('openquake.job.Job.cleanup') as clean_mock:
                    self.job.launch()

                    self.assertEqual(1, clean_mock.call_count)

    def test_cleanup_calls_cache_gc(self):
        """
        This ensures that the job cleanup method
        :py:method:`openquake.job.Job.cleanup` properly initiates KVS
        garbage collection.
        """
        expected_args = (['python', 'bin/cache_gc.py', '--job=1'], )

        with patch('subprocess.Popen') as popen_mock:
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

    def test_job_init_assigns_unique_id(self):
        """
        This test ensures that unique job IDs are assigned to each Job object.
        """
        job1 = Job({})
        job2 = Job({})

        self.assertTrue(job1.job_id is not None)
        self.assertTrue(job2.job_id is not None)

        self.assertNotEqual(job1.job_id, job2.job_id)

    def test_job_sets_job_id_in_java_logging(self):
        """
        When a Job is instantiated, a 'job_id' parameter should be set in
        'org.apache.log4j.MDC'. This is used by the java logging system to
        tag log messages with the job_id.
        """
        mdc = java.jclass('MDC')

        # allocate a job_id for us:
        test_job_1 = Job({})

        self.assertEqual(test_job_1.job_id, mdc.get('job_id'))

        # specify a job ID:
        job_id = 7
        test_job_2 = Job({}, job_id=job_id)

        self.assertEqual(job_id, mdc.get('job_id'))
