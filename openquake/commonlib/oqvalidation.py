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

from openquake.hazardlib.gsim import get_available_gsims
from openquake.commonlib import valid

GSIMS = get_available_gsims()

GROUND_MOTION_CORRELATION_MODELS = [
    'JB2009', 'Jayaram-Baker 2009']

HAZARD_CALCULATORS = [
    'classical', 'disaggregation', 'event_based', 'scenario']

RISK_CALCULATORS = [
    'classical_risk', 'event_based_risk', 'scenario_risk',
    'classical_bcr', 'event_based_bcr', 'scenario_damage']

EXPERIMENTAL_CALCULATORS = [
    'event_based_fr']

CALCULATORS = HAZARD_CALCULATORS + RISK_CALCULATORS + EXPERIMENTAL_CALCULATORS

KNOWN_VULNERABILITIES = (
    'structural_vulnerability', 'nonstructural_vulnerability',
    'contents_vulnerability', 'business_interruption_vulnerability',
    'occupants_vulnerability', 'structural_vulnerability_retrofitted')


def vulnerability_files(inputs):
    """
    Return a list of path names for the known vulnerability keys.

    :param inputs: a dictionary key -> path name
    """
    return [inputs[key] for key in inputs if key in KNOWN_VULNERABILITIES]


def fragility_files(inputs):
    """
    Return a list of path names for the fragility keys.

    :param inputs: a dictionary key -> path name

    NB: at the moment there is a single fragility key, so the list
    contains at most one element.
    """
    return [inputs[key] for key in inputs if key == 'fragility']


class OqParam(valid.ParamSet):
    params = valid.parameters(
        area_source_discretization=valid.positivefloat,
        asset_correlation=valid.NoneOr(valid.FloatRange(0, 1)),
        asset_life_expectancy=valid.positivefloat,
        base_path=valid.utf8,
        calculation_mode=valid.Choice(*CALCULATORS),
        coordinate_bin_width=valid.positivefloat,
        conditional_loss_poes=valid.probabilities,
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
        individual_curves=valid.boolean,
        inputs=dict,
        insured_losses=valid.boolean,
        intensity_measure_types=valid.intensity_measure_types,
        intensity_measure_types_and_levels=
        valid.intensity_measure_types_and_levels,
        interest_rate=valid.positivefloat,
        investigation_time=valid.positivefloat,
        loss_curve_resolution=valid.positiveint,
        lrem_steps_per_interval=valid.positiveint,
        master_seed=valid.positiveint,
        maximum_distance=valid.positivefloat,
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
        region=valid.coordinates,
        region_constraint=valid.coordinates,
        region_grid_spacing=valid.positivefloat,
        risk_investigation_time=valid.positivefloat,
        rupture_mesh_spacing=valid.positivefloat,
        ses_per_logic_tree_path=valid.positiveint,
        sites=valid.NoneOr(valid.coordinates),
        sites_disagg=valid.NoneOr(valid.coordinates),
        taxonomies_from_model=valid.boolean,
        time_event=str,
        truncation_level=valid.NoneOr(valid.positivefloat),
        uniform_hazard_spectra=valid.boolean,
        width_of_mfd_bin=valid.positivefloat,
        )

    def is_valid_hazard_calculation_and_output(self):
        """
        The parameters `hazard_calculation_id` and `hazard_output_id`
        are not correct for this calculator.
        """
        if self.calculation_mode in HAZARD_CALCULATORS:
            return (self.hazard_calculation_id is None and
                    self.hazard_output_id is None)
        return (self.hazard_calculation_id is None and
                self.hazard_output_id is not None) or \
            (self.hazard_calculation_id is not None and
             self.hazard_output_id is None)

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
        Must specify either region, sites or exposure_file.
        """
        if self.calculation_mode not in HAZARD_CALCULATORS:
            return True  # no check on the sites for risk
        sites = getattr(self, 'sites', self.inputs.get('site'))
        if getattr(self, 'region', None):
            return sites is None and not 'exposure' in self.inputs
        elif 'exposure' in self.inputs:
            return sites is None
        else:
            return sites is not None

    def is_valid_poes(self):
        """
        When computing hazard maps and/or uniform hazard spectra,
        the poes list must be non-empty.
        """
        if getattr(self, 'hazard_maps', None) or getattr(
                self, 'uniform_hazard_spectra', None):
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
