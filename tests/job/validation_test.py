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

    VALID_IML_IMT_JSON = r"""
{"PGV": [0.005, 0.007, 0.0098],
"IA": [0.005, 0.007, 0.0098],
"PGD": [0.005, 0.007, 0.0098],
"MMI": [0.005, 0.007, 0.0098],
"PGA": [0.005, 0.007, 0.0098],
"RSD": [0.005, 0.007, 0.0098],
"SA(0)": [0.005, 0.007, 0.0098],
"SA(0.025)": [0.005, 0.007, 0.0098],
"SA(2.5)": [0.005, 0.007, 0.0098],
"SA(0.45)": [0.005, 0.007, 0.0098]}"""

    INVALID_IML_IMT_JSON = r"""
{"PGZ": [0.005, 0.007, 0.0098],
"IA": [0.0, 0.007, 0.0098],
"PGD": [0.005, 0.007, 0.0098],
"MMI": [0.005, 0.007, 0.0098],
"PGA": [0.005, 0.007, 0.0098],
"RSD": [0.005, 0.007, 0.0098],
"SA(-0.1)": [0.005, 0.007, 0.0098],
"SA(0.025)": [0.005, 0.007, 0.0098],
"SA<2.5>": [0.005, 0.007, 0.0098],
"SA(0.45)": [0.005, 0.007, 0.0098]}"""


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
            investigation_time=1.0,
            intensity_measure_types_and_levels=(self.VALID_IML_IMT_JSON),
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )
        form = validation.ClassicalHazardJobForm(instance=hjp, files=None)

        self.assertTrue(form.is_valid())

    def test_hazard_job_profile_is_not_valid(self):
        # test with an invalid job profile
        # several parameters are given invalid values
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
            calculation_mode='classical',
            random_seed=2147483648,
            number_of_logic_tree_samples=0,
            rupture_mesh_spacing=0,
            width_of_mfd_bin=0,
            area_source_discretization=0,
            investigation_time=0,
            intensity_measure_types_and_levels=(self.INVALID_IML_IMT_JSON),
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )

        form = validation.ClassicalHazardJobForm(instance=hjp, files=None)

        self.assertFalse(form.is_valid())
        print form.errors
        import nose; nose.tools.set_trace()
        self.assertTrue(False)
