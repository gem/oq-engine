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


import json
import unittest
import itertools

from openquake.db import models
from openquake.job import validation

from tests.utils import helpers


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

VALID_IML_IMT_STR = json.dumps(VALID_IML_IMT)

INVALID_IML_IMT = {
    "PGZ": [0.005, 0.007, 0.0098],
    "IA": [0.0, 0.007, 0.0098],
    "PGD": [],
    "MMI": (0.005, 0.007, 0.0098),
    "PGA": [-0.001, 0.6, 0.0098],
    "RSD": [0.005, 0.007, 0.0098],
    "SA(-0.1)": [0.005, 0.007, 0.0098],
    "SA(0.025)": [],
    "SA<2.5>": [0.005, 0.007, 0.0098],
    "SA(0.45)": [0.005, 0.007, 0.0098],
    "SA(2x)": [0.005, 0.007, 0.0098],
}


class ClassicalHazardCalculationFormTestCase(unittest.TestCase):
    """Tests for classical hazard job param validation."""

    def test_hazard_calculation_is_valid_region_only(self):
        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0.001,
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
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )
        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None
        )
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_hazard_calculation_is_valid_region_only_as_str_list(self):
        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region='-122.0, 38.113, -122.114, 38.113, -122.57, 38.111',
            region_grid_spacing=0.001,
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
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )
        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None
        )
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_hazard_calculation_is_valid_with_site_model(self):
        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0.001,
            calculation_mode='classical',
            random_seed=37,
            number_of_logic_tree_samples=1,
            rupture_mesh_spacing=0.001,
            width_of_mfd_bin=0.001,
            area_source_discretization=0.001,
            # The 4 `reference` parameters should be ignored since the site
            # model file is specified.
            # We can define invalid values here; the validator shouldn't care.
            reference_vs30_value=0,
            reference_vs30_type=None,
            reference_depth_to_2pt5km_per_sec=0,
            reference_depth_to_1pt0km_per_sec=0,
            investigation_time=1.0,
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )
        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=dict(site_model_file=object())
        )
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_hazard_calculation_is_valid_sites_only(self):
        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            sites='MULTIPOINT((-122.114 38.113))',
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
            intensity_measure_types_and_levels=VALID_IML_IMT_STR,
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves='true',
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )
        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None
        )
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_hazard_calculation_is_valid_sites_only_as_str_list(self):
        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            sites='-122.114, 38.113, -122.115, 38.114',
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
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )
        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None
        )
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_hazard_calculation_is_not_valid_missing_geom(self):
        expected_errors = {
            'region': ['Must specify either `region` or `sites`.'],
            'sites': ['Must specify either `region` or `sites`.'],
        }

        hc = models.HazardCalculation(
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
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )
        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None
        )
        self.assertFalse(form.is_valid())

        self.assertEqual(expected_errors, dict(form.errors))

    def test_hazard_calculation_is_not_valid(self):
        # test with an invalid job profile
        # several parameters are given invalid values
        expected_errors = {
            'area_source_discretization': [
                'Area source discretization must be > 0',
            ],
            'calculation_mode': [
                'Calculation mode must be "classical"',
            ],
            'investigation_time': ['Investigation time must be > 0'],
            'maximum_distance': ['Maximum distance must be > 0'],
            'number_of_logic_tree_samples': [
                'Number of logic tree samples must be >= 0',
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
            'intensity_measure_types_and_levels': [
                'SA(-0.1): SA period values must be >= 0',
                ('SA<2.5>: SA must be specified with a period value, in the '
                 'form `SA(N)`, where N is a value >= 0'),
                'IA: IMLs must be > 0',
                'PGD: IML lists must have at least 1 value',
                'SA(2x): SA period value should be a float >= 0',
                'PGA: IMLs must be > 0',
                'PGZ: Invalid intensity measure type',
                'SA(0.025): IML lists must have at least 1 value',
                'MMI: IMLs must be specified as a list of floats',
            ],
            'region': ['Cannot specify `region` and `sites`. Choose one.'],
            'reference_vs30_value': ['Reference VS30 value must be > 0'],
            'reference_vs30_type': [
                'Reference VS30 type must be either "measured" or "inferred"',
            ],
            'reference_depth_to_1pt0km_per_sec': [
                'Reference depth to 1.0 km/sec must be > 0',
            ],
            'reference_depth_to_2pt5km_per_sec': [
                'Reference depth to 2.5 km/sec must be > 0',
            ],

        }

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0,
            sites='-122.0  38.113 , -122.114,38.113',
            calculation_mode='Classical',
            random_seed=2147483648,
            number_of_logic_tree_samples=-1,
            rupture_mesh_spacing=0,
            width_of_mfd_bin=0,
            area_source_discretization=0,
            reference_vs30_value=0,
            reference_depth_to_2pt5km_per_sec=0,
            reference_depth_to_1pt0km_per_sec=0,
            investigation_time=0,
            intensity_measure_types_and_levels=INVALID_IML_IMT,
            truncation_level=-0.1,
            maximum_distance=0,
            quantile_hazard_curves=[0.0, -0.1, 1.1],
            poes_hazard_maps=[1.00001, -0.5, 0.0],
        )

        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_hazard_calculation_is_not_valid_region_only(self):
        expected_errors = {
            'region_grid_spacing': ['Region grid spacing must be > 0'],
            'region': [
                'Invalid region geomerty: Self-intersection[0 0]',
                'Region geometry can only be a single linear ring',
                'Longitude values must in the range [-180, 180]',
                'Latitude values must be in the range [-90, 90]'],
            'reference_vs30_value': ['Reference VS30 value must be > 0'],
            'reference_vs30_type': [
                'Reference VS30 type must be either "measured" or "inferred"',
            ],
            'reference_depth_to_1pt0km_per_sec': [
                'Reference depth to 1.0 km/sec must be > 0',
            ],
            'reference_depth_to_2pt5km_per_sec': [
                'Reference depth to 2.5 km/sec must be > 0',
            ],
        }

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-180.001 90.001, 180.001 -90.001, -179.001 -89.001, '
                '179.001 89.001, -180.001 90.001), (1 1, 2 2, 3 3, 4 4, 1 1))'
            ),
            region_grid_spacing=0,
            calculation_mode='classical',
            random_seed=2147483647,
            number_of_logic_tree_samples=1,
            rupture_mesh_spacing=1,
            width_of_mfd_bin=1,
            area_source_discretization=1,
            investigation_time=1,
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0,
            maximum_distance=1,
            quantile_hazard_curves=[0.0, 0.1, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )

        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_hazard_calculation_is_not_valid_missing_grid_spacing(self):
        expected_errors = {
            'region': ['`region` requires `region_grid_spacing`'],
        }

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
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
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )

        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_hazard_calculation_is_not_valid_sites_only(self):
        expected_errors = {
            'sites': [
                'Longitude values must in the range [-180, 180]',
                'Latitude values must be in the range [-90, 90]',
            ],
            'reference_vs30_value': ['Reference VS30 value must be > 0'],
            'reference_vs30_type': [
                'Reference VS30 type must be either "measured" or "inferred"',
            ],
            'reference_depth_to_1pt0km_per_sec': [
                'Reference depth to 1.0 km/sec must be > 0',
            ],
            'reference_depth_to_2pt5km_per_sec': [
                'Reference depth to 2.5 km/sec must be > 0',
            ],
        }

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            sites='MULTIPOINT((-180.001 90.001), (180.001 -90.001))',
            calculation_mode='classical',
            random_seed=2147483647,
            number_of_logic_tree_samples=1,
            rupture_mesh_spacing=1,
            width_of_mfd_bin=1,
            area_source_discretization=1,
            investigation_time=1,
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0,
            maximum_distance=1,
            quantile_hazard_curves=[0.0, 0.1, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )

        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_hazard_calculation_is_not_valid_missing_export_dir(self):
        # When the user specifies '--exports' on the command line the
        # 'export_dir' parameter must be present in the .ini file.
        err = ('--exports specified on the command line but the '
               '"export_dir" parameter is missing in the .ini file')
        expected_errors = {
            'export_dir': [err],
        }

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0.001,
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
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )

        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None, exports=['xml']
        )
        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_hazard_calculation_is_valid_with_no_exports(self):
        # When the user does not specify '--exports' on the command line the
        # 'export_dir' parameter needs not be present in the .ini file.
        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0.001,
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
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0.0,
            maximum_distance=100.0,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.0, 0.5, 1.0],
            poes_hazard_maps=[1.0, 0.5, 0.0],
        )

        form = validation.ClassicalHazardCalculationForm(
            instance=hc, files=None
        )
        self.assertTrue(form.is_valid())


