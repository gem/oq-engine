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

    def test_with_a_validator_the_result_is_the_validator(self):
        set = config.ValidatorSet()
        set.add(AlwaysTrueValidator())

        self.assertTrue(set.is_valid()[0])

    def test_a_set_is_valid_when_all_validators_are_valid(self):
        set = config.ValidatorSet()

        set.add(AlwaysTrueValidator())
        set.add(AlwaysTrueValidator())
        set.add(AlwaysTrueValidator())

        self.assertTrue(set.is_valid()[0])
        set.add(AlwaysFalseValidator(""))

        self.assertFalse(set.is_valid()[0])

    def test_no_error_messages_when_the_set_is_valid(self):
        set = config.ValidatorSet()

        set.add(AlwaysTrueValidator())
        set.add(AlwaysTrueValidator())
        set.add(AlwaysTrueValidator())

        self.assertEquals([], set.is_valid()[1])

    def test_the_set_keeps_track_of_the_failed_validators(self):
        set = config.ValidatorSet()

        set.add(AlwaysTrueValidator())
        set.add(AlwaysFalseValidator("MESSAGE#1"))
        set.add(AlwaysFalseValidator("MESSAGE#2"))
        set.add(AlwaysFalseValidator("MESSAGE#3"))

        self.assertFalse(set.is_valid()[0])

        error_messages = ["MESSAGE#1", "MESSAGE#2", "MESSAGE#3"]
        self.assertEquals(error_messages, set.is_valid()[1])


class ConfigurationConstraintsTestCase(unittest.TestCase):

    def test_with_risk_processing_the_exposure_must_be_specified(self):
        sections = [config.RISK_SECTION, "HAZARD", "general"]
        params = {}

        engine = helpers.create_job(params, sections=sections)
        self.assertFalse(engine.is_valid()[0])

        params = {config.EXPOSURE: "/a/path/to/exposure"}

        engine = helpers.create_job(params, sections=sections)
        self.assertTrue(engine.is_valid()[0])
