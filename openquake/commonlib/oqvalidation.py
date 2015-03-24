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
from openquake.hazardlib.gsim import get_available_gsims
from openquake.commonlib import valid
from openquake.commonlib.riskmodels import (
    get_fragility_functions, get_imtls_from_vulnerabilities,
    vulnerability_files, fragility_files)

GSIMS = get_available_gsims()

GROUND_MOTION_CORRELATION_MODELS = ['JB2009']

HAZARD_CALCULATORS = [
    'classical', 'disaggregation', 'event_based', 'scenario',
    'classical_tiling']

RISK_CALCULATORS = [
    'classical_risk', 'event_based_risk', 'scenario_risk',
    'classical_bcr', 'event_based_bcr', 'scenario_damage', 'classical_damage']

EXPERIMENTAL_CALCULATORS = [
    'event_loss']

CALCULATORS = HAZARD_CALCULATORS + RISK_CALCULATORS + EXPERIMENTAL_CALCULATORS


class OqParam(valid.ParamSet):
    exports = 'csv'  # default value, normally overridden

    params = valid.parameters(
        area_source_discretization=valid.NoneOr(valid.positivefloat),
        asset_correlation=valid.NoneOr(valid.FloatRange(0, 1)),
        asset_life_expectancy=valid.positivefloat,
        base_path=valid.utf8,
        calculation_mode=valid.Choice(*CALCULATORS),
        coordinate_bin_width=valid.positivefloat,
        conditional_loss_poes=valid.probabilities,
        continuous_fragility_discretization=valid.positiveint,
        description=valid.utf8_not_empty,
        distance_bin_width=valid.positivefloat,
        mag_bin_width=valid.positivefloat,
        export_dir=valid.utf8,
        export_multi_curves=valid.boolean,
        ground_motion_correlation_model=valid.NoneOr(
            valid.Choice(*GROUND_MOTION_CORRELATION_MODELS)),
        ground_motion_correlation_params=valid.dictionary,
        ground_motion_fields=valid.boolean,
        gsim=valid.Choice(*GSIMS),
        hazard_calculation_id=valid.NoneOr(valid.positiveint),
        hazard_curves_from_gmfs=valid.boolean,
        hazard_output_id=valid.NoneOr(valid.positiveint),
        hazard_maps=valid.boolean,
        hypocenter=valid.point3d,
        ignore_missing_costs=valid.namelist,
        individual_curves=valid.boolean,
        inputs=dict,
        insured_losses=valid.boolean,
        intensity_measure_types=valid.intensity_measure_types,
        intensity_measure_types_and_levels=
        valid.intensity_measure_types_and_levels,
        hazard_imtls=valid.intensity_measure_types_and_levels,
        hazard_investigation_time=valid.positivefloat,
        interest_rate=valid.positivefloat,
        investigation_time=valid.positivefloat,
        loss_curve_resolution=valid.positiveint,
        lrem_steps_per_interval=valid.positiveint,  # maybe will be deprecated
        steps_per_interval=valid.positiveint,
        master_seed=valid.positiveint,
        maximum_distance=valid.positivefloat,
        maximum_tile_weight=valid.positivefloat,
        mean_hazard_curves=valid.boolean,
        number_of_ground_motion_fields=valid.positiveint,
        number_of_logic_tree_samples=valid.positiveint,
        num_epsilon_bins=valid.positiveint,
        poes=valid.probabilities,
        poes_disagg=valid.probabilities,
        quantile_hazard_curves=valid.probabilities,
        quantile_loss_curves=valid.probabilities,
        random_seed=valid.positiveint,
        reference_depth_to_1pt0km_per_sec=valid.positivefloat,
        reference_depth_to_2pt5km_per_sec=valid.positivefloat,
        reference_vs30_type=valid.Choice('measured', 'inferred'),
        reference_vs30_value=valid.positivefloat,
        reference_backarc=valid.boolean,
        region=valid.coordinates,
        region_constraint=valid.wkt_polygon,
        region_grid_spacing=valid.positivefloat,
        risk_investigation_time=valid.positivefloat,
        rupture_mesh_spacing=valid.positivefloat,
        complex_fault_mesh_spacing=valid.NoneOr(valid.positivefloat),
        ses_per_logic_tree_path=valid.positiveint,
        sites=valid.NoneOr(valid.coordinates),
        sites_disagg=valid.NoneOr(valid.coordinates),
        specific_assets=str.split,
        statistics=valid.boolean,
        taxonomies_from_model=valid.boolean,
        time_event=str,
        truncation_level=valid.NoneOr(valid.positivefloat),
        uniform_hazard_spectra=valid.boolean,
        width_of_mfd_bin=valid.positivefloat,
        )

    def __init__(self, **names_vals):
        super(OqParam, self).__init__(**names_vals)
        if not hasattr(self, 'reference_backarc'):
            self.reference_backarc = False
        if hasattr(self, 'intensity_measure_types'):
            self.hazard_imtls = dict.fromkeys(self.intensity_measure_types)
            # remove the now redundant parameter
            delattr(self, 'intensity_measure_types')
        elif hasattr(self, 'intensity_measure_types_and_levels'):
            self.hazard_imtls = self.intensity_measure_types_and_levels
            # remove the now redundant parameter
            delattr(self, 'intensity_measure_types_and_levels')
        if vulnerability_files(self.inputs):
            self.risk_imtls = get_imtls_from_vulnerabilities(self.inputs)
        elif fragility_files(self.inputs):
            fname = self.inputs['fragility']
            # continuous_fragility_discretization with a default
            cfd = self.__dict__.setdefault(
                'continuous_fragility_discretization', 20)
            ffs = get_fragility_functions(fname, cfd)
            self.risk_imtls = {fset.imt: fset.imls
                               for fset in ffs.itervalues()}
        if 'event_based' in self.calculation_mode and not hasattr(
                self, 'loss_curve_resolution'):
            self.loss_curve_resolution = 50  # default

    @property
    def imtls(self):
        """
        Returns an OrderedDict with the risk intensity measure types and
        levels, if given, or the hazard ones.
        """
        imtls = getattr(self, 'risk_imtls', None) or getattr(
            self, 'hazard_imtls', None)
        return collections.OrderedDict(sorted(imtls.items()))

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
        one of sites, sites_csv, hazard_curves_csv, gmvs_csv,
        region and exposure_file is set. You did set more than
        one, or nothing.
        """
        if self.calculation_mode not in HAZARD_CALCULATORS:
            return True  # no check on the sites for risk
        flags = dict(
            sites=getattr(self, 'sites', 0),
            sites_csv=self.inputs.get('sites', 0),
            hazard_curves_csv=self.inputs.get('hazard_curves', 0),
            gmvs_csv=self.inputs.get('gmvs', 0),
            region=getattr(self, 'region', 0),
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
        if getattr(self, 'hazard_maps', None) or getattr(
                self, 'uniform_hazard_spectra', None):
            return bool(getattr(self, 'poes', None))
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
        return self.calculation_mode in RISK_CALCULATORS or (
            getattr(self, 'maximum_distance', None))

    def is_valid_imtls(self):
        """
        If the IMTs and levels are extracted from the risk models,
        they must not be set directly. Moreover, if
        `intensity_measure_types_and_levels` is set directly,
        `intensity_measure_types` must not be set.
        """
        if fragility_files(self.inputs) or vulnerability_files(self.inputs):
            return (
                getattr(self, 'intensity_measure_types', None) is None
                and getattr(self, 'intensity_measure_types_and_levels', None
                            ) is None
                )
        elif getattr(self, 'intensity_measure_types_and_levels', None):
            return getattr(self, 'intensity_measure_types', None) is None
        return True

    def is_valid_sites_disagg(self):
        """
        The option `sites_disagg` (when given) requires `specific_assets` to
        be set.
        """
        if getattr(self, 'sites_disagg', None):
            return getattr(self, 'specific_assets', None) or \
                'specific_assets' in self.inputs
        return True  # a missing sites_disagg is valid

    def is_valid_specific_assets(self):
        """
        Read the special assets from the parameters `specific_assets` or
        `specific_assets_csv`, if present. You cannot have both. The
        concept is meaninful only for risk calculators.
        """
        specific_assets = getattr(self, 'specific_assets', None)
        if specific_assets and 'specific_assets' in self.inputs:
            return False
        else:
            return True

    def is_valid_hazard_curves(self):
        """
        You must set `hazard_curves_from_gmfs` if `mean_hazard_curves`
        or `quantile_hazard_curves` are set.
        """
        if self.calculation_mode == 'event_based' and (
           getattr(self, 'mean_hazard_curves', False) or
           getattr(self, 'quantile_hazard_curves', False)):
            return getattr(self, 'hazard_curves_from_gmfs', False)
        return True

    def is_valid_export_dir(self):
        """
        The `export_dir` parameter must refer to a directory,
        and the user must have the permission to write on it.
        """
        if not hasattr(self, 'export_dir'):
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

    def is_valid_tiling(self):
        """
        Currently the classical_tiling calculator does not support
        sampling.
        """
        if self.calculation_mode == 'classical_tiling':
            return (self.maximum_tile_weight and not
                    self.number_of_logic_tree_samples)
        return True
