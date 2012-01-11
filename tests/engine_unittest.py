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


class EngineAPITestCase(unittest.TestCase):

    def test_import_job_profile(self):
        """Given a path to a demo config file, ensure that the appropriate
        database records for OqJobProfile, InputSet, and Input are created.
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
            subduction_fault_magnitude_scaling_relationship=
                'W&C 1994 Mag-Length Rel.',
            subduction_fault_magnitude_scaling_sigma=0.0,
            subduction_rupture_aspect_ratio=1.5,
            subduction_rupture_floating_type='downdip',
            quantile_levels=[],
            compute_mean_hazard_curve=True)

        actual_jp = engine.import_job_profile(cfg_path)

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