class EventBasedHazardCalculationFormTestCase(unittest.TestCase):

    def test_ses_per_logic_tree_path_is_not_valid(self):
        expected_errors = {
            'ses_per_logic_tree_path': [
                '`Stochastic Event Sets Per Sample` (ses_per_logic_tree_path) '
                'must be > 0'],
        }

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0.001,
            calculation_mode='event_based',
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
            intensity_measure_types=VALID_IML_IMT.keys(),
            truncation_level=0.0,
            maximum_distance=100.0,
        )
        form = validation.EventBasedHazardCalculationForm(
            instance=hc, files=None
        )
        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_valid_event_based_params(self):
        subset_iml_imt = VALID_IML_IMT.copy()
        subset_iml_imt.pop('PGA')

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0.001,
            calculation_mode='event_based',
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
            intensity_measure_types=VALID_IML_IMT.keys(),
            # intensity_measure_types_and_levels just needs to be a subset of
            # intensity_measure_types
            intensity_measure_types_and_levels=subset_iml_imt,
            truncation_level=0.0,
            maximum_distance=100.0,
            ses_per_logic_tree_path=5,
            ground_motion_correlation_model='JB2009',
            ground_motion_correlation_params={"vs30_clustering": True},
            complete_logic_tree_ses=False,
            complete_logic_tree_gmf=True,
            ground_motion_fields=True,
            hazard_curves_from_gmfs=True,
            mean_hazard_curves=True,
            quantile_hazard_curves=[0.5, 0.95],
            poes_hazard_maps=[0.1, 0.2],
        )
        form = validation.EventBasedHazardCalculationForm(
            instance=hc, files=None
        )

        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_invalid_imts(self):
        expected_errors = {
            'intensity_measure_types': [
                'SA(-0.1): SA period values must be >= 0',
                ('SA<2.5>: SA must be specified with a period value, in the '
                 'form `SA(N)`, where N is a value >= 0'),
                'SA(2x): SA period value should be a float >= 0',
                'PGZ: Invalid intensity measure type',
            ],
        }

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0.001,
            calculation_mode='event_based',
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
            intensity_measure_types=INVALID_IML_IMT.keys(),
            truncation_level=0.0,
            maximum_distance=100.0,
            ses_per_logic_tree_path=5,
            ground_motion_correlation_model='JB2009',
            ground_motion_correlation_params={"vs30_clustering": True},
            complete_logic_tree_ses=False,
            complete_logic_tree_gmf=True,
            ground_motion_fields=True,
        )
        form = validation.EventBasedHazardCalculationForm(
            instance=hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_hazard_curves_from_gmf_no_iml_imt(self):
        # Test a configuration where the user has requested to post-process
        # GMFs into hazard curves.
        # In this case, the configuration is missing the required
        # `intensity_measure_types_and_levels`.
        expected_errors = {
            'intensity_measure_types_and_levels': [
                '`hazard_curve_from_gmfs` requires '
                '`intensity_measure_types_and_levels`'],
        }

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0.001,
            calculation_mode='event_based',
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
            intensity_measure_types=VALID_IML_IMT.keys(),
            truncation_level=0.0,
            maximum_distance=100.0,
            ses_per_logic_tree_path=5,
            ground_motion_correlation_model='JB2009',
            ground_motion_correlation_params={"vs30_clustering": True},
            complete_logic_tree_ses=False,
            complete_logic_tree_gmf=True,
            ground_motion_fields=True,
            hazard_curves_from_gmfs=True,
        )
        form = validation.EventBasedHazardCalculationForm(
            instance=hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_hazard_curves_from_gmf_invalid_iml_imt(self):
        # Test a configuration where the user has requested to post-process
        # GMFs into hazard curves.
        # In this case, the configuration has the required
        # `intensity_measure_types_and_levels`, but the IMTs are not a subset
        # of `intensity_measure_types`.
        expected_errors = {
            'intensity_measure_types_and_levels': [
                'Unknown IMT(s) [SA(0)] in `intensity_measure_types`'],
        }
        iml_imt = VALID_IML_IMT.keys()
        iml_imt.pop()

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0.001,
            calculation_mode='event_based',
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
            intensity_measure_types=iml_imt,
            intensity_measure_types_and_levels=VALID_IML_IMT,
            truncation_level=0.0,
            maximum_distance=100.0,
            ses_per_logic_tree_path=5,
            ground_motion_correlation_model='JB2009',
            ground_motion_correlation_params={"vs30_clustering": True},
            complete_logic_tree_ses=False,
            complete_logic_tree_gmf=True,
            ground_motion_fields=True,
            hazard_curves_from_gmfs=True,
        )
        form = validation.EventBasedHazardCalculationForm(
            instance=hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_invalid_params_complet_lt_gmf_with_eb_enum(self):
        # When the `complete_logic_tree_gmf` is requested with end-branch
        # enumeration, this is not allowed. (The complete LT GMF is not a
        # useful artifact in this case.)
        expected_errors = {
            'complete_logic_tree_gmf': [
                '`complete_logic_tree_gmf` is not available with end branch '
                'enumeration'],
        }

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            region=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'
            ),
            region_grid_spacing=0.001,
            calculation_mode='event_based',
            random_seed=37,
            number_of_logic_tree_samples=0,
            rupture_mesh_spacing=0.001,
            width_of_mfd_bin=0.001,
            area_source_discretization=0.001,
            reference_vs30_value=0.001,
            reference_vs30_type='measured',
            reference_depth_to_2pt5km_per_sec=0.001,
            reference_depth_to_1pt0km_per_sec=0.001,
            investigation_time=1.0,
            intensity_measure_types=VALID_IML_IMT.keys(),
            truncation_level=0.0,
            maximum_distance=100.0,
            ses_per_logic_tree_path=5,
            ground_motion_correlation_model='JB2009',
            ground_motion_correlation_params={"vs30_clustering": True},
            complete_logic_tree_ses=False,
            complete_logic_tree_gmf=True,
            ground_motion_fields=True,
        )
        form = validation.EventBasedHazardCalculationForm(
            instance=hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)


