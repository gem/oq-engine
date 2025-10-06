# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
import sys
import json
import inspect
import logging
import pathlib
import tempfile
import functools
import collections
import numpy
import pandas
import itertools

from openquake.baselib import __version__, hdf5, python3compat, config
from openquake.baselib.parallel import Starmap
from openquake.baselib.general import (
    DictArray, AccumDict, cached_property, engine_version)
from openquake.hazardlib.imt import from_string, sort_by_imt, sec_imts
from openquake.hazardlib import shakemap
from openquake.hazardlib import correlation, cross_correlation, stats, calc
from openquake.hazardlib import valid, InvalidFile, site
from openquake.sep.classes import SecondaryPeril
from openquake.hazardlib.gsim_lt import GsimLogicTree
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

aggregate_exposure:
  Used to aggregate the exposure by hazard site and taxonomy.
  Example: *aggregate_exposure = true*
  Default: False

aggregate_loss_curves_types:
  Used for event-based risk and damage calculations, to estimate the aggregated
  loss Exceedance Probability (EP) only or to also calculate (if possible) the
  Occurrence Exceedance Probability (OEP) and/or the Aggregate Exceedance
  Probability (AEP).
  Example: *aggregate_loss_curves_types = aep, oep*.
  Default: ep

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

asce_version:
  ASCE version used in AELO mode.
  Example: *asce_version = asce7-22*.
  Default: "asce7-16"

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
  too distant from the hazard sites. In multi_risk calculations can be a
  dictionary: asset_hazard_distance = {'ASH': 50, 'LAVA': 10, ...}
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

correlation_cutoff:
  Used in conditioned GMF calculation to avoid small negative eigenvalues
  wreaking havoc with the numerics
  Example: *correlation_cutoff = 1E-11*
  Default: 1E-12

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

countries:
  Used to restrict the exposure to a single country in Aristotle mode.
  Example: *countries = ITA*.
  Default: ()

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

infer_occur_rates:
   If set infer the occurrence rates from the first probs_occur in
   nonparametric sources.
   Example: *infer_occur_rates = true*
   Default: False

infrastructure_connectivity_analysis:
    If set, run the infrastructure connectivity analysis.
    Example: *infrastructure_connectivity_analysis = true*
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

job_id:
   ID of a job in the database
   Example: *job_id = 42*.
   Default: 0 (meaning create a new job)

limit_states:
   Limit states used in damage calculations.
   Example: *limit_states = moderate, complete*
   Default: no default

local_timestamp:
  Timestamp that includes both the date, time and the time zone information
  Example: 2023-02-06 04:17:34+03:00
  Default: None

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

max_blocks:
  INTERNAL. Used in classical calculations

max_data_transfer:
  INTERNAL. Restrict the maximum data transfer in disaggregation calculations.

max_potential_gmfs:
  Restrict the product *num_sites * num_events*.
  Example: *max_potential_gmfs = 1E9*.
  Default: 2E11

max_potential_paths:
  Restrict the maximum number of realizations.
  Example: *max_potential_paths = 200*.
  Default: 15_000

max_sites_correl:
  Maximum number of sites for GMF-correlation.
  Example: *max_sites_correl = 2000*
  Default: 1200

max_sites_disagg:
  Maximum number of sites for which to store rupture information.
  In disaggregation calculations with many sites you may be forced to raise
  *max_sites_disagg*, that must be greater or equal to the number of sites.
  Example: *max_sites_disagg = 100*
  Default: 10

max_weight:
  INTERNAL

maximum_distance:
  Integration distance. Can be give as a scalar, as a dictionary TRT -> scalar
  or as dictionary TRT -> [(mag, dist), ...]
  Example: *maximum_distance = 200*.
  Default: no default

maximum_distance_stations:
  Applies only to scenario calculations with conditioned GMFs to discard
  stations.
  Example: *maximum_distance_stations = 100*.
  Default: None

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

minimum_engine_version:
   If set, raise an error if the engine version is below the minimum
   Example: *minimum_engine_version = 3.22*
   Default: None

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

mosaic_model:
  Used to restrict the ruptures to a given model
  Example: *mosaic_model = ZAF*
  Default: empty string

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
  calculations; when equal to "tolerate" do not raise the error (the default).
  Example: *oversampling = forbid*
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
  Default: {'default': 100}

postproc_func:
  Specify a postprocessing function in calculators/postproc.
  Example: *postproc_func = compute_mrd.main*
  Default: 'dummy.main' (no postprocessing)

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

rupture_dict:
  Dictionary with rupture parameters lon, lat, dep, mag, rake, strike, dip
  Example: *rupture_dict = {'lon': 10, 'lat': 20, 'dep': 10, 'mag': 6, 'rake': 0}*
  Default: {}

rupture_mesh_spacing:
  Set the discretization parameter (in km) for rupture geometries.
  Example: *rupture_mesh_spacing = 2.0*.
  Default: 5.0

sampling_method:
  One of early_weights, late_weights, early_latin, late_latin)
  Example: *sampling_method = early_latin*.
  Default: 'early_weights'

mea_tau_phi:
  Save the mean and standard deviations computed by the GMPEs
  Example: *mea_tau_phi = true*
  Default: False

