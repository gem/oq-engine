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
import logging
import tempfile
import traceback
import numpy as np
import pandas as pd
import json

from openquake.engine import engine
from openquake.baselib import writers, hdf5, config
from openquake.baselib.general import group_array, mp
from openquake.commonlib.logs import get_datadir, get_job_info
from openquake.commonlib.readinput import get_oqparam
from openquake.hazardlib.source.rupture import get_ebr
from openquake.hazardlib import nrml
from openquake.hazardlib.source import rupture
from openquake.hazardlib.gsim_lt import GsimLogicTree
from openquake.hazardlib.calc.filters import filter_site_array_around
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.site import Site, SiteCollection

from django.http import JsonResponse
from django.conf import settings

# (
#    HttpResponse, HttpResponseNotFound, HttpResponseBadRequest,
#    HttpResponseForbidden, )


# Base path
BASE = os.path.abspath(
    os.path.join(
        getattr(settings, 'PAPERS_BASEPATH', '/opt/openquake'),
        'Earthquake_Scenarios/Hypothetical_Events'))

# oqdata path
OQDATA = get_datadir()

"""DEFAULT INPUTS - ANY OF THESE COULD BE OVERWRITTEN IF THE USER WISHES THROUGH THE DASHBOARD"""
# unused from engine
# RUP_ID = 6667936727154 # ID attribute of the rupture in the ses hdf5 - will be obtained from the dashboard

# Hazard inputs
HAZARD_ONLY = False # Median hazard only if True
GMM_LT = os.path.join(BASE, "inputs", "PAPERS_gmc.xml")
SITE_MODEL = os.path.join(BASE, "..", "Vs30", "site_model_ITA_025_adjusted.csv")
IMTS_RISK = 'PGA, SA(0.3), SA(0.6), SA(1.0)'
# INTEGRATION_DISTANCE = 150
INTEGRATION_DISTANCE = 20
TRUNCATION = 3
NGMFS = 250

# Risk inputs
EXPOSURE = os.path.join(BASE, "..", "Building_National_Exposure", "Exposure_ITA.xml")
TAXONOMY = os.path.join(BASE,  "..", "Building_National_Exposure", "Vulnerability_mapping_ITA.csv")
FRAGILITY = os.path.join(BASE, "..", "Building_Fragility_Consequences", "fragility_structural.xml")
CONSEQUENCE = {
    'taxonomy': [
        os.path.join(BASE, "..", "Building_Fragility_Consequences", "consequence_fatalities.csv"),                            
        os.path.join(BASE, "..", "Building_Fragility_Consequences", "consequence_losses.csv")
        ]
        }
TOD = "day"

# Fixed inputs/constants
FNAME = os.path.join(BASE,"inputs", "papers_ses.hdf5") # Datastore (the hdf5 containing the SES ruptures)
TWO24 = 2 ** 24