class DisaggHazardCalculationFormTestCase(unittest.TestCase):

    def test_valid_disagg_calc(self):
        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            sites='MULTIPOINT((-122.114 38.113))',
            calculation_mode='disaggregation',
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
            intensity_measure_types_and_levels=VALID_IML_IMT_STR,
            truncation_level=0.1,
            maximum_distance=100.0,
            mag_bin_width=0.3,
            distance_bin_width=10.0,
            coordinate_bin_width=0.02,  # decimal degrees
            num_epsilon_bins=4,
        )
        form = validation.DisaggHazardCalculationForm(
            instance=hc, files=None
        )
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_invalid_disagg_calc(self):
        expected_errors = {
            'mag_bin_width': ['Magnitude bin width must be > 0.0'],
            'distance_bin_width': ['Distance bin width must be > 0.0'],
            'coordinate_bin_width': ['Coordinate bin width must be > 0.0'],
            'num_epsilon_bins': ['Number of epsilon bins must be > 0'],
            'truncation_level': ['Truncation level must be > 0 for'
                                 ' disaggregation calculations'],
        }

        hc = models.HazardCalculation(
            owner=helpers.default_user(),
            description='',
            sites='MULTIPOINT((-122.114 38.113))',
            calculation_mode='disaggregation',
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
            intensity_measure_types_and_levels=VALID_IML_IMT_STR,
            truncation_level=0.0,
            maximum_distance=100.0,
            mag_bin_width=0.0,
            distance_bin_width=0.0,
            coordinate_bin_width=0.0,  # decimal degrees
            num_epsilon_bins=0,
        )
        form = validation.DisaggHazardCalculationForm(
            instance=hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)


