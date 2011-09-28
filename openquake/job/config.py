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
This module contains logic related to the configuration and
its validation.
"""

import os
import re

from django.contrib.gis.db import models
from openquake.db.models import CharArrayField, FloatArrayField

from openquake.job.params import PARAMS, PATH_PARAMS


EXPOSURE = "EXPOSURE"
RISK_SECTION = "RISK"
INPUT_REGION = "REGION_VERTEX"
HAZARD_SECTION = "HAZARD"
GENERAL_SECTION = "general"
REGION_GRID_SPACING = "REGION_GRID_SPACING"
CALCULATION_MODE = "CALCULATION_MODE"
REGION_GRID_SPACING = "REGION_GRID_SPACING"
SITES = "SITES"
DETERMINISTIC_MODE = "Deterministic"
DISAGGREGATION_MODE = "Disaggregation"
CALCULATION_MODE = "CALCULATION_MODE"
BASE_PATH = "BASE_PATH"
COMPUTE_HAZARD_AT_ASSETS = "COMPUTE_HAZARD_AT_ASSETS_LOCATIONS"


ARRAY_RE = re.compile('[ ,]+')


def to_float_array(value):
    """Convert string value to floating point value array"""
    return [float(v) for v in ARRAY_RE.split(value) if len(v)]


def to_str_array(value):
    """Convert string value to string array"""
    return [v for v in ARRAY_RE.split(value) if len(v)]


class ValidationException(Exception):
    """Trivial wrapper for configuration validation errors"""

    def __init__(self, errors):
        super(ValidationException, self).__init__()

        self.errors = errors

    def __str__(self):
        msg = 'The job configuration contained some errors:\n\n'

        return msg + '\n'.join(self.errors)


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


class RiskMandatoryParametersValidator(object):
    """Validator that checks if the mandatory parameters
    for risk processing are specified."""

    def __init__(self, sections, params):
        self.sections = sections
        self.params = params

    def is_valid(self):
        """Return true if the mandatory risk parameters are specified,
        false otherwise. When invalid returns also the error messages.

        :returns: the status of this validator and the related error messages.
        :rtype: when valid, a (True, []) tuple is returned. When invalid, a
            (False, [ERROR_MESSAGE#1, ERROR_MESSAGE#2, ..., ERROR_MESSAGE#N])
            tuple is returned
        """

        mandatory_params = [EXPOSURE, INPUT_REGION, REGION_GRID_SPACING]

        if RISK_SECTION in self.sections:
            for mandatory_param in mandatory_params:
                if mandatory_param not in self.params.keys():
                    return (False, [
                            "With RISK processing, EXPOSURE, REGION_VERTEX " +
                            "and REGION_GRID_SPACING must be specified"])

        return (True, [])


class ComputationTypeValidator(object):
    """Validator that checks if the user has specified the correct
    algorithm to use for grabbing the sites to compute."""

    def __init__(self, params):
        self.params = params

    def is_valid(self):
        """Return true if the user has specified the region
        or the set of sites, false otherwise.
        """
        has_input_region = INPUT_REGION in self.params
        has_sites = SITES in self.params

        if has_input_region and has_sites:
            return (False, ["You can specify the input region or "
                    + "a set of sites, not both"])
        if not has_input_region and not has_sites:
            return (False, ["You must specify either input region or "
                    + "a set of sites"])
        if has_input_region and REGION_GRID_SPACING not in self.params:
            return (False, ["You must specify region grid spacing together "
                    + "with the input region"])

        return (True, [])


class DeterministicComputationValidator(object):
    """Validator that checks if the deterministic calculation
    mode specified in the configuration file is for an
    hazard + risk job. We don't currently support deterministic
    calculations for hazard jobs only."""

    def __init__(self, sections, params):
        self.params = params
        self.sections = sections

    def is_valid(self):
        """Return true if the deterministic calculation mode
        specified is for an hazard + risk job, false otherwise."""

        if RISK_SECTION not in self.sections \
                and self.params[CALCULATION_MODE] == DETERMINISTIC_MODE:

            return (False, ["With DETERMINISTIC calculations we"
                    + " only support hazard + risk jobs."])

        return (True, [])


class DisaggregationValidator(object):
    """Validator for parameters which are specific to the Disaggregation
    calculator."""

    LAT_BIN_LIMITS = 'LATITUDE_BIN_LIMITS'
    LON_BIN_LIMITS = 'LONGITUDE_BIN_LIMITS'
    MAG_BIN_LIMITS = 'MAGNITUDE_BIN_LIMITS'
    EPS_BIN_LIMITS = 'EPSILON_BIN_LIMITS'
    DIST_BIN_LIMITS = 'DISTANCE_BIN_LIMITS'

    def __init__(self, params):
        self.params = params

    @staticmethod
    def check_bin_limits(limits, bin_min=None, bin_max=None):
        """Check a sequence of bin limits to ensure the following:
            - There are at least 2 elements
            - Elements are in ascending order
            - There are no duplicates
            - Limits are within the correct range (if range min and/or max
              are specified

        If limits are not valid, a ValueError is raised.
        """

        try:
            # at least 2 elements:
            assert len(limits) >= 2, \
                "Limits should contain at least 2 elements"

            # ascening order:
            assert all(
                limits[i] < limits[i + 1] for i in xrange(len(limits) - 1)), \
                "Limits should be arranged in ascending order"

            # no duplicates:
            assert sorted(list(set(limits))) == list(limits), \
                "Limits should not contain duplicates"

            # values are in the correct range:
            assert bin_min is None or all(x >= bin_min for x in limits), \
                "Limits must be >= %s" % bin_min
            assert bin_max is None or all(x <= bin_max for x in limits), \
                "Limits must be <= %s" % bin_max

        except AssertionError, err:
            msg = "Invalid bin limits: %s. %s" % (limits, err)
            raise ValueError(msg)


    def is_valid(self):
        """Check if parameters are valid for a Disaggregation calculation.

        :returns: the status of this validator and the related error messages.
        :rtype: when valid, a (True, []) tuple is returned. When invalid, a
            (False, [ERROR_MESSAGE#1, ERROR_MESSAGE#2, ..., ERROR_MESSAGE#N])
            tuple is returned
        """

        valid = True

        checks = (
            dict(param=self.LAT_BIN_LIMITS, bin_min=-90.0, bin_max=90.0),
            dict(param=self.LON_BIN_LIMITS, bin_min=-180.0, bin_max=180.0),
            dict(param=self.MAG_BIN_LIMITS, bin_min=0.0),
            dict(param=self.EPS_BIN_LIMITS),
            dict(param=self.DIST_BIN_LIMITS, bin_min=0.0),
        )

        errors = []

        for check in checks:
            limits = to_float_array(self.params.get(check.get('param')))
            bin_min = check.get('bin_min', None)
            bin_max = check.get('bin_max', None)
            try:
                DisaggregationValidator.check_bin_limits(limits, bin_min,
                                                         bin_max)
            except ValueError, err:
                valid = False
                errors.append(err.message)

        return (valid, errors)


class FilePathValidator(object):
    """Validator that checks paths defined in configuration files are valid"""

    def __init__(self, params):
        self.params = params

    def is_valid(self):
        """Check all defined paths"""
        errors = []

        for name in PATH_PARAMS:
            if name not in self.params:
                continue

            if not os.path.exists(self.params[name]):
                errors.append("File '%s' specified by parameter %s not found" %
                              (self.params[name], name))

        return (len(errors) == 0, errors)


class BasicParameterValidator(object):
    """Validator that checks the type of configuration parameters"""

    def __init__(self, params):
        self.params = params

    def is_valid(self):
        """Check type for all parameters"""
        errors = []

        for name, value in self.params.items():
            param = PARAMS[name]
            value = value.strip()

            if param.type in (None, models.TextField) and param.to_db is None:
                continue

            invalid = False
            try:
                if param.type in (models.BooleanField,
                                    models.NullBooleanField):
                    description = 'true/false value'
                    invalid = value.lower() not in ('0', '1', 'true', 'false')
                elif param.type is models.PolygonField:
                    description = 'polygon value'
                    # check the array contains matching pairs and at least 3
                    # vertices (allow an empty array)
                    length = len(to_float_array(value))
                    invalid = length != 0 and (length % 2 == 1 or length < 6)
                elif param.type is models.MultiPointField:
                    description = 'multi-point value'
                    # just check the array contains matching pairs
                    length = len(to_float_array(value))
                    invalid = length % 2 == 1
                elif param.type is FloatArrayField:
                    description = 'floating point array value'
                    value = to_float_array(value)
                elif param.type is CharArrayField:
                    description = 'string array value'
                    value = to_str_array(value)

                    # if there is a 'to_db' transform,
                    # apply it to each element in the list
                    if param.to_db is not None:
                        value = [param.to_db(v) for v in value]

                elif param.type is models.FloatField:
                    description = 'floating point value'
                    value = float(value)
                elif param.type is models.IntegerField:
                    description = 'integer value'
                    value = int(value)
                elif param.to_db is not None:
                    description = 'value'
                    value = param.to_db(value)

                else:
                    raise RuntimeError(
                        "Invalid parameter type %s for parameter %s" % (
                            param.type.__name__, name))
            except (KeyError, ValueError):
                invalid = True

            if invalid:
                errors.append("Value '%s' is not a valid %s for parameter %s" %
                              (value, description, name))

        return (len(errors) == 0, errors)


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

    exposure = RiskMandatoryParametersValidator(sections, params)
    deterministic = DeterministicComputationValidator(sections, params)
    hazard_comp_type = ComputationTypeValidator(params)
    file_path = FilePathValidator(params)
    parameter = BasicParameterValidator(params)

    validators = ValidatorSet()
    validators.add(hazard_comp_type)
    validators.add(deterministic)
    validators.add(exposure)
    validators.add(parameter)
    validators.add(file_path)

    #if params.get(CALCULATION_MODE) == DISAGGREGATION_MODE:
    #    validators.add(DisaggregationValidator(params))

    return validators