sec_peril_params:
  INTERNAL

secondary_perils:
  List of supported secondary perils.
  Example: *secondary_perils = HazusLiquefaction, HazusDeformation*
  Default: empty list

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

site_class:
  ASCE site class used in AELO mode.
  Example: *site_class = 'A'*.
  Default: None

sites:
  Used to specify a list of sites.
  Example: *sites = 10.1 45, 10.2 45*.

site_labels:
  Specify a dictionary label_string -> label_index assuming each site
  have a field "label" corresponding to the label index.
  Example: *site_labels = {"Cascadia": 1}*.
  Default: {}

tile_spec:
  INTERNAL

tiling:
  Used to force the tiling or non-tiling strategy in classical calculations
  Example: *tiling = true*.
  Default: None, meaning the engine will decide what to do

smlt_branch:
   Used to restrict the source model logic tree to a specific branch
   Example: *smlt_branch=b1*
   Default: empty string, meaning all branches

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

split_by_gsim:
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

tectonic_region_type:
   Used to specify a tectonic region type.
   Example: *tectonic_region_type = Active Shallow Crust*.
   Default: '*'

time_event:
  Used in scenario_risk calculations when the occupancy depend on the time.
  Valid choices are "avg", "day", "night", "transit".
  Example: *time_event = day*.
  Default: "avg"

time_per_task:
  Used in calculations with task splitting. If a task slice takes longer
  then *time_per_task* seconds, then spawn subtasks for the other slices.
  Example: *time_per_task=1000*
  Default: 600

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

with_betw_ratio:
  Specify the between ratio for GSIMs with only the Total StdDev.
  This is necessary in conditioned GMFs calculations.
  Example: *with_betw_ratio = 1.7*
  Default: None