class ClassicalRiskCalculationFormTestCase(unittest.TestCase):
    def setUp(self):
        job, _ = helpers.get_risk_job('classical_psha_based_risk/job.ini',
                                          'simple_fault_demo_hazard/job.ini')
        self.compulsory_arguments = dict(
            calculation_mode="classical",
            lrem_steps_per_interval=5)
        self.other_args = dict(
            owner=helpers.default_user(),
            region_constraint=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'),
            hazard_output=job.risk_calculation.hazard_output)

    def test_valid_form(self):
        args = dict(self.compulsory_arguments.items())
        args.update(self.other_args)

        rc = models.RiskCalculation(**args)

        form = validation.ClassicalRiskCalculationForm(
            instance=rc, files=None)
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_invalid_form(self):

        def powerset(iterable):
            s = list(iterable)
            return itertools.chain.from_iterable(
                itertools.combinations(s, r) for r in range(len(s) + 1))

        for fields in list(powerset(self.compulsory_arguments))[1:]:
            compulsory_arguments = dict(self.compulsory_arguments.items())
            for field in fields:
                compulsory_arguments[field] = None
            compulsory_arguments.update(self.other_args)
            rc = models.RiskCalculation(**compulsory_arguments)

            form = validation.ClassicalRiskCalculationForm(
                instance=rc, files=None)

            self.assertFalse(form.is_valid(), fields)


