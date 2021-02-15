# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from openquake.baselib import __version__

__doc__ = """\
Full list of configuration parameters
=====================================

Engine Version: %s

Some parameters have a default that it is used when the parameter is
not specified in the job.ini file. Some other parameters have no default,
which means that not specifying them will raise an error when running
a calculation for which they are required.

aggregate_by:
  Used to compute aggregate losses and aggregate loss curves in risk
  calculations. Takes in input one or more exposure tags.
  Example: *aggregate_by = region, taxonomy*.
  Default: empty list

amplification_method:
  Used in classical PSHA calculations to amplify the hazard curves with
  the convolution or kernel method.
  Example: *amplification_method = convolution*.
  Default: None

area_source_discretization:
  Discretization parameters (in km) for area sources.
  Example: *area_source_discretization = 10*.
  Default: 10

ash_wet_amplification_factor:
  Used in volcanic risk calculations.
  Example: *ash_wet_amplification_factor=1.0*.
  Default: 1.0

asset_correlation:
  Used in risk calculations to take into account asset correlation. Accepts
  only the values 1 (full correlation) and 0 (no correlation).
  Example: *asset_correlation=1*.
  Default: 0

asset_hazard_distance:
  In km, used in risk calculations to print a warning when there are assets
  too distant from the hazard sites.
  Example: *asset_hazard_distance = 5*.
  Default: 15

asset_life_expectancy:
  Used in the classical_bcr calculator.
  Example: *asset_life_expectancy = 50*.
  Default: no default

assets_per_site_limit:
  INTERNAL

avg_losses:
  Used in risk calculations to compute average losses.
  Example: *avg_losses=false*.
  Default: True

base_path:
  INTERNAL

cachedir:
  INTERNAL

calculation_mode:
  One of classical, disaggregation, event_based, scenario, scenario_risk,
  scenario_damage, event_based_risk, classical_risk, classical_bcr.
  Example: *calculation_mode=classical*
  Default: no default

collapse_gsim_logic_tree:
  INTERNAL

collapse_level:
  INTERNAL

compare_with_classical:
  Used in event based calculation to perform also a classical calculation,
  so that the hazard curves can be compared.
  Example: *compare_with_classical = true*.
  Default: False

complex_fault_mesh_spacing:
  In km, used to discretize complex faults.
  Example: *complex_fault_mesh_spacing = 15*.
  Default: 5

concurrent_tasks:
  A hint to the engine for the number of tasks to generate. Do not set
  it unless you know what you are doing.
  Example: *concurrent_tasks = 100*.
  Default: twice the number of cores

conditional_loss_poes:
  Used in classical_risk calculations to compute loss curves.
  Example: *conditional_loss_poes = 0.01 0.02*.
  Default: empty list

float_dmg_dist:
  Flag used in scenario_damage calculations to specify that the damage
  distributions should be stored as floating point numbers (float32)
  and not as integers (uint32).
  Example: *float_dmg_dist = true*.
  Default: False

continuous_fragility_discretization:
  Used when discretizing continuuos fragility functions.
  Example: *continuous_fragility_discretization = 10*.
  Default: 20

coordinate_bin_width:
  Used in disaggregation calculations.
  Example: *coordinate_bin_width = 1.0*.
  Default: no default

cross_correlation:
  Used in ShakeMap calculations. Valid choices are "yes", "no" "full",
  same as for *spatial_correlation*.
  Example: *cross_correlation = no*.
  Default: "yes"

description:
  A string describing the calculation.
  Example: *description = Test calculation*.
  Default: no default

disagg_by_src:
  Flag used to enable disaggregation by source when possible.
  Example: *disagg_by_src = true*.
  Default: False

disagg_outputs:
  Used in disaggregation calculations to restrict the number of exported
  outputs.
  Example: *disagg_outputs = Mag_Dist*
  Default: list of all possible outputs

discard_assets:
  Flag used in risk calculations to discard assets from the exposure.
  Example: *discard_assets = true*.
  Default: False

discard_trts:
  Used to discard tectonic region types that do not contribute to the hazard.
  Example: *discard_trts = Volcanic*.
  Default: empty list

distance_bin_width:
  In km, used in disaggregation calculations to specify the distance bins.
  Example: *distance_bin_width = 20*.
  Default: no default

ebrisk_maxsize:
  INTERNAL

export_dir:
  Set the export directory.
  Example: *export_dir = /tmp*.
  Default: the current directory, "."

exports:
  Specify what kind of outputs to export by default.
  Example: *exports = csv, rst*.
  Default: empty list

ground_motion_correlation_model:
  Enable ground motion correlation.
  Example: *ground_motion_correlation_model = JB2009*.
  Default: None

ground_motion_correlation_params:
  To be used together with ground_motion_correlation_model.
  Example: *ground_motion_correlation_params = {"vs30_clustering": False}*.
  Default: empty dictionary

ground_motion_fields:
  Flag to turn on/off the calculation of ground motion fields.
  Example: *ground_motion_fields = false*.
  Default: True

gsim:
   Used to specify a GSIM in scenario or event based calculations.
   Example: *gsim = BooreAtkinson2008*.
   Default: "[FromFile]"

hazard_calculation_id:
  Used to specify a previous calculation from which the hazard is read.
  Example: *hazard_calculation_id = 42*.
  Default: None

hazard_curves_from_gmfs:
  Used in scenario/event based calculations. If set, generates hazard curves
  from the ground motion fields.
  Example: *hazard_curves_from_gmfs = true*.
  Default: False

hazard_maps:
  Set it to true to export the hazard maps.
  Example: *hazard_maps = true*.
  Default: False

ignore_covs:
  Used in risk calculations to set all the coefficients of variation of the
  vulnerability functions to zero.
  Example *ignore_covs = true*
  Default: False

ignore_missing_costs:
  Accepts exposures with missing costs (by discarding such assets).
  Example: *ignore_missing_costs = nonstructural, business_interruption*.
  Default: False

iml_disagg:
  Used in disaggregation calculations to specify an intensity measure type
  and level.
  Example: *iml_disagg = {'PGA': 0.02}*.
  Default: no default

individual_curves:
  When set, store the individual hazard curves and/or individual risk curves
  for each realization.
  Example: *individual_curves = true*.
  Default: False

inputs:
  INTERNAL. Dictionary with the input files paths.

intensity_measure_types:
  List of intensity measure types in an event based calculation.
  Example: *intensity_measure_types = PGA SA(0.1)*.
  Default: empty list

intensity_measure_types_and_levels:
  List of intensity measure types and levels in a classical calculation.
  Example: *intensity_measure_types_and_levels={"PGA": logscale(0.1, 1, 20)}*.
  Default: empty dictionary

interest_rate:
  Used in classical_bcr calculations.
  Example: *interest_rate = 0.05*.
  Default: no default

investigation_time:
  Hazard investigation time in years, used in classical and event based
  calculations.
  Example: *investigation_time = 50*.
  Default: no default

lrem_steps_per_interval:
  Used in the vulnerability functions.
  Example: *lrem_steps_per_interval  = 1*.
  Default: 0

mag_bin_width:
  Width of the magnitude bin used in disaggregation calculations.
  Example: *mag_bin_width = 0.5*.
  Default: no default

master_seed:
  Seed used to control the generation of the epsilons, relevant for risk
  calculations with vulnerability functions with nonzero coefficients of
  variation.
  Example: *master_seed = 1234*.
  Default: 0

max:
  Compute the maximum across realizations. Akin to mean and quantiles.
  Example: *max = true*.
  Default: False

max_data_transfer:
  INTERNAL. Restrict the maximum data transfer in disaggregation calculations.

max_potential_gmfs:
  Restrict the product *num_sites * num_events*.
  Example: *max_potential_gmfs = 1E9*.
  Default: 2E11

max_potential_paths:
  Restrict the maximum number of realizations.
  Example: *max_potential_paths = 200*.
  Default: 100

max_sites_disagg:
  Maximum number of sites for which to store rupture information.
  In disaggregation calculations with many sites you may be forced to raise
  *max_sites_disagg*, that must be greater or equal to the number of sites.
  Example: *max_sites_disagg = 100*
  Default: 10

max_sites_per_gmf:
  Restrict the maximum number of sites in event based calculation with GMFs.
  Example: *max_sites_per_gmf = 100_000*.
  Default: 65536

max_sites_per_tile:
  INTERNAL

max_weight:
  INTERNAL

maximum_distance:
  Integration distance. Can be give as a scalar, as a dictionary TRT -> scalar
  or as dictionary TRT -> [(mag, dist), ...]
  Example: *maximum_distance = 200*.
  Default: no default

mean:
  Flag to enable/disable the calculation of mean curves.
  Example: *mean = false*.
  Default: True

min_weight:
  INTERNAL

minimum_asset_loss:
  Used in risk calculations. If set, losses smaller than the
  *minimum_asset_loss* are consider zeros.
  Example: *minimum_asset_loss = {"structural": 1000}*.
  Default: empty dictionary

minimum_intensity:
  If set, ground motion values below the *minimum_intensity* are
  considered zeros.
  Example: *minimum_intensity = {'PGA': .01}*.
  Default: empty dictionary

minimum_magnitude:
  If set, ruptures below the *minimum_magnitude* are discarded.
  Example: *minimum_magnitude = 5.0*.
  Default: 0

modal_damage_state:
  Used in scenario_damage calculations to export only the damage state
  with the highest probability.
  Example: *modal_damage_state = true*.
  Default: false

num_epsilon_bins:
  Number of epsilon bins in disaggregation calculations.
  Example: *num_epsilon_bins = 3*.
  Default: no default

num_rlzs_disagg:
  Used in disaggregation calculation to specify how many outputs will be
  generated.
  Example: *num_rlzs_disagg=1*.
  Default: None

number_of_ground_motion_fields:
  Used in scenario calculations to specify how many random ground motion
  fields to generate.
  Example: *number_of_ground_motion_fields = 100*.
  Default: no default

number_of_logic_tree_samples:
  Used to specify the number of realizations to generate when using logic tree
  sampling. If zero, full enumeration is performed.
  Example: *number_of_logic_tree_samples = 0*.
  Default: no default

poes:
  Probabilities of Exceedance used to specify the hazard maps or hazard spectra
  to compute.
  Example: *poes = 0.01 0.02*.
  Default: empty list

poes_disagg:
   Alias for poes.

pointsource_distance:
  Used in classical calculations to collapse the point sources. Can also be
  used in conjunction with *ps_grid_spacing*.
  Example: *pointsource_distance = 50*.
  Default: empty dictionary

ps_grid_spacing:
  Used in classical calculations to grid the point sources. Requires the
  *pointsource_distance* to be set too.
  Example: *ps_grid_spacing = 50*.
  Default: no default

quantiles:
  List of probabilities used to compute the quantiles across realizations.
  Example: quantiles = 9.15 0.50 0.85
  Default: empty list

random_seed:
  Seed used in the sampling of the logic tree.
  Example: *random_seed = 1234*.
  Default: 42

reference_backarc:
  Used when there is no site model to specify a global backarc parameter,
  used in some GMPEs. Can be True or False
  Example: *reference_backarc = true*.
  Default: False

reference_depth_to_1pt0km_per_sec:
  Used when there is no site model to specify a global z1pt0 parameter,
  used in some GMPEs.
  Example: *reference_depth_to_1pt0km_per_sec = 100*.
  Default: no default

reference_depth_to_2pt5km_per_sec:
  Used when there is no site model to specify a global z2pt5 parameter,
  used in some GMPEs.
  Example: *reference_depth_to_2pt5km_per_sec = 5*.
  Default: no default

reference_siteclass:
  Used when there is no site model to specify a global site class.
  The siteclass is a one-character letter used in some GMPEs, like the
  McVerry (2006), and has values "A", "B", "C" or "D".
  Example: *reference_siteclass = "A"*.
  Default: "D"

reference_vs30_type:
  Used when there is no site model to specify a global vs30 type.
  The choices are "inferred" or "measured"
  Example: *reference_vs30_type = inferred".
  Default: "measured"

reference_vs30_value:
  Used when there is no site model to specify a global vs30 value.
  Example: *reference_vs30_value = 760*.
  Default: no default

region:
  A list of lon/lat pairs used to specify a region of interest
  Example: *region = 10.0 43.0, 12.0 43.0, 12.0 46.0, 10.0 46.0*
  Default: None

region_grid_spacing:
  Used together with the *region* option to generate the hazard sites.
  Example: *region_grid_spacing = 10*.
  Default: None

return_periods:
  Used in the computation of the loss curves.
  Example: *return_periods = 200 500 1000*.
  Default: empty list.

risk_imtls:
  INTERNAL. Automatically set by the engine.

risk_investigation_time:
  Used in risk calculations. If not specified, the (hazard) investigation_time
  is used instead.
  Example: *risk_investigation_time = 50*.
  Default: None

rlz_index:
  Used in disaggregation calculations to specify the realization from which
  to start the disaggregation.
  Example: *rlz_index = 0*.
  Default: None

rupture_mesh_spacing:
  Set the discretization parameter (in km) for rupture geometries.
  Example: *rupture_mesh_spacing = 2.0*.
  Default: 5.0

ruptures_per_block:
  INTERNAL

sampling_method:
  One of early_weights, late_weights, early_latin, late_latin)
  Example: *sampling_method = early_latin*.
  Default: 'early_weights'

save_disk_space:
 INTERNAL

sec_peril_params:
  INTERNAL

secondary_perils:
  INTERNAL

secondary_simulations:
  INTERNAL

sensitivity_analysis:
  Dictionary describing a sensitivity analysis.
  Example: *sensitivity_analysis = {'maximum_distance': [200, 300]}*.
  Default: empty dictionary

ses_per_logic_tree_path:
  Set the number of stochastic event sets per logic tree realization in
  event based calculations.
  Example: *ses_per_logic_tree_path = 100*.
  Default: 1

ses_seed:
  Seed governing the generation of the ground motion field.
  Example: *ses_seed = 123*.
  Default: 42

shakemap_id:
  Used in ShakeMap calculations to download a ShakeMap from the USGS site
  Example: *shakemap_id = usp000fjta*.
  Default: no default

shift_hypo:
  Used in classical calculations to shift the rupture hypocenter.
  Example: *shift_hypo = true*.
  Default: false

site_effects:
  Flag used in ShakeMap calculations to turn out GMF amplification
  Example: *site_effects = true*.
  Default: False

sites:
  Used to specify a list of sites.
  Example: *sites = 10.1 45, 10.2 45*.

sites_slice:
  INTERNAL

soil_intensities:
  Used in classical calculations with amplification_method = convolution

source_id:
   Used for debugging purposes. When given, restricts the source model to the
   given source IDs.
   Example: *source_id = src001 src002*.
   Default: empty list

spatial_correlation:
  Used in the ShakeMap calculator. The choics are "yes", "no" and "full".
  Example: *spatial_correlation = full*.
  Default: "yes"

specific_assets:
  INTERNAL

split_sources:
  INTERNAL

std:
  Compute the standard deviation  across realizations. Akin to mean and max.
  Example: *std = true*.
  Default: False

steps_per_interval:
  Used in the fragility functions when building the intensity levels
  Example: *steps_per_interval = 4*.
  Default: 1

time_event:
  Used in scenario_risk calculations when the occupancy depend on the time.
  Valid choices are "day", "night", "transit".
  Example: *time_event = day*.
  Default: None

truncation_level:
  Truncation level used in the GMPEs.
  Example: *truncation_level = 0* to compute median GMFs.
  Default: no default

uniform_hazard_spectra:
  Flag used to generated uniform hazard specta for the given poes
  Example: *uniform_hazard_spectra = true*.
  Default: False

vs30_tolerance:
  Used when amplification_method = convolution.
  Example: *vs30_tolerance = 20*.
  Default: 0

width_of_mfd_bin:
  Used to specify the width of the Magnitude Frequency Distribution.
  Example: *width_of_mfd_bin = 0.2*.
  Default: None
""" % __version__
import os
import re
import logging
import functools
import multiprocessing
import numpy

