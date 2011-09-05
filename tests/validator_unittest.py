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


class ConfigurationConstraintsTestCase(unittest.TestCase, helpers.TestMixin):

    def test_risk_mandatory_parameters(self):
        sections = [config.RISK_SECTION,
                config.HAZARD_SECTION, config.GENERAL_SECTION]

        dummy_exposure = self.touch()

        params = {}

        validator = config.default_validators(sections, params)
        self.assertFalse(validator.is_valid()[0])

        params = {config.EXPOSURE: dummy_exposure}

        validator = config.default_validators(sections, params)
        self.assertFalse(validator.is_valid()[0])

        params = {config.EXPOSURE: dummy_exposure,
                  config.REGION_GRID_SPACING: '0.5'}

        validator = config.default_validators(sections, params)
        self.assertFalse(validator.is_valid()[0])

        params = {config.EXPOSURE: dummy_exposure,
                  config.INPUT_REGION: "1.0, 2.0, 3.0, 4.0, 5.0, 6.0",
                  config.REGION_GRID_SPACING: '0.5'}

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

    def test_file_path_validation(self):
        # existing file
        params = dict()
        params['EXPOSURE'] = self.touch()

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