class ClassicalRiskCalculationWithBCRFormTestCase(unittest.TestCase):
    def setUp(self):
        job, _ = helpers.get_risk_job('classical_psha_based_risk/job.ini',
                                      'simple_fault_demo_hazard/job.ini')
        self.compulsory_arguments = dict(
            calculation_mode="classical_bcr",
            lrem_steps_per_interval=5,
            interest_rate=0.05,
            asset_life_expectancy=40)

        self.other_args = dict(
            owner=helpers.default_user(),
            region_constraint=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'),
            hazard_output=job.risk_calculation.hazard_output)

    def test_valid_form(self):
        args = dict(self.compulsory_arguments.items())
        args.update(self.other_args)

        rc = models.RiskCalculation(**args)

        form = validation.ClassicalRiskCalculationWithBCRForm(
            instance=rc, files=None)
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_invalid_form(self):
        def powerset(iterable):
            s = list(iterable)
            return itertools.chain.from_iterable(
                itertools.combinations(s, r) for r in range(len(s) + 1))

        for fields in list(powerset(self.compulsory_arguments))[1:]:
            compulsory_arguments = dict(self.compulsory_arguments.items())
            for field in fields:
                compulsory_arguments[field] = None
            compulsory_arguments.update(self.other_args)
            rc = models.RiskCalculation(**compulsory_arguments)

            form = validation.ClassicalRiskCalculationWithBCRForm(
                instance=rc, files=None)

            self.assertFalse(form.is_valid(), fields)
