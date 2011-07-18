# -*- coding: utf-8 -*-

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
This module tests contains logic related to the configuration and
its validation.
"""

EXPOSURE = "EXPOSURE"
RISK_SECTION = "RISK"
INPUT_REGION = "REGION_VERTEX"
CALCULATION_MODE = "CALCULATION_MODE"
REGION_GRID_SPACING = "REGION_GRID_SPACING"


class ValidatorSet(object):
    """A set of validators."""

    def __init__(self):
        self.validators = []

    def is_valid(self):
        """Return true if all validators defined in this set
        are valid, false otherwise.

        :returns: the status of this set and the related error messages.
        :rtype: when valid, a (True, []) tuple is returned. When invalid, a
            (False, [ERROR_MESSAGE#1, ERROR_MESSAGE#2, ..., ERROR_MESSAGE#N])
            tuple is returned
        """

        valid = True
        error_messages = []

        for validator in self.validators:
            if not validator.is_valid()[0]:
                error_messages.extend(validator.is_valid()[1])
                valid = False

        return (valid, error_messages)

    def add(self, validator):
        """Add a validator to this set.

        :param validator: the validator to add to this set.
        :type validator: :py:class:`object` defining an is_valid()
            method conformed to the validator interface
        """

        self.validators.append(validator)


class ExposureValidator(object):
    """Validator that checks if the exposure file
    is specified when computing risk jobs."""

    def __init__(self, sections, params):
        self.sections = sections
        self.params = params

    def is_valid(self):
        """Return true if the EXPOSURE parameter is specified,
        false otherwise. When invalid returns also the error messages.

        :returns: the status of this validator and the related error messages.
        :rtype: when valid, a (True, []) tuple is returned. When invalid, a
            (False, [ERROR_MESSAGE#1, ERROR_MESSAGE#2, ..., ERROR_MESSAGE#N])
            tuple is returned
        """

        if RISK_SECTION in self.sections:
            if not EXPOSURE in self.params:
                return (False, [
                    "With RISK processing, the EXPOSURE must be specified"])

        return (True, [])


def default_validators(sections, params):
    """Create the set of default validators for a job.

    :param sections: sections defined for the job.
    :type sections: :py:class:`list`
    :param params: parameters defined for the job.
    :type params: :py:class:`dict` where each key is the parameter
        name, and each value is the parameter value
        specified in the configuration file
    :returns: the default validators for a job.
    :rtype: an instance of
        :py:class:`openquake.config.ValidatorSet`
    """

    exposure = ExposureValidator(sections, params)

    validators = ValidatorSet()
    validators.add(exposure)

    return validators
