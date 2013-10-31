# Copyright (c) 2010-2013, GEM Foundation.
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


import itertools
import json
import unittest
import warnings

from openquake.engine import engine
from openquake.engine.db import models
from openquake.engine.job import validation

from tests.utils import helpers
from tests.utils.helpers import get_data_path


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


class ClassicalHazardFormTestCase(unittest.TestCase):
    """Tests for classical hazard job param validation."""

    def setUp(self):
        self.hc = models.HazardCalculation(
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
            poes=[1.0, 0.5, 0.0],
        )

    def test_hazard_calculation_is_valid_region_only(self):
        form = validation.ClassicalHazardForm(
            instance=self.hc, files=None
        )
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_hazard_calculation_is_valid_with_site_model(self):
        form = validation.ClassicalHazardForm(
            instance=self.hc, files=dict(site_model_file=object())
        )
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_hazard_calculation_is_valid_sites_only(self):
        self.hc.region = None
        self.hc.region_grid_spacing = None
        self.hc.sites = 'MULTIPOINT((-122.114 38.113))'
        form = validation.ClassicalHazardForm(
            instance=self.hc, files=None
        )
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_hazard_calculation_is_not_valid_missing_geom(self):
        expected_errors = {
            'region': [
                'Must specify either `region`, `sites` or `exposure_file`.'],
            'sites': [
                'Must specify either `region`, `sites` or `exposure_file`.'],
        }
        self.hc.region = None
        self.hc.sites = None
        form = validation.ClassicalHazardForm(
            instance=self.hc, files=None
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
            'poes': [
                '`poes` values must be in the range [0, 1]',
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
            reference_vs30_type=None,
            reference_vs30_value=0,
            reference_depth_to_2pt5km_per_sec=0,
            reference_depth_to_1pt0km_per_sec=0,
            investigation_time=0,
            intensity_measure_types_and_levels=INVALID_IML_IMT,
            truncation_level=-0.1,
            maximum_distance=0,
            quantile_hazard_curves=[0.0, -0.1, 1.1],
            poes=[1.00001, -0.5, 0.0],
        )

        form = validation.ClassicalHazardForm(
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
        }

        self.hc.region_grid_spacing = 0
        self.hc.region = (
            'POLYGON((-180.001 90.001, 180.001 -90.001, -179.001 -89.001, '
            '179.001 89.001, -180.001 90.001), (1 1, 2 2, 3 3, 4 4, 1 1))'
        )

        form = validation.ClassicalHazardForm(
            instance=self.hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_hazard_calculation_is_not_valid_missing_grid_spacing(self):
        expected_errors = {
            'region': ['`region` requires `region_grid_spacing`'],
        }

        self.hc.region_grid_spacing = None

        form = validation.ClassicalHazardForm(
            instance=self.hc, files=None
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
        }

        self.hc.region = None
        self.hc.region_grid_spacing = None
        self.hc.sites = 'MULTIPOINT((-180.001 90.001), (180.001 -90.001))'

        form = validation.ClassicalHazardForm(
            instance=self.hc, files=None
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

        form = validation.ClassicalHazardForm(
            instance=self.hc, files=None, exports=['xml']
        )
        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_classical_hc_hazard_maps_uhs_no_poes(self):
        # Test that errors are reported if `hazard_maps` and
        # `uniform_hazard_spectra` are `true` but no `poes` are
        # specified.
        expected_errors = {
            'hazard_maps': ['`poes` are required to compute hazard maps'],
            'uniform_hazard_spectra': ['`poes` are required to compute UHS'],
        }

        self.hc.hazard_maps = True
        self.hc.uniform_hazard_spectra = True
        self.hc.poes = None

        form = validation.ClassicalHazardForm(
            instance=self.hc, files=None
        )
        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_is_valid_warns(self):
        # `is_valid` should warn if we specify a `vulnerability_file` as well
        # as `intensity_measure_types_and_levels`
        form = validation.ClassicalHazardForm(
            instance=self.hc, files=dict(
                structural_vulnerability_file=object())
        )

        with warnings.catch_warnings(record=True) as w:
            form.is_valid()

        expected_warnings = [
            '`intensity_measure_types_and_levels` is ignored when a '
            '`vulnerability_file` is specified',
        ]

        actual_warnings = [m.message.message for m in w]
        self.assertEqual(expected_warnings, actual_warnings)


class EventBasedHazardFormTestCase(unittest.TestCase):

    def setUp(self):
        subset_iml_imt = VALID_IML_IMT.copy()
        subset_iml_imt.pop('PGA')

        self.hc = models.HazardCalculation(
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
            poes=[0.1, 0.2],
        )

    def test_valid_event_based_params(self):
        form = validation.EventBasedHazardForm(
            instance=self.hc, files=None
        )

        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_ses_per_logic_tree_path_is_not_valid(self):
        expected_errors = {
            'ses_per_logic_tree_path': [
                '`Stochastic Event Sets Per Sample` (ses_per_logic_tree_path) '
                'must be > 0'],
        }

        self.hc.ses_per_logic_tree_path = -1

        form = validation.EventBasedHazardForm(
            instance=self.hc, files=None
        )
        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

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

        self.hc.intensity_measure_types = INVALID_IML_IMT.keys()
        self.hc.intensity_measure_types_and_levels = None
        self.hc.hazard_curves_from_gmfs = False

        form = validation.EventBasedHazardForm(
            instance=self.hc, files=None
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
                '`hazard_curves_from_gmfs` requires '
                '`intensity_measure_types_and_levels`'],
        }

        self.hc.intensity_measure_types_and_levels = None

        form = validation.EventBasedHazardForm(
            instance=self.hc, files=None
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

        self.hc.intensity_measure_types = iml_imt
        self.hc.intensity_measure_types_and_levels = VALID_IML_IMT

        form = validation.EventBasedHazardForm(
            instance=self.hc, files=None
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

        self.hc.number_of_logic_tree_samples = 0
        self.hc.complete_logic_tree_gmf = True

        form = validation.EventBasedHazardForm(
            instance=self.hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_is_valid_warns(self):
        # `is_valid` should warn if we specify a `vulnerability_file` as well
        # as `intensity_measure_types` and `intensity_measure_types_and_levels`
        subset_iml_imt = VALID_IML_IMT.copy()
        subset_iml_imt.pop('PGA')

        # intensity_measure_types_and_levels just needs to be a subset of
        # intensity_measure_types
        self.hc.intensity_measure_types_and_levels = subset_iml_imt

        form = validation.EventBasedHazardForm(
            instance=self.hc, files=dict(
                structural_vulnerability_file=object())
        )

        with warnings.catch_warnings(record=True) as w:
            form.is_valid()

        expected_warnings = [
            '`intensity_measure_types_and_levels` is ignored when a '
            '`vulnerability_file` is specified',
            '`intensity_measure_types` is ignored when a `vulnerability_file` '
            'is specified',
        ]

        actual_warnings = [m.message.message for m in w]
        self.assertEqual(sorted(expected_warnings), sorted(actual_warnings))

    def test_gmfs_false_hazard_curves_true(self):
        # An error should be raised if `hazard_curves_from_gmfs` is `True`, but
        # `ground_motion_fields` is `False`.
        # GMFs are needed to compute hazard curves.
        expected_errors = {
            'hazard_curves_from_gmfs': ['`hazard_curves_from_gmfs` requires '
                                        '`ground_motion_fields` to be `true`'],
        }
        self.hc.ground_motion_fields = False
        self.hc.hazard_curves_from_gmfs = True

        form = validation.EventBasedHazardForm(instance=self.hc, files=None)

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

class DisaggHazardFormTestCase(unittest.TestCase):

    def setUp(self):
        self.hc = models.HazardCalculation(
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
            poes_disagg=[0.02, 0.1],
        )

    def test_valid_disagg_calc(self):
        form = validation.DisaggHazardForm(
            instance=self.hc, files=None
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
            'poes_disagg': ['PoEs for disaggregation must be in the range'
                            ' [0, 1]'],
        }

        self.hc.mag_bin_width = 0.0
        self.hc.distance_bin_width = 0.0
        self.hc.coordinate_bin_width = 0.0  # decimal degrees
        self.hc.num_epsilon_bins = 0
        self.hc.poes_disagg = [1.00001, -0.5, 0.0]
        self.hc.truncation_level = 0.0

        form = validation.DisaggHazardForm(instance=self.hc, files=None)

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

        # test with an empty `poes_disagg` list
        self.hc.poes_disagg = []
        form = validation.DisaggHazardForm(instance=self.hc, files=None)
        expected_errors['poes_disagg'] = [(
            '`poes_disagg` must contain at least 1 value')]
        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_invalid_disagg_calc_truncation_not_set(self):
        expected_errors = {
            'mag_bin_width': ['Magnitude bin width must be > 0.0'],
            'distance_bin_width': ['Distance bin width must be > 0.0'],
            'coordinate_bin_width': ['Coordinate bin width must be > 0.0'],
            'num_epsilon_bins': ['Number of epsilon bins must be > 0'],
            'truncation_level': ['Truncation level must be set for'
                                 ' disaggregation calculations'],
            'poes_disagg': ['PoEs for disaggregation must be in the range'
                            ' [0, 1]'],
        }

        self.hc.truncation_level = None
        self.hc.mag_bin_width = 0.0
        self.hc.distance_bin_width = 0.0
        self.hc.coordinate_bin_width = 0.0  # decimal degrees
        self.hc.num_epsilon_bins = 0
        self.hc.poes_disagg = [1.00001, -0.5, 0.0]

        form = validation.DisaggHazardForm(instance=self.hc, files=None)

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))

    def test_is_valid_warns(self):
        # `is_valid` should warn if we specify a `vulnerability_file` as well
        # as `intensity_measure_types_and_levels`
        form = validation.DisaggHazardForm(
            instance=self.hc, files=dict(
                structural_vulnerability_file=object())
        )

        with warnings.catch_warnings(record=True) as w:
            form.is_valid()

        expected_warnings = [
            '`intensity_measure_types_and_levels` is ignored when a '
            '`vulnerability_file` is specified',
        ]

        actual_warnings = [m.message.message for m in w]
        self.assertEqual(expected_warnings, actual_warnings)


class ScenarioFormTestCase(unittest.TestCase):

    def setUp(self):
        self.hc = models.HazardCalculation(
            description='',
            sites='MULTIPOINT((-122.114 38.113))',
            calculation_mode='scenario',
            random_seed=37,
            rupture_mesh_spacing=0.001,
            reference_vs30_value=0.001,
            reference_vs30_type='measured',
            reference_depth_to_2pt5km_per_sec=0.001,
            reference_depth_to_1pt0km_per_sec=0.001,
            intensity_measure_types=VALID_IML_IMT.keys(),
            truncation_level=0.1,
            maximum_distance=100.0,
            gsim='BooreAtkinson2008',
            ground_motion_correlation_model='JB2009',
            number_of_ground_motion_fields=10,
        )

    def test_valid_scenario_calc(self):
        form = validation.ScenarioHazardForm(
            instance=self.hc, files=None
        )
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_invalid_scenario_calc(self):
        expected_errors = {
            'gsim': ["The gsim u'BooreAtkinson208' is not in in \
openquake.hazardlib.gsim"],
            'number_of_ground_motion_fields': [
                'The number_of_ground_motion_fields must be a positive '
                'integer, got -10']
        }
        self.hc.number_of_ground_motion_fields = -10
        self.hc.gsim = 'BooreAtkinson208'
        form = validation.ScenarioHazardForm(
            instance=self.hc, files=None
        )

        self.assertFalse(form.is_valid())
        equal, err = helpers.deep_eq(expected_errors, dict(form.errors))
        self.assertTrue(equal, err)

    def test_is_valid_warns(self):
        # `is_valid` should warn if we specify a `vulnerability_file` as well
        # as `intensity_measure_types`
        form = validation.ScenarioHazardForm(
            instance=self.hc, files=dict(
                structural_vulnerability_file=object())
        )

        with warnings.catch_warnings(record=True) as w:
            form.is_valid()

        expected_warnings = [
            '`intensity_measure_types` is ignored when a '
            '`vulnerability_file` is specified',
        ]

        actual_warnings = [m.message.message for m in w]
        self.assertEqual(expected_warnings, actual_warnings)


class ClassicalRiskFormTestCase(unittest.TestCase):
    def setUp(self):
        job, _ = helpers.get_fake_risk_job(
            get_data_path('classical_psha_based_risk/job.ini'),
            get_data_path('simple_fault_demo_hazard/job.ini')
        )
        self.compulsory_arguments = dict(
            lrem_steps_per_interval=5)
        self.other_args = dict(
            calculation_mode="classical",
            region_constraint=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'),
            hazard_output=job.risk_calculation.hazard_output)

    def test_valid_form(self):
        args = dict(self.compulsory_arguments.items())
        args.update(self.other_args)

        rc = models.RiskCalculation(**args)

        form = validation.ClassicalRiskForm(
            instance=rc, files=None)
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_invalid_form(self):

        def powerset(iterable):
            s = list(iterable)
            return itertools.chain.from_iterable(
                itertools.combinations(s, r) for r in range(len(s) + 1))

        # for each set of compulsory arguments, we set them to None
        for fields in list(powerset(self.compulsory_arguments))[1:]:
            arguments = dict(self.compulsory_arguments.items())
            for field in fields:
                arguments[field] = None

            # then we set other not-compulsory arguments
            arguments.update(self.other_args)

            rc = models.RiskCalculation(**arguments)

            form = validation.ClassicalRiskForm(instance=rc, files=None)

            self.assertFalse(form.is_valid(), fields)


class ClassicalBCRRiskFormTestCase(unittest.TestCase):
    def setUp(self):
        job, _ = helpers.get_fake_risk_job(
            get_data_path('classical_psha_based_risk/job.ini'),
            get_data_path('simple_fault_demo_hazard/job.ini')
        )
        self.compulsory_arguments = dict(
            calculation_mode="classical_bcr",
            lrem_steps_per_interval=5,
            interest_rate=0.05,
            asset_life_expectancy=40)

        self.other_args = dict(
            region_constraint=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'),
            hazard_output=job.risk_calculation.hazard_output)

    def test_valid_form(self):
        args = dict(self.compulsory_arguments.items())
        args.update(self.other_args)

        rc = models.RiskCalculation(**args)

        form = validation.ClassicalBCRRiskForm(
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
            form = validation.ClassicalBCRRiskForm(instance=rc, files=None)

            self.assertFalse(form.is_valid(), fields)


class EventBasedBCRRiskForm(unittest.TestCase):

    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            get_data_path('event_based_bcr/job.ini'),
            get_data_path('event_based_hazard/job.ini')
        )

    def test_valid_form(self):
        region_constraint = (
            'POLYGON((-122.0 38.113, -122.114 38.113, '
            '-122.57 38.111, -122.0 38.113))'
        )

        rc = models.RiskCalculation(
            calculation_mode="event_based_bcr",
            region_constraint=region_constraint,
            hazard_output=self.job.risk_calculation.hazard_output,
            interest_rate=0.05,
            asset_life_expectancy=40,
        )

        form = validation.EventBasedBCRRiskForm(
            instance=rc, files=None)

        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_invalid_form(self):
        region_constraint = (
            'POLYGON((-122.0 38.113, -122.114 38.113, '
            '-122.57 38.111, -122.0 38.113))'
        )

        rc = models.RiskCalculation(
            calculation_mode="event_based_bcr",
            region_constraint=region_constraint,
            hazard_output=self.job.risk_calculation.hazard_output,
        )

        form = validation.EventBasedBCRRiskForm(
            instance=rc, files=None)

        self.assertFalse(form.is_valid())


class EventBasedRiskValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            get_data_path('event_based_risk/job.ini'),
            get_data_path('event_based_hazard/job.ini')
        )

    def test_valid_form_with_default_resolution(self):
        rc = models.RiskCalculation(
            calculation_mode="event_based",
            region_constraint=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'),
            hazard_output=self.job.risk_calculation.hazard_output)

        form = validation.EventBasedRiskForm(
            instance=rc, files=None)
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_valid_form_with_custom_resolution(self):
        rc = models.RiskCalculation(
            calculation_mode="event_based",
            loss_curve_resolution=60,
            region_constraint=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'),
            hazard_output=self.job.risk_calculation.hazard_output)

        form = validation.EventBasedRiskForm(
            instance=rc, files=None)
        self.assertTrue(form.is_valid(), dict(form.errors))

    def test_invalid_form(self):
        rc = models.RiskCalculation(
            calculation_mode="event_based",
            region_constraint=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'),
            hazard_output=self.job.risk_calculation.hazard_output,
            sites_disagg='-180.1 38.113, -122.114 38.113',
            coordinate_bin_width=0.0,
            loss_curve_resolution=0,
            mag_bin_width=0.0,
        )

        expected_errors = {
            'coordinate_bin_width': ['Coordinate bin width must be > 0.0'],
            'distance_bin_width': ['Distance bin width must be > 0.0'],
            'loss_curve_resolution': ['Loss Curve Resolution must be >= 1'],
            'mag_bin_width': ['Magnitude bin width must be > 0.0'],
            'sites_disagg': ['Longitude values must in the range [-180, 180]',
                             'disaggregation requires mag_bin_width, '
                             'coordinate_bin_width, distance_bin_width'],
        }

        form = validation.EventBasedRiskForm(
            instance=rc, files=None)
        self.assertFalse(form.is_valid())
        self.assertEqual(expected_errors, dict(form.errors))


class ScenarioRiskValidationTestCase(unittest.TestCase):

    def test_invalid_form(self):
        rc = models.RiskCalculation(
            calculation_mode='scenario',
            region_constraint=(
                'POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
                '-122.0 38.113))'),
            maximum_distance=100,
            master_seed=666,
            asset_correlation='foo',
            insured_losses=True,
        )

        form = validation.ScenarioRiskForm(
            instance=rc,
            files=dict(occupants_vulnerability_file=object())
        )

        expected_errors = {
            'asset_correlation': [u'Enter a number.',
                                  u'Asset Correlation must be >= 0 and <= 1'],
             'time_event': ['Scenario Risk requires time_event when an '
                            'occupants vulnerability model is given'],
        }
        self.assertFalse(form.is_valid())
        self.assertEqual(expected_errors, dict(form.errors))


class ValidateTestCase(unittest.TestCase):
    """
    Tests for :func:`openquake.engine.job.validation.validate`.
    """

    def test_validate_warns(self):
        # Test that `validate` raises warnings if unnecessary parameters are
        # specified for a given calculation.
        # For example, `ses_per_logic_tree_path` is an event-based hazard
        # param; if this param is specified for a classical hazard job, a
        # warning should be raised.
        cfg_file = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        job = engine.prepare_job()
        params = engine.parse_config(open(cfg_file, 'r'))
        # Add a few superfluous parameters:
        params['ses_per_logic_tree_path'] = 5
        params['ground_motion_correlation_model'] = 'JB2009'
        calculation = engine.create_calculation(
            models.HazardCalculation, params)
        job.hazard_calculation = calculation
        job.save()

        with warnings.catch_warnings(record=True) as w:
            validation.validate(job, 'hazard', params, ['xml'])

        expected_warnings = [
            "Unknown parameter '%s' for calculation mode 'classical'."
            " Ignoring." % x for x in ('ses_per_logic_tree_path',
                                       'ground_motion_correlation_model')
        ]

        actual_warnings = [m.message.message for m in w]
        self.assertEqual(sorted(expected_warnings), sorted(actual_warnings))