def get_ebrup(dstore, rup_id):
    """
    Get EBRupture from SEESAWS hdf5.
    """
    trts = {}
    rlzs_by_gsim = {}
    with hdf5.File(dstore) as r:

        # Get all the ruptures and geometries
        ruptures = r['ruptures'][:]
        geometry = r['rupgeoms']

        # Get the rup array and the geometry for given ID
        rup_idx, = np.where(ruptures['id'] == rup_id)
        [rec] = ruptures[rup_idx]
        geom = geometry[rec['geom_id']]

        # Tricky bit - need to convert the trt_smr to a regular TRT
        for model in r['full_lt']:
            full_lt = r[f'full_lt/{model}']
            trts[model] = full_lt.trts
            for trt_smr, rbg in full_lt.get_rlzs_by_gsim_dic().items():
                rlzs_by_gsim[model, trt_smr] = rbg

    rups_dic = group_array(ruptures, 'model', 'trt_smr')
    check = []
    for (model, trt_smr), rups in rups_dic.items():
            model = model.decode('ascii')
            if trt_smr == rec['trt_smr']:
                trt = trts[model][trt_smr // TWO24]
                if trt in check:
                    raise ValueError("debug - trt is not being assigned correctly")
                check.append(trt)
    
    return get_ebr(rec, geom, trt)            


def get_scenario_rup_csv(fname, rup_id):
    """
    Convert each rupture in a hdf5 (generated within a SEESAWS
    calculation) into a scenario rupture CSV, and then store the
    bytes of each CSV within the datastore so they can be retrieved
    as required later.
    """
    # Get the (event-based) rupture corresponding to the rup id
    eb_rup = get_ebrup(fname, rup_id)
    assert eb_rup.id == rup_id # Sanity check

    # Write to tmp csv in scenario format
    arr = rupture.to_csv_array([eb_rup])
    trts=[eb_rup.tectonic_region_type]
    rup_csv = os.path.join(tempfile.mkdtemp(), f'rup_{eb_rup.id}.csv')
    writers.write_csv(rup_csv, arr, sep=',', comment=dict(trts=trts, ses_seed=42))

    return rup_csv, eb_rup


def get_truncated_gmc_xml(trt, gmm_lt_fname):
    """
    Write the GMM LT for the given TRT to a temp XML (simplified version here
    given we are only handling EUR model - there is a region-dependent GMC
    version in GEESE if needed in the future).
    """
    # Get the gsim logic tree corresponding to the rupture's TRT
    gsim_lt = GsimLogicTree.read_dict(gmm_lt_fname, [trt])

    # Make tmp
    gmmLT_out = os.path.join(tempfile.mkdtemp(), 'trunc_gsim_lt.xml')

    # Write to another tmp XML
    for gmm_lt in gsim_lt.keys():
        lt = gsim_lt[gmm_lt]
        with open(gmmLT_out, 'wb') as f:
            nrml.write([lt.to_node()], f)

    return gmmLT_out


def get_hdist(trt):
    """
    Return the hazard integration distance for the given
    TRT. This is used to filter the sites to only those
    around the rupture.
    """
    # Path to EUR Vs30 job which contains TRT-dependent hdist
    job_file = os.path.join(BASE, "inputs", "job_vs30.ini")

    # Get into oqparam
    oq = get_oqparam(job_file)

    # Return integraiton distance for given TRT
    return np.max(oq.maximum_distance[trt])


def get_filt_sites(sites_fname, rup, hdist):
    """
    Filter the sites around the rupture and if any sites are
    left return a filtered site model in CSV format.
    """
    # Into dataframe
    sites = pd.read_csv(sites_fname)

    # Need a list of points to make the site model here
    sites_points = []
    for idx_site, site in sites.iterrows():

        # Extras specific to ESHM20 crustal GMC
        extras = {
            "xvf": site.xvf,
            "region": site.region,
            'slope': site.slope,
            'geology': site.geology
            }

        # Set to -999 to use GMM's own values
        setattr(site, 'z1pt0', -999)
        setattr(site, 'z2pt5', -999)

        # Make site obj
        pnt = Site(Point(site.lon, site.lat), site.vs30, site.z1pt0, site.z2pt5, **extras)
    
        # Add to the list of points
        sites_points.append(pnt)

    # Into site model
    sites_start = SiteCollection(sites_points)

    # Filter around the rupture
    filt_sites_arr = filter_site_array_around(sites_start.array, rup, hdist)

    # If sites remain in filtered sitecol
    if len(filt_sites_arr) == 0:
        raise ValueError(f"Cannot proceed - no sites within {hdist} km of the rupture")
    else:
        # Otherwise make new sitecol
        new_sites = object.__new__(SiteCollection)
        new_sites.array = filt_sites_arr

        # And return the new sites in a tmp csv
        return get_filt_sites_csv(new_sites)
    

def get_filt_sites_csv(filt_sites):
    """
    Get filtered sites into a csv.
    """
    # Set dict of main site params
    site_params = {"lon": [],
                   "lat": [],
                   "vs30": [],
                   "vs30measured": [],
                   "z1pt0": [],
                   "z2pt5": [],
                   'xvf': [],
                   'region': [],
                   'slope': [],
                   'geology': []
                   }

    # Get values from each site
    for _, site in enumerate(filt_sites):
        site_params['lon'].append(site.location.longitude)
        site_params['lat'].append(site.location.latitude)
        site_params['vs30'].append(site.vs30)
        site_params['vs30measured'].append(0) # Set vs30 measured to False
        site_params['slope'].append(site.slope)
        site_params['geology'].append(site.geology)
        site_params['z1pt0'].append(-999)
        site_params['z2pt5'].append(-999)
        site_params['xvf'].append(site.xvf)
        site_params['region'].append(site.region)

    # Into sites df
    filt_sites_df = pd.DataFrame(site_params)
    tmp = tempfile.mkdtemp()
    filt_sites_csv = os.path.join(tmp, 'sites_around_rup.csv')

    # Write to tmp csv        
    filt_sites_df.to_csv(filt_sites_csv, index=False)

    return filt_sites_csv


def get_job_ctx(rup_id,
                rup_csv,
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
                day_or_night,
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
        'base_path': BASE,
        'inputs':{
            'rupture_model': rup_csv,
            'gsim_logic_tree': gsim_lt_xml,
            'site_model': [site_model_csv],
            'exposure': [exposure_model_xml],
            'taxonomy_mapping': taxonomy_model_csv,
            'fragility': fragility_csv,
            'consequence': consequence_csv
                  },
        'description': f'rupture_id = {rup_id}',
        'calculation_mode': calc_mode,
        'rupture_mesh_spacing': '5',
        'intensity_measure_types': imts,
        'truncation_level': str(trunc),
        'maximum_distance': str(hdist),
        'asset_hazard_distance': '5',
        'number_of_ground_motion_fields': str(num_gmfs),
        'cross_correlation': 'GodaAtkinson2009',
        'ground_motion_correlation_model': 'JB2009',
        'ground_motion_correlation_params': '{"vs30_clustering":True}',
        'horiz_comp_to_geom_mean': 'true',
        'time_event': day_or_night,
        'export_dir': '/tmp',
        'ground_motion_fields': 'true',
        'minimum_intensity': '0.05',
        'quantiles': "[0.05 0.95]",
        'username': username
        }

    # If only want a scenario hazard calculation remove the risk inputs/parameters    
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


def export_rup_to_geojson(rup, rup_id):
    """
    Export the extracted rupture's surface to a geojson
    """
    # Extract the lon/lats of each surface in the rupture
    if hasattr(rup.surface, 'surfaces'):
        surfaces = []
        for surface in rup.surface.surfaces: # Multi-surface rupture
            bounds = surface.get_surface_boundaries()
            surfaces.append(bounds)
    else:
        surfaces = [[rup.surface.get_surface_boundaries()]]
        
    # Make a geojson of the rupture surface
    features = []
    for surf in surfaces:
        for lons, lats in surf:
            coords = [[float(lon), float(lat)] for lat, lon in zip(lats, lons)]
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                },
                "properties": {"fillColor": "#FFA500"}
                })
        
    rup_geojson = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::4326"
            }
        },
        "features": features
    }

    # Make a directory to store the ruptures in
    out = os.path.join(BASE, "rupture_geojsons")
    if not os.path.exists(out):
        os.makedirs(out)

    # Write to geojson
    rup_fname = os.path.join(out, f"rupture_id_{rup_id}.geojson")
    with open(rup_fname, "w") as f:
        json.dump(rup_geojson, f, indent=2)

    return rup_fname