""" % __version__

PSDIST = float(config.performance.pointsource_distance)
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
VULN_TYPES = COST_TYPES + [
    'number', 'area', 'occupants', 'residents', 'affectedpop', 'injured']

# mapping version -> corresponding display name
ASCE_VERSIONS = {'ASCE7-16': 'ASCE 7-16 & 41-17',
                 'ASCE7-22': 'ASCE 7-22 & 41-23'}

SITE_CLASSES = {
    'A': {'display_name': 'A - Hard Rock', 'vs30': 1500},
    'B': {'display_name': 'B - Rock', 'vs30': 1080},
    'BC': {'display_name': 'BC', 'vs30': 760},
    'C': {'display_name': 'C - Very Dense Soil and Soft Rock', 'vs30': 530},
    'CD': {'display_name': 'CD', 'vs30': 365},
    'D': {'display_name': 'D - Stiff Soil', 'vs30': 260},
    'DE': {'display_name': 'DE', 'vs30': 185},
    'E': {'display_name': 'E - Soft Clay Soil', 'vs30': 150},
    'default': {'display_name': 'Default', 'vs30': [260, 365, 530]},
    'custom': {'display_name': 'Specify Vs30', 'vs30': None},
}


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


def check_increasing(dframe, *columns):
    """
    Make sure the passed columns of the dataframe exists and correspond
    to increasing numbers
    """
    for col in columns:
        arr = dframe[col].to_numpy()
        assert (numpy.diff(arr) >= 0).all(), arr


class OqParam(valid.ParamSet):
    _input_files = ()  # set in get_oqparam
    KNOWN_INPUTS = {
        'rupture_model', 'exposure', 'site_model', 'delta_rates',
        'source_model', 'shakemap', 'gmfs', 'gsim_logic_tree',
        'source_model_logic_tree', 'geometry', 'hazard_curves',
        'insurance', 'reinsurance', 'ins_loss',
        'job_ini', 'multi_peril', 'taxonomy_mapping',
        'fragility', 'consequence', 'reqv', 'input_zip',
        'reqv_ignore_sources', 'amplification', 'station_data', 'mmi',
        'nonstructural_fragility',
        'nonstructural_consequence',
        'structural_fragility',
        'structural_consequence',
        'contents_fragility',
        'contents_consequence',
        'business_interruption_fragility',
        'business_interruption_consequence',
        'structural_vulnerability_retrofitted',
        'groundshaking_fragility',
        'groundshaking_vulnerability',
        'liquefaction_fragility',
        'liquefaction_vulnerability',
        'landslide_fragility',
        'landslide_vulnerability',
        'post_loss_amplification',
    } | {vtype + '_vulnerability' for vtype in VULN_TYPES}
    # old name => new name
    ALIASES = {'individual_curves': 'individual_rlzs',
               'quantile_hazard_curves': 'quantiles',
               'mean_hazard_curves': 'mean',
               'max_hazard_curves': 'max'}

    hazard_imtls = {}
    override_vs30 = valid.Param(valid.positivefloats, ())
    aggregate_by = valid.Param(valid.namelists, [])
    aggregate_exposure = valid.Param(valid.boolean, False)
    aggregate_loss_curves_types = valid.Param(
        # accepting all comma-separated permutations of 1, 2 or 3 elements
        # of the list ['ep', 'aep' 'oep']
        valid.Choice(
            'ep', 'aep', 'oep',
            'ep, aep', 'ep, oep', 'aep, ep', 'aep, oep', 'oep, ep', 'oep, aep',
            'ep, aep, oep', 'ep, oep, aep', 'aep, ep, oep', 'aep, oep, ep',
            'oep, ep, aep', 'oep, aep, ep'),
        'ep')
    reaggregate_by = valid.Param(valid.namelist, [])
    amplification_method = valid.Param(
        valid.Choice('convolution', 'kernel'), 'convolution')
    asce_version = valid.Param(
        valid.Choice(*ASCE_VERSIONS.keys()), 'ASCE7-16')
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
    concurrent_tasks = valid.Param(valid.positiveint, Starmap.CT)
    conditional_loss_poes = valid.Param(valid.probabilities, [])
    continuous_fragility_discretization = valid.Param(valid.positiveint, 20)
    countries = valid.Param(valid.namelist, ())
    cross_correlation = valid.Param(valid.utf8_not_empty, 'yes')
    cholesky_limit = valid.Param(valid.positiveint, 10_000)
    correlation_cutoff = valid.Param(valid.positivefloat, 1E-12)
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
    infrastructure_connectivity_analysis = valid.Param(valid.boolean, False)
    intensity_measure_types = valid.Param(valid.intensity_measure_types, '')
    intensity_measure_types_and_levels = valid.Param(
        valid.intensity_measure_types_and_levels, None)
    interest_rate = valid.Param(valid.positivefloat)
    investigation_time = valid.Param(valid.positivefloat, None)
    job_id = valid.Param(valid.positiveint, 0)
    limit_states = valid.Param(valid.namelist, [])
    local_timestamp = valid.Param(valid.local_timestamp, None)
    lrem_steps_per_interval = valid.Param(valid.positiveint, 0)
    steps_per_interval = valid.Param(valid.positiveint, 1)
    master_seed = valid.Param(valid.positiveint, 123456789)
    maximum_distance = valid.Param(valid.IntegrationDistance.new)  # km
    maximum_distance_stations = valid.Param(valid.positivefloat, None)  # km
    asset_hazard_distance = valid.Param(valid.floatdict, {'default': 15})  # km
    max = valid.Param(valid.boolean, False)
    max_blocks = valid.Param(valid.positiveint, 100)
    max_data_transfer = valid.Param(valid.positivefloat, 2E11)
    max_potential_gmfs = valid.Param(valid.positiveint, 1E12)
    max_potential_paths = valid.Param(valid.positiveint, 15_000)
    max_sites_disagg = valid.Param(valid.positiveint, 10)
    max_sites_correl = valid.Param(valid.positiveint, 1200)
    mean_hazard_curves = mean = valid.Param(valid.boolean, True)
    mosaic_model = valid.Param(valid.three_letters, '')
    std = valid.Param(valid.boolean, False)
    minimum_distance = valid.Param(valid.positivefloat, 0)
    minimum_engine_version = valid.Param(valid.version, None)
    minimum_intensity = valid.Param(valid.floatdict, {})  # IMT -> minIML
    minimum_magnitude = valid.Param(valid.floatdict, {'default': 0})  # by TRT
    modal_damage_state = valid.Param(valid.boolean, False)
    number_of_ground_motion_fields = valid.Param(valid.positiveint)
    number_of_logic_tree_samples = valid.Param(valid.positiveint, 0)
    num_epsilon_bins = valid.Param(valid.positiveint, 1)
    num_rlzs_disagg = valid.Param(valid.positiveint, 0)
    oversampling = valid.Param(
        valid.Choice('forbid', 'tolerate'), 'tolerate')
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
        # Can be positive float, -999 or nan
        valid.positivefloatorsentinel, numpy.nan)
    reference_depth_to_2pt5km_per_sec = valid.Param(
        # Can be positive float, -999 or nan
        valid.positivefloatorsentinel, numpy.nan)
    reference_vs30_type = valid.Param(
        valid.Choice('measured', 'inferred'), 'inferred')
    reference_vs30_value = valid.Param(
        valid.positivefloat, numpy.nan)
    region = valid.Param(valid.wkt_polygon, None)
    region_grid_spacing = valid.Param(valid.positivefloat, None)
    reqv_ignore_sources = valid.Param(valid.namelist, [])
    risk_imtls = valid.Param(valid.intensity_measure_types_and_levels, {})
    risk_investigation_time = valid.Param(valid.positivefloat, None)
    rlz_index = valid.Param(valid.positiveints, None)
    rupture_mesh_spacing = valid.Param(valid.positivefloat, 5.0)
    rupture_dict = valid.Param(valid.dictionary, {})
    complex_fault_mesh_spacing = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    return_periods = valid.Param(valid.positiveints, [])
    sampling_method = valid.Param(
        valid.Choice('early_weights', 'late_weights',
                     'early_latin', 'late_latin'), 'early_weights')
    mea_tau_phi = valid.Param(valid.boolean, False)
    secondary_perils = valid.Param(valid.secondary_perils, [])
    sec_peril_params = valid.Param(valid.list_of_dict, [])
    ses_per_logic_tree_path = valid.Param(
        valid.compose(valid.nonzero, valid.positiveint), 1)
    ses_seed = valid.Param(valid.positiveint, 42)
    shakemap_id = valid.Param(valid.nice_string, None)
    # example: shakemap_uri = {'kind': 'usgs_id', 'id': 'XXX'}
    shakemap_uri = valid.Param(valid.dictionary, {})
    shift_hypo = valid.Param(valid.boolean, False)
    site_class = valid.Param(
        valid.NoneOr(valid.Choice(*SITE_CLASSES)), None)
    site_labels = valid.Param(valid.uint8dict, {})
    sites = valid.Param(valid.NoneOr(valid.coordinates), None)
    tile_spec = valid.Param(valid.tile_spec, None)
    tiling = valid.Param(valid.boolean, None)
    smlt_branch = valid.Param(valid.simple_id, '')
    soil_intensities = valid.Param(valid.positivefloats, None)
    source_id = valid.Param(valid.namelist, [])
    source_nodes = valid.Param(valid.namelist, [])
    spatial_correlation = valid.Param(valid.Choice('yes', 'no', 'full'), 'yes')
    specific_assets = valid.Param(valid.namelist, [])
    split_sources = valid.Param(valid.boolean, True)
    split_by_gsim = valid.Param(valid.positiveint, 0)
    outs_per_task = valid.Param(valid.positiveint, 4)
    tectonic_region_type = valid.Param(valid.utf8, '*')
    time_event = valid.Param(
        valid.Choice('avg', 'day', 'night', 'transit'), 'avg')
    time_per_task = valid.Param(valid.positivefloat, 600)
    total_losses = valid.Param(valid.Choice(*ALL_COST_TYPES), None)
    truncation_level = valid.Param(lambda s: valid.positivefloat(s) or 1E-9)
    uniform_hazard_spectra = valid.Param(valid.boolean, False)
    use_rates = valid.Param(valid.boolean, False)
    vs30_tolerance = valid.Param(int, 0)
    width_of_mfd_bin = valid.Param(valid.positivefloat, None)
    with_betw_ratio = valid.Param(valid.positivefloat, None)

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
        hc0 = ('hazard_calculation_id' in names_vals and
               names_vals['hazard_calculation_id'] == 0)
        if hc0:
            self.hazard_calculation_id = 0  # fake calculation_id
        if 'job_ini' not in self.inputs:
            self.inputs['job_ini'] = '<in-memory>'
        if 'calculation_mode' not in names_vals:
            self.raise_invalid('Missing calculation_mode')
        if 'region_constraint' in names_vals:
            if 'region' in names_vals:
                self.raise_invalid('You cannot have both region and '
                                   'region_constraint')
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
            self.iml_disagg = {str(from_string(imt)): [float(iml)]
                               for imt, iml in self.iml_disagg.items()}
            self.hazard_imtls = self.iml_disagg
            if 'intensity_measure_types_and_levels' in names_vals:
                self.raise_invalid(
                    'Please remove the intensity_measure_types_and_levels '
                    ': they will be inferred from the iml_disagg '
                    'dictionary')
        elif 'intensity_measure_types_and_levels' in names_vals:
            self.hazard_imtls = {
                k: [float(x) for x in v] for k, v in
                self.intensity_measure_types_and_levels.items()}
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

        self.check_hazard()
        self.check_gsim_lt()
        self.set_loss_types()
        self.check_risk()
        self.check_ebrisk()

    def raise_invalid(self, msg):
        """
        Raise an InvalidFile error
        """
        raise InvalidFile('%s: %s' % (self.inputs['job_ini'], msg))

    def check_gsim_lt(self):
        # check the gsim_logic_tree and set req_site_params
        self.req_site_params = set()
        if self.inputs.get('gsim_logic_tree'):
            if self.gsim != '[FromFile]':
                self.raise_invalid('if `gsim_logic_tree_file` is set, there'
                                   ' must be no `gsim` key')
            path = os.path.join(
                self.base_path, self.inputs['gsim_logic_tree'])
            gsim_lt = GsimLogicTree(path, ['*'])
            # check the GSIMs
            self._trts = set()
            discard = {trt.strip() for trt in self.discard_trts.split(',')}
            for trt, gsims in gsim_lt.values.items():
                if trt not in discard:
                    self.check_gsims(gsims)
                    self._trts.add(trt)
        elif self.gsim:
            self.check_gsims([valid.gsim(self.gsim, self.base_path)])
        else:
            self.raise_invalid('Missing gsim or gsim_logic_tree_file')
        if 'amplification' in self.inputs:
            self.req_site_params.add('ampcode')
        self.req_site_params = sorted(self.req_site_params)

    def check_risk(self):
        # checks for risk
        self._risk_files = get_risk_files(self.inputs)
        if (self.job_type == 'risk' and not
                self.shakemap_uri and not self.impact):
            # check the risk_files
            hc = self.hazard_calculation_id
            if 'damage' in self.calculation_mode and not hc:
                ok = any('fragility' in key for key in self._risk_files)
                if not ok:
                    self.raise_invalid('Missing fragility files')
            elif ('risk' in self.calculation_mode and
                  'multi_peril' not in self.inputs and not hc):
                ok = any('vulnerability' in key for key in self._risk_files)
                if not ok:
                    self.raise_invalid('missing vulnerability files')

        if self.hazard_precomputed() and self.job_type == 'risk':
            self.check_missing('site_model', 'debug')
            self.check_missing('gsim_logic_tree', 'debug')
            self.check_missing('source_model_logic_tree', 'debug')

        if self.job_type == 'risk':
            self.check_aggregate_by()
        if ('hazard_curves' not in self.inputs and 'gmfs' not in self.inputs
                and self.inputs['job_ini'] != '<in-memory>'
                and self.calculation_mode != 'scenario'
                and self.hazard_calculation_id is None):
            if 'multi_peril' not in self.inputs and not hasattr(
                    self, 'truncation_level'):
                self.raise_invalid("Missing truncation_level")

        if 'reinsurance' in self.inputs:
            self.check_reinsurance()

        # check investigation_time
        if (self.investigation_time and
                self.calculation_mode.startswith('scenario')):
            raise ValueError('%s: there cannot be investigation_time in %s'
                             % (self.inputs['job_ini'], self.calculation_mode))

        # check inputs
        unknown = set(self.inputs) - self.KNOWN_INPUTS
        if unknown:
            raise ValueError('Unknown key %s_file in %s' %
                             (unknown.pop(), self.inputs['job_ini']))

        # check return_periods vs poes
        if self.return_periods and not self.poes and self.investigation_time:
            self.poes = 1 - numpy.exp(
                - self.investigation_time / numpy.array(self.return_periods))

        # checks for classical_damage
        if self.calculation_mode == 'classical_damage':
            if self.conditional_loss_poes:
                self.raise_invalid(
                    'conditional_loss_poes are not defined '
                    'for classical_damage calculations')
            if (not self.investigation_time and
                    self.hazard_calculation_id is None):
                self.raise_invalid('missing investigation_time')

    def check_ebrisk(self):
        # check specific to ebrisk
        if self.calculation_mode == 'ebrisk':
            if self.ground_motion_fields:
                print('ground_motion_fields overridden to false',
                      file=sys.stderr)
                self.ground_motion_fields = False
            if self.hazard_curves_from_gmfs:
                self.raise_invalid(
                    'hazard_curves_from_gmfs=true is invalid in ebrisk')

    def check_hazard(self):
        # check for GMFs from file
        if (self.inputs.get('gmfs', [''])[0].endswith('.csv')
                and 'site_model' not in self.inputs and self.sites is None):
            self.raise_invalid('You forgot to specify a site_model')

        elif self.inputs.get('gmfs', [''])[0].endswith('.xml'):
            self.raise_invalid('GMFs in XML are not supported anymore')

        elif self.number_of_logic_tree_samples >= TWO16:
            self.raise_invalid('number_of_logic_tree_samples too big: %d' %
                               self.number_of_logic_tree_samples)

        # checks for event_based
        if 'event_based' in self.calculation_mode:
            if self.ruptures_hdf5 and not self.minimum_intensity:
                self.raise_invalid('missing minimum_intensity')

            if self.ps_grid_spacing:
                logging.warning('ps_grid_spacing is ignored in event_based '
                                'calculations')

            if self.ses_per_logic_tree_path >= TWO32:
                self.raise_invalid('ses_per_logic_tree_path too big: %d' %
                                   self.ses_per_logic_tree_path)

        # check for amplification
        if ('amplification' in self.inputs and self.imtls and
                self.calculation_mode in ['classical', 'classical_risk',
                                          'disaggregation']):
            check_same_levels(self.imtls)

        # checks for disaggregation
        if self.calculation_mode == 'disaggregation':
            if not self.poes_disagg and self.poes:
                self.poes_disagg = self.poes
            elif not self.poes and self.poes_disagg:
                self.poes = self.poes_disagg
            elif self.poes != self.poes_disagg:
                self.raise_invalid(
                    'poes_disagg != poes: %s!=%s' %
                    (self.poes_disagg, self.poes))
            if not self.poes_disagg and not self.iml_disagg:
                self.raise_invalid('poes_disagg or iml_disagg must be set')
            elif self.poes_disagg and self.iml_disagg:
                self.raise_invalid(
                    'iml_disagg and poes_disagg cannot be set at the same time')
            if not self.disagg_bin_edges:
                for k in ('mag_bin_width', 'distance_bin_width',
                          'coordinate_bin_width', 'num_epsilon_bins'):
                    if k not in vars(self):
                        self.raise_invalid('%s must be set' % k)
            if self.disagg_outputs and not any(
                    'Eps' in out for out in self.disagg_outputs):
                self.num_epsilon_bins = 1
            if self.rlz_index is not None and self.num_rlzs_disagg != 1:
                self.raise_invalid('you cannot set rlzs_index and '
                                   'num_rlzs_disagg at the same time')

        # check compute_rtgm will run
        if 'rtgm' in self.postproc_func:
            if 'PGA' and "SA(0.2)" and 'SA(1.0)' not in self.imtls:
                self.raise_invalid('the IMTs PGA, SA(0.2), and SA(1.0)'
                                   ' are required to use compute_rtgm')

    def set_loss_types(self):
        """
        Set .all_cost_types and .total_losses from the parent calculation,
        if any
        """
        from openquake.commonlib import datastore  # avoid circular import
        if self.hazard_calculation_id:
            with datastore.read(self.hazard_calculation_id) as ds:
                self._parent = ds['oqparam']
            if not self.total_losses:
                self.total_losses = self._parent.total_losses
        else:
            self._parent = None
        # set all_cost_types
        # rt has the form 'groundshaking/vulnerability/structural', ...
        costtypes = set(rt.split('/')[2] for rt in self.risk_files)
        if not costtypes and self.hazard_calculation_id:
            try:
                self._risk_files = rfs = get_risk_files(self._parent.inputs)
                costtypes = set(rt.split('/')[2] for rt in rfs)
            except OSError:  # FileNotFound for wrong hazard_calculation_id
                pass
        # all_cost_types includes occupants and exclude perils
        self.all_cost_types = sorted(costtypes - set(scientific.PERILTYPE))
        # fix minimum_asset_loss
        self.minimum_asset_loss = {
            ln: calc.filters.getdefault(self.minimum_asset_loss, ln)
            for ln in self.loss_types}

    def validate(self):
        """
        Perform some checks
        """
        super().validate()
        self.check_source_model()
        if 'post_loss_amplification' in self.inputs:
            df = pandas.read_csv(self.inputs['post_loss_amplification'])
            check_increasing(df, 'return_period', 'pla_factor')
            if self.avg_losses:
                self.raise_invalid(
                    "you must set avg_losses=false with post_loss_amplification")

    def check_gsims(self, gsims):
        """
        :param gsims: a sequence of GSIM instances
        """
        for gsim in gsims:
            self.req_site_params.update(gsim.REQUIRES_SITES_PARAMETERS)

        has_sites = self.sites is not None or 'site_model' in self.inputs
        if not has_sites:
            return

        imts = set()
        for imt in self.imtls:
            im = from_string(imt)
            if imt.startswith("SA"):
                imts.add("SA")
            elif imt.startswith("Sa_avg2"):
                imts.add("Sa_avg2")
            elif imt.startswith("Sa_avg3"):
                imts.add("Sa_avg3")
            elif imt.startswith("FIV3"):
                imts.add("FIV3")
            elif imt.startswith("SDi"):
                imts.add("SDi")
            elif imt.startswith("EAS"):
                imts.add("EAS")
            elif imt.startswith("FAS"):
                imts.add("FAS")
            elif imt.startswith("DRVT"):
                imts.add("DRVT")
            elif imt.startswith("AvgSA"):
                imts.add("AvgSA")
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
        min_iml = F64([mini.get(imt) or 1E-10 for imt in self.imtls])
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

    # called in CompositeRiskModel.init
    def set_risk_imts(self, risklist):
        """
        :param risklist:
            a list of risk functions with attributes
            .id, .peril, .loss_type, .kind
        :returns:
            a list of ordered unique perils

        Set the attribute .risk_imtls as a side effect, with the imts extracted
        from the risk functions, i.e. without secondary peril prefixes.
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
                self.raise_invalid(
                    'You must provide the '
                    'intensity measure levels explicitly. Suggestion:' +
                    '\n  '.join(suggested))
        if (len(self.imtls) == 0 and 'event_based' in self.calculation_mode and
                'gmfs' not in self.inputs and not self.hazard_calculation_id
                and self.ground_motion_fields):
            raise ValueError('Please define intensity_measure_types in %s' %
                             self.inputs['job_ini'])

        # check secondary imts
        for imt in self.get_primary_imtls():
            if any(sec_imt.endswith(imt) for sec_imt in sec_imts):
                self.raise_invalid('you forgot to set secondary_perils =')

        seco_imts = {sec_imt.split('_')[1] for sec_imt in self.sec_imts}
        risk_imts = set(self.risk_imtls)
        for imt in risk_imts - seco_imts:
            if imt.startswith(('PGA', 'PGV', 'SA', 'MMI')):
                pass  # ground shaking IMT
            else:
                raise ValueError(f'The risk functions contain {imt} which is '
                                 f'not in the secondary IMTs {seco_imts}')

        risk_perils = sorted(set(getattr(rf, 'peril', 'groundshaking')
                                 for rf in risklist))
        return risk_perils

    def get_primary_imtls(self):
        """
        :returns: IMTs and levels which are not secondary
        """
        return {imt: imls for imt, imls in self.imtls.items()
                if '_' not in imt and imt not in sec_imts}

    def hmap_dt(self):  # used for CSV export
        """
        :returns: a composite dtype (imt, poe)
        """
        imts = list(self.imtls) + self.sec_imts
        return numpy.dtype([('%s-%s' % (imt, poe), F32)
                            for imt in imts for poe in self.poes])

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
        return numpy.dtype([(imt, dtype) for imt in sort_by_imt(self.imtls)])

    @property
    def lti(self):
        """
        Dictionary extended_loss_type -> extended_loss_type index
        """
        return {lt: i for i, lt in enumerate(self.ext_loss_types)}

    @property
    def L(self):
        """
        :returns: the number of loss types
        """
        return len(self.loss_types)

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

    @property
    def total_loss_types(self):
        """
        :returns: a dictionary loss_type -> index
        """
        if self.total_losses:
            total = self.total_losses.split('+')
        elif len(self.loss_types) == 1:
            total = self.loss_types
        else:
            self.raise_invalid('please specify total_losses')
        return {lt: li for li, lt in enumerate(self.loss_types) if lt in total}

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
        for imt in self.all_imts():
            lst.append((imt, F32))
        return numpy.dtype(lst)

    def all_imts(self):
        """
        :returns: imt..., sec_imt...
        """
        return list(self.get_primary_imtls()) + self.sec_imts

    def get_sec_perils(self):
        """
        :returns: a list of secondary perils
        """
        return SecondaryPeril.instantiate(
            self.secondary_perils, self.sec_peril_params, self)

    @cached_property
    def sec_imts(self):
        """
        :returns: a list of secondary outputs
        """
        outs = []
        for sp in self.get_sec_perils():
            for out in sp.outputs:
                outs.append(f'{sp.__class__.__name__}_{out}')
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

    @property
    def rupture_xml(self):
        return ('rupture_model' in self.inputs and
                self.inputs['rupture_model'].endswith('.xml'))

    @property
    def ruptures_hdf5(self):
        if ('rupture_model' in self.inputs and
                self.inputs['rupture_model'].endswith('.hdf5')):
            return self.inputs['rupture_model']

    @property
    def impact(self):
        """
        Return True if we are in OQImpact mode, i.e. there is an HDF5
        exposure with a known structure
        """
        exposures = self.inputs.get('exposure', [])
        yes = exposures and exposures[0].endswith('.hdf5')
        if yes:
            if not self.quantiles:
                self.quantiles = [0.05, 0.50, 0.95]
            if not self.aggregate_by:
                # self.aggregate_by = [['ID_1'], ['OCCUPANCY']]
                self.aggregate_by = [['ID_2']]
        return yes

    @property
    def aelo(self):
        """
        Return True if we are in AELO mode, i.e. if
        postproc_func == 'compute_rtgm.main'
        """
        return self.postproc_func == 'compute_rtgm.main'

    @property
    def fastmean(self):
        """
        Return True if it is possible to use the fast mean algorithm
        """
        return (not self.individual_rlzs and self.soil_intensities is None
                and list(self.hazard_stats()) == ['mean'] and self.use_rates
                and not self.site_labels)

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

    def is_valid_concurrent_tasks(self):
        """
        At most you can use 30_000 tasks
        """
        return self.concurrent_tasks <= 30_000

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
            return True
        return self.hazard_calculation_id if self.shakemap_id else True

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
        gsim_lt = self.inputs['gsim_logic_tree']  # set self._trts
        trts = set(self.maximum_distance)
        unknown = ', '.join(trts - self._trts - set(self.minimum_magnitude)
                            - {'default'})
        if unknown:
            self.error = ('setting the maximum_distance for %s which is '
                          'not in %s' % (unknown, gsim_lt))
            return False
        for trt, val in self.maximum_distance.items():
            if trt not in self._trts and trt != 'default':
                # not a problem, the associated maxdist will simply be ignored
                logging.warning('tectonic region %r not in %s', trt, gsim_lt)
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
                if not (imt.startswith('SA') or imt in ['PGA', 'PGV']):
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
        if self.export_dir == '/tmp' and sys.platform == 'win32':
            # magically convert to the Windows tempdir
            self.export_dir = tempfile.gettempdir()
        if not os.path.isabs(self.export_dir):
            self.export_dir = os.path.normpath(
                os.path.join(self.input_dir, self.export_dir))
        if not self.exports or not self.exports[0]:  # () or ('',)
            # we are not exporting anything
            return True
        elif not os.path.exists(self.export_dir):
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
        sampling_method must be early_weights with collect_rlzs=true
        """
        if self.collect_rlzs is None:
            self.collect_rlzs = self.number_of_logic_tree_samples > 1
        if self.job_type == 'hazard':
            return True

        # there are more checks for risk calculations
        if self.collect_rlzs and self.individual_rlzs:
            self.raise_invalid("you cannot have individual_rlzs=true with "
                               "collect_rlzs=true")
        if self.calculation_mode == 'event_based_damage':
            if not self.investigation_time:
                self.raise_invalid('Missing investigation_time')
            return True
        elif self.collect_rlzs is False:
            return True
        elif self.hazard_calculation_id:
            n = self._parent.number_of_logic_tree_samples
            if n and n != self.number_of_logic_tree_samples:
                raise ValueError('Please specify number_of_logic_tree_samples'
                                 '=%d' % n)
        hstats = list(self.hazard_stats())
        if hstats and hstats != ['mean']:
            self.raise_invalid(
                'quantiles are not supported with collect_rlzs=true')
        if self.number_of_logic_tree_samples == 0:
            raise ValueError('collect_rlzs=true is inconsistent with '
                             'full enumeration')
        return self.sampling_method == 'early_weights'

    def is_valid_version(self):
        """
        The engine version must be >= {minimum_engine_version}
        """
        if not self.minimum_engine_version:
            return True
        return self.minimum_engine_version <= valid.version(engine_version())

    def check_aggregate_by(self):
        tagset = asset.tagset(self.aggregate_by)
        if 'id' in tagset and len(tagset) > 1:
            raise ValueError('aggregate_by = id must contain a single tag')
        elif 'site_id' in tagset and self.avg_losses:
            logging.warning('avg_losses with site_id in aggregate_by')
        elif 'reinsurance' in self.inputs:
            if not any(['policy'] == aggby for aggby in self.aggregate_by):
                err_msg = ('The field `aggregate_by = policy`'
                           ' is required for reinsurance calculations.')
                if self.aggregate_by:
                    err_msg += (' Got `aggregate_by = %s` instead.'
                                % self.aggregate_by)
                self.raise_invalid(err_msg)
        return True

    def check_reinsurance(self):
        # there must be a 'treaty' and a loss type (possibly a total type)
        dic = self.inputs['reinsurance'].copy()
        try:
            [lt] = dic
        except ValueError:
            self.raise_invalid(
                'too many loss types in reinsurance %s' % list(dic))
        if lt not in scientific.LOSSID:
            self.raise_invalid('%s: unknown loss type %s in reinsurance' % lt)
        if '+' in lt and not self.total_losses:
            self.raise_invalid('you forgot to set total_losses=%s' % lt)

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
        if ('hazard_curves' in self.inputs or 'gmfs' in self.inputs
                or 'rupture_model' in self.inputs
                or 'scenario' in self.calculation_mode
                or 'ins_loss' in self.inputs):
            return
        if ('source_model_logic_tree' not in self.inputs and
                'source_model' not in self.inputs and
                'multi_peril' not in self.inputs and
                self.inputs['job_ini'] != '<in-memory>' and
                self.hazard_calculation_id is None):
            raise ValueError('Missing source_model_logic_tree in %s '
                             'or missing --hc option' %
                             self.inputs.get('job_ini', 'job_ini'))

    def check_missing(self, param, action):
        """
        Make sure the given parameter is missing in the job.ini file
        """
        assert action in ('debug', 'info', 'warn', 'error'), action
        if self.inputs.get(param):
            msg = '%s_file is ignored in %s' % (param, self.calculation_mode)
            if action == 'error':
                self.raise_invalid(msg)
            else:
                getattr(logging, action)(msg)

    def hazard_precomputed(self):
        """
        :returns: True if the hazard is precomputed
        """
        if 'gmfs' in self.inputs or 'hazard_curves' in self.inputs:
            return True
        return self.hazard_calculation_id

    def get_haz_distance(self):
        """
        :returns: the asset_hazard_distance or region_grid_spacing * 1.414
        """
        asset_hazard_distance = max(self.asset_hazard_distance.values())
        if self.region_grid_spacing:
            haz_distance = self.region_grid_spacing * 1.414
        else:
            haz_distance = asset_hazard_distance
        return haz_distance

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

    # tested in run-demos.sh
    def to_ini(self, **inputs):
        """
        Converts the parameters into a string in .ini format
        """
        dic = {k: v for k, v in vars(self).items() if not k.startswith('_')}
        dic['inputs'].update(inputs)
        del dic['base_path'], dic['req_site_params']
        dic.pop('close', None)
        dic.pop('mags_by_trt', None)
        dic.pop('sec_imts', None)
        for k in 'export_dir exports all_cost_types hdf5path ideduc M K A'.\
                split():
            dic.pop(k, None)

        if 'secondary_perils' in dic:
            dic['secondary_perils'] = ' '.join(dic['secondary_perils'])
        if 'aggregate_by' in dic:
            dic['aggregate_by'] = '; '.join(
                ','.join(keys) for keys in dic['aggregate_by'])
        ini = '[general]\n' + '\n'.join(to_ini(k, v) for k, v in dic.items())
        return ini

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


def _rel_fnames(obj, base):
    # convert to relative paths
    if isinstance(obj, str):
        *b, n = pathlib.Path(obj).parts
        offset = len(base) - len(b)
        if offset > 0:
            relpath = ['..'] * offset + [n]
        else:
            relpath = b[len(base):] + [n]
        return '/'.join(relpath)
    elif isinstance(obj, list):
        return '\n  '.join(_rel_fnames(s, base) for s in obj)
    else:  # assume dict
        dic = {k: _rel_fnames(v, base) for k, v in obj.items()}
        return str(dic)


def to_ini(key, val):
    """
    Converts key, val into .ini format
    """
    if key == 'inputs':
        *base, _name = pathlib.Path(val.pop('job_ini')).parts
        fnames = []
        for v in val.values():
            if isinstance(v, str):
                fnames.append(v)
            elif isinstance(v, list):
                fnames.extend(v)
            elif isinstance(v, dict):
                fnames.extend(v.values())
        return '\n'.join(f'{k}_file = {_rel_fnames(v, base)}'
                         for k, v in val.items()
                         if not k.startswith('_'))
    elif key == 'sites':
        sites = ', '.join(f'{lon} {lat}' for lon, lat, dep in val)
        return f"sites = {sites}"
    elif key == 'region':
        coords = val[9:-2].split(',')  # strip POLYGON((...))
        return f'{key} = {", ".join(c for c in coords[:-1])}'
    elif key == 'hazard_imtls':
        return f"intensity_measure_types_and_levels = {val}"
    elif key in ('reqv_ignore_sources', 'poes', 'quantiles', 'disagg_outputs',
                 'source_id', 'source_nodes', 'soil_intensities'):
        return f"{key} = {' '.join(map(str, val))}"
    else:
        if val is None:
            val = ''
        return f'{key} = {val}'
