# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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

from django.conf import settings

from openquake.engine import engine
from openquake.baselib import config

BASE = os.path.abspath(
    os.path.join(
        getattr(settings, 'PAPERS_BASEPATH', '/opt/openquake'),
        'Earthquake_Scenarios'))

# DEFAULT INPUTS - ANY OF THESE COULD BE OVERWRITTEN IF THE USER WISHES
# THROUGH THE DASHBOARD
# RUP_ID = 6667936727154 # ID attribute of the rupture in the ses hdf5 -
# will be obtained from the dashboard

# Hazard inputs
HAZARD_ONLY = False # Median hazard only if True
GMM_LT = os.path.join(BASE, "Hypothetical_Events", "inputs", "PAPERS_gmc.xml")
SITE_MODEL = os.path.join(BASE, "Vs30", "site_model_ITA_025.csv")
IMTS_RISK = 'PGA, SA(0.3), SA(0.6), SA(1.0)'
INTEGRATION_DISTANCE = getattr(
    settings, 'PAPERS_HYPO_RUPT_INTEGRATION_DISTANCE', 150)
TRUNCATION = 3
NGMFS = 250

# Risk inputs
EXPOSURE = os.path.join(BASE, "Building_National_Exposure",
                        "Exposure_ITA.xml")
MAPPING = os.path.join(BASE,  "Building_National_Exposure",
                       "Vulnerability_mapping_ITA.csv")
FRAGILITY = os.path.join(BASE, "Building_Fragility_Consequences",
                         "fragility_structural.xml")
CONSEQUENCE = {
    'taxonomy': [
        os.path.join(BASE, "Building_Fragility_Consequences",
                     "consequence_fatalities.csv"),
        os.path.join(BASE, "Building_Fragility_Consequences",
                     "consequence_losses.csv")
    ]
}
# TOD = "day"

# Fixed inputs/constants
FNAME = os.path.join(BASE, "Hypothetical_Events", "inputs",
                     "rups_eur_branch_faults.hdf5")
# Datastore (the hdf5 containing the SES ruptures)
TWO24 = 2 ** 24


def get_job_ctx(rup_id,
                rup_hdf5,
                gsim_lt_xml,
                site_model_csv,
                imts,
                hdist,
                eps,
                ngmfs,
                exposure_model_xml,
                taxonomy_model_csv,
                fragility_csv,
                consequence_csv,
                # day_or_night,
                hazard_only,
                username):
    """
    Create the job context. The risk related parameters here have been chosen
    to mirror those in the scenario calculations for the historical events.
    """
    # Get required calculation mode
    if hazard_only is True:
        calc_mode = "scenario"
        num_gmfs = 1
        trunc = 0
    else:
        calc_mode = "scenario_damage"
        num_gmfs = ngmfs
        trunc = eps

    # Create dict equivalent to parsed .ini file
    job_dict = {
        'base_path': os.path.join(BASE, 'Hypothetical_Events'),
        'inputs':{
            'rupture_model': rup_hdf5,
            'gsim_logic_tree': gsim_lt_xml,
            'site_model': [site_model_csv],
            'exposure': [exposure_model_xml],
            'taxonomy_mapping': taxonomy_model_csv,
            'fragility': fragility_csv,
            'consequence': consequence_csv
        },
        'description': f'rupture_id = {rup_id}',
        'rupture_id': rup_id,
        'calculation_mode': calc_mode,
        'rupture_mesh_spacing': '5',
        'intensity_measure_types': imts,
        'truncation_level': str(trunc),
        'maximum_distance': str(hdist),
        'asset_hazard_distance': '5',
        'number_of_ground_motion_fields': str(num_gmfs),
        # NOTE: correlation disabled to avoid too big
        #       calculations and suppression of avg_gmf outputs
        # 'cross_correlation': 'GodaAtkinson2009',
        # 'ground_motion_correlation_model': 'JB2009',
        # 'ground_motion_correlation_params': '{"vs30_clustering":True}',
        'horiz_comp_to_geom_mean': 'true',
        # 'time_event': day_or_night,
        'export_dir': '/tmp',
        'ground_motion_fields': 'true',
        'gmf_max_gb': '100.0',
        'minimum_intensity': '0.05',
        'quantiles': '[0.05 0.95]',
        'aggregate_by': 'MATERIAL_TYPE;OCCUPANCY',
        'username': username
    }

    # If only want a scenario hazard calculation remove the risk
    # inputs/parameters
    if hazard_only is True:

        # First remove input file keys
        for key in ["exposure", "taxonomy_mapping", "fragility", "consequence"]:
            del job_dict["inputs"][key]

        # Then remove other parameters only needed for risk
        for key in ["asset_hazard_distance", "quantiles"]:
            del job_dict[key]

        # Correlation requires non-zero truncation (it's set to zero
        # in hazard only) given we just want the median ground-motion
        for key in ['cross_correlation',
                    'ground_motion_correlation_model',
                    'ground_motion_correlation_params']:
            del job_dict[key]

    [job] = engine.create_jobs([job_dict], config.distribution.log_level, None,
                               username, None)

    return job
