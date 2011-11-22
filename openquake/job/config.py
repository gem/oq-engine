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

from django.contrib.gis.db import models
from openquake.db.models import CharArrayField, FloatArrayField

from openquake.job.params import PARAMS, PATH_PARAMS, ARRAY_RE


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
UHS_MODE = "UHS"
BASE_PATH = "BASE_PATH"
COMPUTE_HAZARD_AT_ASSETS = "COMPUTE_HAZARD_AT_ASSETS_LOCATIONS"

DEPTHTO1PT0KMPERSEC = "DEPTHTO1PT0KMPERSEC"
VS30_TYPE = "VS30_TYPE"
HAZARD_TASKS = "HAZARD_TASKS"

LAT_BIN_LIMITS = 'LATITUDE_BIN_LIMITS'
LON_BIN_LIMITS = 'LONGITUDE_BIN_LIMITS'
MAG_BIN_LIMITS = 'MAGNITUDE_BIN_LIMITS'
EPS_BIN_LIMITS = 'EPSILON_BIN_LIMITS'
DIST_BIN_LIMITS = 'DISTANCE_BIN_LIMITS'

UHS_PERIODS = 'UHS_PERIODS'


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

    def __iter__(self):
        for v in self.validators:
            yield v

    def is_valid(self):
        """Return `True` if all validators defined in this set
        are valid, `False` otherwise.

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


class MandatoryParamsValidator(object):
    """Validator that checks if the mandatory parameters
    for risk processing are specified."""

    def __init__(self, sections, params):
        self.sections = sections
        self.params = params

    def is_valid(self):
        """
        Return `True` if the mandatory parameters are specified, `False`
        otherwise.

        :returns: the status of this validator and the related error messages.
        :rtype: when valid, a (True, []) tuple is returned. When invalid, a
            (False, [ERROR_MESSAGE#1, ERROR_MESSAGE#2, ..., ERROR_MESSAGE#N])
            tuple is returned
        """
        if self.SECTION_OF_INTEREST in self.sections:
            for mandatory_param in self.MANDATORY_PARAMS:
                if mandatory_param not in self.params.keys():
                    msg = ("Parameter '%s' not supplied in section '%s'" %
                           (mandatory_param, self.SECTION_OF_INTEREST))
                    return (False, [msg])

        return (True, [])


class RiskMandatoryParamsValidator(MandatoryParamsValidator):
    """
    Validator that checks whether the mandatory parameters
    for risk processing are specified.
    """
    SECTION_OF_INTEREST = RISK_SECTION
    MANDATORY_PARAMS = [EXPOSURE, INPUT_REGION, REGION_GRID_SPACING]

    def __init__(self, sections, params):
        super(
            RiskMandatoryParamsValidator, self).__init__(sections, params)


class HazardMandatoryParamsValidator(MandatoryParamsValidator):
    """
    Validator that checks whether the mandatory parameters
    for hazard processing are specified.
    """
    SECTION_OF_INTEREST = HAZARD_SECTION
    MANDATORY_PARAMS = [DEPTHTO1PT0KMPERSEC, VS30_TYPE]

    def __init__(self, sections, params):
        super(
            HazardMandatoryParamsValidator, self).__init__(sections, params)

    def is_valid(self):
        """
        Return `True` if the mandatory parameters are specified, `False`
        otherwise.

        This will additionally check that all mandatory hazard parameters have
        the "java_name" property set.

        :returns: the status of this validator and the related error messages.
        :rtype: when valid, a (True, []) tuple is returned. When invalid, a
            (False, [ERROR_MESSAGE#1, ERROR_MESSAGE#2, ..., ERROR_MESSAGE#N])
            tuple is returned
        """
        result, msgs = super(HazardMandatoryParamsValidator, self).is_valid()
        # The check failed in the base class already, just return.
        if not result:
            return (result, msgs)
        # The check in the base class succeeded. Now -- in addition -- make
        # sure that we have a 'java_name' set for each mandatory hazard
        # parameter.
        params_lacking_java_name = [p for p in self.MANDATORY_PARAMS
                                    if PARAMS[p].java_name is None]
        if params_lacking_java_name:
            msg = ("The following mandatory hazard parameter(s) lack "
                   "a 'java_name' property: %s"
                   % ", ".join(params_lacking_java_name))
            return(False, [msg])
        else:
            return (result, msgs)


class ComputationTypeValidator(object):
    """Validator that checks if the user has specified the correct
    algorithm to use for grabbing the sites to compute."""

    def __init__(self, params):
        self.params = params

    def is_valid(self):
        """Return `True` if the user has specified the region
        or the set of sites, `False` otherwise.
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
        """Return `True` if the deterministic calculation mode
        specified is for an hazard + risk job, `False` otherwise."""

        if RISK_SECTION not in self.sections \
                and self.params[CALCULATION_MODE] == DETERMINISTIC_MODE:

            return (False, ["With DETERMINISTIC calculations we"
                    + " only support hazard + risk jobs."])

        return (True, [])


# pylint: disable=R0913
def validate_numeric_sequence(values, min_length=None, max_length=None,
                              min_val=None, max_val=None,
                              check_sorted=False, check_dupes=False):
    """General function for checking the validity of a numeric sequence.

    If any check fails, a ValueError is raised.

    :param values:
        A sequence (such as `list` or `tuple`) of numeric values.
    :param int min_length:
        Minimum length for the input sequence.
    :param int max_length:
        Maximum length for the input sequence.
    :param float min_val:
        Minimum value for each element in the input sequence.
    :param float max_val:
        Maximum value for each element in the input sequence.
    :param bool check_sorted:
        If True, check if the sequence is sorted in ascending order. If the
        sequence is not sorted, the check will fail.
    :param bool check_dupes:
        If True, check if the sequence contains duplicates. If the sequence
        contains duplicates, the check will fail.
    """
    try:
        assert min_length is None or len(values) >= min_length, (
            "Sequence must contain at least %s elements." % min_length)
        assert max_length is None or len(values) <= max_length, (
            "Sequence must contain at most %s elements." % max_length)
        assert min_val is None or all(x >= min_val for x in values), (
            "All values in sequence must be >= %s." % min_val)
        assert max_val is None or all(x <= max_val for x in values), (
            "All values in sequence must be <= %s." % max_val)
        assert ((not check_sorted)
                or
                (all(values[i] <= values[i + 1]
                       for i in xrange(len(values) - 1)))), (
            "Sequence is not sorted.")
        assert ((not check_dupes)
                or
                (len(set(values)) == len(values))), (
            "Sequence contains duplicates.")

    except AssertionError, err:
        msg = "Invalid numeric sequence: %s. Error: %s" % (values, err.message)
        raise ValueError(msg)


class DisaggregationValidator(object):
    """Validator for parameters which are specific to the Disaggregation
    calculator."""

    def __init__(self, params):
        self.params = params

    def is_valid(self):
        """Check if parameters are valid for a Disaggregation calculation.

        :returns: the status of this validator and the related error messages.
        :rtype: when valid, a (True, []) tuple is returned. When invalid, a
            (False, [ERROR_MESSAGE#1, ERROR_MESSAGE#2, ..., ERROR_MESSAGE#N])
            tuple is returned
        """

        valid = True

        checks = (
            dict(param=LAT_BIN_LIMITS, bin_min=-90.0, bin_max=90.0),
            dict(param=LON_BIN_LIMITS, bin_min=-180.0, bin_max=180.0),
            dict(param=MAG_BIN_LIMITS, bin_min=0.0),
            dict(param=EPS_BIN_LIMITS),
            dict(param=DIST_BIN_LIMITS, bin_min=0.0),
        )

        errors = []

        for check in checks:
            limits = to_float_array(self.params.get(check.get('param')))
            bin_min = check.get('bin_min', None)
            bin_max = check.get('bin_max', None)
            try:
                validate_numeric_sequence(limits, min_length=2,
                                          min_val=bin_min, max_val=bin_max,
                                          check_sorted=True, check_dupes=True)
            except ValueError, err:
                valid = False
                errors.append(err.message)

        return (valid, errors)


class UHSValidator(object):
    """Validator for parameters which are specific to the Uniform Hazard
    Spectra calculator."""

    def __init__(self, params):
        self.params = params

    def is_valid(self):
        """Check if UHS_PERIODS contains valid data for a UHS calculation.

        Currently, this is the only UHS-specific parameter we need to check.
        :returns: the status of this validator and the related error messages.
        :rtype: when valid, a (True, []) tuple is returned. When invalid, a
            (False, [ERROR_MESSAGE#1, ERROR_MESSAGE#2, ..., ERROR_MESSAGE#N])
            tuple is returned
        """
        valid = True
        errors = []

        uhs_periods = self.params.get(UHS_PERIODS)
        if uhs_periods is None:
            valid = False
            errors.append(
                "Parameter `%s` must be defined for UHS calculations."
                % UHS_PERIODS)
        else:
            vals = to_float_array(uhs_periods)
            try:
                validate_numeric_sequence(vals, min_length=1, min_val=0.0,
                                          check_sorted=True, check_dupes=True)
            except ValueError, err:
                valid = False
                errors.append(err.message)

        return (valid, errors)


class BCRValidator(object):
    """
    Validator for both classical- and probabilistic-based BCR calculators
    """

    def __init__(self, params):
        self.params = params

    def is_valid(self):
        """
        Checks the following conditions:

        * INVESTIGATION_TIME is set to 1.0
        * INTEREST_RATE is positive
        * ASSET_LIFE_EXPECTANCY is positive
        """
        errors = []
        if self.params.get('INVESTIGATION_TIME') != 1.0:
            errors.append("Parameter 'INVESTIGATION_TIME' must be set to 1.0 "
                          "for BCR calculations.")
        if self.params.get('INTEREST_RATE') <= 0:
            errors.append("Parameter 'INTEREST_RATE' must be positive")
        if self.params.get('ASSET_LIFE_EXPECTANCY') <= 0:
            errors.append("Parameter 'ASSET_LIFE_EXPECTANCY' must be positive")
        return (not bool(errors), errors)


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


def validate_single_param(param, name, value, errors):
    """Validates a single parameter.

    :param param: the parameter to be validated
    :type param: a `namedtuple` with parameter data. See
        py:class:`openquake.job.params.Param`
    :param str name: parameter name
    :param str value: parameter value
    :param list errors: string list with parameter validation errors.
        Another error will be appended to it if the parameter at hand
        fails to validate.
    """
    invalid = False
    description = ""
    value = value.strip()
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

            # before converting to an array of strings,
            # transform the value to appropriate db input
            if param.to_db is not None:
                value = param.to_db(value)
            value = to_str_array(value)
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


class BasicParameterValidator(object):
    """Validator that checks the type of configuration parameters"""

    def __init__(self, params):
        self.params = params

    def is_valid(self):  # pylint: disable=R0912
        """Check type for all parameters"""
        errors = []

        for name, value in self.params.items():
            param = PARAMS.get(name)
            if param is None:
                # Ignore unknown parameters.
                continue
            else:
                if (param.type in (None, models.TextField)
                    and param.to_db is None):
                    continue
                validate_single_param(param, name, value, errors)

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

    hazard = HazardMandatoryParamsValidator(sections, params)
    exposure = RiskMandatoryParamsValidator(sections, params)
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
    validators.add(hazard)

    if params.get(CALCULATION_MODE) == DISAGGREGATION_MODE:
        validators.add(DisaggregationValidator(params))

    return validators
