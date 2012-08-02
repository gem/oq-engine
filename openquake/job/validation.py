# Copyright (c) 2010-2012, GEM Foundation.
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

"""This module contains functions and Django model forms for carrying out job
profile validation.
"""

import re

from django.forms import ModelForm
from nhlib import imt

from openquake.db import models

#: Minimum value for a signed 32-bit int
MIN_SINT_32 = -(2 ** 31)
#: Maximum value for a signed 32-bit int
MAX_SINT_32 = (2 ** 31) - 1


# Silencing 'Missing docstring' and 'Invalid name' for all of the validation
# functions (the latter because some of the function names are very long).
# pylint: disable=C0111,C0103

def description_is_valid(_mdl):
    return True, []


def calculation_mode_is_valid(mdl):
    if not mdl.calculation_mode == 'classical':
        return False, ['Calculation mode must be "classical"']
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
        if not all([-180 <= x <= 180 for x in lons]):
            valid = False
            errors.append('Longitude values must in the range [-180, 180]')
        if not all([-90 <= x <= 90 for x in lats]):
            valid = False
            errors.append('Latitude values must be in the range [-90, 90]')
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
    if not all([-180 <= x <= 180 for x in lons]):
        valid = False
        errors.append('Longitude values must in the range [-180, 180]')
    if not all([-90 <= x <= 90 for x in lats]):
        valid = False
        errors.append('Latitude values must be in the range [-90, 90]')

    return valid, errors


def random_seed_is_valid(mdl):
    if not MIN_SINT_32 <= mdl.random_seed <= MAX_SINT_32:
        return False, [('Random seed must be a value from %s to %s (inclusive)'
                       % (MIN_SINT_32, MAX_SINT_32))]
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


def intensity_measure_types_and_levels_is_valid(mdl):
    im = mdl.intensity_measure_types_and_levels

    valid = True
    errors = []

    # SA intensity measure configs need special handling
    imts = list(set(imt.__all__) - set(['SA']))

    for im_type, imls in im.iteritems():
        if im_type in imts:
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
        elif 'SA' in im_type:
            match = re.match(r'^SA\(([^)]+?)\)$', im_type)
            if match is None:
                # SA key is not formatted properly
                valid = False
                errors.append(
                    '%s: SA must be specified with a period value, in the form'
                    ' `SA(N)`, where N is a value >= 0' % im_type
                )
            else:
                # there's a match; make sure the period value is valid
                sa_period = match.groups()[0]
                try:
                    if float(sa_period) < 0:
                        valid = False
                        errors.append(
                            '%s: SA period values must be >= 0' % im_type
                        )
                except ValueError:
                    valid = False
                    errors.append(
                        '%s: SA period value should be a float >= 0' % im_type
                    )
        else:
            valid = False
            errors.append('%s: Invalid intensity measure type' % im_type)

    return valid, errors


def truncation_level_is_valid(mdl):
    if not mdl.truncation_level >= 0:
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


def poes_hazard_maps_is_valid(mdl):
    phm = mdl.poes_hazard_maps

    if phm is not None:
        if not all([0.0 <= x <= 1.0 for x in phm]):
            return False, ['PoEs for hazard maps must be in the range [0, 1]']
    return True, []


class BaseOQModelForm(ModelForm):
    """This class is based on :class:`django.forms.ModelForm`. Constructor
    arguments are the same.

    Since we're using forms (at the moment) purely for model validation, it's
    worth noting how we're using forms and what sort of inputs should be
    supplied.

    At the very least, an `instance` should be specified, which is expected to
    be a Django model object (perhaps one from :mod:`openquake.db.models`).

    `data` can be specified to populate the form and model. If no `data` is
    specified, the form will take the current data from the `instance`.

    You can also specify `files`. In the Django web form context, this
    represents a `dict` of name-file_object pairs. The file object type can be,
    for example, one of the types in :mod:`django.core.files.uploadedfile`.

    In this case, however, we expect `files` to be a dict of
    :class:`openquake.db.models.Input`, keyed by config file parameter for the
    input. For example::

    {'site_model_file': <Input: 174||site_model||0xdeadbeef||>}
    """

    def __init__(self, *args, **kwargs):
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
        super(BaseOQModelForm, self).__init__(*args, **kwargs)


class ClassicalHazardCalculationForm(BaseOQModelForm):

    # These fields require more complex validation.
    # The rules for these fields depend on other parameters
    # and files.
    special_fields = (
        'region',
        'region_grid_spacing',
        'sites',
        'reference_vs30_value',
        'reference_vs30_type',
        'reference_depth_to_2pt5km_per_sec',
        'reference_depth_to_1pt0km_per_sec',
    )

    class Meta:
        model = models.HazardCalculation
        fields = (
            'description',
            'calculation_mode',
            'region',
            'region_grid_spacing',
            'sites',
            'random_seed',
            'number_of_logic_tree_samples',
            'rupture_mesh_spacing',
            'width_of_mfd_bin',
            'area_source_discretization',
            'reference_vs30_value',
            'reference_vs30_type',
            'reference_depth_to_2pt5km_per_sec',
            'reference_depth_to_1pt0km_per_sec',
            'investigation_time',
            'intensity_measure_types_and_levels',
            'truncation_level',
            'maximum_distance',
            'mean_hazard_curves',
            'quantile_hazard_curves',
            'poes_hazard_maps',
        )

    def _add_error(self, field_name, error_msg):
        """Add an error to the `errors` dict.

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
        """Overrides :meth:`django.forms.ModelForm.is_valid` to perform
        custom validation checks (in addition to superclass validation).

        :returns:
            If valid return `True`, else `False`.
        """
        super_valid = super(ClassicalHazardCalculationForm, self).is_valid()
        all_valid = super_valid

        # HazardCalculation
        hjp = self.instance

        # Exclude special fields that require contextual validation.
        for field in sorted(set(self.fields) - set(self.special_fields)):
            valid, errs = eval('%s_is_valid' % field)(hjp)
            all_valid = all_valid and valid

            self._add_error(field, errs)

        # Now do checks which require more context.

        # Cannot specify region AND sites
        if (hjp.region is not None
            and hjp.sites is not None):
            all_valid = False
            err = 'Cannot specify `region` and `sites`. Choose one.'
            self._add_error('region', err)
        # At least one must be specified (region OR sites)
        elif not (hjp.region is not None or hjp.sites is not None):
            all_valid = False
            err = 'Must specify either `region` or `sites`.'
            self._add_error('region', err)
            self._add_error('sites', err)
        # Only region is specified
        elif hjp.region is not None:
            if hjp.region_grid_spacing is not None:
                valid, errs = region_grid_spacing_is_valid(hjp)
                all_valid = all_valid and valid

                self._add_error('region_grid_spacing', errs)
            else:
                all_valid = False
                err = '`region` requires `region_grid_spacing`'
                self._add_error('region', err)

            # validate the region
            valid, errs = region_is_valid(hjp)
            all_valid = all_valid and valid
            self._add_error('region', errs)
        # Only sites was specified
        else:
            valid, errs = sites_is_valid(hjp)
            all_valid = all_valid and valid
            self._add_error('sites', errs)

        if 'site_model_file' not in self.files:
            # make sure the reference parameters are defined and valid

            for field in (
                'reference_vs30_value',
                'reference_vs30_type',
                'reference_depth_to_2pt5km_per_sec',
                'reference_depth_to_1pt0km_per_sec',
            ):
                valid, errs = eval('%s_is_valid' % field)(hjp)
                all_valid = all_valid and valid
                self._add_error(field, errs)

        return all_valid
