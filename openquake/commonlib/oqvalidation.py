# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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

import os
import re
import ast
import json
import inspect
import logging
import functools
import collections
import multiprocessing
import numpy
import itertools

from openquake.baselib import __version__, hdf5, python3compat, config
from openquake.baselib.general import DictArray, AccumDict
from openquake.hazardlib.imt import from_string, sort_by_imt
from openquake.hazardlib import shakemap
from openquake.hazardlib import correlation, cross_correlation, stats, calc
from openquake.hazardlib import valid, InvalidFile, site
from openquake.sep.classes import SecondaryPeril
from openquake.commonlib import logictree
from openquake.risklib import asset, scientific
from openquake.risklib.riskmodels import get_risk_files

__doc__ = """\
Full list of configuration parameters
=====================================

Engine Version: %s

Some parameters have a default that it is used when the parameter is
not specified in the job.ini file. Some other parameters have no default,
which means that not specifying them will raise an error when running
a calculation for which they are required.

override_vs30:
  Optional Vs30 parameter to override the site model Vs30
  Example: *override_vs30 = 800*
  Default: None

aggregate_by:
  Used to compute aggregate losses and aggregate loss curves in risk
  calculations. Takes in input one or more exposure tags.
  Example: *aggregate_by = region, taxonomy*.
  Default: empty list

reaggregate_by:
  Used to perform additional aggregations in risk calculations. Takes in
  input a proper subset of the tags in the aggregate_by option.
  Example: *reaggregate_by = region*.
  Default: empty list

amplification_method:
  Used in classical PSHA calculations to amplify the hazard curves with
  the convolution or kernel method.
  Example: *amplification_method = kernel*.
  Default: "convolution"

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

gmf_max_gb:
  If the size (in GB) of the GMFs is below this value, then compute avg_gmf
  Example: *gmf_max_gb = 1.*
  Default: 0.1

avg_losses:
  Used in risk calculations to compute average losses.
  Example: *avg_losses=false*.
  Default: True

base_path:
  INTERNAL

cachedir:
  INTERNAL

cache_distances:
  Useful in UCERF calculations.
  Example: *cache_distances = true*.
  Default: False

calculation_mode:
  One of classical, disaggregation, event_based, scenario, scenario_risk,
  scenario_damage, event_based_risk, classical_risk, classical_bcr.
  Example: *calculation_mode=classical*
  Default: no default

collapse_gsim_logic_tree:
  INTERNAL

collapse_level:
  INTERNAL

collect_rlzs:
  Collect all realizations into a single effective realization. If not given
  it is true for sampling and false for full enumeration.
  Example: *collect_rlzs=true*.
  Default: None

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

cholesky_limit:
  When generating the GMFs from a ShakeMap the engine needs to perform a
  Cholesky decomposition of a matrix of size (M x N)^2, being M the number
  of intensity measure types and N the number of sites. The decomposition
  can become ultra-slow, run out of memory, or produce bogus negative
  eigenvalues, therefore there is a limit on the maximum size of M x N.
  Example: *cholesky_limit = 1000*.
  Default: 10,000

continuous_fragility_discretization:
  Used when discretizing continuuos fragility functions.
  Example: *continuous_fragility_discretization = 10*.
  Default: 20

coordinate_bin_width:
  Used in disaggregation calculations.
  Example: *coordinate_bin_width = 1.0*.
  Default: 100 degrees, meaning don't disaggregate by lon, lat

cross_correlation:
  When used in Conditional Spectrum calculation is the name of a cross
  correlation class (i.e. "BakerJayaram2008").
  When used in ShakeMap calculations the valid choices are "yes", "no" "full",
  same as for *spatial_correlation*.
  Example: *cross_correlation = no*.
  Default: "yes"

description:
  A string describing the calculation.
  Example: *description = Test calculation*.
  Default: "no description"

disagg_bin_edges:
  A dictionary where the keys can be: mag, dist, lon, lat, eps and the
  values are lists of floats indicating the edges of the bins used to
  perform the disaggregation.
  Example: *disagg_bin_edges = {'mag': [5.0, 5.5, 6.0, 6.5]}*.
  Default: empty dictionary

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

discrete_damage_distribution:
  Make sure the damage distribution contain only integers (require the "number"
  field in the exposure to be integer).
  Example: *discrete_damage_distribution = true*
  Default: False

distance_bin_width:
  In km, used in disaggregation calculations to specify the distance bins.
  Example: *distance_bin_width = 20*.
  Default: no default

ebrisk_maxsize:
  INTERNAL

epsilon_star:
  A boolean controlling the typology of disaggregation output to be provided.
  When True disaggregation is perfomed in terms of epsilon* rather then
  epsilon (see Bazzurro and Cornell, 1999)
  Example: *epsilon_star = true*
  Default: False

extreme_gmv:
  A scalar on an IMT-keyed dictionary specifying when a ground motion value is
  extreme and the engine has to treat is specially.
  Example: *extreme_gmv = 5.0*
  Default: {'default': numpy.inf} i.e. no values are extreme

floating_x_step:
  Float, used in rupture generation for kite faults. indicates the fraction
  of fault length used to float ruptures along strike by the given float
  (i.e. "0.5" floats the ruptures at half the rupture length). Uniform
  distribution of the ruptures is maintained, such that if the mesh spacing
  and rupture dimensions prohibit the defined overlap fraction, the fraction
  is increased until uniform distribution is achieved. The minimum possible
  value depends on the rupture dimensions and the mesh spacing.
  If 0, standard rupture floating is used along-strike (i.e. no mesh nodes
  are skipped).
  Example: *floating_x_step = 0.5*
  Default: 0

floating_y_step:
  Float, used in rupture generation for kite faults. indicates the fraction
  of fault width used to float ruptures down dip. (i.e. "0.5" floats that
  half the rupture length). Uniform distribution of the ruptures
  is maintained, such that if the mesh spacing and rupture dimensions
  prohibit the defined overlap fraction, the fraction is increased until
  uniform distribution is achieved. The minimum possible value depends on
  the rupture dimensions and the mesh spacing.
  If 0, standard rupture floating is used along-strike (i.e. no mesh nodes
  on the rupture dimensions and the mesh spacing.
  Example: *floating_y_step = 0.5*
  Default: 0

ignore_encoding_errors:
  If set, skip characters with non-UTF8 encoding
  Example: *ignore_encoding_errors = true*.
  Default: False

ignore_master_seed:
  If set, estimate analytically the uncertainty on the losses due to the
  uncertainty on the vulnerability functions.
  Example: *ignore_master_seed = vulnerability*.
  Default: None

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

hazard_curves:
   Used to disable the calculation of hazard curves when there are
   too many realizations.
   Example: *hazard_curves = false*
   Default: True

hazard_curves_from_gmfs:
  Used in scenario/event based calculations. If set, generates hazard curves
  from the ground motion fields.
  Example: *hazard_curves_from_gmfs = true*.
  Default: False

hazard_maps:
  Set it to true to export the hazard maps.
  Example: *hazard_maps = true*.
  Default: False

horiz_comp_to_geom_mean:
  Apply the correction to the geometric mean when possible,
  depending on the GMPE and the Intensity Measure Component
  Example: *horiz_comp_to_geom_mean = true*.
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

imt_ref:
  Reference intensity measure type used to compute the conditional spectrum.
  The imt_ref must belong to the list of IMTs of the calculation.
  Example: *imt_ref = SA(0.15)*.
  Default: empty string

individual_rlzs:
  When set, store the individual hazard curves and/or individual risk curves
  for each realization.
  Example: *individual_rlzs = true*.
  Default: False

individual_curves:
  Legacy name for `individual_rlzs`, it should not be used.
  Example: *individual_curves = true*.
  Default: False

infer_occur_rates:
   If set infer the occurrence rates from the first probs_occur in
   nonparametric sources.
   Example: *infer_occur_rates = true*
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

limit_states:
   Limit states used in damage calculations.
   Example: *limit_states = moderate, complete*
   Default: no default

lrem_steps_per_interval:
  Used in the vulnerability functions.
  Example: *lrem_steps_per_interval  = 1*.
  Default: 0

mag_bin_width:
  Width of the magnitude bin used in disaggregation calculations.
  Example: *mag_bin_width = 0.5*.
  Default: 1.

master_seed:
  Seed used to control the generation of the epsilons, relevant for risk
  calculations with vulnerability functions with nonzero coefficients of
  variation.
  Example: *master_seed = 1234*.
  Default: 123456789

max:
  Compute the maximum across realizations. Akin to mean and quantiles.
  Example: *max = true*.
  Default: False

max_aggregations:
  Maximum number of aggregation keys.
  Example: *max_aggregations = 200_000*
  Default: 100_000

max_data_transfer:
  INTERNAL. Restrict the maximum data transfer in disaggregation calculations.

max_gmvs_per_task:
  Maximum number of rows of the gmf_data table per task.
  Example: *max_gmvs_per_task = 100_000*
  Default: 1_000_0000

max_potential_gmfs:
  Restrict the product *num_sites * num_events*.
  Example: *max_potential_gmfs = 1E9*.
  Default: 2E11

max_potential_paths:
  Restrict the maximum number of realizations.
  Example: *max_potential_paths = 200*.
  Default: 15000

max_sites_disagg:
  Maximum number of sites for which to store rupture information.
  In disaggregation calculations with many sites you may be forced to raise
  *max_sites_disagg*, that must be greater or equal to the number of sites.
  Example: *max_sites_disagg = 100*
  Default: 10

pmap_max_mb:
   Control the size of the returned pmaps in classical calculations.
   The default is 50 MB; you can reduce it if zmq cannot keep up.
   Example: *pmap_max_mb = 25*
   Default: 50

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

minimum_asset_loss:
  Used in risk calculations. If set, losses smaller than the
  *minimum_asset_loss* are consider zeros.
  Example: *minimum_asset_loss = {"structural": 1000}*.
  Default: empty dictionary

minimum_distance:
   If set, distances below the minimum are rounded up.
   Example: *minimum_distance = 5*
   Default: 0

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
  Default: 1

num_rlzs_disagg:
  Used in disaggregation calculation to specify how many outputs will be
  generated. `0` means all realizations, `n` means the n closest to the mean
  hazard curve.
  Example: *num_rlzs_disagg=1*.
  Default: 0

number_of_ground_motion_fields:
  Used in scenario calculations to specify how many random ground motion
  fields to generate.
  Example: *number_of_ground_motion_fields = 100*.
  Default: no default

number_of_logic_tree_samples:
  Used to specify the number of realizations to generate when using logic tree
  sampling. If zero, full enumeration is performed.
  Example: *number_of_logic_tree_samples = 0*.
  Default: 0

oversampling:
  When equal to "forbid" raise an error if tot_samples > num_paths in classical
  calculations; when equal to "tolerate" do not raise the error (the default);
  when equal to "reduce_rlzs" reduce the realizations to the unique paths with
  weights num_samples/tot_samples
  Example: *oversampling = reduce_rlzs*
  Default: tolerate

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
  Default: {'default': 1000}

postproc_func:
  Specify a postprocessing function in calculators/postproc.
  Example: *postproc_func = compute_mrd.main*
  Default: '' (no postprocessing)

postproc_args:
  Specify the arguments to be passed to the postprocessing function
  Example: *postproc_args = {'imt': 'PGA'}*
  Default: {} (no arguments)

prefer_global_site_params:
  INTERNAL. Automatically set by the engine.

ps_grid_spacing:
  Used in classical calculations to grid the point sources. Requires the
  *pointsource_distance* to be set too.
  Example: *ps_grid_spacing = 50*.
  Default: 0, meaning no grid

quantiles:
  List of probabilities used to compute the quantiles across realizations.
  Example: quantiles = 0.15 0.50 0.85
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

reference_vs30_type:
  Used when there is no site model to specify a global vs30 type.
  The choices are "inferred" or "measured"
  Example: *reference_vs30_type = measured"*.
  Default: "inferred"

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

reqv_ignore_sources:
  Used when some sources in a TRT that uses the equivalent distance term
  should not be collapsed.
  Example: *reqv_ignore_sources = src1 src2 src3*
  Default: empty list

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

sampling_method:
  One of early_weights, late_weights, early_latin, late_latin)
  Example: *sampling_method = early_latin*.
  Default: 'early_weights'

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

shakemap_uri:
  Dictionary used in ShakeMap calculations to specify a ShakeMap. Must contain
  a key named "kind" with values "usgs_id", "usgs_xml" or "file_npy".
  Example: shakemap_uri = {
  "kind": "usgs_xml",
  "grid_url": "file:///home/michele/usp000fjta/grid.xml",
  "uncertainty_url": "file:///home/michele/usp000fjta/uncertainty.xml"}.
  Default: empty dictionary

shift_hypo:
  Used in classical calculations to shift the rupture hypocenter.
  Example: *shift_hypo = true*.
  Default: false

site_effects:
  Used in ShakeMap calculations to turn on GMF amplification based
  on the vs30 values in the ShakeMap (site_effects='shakemap') or in the
  site collection (site_effects='sitecol').
  Example: *site_effects = 'shakemap'*.
  Default: 'no'

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

source_nodes:
  INTERNAL

spatial_correlation:
  Used in the ShakeMap calculator. The choics are "yes", "no" and "full".
  Example: *spatial_correlation = full*.
  Default: "yes"

specific_assets:
  INTERNAL

split_sources:
  INTERNAL

outs_per_task:
  How many outputs per task to generate (honored in some calculators)
  Example: *outs_per_task = 3*
  Default: 4

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
  Default: "avg"

time_per_task:
  Used in calculations with task splitting. If a task slice takes longer
  then *time_per_task* seconds, then spawn subtasks for the other slices.
  Example: *time_per_task=600*
  Default: 2000

total_losses:
  Used in event based risk calculations to compute total losses and
  and total curves by summing across different loss types. Possible values
  are "structural+nonstructural", "structural+contents",
  "nonstructural+contents", "structural+nonstructural+contents".
  Example: *total_losses = structural+nonstructural*
  Default: None

truncation_level:
  Truncation level used in the GMPEs.
  Example: *truncation_level = 0* to compute median GMFs.
  Default: no default

uniform_hazard_spectra:
  Flag used to generated uniform hazard specta for the given poes
  Example: *uniform_hazard_spectra = true*.
  Default: False

use_rates:
  When set, convert to rates before computing the statistical hazard curves
  Example: *use_rates = true*.
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

try:
    PSDIST = config.performance.pointsource_distance
except AttributeError:
    PSDIST = 1000
GROUND_MOTION_CORRELATION_MODELS = ['JB2009', 'HM2018']
TWO16 = 2 ** 16  # 65536
TWO32 = 2 ** 32
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64
ALL_CALCULATORS = ['aftershock',
                   'classical_risk',
                   'classical_damage',
                   'classical',
                   'custom',
                   'event_based',
                   'scenario',
                   'post_risk',
                   'ebrisk',
                   'scenario_risk',
                   'event_based_risk',
                   'disaggregation',
                   'multi_risk',
                   'classical_bcr',
                   'preclassical',
                   'event_based_damage',
                   'scenario_damage']

COST_TYPES = [
    'structural', 'nonstructural', 'contents', 'business_interruption']
ALL_COST_TYPES = [
    '+'.join(s) for l_idx in range(len(COST_TYPES))
    for s in itertools.combinations(COST_TYPES, l_idx + 1)]


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
    _input_files = ()  # set in get_oqparam

    KNOWN_INPUTS = {
        'rupture_model', 'exposure', 'site_model',
        'source_model', 'shakemap', 'gmfs', 'gsim_logic_tree',
        'source_model_logic_tree', 'hazard_curves',
        'insurance', 'reinsurance', 'ins_loss',
        'job_ini', 'multi_peril', 'taxonomy_mapping',
        'fragility', 'consequence', 'reqv', 'input_zip',
        'reqv_ignore_sources', 'amplification', 'station_data',
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
        'occupants_vulnerability',
        'residents_vulnerability',
        'area_vulnerability',
        'number_vulnerability',
    }
    # old name => new name
    ALIASES = {'individual_curves': 'individual_rlzs',
               'quantile_hazard_curves': 'quantiles',
               'mean_hazard_curves': 'mean',
               'max_hazard_curves': 'max'}

    hazard_imtls = {}
    override_vs30 = valid.Param(valid.positivefloat, None)
    aggregate_by = valid.Param(valid.namelists, [])
    reaggregate_by = valid.Param(valid.namelist, [])
    amplification_method = valid.Param(
        valid.Choice('convolution', 'kernel'), 'convolution')
    minimum_asset_loss = valid.Param(valid.floatdict, {'default': 0})
    area_source_discretization = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    asset_correlation = valid.Param(valid.Choice('0', '1'), 0)
    asset_life_expectancy = valid.Param(valid.positivefloat)
    assets_per_site_limit = valid.Param(valid.positivefloat, 1000)
    avg_losses = valid.Param(valid.boolean, True)
    base_path = valid.Param(valid.utf8, '.')
    calculation_mode = valid.Param(valid.Choice(*ALL_CALCULATORS))
    collapse_gsim_logic_tree = valid.Param(valid.namelist, [])
    collapse_level = valid.Param(int, -1)
    collect_rlzs = valid.Param(valid.boolean, None)
    coordinate_bin_width = valid.Param(valid.positivefloat, 100.)
    compare_with_classical = valid.Param(valid.boolean, False)
    concurrent_tasks = valid.Param(
        valid.positiveint, multiprocessing.cpu_count() * 2)  # by M. Simionato
    conditional_loss_poes = valid.Param(valid.probabilities, [])
    continuous_fragility_discretization = valid.Param(valid.positiveint, 20)
    cross_correlation = valid.Param(valid.utf8_not_empty, 'yes')
    cholesky_limit = valid.Param(valid.positiveint, 10_000)
    cachedir = valid.Param(valid.utf8, '')
    cache_distances = valid.Param(valid.boolean, False)
    description = valid.Param(valid.utf8_not_empty, "no description")
    disagg_by_src = valid.Param(valid.boolean, False)
    disagg_outputs = valid.Param(valid.disagg_outputs, list(valid.pmf_map))
    disagg_bin_edges = valid.Param(valid.dictionary, {})
    discard_assets = valid.Param(valid.boolean, False)
    discard_trts = valid.Param(str, '')  # tested in the cariboo example
    discrete_damage_distribution = valid.Param(valid.boolean, False)
    distance_bin_width = valid.Param(valid.positivefloat)
    mag_bin_width = valid.Param(valid.positivefloat, 1.)
    floating_x_step = valid.Param(valid.positivefloat, 0)
    floating_y_step = valid.Param(valid.positivefloat, 0)
    ignore_encoding_errors = valid.Param(valid.boolean, False)
    ignore_master_seed = valid.Param(valid.boolean, False)
    epsilon_star = valid.Param(valid.boolean, False)
    export_dir = valid.Param(valid.utf8, '.')
    exports = valid.Param(valid.export_formats, ())
    extreme_gmv = valid.Param(valid.floatdict, {'default': numpy.inf})
    gmf_max_gb = valid.Param(valid.positivefloat, .1)
    ground_motion_correlation_model = valid.Param(
        valid.NoneOr(valid.Choice(*GROUND_MOTION_CORRELATION_MODELS)), None)
    ground_motion_correlation_params = valid.Param(valid.dictionary, {})
    ground_motion_fields = valid.Param(valid.boolean, True)
    gsim = valid.Param(valid.utf8, '[FromFile]')
    hazard_calculation_id = valid.Param(valid.NoneOr(valid.positiveint), None)
    hazard_curves = valid.Param(valid.boolean, True)
    hazard_curves_from_gmfs = valid.Param(valid.boolean, False)
    hazard_maps = valid.Param(valid.boolean, False)
    horiz_comp_to_geom_mean = valid.Param(valid.boolean, False)
    ignore_missing_costs = valid.Param(valid.namelist, [])
    ignore_covs = valid.Param(valid.boolean, False)
    iml_disagg = valid.Param(valid.floatdict, {})  # IMT -> IML
    imt_ref = valid.Param(valid.intensity_measure_type, '')
    individual_rlzs = valid.Param(valid.boolean, None)
    inputs = valid.Param(dict, {})
    ash_wet_amplification_factor = valid.Param(valid.positivefloat, 1.0)
    infer_occur_rates = valid.Param(valid.boolean, False)
    intensity_measure_types = valid.Param(valid.intensity_measure_types, '')
    intensity_measure_types_and_levels = valid.Param(
        valid.intensity_measure_types_and_levels, None)
    interest_rate = valid.Param(valid.positivefloat)
    investigation_time = valid.Param(valid.positivefloat, None)
    limit_states = valid.Param(valid.namelist, [])
    lrem_steps_per_interval = valid.Param(valid.positiveint, 0)
    steps_per_interval = valid.Param(valid.positiveint, 1)
    master_seed = valid.Param(valid.positiveint, 123456789)
    maximum_distance = valid.Param(valid.IntegrationDistance.new)  # km
    asset_hazard_distance = valid.Param(valid.floatdict, {'default': 15})  # km
    max = valid.Param(valid.boolean, False)
    max_aggregations = valid.Param(valid.positivefloat, 100_000)
    max_data_transfer = valid.Param(valid.positivefloat, 2E11)
    max_gmvs_per_task = valid.Param(valid.positiveint, 1_000_000)
    max_potential_gmfs = valid.Param(valid.positiveint, 1E12)
    max_potential_paths = valid.Param(valid.positiveint, 15_000)
    max_sites_disagg = valid.Param(valid.positiveint, 10)
    pmap_max_mb = valid.Param(valid.positivefloat, 50.)
    mean_hazard_curves = mean = valid.Param(valid.boolean, True)
    std = valid.Param(valid.boolean, False)
    minimum_distance = valid.Param(valid.positivefloat, 0)
    minimum_intensity = valid.Param(valid.floatdict, {})  # IMT -> minIML
    minimum_magnitude = valid.Param(valid.floatdict, {'default': 0})  # by TRT
    modal_damage_state = valid.Param(valid.boolean, False)
    number_of_ground_motion_fields = valid.Param(valid.positiveint)
    number_of_logic_tree_samples = valid.Param(valid.positiveint, 0)
    num_epsilon_bins = valid.Param(valid.positiveint, 1)
    num_rlzs_disagg = valid.Param(valid.positiveint, 0)
    oversampling = valid.Param(
        valid.Choice('forbid', 'tolerate', 'reduce-rlzs'), 'tolerate')
    poes = valid.Param(valid.probabilities, [])
    poes_disagg = valid.Param(valid.probabilities, [])
    pointsource_distance = valid.Param(valid.floatdict, {'default': PSDIST})
    postproc_func = valid.Param(valid.mod_func, 'dummy.main')
    postproc_args = valid.Param(valid.dictionary, {})
    prefer_global_site_params = valid.Param(valid.boolean, None)
    ps_grid_spacing = valid.Param(valid.positivefloat, 0)
    quantile_hazard_curves = quantiles = valid.Param(valid.probabilities, [])
    random_seed = valid.Param(valid.positiveint, 42)
    reference_depth_to_1pt0km_per_sec = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_depth_to_2pt5km_per_sec = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_vs30_type = valid.Param(
        valid.Choice('measured', 'inferred'), 'inferred')
    reference_vs30_value = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_backarc = valid.Param(valid.boolean, False)
    region = valid.Param(valid.wkt_polygon, None)
    region_grid_spacing = valid.Param(valid.positivefloat, None)
    reqv_ignore_sources = valid.Param(valid.namelist, [])
    risk_imtls = valid.Param(valid.intensity_measure_types_and_levels, {})
    risk_investigation_time = valid.Param(valid.positivefloat, None)
    rlz_index = valid.Param(valid.positiveints, None)
    rupture_mesh_spacing = valid.Param(valid.positivefloat, 5.0)
    complex_fault_mesh_spacing = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    return_periods = valid.Param(valid.positiveints, [])
    sampling_method = valid.Param(
        valid.Choice('early_weights', 'late_weights',
                     'early_latin', 'late_latin'), 'early_weights')
    secondary_perils = valid.Param(valid.namelist, [])
    sec_peril_params = valid.Param(valid.dictionary, {})
    secondary_simulations = valid.Param(valid.dictionary, {})
    sensitivity_analysis = valid.Param(valid.dictionary, {})
    ses_per_logic_tree_path = valid.Param(
        valid.compose(valid.nonzero, valid.positiveint), 1)
    ses_seed = valid.Param(valid.positiveint, 42)
    shakemap_id = valid.Param(valid.nice_string, None)
    shakemap_uri = valid.Param(valid.dictionary, {})
    shift_hypo = valid.Param(valid.boolean, False)
    site_effects = valid.Param(
        valid.Choice('no', 'shakemap', 'sitemodel'), 'no')  # shakemap amplif.
    sites = valid.Param(valid.NoneOr(valid.coordinates), None)
    sites_slice = valid.Param(valid.simple_slice, None)
    soil_intensities = valid.Param(valid.positivefloats, None)
    source_id = valid.Param(valid.namelist, [])
    source_nodes = valid.Param(valid.namelist, [])
    spatial_correlation = valid.Param(valid.Choice('yes', 'no', 'full'), 'yes')
    specific_assets = valid.Param(valid.namelist, [])
    split_sources = valid.Param(valid.boolean, True)
    outs_per_task = valid.Param(valid.positiveint, 4)
    ebrisk_maxsize = valid.Param(valid.positivefloat, 2E10)  # used in ebrisk
    time_event = valid.Param(str, 'avg')
    time_per_task = valid.Param(valid.positivefloat, 2000)
    total_losses = valid.Param(valid.Choice(*ALL_COST_TYPES), None)
    truncation_level = valid.Param(lambda s: valid.positivefloat(s) or 1E-9)
    uniform_hazard_spectra = valid.Param(valid.boolean, False)
    use_rates = valid.Param(valid.boolean, False)
    vs30_tolerance = valid.Param(valid.positiveint, 0)
    width_of_mfd_bin = valid.Param(valid.positivefloat, None)

    @property
    def no_pointsource_distance(self):
        """
        :returns: True if the pointsource_distance is 1000 km
        """
        return set(self.pointsource_distance.values()) == {1000}

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

    def get_input_size(self):
        """
        :returns: the total size in bytes of the input files

        NB: this will fail if the files are not available, so it
        should be called only before starting the calculation.
        The same information is stored in the datastore.
        """
        # NB: when the OqParam object is instantiated from a dictionary and
        # not from a job.ini file the key 'job_ini ' has value '<in-memory>'
        return sum(os.path.getsize(f) for f in self._input_files
                   if f != '<in-memory>')

    def get_reqv(self):
        """
        :returns: an instance of class:`RjbEquivalent` if reqv_hdf5 is set
        """
        if 'reqv' not in self.inputs:
            return
        return {key: valid.RjbEquivalent(value)
                for key, value in self.inputs['reqv'].items()}

    def fix_legacy_names(self, dic):
        for name in list(dic):
            if name in self.ALIASES:
                if self.ALIASES[name] in dic:
                    # passed both the new (self.ALIASES[name]) and the old name
                    raise NameError('Please remove %s, you should use only %s'
                                    % (name, self.ALIASES[name]))
                # use the new name instead of the old one
                dic[self.ALIASES[name]] = dic.pop(name)

        inp = dic.get('inputs', {})
        if 'sites' in inp:
            if inp.get('site_model'):
                raise NameError('Please remove sites, you should use '
                                'only site_model')
            inp['site_model'] = [inp.pop('sites')]
            self.prefer_global_site_params = True

    def __init__(self, **names_vals):
        if '_log' in names_vals:  # called from engine
            del names_vals['_log']

        self.fix_legacy_names(names_vals)
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
        if ('intensity_measure_types_and_levels' in names_vals and
                'intensity_measure_types' in names_vals):
            logging.warning('Ignoring intensity_measure_types since '
                            'intensity_measure_types_and_levels is set')
        if 'iml_disagg' in names_vals:
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
        if 'minimum_intensity' in names_vals:
            dic = {}
            for imt, iml in self.minimum_intensity.items():
                if imt == 'default':
                    dic[imt] = iml
                else:
                    # normalize IMT, for instance SA(1.) => SA(1.0)
                    dic[from_string(imt).string] = iml
            self.minimum_intensity = dic
        if ('ps_grid_spacing' in names_vals and
                float(names_vals['ps_grid_spacing']) and
                'pointsource_distance' not in names_vals):
            self.pointsource_distance = dict(default=40.)
        if self.collapse_level >= 0:
            self.time_per_task = 1_000_000  # disable task_splitting

        # cut maximum_distance with minimum_magnitude
        if hasattr(self, 'maximum_distance'):
            # can be missing in post-calculations
            self.maximum_distance.cut(self.minimum_magnitude)

        # checks for risk
        self._risk_files = get_risk_files(self.inputs)
        if self.risk_files:
            # checks for risk_files
            hc = self.hazard_calculation_id
            if 'damage' in self.calculation_mode and not hc:
                ok = any('fragility' in key for key in self._risk_files)
                if not ok:
                    raise InvalidFile('Missing fragility files in %s' %
                                      self.inputs['job_ini'])
            elif ('risk' in self.calculation_mode and
                  self.calculation_mode != 'multi_risk' and not hc):
                ok = any('vulnerability' in key for key in self._risk_files)
                if not ok:
                    raise InvalidFile('Missing vulnerability files in %s' %
                                      self.inputs['job_ini'])

        if self.hazard_precomputed() and self.job_type == 'risk':
            self.check_missing('site_model', 'debug')
            self.check_missing('gsim_logic_tree', 'debug')
            self.check_missing('source_model_logic_tree', 'debug')

        if self.job_type == 'risk':
            self.check_aggregate_by()
        if ('hazard_curves' not in self.inputs and 'gmfs' not in self.inputs
                and 'multi_peril' not in self.inputs
                and self.inputs['job_ini'] != '<in-memory>'
                and self.calculation_mode != 'scenario'
                and not self.hazard_calculation_id):
            if not hasattr(self, 'truncation_level'):
                raise InvalidFile("Missing truncation_level in %s" %
                                  self.inputs['job_ini'])

        if 'reinsurance' in self.inputs:
            self.check_reinsurance()

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
        elif self.gsim:
            self.check_gsims([valid.gsim(self.gsim, self.base_path)])

        # check inputs
        unknown = set(self.inputs) - self.KNOWN_INPUTS
        if unknown:
            raise ValueError('Unknown key %s_file in %s' %
                             (unknown.pop(), self.inputs['job_ini']))

        # check return_periods vs poes
        if self.return_periods and not self.poes and self.investigation_time:
            self.poes = 1 - numpy.exp(
                - self.investigation_time / numpy.array(self.return_periods))

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
            if not self.disagg_bin_edges:
                for k in ('mag_bin_width', 'distance_bin_width',
                          'coordinate_bin_width', 'num_epsilon_bins'):
                    if k not in vars(self):
                        raise InvalidFile(
                            '%s must be set in %s' % (k, job_ini))
            if self.disagg_outputs and not any(
                    'Eps' in out for out in self.disagg_outputs):
                self.num_epsilon_bins = 1
            if self.rlz_index is not None and self.num_rlzs_disagg != 1:
                raise InvalidFile('%s: you cannot set rlzs_index and '
                                  'num_rlzs_disagg at the same time' % job_ini)

        # checks for classical_damage
        if self.calculation_mode == 'classical_damage':
            if self.conditional_loss_poes:
                raise InvalidFile(
                    '%s: conditional_loss_poes are not defined '
                    'for classical_damage calculations' % job_ini)
            if not self.investigation_time and not self.hazard_calculation_id:
                raise InvalidFile('%s: missing investigation_time' % job_ini)

        # check for GMFs from file
        if (self.inputs.get('gmfs', '').endswith('.csv')
                and 'site_model' not in self.inputs and self.sites is None):
            raise InvalidFile('%s: You forgot to specify a site_model'
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

        # check for amplification
        if ('amplification' in self.inputs and self.imtls and
                self.calculation_mode in ['classical', 'classical_risk',
                                          'disaggregation']):
            check_same_levels(self.imtls)

    def validate(self):
        """
        Set self.loss_types
        """
        from openquake.commonlib import datastore  # avoid circular import
        if self.hazard_calculation_id:
            with datastore.read(self.hazard_calculation_id) as ds:
                self._parent = ds['oqparam']
        else:
            self._parent = None
        # set all_cost_types
        # rt has the form 'vulnerability/structural', 'fragility/...', ...
        costtypes = set(rt.rsplit('/')[1] for rt in self.risk_files)
        if not costtypes and self.hazard_calculation_id:
            try:
                self._risk_files = rfs = get_risk_files(self._parent.inputs)
                costtypes = set(rt.rsplit('/')[1] for rt in rfs)
            except OSError:  # FileNotFound for wrong hazard_calculation_id
                pass
        self.all_cost_types = sorted(costtypes)  # including occupants

        # fix minimum_asset_loss
        self.minimum_asset_loss = {
            ln: calc.filters.getdefault(self.minimum_asset_loss, ln)
            for ln in self.loss_types}

        super().validate()
        self.check_source_model()

    def check_gsims(self, gsims):
        """
        :param gsims: a sequence of GSIM instances
        """
        has_sites = self.sites is not None or 'site_model' in self.inputs
        if not has_sites:
            return

        imts = set()
        for imt in self.imtls:
            im = from_string(imt)
            if imt.startswith("SA"):
                imts.add("SA")
            elif imt.startswith("EAS"):
                imts.add("EAS")
            elif imt.startswith("FAS"):
                imts.add("FAS")
            elif imt.startswith("DRVT"):
                imts.add("DRVT")
            else:
                imts.add(im.string)
        for gsim in gsims:
            if (hasattr(gsim, 'weight') or
                    self.calculation_mode == 'aftershock'):
                continue  # disable the check
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
                    elif param in site.param:  # mandatory params
                        param_name = site.param[param]
                        param_value = getattr(self, param_name)
                        if (isinstance(param_value, float) and
                                numpy.isnan(param_value)):
                            raise ValueError(
                                'Please set a value for %r, this is required '
                                'by the GSIM %s' % (param_name, gsim))

    @property
    def tses(self):
        """
        Return the total time as investigation_time * ses_per_logic_tree_path *
        (number_of_logic_tree_samples or 1)
        """
        return (self.investigation_time * self.ses_per_logic_tree_path *
                (self.number_of_logic_tree_samples or 1))

    @property
    def time_ratio(self):
        """
        The ratio risk_investigation_time / eff_investigation_time per rlz
        """
        if self.investigation_time is None:
            raise ValueError('Missing investigation_time in the .ini file')
        return (self.risk_investigation_time or self.investigation_time) / (
            self.investigation_time * self.ses_per_logic_tree_path)

    def risk_event_rates(self, num_events, num_haz_rlzs):
        """
        :param num_events: the number of events per risk realization
        :param num_haz_rlzs: the number of hazard realizations

        If risk_investigation_time is 1, returns the annual event rates for
        each realization as a list, possibly of 1 element.
        """
        if self.investigation_time is None:
            # for scenarios there is no effective_time
            return numpy.full_like(num_events, len(num_events))
        else:
            # for event based compute the time_ratio
            time_ratio = self.time_ratio
            if self.collect_rlzs:
                time_ratio /= num_haz_rlzs
            return time_ratio * num_events

    @property
    def imtls(self):
        """
        Returns a DictArray with the risk intensity measure types and
        levels, if given, or the hazard ones.
        """
        imtls = self.hazard_imtls or self.risk_imtls
        return DictArray(sort_by_imt(imtls)) if imtls else {}

    @property
    def min_iml(self):
        """
        :returns: a vector of minimum intensities, one per IMT
        """
        mini = self.minimum_intensity
        if mini:
            for imt in self.imtls:
                try:
                    mini[imt] = calc.filters.getdefault(mini, imt)
                except KeyError:
                    mini[imt] = 0
        if 'default' in mini:
            del mini['default']
        min_iml = numpy.array([mini.get(imt) or 1E-10 for imt in self.imtls])
        return min_iml

    def get_max_iml(self):
        """
        :returns: a vector of extreme intensities, one per IMT
        """
        max_iml = numpy.zeros(len(self.imtls))
        for m, imt in enumerate(self.imtls):
            max_iml[m] = calc.filters.getdefault(self.extreme_gmv, imt)
        return max_iml

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
        risk_imtls = AccumDict(accum=[])  # imt -> imls
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
            risk_imtls[rf.imt].extend(iml for iml in rf.imls if iml > 0)
        suggested = ['\nintensity_measure_types_and_levels = {']
        for imt, imls in risk_imtls.items():
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
        return numpy.dtype([('%.6f' % poe, imts_dt) for poe in self.poes])

    def imt_periods(self):
        """
        :returns: the IMTs with a period, to be used in an UHS calculation
        """
        imts = []
        for im in self.imtls:
            imt = from_string(im)
            if imt.period or imt.string == 'PGA':
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
        return {lt: i for i, lt in enumerate(self.ext_loss_types)}

    @property
    def loss_types(self):
        """
        :returns: list of loss types (empty for hazard)
        """
        if not hasattr(self, "all_cost_types"):  # for hazard
            return []
        names = []
        for lt in self.all_cost_types:
            names.append(lt)
        return names

    @property
    def ext_loss_types(self):
        """
        :returns: list of loss types + secondary loss types
        """
        etypes = self.loss_types
        if self.total_losses:
            etypes = self.loss_types + [self.total_losses]
        if 'insurance' in self.inputs:
            itypes = [lt + '_ins' for lt in self.inputs['insurance']]
            etypes = self.loss_types + itypes
        return etypes

    def loss_dt(self, dtype=F64):
        """
        :returns: a composite dtype based on the loss types including occupants
        """
        return numpy.dtype(self.loss_dt_list(dtype))

    def loss_dt_list(self, dtype=F64):
        """
        :returns: a data type list [(loss_name, dtype), ...]
        """
        dts = [(str(lt), dtype) for lt in self.loss_types]
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

    @property
    def cross_correl(self):
        """
        Return a cross correlation object (or None). See
        :mod:`openquake.hazardlib.cross_correlation` for more info.
        """
        try:
            cls = getattr(cross_correlation, self.cross_correlation)
        except AttributeError:
            return None
        return cls()

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
        if R > 1 and self.individual_rlzs or not stats:
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
                'event_based_risk ebrisk event_based_damage')

    def is_valid_disagg_by_src(self):
        """
        disagg_by_src can be set only if ps_grid_spacing = 0
        """
        if self.disagg_by_src:
            return self.ps_grid_spacing == 0
        return True

    def is_valid_shakemap(self):
        """
        hazard_calculation_id must be set if shakemap_id is set
        """
        if self.shakemap_uri:
            kind = self.shakemap_uri['kind']
            get_array = getattr(shakemap.parsers, 'get_array_' + kind)
            sig = inspect.signature(get_array)
            # parameters without default value
            params = [p.name for p in list(
                sig.parameters.values()) if p.default is p.empty]
            all_params = list(sig.parameters)
            if not all(p in list(self.shakemap_uri) for p in params) or \
                    not all(p in all_params for p in list(self.shakemap_uri)):
                raise ValueError(
                    'Error in shakemap_uri: Expected parameters %s, '
                    'valid parameters %s, got %s' %
                    (params, all_params, list(self.shakemap_uri)))
        return self.hazard_calculation_id if (
            self.shakemap_id or self.shakemap_uri) else True

    def is_valid_truncation_level(self):
        """
        In presence of a correlation model the truncation level must be nonzero
        """
        if self.ground_motion_correlation_model:
            return self.truncation_level != 0
        else:
            return True

    def is_valid_geometry(self):
        """
        It is possible to infer the geometry only if exactly
        one of sites, sites_csv, hazard_curves_csv, region is set.
        You did set more than one, or nothing.
        """
        if self.calculation_mode in ('preclassical', 'aftershock'):
            return True  # disable the check
        if 'hazard_curves' in self.inputs and (
                self.sites is not None or 'site_model' in self.inputs):
            return False
        has_sites = self.sites is not None or 'site_model' in self.inputs
        if not has_sites and not self.ground_motion_fields:
            # when generating only the ruptures you do not need the sites
            return True
        if ('risk' in self.calculation_mode or
                'damage' in self.calculation_mode or
                'bcr' in self.calculation_mode):
            return True  # no check on the sites for risk
        flags = dict(
            sites=bool(self.sites),
            site_model_csv=self.inputs.get('site_model', 0),
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
            return True  # disable the check
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
        soil_intensities must be defined only in classical calculations
        with amplification_method=convolution
        """
        classical = ('classical' in self.calculation_mode or
                     'disaggregation' in self.calculation_mode)
        if (classical and 'amplification' in self.inputs and
                self.amplification_method == 'convolution'):
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

    def is_valid_collect_rlzs(self):
        """
        sampling_method must be early_weights, only the mean is available,
        and number_of_logic_tree_samples must be greater than 1.
        """
        if self.collect_rlzs is None:
            self.collect_rlzs = self.number_of_logic_tree_samples > 1
        if self.job_type == 'hazard':
            return True
        if self.calculation_mode == 'event_based_damage':
            ini = self.inputs['job_ini']
            if not self.investigation_time:
                raise InvalidFile('Missing investigation_time in %s' % ini)
            return True
        elif self.collect_rlzs is False:
            return True
        elif self.hazard_calculation_id:
            n = self._parent.number_of_logic_tree_samples
            if n and n != self.number_of_logic_tree_samples:
                raise ValueError('Please specify number_of_logic_tree_samples'
                                 '=%d' % n)
        hstats = list(self.hazard_stats())
        nostats = not hstats or hstats == ['mean']
        return nostats and self.number_of_logic_tree_samples > 1 and (
            self.sampling_method == 'early_weights')

    def check_aggregate_by(self):
        tagset = asset.tagset(self.aggregate_by)
        if 'id' in tagset and len(tagset) > 1:
            raise ValueError('aggregate_by = id must contain a single tag')
        elif 'site_id' in tagset and len(tagset) > 1:
            raise ValueError(
                'aggregate_by = site_id must contain a single tag')
        elif 'reinsurance' in self.inputs:
            if not any(['policy'] == aggby for aggby in self.aggregate_by):
                err_msg = ('The field `aggregate_by = policy` in the %s file'
                           ' is required for reinsurance calculations.'
                           % self.inputs['job_ini'])
                if self.aggregate_by:
                    err_msg += (' Got `aggregate_by = %s` instead.'
                                % self.aggregate_by)
                raise InvalidFile(err_msg)
        return True

    def check_reinsurance(self):
        # there must be a 'treaty' and a loss type (possibly a total type)
        dic = self.inputs['reinsurance'].copy()
        try:
            [lt] = dic
        except ValueError:
            raise InvalidFile('%s: too many loss types in reinsurance %s'
                              % (self.inputs['job_ini'], list(dic)))
        if lt not in scientific.LOSSID:
            raise InvalidFile('%s: unknown loss type %s in reinsurance'
                              % (self.inputs['job_ini'], lt))
        if '+' in lt and not self.total_losses:
            raise InvalidFile('%s: you forgot to set total_losses=%s'
                              % (self.inputs['job_ini'], lt))

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
                or 'scenario' in self.calculation_mode
                or 'ins_loss' in self.inputs):
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

    def __toh5__(self):
        return hdf5.dumps(vars(self)), {}

    def __fromh5__(self, array, attrs):
        if isinstance(array, numpy.ndarray):
            # old format <= 3.11, tested in read_old_data,
            # used to read old GMFs
            dd = collections.defaultdict(dict)
            for (name_, literal_) in array:
                name = python3compat.decode(name_)
                literal = python3compat.decode(literal_)
                if '.' in name:
                    k1, k2 = name.split('.', 1)
                    dd[k1][k2] = ast.literal_eval(literal)
                else:
                    dd[name] = ast.literal_eval(literal)
            vars(self).update(dd)
        else:
            # for version >= 3.12
            vars(self).update(json.loads(python3compat.decode(array)))

        Idist = calc.filters.IntegrationDistance
        if hasattr(self, 'maximum_distance') and not isinstance(
                self.maximum_distance, Idist):
            self.maximum_distance = Idist(**self.maximum_distance)
