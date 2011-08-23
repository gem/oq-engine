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
import sqlalchemy
import unittest

from openquake import kvs
from openquake import flags
from openquake import shapes
from openquake.job import Job, LOG, config, prepare_job, run_job
from openquake.db.alchemy.db_utils import get_db_session
from openquake.db.alchemy.models import OqJob
from openquake.job.mixins import Mixin
from openquake.risk.job import general
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


def _toCoordList(polygon):
    session = get_db_session("reslt", "writer")

    pts = []

    # postgis -> lon/lat -> config lat/lon, skip the closing point
    for c in polygon.coords(session)[0][:-1]:
        pts.append("%.2f" % c[1])
        pts.append("%.2f" % c[0])

    return ", ".join(pts)


class JobTestCase(unittest.TestCase):

    def setUp(self):
        client = kvs.get_client()

        # Delete managed job id info so we can predict the job key
        # which will be allocated for us
        client.delete(kvs.tokens.CURRENT_JOBS)

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
        try:
            job_with_only_hazard = \
                helpers.job_from_file(helpers.get_data_path(HAZARD_ONLY))
            self.assertEqual(["HAZARD"], job_with_only_hazard.sections)
        finally:
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

    def test_can_store_and_read_jobs_from_kvs(self):
        self.job = helpers.job_from_file(
            os.path.join(helpers.DATA_DIR, CONFIG_FILE))
        self.generated_files.append(self.job.super_config_path)
        self.assertEqual(self.job, Job.from_kvs(self.job.job_id))
        helpers.cleanup_loggers()

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
        expected_args = (['python', 'bin/cache_gc.py',
                          '--job=%d' % self.job.job_id], )

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


class JobDbRecordTestCase(unittest.TestCase):

    def setUp(self):
        self.job = None

    def tearDown(self):
        try:
            if self.job:
                os.remove(self.job.super_config_path)
        except OSError:
            pass

    def test_job_db_record_for_output_type_db(self):
        self.job = Job.from_file(helpers.get_data_path(CONFIG_FILE), 'db')

        session = get_db_session("uiapi", "writer")

        session.query(OqJob).filter(OqJob.id == self.job.job_id).one()

    def test_job_db_record_for_output_type_xml(self):
        self.job = Job.from_file(helpers.get_data_path(CONFIG_FILE), 'xml')

        session = get_db_session("uiapi", "writer")

        session.query(OqJob).filter(OqJob.id == self.job.job_id).one()

    def test_set_status(self):
        self.job = Job.from_file(helpers.get_data_path(CONFIG_FILE), 'db')

        session = get_db_session("reslt", "writer")

        status = 'running'
        self.job.set_status(status)

        job = session.query(OqJob).filter(OqJob.id == self.job.job_id).one()

        self.assertEqual(status, job.status)

    def test_get_status_from_db(self):
        self.job = Job.from_file(helpers.get_data_path(CONFIG_FILE), 'db')

        session = get_db_session("reslt", "writer")
        session.query(OqJob).update({'status': 'failed'})
        session.commit()
        self.assertEqual(Job.get_status_from_db(self.job.job_id), 'failed')
        session.query(OqJob).update({'status': 'running'})
        session.commit()
        self.assertEqual(Job.get_status_from_db(self.job.job_id), 'running')

    def test_is_job_completed(self):
        job_id = Job.from_file(helpers.get_data_path(CONFIG_FILE), 'db').job_id
        session = get_db_session("reslt", "writer")
        pairs = [('pending', False), ('running', False),
                 ('succeeded', True), ('failed', True)]
        for status, is_completed in pairs:
            session.query(OqJob).update({'status': status})
            session.commit()
            self.assertEqual(Job.is_job_completed(job_id), is_completed)


