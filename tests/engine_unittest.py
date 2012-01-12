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
import unittest

from django.contrib.gis.geos import GEOSGeometry

from openquake import engine
from openquake.db.models import model_equals
from openquake.db.models import Input
from openquake.db.models import InputSet
from openquake.db.models import OqJobProfile
from openquake.db.models import OqUser

from tests.utils.helpers import demo_file
from tests.utils.helpers import patch


class EngineAPITestCase(unittest.TestCase):

    def test_import_job_profile(self):
        """Given a path to a demo config file, ensure that the appropriate
        database records for OqJobProfile, InputSet, and Input are created.

        At the moment, the api function used to import the job profile also
        returns a dict of the config params and a list of config file sections.
        """
        cfg_path = demo_file('HazardMapTest/config.gem')

        # Default 'openquake' user:
        owner = OqUser.objects.get(user_name='openquake')

        expected_input_set = InputSet(owner=owner)

        smlt_input = Input(
            input_set=expected_input_set,
            path=os.path.abspath(demo_file(
                'HazardMapTest/source_model_logic_tree.xml')),
            input_type='lt_source',
            size=671)

        gmpelt_input = Input(
            input_set=expected_input_set,
            path=os.path.abspath(demo_file(
                'HazardMapTest/gmpe_logic_tree.xml')),
            input_type='lt_gmpe',
            size=709)

        src_model_input = Input(
            input_set=expected_input_set,
            path=os.path.abspath(demo_file(
                'HazardMapTest/source_model.xml')),
            input_type='source',
            size=1644)

        expected_inputs_map = dict(
            lt_source=smlt_input, lt_gmpe=gmpelt_input, source=src_model_input)

        expected_jp = OqJobProfile(
            owner=owner,
            calc_mode='classical',
            job_type=['hazard'],
            region=GEOSGeometry(
                    'POLYGON((-122.2 37.6, -122.2 38.2, '
                    '-121.5 38.2, -121.5 37.6, -122.2 37.6))'),
            region_grid_spacing=0.01,
            input_set=expected_input_set,
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
            'BASE_PATH': os.path.abspath(demo_file('HazardMapTest')),
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
                demo_file('HazardMapTest/gmpe_logic_tree.xml')),
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
                demo_file('HazardMapTest/source_model_logic_tree.xml')),
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

        actual_jp, params, sections = engine.import_job_profile(cfg_path)
        self.assertEquals(expected_params, params)
        self.assertEquals(expected_sections, sections)

        # Test the OqJobProfile:
        self.assertTrue(
            model_equals(expected_jp, actual_jp, ignore=(
                'id', 'input_set', 'last_update', 'input_set_id',
                '_input_set_cache', '_owner_cache')))

        actual_input_set = actual_jp.input_set
        # Test the InputSet:
        self.assertTrue(
            model_equals(expected_input_set, actual_input_set,
                         ignore=('id', 'last_update', '_owner_cache')))

        # Test the Inputs:
        actual_inputs = Input.objects.filter(input_set=actual_input_set.id)
        self.assertEquals(3, len(actual_inputs))

        for act_inp in actual_inputs:
            exp_inp = expected_inputs_map[act_inp.input_type]
            self.assertTrue(
                model_equals(exp_inp, act_inp,
                             ignore=('id', 'input_set_id', 'last_update',
                                     '_input_set_cache')))

    def test_run_calculation_deletes_job_counters(self):
        """This test ensures that
        :function:`openquake.utils.stats.delete_job_counters` is called"""
        cfg_path = demo_file('HazardMapTest/config.gem')

        job_profile, params, sections = engine.import_job_profile(cfg_path)

        # We don't want any of the supervisor/executor forking to happen; it's
        # not necessary. Also, forking should not happen in the context of a
        # test run.
        with patch('os.fork', mocksignature=False) as fork_mock:
            # Fake return val for fork:
            fork_mock.return_value = 0
            # And we don't actually want to run the calculation.
            with patch('openquake.engine._launch_calculation'):
                with patch(
                    'openquake.utils.stats.delete_job_counters') as djc_mock:
                    engine.run_calculation(job_profile, params, sections)

                    self.assertEquals(1, djc_mock.call_count)
