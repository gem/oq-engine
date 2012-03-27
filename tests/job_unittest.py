# -*- coding: utf-8 -*-

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


import mock
import os
import textwrap
import unittest

from functools import partial
from tempfile import gettempdir

from django.contrib.gis.geos.polygon import Polygon
from django.contrib.gis.geos.collections import MultiPoint

from openquake import engine
from openquake import kvs
from openquake.db import models
from openquake import shapes
from openquake.calculators.risk.event_based.core import (
    EventBasedRiskCalculator)
from openquake.engine import _get_source_models
from openquake.engine import import_job_profile
from openquake.engine import JobContext
from openquake.engine import _parse_config_file
from openquake.engine import _prepare_config_parameters
from openquake.engine import _prepare_job
from openquake.job import config
from openquake.job.params import config_text_to_list

from tests.utils import helpers
from tests.utils.helpers import patch


CONFIG_FILE = "config.gem"
CONFIG_WITH_INCLUDES = "config_with_includes.gem"
HAZARD_ONLY = "hazard-config.gem"

REGION_EXPOSURE_TEST_FILE = "ExposureModelFile-helpers.region"
BLOCK_SPLIT_TEST_FILE = "block_split.gem"
REGION_TEST_FILE = "small.region"


def _to_coord_list(geometry):
    pts = []

    if isinstance(geometry, Polygon):
        # Ignore the last coord:
        for c in geometry.coords[0][:-1]:
            pts.append(str(c[1]))
            pts.append(str(c[0]))

        return ', '.join(pts)
    elif isinstance(geometry, MultiPoint):
        for c in geometry.coords:
            pts.append(str(c[1]))
            pts.append(str(c[0]))

        return ', '.join(pts)
    else:
        raise RuntimeError('Unexpected geometry type: %s' % type(geometry))


class JobTestCase(unittest.TestCase):

    def setUp(self):
        client = kvs.get_client()

        # Delete managed job id info so we can predict the job key
        # which will be allocated for us
        client.delete(kvs.tokens.CURRENT_JOBS)

        self.generated_files = []

        job = engine.prepare_job()
        jp, params, sections = import_job_profile(helpers.get_data_path(
            CONFIG_FILE), job)
        self.job_ctxt = JobContext(
            params, job.id, sections=sections, oq_job_profile=jp, oq_job=job)

        job = engine.prepare_job()
        jp, params, sections = import_job_profile(helpers.get_data_path(
            CONFIG_WITH_INCLUDES), job)
        self.job_ctxt_with_includes = JobContext(
            params, job.id, sections=sections, oq_job_profile=jp, oq_job=job)

    def tearDown(self):
        for cfg in self.generated_files:
            try:
                os.remove(cfg)
            except OSError:
                pass

        kvs.cache_gc('::JOB::1::')
        kvs.cache_gc('::JOB::2::')

    def test_job_has_the_correct_sections(self):
        self.assertEqual(["RISK", "HAZARD", "general"], self.job_ctxt.sections)
        self.assertEqual(self.job_ctxt.sections,
                         self.job_ctxt_with_includes.sections)

    def test_job_with_only_hazard_config_only_has_hazard_section(self):
        job_with_only_hazard = \
            helpers.job_from_file(helpers.get_data_path(HAZARD_ONLY))
        self.assertEqual(["HAZARD"], job_with_only_hazard.sections)

    def test_configuration_is_the_same_no_matter_which_way_its_provided(self):

        sha_from_file_key = lambda params, key: params[key].split('!')[1]

        # A unique job key is prepended to these file hashes
        # to enable garabage collection.
        # Thus, we have to do a little voodoo to make this test work.
        src_model = 'SOURCE_MODEL_LOGIC_TREE_FILE'
        gmpe = 'GMPE_LOGIC_TREE_FILE'

        self.job_ctxt.to_kvs()
        self.job_ctxt_with_includes.to_kvs()

        job1_src_model_sha = sha_from_file_key(self.job_ctxt.params, src_model)
        job2_src_model_sha = sha_from_file_key(
            self.job_ctxt_with_includes.params, src_model)

        self.assertEqual(job1_src_model_sha, job2_src_model_sha)

        del self.job_ctxt.params[src_model]
        del self.job_ctxt_with_includes.params[src_model]

        job1_gmpe_sha = sha_from_file_key(self.job_ctxt.params, gmpe)
        job2_gmpe_sha = sha_from_file_key(self.job_ctxt_with_includes.params,
                                          gmpe)
        self.assertEqual(job1_gmpe_sha, job2_gmpe_sha)

        del self.job_ctxt.params[gmpe]
        del self.job_ctxt_with_includes.params[gmpe]

        self.assertEqual(self.job_ctxt.params,
                         self.job_ctxt_with_includes.params)

    def test_can_store_and_read_jobs_from_kvs(self):
        self.job_ctxt._log_level = 'debug'
        self.job_ctxt.params['debug'] = self.job_ctxt.log_level
        try:
            self.job_ctxt.to_kvs()

            job_from_kvs = JobContext.from_kvs(self.job_ctxt.job_id)
            self.assertEqual(self.job_ctxt.params, job_from_kvs.params)
        finally:
            helpers.cleanup_loggers()