class PrepareJobTestCase(unittest.TestCase, helpers.DbTestMixin):
    maxDiff = None

    """
    Unit tests for the prepare_job helper function, which creates a new
    job entry with the associated parameters.

    Test data is a trimmed-down version of smoketest config files

    As a side-effect, also tests that the inserted record satisfied
    the DB constraints.
    """
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)

    def assertFieldsEqual(self, expected, params):
        got_params = dict((k, getattr(params, k)) for k in expected.keys())

        self.assertEquals(expected, got_params)

    def test_prepare_classical_job(self):
        params = {
            'CALCULATION_MODE': 'Classical',
            'POES_HAZARD_MAPS': '0.01 0.1',
            'INTENSITY_MEASURE_TYPE': 'PGA',
            'REGION_VERTEX': '37.90, -121.90, 37.90, -121.60, 37.50, -121.60',
            'MINIMUM_MAGNITUDE': '5.0',
            'INVESTIGATION_TIME': '50.0',
            'TREAT_GRID_SOURCE_AS': 'Point Sources',
            'INCLUDE_AREA_SOURCES': 'true',
            'TREAT_AREA_SOURCE_AS': 'Point Sources',
            'QUANTILE_LEVELS': '0.25 0.50',
            'INTENSITY_MEASURE_LEVELS': '0.005, 0.007, 0.0098, 0.0137, 0.0192',
            'GROUND_MOTION_CORRELATION': 'true',
            'GMPE_TRUNCATION_TYPE': '2 Sided',
            'STANDARD_DEVIATION_TYPE': 'Total',
            'MAXIMUM_DISTANCE': '200.0',
            'NUMBER_OF_LOGIC_TREE_SAMPLES': '2',
            'REGION_GRID_SPACING': '0.1',
            'PERIOD': '0.0',
            'AGGREGATE_LOSS_CURVE': '1',
            'NUMBER_OF_SEISMICITY_HISTORIES': '1',
            'INCLUDE_FAULT_SOURCE': 'true',
            'FAULT_SURFACE_DISCRETIZATION': '1.0',
            'REFERENCE_VS30_VALUE': '760.0',
            'COMPONENT': 'Average Horizontal (GMRotI50)',
            'CONDITIONAL_LOSS_POE': '0.01',
            'TRUNCATION_LEVEL': '3',
            'COMPUTE_MEAN_HAZARD_CURVE': 'true',
            'AREA_SOURCE_DISCRETIZATION': '0.1',
        }

        self.job = prepare_job(params)
        self.assertEquals(params['REGION_VERTEX'],
                          _toCoordList(self.job.oq_params.region))
        self.assertFieldsEqual(
            {'job_type': 'classical',
             'upload': None,
             'region_grid_spacing': 0.1,
             'min_magnitude': 5.0,
             'investigation_time': 50.0,
             'component': 'gmroti50',
             'imt': 'pga',
             'period': None,
             'truncation_type': 'twosided',
             'truncation_level': 3.0,
             'reference_vs30_value': 760.0,
             'imls': [0.005, 0.007, 0.0098, 0.0137, 0.0192],
             'poes': [0.01, 0.1],
             'realizations': 2,
             'histories': None,
             'gm_correlated': None,
             }, self.job.oq_params)

    def test_prepare_deterministic_job(self):
        params = {
            'CALCULATION_MODE': 'Deterministic',
            'GMPE_MODEL_NAME': 'BA_2008_AttenRel',
            'GMF_RANDOM_SEED': '3',
            'RUPTURE_SURFACE_DISCRETIZATION': '0.1',
            'INTENSITY_MEASURE_TYPE': 'PGA',
            'REFERENCE_VS30_VALUE': '759.0',
            'COMPONENT': 'Average Horizontal (GMRotI50)',
            'REGION_GRID_SPACING': '0.02',
            'REGION_VERTEX': '34.07, -118.25, 34.07, -118.22, 34.04, -118.22',
            'PERIOD': '0.0',
            'NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS': '5',
            'TRUNCATION_LEVEL': '3',
            'GMPE_TRUNCATION_TYPE': '1 Sided',
            'GROUND_MOTION_CORRELATION': 'true',
        }

        self.job = prepare_job(params)
        self.assertEquals(params['REGION_VERTEX'],
                          _toCoordList(self.job.oq_params.region))
        self.assertFieldsEqual(
            {'job_type': 'deterministic',
             'upload': None,
             'region_grid_spacing': 0.02,
             'min_magnitude': None,
             'investigation_time': None,
             'component': 'gmroti50',
             'imt': 'pga',
             'period': None,
             'truncation_type': 'onesided',
             'truncation_level': 3.0,
             'reference_vs30_value': 759.0,
             'imls': None,
             'poes': None,
             'realizations': None,
             'histories': None,
             'gm_correlated': True,
             }, self.job.oq_params)

    def test_prepare_event_based_job(self):
        params = {
            'CALCULATION_MODE': 'Event Based',
            'POES_HAZARD_MAPS': '0.01 0.10',
            'INTENSITY_MEASURE_TYPE': 'SA',
            'REGION_VERTEX': '33.88, -118.30, 33.88, -118.06, 33.76, -118.06',
            'INCLUDE_GRID_SOURCES': 'false',
            'INCLUDE_SUBDUCTION_FAULT_SOURCE': 'false',
            'RUPTURE_ASPECT_RATIO': '1.5',
            'MINIMUM_MAGNITUDE': '5.0',
            'SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA': '0.0',
            'INVESTIGATION_TIME': '50.0',
            'TREAT_GRID_SOURCE_AS': 'Point Sources',
            'INCLUDE_AREA_SOURCES': 'true',
            'TREAT_AREA_SOURCE_AS': 'Point Sources',
            'QUANTILE_LEVELS': '0.25 0.50',
            'INTENSITY_MEASURE_LEVELS': '0.005, 0.007, 0.0098, 0.0137, 0.0192',
            'GROUND_MOTION_CORRELATION': 'false',
            'GMPE_TRUNCATION_TYPE': 'None',
            'STANDARD_DEVIATION_TYPE': 'Total',
            'SUBDUCTION_FAULT_RUPTURE_OFFSET': '10.0',
            'RISK_CELL_SIZE': '0.0005',
            'MAXIMUM_DISTANCE': '200.0',
            'NUMBER_OF_LOGIC_TREE_SAMPLES': '5',
            'REGION_GRID_SPACING': '0.02',
            'PERIOD': '1.0',
            'AGGREGATE_LOSS_CURVE': 'true',
            'NUMBER_OF_SEISMICITY_HISTORIES': '1',
            'INCLUDE_FAULT_SOURCE': 'true',
            'SUBDUCTION_RUPTURE_ASPECT_RATIO': '1.5',
            'FAULT_SURFACE_DISCRETIZATION': '1.0',
            'REFERENCE_VS30_VALUE': '760.0',
            'COMPONENT': 'Average Horizontal',
            'CONDITIONAL_LOSS_POE': '0.01',
            'TRUNCATION_LEVEL': '3',
            'COMPUTE_MEAN_HAZARD_CURVE': 'true',
            'AREA_SOURCE_DISCRETIZATION': '0.1',
            'FAULT_RUPTURE_OFFSET': '5.0',
        }

        self.job = prepare_job(params)
        self.assertEquals(params['REGION_VERTEX'],
                          _toCoordList(self.job.oq_params.region))
        self.assertFieldsEqual(
            {'job_type': 'event_based',
             'upload': None,
             'region_grid_spacing': 0.02,
             'min_magnitude': 5.0,
             'investigation_time': 50.0,
             'component': 'average',
             'imt': 'sa',
             'period': 1.0,
             'truncation_type': 'none',
             'truncation_level': 3.0,
             'reference_vs30_value': 760.0,
             'imls': None,
             'poes': None,
             'realizations': 5,
             'histories': 1,
             'gm_correlated': False,
             }, self.job.oq_params)