def run_scenario_calc_from_ses_rupture_ext(
        fname,
        rup_id,
        gmm_lt,
        site_model,
        imts,
        hdist,
        eps,
        ngmfs,
        exposure,
        taxonomy,
        fragility,
        consequence,
        day_or_night,
        hazard_only=False,
        notify_to=None,
        username=None
        ): # By default compute risk too)
    """
    Author: christopher.brooks@globalquakemodel.org

    Code for PAPERS: Extract a rupture from an SES contained within a hdf5
    (generated from an a SEESAWS calc), write it to a scenario format CSV
    and generate a job which is executed using the OQ-Engine. Generates an
    additional hdf5 containing all of the results of a scenario risk calc.
    A geoJSON containing the rupture's surface geometry is returned too to
    permit visualisation of the rupture in the platform.

    The GSIM logic tree corresponds to the TRT of the rupture extracted (e.g.
    we use the Subduction Interface TRT GMC logic tree if the extracted rupture
    has a Subduction Interface TRT).

    NOTE: we use a modified GMC logic tree for the ASCR TRT.

        :param fname: Path to the hdf5 file containing the ruptures.

        :param rup_id: id attribute of the rupture to retrieve from the dstore
        
        :param gmm_lt: Path to the ground-motion characterisation. If the user
                       specifies an alternative ground-motion characterisation
                       it will be used instead of the default one. Remember that
                       the TRTs in the alternative gmm LT will need to correspond
                       to those in the EUR seismic source model.

        :param site_model: Path to the site model. If the user specifies an
                           alternative site model it will be used instead of the
                           default one (the default is 2.5 km spacing).

        :param imts: The IMTs the user wishes to consider. By default uses the
                     risk mosaic IMTs. See the IMTS_RISK variable at the top
                     of this script for how the IMTs must be specified.

        :param hdist: Hazard integration distance, which is used to filter sites
                      around the selected rupture. If set to None, then it is
                      determined by the TRT of the rupture based on the information
                      in the EUR Vs30 ini file.

        :param eps: Number of standard deviations to sample from mean (i.e. the
                    truncation level input parameter).

        :param ngmfs: Number of ground-motion fields to generate.

        :param exposure: Path to the exposure file. If the user specifies an
                         alternative exposure file for this parameter, it will
                         be used instead of the default one.

        :param taxonomy: Path to the taxonomy file. If the user specifies an
                         alternative taxonomy file for this parameter, it will
                         be used instead of the default one.

        :param fragility: Path to the fragility file. If the user specifies an
                          alternative fragility file for this parameter, it will
                          be used instead of the default one.

        :param consequence: Dictionary containing the paths to the consequences
                            input files. If the user specifies an alternative
                            file for this parameter, it will be used instead of
                            the default one.

        :param day_or_night: Determines if the calculation is ran assuming day
                             or night conditions. Must be set to either "day" or
                             "night".

        :param hazard_only: Boolean where if set to True will only generate
                            a hazard calculation using the median ground-motion
                            (the risk parameters will not be added to the dictionary
                            used to create the job file and the ngmfs and truncation
                            level will be set to 1 and 0 respectively).

    """
    # Extract the EBrupture into a tmp CSV usable in a scenario calculation
    rup_csv, eb_rup = get_scenario_rup_csv(fname, rup_id)

    # Export the rupture as a geojson
    rup_geojson = export_rup_to_geojson(eb_rup.rupture, rup_id)

    # Write the GMM LT to an OQ XML
    gsim_lt_xml = get_truncated_gmc_xml(eb_rup.rupture.tectonic_region_type, gmm_lt)

    # Get the TRT-dependent maximum distance if an integration distance is not specified
    if hdist is None:
        hdist = get_hdist(eb_rup.rupture.tectonic_region_type)

    # Filter sites to within a TRT-dependent distance of the rupture
    filt_sites_csv = get_filt_sites(site_model, eb_rup.rupture, hdist=hdist)

    # Build the job for extracted scenario format rupture
    job_ctx = get_job_ctx(rup_id,
                          rup_csv,
                          gsim_lt_xml,
                          filt_sites_csv,
                          imts,
                          hdist,
                          eps,
                          ngmfs,
                          exposure,
                          taxonomy,
                          fragility,
                          consequence,
                          day_or_night,
                          hazard_only,
                          username)

    try:
        mp.Process(target=engine.run_jobs, args=([job_ctx],), kwargs={
            'notify_to': notify_to}).start()
    except Exception as exc:
        # get the exception message
        exc_msg = traceback.format_exc() + str(exc)
        logging.error(exc_msg)
        response_data = dict(traceback=exc_msg.splitlines(), job_id=exc.job_id)
        status = 500
    else:
        response_data = get_job_info(job_ctx.calc_id)
        status = 200
    return JsonResponse(response_data, status=status)

    #     dstore = os.path.join(OQDATA, f"calc_{job_ctx.calc_id}.hdf5")
    # 
    #     return dstore, rup_geojson


def run_scenario_calc_from_ses_rupture(rup_id, notify_to=None, username=None):
    return run_scenario_calc_from_ses_rupture_ext(
        fname=FNAME,
        rup_id=rup_id,
        gmm_lt=GMM_LT,
        site_model=SITE_MODEL,
        imts=IMTS_RISK,
        hdist=INTEGRATION_DISTANCE,
        eps=TRUNCATION,
        ngmfs=NGMFS,
        exposure=EXPOSURE,
        taxonomy=TAXONOMY,
        fragility=FRAGILITY,
        consequence=CONSEQUENCE,
        day_or_night=TOD,
        hazard_only=HAZARD_ONLY,
        notify_to=notify_to,
        username=username
        )
