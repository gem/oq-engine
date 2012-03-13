# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

"""
This module tests the logic related to the engine configuration
and its validation.
"""

from openquake import engine
from openquake.job import config
from openquake.job.config import BCRValidator
from openquake.job.config import ClassicalValidator
from openquake.job.config import ClassicalRiskValidator
from openquake.job.config import DisaggregationValidator
from openquake.job.config import EventBasedRiskValidator
from openquake.job.config import HazardMandatoryParamsValidator
from openquake.job.config import RiskMandatoryParamsValidator
from openquake.job.config import ScenarioComputationValidator
from openquake.job.config import UHSValidator
from openquake.job.config import to_float_array
from openquake.job.config import to_str_array
from openquake.job.config import validate_numeric_sequence
from tests.utils import helpers

import unittest


class AlwaysTrueValidator(object):

    def is_valid(self):
        return (True, [])


class AlwaysFalseValidator(object):

    def __init__(self, error):
        self.error = error

    def is_valid(self):
        return (False, [self.error])


class ValidatorSetTestCase(unittest.TestCase):

    def test_an_empty_set_is_valid(self):
        self.assertTrue(config.ValidatorSet().is_valid()[0])

    def test_an_empty_set_has_no_error_messages(self):
        self.assertEquals([], config.ValidatorSet().is_valid()[1])

    def test_with_a_single_validator_the_result_is_the_validator(self):
        validator = config.ValidatorSet()
        validator.add(AlwaysTrueValidator())

        self.assertTrue(validator.is_valid()[0])

    def test_a_set_is_valid_when_all_validators_are_valid(self):
        validator = config.ValidatorSet()

        validator.add(AlwaysTrueValidator())
        validator.add(AlwaysTrueValidator())
        validator.add(AlwaysTrueValidator())

        self.assertTrue(validator.is_valid()[0])
        validator.add(AlwaysFalseValidator(""))

        self.assertFalse(validator.is_valid()[0])

    def test_no_error_messages_when_the_set_is_valid(self):
        validator = config.ValidatorSet()

        validator.add(AlwaysTrueValidator())
        validator.add(AlwaysTrueValidator())
        validator.add(AlwaysTrueValidator())

        self.assertEquals([], validator.is_valid()[1])

    def test_the_set_keeps_track_of_the_failed_validators(self):
        validator = config.ValidatorSet()

        validator.add(AlwaysTrueValidator())
        validator.add(AlwaysFalseValidator("MESSAGE#1"))
        validator.add(AlwaysFalseValidator("MESSAGE#2"))
        validator.add(AlwaysFalseValidator("MESSAGE#3"))

        self.assertFalse(validator.is_valid()[0])

        error_messages = ["MESSAGE#1", "MESSAGE#2", "MESSAGE#3"]
        self.assertEquals(error_messages, validator.is_valid()[1])

    def test_iter(self):
        """ValidatorSets are iterable (over the list of validators)."""
        vset = config.ValidatorSet()

        validators = [
            RiskMandatoryParamsValidator(None, None),
            DisaggregationValidator(None),
            ScenarioComputationValidator(None, None),
        ]

        for v in validators:
            vset.add(v)

        for cnt, val in enumerate(vset):
            self.assertEqual(validators[cnt], val)