class JobDbRecordTestCase(unittest.TestCase):

    def setUp(self):
        self.job = None

    def test_job_db_record_for_output_type_db(self):
        self.job = engine._job_from_file(
            helpers.get_data_path(CONFIG_FILE), 'db')
        models.OqJob.objects.get(id=self.job.job_id)

    def test_job_db_record_for_output_type_xml(self):
        self.job = engine._job_from_file(
            helpers.get_data_path(CONFIG_FILE), 'xml')
        models.OqJob.objects.get(id=self.job.job_id)

    def test_get_status_from_db(self):
        self.job = engine._job_from_file(
            helpers.get_data_path(CONFIG_FILE), 'db')
        row = models.OqJob.objects.get(id=self.job.job_id)

        row.status = "failed"
        row.save()
        self.assertEqual(
            "failed", JobContext.get_status_from_db(self.job.job_id))

        row.status = "running"
        row.save()
        self.assertEqual(
            "running", JobContext.get_status_from_db(self.job.job_id))

    def test_is_job_completed(self):
        job_id = engine._job_from_file(
            helpers.get_data_path(CONFIG_FILE), 'db').job_id
        row = models.OqJob.objects.get(id=job_id)
        pairs = [('pending', False), ('running', False),
                 ('succeeded', True), ('failed', True)]
        for status, is_completed in pairs:
            row.status = status
            row.save()
            self.assertEqual(
                JobContext.is_job_completed(job_id), is_completed)


class ConfigParseTestCase(unittest.TestCase):

    def test_parse_file(self):
        content = '''
            [GENERAL]
            CALCULATION_MODE = Event Based

            [HAZARD]
            MINIMUM_MAGNITUDE = 5.0
            '''
        config_path = helpers.touch(
            dir=gettempdir(), content=textwrap.dedent(content))

        params, sections = _parse_config_file(config_path)

        self.assertEqual(
            {'BASE_PATH': gettempdir(),
             'CALCULATION_MODE': 'Event Based',
             'MINIMUM_MAGNITUDE': '5.0'},
            params)
        self.assertEqual(['GENERAL', 'HAZARD'], sorted(sections))

    def test_parse_missing_files(self):
        config_path = '/does/not/exist'

        self.assertRaises(config.ValidationException, _parse_config_file,
                          config_path)

    def test_prepare_parameters(self):
        content = '''
            [GENERAL]
            CALCULATION_MODE = Event Based
            # unknown parameter
            FOO = 5

            [HAZARD]
            MINIMUM_MAGNITUDE = 5.0
            # not used for this calc mode
            COMPUTE_MEAN_HAZARD_CURVE = true
            '''
        config_path = helpers.touch(
            dir=gettempdir(), content=textwrap.dedent(content))

        params, sections = _parse_config_file(config_path)
        params, sections = _prepare_config_parameters(params, sections)

        self.assertEqual(
            {'BASE_PATH': gettempdir(),
             'MINIMUM_MAGNITUDE': '5.0',
             'CALCULATION_MODE': 'Event Based'},
            params)
        self.assertEqual(['GENERAL', 'HAZARD'], sorted(sections))

    def test_prepare_path_parameters(self):
        content = '''
            [GENERAL]
            CALCULATION_MODE = Event Based
            OUTPUT_DIR = output

            [HAZARD]
            SOURCE_MODEL_LOGIC_TREE_FILE = source-model.xml
            GMPE_LOGIC_TREE_FILE = gmpe.xml

            [RISK]
            EXPOSURE = /absolute/exposure.xml
            VULNERABILITY = vulnerability.xml
            '''
        config_path = helpers.touch(content=textwrap.dedent(content))

        params, sections = _parse_config_file(config_path)
        params, sections = _prepare_config_parameters(params, sections)

        self.assertEqual(
            {'BASE_PATH': gettempdir(),
             'OUTPUT_DIR': 'output',
             'SOURCE_MODEL_LOGIC_TREE_FILE': os.path.join(gettempdir(),
                                                          'source-model.xml'),
             'GMPE_LOGIC_TREE_FILE': os.path.join(gettempdir(), 'gmpe.xml'),
             'EXPOSURE': '/absolute/exposure.xml',
             'VULNERABILITY': os.path.join(gettempdir(), 'vulnerability.xml'),
             'CALCULATION_MODE': 'Event Based'},
            params)
        self.assertEqual(['GENERAL', 'HAZARD', 'RISK'], sorted(sections))


