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


import os
import unittest
import uuid

from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ObjectDoesNotExist

from openquake.calculators.risk.event_based import core
from openquake.db import models
from openquake import engine
from openquake import shapes

from tests.utils import helpers


class EngineAPITestCase(unittest.TestCase):

    def setUp(self):
        self.job = engine.prepare_job()

    def test_import_job_profile(self):
        # Given a path to a demo config file, ensure that the appropriate
        # database record for OqJobProfile is created.

        # At the moment, the api function used to import the job profile also
        # returns a dict of the config params and a list of config file
        # sections.

        cfg_path = helpers.demo_file('HazardMapTest/config.gem')

        # Default 'openquake' user:
        owner = helpers.default_user()

        smlt_input = models.Input(
            owner=helpers.default_user(),
            path=os.path.abspath(helpers.demo_file(
                'HazardMapTest/source_model_logic_tree.xml')),
            input_type='lt_source', size=671)

        gmpelt_input = models.Input(
            owner=helpers.default_user(),
            path=os.path.abspath(helpers.demo_file(
                'HazardMapTest/gmpe_logic_tree.xml')),
            input_type='lt_gmpe', size=709)

        src_model_input = models.Input(
            owner=helpers.default_user(),
            path=os.path.abspath(helpers.demo_file(
                'HazardMapTest/source_model.xml')),
            input_type='source', size=1644)

        expected_inputs_map = dict(
            lt_source=smlt_input, lt_gmpe=gmpelt_input, source=src_model_input)

        expected_jp = models.OqJobProfile(
            owner=owner,
            calc_mode='classical',
            job_type=['hazard'],
            region=GEOSGeometry(
                    'POLYGON((-122.2 37.6, -122.2 38.2, '
                    '-121.5 38.2, -121.5 37.6, -122.2 37.6))'),
            region_grid_spacing=0.01,
            min_magnitude=5.0,
            investigation_time=50.0,
            maximum_distance=200.0,
            component='gmroti50',
            imt='pga',
            period=None,
            damping=None,
            truncation_type='twosided',
            truncation_level=3.0,
            imls=[
                0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527,
                0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778, 1.09],
            poes=[0.1],
            realizations=1,
            depth_to_1pt_0km_per_sec=100.0,
            vs30_type='measured',
            source_model_lt_random_seed=23,
            gmpe_lt_random_seed=5,
            width_of_mfd_bin=0.1,
            standard_deviation_type='total',
            reference_vs30_value=760.0,
            reference_depth_to_2pt5km_per_sec_param=5.0,
            sadigh_site_type='rock',
            # area sources:
            include_area_sources=True,
            treat_area_source_as='pointsources',
            area_source_discretization=0.1,
            area_source_magnitude_scaling_relationship=(
                'W&C 1994 Mag-Length Rel.'),
            # point sources:
            include_grid_sources=False,
            treat_grid_source_as='pointsources',
            grid_source_magnitude_scaling_relationship=(
                'W&C 1994 Mag-Length Rel.'),
            # simple faults:
            include_fault_source=True,
            fault_rupture_offset=1.0,
            fault_surface_discretization=1.0,
            fault_magnitude_scaling_relationship='Wells & Coppersmith (1994)',
            fault_magnitude_scaling_sigma=0.0,
            rupture_aspect_ratio=2.0,
            rupture_floating_type='downdip',
            # complex faults:
            include_subduction_fault_source=False,
            subduction_fault_rupture_offset=10.0,
            subduction_fault_surface_discretization=10.0,
            subduction_fault_magnitude_scaling_relationship=(
                'W&C 1994 Mag-Length Rel.'),
            subduction_fault_magnitude_scaling_sigma=0.0,
            subduction_rupture_aspect_ratio=1.5,
            subduction_rupture_floating_type='downdip',
            quantile_levels=[],
            compute_mean_hazard_curve=True)

        expected_sections = ['HAZARD', 'general']
        expected_params = {
            'AREA_SOURCE_DISCRETIZATION': '0.1',
            'AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP':
                'W&C 1994 Mag-Length Rel.',
            'BASE_PATH': os.path.abspath(helpers.demo_file('HazardMapTest')),
            'CALCULATION_MODE': 'Classical',
            'COMPONENT': 'Average Horizontal (GMRotI50)',
            'COMPUTE_MEAN_HAZARD_CURVE': 'true',
            'DAMPING': '5.0',
            'DEPTHTO1PT0KMPERSEC': '100.0',
            'FAULT_MAGNITUDE_SCALING_RELATIONSHIP':
                'Wells & Coppersmith (1994)',
            'FAULT_MAGNITUDE_SCALING_SIGMA': '0.0',
            'FAULT_RUPTURE_OFFSET': '1.0',
            'FAULT_SURFACE_DISCRETIZATION': '1.0',
            'GMPE_LOGIC_TREE_FILE': os.path.abspath(
                helpers.demo_file('HazardMapTest/gmpe_logic_tree.xml')),
            'GMPE_LT_RANDOM_SEED': '5',
            'GMPE_TRUNCATION_TYPE': '2 Sided',
            'GRID_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP':
                'W&C 1994 Mag-Length Rel.',
            'INCLUDE_AREA_SOURCES': 'true',
            'INCLUDE_FAULT_SOURCE': 'true',
            'INCLUDE_GRID_SOURCES': 'false',
            'INCLUDE_SUBDUCTION_FAULT_SOURCE': 'false',
            'INTENSITY_MEASURE_LEVELS': (
                '0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527,'
                ' 0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778,'
                ' 1.09'),
            'INTENSITY_MEASURE_TYPE': 'PGA',
            'INVESTIGATION_TIME': '50.0',
            'MAXIMUM_DISTANCE': '200.0',
            'MINIMUM_MAGNITUDE': '5.0',
            'NUMBER_OF_LOGIC_TREE_SAMPLES': '1',
            'OUTPUT_DIR': 'computed_output',
            'PERIOD': '0.0',
            'POES': '0.1',
            'QUANTILE_LEVELS': '',
            'REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM': '5.0',
            'REFERENCE_VS30_VALUE': '760.0',
            'REGION_GRID_SPACING': '0.01',
            'REGION_VERTEX':
                '37.6, -122.2, 38.2, -122.2, 38.2, -121.5, 37.6, -121.5',
            'RUPTURE_ASPECT_RATIO': '2.0',
            'RUPTURE_FLOATING_TYPE': 'Along strike and down dip',
            'SADIGH_SITE_TYPE': 'Rock',
            'SOURCE_MODEL_LOGIC_TREE_FILE': os.path.abspath(
                helpers.demo_file(
                    'HazardMapTest/source_model_logic_tree.xml')),
            'SOURCE_MODEL_LT_RANDOM_SEED': '23',
            'STANDARD_DEVIATION_TYPE': 'Total',
            'SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP':
                'W&C 1994 Mag-Length Rel.',
            'SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA': '0.0',
            'SUBDUCTION_FAULT_RUPTURE_OFFSET': '10.0',
            'SUBDUCTION_FAULT_SURFACE_DISCRETIZATION': '10.0',
            'SUBDUCTION_RUPTURE_ASPECT_RATIO': '1.5',
            'SUBDUCTION_RUPTURE_FLOATING_TYPE': 'Along strike and down dip',
            'TREAT_AREA_SOURCE_AS': 'Point Sources',
            'TREAT_GRID_SOURCE_AS': 'Point Sources',
            'TRUNCATION_LEVEL': '3',
            'VS30_TYPE': 'measured',
            'WIDTH_OF_MFD_BIN': '0.1'}

        actual_jp, params, sections = engine.import_job_profile(
            cfg_path, self.job)
        self.assertEquals(expected_params, params)
        self.assertEquals(expected_sections, sections)

        # Test the OqJobProfile:
        self.assertTrue(
            models.model_equals(expected_jp, actual_jp, ignore=(
                'id', 'last_update', '_owner_cache')))

        # Test the Inputs:
        actual_inputs = models.inputs4job(self.job.id)
        self.assertEquals(3, len(actual_inputs))

        for act_inp in actual_inputs:
            exp_inp = expected_inputs_map[act_inp.input_type]
            self.assertTrue(
                models.model_equals(exp_inp, act_inp,
                                    ignore=('id',  'last_update',
                                            '_owner_cache')))

    def test_import_job_profile_as_specified_user(self):
        # Test importing of a job profile when a user is specified
        # The username will be randomly generated and unique to give
        # a clean set of test conditions.
        user_name = str(uuid.uuid4())

        # For sanity, check that the user does not exist to begin with.
        self.assertRaises(ObjectDoesNotExist, models.OqUser.objects.get,
                          user_name=user_name)

        cfg_path = helpers.demo_file('HazardMapTest/config.gem')

        job_profile, _params, _sections = engine.import_job_profile(
            cfg_path, self.job, user_name=user_name)

        self.assertEqual(user_name, job_profile.owner.user_name)
        # Check that the OqUser record for this user now exists.
        # If this fails, it will raise an `ObjectDoesNotExist` exception.
        models.OqUser.objects.get(user_name=user_name)

    def test_run_job_deletes_job_counters(self):
        # This test ensures that
        # :function:`openquake.utils.stats.delete_job_counters` is called
        cfg_path = helpers.demo_file('HazardMapTest/config.gem')

        job_profile, params, sections = engine.import_job_profile(
            cfg_path, self.job)

        # We don't want any of the supervisor/executor forking to happen; it's
        # not necessary. Also, forking should not happen in the context of a
        # test run.
        with helpers.patch('os.fork', mocksignature=False) as fork_mock:
            # Fake return val for fork:
            fork_mock.return_value = 0
            # And we don't actually want to run the job.
            with helpers.patch('openquake.engine._launch_job'):
                with helpers.patch(
                    'openquake.utils.stats.delete_job_counters') as djc_mock:
                    engine.run_job(self.job, params, sections)
                    self.assertEquals(1, djc_mock.call_count)