class ConfigurationConstraintsTestCase(unittest.TestCase):

    def test_risk_mandatory_parameters(self):
        sections = [
            config.RISK_SECTION, config.HAZARD_SECTION, config.GENERAL_SECTION]

        dummy_exposure = helpers.touch()

        params = {}

        validator = config.default_validators(sections, params)
        self.assertFalse(validator.is_valid()[0])

        params = {config.EXPOSURE: dummy_exposure,
                  config.DEPTHTO1PT0KMPERSEC: "33.33",
                  config.VS30_TYPE: "measured"}

        validator = config.default_validators(sections, params)
        self.assertFalse(validator.is_valid()[0])

        params = {config.EXPOSURE: dummy_exposure,
                  config.REGION_GRID_SPACING: '0.5',
                  config.DEPTHTO1PT0KMPERSEC: "33.33",
                  config.VS30_TYPE: "measured"}

        validator = config.default_validators(sections, params)
        self.assertFalse(validator.is_valid()[0])

        params = {config.EXPOSURE: dummy_exposure,
                  config.INPUT_REGION: "1.0, 2.0, 3.0, 4.0, 5.0, 6.0",
                  config.REGION_GRID_SPACING: '0.5',
                  config.DEPTHTO1PT0KMPERSEC: "33.33",
                  config.VS30_TYPE: "measured"}

        validator = config.default_validators(sections, params)
        self.assertTrue(validator.is_valid()[0])

    def test_hazard_mandatory_parameters(self):
        sections = [config.HAZARD_SECTION]

        params = {config.CALCULATION_MODE: "CLASSICAL",
                  config.SITES: "37.9, -121.9",
                  config.DEPTHTO1PT0KMPERSEC: "33.33"}

        validator = config.default_validators(sections, params)
        self.assertFalse(validator.is_valid()[0])

        params = {config.CALCULATION_MODE: "CLASSICAL",
                  config.SITES: "37.9, -121.9",
                  config.DEPTHTO1PT0KMPERSEC: "33.33",
                  config.VS30_TYPE: "measured"}

        validator = config.default_validators(sections, params)
        self.assertTrue(validator.is_valid()[0])

    def test_mandatory_hazard_params_without_java_names(self):
        """
        All mandatory hazard parameters must have the 'java_name' property
        set.
        """
        sections = [config.HAZARD_SECTION]

        params = {config.CALCULATION_MODE: "CLASSICAL",
                  config.BASE_PATH: "/a/b/c",
                  config.SITES: "37.9, -121.9",
                  config.DEPTHTO1PT0KMPERSEC: "33.33",
                  config.VS30_TYPE: "measured"}

        # Add a paramer *without* a 'java_name' property to the mandatory
        # hazard parameters list in order to provoke the error.
        HazardMandatoryParamsValidator.MANDATORY_PARAMS.append("BASE_PATH")

        # Now validate ..
        validator = config.default_validators(sections, params)
        result, msgs = validator.is_valid()

        # .. and check that the validation blew up due to the lack of the
        # 'java_name' property.
        self.assertFalse(result)
        self.assertEqual(
            ["The following mandatory hazard parameter(s) lack a 'java_name' "
             "property: BASE_PATH"], msgs)

        # Restore the list with the mandatory hazard parameters.
        HazardMandatoryParamsValidator.MANDATORY_PARAMS.pop()

    def test_scenario_is_not_supported_alone(self):
        """When we specify a scenario computation, we only
        support hazard + risk jobs."""

        sections = [config.RISK_SECTION,
                config.HAZARD_SECTION, config.GENERAL_SECTION]

        params = {config.CALCULATION_MODE: config.SCENARIO_MODE,
                  'NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS': '1'}

        validator = config.ScenarioComputationValidator(sections, params)

        self.assertTrue(validator.is_valid()[0])

        sections.remove(config.RISK_SECTION)

        self.assertFalse(validator.is_valid()[0])

    def test_must_specify_geometry(self):
        '''
        If no geometry is specified (neither SITES nor REGION_VERTEX +
        REGION_GRID_SPACING), validation should fail
        '''
        # no geometry
        params = dict()

        validator = config.ComputationTypeValidator(params)
        self.assertFalse(validator.is_valid()[0])

        # invalid region geometry
        params = dict()
        params['REGION_VERTEX'] = '37.9, -121.9, 37.9, -121.6, 37.5, -121.6'

        validator = config.ComputationTypeValidator(params)
        self.assertFalse(validator.is_valid()[0])

    def test_region_geometry(self):
        '''
        Either a region or a set of sites has been specified
        '''
        # region
        params = dict()
        params['REGION_VERTEX'] = '37.9, -121.9, 37.9, -121.6, 37.5, -121.6'
        params['REGION_GRID_SPACING'] = '0.1'

        validator = config.ComputationTypeValidator(params)
        self.assertTrue(validator.is_valid()[0])

        # sites
        params = dict()
        params['SITES'] = '37.9, -121.9, 37.9, -121.6, 37.5, -121.6'

        validator = config.ComputationTypeValidator(params)
        self.assertTrue(validator.is_valid()[0])

    def test_must_specify_only_one_geometry(self):
        '''
        If both SITES and REGION_VERTEX + REGION_GRID_SPACING are specified,
        validation should fail. A job config can only have one or the
        other.
        '''
        params = dict()
        params['REGION_VERTEX'] = '37.9, -121.9, 37.9, -121.6, 37.5, -121.6'
        params['REGION_GRID_SPACING'] = '0.1'
        params['SITES'] = '37.9, -121.9, 37.9, -121.6, 37.5, -121.6'

        validator = config.ComputationTypeValidator(params)
        self.assertFalse(validator.is_valid()[0])

    def test_file_path_validation(self):
        # existing file
        params = dict()
        params['EXPOSURE'] = helpers.touch()

        validator = config.FilePathValidator(params)
        self.assertTrue(validator.is_valid()[0])

        # non-existing file
        params = dict()
        params['VULNERABILITY'] = '/a/b/c'
        params['SOURCE_MODEL_LOGIC_TREE_FILE'] = '/a/b/c'

        validator = config.FilePathValidator(params)
        valid, messages = validator.is_valid()

        self.assertFalse(valid)
        self.assertEquals(2, len(messages))

    def test_parameter_type_custom(self):
        # valid values
        for v in ('SA', 'PGA'):
            params = dict()
            params['INTENSITY_MEASURE_TYPE'] = v

            validator = config.BasicParameterValidator(params)
            self.assertTrue(validator.is_valid()[0], v)

        # some invalid values
        for v in ('sa', 'Pga', 'Foo'):
            params = dict()
            params['INTENSITY_MEASURE_TYPE'] = v

            validator = config.BasicParameterValidator(params)
            self.assertFalse(validator.is_valid()[0], v)

    def test_parameter_type_boolean(self):
        # valid values
        for v in ('0', '1', 'True', 'false', 'false '):
            params = dict()
            params['INCLUDE_SUBDUCTION_FAULT_SOURCE'] = v

            validator = config.BasicParameterValidator(params)
            self.assertTrue(validator.is_valid()[0], v)

        # some invalid values
        for v in ('x', '2', '-1', 'falsex'):
            params = dict()
            params['INCLUDE_SUBDUCTION_FAULT_SOURCE'] = v

            validator = config.BasicParameterValidator(params)
            self.assertFalse(validator.is_valid()[0], v)

    def test_parameter_type_polygon(self):
        # valid values
        for v in ('', '33.88, -118.30, 33.88, -118.06, 33.76, -118.06'):
            params = dict()
            params['REGION_VERTEX'] = v

            validator = config.BasicParameterValidator(params)
            self.assertTrue(validator.is_valid()[0], v)

        # some invalid values
        for v in ('a', '1.0', '1.0, -118.30, 33.88', '33, -118, 33, -118'):
            params = dict()
            params['REGION_VERTEX'] = v

            validator = config.BasicParameterValidator(params)
            self.assertFalse(validator.is_valid()[0], v)

    def test_parameter_type_multipoint(self):
        # valid values
        for v in ('', '33.88, -118.30, 33.88, -118.06'):
            params = dict()
            params['SITES'] = v

            validator = config.BasicParameterValidator(params)
            self.assertTrue(validator.is_valid()[0], v)

        # some invalid values
        for v in ('a', '1.0', '1.0, -118.30, 33.88'):
            params = dict()
            params['SITES'] = v

            validator = config.BasicParameterValidator(params)
            self.assertFalse(validator.is_valid()[0], v)

    def test_parameter_type_floatarray(self):
        # valid values
        for v in ('', '0', '0.1, 0.2'):
            params = dict()
            params['QUANTILE_LEVELS'] = v

            validator = config.BasicParameterValidator(params)
            self.assertTrue(validator.is_valid()[0], v)

        # some invalid values
        for v in ('0x', '1 x 2'):
            params = dict()
            params['QUANTILE_LEVELS'] = v

            validator = config.BasicParameterValidator(params)
            self.assertFalse(validator.is_valid()[0], v)

    def test_parameter_type_strarray(self):
        # valid values
        for v in ('MagPMF', 'MagPMF, MagDistPMF', 'MagPMF MagDistPMF'):
            params = dict()
            params['DISAGGREGATION_RESULTS'] = v

            validator = config.BasicParameterValidator(params)
            self.assertTrue(validator.is_valid()[0], v)

    def test_parameter_type_float(self):
        # valid values
        for v in ('0', '-1', '-7.0', '1.2E3', '2 ', ' 2'):
            params = dict()
            params['MINIMUM_MAGNITUDE'] = v

            validator = config.BasicParameterValidator(params)
            self.assertTrue(validator.is_valid()[0], v)

        # some invalid values
        for v in ('x', 'false', '0, 1'):
            params = dict()
            params['MINIMUM_MAGNITUDE'] = v

            validator = config.BasicParameterValidator(params)
            self.assertFalse(validator.is_valid()[0], v)

    def test_parameter_type_integer(self):
        # valid values
        for v in ('0', '1', '-42'):
            params = dict()
            params['NUMBER_OF_SEISMICITY_HISTORIES'] = v

            validator = config.BasicParameterValidator(params)
            self.assertTrue(validator.is_valid()[0], v)

        # some invalid values
        for v in ('x', '2.0', '1, 2 '):
            params = dict()
            params['NUMBER_OF_SEISMICITY_HISTORIES'] = v

            validator = config.BasicParameterValidator(params)
            self.assertFalse(validator.is_valid()[0], v)