def datapath(test, path):
    return helpers.testdata_path("%s/%s" % (test, path))


class PrepareJobTestCase(unittest.TestCase, helpers.DbTestCase):
    """
    Unit tests for the _prepare_job helper function, which creates a new
    job entry with the associated parameters.

    Test data is a trimmed-down version of smoketest config files

    As a side-effect, also tests that the inserted record satisfied
    the DB constraints.
    """

    BASE_CLASSICAL_PARAMS = {
        'CALCULATION_MODE': 'Classical',
        'POES': '0.01 0.1',
        'SOURCE_MODEL_LT_RANDOM_SEED': '23',
        'GMPE_LT_RANDOM_SEED': '5',
        'INTENSITY_MEASURE_TYPE': 'PGA',
        'MINIMUM_MAGNITUDE': '5.0',
        'INVESTIGATION_TIME': '50.0',
        'INCLUDE_GRID_SOURCES': 'true',
        'TREAT_GRID_SOURCE_AS': 'Point Sources',
        'INCLUDE_AREA_SOURCES': 'true',
        'TREAT_AREA_SOURCE_AS': 'Point Sources',
        'QUANTILE_LEVELS': '0.25 0.50',
        'INTENSITY_MEASURE_LEVELS': '0.005, 0.007, 0.0098, 0.0137, 0.0192',
        'GMPE_TRUNCATION_TYPE': '2 Sided',
        'STANDARD_DEVIATION_TYPE': 'Total',
        'MAXIMUM_DISTANCE': '200.0',
        'NUMBER_OF_LOGIC_TREE_SAMPLES': '2',
        'PERIOD': '0.0',
        'DAMPING': '5.0',
        'AGGREGATE_LOSS_CURVE': '1',
        'INCLUDE_FAULT_SOURCE': 'true',
        'FAULT_RUPTURE_OFFSET': '5.0',
        'FAULT_SURFACE_DISCRETIZATION': '1.0',
        'FAULT_MAGNITUDE_SCALING_SIGMA': '0.0',
        'FAULT_MAGNITUDE_SCALING_RELATIONSHIP': 'W&C 1994 Mag-Length Rel.',
        'REFERENCE_VS30_VALUE': '760.0',
        'REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM': '5.0',
        'COMPONENT': 'Average Horizontal (GMRotI50)',
        'CONDITIONAL_LOSS_POE': '0.01',
        'TRUNCATION_LEVEL': '3',
        'COMPUTE_MEAN_HAZARD_CURVE': 'true',
        'AREA_SOURCE_DISCRETIZATION': '0.1',
        'AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP':
            'W&C 1994 Mag-Length Rel.',
        'WIDTH_OF_MFD_BIN': '0.1',
        'SADIGH_SITE_TYPE': 'Rock',
        'INCLUDE_SUBDUCTION_FAULT_SOURCE': 'true',
        'SUBDUCTION_FAULT_RUPTURE_OFFSET': '10.0',
        'SUBDUCTION_FAULT_SURFACE_DISCRETIZATION': '10.0',
        'SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA': '0.0',
        'SUBDUCTION_RUPTURE_ASPECT_RATIO': '1.5',
        'SUBDUCTION_RUPTURE_FLOATING_TYPE': 'Along strike and down dip',
        'SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP':
            'W&C 1994 Mag-Length Rel.',
        'RUPTURE_ASPECT_RATIO': '1.5',
        'RUPTURE_FLOATING_TYPE': 'Along strike and down dip',
    }

    BASE_SCENARIO_PARAMS = {
        'CALCULATION_MODE': 'Scenario',
        'GMPE_MODEL_NAME': 'BA_2008_AttenRel',
        'GMF_RANDOM_SEED': '3',
        'RUPTURE_SURFACE_DISCRETIZATION': '0.1',
        'INTENSITY_MEASURE_TYPE': 'PGA',
        'REFERENCE_VS30_VALUE': '759.0',
        'COMPONENT': 'Average Horizontal (GMRotI50)',
        'PERIOD': '0.0',
        'DAMPING': '5.0',
        'NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS': '5',
        'TRUNCATION_LEVEL': '3',
        'GMPE_TRUNCATION_TYPE': '1 Sided',
        'GROUND_MOTION_CORRELATION': 'true',
    }

    BASE_EVENT_BASED_PARAMS = {
        'CALCULATION_MODE': 'Event Based',
        'SOURCE_MODEL_LT_RANDOM_SEED': '23',
        'GMPE_LT_RANDOM_SEED': '5',
        'INTENSITY_MEASURE_TYPE': 'SA',
        'INCLUDE_GRID_SOURCES': 'false',
        'INCLUDE_SUBDUCTION_FAULT_SOURCE': 'false',
        'RUPTURE_ASPECT_RATIO': '1.5',
        'MINIMUM_MAGNITUDE': '5.0',
        'SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA': '0.0',
        'INVESTIGATION_TIME': '50.0',
        'TREAT_GRID_SOURCE_AS': 'Point Sources',
        'INCLUDE_AREA_SOURCES': 'true',
        'TREAT_AREA_SOURCE_AS': 'Point Sources',
        'INTENSITY_MEASURE_LEVELS': '0.005, 0.007, 0.0098, 0.0137, 0.0192',
        'GROUND_MOTION_CORRELATION': 'false',
        'GMPE_TRUNCATION_TYPE': 'None',
        'STANDARD_DEVIATION_TYPE': 'Total',
        'SUBDUCTION_FAULT_RUPTURE_OFFSET': '10.0',
        'NUMBER_OF_LOGIC_TREE_SAMPLES': '5',
        'PERIOD': '1.0',
        'DAMPING': '5.0',
        'AGGREGATE_LOSS_CURVE': 'true',
        'NUMBER_OF_SEISMICITY_HISTORIES': '1',
        'INCLUDE_FAULT_SOURCE': 'true',
        'FAULT_RUPTURE_OFFSET': '5.0',
        'FAULT_SURFACE_DISCRETIZATION': '1.0',
        'FAULT_MAGNITUDE_SCALING_SIGMA': '0.0',
        'FAULT_MAGNITUDE_SCALING_RELATIONSHIP': 'W&C 1994 Mag-Length Rel.',
        'SUBDUCTION_RUPTURE_ASPECT_RATIO': '1.5',
        'REFERENCE_VS30_VALUE': '760.0',
        'REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM': '5.0',
        'COMPONENT': 'Average Horizontal',
        'CONDITIONAL_LOSS_POE': '0.01',
        'TRUNCATION_LEVEL': '3',
        'AREA_SOURCE_DISCRETIZATION': '0.1',
        'AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP':
            'W&C 1994 Mag-Length Rel.',
        'WIDTH_OF_MFD_BIN': '0.1',
        'SADIGH_SITE_TYPE': 'Rock',
        'SUBDUCTION_FAULT_RUPTURE_OFFSET': '10.0',
        'SUBDUCTION_FAULT_SURFACE_DISCRETIZATION': '10.0',
        'SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA': '0.0',
        'SUBDUCTION_RUPTURE_ASPECT_RATIO': '1.5',
        'SUBDUCTION_RUPTURE_FLOATING_TYPE': 'Along strike and down dip',
        'SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP':
            'W&C 1994 Mag-Length Rel.',
        'RUPTURE_ASPECT_RATIO': '1.5',
        'RUPTURE_FLOATING_TYPE': 'Along strike and down dip',
        'GMF_RANDOM_SEED': '1',
    }

    def setUp(self):
        self.job = engine.prepare_job()

    def tearDown(self):
        if (hasattr(self, "job") and self.job):
            self.teardown_job(self.job)

    def _reload_params(self):
        return models.profile4job(self.job.id)

    def assertFieldsEqual(self, expected, params):
        got_params = dict((k, getattr(params, k)) for k in expected.keys())

        self.assertEqual(expected, got_params)

    def _get_inputs(self, job):
        inputs = [dict(path=i.path, type=i.input_type)
                  for i in models.inputs4job(self.job.id)]

        return sorted(inputs, key=lambda i: (i['type'], i['path']))

    def test_get_source_models(self):
        abs_path = partial(datapath, "classical_psha_simple")

        path = abs_path('source_model_logic_tree.xml')
        models = _get_source_models(path)
        expected_models = [abs_path('source_model1.xml'),
                           abs_path('source_model2.xml')]

        self.assertEqual(expected_models, models),

    def test_prepare_classical_job(self):
        abs_path = partial(datapath, "classical_psha_simple")
        params = self.BASE_CLASSICAL_PARAMS.copy()
        params['REGION_VERTEX'] = '37.9, -121.9, 37.9, -121.6, 37.5, -121.6'
        params['REGION_GRID_SPACING'] = '0.1'
        params['SOURCE_MODEL_LOGIC_TREE_FILE'] = abs_path(
            "source_model_logic_tree.xml")
        params['GMPE_LOGIC_TREE_FILE'] = abs_path("gmpe_logic_tree.xml")
        params['EXPOSURE'] = abs_path("small_exposure.xml")
        params['VULNERABILITY'] = abs_path("vulnerability.xml")
        params['SOURCE_MODEL_LT_RANDOM_SEED'] = '23'
        params['GMPE_LT_RANDOM_SEED'] = '5'
        params['LREM_STEPS_PER_INTERVAL'] = '5'

        jp = _prepare_job(params, ['HAZARD', 'RISK'], 'openquake', self.job)
        self.assertEqual(params['REGION_VERTEX'], _to_coord_list(jp.region))
        self.assertFieldsEqual(
            {'calc_mode': 'classical',
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
             'damping': None,
             'gmf_calculation_number': None,
             'rupture_surface_discretization': None,
             'subduction_rupture_floating_type': 'downdip',
             }, jp)
        self.assertEqual([
                {'path': abs_path("small_exposure.xml"),
                 'type': 'exposure'},
                {'path': abs_path("gmpe_logic_tree.xml"),
                 'type': 'lt_gmpe'},
                {'path': abs_path("source_model_logic_tree.xml"),
                 'type': 'lt_source'},
                {'path': abs_path("source_model1.xml"),
                 'type': 'source'},
                {'path': abs_path("source_model2.xml"),
                 'type': 'source'},
                {'path': abs_path("vulnerability.xml"),
                 'type': 'vulnerability'},
                ], self._get_inputs(self.job))

    def test_prepare_classical_job_over_sites(self):
        '''
        Same as test_prepare_classical_job, but with geometry specified as
        a list of sites.
        '''
        params = self.BASE_CLASSICAL_PARAMS.copy()
        params['SITES'] = '37.9, -121.9, 37.9, -121.6, 37.5, -121.6'
        params['LREM_STEPS_PER_INTERVAL'] = '5'

        jp = _prepare_job(params, ['HAZARD', 'RISK'], 'openquake', self.job)
        self.assertEqual(params['SITES'], _to_coord_list(jp.sites))
        self.assertFieldsEqual(
            {'calc_mode': 'classical',
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
             }, jp)

    def test_prepare_scenario_job(self):
        abs_path = partial(datapath, "scenario")
        params = self.BASE_SCENARIO_PARAMS.copy()
        params['REGION_VERTEX'] = \
            '34.07, -118.25, 34.07, -118.22, 34.04, -118.22'
        params['REGION_GRID_SPACING'] = '0.02'
        params['SINGLE_RUPTURE_MODEL'] = abs_path("simple-fault-rupture.xml")
        params['EXPOSURE'] = abs_path("LA_small_portfolio.xml")
        params['VULNERABILITY'] = abs_path("vulnerability.xml")

        jp = _prepare_job(params, ['HAZARD', 'RISK'], 'openquake', self.job)
        self.assertEqual(params['REGION_VERTEX'], _to_coord_list(jp.region))
        self.assertFieldsEqual(
            {'calc_mode': 'scenario',
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
             'damping': None,
             'gmf_calculation_number': 5,
             'rupture_surface_discretization': 0.1,
             }, jp)
        self.assertEqual([
                {'path': abs_path("LA_small_portfolio.xml"),
                 'type': 'exposure'},
                {'path': abs_path("simple-fault-rupture.xml"),
                 'type': 'rupture'},
                {'path': abs_path("vulnerability.xml"),
                 'type': 'vulnerability'},
                ], self._get_inputs(self.job))

    def test_prepare_scenario_job_over_sites(self):
        '''
        Same as test_prepare_scenario_job, but with geometry specified as
        a list of sites.
        '''
        params = self.BASE_SCENARIO_PARAMS.copy()
        params['SITES'] = '34.07, -118.25, 34.07, -118.22, 34.04, -118.22'

        jp = _prepare_job(params, ['HAZARD', 'RISK'], 'openquake', self.job)
        self.assertEqual(params['SITES'], _to_coord_list(jp.sites))
        self.assertFieldsEqual(
            {'calc_mode': 'scenario',
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
             }, jp)

    def test_prepare_event_based_job(self):
        abs_path = partial(datapath, "simplecase")
        params = self.BASE_EVENT_BASED_PARAMS.copy()
        params['REGION_VERTEX'] = \
            '33.88, -118.3, 33.88, -118.06, 33.76, -118.06'
        params['REGION_GRID_SPACING'] = '0.02'
        params['SOURCE_MODEL_LOGIC_TREE_FILE'] = abs_path(
            "source_model_logic_tree.xml")
        params['GMPE_LOGIC_TREE_FILE'] = abs_path("gmpe_logic_tree.xml")
        params['EXPOSURE'] = abs_path("small_exposure.xml")
        params['VULNERABILITY'] = abs_path("vulnerability.xml")
        params['GMF_RANDOM_SEED'] = '1'
        params['LOSS_HISTOGRAM_BINS'] = '25'

        jp = _prepare_job(params, ['HAZARD', 'RISK'], 'openquake', self.job)
        self.assertEqual(params['REGION_VERTEX'], _to_coord_list(jp.region))
        self.assertFieldsEqual(
            {'calc_mode': 'event_based',
             'region_grid_spacing': 0.02,
             'min_magnitude': 5.0,
             'investigation_time': 50.0,
             'component': 'average',
             'imt': 'sa',
             'period': 1.0,
             'truncation_type': 'none',
             'truncation_level': 3.0,
             'reference_vs30_value': 760.0,
             'imls': [0.005, 0.007, 0.0098, 0.0137, 0.0192],
             'poes': None,
             'realizations': 5,
             'histories': 1,
             'gm_correlated': False,
             'damping': 5.0,
             'gmf_calculation_number': None,
             'rupture_surface_discretization': None,
             }, jp)
        self.assertEqual([
                {'path': abs_path("small_exposure.xml"),
                 'type': 'exposure'},
                {'path': abs_path("gmpe_logic_tree.xml"),
                 'type': 'lt_gmpe'},
                {'path': abs_path("source_model_logic_tree.xml"),
                 'type': 'lt_source'},
                {'path': abs_path("source_model1.xml"),
                 'type': 'source'},
                {'path': abs_path("source_model2.xml"),
                 'type': 'source'},
                {'path': abs_path("vulnerability.xml"),
                 'type': 'vulnerability'},
                ], self._get_inputs(self.job))

    def test_prepare_event_based_job_over_sites(self):
        '''
        Same as test_prepare_event_based_job, but with geometry specified as
        a list of sites.
        '''

        params = self.BASE_EVENT_BASED_PARAMS.copy()
        params['SITES'] = '33.88, -118.3, 33.88, -118.06, 33.76, -118.06'
        params['LOSS_HISTOGRAM_BINS'] = '25'

        jp = _prepare_job(params, ['HAZARD', 'RISK'], 'openquake', self.job)
        self.assertEqual(params['SITES'], _to_coord_list(jp.sites))
        self.assertFieldsEqual(
            {'calc_mode': 'event_based',
             'min_magnitude': 5.0,
             'investigation_time': 50.0,
             'component': 'average',
             'imt': 'sa',
             'period': 1.0,
             'truncation_type': 'none',
             'truncation_level': 3.0,
             'reference_vs30_value': 760.0,
             'imls': [0.005, 0.007, 0.0098, 0.0137, 0.0192],
             'poes': None,
             'realizations': 5,
             'histories': 1,
             'gm_correlated': False,
             }, jp)


