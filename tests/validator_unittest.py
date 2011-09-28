# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

"""
This module tests the logic related to the engine configuration
and its validation.
"""

from openquake.job import config
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


class ConfigurationConstraintsTestCase(unittest.TestCase):

    def test_risk_mandatory_parameters(self):
        sections = [config.RISK_SECTION,
                config.HAZARD_SECTION, config.GENERAL_SECTION]

        params = {}

        validator = config.default_validators(sections, params)
        self.assertFalse(validator.is_valid()[0])

        params = {config.EXPOSURE: "/a/path/to/exposure"}

        validator = config.default_validators(sections, params)
        self.assertFalse(validator.is_valid()[0])

        params = {config.EXPOSURE: "/a/path/to/exposure",
                config.REGION_GRID_SPACING: 0.5}

        validator = config.default_validators(sections, params)
        self.assertFalse(validator.is_valid()[0])

        params = {config.EXPOSURE: "/a/path/to/exposure",
                config.INPUT_REGION: "a, polygon",
                config.REGION_GRID_SPACING: 0.5}

        validator = config.default_validators(sections, params)
        self.assertTrue(validator.is_valid()[0])

    def test_deterministic_is_not_supported_alone(self):
        """When we specify a deterministic computation, we only
        support hazard + risk jobs."""

        sections = [config.RISK_SECTION,
                config.HAZARD_SECTION, config.GENERAL_SECTION]

        params = {config.CALCULATION_MODE: config.DETERMINISTIC_MODE}

        validator = config.DeterministicComputationValidator(sections, params)

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


class DisaggregationValidatorTestCase(unittest.TestCase):
    """Validator tests for Disaggregation Calculator params"""

    GOOD_PARAMS = {
        'LATITUDE_BIN_LIMITS': [-90, 0, 90],
        'LONGITUDE_BIN_LIMITS': [-180, 0, 180],
        'MAGNITUDE_BIN_LIMITS': [0, 1, 2, 4],
        'EPSILON_BIN_LIMITS': [-1, 3, 5, 7],
        'DISTANCE_BIN_LIMITS': [0, 10, 20]
    }
    BAD_PARAMS = {
        'LATITUDE_BIN_LIMITS': [-90.1, 0, 90],
        'LONGITUDE_BIN_LIMITS': [-180, 0, 180.1],
        'MAGNITUDE_BIN_LIMITS': [-0.5, 0, 1, 2],
        'EPSILON_BIN_LIMITS': [-1, 3, 5, 7],
        'DISTANCE_BIN_LIMITS': [-10, 0, 10]
    }


    @classmethod
    def setUpClass(cls):
        cls.dav_cls = config.DisaggregationValidator

    def test_check_good_bin_limits(self):
        """Check validation for known-good limits"""
        good_limits = (
            [5, 6, 7, 8],
            [5, 6],
            [-8.6, -7.3, -6.2, -6.1],
        )

        for limits in good_limits:
            # if no error is raised, the limits are good
            self.dav_cls.check_bin_limits(limits)

    def test_check_bad_bin_limits(self):
        """Check validation for known-bad limits"""
        bad_limits = (
            [5],
            [],
            [1.3],
        )

        for limits in bad_limits:
            self.assertRaises(ValueError, self.dav_cls.check_bin_limits, limits)

    def test_check_good_bin_limits_with_min_max(self):
        """Check validation for known-good limits, with min/max specified"""
        bin_min = -90.0
        bin_max = 90.0

        limits = [-90.0, 42.7, 90.0]

        self.dav_cls.check_bin_limits(limits, bin_min=bin_min, bin_max=bin_max)

    def test_check_bad_limits_with_min_max(self):
        """Check validation for known-bad limits, with min/max specified"""
        bin_min = -90.0
        bin_max = 90.0

        too_low = [-90.1, 42.7, 90.0]
        too_high = [-90.0, 42.7, 90.1]

        for limits in (too_low, too_high):
            self.assertRaises(ValueError, self.dav_cls.check_bin_limits, too_low,
                              bin_min=bin_min, bin_max=bin_max)

    def test_is_valid_good_params(self):
        """Test the entire validator with a set of known-good parameters"""
        validator = config.DisaggregationValidator(self.GOOD_PARAMS)

        self.assertEqual((True, []), validator.is_valid())

    def test_is_valid_bad_params(self):
        """Test the entire validator with a set of known-bad parameters"""
        validator = config.DisaggregationValidator(self.BAD_PARAMS)

        expected_results = (False,
            ['Invalid bin limits: [-90.1, 0, 90]. Limits must be >= -90.0',
             'Invalid bin limits: [-180, 0, 180.1]. Limits must be <= 180.0',
             'Invalid bin limits: [-0.5, 0, 1, 2]. Limits must be >= 0.0',
             'Invalid bin limits: [-10, 0, 10]. Limits must be >= 0.0']
        )

        actual_results =  validator.is_valid()

        self.assertEqual(expected_results, actual_results)


class DefaultValidatorsTestCase(unittest.TestCase):
    """Tests :function:`openquake.job.config.default_validators`
    for correct behavior with various types of job configurations.
    """

    def test_default_validators_disagg_job(self):
        da_job_path = helpers.smoketest_file('disaggregation/config.gem')
        da_job = helpers.job_from_file(da_job_path)

        print dir(da_job)
        print da_job.params
        self.assertTrue(False)