class DisaggregationValidatorTestCase(unittest.TestCase):
    """Validator tests for Disaggregation Calculator params"""

    GOOD_PARAMS = {
        'LATITUDE_BIN_LIMITS': '-90, 0, 90',
        'LONGITUDE_BIN_LIMITS': '-180, 0, 180',
        'MAGNITUDE_BIN_LIMITS': '0, 1, 2, 4',
        'EPSILON_BIN_LIMITS': '-1, 3, 5, 7',
        'DISTANCE_BIN_LIMITS': '0, 10, 20',
    }
    BAD_PARAMS = {
        'LATITUDE_BIN_LIMITS': '-90.1, 0, 90',
        'LONGITUDE_BIN_LIMITS': '-180, 0, 180.1',
        'MAGNITUDE_BIN_LIMITS': '-0.5, 0, 1, 2',
        'EPSILON_BIN_LIMITS': '-1, 3, 5, 7',
        'DISTANCE_BIN_LIMITS': '-10, 0, 10',
    }

    def test_good_params(self):
        validator = config.DisaggregationValidator(self.GOOD_PARAMS)
        self.assertTrue(validator.is_valid()[0])

    def test_bad_params(self):
        validator = config.DisaggregationValidator(self.BAD_PARAMS)
        self.assertFalse(validator.is_valid()[0])


