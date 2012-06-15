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


import unittest

from openquake.db import models
from openquake.job import validation

from tests.utils import helpers


class ClassicalHazardJobFormTestCase(unittest.TestCase):
    """Tests for classical hazard job param validation."""

    VALID_IML_IMT = {
        "PGV": [0.005, 0.007, 0.0098],
        "IA": [0.005, 0.007, 0.0098],
        "PGD": [0.005, 0.007, 0.0098],
        "MMI": [0.005, 0.007, 0.0098],
        "PGA": [0.007, 0.005, 0.0098],
        "RSD": [0.005, 0.007, 0.0098],
        "SA(0)": [0.005, 0.007, 0.0098],
        "SA(0.025)": [0.005, 0.007, 0.0098],
        "SA(2.5)": [0.005, 0.007, 0.0098],
        "SA(0.45)": [0.005, 0.007, 0.0098],
    }

    INVALID_IML_IMT = {
        "PGZ": [0.005, 0.007, 0.0098],
        "IA": [0.0, 0.007, 0.0098],
        "PGD": [0.005, 0.007, 0.0098],
        "MMI": [0.005, 0.007, 0.0098],
        "PGA": [-0.001, 0.6, 0.0098],
        "RSD": [0.005, 0.007, 0.0098],
        "SA(-0.1)": [0.005, 0.007, 0.0098],
        "SA(0.025)": [0.005, 0.007, 0.0098],
        "SA<2.5>": [0.005, 0.007, 0.0098],
        "SA(0.45)": [0.005, 0.007, 0.0098],
    }


    def test_hazard_job_profile_is_valid(self):
        hjp = models.HazardJobProfile(
            owner=helpers.default_user(),
            description='',
            calculation_mode='classical',
            random_seed=37,
            number_of_logic_tree_samples=1,
            rupture_mesh_spacing=0.001,
            width_of_mfd_bin=0.001,
            area_source_discretization=0.001,
            reference_vs30_value=0.001,
            reference_vs30_type='measured',
            reference_depth_to_2pt5km_per_sec=0.001,
            reference_depth_to_1pt0km_per_sec=0.001,
            investigation_time=1.0,
            intensity_measure_types_and_levels=self.VALID_IML_IMT,
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )
        form = validation.ClassicalHazardJobForm(instance=hjp, files=None)
        import nose; nose.tools.set_trace()
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_hazard_job_profile_is_not_valid(self):
        # test with an invalid job profile
        # several parameters are given invalid values
        expected_errors = {
            'area_source_discretization': [
                'Area source discretization must be > 0',
            ],
            'calculation_mode': [
                'Select a valid choice. Classical is not one of the available '
                'choices.',
                'Calculation mode must be "classical"',
            ],
            'investigation_time': ['Investigation time must be > 0'],
            'maximum_distance': ['Maximum distance must be > 0'],
            'number_of_logic_tree_samples': [
                'Number of logic tree samples must be > 0',
            ],
            'poes_hazard_maps': [
                'PoEs for hazard maps must be in the range [0, 1]',
            ],
            'quantile_hazard_curves': [
                'Quantile hazard curve values must in the range [0, 1]'
            ],
            'random_seed': [
                'Random seed must be a value from -2147483648 to 2147483647 '
                '(inclusive)',
            ],
            'rupture_mesh_spacing': ['Rupture mesh spacing must be > 0'],
            'truncation_level': ['Truncation level must be >= 0'],
            'width_of_mfd_bin': ['Width of MFD bin must be > 0'],
        }


        hjp = models.HazardJobProfile(
            owner=helpers.default_user(),
            description='',
            # TODO: customize the field to parse right from the config file?
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0,
            sites='MULTIPOINT((-122.0 38.113), (-122.114 38.113))',
            calculation_mode='Classical',
            random_seed=2147483648,
            number_of_logic_tree_samples=0,
            rupture_mesh_spacing=0,
            width_of_mfd_bin=0,
            area_source_discretization=0,
            investigation_time=0,
            intensity_measure_types_and_levels=self.INVALID_IML_IMT,
            truncation_level=-0.1,
            maximum_distance=0,
            quantile_hazard_curves=[0.0, -0.1, 1.1],
            poes_hazard_maps=[1.00001, -0.5, 0.0],
        )

        form = validation.ClassicalHazardJobForm(instance=hjp, files=None)

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)
