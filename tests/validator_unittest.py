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

import unittest


class AlwaysTrueValidator(config.Validator):

    def __init__(self):
        super(AlwaysTrueValidator, self).__init__()

    def is_valid(self):
        return True

    def error_message(self):
        return "Always true error message"


class AlwaysFalseValidator(config.Validator):

    def __init__(self, error):
        self.error = error

    def is_valid(self):
        return False

    def error_message(self):
        return self.error


class ValidatorSetTestCase(unittest.TestCase):

    def test_an_empty_set_is_valid(self):
        self.assertTrue(config.ValidatorSet().is_valid())

    def test_an_empty_set_has_no_error_messages(self):
        self.assertEquals([], config.ValidatorSet().error_message())

    def test_with_a_validator_the_result_is_the_validator(self):
        set = config.ValidatorSet()
        set.append(AlwaysTrueValidator())

        self.assertTrue(set.is_valid())

    def test_a_set_is_valid_when_all_validators_are_valid(self):
        set = config.ValidatorSet()

        set.append(AlwaysTrueValidator())
        set.append(AlwaysTrueValidator())
        set.append(AlwaysTrueValidator())

        self.assertTrue(set.is_valid())
        set.append(AlwaysFalseValidator(""))

        self.assertFalse(set.is_valid())

    def test_no_error_messages_when_the_set_is_valid(self):
        set = config.ValidatorSet()

        set.append(AlwaysTrueValidator())
        set.append(AlwaysTrueValidator())
        set.append(AlwaysTrueValidator())

        self.assertEquals([], set.error_message())

    def test_the_set_keeps_track_of_the_failed_validators(self):
        set = config.ValidatorSet()

        set.append(AlwaysTrueValidator())
        set.append(AlwaysFalseValidator("MESSAGE#1"))
        set.append(AlwaysFalseValidator("MESSAGE#2"))
        set.append(AlwaysFalseValidator("MESSAGE#3"))

        self.assertFalse(set.is_valid())

        error_messages = ["MESSAGE#1", "MESSAGE#2", "MESSAGE#3"]
        self.assertEquals(error_messages, set.error_message())