class DefaultValidatorsTestCase(unittest.TestCase):
    """Tests :function:`openquake.job.config.default_validators`
    for correct behavior with various types of job configurations.
    """

    def setUp(self):
        self.job = engine.prepare_job()

    def test_default_validators_disagg_job(self):
        """Test to ensure that a Disaggregation job always includes the
        :class:`openquake.job.config.DisaggregationValidator`.
        """
        da_job_path = helpers.demo_file('disaggregation/config.gem')
        da_job = helpers.job_from_file(da_job_path)

        validators = config.default_validators(da_job.sections, da_job.params)

        # test that the default validators include a DisaggregationValidator
        self.assertTrue(
            any(isinstance(v, DisaggregationValidator) for v in validators))

    def test_default_validators_classical_job(self):
        """Test to ensure that a classical always includes the
        :class:`openquake.job.config.ClassicalValidator`.
        """
        classical_risk_job_path = helpers.demo_file(
            'classical_psha_based_risk/config.gem')
        classical_risk_job = helpers.job_from_file(classical_risk_job_path)

        validators = config.default_validators(classical_risk_job.sections,
                                               classical_risk_job.params)

        self.assertTrue(
            any(isinstance(v, ClassicalValidator) for v in validators))

    def test_default_validators_scenario_job(self):
        """Test to ensure that a Scenario job always includes the
        :class:`openquake.job.config.ScenarioComputationValidator`."""
        scenario_job_path = helpers.demo_file('scenario_risk/config.gem')
        scenario_job = helpers.job_from_file(scenario_job_path)

        validators = config.default_validators(scenario_job.sections,
                                               scenario_job.params)

        self.assertTrue(any(
            isinstance(v, ScenarioComputationValidator) for v in validators))

    def test_default_validators_classical_risk(self):
        # For Classical Hazard+Risk calculations, ensure that a
        # `ClassicalRiskValidator` is included in the default validators.
        cfg_path = helpers.demo_file('classical_psha_based_risk/config.gem')

        job_profile, params, sections = engine.import_job_profile(
            cfg_path, self.job)

        validators = config.default_validators(sections, params)

        self.assertTrue(any(
            isinstance(v, ClassicalRiskValidator) for v in validators))

    def test_default_validators_classical_bcr_risk(self):
        # For Classical BCR Hazard+Risk calculations, ensure that a
        # `ClassicalRiskValidator` is included in the default validators.
        cfg_path = helpers.demo_file('benefit_cost_ratio/config.gem')

        job_profile, params, sections = engine.import_job_profile(
            cfg_path, self.job)

        validators = config.default_validators(sections, params)

        self.assertTrue(any(
            isinstance(v, ClassicalRiskValidator) for v in validators))

    def test_default_validators_event_based_risk(self):
        # For Event-Based Risk calculations, ensure that a
        # `EventBasedRiskValidator` is included in the default validators.
        cfg_path = helpers.demo_file(
            'probabilistic_event_based_risk/config.gem')

        job_profile, params, sections = engine.import_job_profile(
            cfg_path, self.job)

        validators = config.default_validators(sections, params)

        self.assertTrue(any(
            isinstance(v, EventBasedRiskValidator) for v in validators))

    # Currently skipped because we do not have a set of demo files for
    # Event-Based BCR Risk.
    @helpers.skipit
    def test_default_validators_event_based_bcr_risk(self):
        # For Event-Based BCR Risk calculations, ensure that a
        # `EventBasedRiskValidator` is included in the default validators.
        cfg_path = helpers.demo_file(
            'event_based_bcr_risk/config.gem')

        job_profile, params, sections = engine.import_job_profile(
            cfg_path, self.job)

        validators = config.default_validators(sections, params)

        self.assertTrue(any(
            isinstance(v, EventBasedRiskValidator) for v in validators))