from openquake.baselib.general import DictArray, AccumDict
from openquake.hazardlib.imt import from_string
from openquake.hazardlib import correlation, stats, calc
from openquake.hazardlib import valid, InvalidFile
from openquake.sep.classes import SecondaryPeril
from openquake.commonlib import logictree, util
from openquake.risklib.riskmodels import get_risk_files

GROUND_MOTION_CORRELATION_MODELS = ['JB2009', 'HM2018']
TWO16 = 2 ** 16  # 65536
TWO32 = 2 ** 32
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64


def check_same_levels(imtls):
    """
    :param imtls: a dictionary (or dict-like) imt -> imls
    :returns: the periods and the levels
    :raises: a ValueError if the levels are not the same across all IMTs
    """
    if not imtls:
        raise ValueError('There are no intensity_measure_types_and_levels!')
    imls = imtls[next(iter(imtls))]
    for imt in imtls:
        if not imt.startswith(('PGA', 'SA')):
            raise ValueError('Site amplification works only with '
                             'PGA and SA, got %s' % imt)
        if (imtls[imt] == 0).all():
            raise ValueError(
                'You forgot to set intensity_measure_types_and_levels!')
        elif len(imtls[imt]) != len(imls) or any(
                l1 != l2 for l1, l2 in zip(imtls[imt], imls)):
            raise ValueError('Site amplification works only if the '
                             'levels are the same across all IMTs')
    periods = [from_string(imt).period for imt in imtls]
    return periods, imls