class RunJobTestCase(unittest.TestCase):

    def setUp(self):
        self.job_from_file = engine._job_from_file
        self.init_logs_amqp_send = patch('openquake.logs.init_logs_amqp_send')
        self.init_logs_amqp_send.start()
        self.job = engine.prepare_job()
        self.job_profile, self.params, self.sections = (
            engine.import_job_profile(helpers.get_data_path(CONFIG_FILE),
                                      self.job))

    def tearDown(self):
        self.init_logs_amqp_send.stop()

    def _calculation_status(self):
        return models.OqJob.objects.latest(field_name='last_update').status

    def test_successful_job_lifecycle(self):

        def test_status_running_and_succeed(*args):
            self.assertEqual('running', self._calculation_status())

            return []

        def patch_job_launch(*args, **kwargs):
            self.job = self.job_from_file(*args, **kwargs)

            self.assertEqual('pending', self._calculation_status())

            return self.job

        before_launch = engine._launch_job
        try:
            engine._launch_job = mock.Mock(
                side_effect=test_status_running_and_succeed)

            with patch('openquake.engine._job_from_file') as from_file:
                from_file.side_effect = patch_job_launch

                with patch('os.fork', mocksignature=False) as fork:
                    fork.return_value = 0
                    engine.run_job(self.job, self.params, self.sections)

            self.assertEqual(1, engine._launch_job.call_count)
            self.assertEqual('succeeded', self._calculation_status())
        finally:
            engine._launch_job = before_launch

    def test_failed_job_lifecycle(self):

        def test_status_running_and_fail(*args):
            self.assertEqual('running', self._calculation_status())

            raise Exception('OMG!')

        def patch_job_launch(*args, **kwargs):
            self.job = self.job_from_file(*args, **kwargs)

            self.assertEqual('pending', self._calculation_status())

            return self.job

        before_launch = engine._launch_job
        try:
            engine._launch_job = mock.Mock(
                side_effect=test_status_running_and_fail)

            with patch('openquake.engine._job_from_file') as from_file:
                from_file.side_effect = patch_job_launch

                with patch('os.fork', mocksignature=False) as fork:
                    fork.return_value = 0
                    self.assertRaises(Exception, engine.run_job,
                                      self.job, self.params, self.sections)

            self.assertEqual(1, engine._launch_job.call_count)
            self.assertEqual('failed', self._calculation_status())
        finally:
            engine._launch_job = before_launch

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

        self.assertEqual(expected_sites, engine.sites_to_compute())

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

        self.assertEqual(expected_sites, engine.sites_to_compute())

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

        self.assertEqual(expected_sites, engine.sites_to_compute())

    def test_supervisor_is_spawned(self):
        with patch('openquake.engine._job_from_file'):

            before_launch = engine._launch_job
            try:
                engine._launch_job = mock.Mock()
                with patch('os.fork', mocksignature=False) as fork:

                    def fork_side_effect():
                        fork.side_effect = lambda: 0
                        return 1234
                    fork.side_effect = fork_side_effect
                    superv_func = 'openquake.supervising.supervisor.supervise'
                    with patch(superv_func) as sv:
                        engine.run_job(self.job, self.params, self.sections)
                        job = models.OqJob.objects.latest(
                            field_name='last_update')

                        self.assertEqual(1, sv.call_count)
                        self.assertEqual(((1234, job.id), {}), sv.call_args)
            finally:
                engine._launch_job = before_launch


