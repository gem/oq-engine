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


EXPOSURE = "EXPOSURE"
RISK_SECTION = "RISK"
INPUT_REGION = "INPUT_REGION"


class Validator(object):
    """This class represents a constraint on the
    configuration file."""

    def is_valid(self):
        """Return true if this constraint is true,
        false otherwise."""
        raise NotImplementedError()

    def error_message(self):
        """Return the error message of this constraint,
        if it is not valid."""
        raise NotImplementedError()


class ValidatorSet(Validator):
    """A set of validators."""

    def __init__(self):
        super(ValidatorSet, self).__init__()
        self.validators = []

    def is_valid(self):
        """Return true if all validators are true,
        false otherwise."""
        result = True

        for validator in self.validators:
            if not validator.is_valid():
                result = False

        return result

    def error_message(self):
        """When this set is not valid, return the
        error messages of the failed validators."""
        error_messages = []
        
        for validator in self.validators:
            if not validator.is_valid():
                error_messages.append(validator.error_message())
        
        return error_messages

    def append(self, validator):
        """Add a validator to this set."""
        self.validators.append(validator)

        
class ExposureValidator(Validator):
    """Validator that checks if the exposure file
    is specified when computing risk jobs."""

    def __init__(self, sections, params):
        super(Validator, self).__init__()

        self.sections = sections
        self.params = params

    def is_valid(self):
        """Return true if the EXPOSURE parameter is
        specified, false otherwise."""
        if RISK_SECTION in self.sections:
            return EXPOSURE in self.params

        return True

    def error_message(self):
        return "With RISK processing, the EXPOSURE must be specified"


def default_validators(sections, params):
    """Create the set of defaults validator for a job."""
    exposure = ExposureValidator(sections, params)

    validators = ValidatorSet()
    validators.append(exposure)
    
    return validators