class OqParam(valid.ParamSet):
    KNOWN_INPUTS = {'rupture_model', 'exposure', 'site_model',
                    'source_model', 'shakemap', 'gmfs', 'gsim_logic_tree',
                    'source_model_logic_tree', 'hazard_curves', 'insurance',
                    'sites', 'job_ini', 'multi_peril', 'taxonomy_mapping',
                    'fragility', 'consequence', 'reqv', 'input_zip',
                    'amplification',
                    'nonstructural_vulnerability',
                    'nonstructural_fragility',
                    'nonstructural_consequence',
                    'structural_vulnerability',
                    'structural_fragility',
                    'structural_consequence',
                    'contents_vulnerability',
                    'contents_fragility',
                    'contents_consequence',
                    'business_interruption_vulnerability',
                    'business_interruption_fragility',
                    'business_interruption_consequence',
                    'structural_vulnerability_retrofitted',
                    'occupants_vulnerability'}
    hazard_imtls = {}
    siteparam = dict(
        vs30measured='reference_vs30_type',
        vs30='reference_vs30_value',
        z1pt0='reference_depth_to_1pt0km_per_sec',
        z2pt5='reference_depth_to_2pt5km_per_sec',
        siteclass='reference_siteclass',
        backarc='reference_backarc')
    aggregate_by = valid.Param(valid.namelist, [])
    amplification_method = valid.Param(
        valid.Choice('convolution', 'kernel'), None)
    minimum_asset_loss = valid.Param(valid.floatdict, {'default': 0})
    area_source_discretization = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    asset_correlation = valid.Param(valid.NoneOr(valid.FloatRange(0, 1)), 0)
    asset_life_expectancy = valid.Param(valid.positivefloat)
    assets_per_site_limit = valid.Param(valid.positivefloat, 1000)
    avg_losses = valid.Param(valid.boolean, True)
    base_path = valid.Param(valid.utf8, '.')
    calculation_mode = valid.Param(valid.Choice())  # -> get_oqparam
    collapse_gsim_logic_tree = valid.Param(valid.namelist, [])
    collapse_level = valid.Param(valid.Choice('0', '1', '2', '3'), 0)
    coordinate_bin_width = valid.Param(valid.positivefloat)
    compare_with_classical = valid.Param(valid.boolean, False)
    concurrent_tasks = valid.Param(
        valid.positiveint, multiprocessing.cpu_count() * 2)  # by M. Simionato
    conditional_loss_poes = valid.Param(valid.probabilities, [])
    continuous_fragility_discretization = valid.Param(valid.positiveint, 20)
    cross_correlation = valid.Param(valid.Choice('yes', 'no', 'full'), 'yes')
    cachedir = valid.Param(valid.utf8, '')
    description = valid.Param(valid.utf8_not_empty)
    disagg_by_src = valid.Param(valid.boolean, False)
    disagg_outputs = valid.Param(valid.disagg_outputs,
                                 list(calc.disagg.pmf_map))
    discard_assets = valid.Param(valid.boolean, False)
    discard_trts = valid.Param(str, '')  # tested in the cariboo example
    distance_bin_width = valid.Param(valid.positivefloat)
    float_dmg_dist = valid.Param(valid.boolean, False)
    mag_bin_width = valid.Param(valid.positivefloat)
    export_dir = valid.Param(valid.utf8, '.')
    exports = valid.Param(valid.export_formats, ())
    ground_motion_correlation_model = valid.Param(
        valid.NoneOr(valid.Choice(*GROUND_MOTION_CORRELATION_MODELS)), None)
    ground_motion_correlation_params = valid.Param(valid.dictionary, {})
    ground_motion_fields = valid.Param(valid.boolean, True)
    gsim = valid.Param(valid.utf8, '[FromFile]')
    hazard_calculation_id = valid.Param(valid.NoneOr(valid.positiveint), None)
    hazard_curves_from_gmfs = valid.Param(valid.boolean, False)
    hazard_maps = valid.Param(valid.boolean, False)
    ignore_missing_costs = valid.Param(valid.namelist, [])
    ignore_covs = valid.Param(valid.boolean, False)
    iml_disagg = valid.Param(valid.floatdict, {})  # IMT -> IML
    individual_curves = valid.Param(valid.boolean, False)
    inputs = valid.Param(dict, {})
    ash_wet_amplification_factor = valid.Param(valid.positivefloat, 1.0)
    intensity_measure_types = valid.Param(valid.intensity_measure_types, '')
    intensity_measure_types_and_levels = valid.Param(
        valid.intensity_measure_types_and_levels, None)
    interest_rate = valid.Param(valid.positivefloat)
    investigation_time = valid.Param(valid.positivefloat, None)
    lrem_steps_per_interval = valid.Param(valid.positiveint, 0)
    steps_per_interval = valid.Param(valid.positiveint, 1)
    master_seed = valid.Param(valid.positiveint, 0)
    maximum_distance = valid.Param(valid.MagDepDistance.new)  # km
    asset_hazard_distance = valid.Param(valid.floatdict, {'default': 15})  # km
    max = valid.Param(valid.boolean, False)
    max_data_transfer = valid.Param(valid.positivefloat, 2E11)
    max_potential_gmfs = valid.Param(valid.positiveint, 2E11)
    max_potential_paths = valid.Param(valid.positiveint, 100)
    max_sites_per_gmf = valid.Param(valid.positiveint, 65536)
    max_sites_per_tile = valid.Param(valid.positiveint, 500_000)
    max_sites_disagg = valid.Param(valid.positiveint, 10)
    mean_hazard_curves = mean = valid.Param(valid.boolean, True)
    std = valid.Param(valid.boolean, False)
    minimum_intensity = valid.Param(valid.floatdict, {})  # IMT -> minIML
    minimum_magnitude = valid.Param(valid.floatdict, {'default': 0})  # by TRT
    modal_damage_state = valid.Param(valid.boolean, False)
    number_of_ground_motion_fields = valid.Param(valid.positiveint)
    number_of_logic_tree_samples = valid.Param(valid.positiveint, 0)
    num_epsilon_bins = valid.Param(valid.positiveint)
    num_rlzs_disagg = valid.Param(valid.positiveint, None)
    poes = valid.Param(valid.probabilities, [])
    poes_disagg = valid.Param(valid.probabilities, [])
    pointsource_distance = valid.Param(valid.MagDepDistance.new, None)
    ps_grid_spacing = valid.Param(valid.positivefloat, None)
    quantile_hazard_curves = quantiles = valid.Param(valid.probabilities, [])
    random_seed = valid.Param(valid.positiveint, 42)
    reference_depth_to_1pt0km_per_sec = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_depth_to_2pt5km_per_sec = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_vs30_type = valid.Param(
        valid.Choice('measured', 'inferred'), 'measured')
    reference_vs30_value = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_siteclass = valid.Param(valid.Choice('A', 'B', 'C', 'D'), 'D')
    reference_backarc = valid.Param(valid.boolean, False)
    region = valid.Param(valid.wkt_polygon, None)
    region_grid_spacing = valid.Param(valid.positivefloat, None)
    risk_imtls = valid.Param(valid.intensity_measure_types_and_levels, {})
    risk_investigation_time = valid.Param(valid.positivefloat, None)
    rlz_index = valid.Param(valid.positiveints, None)
    rupture_mesh_spacing = valid.Param(valid.positivefloat, 5.0)
    complex_fault_mesh_spacing = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    return_periods = valid.Param(valid.positiveints, [])
    ruptures_per_block = valid.Param(valid.positiveint, 500)  # for UCERF
    sampling_method = valid.Param(
        valid.Choice('early_weights', 'late_weights',
                     'early_latin', 'late_latin'), 'early_weights')
    save_disk_space = valid.Param(valid.boolean, False)
    secondary_perils = valid.Param(valid.namelist, [])
    sec_peril_params = valid.Param(valid.dictionary, {})
    secondary_simulations = valid.Param(valid.dictionary, {})
    sensitivity_analysis = valid.Param(valid.dictionary, {})
    ses_per_logic_tree_path = valid.Param(
        valid.compose(valid.nonzero, valid.positiveint), 1)
    ses_seed = valid.Param(valid.positiveint, 42)
    shakemap_id = valid.Param(valid.nice_string, None)
    shift_hypo = valid.Param(valid.boolean, False)
    site_effects = valid.Param(valid.boolean, False)  # shakemap amplification
    sites = valid.Param(valid.NoneOr(valid.coordinates), None)
    sites_slice = valid.Param(valid.simple_slice, (None, None))
    soil_intensities = valid.Param(valid.positivefloats, None)
    source_id = valid.Param(valid.namelist, [])
    spatial_correlation = valid.Param(valid.Choice('yes', 'no', 'full'), 'yes')
    specific_assets = valid.Param(valid.namelist, [])
    split_sources = valid.Param(valid.boolean, True)
    ebrisk_maxsize = valid.Param(valid.positivefloat, 2E10)  # used in ebrisk
    # NB: you cannot increase too much min_weight otherwise too few tasks will
    # be generated in cases like Ecuador inside full South America
    min_weight = valid.Param(valid.positiveint, 200)  # used in classical
    max_weight = valid.Param(valid.positiveint, 1E6)  # used in classical
    time_event = valid.Param(str, None)
    truncation_level = valid.Param(valid.NoneOr(valid.positivefloat), None)
    uniform_hazard_spectra = valid.Param(valid.boolean, False)
    vs30_tolerance = valid.Param(valid.positiveint, 0)
    width_of_mfd_bin = valid.Param(valid.positivefloat, None)

    @property
    def risk_files(self):
        try:
            return self._risk_files
        except AttributeError:
            self._risk_files = get_risk_files(self.inputs)
            return self._risk_files

    @property
    def input_dir(self):
        """
        :returns: absolute path to where the job.ini is
        """
        return os.path.abspath(os.path.dirname(self.inputs['job_ini']))

    def get_reqv(self):
        """
        :returns: an instance of class:`RjbEquivalent` if reqv_hdf5 is set
        """
        if 'reqv' not in self.inputs:
            return
        return {key: valid.RjbEquivalent(value)
                for key, value in self.inputs['reqv'].items()}

    def __init__(self, **names_vals):
        if '_job_id' in names_vals:  # called from engine
            del names_vals['_job_id']

        # support legacy names
        for name in list(names_vals):
            if name == 'quantile_hazard_curves':
                names_vals['quantiles'] = names_vals.pop(name)
            elif name == 'mean_hazard_curves':
                names_vals['mean'] = names_vals.pop(name)
            elif name == 'max':
                names_vals['max'] = names_vals.pop(name)
        super().__init__(**names_vals)
        if 'job_ini' not in self.inputs:
            self.inputs['job_ini'] = '<in-memory>'
        job_ini = self.inputs['job_ini']
        if 'calculation_mode' not in names_vals:
            raise InvalidFile('Missing calculation_mode in %s' % job_ini)
        if 'region_constraint' in names_vals:
            if 'region' in names_vals:
                raise InvalidFile('You cannot have both region and '
                                  'region_constraint in %s' % job_ini)
            logging.warning(
                'region_constraint is obsolete, use region instead')
            self.region = valid.wkt_polygon(
                names_vals.pop('region_constraint'))
        self.risk_investigation_time = (
            self.risk_investigation_time or self.investigation_time)
        self.collapse_level = int(self.collapse_level)
        if ('intensity_measure_types_and_levels' in names_vals and
                'intensity_measure_types' in names_vals):
            logging.warning('Ignoring intensity_measure_types since '
                            'intensity_measure_types_and_levels is set')
        if 'iml_disagg' in names_vals:
            self.iml_disagg.pop('default')
            # normalize things like SA(0.10) -> SA(0.1)
            self.iml_disagg = {str(from_string(imt)): [iml]
                               for imt, iml in self.iml_disagg.items()}
            self.hazard_imtls = self.iml_disagg
            if 'intensity_measure_types_and_levels' in names_vals:
                raise InvalidFile(
                    'Please remove the intensity_measure_types_and_levels '
                    'from %s: they will be inferred from the iml_disagg '
                    'dictionary' % job_ini)
        elif 'intensity_measure_types_and_levels' in names_vals:
            self.hazard_imtls = self.intensity_measure_types_and_levels
            delattr(self, 'intensity_measure_types_and_levels')
            lens = set(map(len, self.hazard_imtls.values()))
            if len(lens) > 1:
                dic = {imt: len(ls) for imt, ls in self.hazard_imtls.items()}
                raise ValueError(
                    'Each IMT must have the same number of levels, instead '
                    'you have %s' % dic)
        elif 'intensity_measure_types' in names_vals:
            self.hazard_imtls = dict.fromkeys(
                self.intensity_measure_types, [0])
            delattr(self, 'intensity_measure_types')
        if ('ps_grid_spacing' in names_vals and
                'pointsource_distance' not in names_vals):
            raise InvalidFile('%s: ps_grid_spacing requires setting a '
                              'pointsource_distance!' % self.inputs['job_ini'])

        self._risk_files = get_risk_files(self.inputs)

        if self.hazard_precomputed() and self.job_type == 'risk':
            self.check_missing('site_model', 'debug')
            self.check_missing('gsim_logic_tree', 'debug')
            self.check_missing('source_model_logic_tree', 'debug')

        # check investigation_time
        if (self.investigation_time and
                self.calculation_mode.startswith('scenario')):
            raise ValueError('%s: there cannot be investigation_time in %s'
                             % (self.inputs['job_ini'], self.calculation_mode))

        # check the gsim_logic_tree
        if self.inputs.get('gsim_logic_tree'):
            if self.gsim != '[FromFile]':
                raise InvalidFile('%s: if `gsim_logic_tree_file` is set, there'
                                  ' must be no `gsim` key' % job_ini)
            path = os.path.join(
                self.base_path, self.inputs['gsim_logic_tree'])
            gsim_lt = logictree.GsimLogicTree(path, ['*'])

            # check the IMTs vs the GSIMs
            self._trts = set(gsim_lt.values)
            for gsims in gsim_lt.values.values():
                self.check_gsims(gsims)
        elif self.gsim is not None:
            self.check_gsims([valid.gsim(self.gsim, self.base_path)])

        # check inputs
        unknown = set(self.inputs) - self.KNOWN_INPUTS
        if unknown:
            raise ValueError('Unknown key %s_file in %s' %
                             (unknown.pop(), self.inputs['job_ini']))

        # checks for disaggregation
        if self.calculation_mode == 'disaggregation':
            if not self.poes_disagg and self.poes:
                self.poes_disagg = self.poes
            elif not self.poes and self.poes_disagg:
                self.poes = self.poes_disagg
            elif self.poes != self.poes_disagg:
                raise InvalidFile(
                    'poes_disagg != poes: %s!=%s in %s' %
                    (self.poes_disagg, self.poes, self.inputs['job_ini']))
            if not self.poes_disagg and not self.iml_disagg:
                raise InvalidFile('poes_disagg or iml_disagg must be set '
                                  'in %(job_ini)s' % self.inputs)
            elif self.poes_disagg and self.iml_disagg:
                raise InvalidFile(
                    '%s: iml_disagg and poes_disagg cannot be set '
                    'at the same time' % job_ini)
            for k in ('mag_bin_width', 'distance_bin_width',
                      'coordinate_bin_width', 'num_epsilon_bins'):
                if k not in vars(self):
                    raise InvalidFile('%s must be set in %s' % (k, job_ini))
            if self.disagg_outputs and not any(
                    'Eps' in out for out in self.disagg_outputs):
                self.num_epsilon_bins = 1
            if (self.rlz_index is not None
                    and self.num_rlzs_disagg is not None):
                raise InvalidFile('%s: you cannot set rlzs_index and '
                                  'num_rlzs_disagg at the same time' % job_ini)

        # checks for classical_damage
        if self.calculation_mode == 'classical_damage':
            if self.conditional_loss_poes:
                raise InvalidFile(
                    '%s: conditional_loss_poes are not defined '
                    'for classical_damage calculations' % job_ini)

        # checks for event_based_risk
        if (self.calculation_mode == 'event_based_risk' and
                self.asset_correlation not in (0, 1)):
            raise ValueError('asset_correlation != {0, 1} is no longer'
                             ' supported in %s' % job_ini)
        elif (self.calculation_mode == 'event_based_risk' and
              not self.ground_motion_fields):
            raise ValueError('ground_motion_fields must be set to true in %s'
                             % job_ini)

        # checks for ebrisk
        if self.calculation_mode == 'ebrisk':
            if self.risk_investigation_time is None:
                raise InvalidFile('Please set the risk_investigation_time in'
                                  ' %s' % job_ini)

        # check for GMFs from file
        if (self.inputs.get('gmfs', '').endswith('.csv')
                and 'sites' not in self.inputs and self.sites is None):
            raise InvalidFile('%s: You forgot sites|sites_csv'
                              % job_ini)
        elif self.inputs.get('gmfs', '').endswith('.xml'):
            raise InvalidFile('%s: GMFs in XML are not supported anymore'
                              % job_ini)

        # checks for event_based
        if 'event_based' in self.calculation_mode:
            if self.ps_grid_spacing:
                logging.warning('ps_grid_spacing is ignored in event_based '
                                'calculations"')

            if self.ses_per_logic_tree_path >= TWO32:
                raise ValueError('ses_per_logic_tree_path too big: %d' %
                                 self.ses_per_logic_tree_path)
            if self.number_of_logic_tree_samples >= TWO16:
                raise ValueError('number_of_logic_tree_samples too big: %d' %
                                 self.number_of_logic_tree_samples)

        # check grid + sites
        if self.region_grid_spacing and ('sites' in self.inputs or self.sites):
            raise ValueError('You are specifying grid and sites at the same '
                             'time: which one do you want?')

        # check for amplification
        if ('amplification' in self.inputs and self.imtls and
                self.calculation_mode in ['classical', 'classical_risk',
                                          'disaggregation']):
            check_same_levels(self.imtls)

        if ('amplification' in self.inputs and
            self.amplification_method == 'convolution' and
            not self.soil_intensities):
                raise InvalidFile('%s: The soil_intensities must be defined'
                     % job_ini)

    def check_gsims(self, gsims):
        """
        :param gsims: a sequence of GSIM instances
        """
        imts = set(from_string(imt).name for imt in self.imtls)
        for gsim in gsims:
            if hasattr(gsim, 'weight'):  # disable the check
                continue
            restrict_imts = gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES
            if restrict_imts:
                names = set(cls.__name__ for cls in restrict_imts)
                invalid_imts = ', '.join(imts - names)
                if invalid_imts:
                    raise ValueError(
                        'The IMT %s is not accepted by the GSIM %s' %
                        (invalid_imts, gsim))

            if (self.hazard_calculation_id is None
                    and 'site_model' not in self.inputs):
                # look at the required sites parameters: they must have
                # a valid value; the other parameters can keep a NaN
                # value since they are not used by the calculator
                for param in gsim.REQUIRES_SITES_PARAMETERS:
                    if param in ('lon', 'lat'):  # no check
                        continue
                    param_name = self.siteparam[param]
                    param_value = getattr(self, param_name)
                    if (isinstance(param_value, float) and
                            numpy.isnan(param_value)):
                        raise ValueError(
                            'Please set a value for %r, this is required by '
                            'the GSIM %s' % (param_name, gsim))

    @property
    def tses(self):
        """
        Return the total time as investigation_time * ses_per_logic_tree_path *
        (number_of_logic_tree_samples or 1)
        """
        return (self.investigation_time * self.ses_per_logic_tree_path *
                (self.number_of_logic_tree_samples or 1))

    @property
    def ses_ratio(self):
        """
        The ratio

        risk_investigation_time / investigation_time / ses_per_logic_tree_path
        """
        if self.investigation_time is None:
            raise ValueError('Missing investigation_time in the .ini file')
        return (self.risk_investigation_time or self.investigation_time) / (
            self.investigation_time * self.ses_per_logic_tree_path)

    @property
    def imtls(self):
        """
        Returns a DictArray with the risk intensity measure types and
        levels, if given, or the hazard ones.
        """
        imtls = self.hazard_imtls or self.risk_imtls
        return DictArray(imtls) if imtls else {}

    @property
    def all_cost_types(self):
        """
        Return the cost types of the computation (including `occupants`
        if it is there) in order.
        """
        # rt has the form 'vulnerability/structural', 'fragility/...', ...
        costtypes = set(rt.rsplit('/')[1] for rt in self.risk_files)
        if not costtypes and self.hazard_calculation_id:
            with util.read(self.hazard_calculation_id) as ds:
                parent = ds['oqparam']
            self._risk_files = get_risk_files(parent.inputs)
            costtypes = set(rt.rsplit('/')[1] for rt in self.risk_files)
        return sorted(costtypes)

    @property
    def min_iml(self):
        """
        :returns: a dictionary of intensities, one per IMT
        """
        mini = self.minimum_intensity
        if mini:
            for imt in self.imtls:
                try:
                    mini[imt] = calc.filters.getdefault(mini, imt)
                except KeyError:
                    raise ValueError(
                        'The parameter `minimum_intensity` in the job.ini '
                        'file is missing the IMT %r' % imt)
        if 'default' in mini:
            del mini['default']
        return numpy.array([mini.get(imt) or 1E-10 for imt in self.imtls])

    def levels_per_imt(self):
        """
        :returns: the number of levels per IMT (a.ka. L1)
        """
        return self.imtls.size // len(self.imtls)

    def set_risk_imts(self, risklist):
        """
        :param risklist:
            a list of risk functions with attributes .id, .loss_type, .kind

        Set the attribute risk_imtls.
        """
        imtls = AccumDict(accum=[])  # imt -> imls
        for i, rf in enumerate(risklist):
            if not hasattr(rf, 'imt') or rf.kind.endswith('_retrofitted'):
                # for consequence or retrofitted
                continue
            if hasattr(rf, 'build'):  # FragilityFunctionList
                rf = rf.build(risklist.limit_states,
                              self.continuous_fragility_discretization,
                              self.steps_per_interval)
                risklist[i] = rf
            from_string(rf.imt)  # make sure it is a valid IMT
            imtls[rf.imt].extend(iml for iml in rf.imls if iml > 0)
        suggested = ['\nintensity_measure_types_and_levels = {']
        risk_imtls = self.risk_imtls.copy()
        for imt, imls in imtls.items():
            risk_imtls[imt] = list(valid.logscale(min(imls), max(imls), 20))
            suggested.append('  %r: logscale(%s, %s, 20),' %
                             (imt, min(imls), max(imls)))
        suggested[-1] += '}'
        self.risk_imtls = {imt: [min(ls)] for imt, ls in risk_imtls.items()}
        if self.uniform_hazard_spectra:
            self.check_uniform_hazard_spectra()
        if not self.hazard_imtls:
            if (self.calculation_mode.startswith('classical') or
                    self.hazard_curves_from_gmfs):
                raise InvalidFile('%s: %s' % (
                    self.inputs['job_ini'], 'You must provide the '
                    'intensity measure levels explicitly. Suggestion:' +
                    '\n  '.join(suggested)))
        if (len(self.imtls) == 0 and 'event_based' in self.calculation_mode and
                'gmfs' not in self.inputs and not self.hazard_calculation_id
                and self.ground_motion_fields):
            raise ValueError('Please define intensity_measure_types in %s' %
                             self.inputs['job_ini'])

    def get_primary_imtls(self):
        """
        :returns: IMTs and levels which are not secondary
        """
        sec_imts = set(self.get_sec_imts())
        return {imt: imls for imt, imls in self.imtls.items()
                if imt not in sec_imts}

    def hmap_dt(self):  # used for CSV export
        """
        :returns: a composite dtype (imt, poe)
        """
        return numpy.dtype([('%s-%s' % (imt, poe), F32)
                            for imt in self.imtls for poe in self.poes])

    def uhs_dt(self):  # used for CSV and NPZ export
        """
        :returns: a composity dtype (poe, imt)
        """
        imts_dt = numpy.dtype([(imt, F32) for imt in self.imtls
                               if imt.startswith(('PGA', 'SA'))])
        return numpy.dtype([(str(poe), imts_dt) for poe in self.poes])

    def imt_periods(self):
        """
        :returns: the IMTs with a period, as objects
        """
        imts = []
        for im in self.imtls:
            imt = from_string(im)
            if hasattr(imt, 'period'):
                imts.append(imt)
        return imts

    def imt_dt(self, dtype=F64):
        """
        :returns: a numpy dtype {imt: float}
        """
        return numpy.dtype([(imt, dtype) for imt in self.imtls])

    @property
    def lti(self):
        """
        Dictionary extended_loss_type -> extended_loss_type index
        """
        return {lt: i for i, (lt, dt) in enumerate(self.loss_dt_list())}

    @property
    def loss_names(self):
        """
        Loss types plus insured types, if any
        """
        names = []
        for lt, _ in self.loss_dt_list():
            names.append(lt)
        for name in self.inputs.get('insurance', []):
            names.append(lt + '_ins')
        return names

    def loss_dt(self, dtype=F32):
        """
        :returns: a composite dtype based on the loss types including occupants
        """
        return numpy.dtype(self.loss_dt_list(dtype))

    def loss_dt_list(self, dtype=F32):
        """
        :returns: a data type list [(loss_name, dtype), ...]
        """
        loss_types = self.all_cost_types
        dts = [(str(lt), dtype) for lt in loss_types]
        return dts

    def loss_maps_dt(self, dtype=F32):
        """
        Return a composite data type for loss maps
        """
        ltypes = self.loss_dt(dtype).names
        lst = [('poe-%s' % poe, dtype) for poe in self.conditional_loss_poes]
        return numpy.dtype([(lt, lst) for lt in ltypes])

    def gmf_data_dt(self):
        """
        :returns: a composite data type for the GMFs
        """
        lst = [('sid', U32), ('eid', U32)]
        for m, imt in enumerate(self.get_primary_imtls()):
            lst.append((f'gmv_{m}', F32))
        for out in self.get_sec_imts():
            lst.append((out, F32))
        return numpy.dtype(lst)

    def all_imts(self):
        """
        :returns: gmv_0, ... gmv_M, sec_imt...
        """
        lst = []
        for m, imt in enumerate(self.get_primary_imtls()):
            lst.append(f'gmv_{m}')
        for out in self.get_sec_imts():
            lst.append(out)
        return lst

    def get_sec_perils(self):
        """
        :returns: a list of secondary perils
        """
        return SecondaryPeril.instantiate(self.secondary_perils,
                                          self.sec_peril_params)

    def get_sec_imts(self):
        """
        :returns: a list of secondary outputs
        """
        outs = []
        for sp in self.get_sec_perils():
            outs.extend(sp.outputs)
        return outs

    def no_imls(self):
        """
        Return True if there are no intensity measure levels
        """
        return sum(sum(imls) for imls in self.imtls.values()) == 0

    @property
    def correl_model(self):
        """
        Return a correlation object. See :mod:`openquake.hazardlib.correlation`
        for more info.
        """
        correl_name = self.ground_motion_correlation_model
        if correl_name is None:  # no correlation model
            return
        correl_model_cls = getattr(
            correlation, '%sCorrelationModel' % correl_name)
        return correl_model_cls(**self.ground_motion_correlation_params)

    def get_kinds(self, kind, R):
        """
        Yield 'rlz-000', 'rlz-001', ...', 'mean', 'quantile-0.1', ...
        """
        stats = self.hazard_stats()
        if kind == 'stats':
            yield from stats
            return
        elif kind == 'rlzs':
            for r in range(R):
                yield 'rlz-%d' % r
            return
        elif kind:
            yield kind
            return
        # default: yield stats (and realizations if required)
        if R > 1 and self.individual_curves or not stats:
            for r in range(R):
                yield 'rlz-%03d' % r
        yield from stats

    def hazard_stats(self):
        """
        Return a dictionary stat_name -> stat_func
        """
        names = []  # name of statistical functions
        funcs = []  # statistical functions of kind func(values, weights)
        if self.mean:
            names.append('mean')
            funcs.append(stats.mean_curve)
        if self.std:
            names.append('std')
            funcs.append(stats.std_curve)
        for q in self.quantiles:
            names.append('quantile-%s' % q)
            funcs.append(functools.partial(stats.quantile_curve, q))
        if self.max:
            names.append('max')
            funcs.append(stats.max_curve)
        return dict(zip(names, funcs))

    @property
    def job_type(self):
        """
        'hazard' or 'risk'
        """
        return 'risk' if ('risk' in self.calculation_mode or
                          'damage' in self.calculation_mode or
                          'bcr' in self.calculation_mode) else 'hazard'

    def is_event_based(self):
        """
        The calculation mode is event_based, event_based_risk or ebrisk
        """
        return (self.calculation_mode in
                'event_based_risk ebrisk event_based_damage ucerf_hazard')

    def is_ucerf(self):
        """
        :returns: True for UCERF calculations, False otherwise
        """
        return 'source_model' in self.inputs

    def is_valid_shakemap(self):
        """
        hazard_calculation_id must be set if shakemap_id is set
        """
        return self.hazard_calculation_id if self.shakemap_id else True

    def is_valid_truncation_level(self):
        """
        In presence of a correlation model the truncation level must be nonzero
        """
        if self.ground_motion_correlation_model:
            return self.truncation_level != 0
        else:
            return True

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
        one of sites, sites_csv, hazard_curves_csv, region is set.
        You did set more than one, or nothing.
        """
        if 'hazard_curves' in self.inputs and (
                self.sites is not None or 'sites' in self.inputs
                or 'site_model' in self.inputs):
            return False
        has_sites = (self.sites is not None or 'sites' in self.inputs
                     or 'site_model' in self.inputs)
        if not has_sites and not self.ground_motion_fields:
            # when generating only the ruptures you do not need the sites
            return True
        if ('risk' in self.calculation_mode or
                'damage' in self.calculation_mode or
                'bcr' in self.calculation_mode):
            return True  # no check on the sites for risk
        flags = dict(
            sites=bool(self.sites),
            sites_csv=self.inputs.get('sites', 0),
            hazard_curves_csv=self.inputs.get('hazard_curves', 0),
            gmfs_csv=self.inputs.get('gmfs', 0),
            region=bool(self.region and self.region_grid_spacing))
        # NB: below we check that all the flags
        # are mutually exclusive
        return sum(bool(v) for v in flags.values()) == 1 or self.inputs.get(
            'exposure') or self.inputs.get('site_model')

    def is_valid_poes(self):
        """
        When computing hazard maps and/or uniform hazard spectra,
        the poes list must be non-empty.
        """
        if self.hazard_maps or self.uniform_hazard_spectra:
            return bool(self.poes)
        else:
            return True

    def is_valid_maximum_distance(self):
        """
        Invalid maximum_distance={maximum_distance}: {error}
        """
        if 'gsim_logic_tree' not in self.inputs:
            return True  # don't apply validation
        gsim_lt = self.inputs['gsim_logic_tree']
        trts = set(self.maximum_distance)
        unknown = ', '.join(trts - self._trts - {'default'})
        if unknown:
            self.error = ('setting the maximum_distance for %s which is '
                          'not in %s' % (unknown, gsim_lt))
            return False
        for trt, val in self.maximum_distance.items():
            if trt not in self._trts and trt != 'default':
                self.error = 'tectonic region %r not in %s' % (trt, gsim_lt)
                return False
        if 'default' not in trts and trts < self._trts:
            missing = ', '.join(self._trts - trts)
            self.error = 'missing distance for %s and no default' % missing
            return False
        return True

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
        if self.risk_files:  # IMTLs extracted from the risk files
            return (self.intensity_measure_types == '' and
                    self.intensity_measure_types_and_levels is None)
        elif not self.hazard_imtls and not hasattr(self, 'risk_imtls'):
            return False
        return True

    def is_valid_intensity_measure_levels(self):
        """
        In order to compute hazard curves, `intensity_measure_types_and_levels`
        must be set or extracted from the risk models.
        """
        invalid = self.no_imls() and not self.risk_files and (
            self.hazard_curves_from_gmfs or self.calculation_mode in
            ('classical', 'disaggregation'))
        return not invalid

    def is_valid_soil_intensities(self):
        """
        soil_intensities can be set only if amplification_method=convolution
        """
        if self.amplification_method == 'convolution':
            return len(self.soil_intensities) > 1
        else:
            return self.soil_intensities is None

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

    def is_valid_aggregate_by(self):
        """
        At the moment only `aggregate_by=id` or `aggregate_by=site_id`
        are accepted
        """
        if 'id' in self.aggregate_by and len(self.aggregate_by) > 1:
            return False
        elif 'site_id' in self.aggregate_by and len(self.aggregate_by) > 1:
            return False
        return True

    def is_valid_export_dir(self):
        """
        export_dir={export_dir} must refer to a directory,
        and the user must have the permission to write on it.
        """
        if self.export_dir and not os.path.isabs(self.export_dir):
            self.export_dir = os.path.normpath(
                os.path.join(self.input_dir, self.export_dir))
        if not self.export_dir:
            self.export_dir = os.path.expanduser('~')  # home directory
            logging.warning('export_dir not specified. Using export_dir=%s'
                            % self.export_dir)
            return True
        if not os.path.exists(self.export_dir):
            try:
                os.makedirs(self.export_dir)
            except PermissionError:
                return False
            return True
        return os.path.isdir(self.export_dir) and os.access(
            self.export_dir, os.W_OK)

    def is_valid_complex_fault_mesh_spacing(self):
        """
        The `complex_fault_mesh_spacing` parameter can be None only if
        `rupture_mesh_spacing` is set. In that case it is identified with it.
        """
        rms = getattr(self, 'rupture_mesh_spacing', None)
        if rms and not getattr(self, 'complex_fault_mesh_spacing', None):
            self.complex_fault_mesh_spacing = self.rupture_mesh_spacing
        return True

    def check_uniform_hazard_spectra(self):
        ok_imts = [imt for imt in self.imtls if imt == 'PGA' or
                   imt.startswith('SA')]
        if not ok_imts:
            raise ValueError('The `uniform_hazard_spectra` can be True only '
                             'if the IMT set contains SA(...) or PGA, got %s'
                             % list(self.imtls))
        elif len(ok_imts) == 1:
            logging.warning(
                'There is a single IMT, the uniform_hazard_spectra plot will '
                'contain a single point')

    def check_source_model(self):
        if ('hazard_curves' in self.inputs or 'gmfs' in self.inputs or
                'multi_peril' in self.inputs or 'rupture_model' in self.inputs
                or 'scenario' in self.calculation_mode):
            return
        if ('source_model_logic_tree' not in self.inputs and
                self.inputs['job_ini'] != '<in-memory>' and
                not self.hazard_calculation_id):
            raise ValueError('Missing source_model_logic_tree in %s '
                             'or missing --hc option' %
                             self.inputs.get('job_ini', 'job_ini'))

    def check_missing(self, param, action):
        """
        Make sure the given parameter is missing in the job.ini file
        """
        assert action in ('debug', 'info', 'warn', 'error'), action
        if self.inputs.get(param):
            msg = '%s_file in %s is ignored in %s' % (
                param, self.inputs['job_ini'], self.calculation_mode)
            if action == 'error':
                raise InvalidFile(msg)
            else:
                getattr(logging, action)(msg)

    def hazard_precomputed(self):
        """
        :returns: True if the hazard is precomputed
        """
        if 'gmfs' in self.inputs or 'hazard_curves' in self.inputs:
            return True
        return self.hazard_calculation_id

    @classmethod
    def docs(cls):
        """
        :returns: a dictionary parameter name -> parameter documentation
        """
        dic = {}
        lst = re.split(r'\n([\w_]+):\n', __doc__)
        for name, doc in zip(lst[1::2], lst[2::2]):
            name = name.split()[-1]
            dic[name] = doc
        return dic
