# Copyright (c) 2010-2013, GEM Foundation.
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
This module contains functions and Django model forms for carrying out job
profile validation.
"""
import re
import warnings

from django.forms import ModelForm

import openquake.hazardlib
from openquake.engine.db import models
from openquake.engine.utils import get_calculator_class


AVAILABLE_GSIMS = openquake.hazardlib.gsim.get_available_gsims().keys()


# used in bin/openquake
def validate(job, job_type, params, exports):
    """
    Validate a job of type 'hazard' or 'risk' by instantiating its
    form class with the given files and exports.

    :param job:
        an instance of :class:`openquake.engine.db.models.OqJob`
    :param str job_type:
        "hazard" or "risk"
    :param dict params:
        The raw dictionary of parameters parsed from the config file.
    :param exports:
        a list of export types
    :returns:
        an error message if the form is invalid, None otherwise.
    """
    calculation = getattr(job, '%s_calculation' % job_type)
    calc_mode = calculation.calculation_mode
    calculator_cls = get_calculator_class(job_type, calc_mode)
    formname = calculator_cls.__name__.replace('Calculator', 'Form')
    try:
        form_class = globals()[formname]
    except KeyError:
        return 'Could not find form class for "%s"' % calc_mode

    files = set(params['inputs'])
    form = form_class(instance=calculation, files=files, exports=exports)

    # Check for superfluous params and raise warnings:
    params_copy = params.copy()
    # There are a couple of parameters we can ignore.
    # `calculation_mode` is supplied in every config file, but is validated in
    # a special way; therefore, we don't declare it on the forms.
    # The `base_path` is extracted from the directory containing the config
    # file; it's not a real param.
    # `hazard_output_id` and `hazard_calculation_id` are supplied via command
    # line args.
    for p in ('calculation_mode', 'base_path', 'hazard_output_id',
              'hazard_calculation_id'):
        if p in params_copy:
            params_copy.pop(p)

    for param in set(params_copy.keys()).difference(set(form._meta.fields)):
        msg = "Unknown parameter '%s' for calculation mode '%s'. Ignoring."
        msg %= (param, calc_mode)
        warnings.warn(msg, RuntimeWarning)

    if not form.is_valid():
        return 'Job configuration is not valid. Errors: %s' % dict(form.errors)


class BaseOQModelForm(ModelForm):
    """
    This class is based on :class:`django.forms.ModelForm`. Constructor
    arguments are the same.

    Since we're using forms (at the moment) purely for model validation, it's
    worth noting how we're using forms and what sort of inputs should be
    supplied.

    At the very least, an `instance` should be specified, which is expected to
    be a Django model object (perhaps one from
    :mod:`openquake.engine.db.models`).

    `data` can be specified to populate the form and model. If no `data` is
    specified, the form will take the current data from the `instance`.

    You can also specify `files`. In the Django web form context, this
    represents a `dict` of name-file_object pairs. The file object type can be,
    for example, one of the types in :mod:`django.core.files.uploadedfile`.

    In this case, however, we expect `files` to be a dict of
    filenames, keyed by config file parameter
    for the input. For example::

    {'site_model': 'site_model.xml'}
    """

    # These fields require more complex validation.
    # The rules for these fields depend on other parameters
    # and files.
    # At the moment, these are common to all hazard calculation modes.
    special_fields = (
        'export_dir',
        'inputs',
    )

    def __init__(self, *args, **kwargs):
        self.exports = kwargs.get('exports')
        if not 'data' in kwargs:
            # Because we're not using ModelForms in exactly the
            # originally-intended modus operandi, we need to pass all of the
            # field values from the instance model object as the `data` kwarg
            # (`data` needs to be a dict of fieldname-value pairs).
            # This serves to populate the form (as if a user had done so) and
            # immediately enables validation checking (through `is_valid()`,
            # for example).
            # This is, of course, only applicable if `instance` was supplied to
            # the form. For the purpose of just doing validation (which is why
            # these forms were created), we need to specify the `instance`.
            instance = kwargs.get('instance')
            if instance is not None:
                kwargs['data'] = instance.__dict__
        if "exports" in kwargs:
            del kwargs['exports']
        super(BaseOQModelForm, self).__init__(*args, **kwargs)

    def has_vulnerability(self):
        """
        :returns: True if a vulnerability file has been given
        """
        return [itype
                for itype, _desc in models.INPUT_TYPE_CHOICES
                if itype.endswith('vulnerability') and itype in self.files]

    def _add_error(self, field_name, error_msg):
        """
        Add an error to the `errors` dict.

        If errors for the given ``field_name`` already exist append the error
        to that list. Otherwise, a new entry will have to be created for the
        ``field_name`` to hold the ``error_msg``.

        ``error_msg`` can also be a list or tuple of error messages.
        """
        is_list = isinstance(error_msg, (list, tuple))
        if self.errors.get(field_name) is not None:
            if is_list:
                self.errors[field_name].extend(error_msg)
            else:
                self.errors[field_name].append(error_msg)
        else:
            # no errors for this field have been recorded yet
            if is_list:
                if len(error_msg) > 0:
                    self.errors[field_name] = error_msg
            else:
                self.errors[field_name] = [error_msg]

    def is_valid(self):
        """
        Overrides :meth:`django.forms.ModelForm.is_valid` to perform
        custom validation checks (in addition to superclass validation).

        :returns:
            If valid return `True`, else `False`.
        """

        # FIXME(lp). Django allows custom validation by overriding the
        # `clean` method and `clean_<field>` methods. We should go for
        # the standard approach

        super_valid = super(BaseOQModelForm, self).is_valid()
        all_valid = super_valid

        # Calculation
        calc = self.instance

        # First, check the calculation mode:
        valid, errs = calculation_mode_is_valid(calc, self.calc_mode)
        all_valid &= valid
        self._add_error('calculation_mode', errs)

        # Exclude special fields that require contextual validation.
        fields = self.__class__.Meta.fields

        for field in sorted(set(fields) - set(self.special_fields)):
            valid, errs = globals()['%s_is_valid' % field](calc)
            all_valid &= valid

            self._add_error(field, errs)

        if self.exports:
            # The user has requested that exports be performed after the
            # calculation i.e. an 'export_dir' parameter must be present.
            if not calc.export_dir:
                all_valid = False
                err = ('--exports specified on the command line but the '
                       '"export_dir" parameter is missing in the .ini file')
                self._add_error('export_dir', err)

        return all_valid


class BaseHazardModelForm(BaseOQModelForm):
    """
    Base ModelForm used to validate HazardCalculation objects
    """

    special_fields = (
        'region',
        'region_grid_spacing',
        'sites',
        'reference_vs30_value',
        'reference_vs30_type',
        'reference_depth_to_2pt5km_per_sec',
        'reference_depth_to_1pt0km_per_sec',
        'export_dir',
        'inputs',
    )

    def is_valid(self):
        super_valid = super(BaseHazardModelForm, self).is_valid()
        all_valid = super_valid

        # HazardCalculation
        hc = self.instance
        # Now do checks which require more context.

        # Cannot specify region AND sites
        if (hc.region is not None and hc.sites is not None):
            all_valid = False
            err = 'Cannot specify `region` and `sites`. Choose one.'
            self._add_error('region', err)
        # At least one must be specified (region OR sites)
        elif not (hc.region is not None or
                  hc.sites is not None or 'exposure' in self.files):
            all_valid = False
            err = 'Must specify either `region`, `sites` or `exposure_file`.'
            self._add_error('region', err)
            self._add_error('sites', err)
        # Only region is specified
        elif hc.region is not None:
            if hc.region_grid_spacing is not None:
                valid, errs = region_grid_spacing_is_valid(hc)
                all_valid &= valid

                self._add_error('region_grid_spacing', errs)
            else:
                all_valid = False
                err = '`region` requires `region_grid_spacing`'
                self._add_error('region', err)

            # validate the region
            valid, errs = region_is_valid(hc)
            all_valid &= valid
            self._add_error('region', errs)
        # Only sites was specified
        elif hc.sites:
            valid, errs = sites_is_valid(hc)
            all_valid &= valid
            self._add_error('sites', errs)

        if 'site_model' not in self.files:
            # make sure the reference parameters are defined and valid

            for field in (
                'reference_vs30_value',
                'reference_vs30_type',
                'reference_depth_to_2pt5km_per_sec',
                'reference_depth_to_1pt0km_per_sec',
            ):
                valid, errs = globals().get('%s_is_valid' % field)(hc)
                all_valid &= valid
                self._add_error(field, errs)

        return all_valid


class ClassicalHazardForm(BaseHazardModelForm):

    calc_mode = 'classical'

    class Meta:
        model = models.HazardCalculation
        fields = (
            'description',
            'region',
            'region_grid_spacing',
            'sites',
            'random_seed',
            'intensity_measure_types_and_levels',
            'number_of_logic_tree_samples',
            'rupture_mesh_spacing',
            'width_of_mfd_bin',
            'area_source_discretization',
            'reference_vs30_value',
            'reference_vs30_type',
            'reference_depth_to_2pt5km_per_sec',
            'reference_depth_to_1pt0km_per_sec',
            'investigation_time',
            'truncation_level',
            'maximum_distance',
            'mean_hazard_curves',
            'quantile_hazard_curves',
            'poes',
            'export_dir',
            'inputs',
            'hazard_maps',
            'uniform_hazard_spectra',
            'export_multi_curves',
        )

    def is_valid(self):
        super_valid = super(ClassicalHazardForm, self).is_valid()
        all_valid = super_valid

        if self.has_vulnerability():
            if self.instance.intensity_measure_types_and_levels is not None:
                msg = (
                    '`intensity_measure_types_and_levels` is ignored when a '
                    '`vulnerability_file` is specified'
                )
                warnings.warn(msg)

        return all_valid


class EventBasedHazardForm(BaseHazardModelForm):

    calc_mode = 'event_based'

    class Meta:
        model = models.HazardCalculation
        fields = (
            'description',
            'region',
            'region_grid_spacing',
            'sites',
            'random_seed',
            'number_of_logic_tree_samples',
            'rupture_mesh_spacing',
            'intensity_measure_types',
            'intensity_measure_types_and_levels',
            'width_of_mfd_bin',
            'area_source_discretization',
            'reference_vs30_value',
            'reference_vs30_type',
            'reference_depth_to_2pt5km_per_sec',
            'reference_depth_to_1pt0km_per_sec',
            'investigation_time',
            'truncation_level',
            'maximum_distance',
            'ses_per_logic_tree_path',
            'ground_motion_correlation_model',
            'ground_motion_correlation_params',
            'ground_motion_fields',
            'hazard_curves_from_gmfs',
            'mean_hazard_curves',
            'quantile_hazard_curves',
            'poes',
            'export_dir',
            'inputs',
            'hazard_maps',
            'export_multi_curves',
        )

    def is_valid(self):
        super_valid = super(EventBasedHazardForm, self).is_valid()
        all_valid = super_valid

        hc = self.instance

        # contextual validation
        # If a vulnerability model is defined, show warnings if the user also
        # specified `intensity_measure_types_and_levels` or
        # `intensity_measure_types`:
        if self.has_vulnerability():
            if (self.instance.intensity_measure_types_and_levels
                    is not None):
                msg = (
                    '`intensity_measure_types_and_levels` is ignored when '
                    'a `vulnerability_file` is specified'
                )
                warnings.warn(msg)
            if (self.instance.intensity_measure_types is not None):
                msg = (
                    '`intensity_measure_types` is ignored when '
                    'a `vulnerability_file` is specified'
                )
                warnings.warn(msg)
        else:
            if hc.hazard_curves_from_gmfs:
                # The vulnerability model can define the IMTs/IMLs;
                # if there isn't one, we need to check that
                # `intensity_measure_types_and_levels` and
                # `intensity_measure_types` are both defined and valid.
                if hc.intensity_measure_types_and_levels is None:
                    # Not defined
                    msg = '`%s` requires `%s`'
                    msg %= ('hazard_curves_from_gmfs',
                            'intensity_measure_types_and_levels')

                    self._add_error('intensity_measure_types_and_levels', msg)
                    all_valid = False
                else:
                    # IMTs/IMLs is defined
                    # The IMT keys in `intensity_measure_types_and_levels` need
                    # to be a subset of `intensity_measure_types`.
                    imts = set(hc.intensity_measure_types_and_levels.keys())

                    all_imts = set(hc.intensity_measure_types)

                    if not imts.issubset(all_imts):
                        msg = 'Unknown IMT(s) [%s] in `%s`'
                        msg %= (', '.join(sorted(imts - all_imts)),
                                'intensity_measure_types')

                        self._add_error('intensity_measure_types_and_levels',
                                        msg)
                        all_valid = False

                if not hc.ground_motion_fields:
                    msg = ('`hazard_curves_from_gmfs` requires '
                           '`ground_motion_fields` to be `true`')
                    self._add_error('hazard_curves_from_gmfs', msg)
                    all_valid = False

        return all_valid


class DisaggHazardForm(BaseHazardModelForm):

    calc_mode = 'disaggregation'

    class Meta:
        model = models.HazardCalculation
        fields = (
            'description',
            'region',
            'region_grid_spacing',
            'sites',
            'random_seed',
            'intensity_measure_types_and_levels',
            'number_of_logic_tree_samples',
            'rupture_mesh_spacing',
            'width_of_mfd_bin',
            'area_source_discretization',
            'reference_vs30_value',
            'reference_vs30_type',
            'reference_depth_to_2pt5km_per_sec',
            'reference_depth_to_1pt0km_per_sec',
            'investigation_time',
            'truncation_level',
            'maximum_distance',
            'mag_bin_width',
            'distance_bin_width',
            'coordinate_bin_width',
            'num_epsilon_bins',
            'poes_disagg',
            'export_dir',
            'inputs',
        )

    def is_valid(self):
        super_valid = super(DisaggHazardForm, self).is_valid()
        all_valid = super_valid

        if self.has_vulnerability():
            if self.instance.intensity_measure_types_and_levels is not None:
                msg = (
                    '`intensity_measure_types_and_levels` is ignored when a '
                    '`vulnerability_file` is specified'
                )
                warnings.warn(msg)

        return all_valid


class ScenarioHazardForm(BaseHazardModelForm):

    calc_mode = 'scenario'

    class Meta:
        model = models.HazardCalculation
        fields = (
            'description',
            'region',
            'region_grid_spacing',
            'sites',
            'random_seed',
            'intensity_measure_types',
            'rupture_mesh_spacing',
            'reference_vs30_value',
            'reference_vs30_type',
            'reference_depth_to_2pt5km_per_sec',
            'reference_depth_to_1pt0km_per_sec',
            'truncation_level',
            'maximum_distance',
            'number_of_ground_motion_fields',
            'gsim',
            'ground_motion_correlation_model',
            'ground_motion_correlation_params',
            'export_dir',
            'inputs',
        )

    def is_valid(self):
        super_valid = super(ScenarioHazardForm, self).is_valid()
        all_valid = super_valid

        if self.has_vulnerability():
            if self.instance.intensity_measure_types is not None:
                msg = (
                    '`intensity_measure_types` is ignored when a '
                    '`vulnerability_file` is specified'
                )
                warnings.warn(msg)

        return all_valid


class ClassicalRiskForm(BaseOQModelForm):
    calc_mode = 'classical'

    class Meta:
        model = models.RiskCalculation
        fields = (
            'description',
            'region_constraint',
            'maximum_distance',
            'lrem_steps_per_interval',
            'conditional_loss_poes',
            'quantile_loss_curves',
            'insured_losses',
            'poes_disagg',
            'export_dir',
            'inputs',
        )


class ClassicalBCRRiskForm(BaseOQModelForm):
    calc_mode = 'classical_bcr'

    class Meta:
        model = models.RiskCalculation
        fields = (
            'description',
            'region_constraint',
            'maximum_distance',
            'lrem_steps_per_interval',
            'interest_rate',
            'asset_life_expectancy',
            'export_dir',
            'inputs',
        )


class EventBasedBCRRiskForm(BaseOQModelForm):
    calc_mode = 'event_based_bcr'

    class Meta:
        model = models.RiskCalculation
        fields = (
            'description',
            'region_constraint',
            'maximum_distance',
            'loss_curve_resolution',
            'master_seed',
            'asset_correlation',
            'interest_rate',
            'asset_life_expectancy',
            'export_dir',
            'inputs',
        )


class EventBasedRiskForm(BaseOQModelForm):
    calc_mode = 'event_based'

    class Meta:
        model = models.RiskCalculation
        fields = (
            'description',
            'region_constraint',
            'maximum_distance',
            'risk_investigation_time',
            'loss_curve_resolution',
            'conditional_loss_poes',
            'insured_losses',
            'master_seed',
            'asset_correlation',
            'quantile_loss_curves',
            'sites_disagg',
            'mag_bin_width',
            'distance_bin_width',
            'coordinate_bin_width',
            'export_dir',
            'inputs',
        )

    def is_valid(self):
        super_valid = super(EventBasedRiskForm, self).is_valid()
        rc = self.instance          # RiskCalculation instance

        if rc.sites_disagg and not (rc.mag_bin_width
                                    and rc.coordinate_bin_width
                                    and rc.distance_bin_width):
            self._add_error('sites_disagg', "disaggregation requires "
                            "mag_bin_width, coordinate_bin_width, "
                            "distance_bin_width")
            return False

        return super_valid


class ScenarioDamageRiskForm(BaseOQModelForm):
    calc_mode = 'scenario_damage'

    class Meta:
        model = models.RiskCalculation
        fields = (
            'description',
            'region_constraint',
            'maximum_distance',
            'export_dir',
            'inputs',
        )


class ScenarioRiskForm(BaseOQModelForm):
    calc_mode = 'scenario'

    class Meta:
        model = models.RiskCalculation
        fields = (
            'description',
            'region_constraint',
            'maximum_distance',
            'master_seed',
            'asset_correlation',
            'insured_losses',
            'time_event',
            'export_dir',
            'inputs',
        )

    def is_valid(self):
        super_valid = super(ScenarioRiskForm, self).is_valid()
        rc = self.instance          # RiskCalculation instance

        if 'occupants_vulnerability' in self.files:
            if not rc.time_event:
                self._add_error('time_event', "Scenario Risk requires "
                                "time_event when an occupants vulnerability "
                                "model is given")

                return False
        return super_valid

# Silencing 'Missing docstring' and 'Invalid name' for all of the validation
# functions (the latter because some of the function names are very long).
# pylint: disable=C0111,C0103


def description_is_valid(_mdl):
    return True, []


def calculation_mode_is_valid(mdl, expected_calc_mode):
    if not mdl.calculation_mode == expected_calc_mode:
        return False, ['Calculation mode must be "%s"' % expected_calc_mode]
    return True, []


def region_is_valid(mdl):
    valid = True
    errors = []

    if not mdl.region.valid:
        valid = False
        errors.append('Invalid region geomerty: %s' % mdl.region.valid_reason)

    if len(mdl.region.coords) > 1:
        valid = False
        errors.append('Region geometry can only be a single linear ring')

    # There should only be a single linear ring.
    # Even if there are multiple, we can still check for and report errors.
    for ring in mdl.region.coords:
        lons = [lon for lon, _ in ring]
        lats = [lat for _, lat in ring]

        errors.extend(_lons_lats_are_valid(lons, lats))

    if errors:
        valid = False

    return valid, errors


def region_grid_spacing_is_valid(mdl):
    if not mdl.region_grid_spacing > 0:
        return False, ['Region grid spacing must be > 0']
    return True, []


def sites_is_valid(mdl):
    valid = True
    errors = []

    lons = [pt.x for pt in mdl.sites]
    lats = [pt.y for pt in mdl.sites]

    errors.extend(_lons_lats_are_valid(lons, lats))
    if errors:
        valid = False

    return valid, errors


def sites_disagg_is_valid(mdl):
    # sites_disagg is optional in risk event based
    if mdl.calculation_mode == 'event_based' and mdl.sites_disagg is None:
        return True, []
    valid = True
    errors = []

    lons = [pt.x for pt in mdl.sites_disagg]
    lats = [pt.y for pt in mdl.sites_disagg]

    errors.extend(_lons_lats_are_valid(lons, lats))
    if errors:
        valid = False

    return valid, errors


def _lons_lats_are_valid(lons, lats):
    """
    Helper function for validating lons/lats.

    :returns:
        A list of error messages, or an empty list.
    """
    errors = []

    if not all([-180 <= x <= 180 for x in lons]):
        errors.append('Longitude values must in the range [-180, 180]')
    if not all([-90 <= x <= 90 for x in lats]):
        errors.append('Latitude values must be in the range [-90, 90]')

    return errors


def random_seed_is_valid(mdl):
    if not models.MIN_SINT_32 <= mdl.random_seed <= models.MAX_SINT_32:
        return False, [('Random seed must be a value from %s to %s (inclusive)'
                       % (models.MIN_SINT_32, models.MAX_SINT_32))]
    return True, []


def number_of_logic_tree_samples_is_valid(mdl):
    if not mdl.number_of_logic_tree_samples >= 0:
        return False, ['Number of logic tree samples must be >= 0']
    return True, []


def rupture_mesh_spacing_is_valid(mdl):
    if not mdl.rupture_mesh_spacing > 0:
        return False, ['Rupture mesh spacing must be > 0']
    return True, []


def width_of_mfd_bin_is_valid(mdl):
    if not mdl.width_of_mfd_bin > 0:
        return False, ['Width of MFD bin must be > 0']
    return True, []


def area_source_discretization_is_valid(mdl):
    if not mdl.area_source_discretization > 0:
        return False, ['Area source discretization must be > 0']
    return True, []


def reference_vs30_value_is_valid(mdl):
    if not mdl.reference_vs30_value > 0:
        return False, ['Reference VS30 value must be > 0']
    return True, []


def reference_vs30_type_is_valid(mdl):
    if not mdl.reference_vs30_type in ('measured', 'inferred'):
        return False, ['Reference VS30 type must be either '
                       '"measured" or "inferred"']
    return True, []


def reference_depth_to_2pt5km_per_sec_is_valid(mdl):
    if not mdl.reference_depth_to_2pt5km_per_sec > 0:
        return False, ['Reference depth to 2.5 km/sec must be > 0']
    return True, []


def reference_depth_to_1pt0km_per_sec_is_valid(mdl):
    if not mdl.reference_depth_to_1pt0km_per_sec > 0:
        return False, ['Reference depth to 1.0 km/sec must be > 0']
    return True, []


def investigation_time_is_valid(mdl):
    if not mdl.investigation_time > 0:
        return False, ['Investigation time must be > 0']
    return True, []


def _validate_imt(imt):
    """
    Validate an intensity measure type string.

    :returns:
        A pair of values. The first is a `bool` indicating whether or not the
        IMT is valid. The second value is a `list` of error messages. (If the
        IMT is valid, the list should be empty.)
    """
    valid = True
    errors = []

    # SA intensity measure configs need special handling
    valid_imts = list(set(openquake.hazardlib.imt.__all__) - set(['SA']))

    if 'SA' in imt:
        match = re.match(r'^SA\(([^)]+?)\)$', imt)
        if match is None:
            # SA key is not formatted properly
            valid = False
            errors.append(
                '%s: SA must be specified with a period value, in the form'
                ' `SA(N)`, where N is a value >= 0' % imt
            )
        else:
            # there's a match; make sure the period value is valid
            sa_period = match.groups()[0]
            try:
                if float(sa_period) < 0:
                    valid = False
                    errors.append(
                        '%s: SA period values must be >= 0' % imt
                    )
            except ValueError:
                valid = False
                errors.append(
                    '%s: SA period value should be a float >= 0' % imt
                )
    elif not imt in valid_imts:
        valid = False
        errors.append('%s: Invalid intensity measure type' % imt)

    return valid, errors


def intensity_measure_types_and_levels_is_valid(mdl):
    im = mdl.intensity_measure_types_and_levels

    valid = True
    errors = []

    if im is None:
        return valid, errors

    for im_type, imls in im.iteritems():
        # validate IMT:
        valid_imt, imt_errors = _validate_imt(im_type)
        valid &= valid_imt
        errors.extend(imt_errors)

        # validate IML values:
        if not isinstance(imls, list):
            valid = False
            errors.append(
                '%s: IMLs must be specified as a list of floats' % im_type
            )
        else:
            if len(imls) == 0:
                valid = False
                errors.append(
                    '%s: IML lists must have at least 1 value' % im_type
                )
            elif not all([x > 0 for x in imls]):
                valid = False
                errors.append('%s: IMLs must be > 0' % im_type)

    return valid, errors


def intensity_measure_types_is_valid(mdl):
    imts = mdl.intensity_measure_types

    if imts is None:
        return True, []

    if isinstance(imts, str):
        imts = [imts]

    valid = True
    errors = []

    for imt in imts:
        valid_imt, imt_errors = _validate_imt(imt)
        valid &= valid_imt
        errors.extend(imt_errors)

    return valid, errors


# FIXME
# This function and similar ones where different
# checking rules are applied according to
# different calculation modes need to be refactored,
# splitting up the checking rules for each calculation
# mode.
def truncation_level_is_valid(mdl):
    if mdl.calculation_mode == 'disaggregation':
        if mdl.truncation_level is not None:
            if mdl.truncation_level <= 0:
                return False, [
                    'Truncation level must be > 0 for disaggregation'
                    ' calculations']
        else:
            return False, [
                'Truncation level must be set for disaggregation'
                ' calculations and it must be > 0']
    else:
        if mdl.truncation_level is not None:
            if mdl.truncation_level < 0:
                return False, ['Truncation level must be >= 0']

    return True, []


def maximum_distance_is_valid(mdl):
    if not mdl.maximum_distance > 0:
        return False, ['Maximum distance must be > 0']
    return True, []


def mean_hazard_curves_is_valid(_mdl):
    # The validation form should normalize the type to a boolean.
    # We don't need to check anything here.
    return True, []


def quantile_hazard_curves_is_valid(mdl):
    qhc = mdl.quantile_hazard_curves

    if qhc is not None:
        if not all([0.0 <= x <= 1.0 for x in qhc]):
            return False, ['Quantile hazard curve values must in the range '
                           '[0, 1]']
    return True, []


def quantile_loss_curves_is_valid(mdl):
    qlc = mdl.quantile_loss_curves

    if qlc is not None:
        if not all([0.0 <= x <= 1.0 for x in qlc]):
            return False, ['Quantile loss curve values must in the range '
                           '[0, 1]']
    return True, []


def poes_is_valid(mdl):
    phm = mdl.poes
    error_msg = '`poes` values must be in the range [0, 1]'
    return _validate_poe_list(phm, error_msg)


def _validate_poe_list(poes, error_msg):
    if poes is not None:
        if not all([0.0 <= x <= 1.0 for x in poes]):
            return False, [error_msg]
    return True, []


def ses_per_logic_tree_path_is_valid(mdl):
    sps = mdl.ses_per_logic_tree_path

    if not sps > 0:
        return False, ['`Stochastic Event Sets Per Sample` '
                       '(ses_per_logic_tree_path) must be > 0']
    return True, []


def ground_motion_correlation_model_is_valid(_mdl):
    # No additional validation is required;
    # the model form and fields will take care of validation based on the
    # valid choices defined for this field.
    return True, []


def ground_motion_correlation_params_is_valid(_mdl):
    # No additional validation is required;
    # it is not appropriate to do detailed checks on the correlation model
    # parameters at this point because the parameters are specific to a given
    # correlation model.
    # Field normalization should make sure that the input is properly formed.
    return True, []


def ground_motion_fields_is_valid(_mdl):
    # This parameter is a simple True or False;
    # field normalization should cover all of validation necessary.
    return True, []


def hazard_curves_from_gmfs_is_valid(_mdl):
    # This parameter is a simple True or False;
    # field normalization should cover all of validation necessary.
    return True, []


def conditional_loss_poes_is_valid(mdl):
    value = mdl.conditional_loss_poes

    if value is not None:
        if not all([0.0 <= x <= 1.0 for x in value]):
            return (
                False,
                ['PoEs for conditional loss poes must be in the range [0, 1]'])
    return True, []


def lrem_steps_per_interval_is_valid(mdl):
    value = mdl.lrem_steps_per_interval
    msg = 'loss conditional exceedence matrix steps per interval must be > 0'

    if value is None or not value > 0:
        return False, [msg]
    return True, []


def region_constraint_is_valid(_mdl):
    # At this stage, we just use the region_is_valid implementation to
    # check for a consistent geometry. Further validation occurs after
    # we have loaded the exposure.
    _mdl.region = _mdl.region_constraint
    return region_is_valid(_mdl)


def mag_bin_width_is_valid(mdl):
    # mag_bin_width is optional in risk event based
    if mdl.calculation_mode == 'event_based' and mdl.sites_disagg is None:
        return True, []

    if not mdl.mag_bin_width > 0.0:
        return False, ['Magnitude bin width must be > 0.0']
    return True, []


def distance_bin_width_is_valid(mdl):
    # distance_bin_width is optional in risk event based
    if mdl.calculation_mode == 'event_based' and mdl.sites_disagg is None:
        return True, []

    if not mdl.distance_bin_width > 0.0:
        return False, ['Distance bin width must be > 0.0']
    return True, []


def coordinate_bin_width_is_valid(mdl):
    # coordinate_bin_width is optional in risk event based
    if mdl.calculation_mode == 'event_based' and mdl.sites_disagg is None:
        return True, []

    if not mdl.coordinate_bin_width > 0.0:
        return False, ['Coordinate bin width must be > 0.0']
    return True, []


def num_epsilon_bins_is_valid(mdl):
    if not mdl.num_epsilon_bins > 0:
        return False, ['Number of epsilon bins must be > 0']
    return True, []


def asset_life_expectancy_is_valid(mdl):
    if mdl.is_bcr:
        if mdl.asset_life_expectancy is None or mdl.asset_life_expectancy <= 0:
            return False, ['Asset Life Expectancy must be > 0']
    return True, []


def taxonomies_from_model_is_valid(_mdl):
    return True, []


def interest_rate_is_valid(mdl):
    if mdl.is_bcr:
        if mdl.interest_rate is None:
            return False, "Interest Rate is mandatory for BCR analysis"
    return True, []


def insured_losses_is_valid(_mdl):
    # The validation form should normalize the type to a boolean.
    # We don't need to check anything here.
    return True, []


def loss_curve_resolution_is_valid(mdl):
    if mdl.calculation_mode == 'event_based':
        if (mdl.loss_curve_resolution is not None and
                mdl.loss_curve_resolution < 1):
            return False, ['Loss Curve Resolution must be >= 1']
    return True, []


def asset_correlation_is_valid(_mdl):
    # The validation form should check if it is in the list
    # We don't need to check anything here.
    if _mdl.asset_correlation is not None:
        if not (_mdl.asset_correlation >= 0 and _mdl.asset_correlation <= 1):
            return False, ['Asset Correlation must be >= 0 and <= 1']
    return True, []


def master_seed_is_valid(_mdl):
    return True, []


def export_multi_curves_is_valid(_mdl):
    return True, []


def gsim_is_valid(mdl):
    if mdl.gsim in AVAILABLE_GSIMS:
        return True, []
    return False, ['The gsim %r is not in in openquake.hazardlib.gsim' %
                   mdl.gsim]


def number_of_ground_motion_fields_is_valid(mdl):
    gmfno = mdl.number_of_ground_motion_fields
    if gmfno > 0:
        return True, []
    return False, ['The number_of_ground_motion_fields must be a positive '
                   'integer, got %r' % gmfno]


def poes_disagg_is_valid(mdl):
    # poes_disagg optional in classical risk
    if mdl.calculation_mode == 'classical':
        return True, []
    poesd = mdl.poes_disagg
    if len(poesd) == 0:
        return False, ['`poes_disagg` must contain at least 1 value']
    error_msg = 'PoEs for disaggregation must be in the range [0, 1]'
    return _validate_poe_list(poesd, error_msg)


def hazard_maps_is_valid(mdl):
    if mdl.hazard_maps and mdl.poes is None:
        return False, ['`poes` are required to compute hazard maps']
    return True, []


def uniform_hazard_spectra_is_valid(mdl):
    if mdl.uniform_hazard_spectra and mdl.poes is None:
        return False, ['`poes` are required to compute UHS']
    return True, []


def time_event_is_valid(_mdl):
    # Any string is allowed, or `None`.
    return True, []


def risk_investigation_time_is_valid(_mdl):
    if _mdl.calculation_mode != 'event_based':
        return False, ['`risk_investigation_time` is only used '
                       'in event based calculations']
    if _mdl.risk_investigation_time is not None:
        if _mdl.risk_investigation_time <= 0:
            return False, ['Risk investigation time must be > 0']
    return True, []
