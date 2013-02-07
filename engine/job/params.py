# -*- coding: utf-8 -*-

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
This module contains the data required to map configuration values into
oq_job_profile columns.
"""

import re

from collections import namedtuple

from openquake.engine.db.models import OqJobProfile
from openquake.engine.utils.general import str2bool


ARRAY_RE = re.compile('[\s,]+')

# pylint: disable=C0103
Param = namedtuple('Param', 'column type default modes to_db to_job java_name')

# TODO unify with utils/oqrunner/config_writer.py
CALCULATION_MODE = {
    'Classical': 'classical',
    'Scenario': 'scenario',
    'Scenario Damage': 'scenario_damage',
    'Event Based': 'event_based',
    'Disaggregation': 'disaggregation',
    'UHS': 'uhs',
    'Classical BCR': 'classical_bcr',
    'Event Based BCR': 'event_based_bcr',
}

INPUT_FILE_TYPES = {
    'SOURCE_MODEL_LOGIC_TREE_FILE': 'lt_source',
    'GMPE_LOGIC_TREE_FILE': 'lt_gsim',
    'EXPOSURE': 'exposure',
    'FRAGILITY': 'fragility',
    'VULNERABILITY': 'vulnerability',
    'VULNERABILITY_RETROFITTED': 'vulnerability_retrofitted',
    'SINGLE_RUPTURE_MODEL': 'rupture_model',
    'SITE_MODEL': 'site_model',
}

ENUM_MAP = {
    'Average Horizontal': 'average',
    'Average Horizontal (GMRotI50)': 'gmroti50',
    'PGA': 'pga',
    'SA': 'sa',
    'PGV': 'pgv',
    'PGD': 'pgd',
    'IA': 'ia',
    'RSD': 'rsd',
    'MMI': 'mmi',
    'None': 'none',
    '1 Sided': 'onesided',
    '2 Sided': 'twosided',
    'Only along strike ( rupture full DDW)': 'alongstrike',
    'Along strike and down dip': 'downdip',
    'Along strike & centered down dip': 'centereddowndip',
    'Rock': 'rock',
    'Deep-Soil': 'deepsoil',
    'Total': 'total',
    'Inter-Event': 'interevent',
    'Intra-Event': 'intraevent',
    'None (zero)': 'zero',
    'Total (Mag Dependent)': 'total_mag_dependent',
    'Total (PGA Dependent)': 'total_pga_dependent',
    'Intra-Event (Mag Dependent)': 'intraevent_mag_dependent',
    'Point Sources': 'pointsources',
    'Line Sources (random or given strike)': 'linesources',
    'Cross Hair Line Sources': 'crosshairsources',
    '16 Spoked Line Sources': '16spokedsources',
}

REVERSE_ENUM_MAP = dict((v, k) for k, v in ENUM_MAP.iteritems())

CALCULATION_MODES = set(CALCULATION_MODE.values())
PARAMS = {}
PATH_PARAMS = INPUT_FILE_TYPES.keys()


def config_text_to_list(text, transform=lambda x: x):
    """ Convert a config file list (as a comma or space delimited list) to a
    list of values, with the option to transform each item. An example of such
    a transformation would be a `float` cast, but you can specify virtually
    any function which accepts and returns a single value.

    :param text: a comma or whitespace delimited list of config values (such as
        a list of PoE levels)
    :type text: `str`
    :param transform: specify a transform to be applied to each element
        (optional)
    :type transform: a function which accepts and returns a single value,
        a type (such as `float` or `int`), or equivalent

    >>> config_text_to_list('MagDistPMF MagDistEpsPMF')
    ['MagDistPMF', 'MagDistEpsPMF']
    >>> config_text_to_list('0.01, 0.02, 0.03', float)
    [0.01, 0.02, 0.03]
    """
    return [transform(val.strip()) for val in ARRAY_RE.split(text) if len(val)]


def map_enum(value):
    """Map enumerated values from configuration to database"""
    return ENUM_MAP[value]


# disabling pylint for 'Access to a protected member %s of a client class'
# and 'Too many arguments'
# pylint: disable=W0212,R0913
def define_param(name, column, modes=None, default=None, to_db=None,
                 to_job=lambda x: x, java_name=None):
    """
    Adds a new parameter definition to the PARAMS dictionary

    :param column: If `column` is `None`, the parameter is only checked but not
        inserted into the `oq_job_profile` table.
    :type column: `str`
    :param modes: The calculation modes to which this parameter applies. (Can
        either be a single string (for a single mode) or a sequence of strings
        for multiple modes. If `modes` is `None', this parameter will apply to
        all calculation modes.
    :param default: The default value for this parameter if it is not
        explicitly defined in a job config.
    :param to_db: A function to transform this parameter for storage in the
        database. Defaults to `None` if no transformation is required.
    :param to_job: A function to transform the value of this parameter when
        reading from a job config file. For example, INTENSITY_MEASURE_LEVELS
        are interpreted as a list of floats.
    :param str java_name: the name of the parameter in the Java domain.
    """

    if modes is None:
        modes = CALCULATION_MODES
    elif isinstance(modes, basestring):
        modes = set([modes])
    else:
        modes = set(modes)

    assert modes.issubset(CALCULATION_MODES), \
           'unexpected mode(s) %r' % (modes - CALCULATION_MODES)

    if column == None:
        PARAMS[name] = Param(column=column, type=None, default=default,
                             modes=modes, to_db=None, to_job=to_job,
                             java_name=java_name)
    else:
        column_type = type(OqJobProfile._meta.get_field_by_name(column)[0])
        PARAMS[name] = Param(column=column, type=column_type,
                             default=default, modes=modes, to_db=to_db,
                             to_job=to_job, java_name=java_name)


# A few helper functions for transforming job config params when they are read
# from the config file into a Job. Shortened names for the sake of brevity.
cttl = config_text_to_list
cttfl = lambda x: cttl(x, float)  # config text to float list


# general params
define_param('CALCULATION_MODE', None)
define_param('DESCRIPTION', 'description', default='')
define_param('SITES', 'sites', to_job=cttfl)
define_param('REGION_GRID_SPACING', 'region_grid_spacing', to_job=float)
define_param('REGION_VERTEX', 'region', to_job=cttfl)
define_param('OUTPUT_DIR', None)
define_param('BASE_PATH', None)
define_param("DEPTHTO1PT0KMPERSEC", "depth_to_1pt_0km_per_sec",
             default=100.0, java_name="Depth 1.0 km/sec", to_job=float)
define_param("VS30_TYPE", "vs30_type", default="measured",
             java_name="Vs30 Type", to_job=lambda s: s.capitalize())

# input files
define_param('FRAGILITY', None, modes=("scenario_damage"))
define_param('VULNERABILITY', None,
             modes=("scenario", "classical", "event_based", "disaggregation",
                    "uhs", "classical_bcr", "event_based_bcr"))
define_param('VULNERABILITY_RETROFITTED', None,
             modes=("classical_bcr", "event_based_bcr"))
define_param("SINGLE_RUPTURE_MODEL", None,
             modes=("scenario", "scenario_damage"))
define_param('EXPOSURE', None)
define_param('GMPE_LOGIC_TREE_FILE', None,
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'))
define_param('SOURCE_MODEL_LOGIC_TREE_FILE', None,
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'))
define_param('SITE_MODEL', None)

# Disaggregation parameters:
define_param('DISAGGREGATION_RESULTS', 'disagg_results',
             modes='disaggregation', to_job=cttl)
define_param('LATITUDE_BIN_LIMITS', 'lat_bin_limits', modes='disaggregation',
             to_job=cttfl)
define_param('LONGITUDE_BIN_LIMITS', 'lon_bin_limits', modes='disaggregation',
             to_job=cttfl)
define_param('MAGNITUDE_BIN_LIMITS', 'mag_bin_limits', modes='disaggregation',
             to_job=cttfl)
define_param('EPSILON_BIN_LIMITS', 'epsilon_bin_limits',
             modes='disaggregation', to_job=cttfl)
define_param('DISTANCE_BIN_LIMITS', 'distance_bin_limits',
             modes='disaggregation', to_job=cttfl)

# Uniform Hazard Spectra parameters:
define_param('UHS_PERIODS', 'uhs_periods', modes='uhs', to_job=cttfl)

# area sources
define_param('INCLUDE_AREA_SOURCES', 'include_area_sources',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=str2bool)
define_param('TREAT_AREA_SOURCE_AS', 'treat_area_source_as',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_db=map_enum)
define_param('AREA_SOURCE_DISCRETIZATION',
             'area_source_discretization',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
define_param('AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP',
             'area_source_magnitude_scaling_relationship',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'))

# grid/point sources
define_param('INCLUDE_GRID_SOURCES', 'include_grid_sources',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=str2bool)
define_param('TREAT_GRID_SOURCE_AS', 'treat_grid_source_as',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_db=map_enum)
define_param('GRID_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP',
             'grid_source_magnitude_scaling_relationship')

# simple faults
define_param('INCLUDE_FAULT_SOURCE', 'include_fault_source',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=str2bool)
define_param('FAULT_RUPTURE_OFFSET', 'fault_rupture_offset',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
define_param('FAULT_SURFACE_DISCRETIZATION', 'fault_surface_discretization',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
define_param('FAULT_MAGNITUDE_SCALING_RELATIONSHIP',
             'fault_magnitude_scaling_relationship',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'))
define_param('FAULT_MAGNITUDE_SCALING_SIGMA',
             'fault_magnitude_scaling_sigma',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
define_param('RUPTURE_ASPECT_RATIO', 'rupture_aspect_ratio',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
define_param('RUPTURE_FLOATING_TYPE', 'rupture_floating_type',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_db=map_enum)

# complex faults
define_param('INCLUDE_SUBDUCTION_FAULT_SOURCE',
             'include_subduction_fault_source',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=str2bool)
define_param('SUBDUCTION_FAULT_RUPTURE_OFFSET',
             'subduction_fault_rupture_offset',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
define_param('SUBDUCTION_FAULT_SURFACE_DISCRETIZATION',
             'subduction_fault_surface_discretization',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
define_param('SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP',
             'subduction_fault_magnitude_scaling_relationship',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'))
define_param('SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA',
             'subduction_fault_magnitude_scaling_sigma',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
define_param('SUBDUCTION_RUPTURE_ASPECT_RATIO',
             'subduction_rupture_aspect_ratio',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'))
define_param('SUBDUCTION_RUPTURE_FLOATING_TYPE',
             'subduction_rupture_floating_type',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_db=map_enum)

# Everything else; please maintain alphabetical ordering.
define_param('ASSET_CORRELATION', 'asset_correlation',
             modes=("scenario", "event_based"))
define_param('ASSET_LIFE_EXPECTANCY', 'asset_life_expectancy', to_job=float,
             modes=("classical_bcr", "event_based_bcr"))
define_param('COMPONENT', 'component', to_db=map_enum)
define_param('COMPUTE_HAZARD_AT_ASSETS_LOCATIONS', None,
             modes=('event_based', 'scenario', 'scenario_damage', 'classical',
                    'classical_bcr', 'event_based_bcr'),
             to_job=str2bool)
define_param('COMPUTE_MEAN_HAZARD_CURVE', 'compute_mean_hazard_curve',
             modes=('classical', 'classical_bcr'), to_job=str2bool)
define_param('CONDITIONAL_LOSS_POE', 'conditional_loss_poe', to_job=cttfl)
define_param('DAMPING', 'damping', default=0.0, to_job=float)
define_param('EPSILON_RANDOM_SEED', None, modes='scenario',
             to_job=int)
define_param('SAVE_GMFS', None,
             modes=('event_based', 'scenario', 'scenario_damage'),
             to_job=str2bool)
define_param('GMF_RANDOM_SEED', 'gmf_random_seed',
             modes=('event_based', 'scenario', 'scenario_damage'), to_job=int)
define_param('GMPE_LT_RANDOM_SEED', 'gmpe_lt_random_seed',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'), to_job=int)
define_param('GMPE_MODEL_NAME', 'gmpe_model_name')
define_param('GMPE_TRUNCATION_TYPE', 'truncation_type', to_db=map_enum)
define_param('GROUND_MOTION_CORRELATION', 'gm_correlated',
             modes=('scenario', 'scenario_damage', 'event_based',
             'event_based_bcr'), to_job=str2bool)
define_param('INTENSITY_MEASURE_LEVELS', 'imls',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=cttfl)
define_param('INTENSITY_MEASURE_TYPE', 'imt', to_db=map_enum,
             modes=('classical', 'event_based', 'disaggregation',
                    'classical_bcr', 'event_based_bcr', 'scenario',
                    'scenario_damage'))
define_param('INTEREST_RATE', 'interest_rate', to_job=float,
             modes=("classical_bcr", "event_based_bcr"))
define_param('INVESTIGATION_TIME', 'investigation_time', default=0.0,
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
define_param('LOSS_CURVES_OUTPUT_PREFIX', 'loss_curves_output_prefix')
define_param('LOSS_HISTOGRAM_BINS', 'loss_histogram_bins',
             modes=('event_based', 'event_based_bcr'), to_job=int)
define_param('LREM_STEPS_PER_INTERVAL', 'lrem_steps_per_interval',
             modes=('classical', 'classical_bcr'), to_job=int)
define_param('MAXIMUM_DISTANCE', 'maximum_distance', to_job=float,
             modes=('classical', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'))
define_param('MINIMUM_MAGNITUDE', 'min_magnitude', default=0.0,
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
define_param('NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS',
             'gmf_calculation_number', modes=('scenario', 'scenario_damage'),
             to_job=int)
define_param('NUMBER_OF_LOGIC_TREE_SAMPLES', 'realizations',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'), to_job=int)
define_param('NUMBER_OF_SEISMICITY_HISTORIES', 'histories',
             modes=('event_based', 'event_based_bcr'), to_job=int)
define_param('PERIOD', 'period', default=0.0, to_job=float)
define_param('POES', 'poes', modes=('classical', 'disaggregation', 'uhs'),
             to_job=cttfl)
define_param('QUANTILE_LEVELS', 'quantile_levels', modes='classical',
             to_job=cttfl)
define_param("REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM",
             "reference_depth_to_2pt5km_per_sec_param",
             java_name="Depth 2.5 km/sec", to_job=float)
define_param("REFERENCE_VS30_VALUE", "reference_vs30_value", java_name="Vs30",
             to_job=float)
define_param('RUPTURE_SURFACE_DISCRETIZATION',
             'rupture_surface_discretization',
             modes=('scenario', 'scenario_damage'), to_job=float)
define_param("SADIGH_SITE_TYPE", "sadigh_site_type", to_db=map_enum,
             java_name="Sadigh Site Type")
define_param('SOURCE_MODEL_LT_RANDOM_SEED', 'source_model_lt_random_seed',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'), to_job=int)
define_param('STANDARD_DEVIATION_TYPE', 'standard_deviation_type',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_db=map_enum)
define_param('TRUNCATION_LEVEL', 'truncation_level', to_job=int)
define_param('WIDTH_OF_MFD_BIN', 'width_of_mfd_bin',
             modes=('classical', 'event_based', 'disaggregation', 'uhs',
                    'classical_bcr', 'event_based_bcr'),
             to_job=float)