class RunJobTestCase(unittest.TestCase):
    def setUp(self):
        self.job = None
        self.session = get_db_session("reslt", "writer")
        self.job_from_file = Job.from_file

    def tearDown(self):
        self.job = None

    def _job_status(self):
        return self.job.get_db_job(self.session).status

    def test_successful_job_lifecycle(self):
        with patch('openquake.job.Job.from_file') as from_file:

            # called in place of Job.launch
            def test_status_running_and_succeed():
                self.assertEquals('running', self._job_status())

                return []

            # replaces Job.launch with a mock
            def patch_job_launch(*args, **kwargs):
                self.job = self.job_from_file(*args, **kwargs)
                self.job.launch = mock.Mock(
                    side_effect=test_status_running_and_succeed)

                self.assertEquals('pending', self._job_status())

                return self.job

            from_file.side_effect = patch_job_launch
            run_job(helpers.get_data_path(CONFIG_FILE), 'db')

        self.assertEquals(1, self.job.launch.call_count)
        self.assertEquals('succeeded', self._job_status())

    def test_failed_job_lifecycle(self):
        with patch('openquake.job.Job.from_file') as from_file:

            # called in place of Job.launch
            def test_status_running_and_fail():
                self.assertEquals('running', self._job_status())

                raise Exception('OMG!')

            # replaces Job.launch with a mock
            def patch_job_launch(*args, **kwargs):
                self.job = self.job_from_file(*args, **kwargs)
                self.job.launch = mock.Mock(
                    side_effect=test_status_running_and_fail)

                self.assertEquals('pending', self._job_status())

                return self.job

            from_file.side_effect = patch_job_launch
            self.assertRaises(Exception, run_job,
                              helpers.get_data_path(CONFIG_FILE), 'db')

        self.assertEquals(1, self.job.launch.call_count)
        self.assertEquals('failed', self._job_status())

    def test_failed_db_job_lifecycle(self):
        with patch('openquake.job.Job.from_file') as from_file:

            # called in place of Job.launch
            def test_status_running_and_fail():
                self.assertEquals('running', self._job_status())

                session = get_db_session("uiapi", "writer")

                session.query(OqJob).filter(OqJob.id == -1).one()

            # replaces Job.launch with a mock
            def patch_job_launch(*args, **kwargs):
                self.job = self.job_from_file(*args, **kwargs)
                self.job.launch = mock.Mock(
                    side_effect=test_status_running_and_fail)

                self.assertEquals('pending', self._job_status())

                return self.job

            from_file.side_effect = patch_job_launch
            self.assertRaises(sqlalchemy.exc.SQLAlchemyError, run_job,
                              helpers.get_data_path(CONFIG_FILE), 'db')

        self.assertEquals(1, self.job.launch.call_count)
        self.assertEquals('failed', self._job_status())

    def test_invalid_job_lifecycle(self):
        with patch('openquake.job.Job.from_file') as from_file:

            # replaces Job.is_valid with a mock
            def patch_job_is_valid(*args, **kwargs):
                self.job = self.job_from_file(*args, **kwargs)
                self.job.is_valid = mock.Mock(
                    return_value=(False, ["OMG!"]))

                self.assertEquals('pending', self._job_status())

                return self.job

            from_file.side_effect = patch_job_is_valid
            run_job(helpers.get_data_path(CONFIG_FILE), 'db')

        self.assertEquals(1, self.job.is_valid.call_count)
        self.assertEquals('failed', self._job_status())

    def test_computes_sites_in_region_when_specified(self):
        """When we have hazard jobs only, and we specify a region,
        we use the standard algorithm to split the region in sites. In this
        example, the region has just four sites (the region boundaries).
        """
        sections = [config.HAZARD_SECTION, config.GENERAL_SECTION]
        input_region = "2.0, 1.0, 2.0, 2.0, 1.0, 2.0, 1.0, 1.0"

        params = {config.INPUT_REGION: input_region,
                config.REGION_GRID_SPACING: 1.0}
                
        engine = helpers.create_job(params, sections=sections)

        expected_sites = [shapes.Site(1.0, 1.0), shapes.Site(2.0, 1.0),
                shapes.Site(1.0, 2.0), shapes.Site(2.0, 2.0)]

        self.assertEquals(expected_sites, engine.sites_to_compute())

    def test_computes_specific_sites_when_specified(self):
        """When we have hazard jobs only, and we specify a list of sites
        (SITES parameter in the configuration file) we trigger the
        computation only on those sites.
        """
        sections = [config.HAZARD_SECTION, config.GENERAL_SECTION]
        sites = "1.0, 1.5, 1.5, 2.5, 3.0, 3.0, 4.0, 4.5"

        params = {config.SITES: sites}

        engine = helpers.create_job(params, sections=sections)

        expected_sites = [shapes.Site(1.5, 1.0), shapes.Site(2.5, 1.5),
                shapes.Site(3.0, 3.0), shapes.Site(4.5, 4.0)]

        self.assertEquals(expected_sites, engine.sites_to_compute())

    def test_computes_sites_in_region_with_risk_jobs(self):
        """When we have hazard and risk jobs, we always use the region."""
        sections = [config.HAZARD_SECTION,
                config.GENERAL_SECTION, config.RISK_SECTION]

        input_region = "2.0, 1.0, 2.0, 2.0, 1.0, 2.0, 1.0, 1.0"

        params = {config.INPUT_REGION: input_region,
                config.REGION_GRID_SPACING: 1.0}

        engine = helpers.create_job(params, sections=sections)

        expected_sites = [shapes.Site(1.0, 1.0), shapes.Site(2.0, 1.0),
                shapes.Site(1.0, 2.0), shapes.Site(2.0, 2.0)]

        self.assertEquals(expected_sites, engine.sites_to_compute())
