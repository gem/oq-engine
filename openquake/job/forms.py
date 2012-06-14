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


from django.forms import ModelForm

from openquake.db import models

"""

[general]
region
region_grid_spacing
sites
src_model_lt_rnd_seed
gmpe_lt_rnd_seed

[erf]
bin_width
area_src_disc
mesh_spacing

[site]
site_model_file

[classical]
src_mdl_lt_file
gmpe_lt_file
investigation_time
imt/iml -> dict()
trunclevel
max_distance

"""
class BaseOQModelForm(ModelForm):

    def __init__(self, *args, **kwargs):
        if not 'data' in kwargs:
            # Because we're not using ModelForms in exactly the
            # originally-intended modus operandi, we need to pass all of the
            # field values from the instance model object as the `data` kwarg
            # (`data` needs to be a dict of fieldname-value pairs).
            # This serves to populate the form (as if a user had done so) and
            # immediately enables validation checking (through `is_valid()`,
            # for example).
            # This is, of course, only applicable is `instance` was supplied to
            # the form. For the purpose of just doing validation (which is why
            # these forms were created), we need to specify the `instance`.
            instance = kwargs.get('instance')
            if instance is not None:
                kwargs['data'] = instance.__dict__
        super(BaseOQModelForm, self).__init__(*args, **kwargs)


class ClassicalHazardJobForm(BaseOQModelForm):

    class Meta:
        model = models.HazardJobProfile
        fields = (
            'description',
            'calculation_mode',
            'region',
            'region_grid_spacing',
            'sites',
            'source_model_lt_random_seed',
            'gmpe_lt_random_seed',
            'number_of_logic_tree_samples',
            'rupture_mesh_spacing',
            'width_of_mfd_bin',
            'area_source_discretization',
            'reference_vs30_value',
            'reference_vs30_type',
            'reference_depth_to_2pt5km_per_sec',
            'reference_depth_to_1pt0km_per_sec',
            'investigation_time',
            '_imts_and_imls',
            'truncation_level',
            'maximum_distance',
            'mean_hazard_curves',
            'quantile_hazard_curves',
            'poes_hazard_maps',
        )

    def is_valid(self):
        """Overrides :method:`django.forms.ModelForm.is_valid` to perform
        custom validation checks (in addition to superclass validation).

        :returns:
            If valid return `True`, else `False`.
        """
        super_valid = super(ClassicalHazardJobForm, self).is_valid()
        valid = True
        return super_valid and valid