class ValidatorsUtilsTestCase(unittest.TestCase):
    """Test for validator utility functions"""

    def test_to_float_array(self):
        expected = [-90.0, 0.0, 90.0]

        test_input = '-90, 0, 90'

        self.assertEqual(expected, to_float_array(test_input))

    def test_to_float_array_no_commas(self):
        expected = [-90.0, 0.0, 90.0]

        test_input = '-90 0 90'

        self.assertEqual(expected, to_float_array(test_input))

    def test_to_str_array(self):
        expected = ['MagPMF', 'MagDistPMF', 'MagDistEpsPMF']

        test_input = 'MagPMF, MagDistPMF, MagDistEpsPMF'

        self.assertEqual(expected, to_str_array(test_input))

    def test_to_str_array_no_commas(self):
        expected = ['MagPMF', 'MagDistPMF', 'MagDistEpsPMF']

        test_input = 'MagPMF MagDistPMF MagDistEpsPMF'

        self.assertEqual(expected, to_str_array(test_input))


class NumericSequenceValidationTestCase(unittest.TestCase):
    """Test cases for
    :function:`openquake.job.config.validate_numeric_sequence`
    """

    # This test sequence can be used to trigger errors with any of the
    # individual checks.
    TEST_VALUES = [-91.0, -91.0, -92.0]

    def test_no_checks(self):
        """If no checks are specified, no errors should be raised."""
        validate_numeric_sequence(self.TEST_VALUES)

    def test_min_length(self):
        self.assertRaises(ValueError, validate_numeric_sequence,
                          self.TEST_VALUES, min_length=4)

    def test_max_length(self):
        self.assertRaises(ValueError, validate_numeric_sequence,
                          self.TEST_VALUES, max_length=2)

    def test_min_val(self):
        self.assertRaises(ValueError, validate_numeric_sequence,
                          self.TEST_VALUES, min_val=-90.0)

    def test_max_val(self):
        self.assertRaises(ValueError, validate_numeric_sequence,
                          self.TEST_VALUES, max_val=-93.0)

    def test_check_sorted(self):
        self.assertRaises(ValueError, validate_numeric_sequence,
                          self.TEST_VALUES, check_sorted=True)

    def test_check_dupes(self):
        self.assertRaises(ValueError, validate_numeric_sequence,
                          self.TEST_VALUES, check_dupes=True)


