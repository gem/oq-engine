# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011, GEM Foundation.
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

from openquake.job import Job, prepare_job, run_job

from openquake.db.alchemy.db_utils import get_db_session

from openquake.db.alchemy.models import OqJob
from db_tests import helpers
from tests.utils import helpers as test_helpers


def _toCoordList(polygon):
    session = get_db_session("reslt", "writer")

    pts = []

    # postgis -> lon/lat -> config lat/lon, skip the closing point
    for c in polygon.coords(session)[0][:-1]:
        pts.append("%.2f" % c[1])
        pts.append("%.2f" % c[0])

    return ", ".join(pts)


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


CONFIG_FILE = "config.gem"


class JobTestCase(unittest.TestCase):

    def setUp(self):
        self.job = None

    def tearDown(self):
        try:
            if self.job:
                os.remove(self.job.super_config_path)
        except OSError:
            pass

    def test_job_db_record_for_output_type_db(self):
        self.job = Job.from_file(test_helpers.get_data_path(CONFIG_FILE), 'db')

        session = get_db_session("uiapi", "writer")

        session.query(OqJob)\
            .filter(OqJob.id == self.job['OPENQUAKE_JOB_ID']).one()

    def test_job_db_record_for_output_type_xml(self):
        self.job = Job.from_file(test_helpers.get_data_path(CONFIG_FILE),
                                 'xml')

        session = get_db_session("uiapi", "writer")

        session.query(OqJob)\
            .filter(OqJob.id == self.job['OPENQUAKE_JOB_ID']).one()

    def test_get_db_job(self):
        self.job = Job.from_file(test_helpers.get_data_path(CONFIG_FILE), 'db')

        session = get_db_session("reslt", "writer")

        expected_job = session.query(OqJob)\
            .filter(OqJob.id == self.job.job_id).one()

        self.assertEqual(expected_job, self.job.get_db_job(session))

    def test_set_status(self):
        self.job = Job.from_file(test_helpers.get_data_path(CONFIG_FILE), 'db')

        session = get_db_session("reslt", "writer")

        status = 'running'
        self.job.set_status(status)

        job = session.query(OqJob).filter(OqJob.id == self.job.job_id).one()

        self.assertEqual(status, job.status)


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
        with mock.patch('openquake.job.Job.from_file') as from_file:

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
            run_job(test_helpers.get_data_path(CONFIG_FILE), 'db')

        self.assertEquals(1, self.job.launch.call_count)
        self.assertEquals('succeeded', self._job_status())

    def test_failed_job_lifecycle(self):
        with mock.patch('openquake.job.Job.from_file') as from_file:

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
                              test_helpers.get_data_path(CONFIG_FILE), 'db')

        self.assertEquals(1, self.job.launch.call_count)
        self.assertEquals('failed', self._job_status())

    def test_failed_db_job_lifecycle(self):
        with mock.patch('openquake.job.Job.from_file') as from_file:

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
                              test_helpers.get_data_path(CONFIG_FILE), 'db')

        self.assertEquals(1, self.job.launch.call_count)
        self.assertEquals('failed', self._job_status())

    def test_invalid_job_lifecycle(self):
        with mock.patch('openquake.job.Job.from_file') as from_file:

            # replaces Job.is_valid with a mock
            def patch_job_is_valid(*args, **kwargs):
                self.job = self.job_from_file(*args, **kwargs)
                self.job.is_valid = mock.Mock(
                    return_value=(False, ["OMG!"]))

                self.assertEquals('pending', self._job_status())

                return self.job

            from_file.side_effect = patch_job_is_valid
            run_job(test_helpers.get_data_path(CONFIG_FILE), 'db')

            self.assertEquals(1, self.job.is_valid.call_count)
            self.assertEquals('failed', self._job_status())