class JobsWithExposureTestCase(unittest.TestCase):
    '''Tests related to job with exposure.'''

    def setUp(self):
        # Test 'event-based' job
        cfg_path = helpers.testdata_path("simplecase/config.gem")

        self.job = engine.prepare_job()
        self.jp, self.params, self.sections = engine.import_job_profile(
            cfg_path, self.job)

    def test_with_risk_jobs_we_can_trigger_hazard_only_on_exposure_sites(self):
        # When we have hazard and risk jobs, we can ask to trigger
        # the hazard computation only on the sites specified
        # in the exposure file.
        self.params['COMPUTE_HAZARD_AT_ASSETS_LOCATIONS'] = True

        job_ctxt = engine.JobContext(
            self.params, self.job.id, sections=self.sections,
            oq_job_profile=self.jp)

        calc = EventBasedRiskCalculator(job_ctxt)
        calc.store_exposure_assets()

        expected_sites = set([
            shapes.Site(-118.077721, 33.852034),
            shapes.Site(-118.067592, 33.855398),
            shapes.Site(-118.186739, 33.779013)])

        actual_sites = set(job_ctxt.sites_to_compute())
        self.assertEqual(expected_sites, actual_sites)


class JobStatsTestCase(unittest.TestCase):
    '''
    Tests related to capturing job stats.
    '''

    def setUp(self):
        # Test 'event-based' job
        cfg_path = helpers.testdata_path("simplecase/config.gem")
        base_path = helpers.testdata_path("simplecase")

        oq_job = engine.prepare_job()
        oq_job_profile, params, sections = engine.import_job_profile(
            cfg_path, oq_job)

        self.eb_job = JobContext(
            params, oq_job.id, sections=sections, base_path=base_path,
            oq_job_profile=oq_job_profile, oq_job=oq_job)

    def test_record_initial_stats(self):
        '''Verify that
        :py:method:`openquake.engine.JobContext._record_initial_stats`
        reports initial calculation stats.

        As we add fields to the uiapi.job_stats table, this test will need to
        be updated to check for this new information.
        '''
        self.eb_job._record_initial_stats()

        actual_stats = models.JobStats.objects.get(oq_job=self.eb_job.job_id)

        self.assertTrue(actual_stats.start_time is not None)
        self.assertEqual(91, actual_stats.num_sites)
        self.assertEqual(1, actual_stats.realizations)

    def test_job_launch_calls_record_initial_stats(self):
        '''When a job is launched, make sure that
        :py:method:`openquake.engine.JobContext._record_initial_stats`
        is called.
        '''
        # Mock out pieces of the test job so it doesn't actually run.
        eb_haz_calc = ('openquake.calculators.hazard.event_based.core'
                       '.EventBasedHazardCalculator')
        eb_risk_calc = ('openquake.calculators.risk.event_based.core'
                       '.EventBasedRiskCalculator')
        methods = ('initialize', 'pre_execute', 'execute', 'post_execute')

        haz_patchers = [patch('%s.%s' % (eb_haz_calc, m)) for m in methods]
        risk_patchers = [patch('%s.%s' % (eb_risk_calc, m)) for m in methods]

        for p in haz_patchers:
            p.start()
        for p in risk_patchers:
            p.start()

        try:
            record = 'openquake.engine.JobContext._record_initial_stats'

            with patch(record) as record_mock:
                engine._launch_job(
                    self.eb_job, ['general', 'HAZARD', 'RISK'])

                self.assertEqual(1, record_mock.call_count)
        finally:
            for p in haz_patchers:
                p.stop()
            for p in risk_patchers:
                p.stop()


class JobUtilsTestCase(unittest.TestCase):
    """Tests for utility functions in the job module."""

    def test_config_text_to_list(self):
        """Exercise :function:`openquake.job.params.config_text_to_list`."""
        expected = ['MagDistPMF', 'MagDistEpsPMF', 'FullDisaggMatrix']

        # the input mixes spaces and commas for robustness testing:
        test_input = 'MagDistPMF,MagDistEpsPMF FullDisaggMatrix'

        self.assertEqual(expected, config_text_to_list(test_input))

    def test_config_text_to_list_with_transform(self):
        """Exercise :function:`openquake.job.params.config_text_to_list` with a
        transform specified.
        """
        expected = [0.01, 0.02, 0.03, 0.04]

        # again, mix spaces and commas
        test_input = '0.01,0.02, 0.03 0.04'

        self.assertEqual(expected, config_text_to_list(test_input, float))

    def test_config_text_to_list_all_whitespace_input(self):
        """Exercise :function:`openquake.job.params.config_text_to_list` with
        an input of only spaces. """

        expected = []

        test_input = '     '

        self.assertEqual(expected, config_text_to_list(test_input))