class UHSValidatorTestCase(unittest.TestCase):
    """Tests for :class:`openquake.job.config.UHSValidator`"""

    # Parameters for success cases:
    GOOD_PARAMS_SHORT = {'UHS_PERIODS': '0.0'}
    GOOD_PARAMS_LONG = {'UHS_PERIODS': '0.0, 0.5, 1.0, 1.5'}

    # Parameters for fail cases:
    MIN_LENGTH = {'UHS_PERIODS': ''}
    MIN_VAL = {'UHS_PERIODS': '1.0, 0.0, 1.0'}
    CHECK_SORTED = {'UHS_PERIODS': '0.5, 0.0, 1.0, 1.5'}
    CHECK_DUPES = {'UHS_PERIODS': '0.0, 0.5, 0.5, 1.0'}

    def test_good_params_short(self):
        validator = UHSValidator(self.GOOD_PARAMS_SHORT)
        self.assertTrue(validator.is_valid()[0])

    def test_good_params_long(self):
        validator = UHSValidator(self.GOOD_PARAMS_LONG)
        self.assertTrue(validator.is_valid()[0])

    def test_invalid_min_length(self):
        validator = UHSValidator(self.MIN_LENGTH)
        self.assertFalse(validator.is_valid()[0])

    def test_invalid_min_val(self):
        validator = UHSValidator(self.MIN_VAL)
        self.assertFalse(validator.is_valid()[0])

    def test_invalid_check_sorted(self):
        validator = UHSValidator(self.CHECK_SORTED)
        self.assertFalse(validator.is_valid()[0])

    def test_invalid_check_dupes(self):
        validator = UHSValidator(self.CHECK_DUPES)
        self.assertFalse(validator.is_valid()[0])


class BCRValidatorTestCase(unittest.TestCase):
    """Tests for :class:`openquake.job.config.BCRValidator`"""

    GOOD_PARAMS = dict(INVESTIGATION_TIME=1.0, INTEREST_RATE=0.05,
                       ASSET_LIFE_EXPECTANCY=30)

    def assert_invalid(self, **params):
        for key in self.GOOD_PARAMS:
            params.setdefault(key, self.GOOD_PARAMS[key])
        validator = BCRValidator(params)
        self.assertEqual(validator.is_valid()[0], False)

    def test_investigation_time(self):
        self.assert_invalid(INVESTIGATION_TIME=0.0)
        self.assert_invalid(INVESTIGATION_TIME=50.0)
        self.assert_invalid(INVESTIGATION_TIME=1.1)

    def test_interest_rate(self):
        self.assert_invalid(INTEREST_RATE=0.0)
        self.assert_invalid(INTEREST_RATE=-1.2)

    def test_asset_life_expectancy(self):
        self.assert_invalid(ASSET_LIFE_EXPECTANCY=0.0)
        self.assert_invalid(ASSET_LIFE_EXPECTANCY=-1.0)

    def test_all_ok(self):
        validator = BCRValidator(self.GOOD_PARAMS)
        self.assertEqual(validator.is_valid(), (True, []))


class ScenarioValidatorTestCase(unittest.TestCase):

    def test_num_of_calculation_set_to_zero(self):
        sections = ['general', 'HAZARD', 'RISK']
        params = dict(NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS='0')
        validator = ScenarioComputationValidator(sections, params)

        self.assertFalse(validator.is_valid()[0])

    def test_num_of_calculation_less_than_zero(self):
        sections = ['general', 'HAZARD', 'RISK']
        params = dict(NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS='-1')
        validator = ScenarioComputationValidator(sections, params)

        self.assertFalse(validator.is_valid()[0])

    def test_num_of_calculation_greater_than_zeroo(self):
        sections = ['general', 'HAZARD', 'RISK']
        params = dict(NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS='1')
        validator = ScenarioComputationValidator(sections, params)

        self.assertTrue(validator.is_valid()[0])


