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

        engine = helpers.create_job(params, sections=sections)
        self.assertFalse(engine.is_valid()[0])

        params = {config.EXPOSURE: "/a/path/to/exposure"}

        engine = helpers.create_job(params, sections=sections)
        self.assertFalse(engine.is_valid()[0])

        params = {config.EXPOSURE: "/a/path/to/exposure",
                config.REGION_GRID_SPACING: 0.5}

        engine = helpers.create_job(params, sections=sections)
        self.assertFalse(engine.is_valid()[0])

        params = {config.EXPOSURE: "/a/path/to/exposure",
                config.INPUT_REGION: "a, polygon",
                config.REGION_GRID_SPACING: 0.5}

        engine = helpers.create_job(params, sections=sections)
        self.assertTrue(engine.is_valid()[0])

    def test_hazard_computation_type(self):
        """Region (REGION_VERTEX) and specific sites (SITES)
        are not supported at the same time."""

        params = {config.SITES: "some, sites"}
        validator = config.ComputationTypeValidator(params)

        engine = helpers.create_job(params, validator=validator)
        self.assertTrue(engine.is_valid()[0])

        params = {config.INPUT_REGION: "a, polygon"}
        validator = config.ComputationTypeValidator(params)

        engine = helpers.create_job(params, validator=validator)
        self.assertTrue(engine.is_valid()[0])

        params = {config.SITES: "some, sites",
                config.INPUT_REGION: "a, polygon"}

        validator = config.ComputationTypeValidator(params)

        engine = helpers.create_job(params, validator=validator)
        self.assertFalse(engine.is_valid()[0])

    def test_deterministic_is_not_supported_alone(self):
        """When we specify a deterministic computation, we only
        support hazard + risk jobs."""

        sections = [config.RISK_SECTION,
                config.HAZARD_SECTION, config.GENERAL_SECTION]

        params = {config.CALCULATION_MODE: config.DETERMINISTIC_MODE}

        validator = config.DeterministicComputationValidator(sections, params)
        engine = helpers.create_job(
            None, sections=sections, validator=validator)

        self.assertTrue(engine.is_valid()[0])

        sections.remove(config.RISK_SECTION)

        self.assertFalse(engine.is_valid()[0])
