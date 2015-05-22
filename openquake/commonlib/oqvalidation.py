#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import collections
from openquake.commonlib import valid, parallel
from openquake.commonlib.riskmodels import (
    get_fragility_functions, get_imtls_from_vulnerabilities,
    vulnerability_files, fragility_files)

GROUND_MOTION_CORRELATION_MODELS = ['JB2009']

HAZARD_CALCULATORS = [
    'classical', 'disaggregation', 'event_based', 'scenario',
    'classical_tiling']

RISK_CALCULATORS = [
    'classical_risk', 'event_based_risk', 'scenario_risk',
    'classical_bcr', 'event_based_bcr', 'scenario_damage',
    'classical_damage', 'event_loss']

CALCULATORS = HAZARD_CALCULATORS + RISK_CALCULATORS


class OqParam(valid.ParamSet):
    area_source_discretization = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    asset_correlation = valid.Param(valid.NoneOr(valid.FloatRange(0, 1)), 0)
    asset_life_expectancy = valid.Param(valid.positivefloat)
    base_path = valid.Param(valid.utf8)
    calculation_mode = valid.Param(valid.Choice(*CALCULATORS), '')
    concurrent_tasks = valid.Param(
        valid.positiveint, parallel.executor.num_tasks_hint)
    coordinate_bin_width = valid.Param(valid.positivefloat)
    conditional_loss_poes = valid.Param(valid.probabilities, [])
    continuous_fragility_discretization = valid.Param(valid.positiveint, 20)
    description = valid.Param(valid.utf8_not_empty)
    distance_bin_width = valid.Param(valid.positivefloat)
    mag_bin_width = valid.Param(valid.positivefloat)
    epsilon_sampling = valid.Param(valid.positiveint, 1000)
    export_dir = valid.Param(valid.utf8, None)
    export_multi_curves = valid.Param(valid.boolean, False)
    exports = valid.Param(valid.export_formats, ('csv',))
    ground_motion_correlation_model = valid.Param(
        valid.NoneOr(valid.Choice(*GROUND_MOTION_CORRELATION_MODELS)), None)
    ground_motion_correlation_params = valid.Param(valid.dictionary)
    ground_motion_fields = valid.Param(valid.boolean, False)
    gsim = valid.Param(valid.gsim, None)
    hazard_calculation_id = valid.Param(valid.NoneOr(valid.positiveint), None)
    hazard_curves_from_gmfs = valid.Param(valid.boolean, False)
    hazard_output_id = valid.Param(valid.NoneOr(valid.positiveint))
    hazard_maps = valid.Param(valid.boolean, False)
    hypocenter = valid.Param(valid.point3d)
    ignore_missing_costs = valid.Param(valid.namelist, [])
    individual_curves = valid.Param(valid.boolean, True)
    inputs = valid.Param(dict, {})
    insured_losses = valid.Param(valid.boolean, False)
    intensity_measure_types = valid.Param(valid.intensity_measure_types, None)
    intensity_measure_types_and_levels = valid.Param(
        valid.intensity_measure_types_and_levels, None)
    # hazard_imtls = valid.Param(valid.intensity_measure_types_and_levels, {})
    hazard_investigation_time = valid.Param(valid.positivefloat, None)
    interest_rate = valid.Param(valid.positivefloat)
    investigation_time = valid.Param(valid.positivefloat, None)
    loss_curve_resolution = valid.Param(valid.positiveint, 50)
    lrem_steps_per_interval = valid.Param(valid.positiveint, 0)
    steps_per_interval = valid.Param(valid.positiveint, 0)
    master_seed = valid.Param(valid.positiveint, 0)
    maximum_distance = valid.Param(valid.positivefloat)  # km
    asset_hazard_distance = valid.Param(valid.positivefloat, 5)  # km
    maximum_tile_weight = valid.Param(valid.positivefloat)
    mean_hazard_curves = valid.Param(valid.boolean, False)
    number_of_ground_motion_fields = valid.Param(valid.positiveint, 0)
    number_of_logic_tree_samples = valid.Param(valid.positiveint, 0)
    num_epsilon_bins = valid.Param(valid.positiveint)
    poes = valid.Param(valid.probabilities)
    poes_disagg = valid.Param(valid.probabilities, [])
    quantile_hazard_curves = valid.Param(valid.probabilities, [])
    quantile_loss_curves = valid.Param(valid.probabilities, [])
    random_seed = valid.Param(valid.positiveint, 42)
    reference_depth_to_1pt0km_per_sec = valid.Param(valid.positivefloat, 1.)
    reference_depth_to_2pt5km_per_sec = valid.Param(valid.positivefloat, 1.)
    reference_vs30_type = valid.Param(
        valid.Choice('measured', 'inferred'), 'measured')
    reference_vs30_value = valid.Param(valid.positivefloat, 1.)
    reference_backarc = valid.Param(valid.boolean, False)
    region = valid.Param(valid.coordinates, None)
    region_constraint = valid.Param(valid.wkt_polygon, None)
    region_grid_spacing = valid.Param(valid.positivefloat, None)
    risk_imtls = valid.Param(valid.intensity_measure_types_and_levels, {})
    risk_investigation_time = valid.Param(valid.positivefloat, None)
    rupture_mesh_spacing = valid.Param(valid.positivefloat, None)
    complex_fault_mesh_spacing = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    ses_per_logic_tree_path = valid.Param(valid.positiveint, 1)
    sites = valid.Param(valid.NoneOr(valid.coordinates), None)
    sites_disagg = valid.Param(valid.NoneOr(valid.coordinates), [])
    specific_assets = valid.Param(valid.namelist, [])
    statistics = valid.Param(valid.boolean, True)
    taxonomies_from_model = valid.Param(valid.boolean, False)
    time_event = valid.Param(str, None)
    truncation_level = valid.Param(valid.NoneOr(valid.positivefloat), None)
    uniform_hazard_spectra = valid.Param(valid.boolean, False)
    width_of_mfd_bin = valid.Param(valid.positivefloat)

    def __init__(self, **names_vals):
        super(OqParam, self).__init__(**names_vals)
        if not self.risk_investigation_time and self.investigation_time:
            self.risk_investigation_time = self.investigation_time
        elif not self.investigation_time and self.hazard_investigation_time:
            self.investigation_time = self.hazard_investigation_time
        if 'intensity_measure_types' in names_vals:
            self.hazard_imtls = dict.fromkeys(self.intensity_measure_types)
            delattr(self, 'intensity_measure_types')
        elif 'intensity_measure_types_and_levels' in names_vals:
            self.hazard_imtls = self.intensity_measure_types_and_levels
            delattr(self, 'intensity_measure_types_and_levels')
        if vulnerability_files(self.inputs):
            self.risk_imtls = get_imtls_from_vulnerabilities(self.inputs)
        elif fragility_files(self.inputs):
            fname = self.inputs['fragility']
            ffs = get_fragility_functions(
                fname, self.continuous_fragility_discretization)
            self.risk_imtls = {fset.imt: fset.imls
                               for fset in ffs.itervalues()}

    @property
    def tses(self):
        """
        Return the total time as investigation_time * ses_per_logic_tree_path *
        (number_of_logic_tree_samples or 1)
        """
        return (self.hazard_investigation_time * self.ses_per_logic_tree_path *
                (self.number_of_logic_tree_samples or 1))

    @property
    def imtls(self):
        """
        Returns an OrderedDict with the risk intensity measure types and
        levels, if given, or the hazard ones.
        """
        imtls = getattr(self, 'hazard_imtls', None) or self.risk_imtls
        return collections.OrderedDict(sorted(imtls.items()))

    def no_imls(self):
        """
        Return True if there are no intensity measure levels
        """
        return all(ls is None for ls in self.imtls.itervalues())

    def is_valid_truncation_level_disaggregation(self):
        """
        Truncation level must be set for disaggregation calculations
        """
        if self.calculation_mode == 'disaggregation':
            return self.truncation_level is not None
        else:
            return True

    def is_valid_geometry(self):
        """
        It is possible to infer the geometry only if exactly
        one of sites, sites_csv, hazard_curves_csv, gmfs_csv,
        region and exposure_file is set. You did set more than
        one, or nothing.
        """
        if self.calculation_mode not in HAZARD_CALCULATORS:
            return True  # no check on the sites for risk
        flags = dict(
            sites=bool(self.sites),
            sites_csv=self.inputs.get('sites', 0),
            hazard_curves_csv=self.inputs.get('hazard_curves', 0),
            gmfs_csv=self.inputs.get('gmvs', 0),
            region=bool(self.region),
            exposure=self.inputs.get('exposure', 0))
        # NB: below we check that all the flags
        # are mutually exclusive
        return sum(bool(v) for v in flags.values()) == 1 or self.inputs.get(
            'site_model')

    def is_valid_poes(self):
        """
        When computing hazard maps and/or uniform hazard spectra,
        the poes list must be non-empty.
        """
        if self.hazard_maps or self.uniform_hazard_spectra:
            return bool(self.poes)
        else:
            return True

    def is_valid_site_model(self):
        """
        In absence of a site_model file the site model parameters
        must be all set.
        """
        if self.calculation_mode in HAZARD_CALCULATORS and (
                'site_model' not in self.inputs):
            return (self.reference_vs30_type and
                    self.reference_vs30_value and
                    self.reference_depth_to_2pt5km_per_sec and
                    self.reference_depth_to_1pt0km_per_sec)
        else:
            return True

    def is_valid_maximum_distance(self):
        """
        The maximum_distance must be set for all hazard calculators
        """
        return (self.calculation_mode not in HAZARD_CALCULATORS
                or getattr(self, 'maximum_distance', None))

    def is_valid_intensity_measure_types(self):
        """
        If the IMTs and levels are extracted from the risk models,
        they must not be set directly. Moreover, if
        `intensity_measure_types_and_levels` is set directly,
        `intensity_measure_types` must not be set.
        """
        if self.ground_motion_correlation_model:
            for imt in self.imtls:
                if not (imt.startswith('SA') or imt == 'PGA'):
                    raise ValueError(
                        'Correlation model %s does not accept IMT=%s' % (
                            self.ground_motion_correlation_model, imt))
        if fragility_files(self.inputs) or vulnerability_files(self.inputs):
            return (self.intensity_measure_types is None
                    and self.intensity_measure_types_and_levels is None)
        elif not hasattr(self, 'hazard_imtls') and not hasattr(
                self, 'risk_imtls'):
            return False
        return True

    def is_valid_intensity_measure_levels(self):
        """
        In order to compute hazard curves, `intensity_measure_types_and_levels`
        must be set or extracted from the risk models.
        """
        invalid = self.no_imls() and (
            self.hazard_curves_from_gmfs or self.calculation_mode in
            ('classical', 'classical_tiling', 'disaggregation'))
        return not invalid

    def is_valid_sites_disagg(self):
        """
        The option `sites_disagg` (when given) requires `specific_assets` to
        be set.
        """
        if self.sites_disagg:
            return self.specific_assets or 'specific_assets' in self.inputs
        return True  # a missing sites_disagg is valid

    def is_valid_specific_assets(self):
        """
        Read the special assets from the parameters `specific_assets` or
        `specific_assets_csv`, if present. You cannot have both. The
        concept is meaninful only for risk calculators.
        """
        if self.specific_assets and 'specific_assets' in self.inputs:
            return False
        else:
            return True

    def is_valid_hazard_curves(self):
        """
        You must set `hazard_curves_from_gmfs` if `mean_hazard_curves`
        or `quantile_hazard_curves` are set.
        """
        if self.calculation_mode == 'event_based' and (
           self.mean_hazard_curves or self.quantile_hazard_curves):
            return self.hazard_curves_from_gmfs
        return True

    def is_valid_export_dir(self):
        """
        The `export_dir` parameter must refer to a directory,
        and the user must have the permission to write on it.
        """
        if not self.export_dir:
            self.export_dir = os.path.expanduser('~')  # home directory
            logging.warn('export_dir not specified. Using export_dir=%s'
                         % self.export_dir)
            return True
        elif not os.path.exists(self.export_dir):
            # check that we can write on the parent directory
            pdir = os.path.dirname(self.export_dir)
            can_write = os.path.exists(pdir) and os.access(pdir, os.W_OK)
            if can_write:
                os.mkdir(self.export_dir)
            return can_write
        return os.path.isdir(self.export_dir) and os.access(
            self.export_dir, os.W_OK)

    def is_valid_inputs(self):
        """
        Invalid calculation_mode="{calculation_mode}" or missing
        fragility_file/vulnerability_file in the .ini file.
        """
        if 'damage' in self.calculation_mode:
            return 'fragility' in self.inputs
        elif 'risk' in self.calculation_mode:
            return any(key.endswith('_vulnerability') for key in self.inputs)
        return True

    def is_valid_complex_fault_mesh_spacing(self):
        """
        The `complex_fault_mesh_spacing` parameter can be None only if
        `rupture_mesh_spacing` is set. In that case it is identified with it.
        """
        rms = getattr(self, 'rupture_mesh_spacing', None)
        if rms and not getattr(self, 'complex_fault_mesh_spacing', None):
            self.complex_fault_mesh_spacing = self.rupture_mesh_spacing
        return True

    def is_valid_gsim(self):
        """
        If `gsim_logic_tree_file` is set, there must be no `gsim` key in
        the configuration file.
        """
        if 'gsim_logic_tree' in self.inputs:
            return self.gsim is None
        return True