class ClassicalValidatorTestCase(unittest.TestCase):
    """Tests for :class:`openquake.job.config.ClassicalValidator`"""

    SECTIONS = ['HAZARD', 'RISK']

    # This is only bad for hazard+risk jobs; this perfectly valid
    # for a hazard-only job:
    PARAMS_1 = dict(COMPUTE_MEAN_HAZARD_CURVE='false')

    PARAMS_2 = dict(COMPUTE_MEAN_HAZARD_CURVE='true')

    def test_invalid_params_haz_plus_risk(self):
        """Test validation on a hazard+risk config with known-bad parameters.
        """
        self.validator = ClassicalValidator(self.SECTIONS, self.PARAMS_1)
        self.assertFalse(self.validator.is_valid()[0])

    def test_valid_params_haz_plus_risk(self):
        """Test validation on a hazard+risk config with known-good parameters.
        """
        self.validator = ClassicalValidator(self.SECTIONS, self.PARAMS_2)
        self.assertTrue(self.validator.is_valid()[0])

    def test_valid_params_haz_only(self):
        """Both sets of parameters are valid for a hazard-only job config."""
        self.validator = ClassicalValidator(['HAZARD'], self.PARAMS_1)
        self.assertTrue(self.validator.is_valid()[0])

        self.validator = ClassicalValidator(['HAZARD'], self.PARAMS_2)
        self.assertTrue(self.validator.is_valid()[0])


class ClassicalRiskValidatorTestCase(unittest.TestCase):
    """Tests for the :class:`openquake.job.config.ClassicalRiskValidator`.
    """

    def test_lrem_steps_defined_valid_value(self):
        # The config should be considered valid if LREM_STEPS_PER_INTERVAL is
        # defined and has a valid value.
        # The value must be >= 1
        val = ClassicalRiskValidator(dict(LREM_STEPS_PER_INTERVAL=1))
        self.assertTrue(val.is_valid()[0])

        val = ClassicalRiskValidator(dict(LREM_STEPS_PER_INTERVAL=2))
        self.assertTrue(val.is_valid()[0])

    def test_lrem_steps_defined_invalid_value(self):
        # LREM_STEPS_PER_INTERVAL values < 1 are not allowed.
        val = ClassicalRiskValidator(dict(LREM_STEPS_PER_INTERVAL=0))
        self.assertFalse(val.is_valid()[0])

        val = ClassicalRiskValidator(dict(LREM_STEPS_PER_INTERVAL=-1))
        self.assertFalse(val.is_valid()[0])

    def test_lrem_steps_not_defined(self):
        val = ClassicalRiskValidator(dict())
        self.assertFalse(val.is_valid()[0])

    def test_lrem_steps_invalid_type(self):
        # An invalid type, in this case, is something that can't be cast to an
        # `int`.
        val = ClassicalRiskValidator(dict(LREM_STEPS_PER_INTERVAL='one'))
        self.assertFalse(val.is_valid()[0])


class EventBasedRiskValidatorTestCase(unittest.TestCase):
    """Tests for the :class:`openquake.job.config.EventBasedRiskValidator`.
    """

    def test_hgram_bins_defined_valid_value(self):
        # The config should be considerd valid if LOSS_HISTOGRAM_BINS is
        # define and has a valid value.
        # The value must be >= 1.
        val = EventBasedRiskValidator(dict(LOSS_HISTOGRAM_BINS=1))
        self.assertTrue(val.is_valid()[0])

        val = EventBasedRiskValidator(dict(LOSS_HISTOGRAM_BINS=2))
        self.assertTrue(val.is_valid()[0])

    def test_hgram_bins_defined_invalid_value(self):
        val = EventBasedRiskValidator(dict(LOSS_HISTOGRAM_BINS=0))
        self.assertFalse(val.is_valid()[0])

        val = EventBasedRiskValidator(dict(LOSS_HISTOGRAM_BINS=-1))
        self.assertFalse(val.is_valid()[0])

    def test_hgram_bins_not_defined(self):
        val = EventBasedRiskValidator(dict())
        self.assertFalse(val.is_valid()[0])

    def test_hgram_bins_invalid_type(self):
        # An invalid type, in this case, is something that can't be cast to an
        # `int`.
        val = EventBasedRiskValidator(dict(LOSS_HISTOGRAM_BINS='one'))
        self.assertFalse(val.is_valid()[0])