class EngineLaunchCalcTestCase(unittest.TestCase):
    """Tests for :func:`openquake.engine._launch_job`."""

    def test__launch_job_calls_core_calc_methods(self):
        # The `Calculator` interface defines 4 general methods:
        # - initialize
        # - pre_execute
        # - execute
        # - post_execute
        # When `_launch_job` is called, each of these methods should be
        # called once per job type (hazard, risk).

        # Calculation setup:
        cfg_file = helpers.demo_file('classical_psha_based_risk/config.gem')

        job = engine.prepare_job()
        job_profile, params, sections = engine.import_job_profile(
            cfg_file, job)

        job_ctxt = engine.JobContext(
            params, job.id, sections=sections,
            serialize_results_to=['xml', 'db'],
            oq_job_profile=job_profile, oq_job=job)

        # Mocking setup:
        cls_haz_calc = ('openquake.calculators.hazard.classical.core'
                        '.ClassicalHazardCalculator')
        cls_risk_calc = ('openquake.calculators.risk.classical.core'
                         '.ClassicalRiskCalculator')
        methods = ('initialize', 'pre_execute', 'execute', 'post_execute')
        haz_patchers = [helpers.patch('%s.%s' % (cls_haz_calc, m))
                        for m in methods]
        risk_patchers = [helpers.patch('%s.%s' % (cls_risk_calc, m))
                         for m in methods]

        haz_mocks = [p.start() for p in haz_patchers]
        risk_mocks = [p.start() for p in risk_patchers]

        # Call the function under test:
        engine._launch_job(job_ctxt, sections)

        self.assertTrue(all(x.call_count == 1 for x in haz_mocks))
        self.assertTrue(all(x.call_count == 1 for x in risk_mocks))

        # Tear down the mocks:
        for p in haz_patchers:
            p.stop()
        for p in risk_patchers:
            p.stop()


class ReadSitesFromExposureTestCase(unittest.TestCase):

    def test_read_sites_from_exposure(self):
        # Test reading site data from an exposure file using
        # :py:function:`openquake.risk.read_sites_from_exposure`.
        job_cfg = helpers.testdata_path('simplecase/config.gem')

        test_job = helpers.job_from_file(job_cfg)
        calc = core.EventBasedRiskCalculator(test_job)
        calc.store_exposure_assets()

        expected_sites = set([
            shapes.Site(-118.077721, 33.852034),
            shapes.Site(-118.067592, 33.855398),
            shapes.Site(-118.186739, 33.779013)])

        actual_sites = set(engine.read_sites_from_exposure(test_job))

        self.assertEqual(expected_sites, actual_sites)
