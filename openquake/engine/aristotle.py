# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
Master script for running an ARISTOTLE analysis
"""
import sys
import os
import getpass
import logging
import numpy
from openquake.baselib import config, hdf5, sap
from openquake.hazardlib import geo
from openquake.hazardlib.shakemap.parsers import get_rupture_dict
from openquake.commonlib import readinput
from openquake.engine import engine

CDIR = os.path.dirname(__file__)  # openquake/engine


def get_trts_around(lon, lat):
    """
    :returns: list of TRTs for the mosaic model covering lon, lat
    """
    lonlats = numpy.array([[lon, lat]])
    mosaic_df = readinput.read_mosaic_df(buffer=0.1)
    [mosaic_model] = geo.utils.geolocate(lonlats, mosaic_df)
    smodel = os.path.join(config.directory.mosaic_dir, 'site_model.hdf5')
    with hdf5.File(smodel) as f:
        df = f.read_df('model_trt_gsim_weight',
                       sel={'model': mosaic_model.encode()})
    return [trt.decode('utf8') for trt in df.trt.unique()]


def get_tmap_keys(exposure_hdf5, countries):
    """
    :returns: list of taxonomy mappings as keys in the the "tmap" data group
    """
    keys = []
    with hdf5.File(exposure_hdf5, 'r') as exp:
        for key in exp['tmap']:
            if set(key.split('_')) & countries:
                keys.append(key)
    return keys


def trivial_callback(
        job_id, params, job_owner_email, outputs_uri, exc=None):
    if exc:
        sys.exit('There was an error: %s' % exc)
    print('Finished job(s) %d correctly. Params: %s' % (job_id, params))


def get_aristotle_allparams(
        usgs_id, lon, lat, dep, mag, rake, dip, strike, maximum_distance, trt,
        truncation_level, number_of_ground_motion_fields,
        asset_hazard_distance, ses_seed):
    smodel = os.path.join(config.directory.mosaic_dir, 'site_model.hdf5')
    expo = os.path.join(config.directory.mosaic_dir, 'exposure.hdf5')
    # two use cases: 1) only usgs_id is passed;
    #                2) rupdic params are passed (including lon)
    if lon is None:
        rupdic = get_rupture_dict(usgs_id)
    else:
        rupdic = dict(
            lon=lon, lat=lat, dep=dep, mag=mag,
            rake=rake, dip=dip, strike=strike)
    inputs = {'exposure': [expo],
              'site_model': [smodel],
              'job_ini': '<in-memory>'}
    if trt is None:
        trts = get_trts_around(rupdic['lon'], rupdic['lat'])
        trt = trts[0]
    params = dict(
        calculation_mode='scenario_risk',
        rupture_dict=str(rupdic),
        maximum_distance=str(maximum_distance),
        tectonic_region_type=trt,
        truncation_level=str(truncation_level),
        number_of_ground_motion_fields=str(number_of_ground_motion_fields),
        asset_hazard_distance=str(asset_hazard_distance),
        ses_seed=str(ses_seed),
        inputs=inputs)
    oq = readinput.get_oqparam(params)
    readinput.Global.reset()  # reset the cache
    sitecol, assetcol, discarded = readinput.get_sitecol_assetcol(oq)
    id0s, counts = numpy.unique(assetcol['ID_0'], return_counts=1)
    countries = set(assetcol.tagcol.ID_0[i] for i in id0s)
    tmap_keys = get_tmap_keys(expo, countries)
    logging.root.handlers = []  # avoid breaking the logs
    allparams = []
    for key in tmap_keys:
        print('Using taxonomy mapping for %s' % key)
        params['countries'] = key.replace('_', ' ')
        countries_per_tmap = ', '.join(
            [country for country in key.split('_') if country in countries])
        params['description'] = (
            f'{usgs_id} ({rupdic["lat"]}, {rupdic["lon"]}) M{rupdic["mag"]}'
            f' {countries_per_tmap}')
        allparams.append(params.copy())
    return allparams


def main(usgs_id, lon=None, lat=None, dep=None, mag=None, rake=None, dip='90',
         strike='0', maximum_distance='300', trt=None, truncation_level='3',
         number_of_ground_motion_fields='10', asset_hazard_distance='15',
         ses_seed='42', job_owner_email=None, outputs_uri=None, allparams=None,
         jobctxs=None,
         callback=trivial_callback):
    """
    This script is meant to be called from the WebUI in production mode,
    and from the command-line in testing mode.
    """
    if jobctxs is None:
        # in  testing mode create a new job context
        user = getpass.getuser()
        allparams = get_aristotle_allparams(
            usgs_id, lon, lat, dep, mag, rake, dip, strike, maximum_distance,
            trt, truncation_level, number_of_ground_motion_fields,
            asset_hazard_distance, ses_seed)
        jobctxs = engine.create_jobs(
            allparams, config.distribution.log_level, None, user, None)
    for job_idx, job in enumerate(jobctxs):
        try:
            engine.run_jobs([job])
        except Exception as exc:
            callback(job.calc_id, allparams[job_idx], job_owner_email,
                     outputs_uri, exc=exc)
        else:
            callback(job.calc_id, allparams[job_idx], job_owner_email,
                     outputs_uri, exc=None)


main.usgs_id = 'ShakeMap ID'
main.lon = 'Longitude'
main.lat = 'Latitude'
main.dep = 'Dep'
main.mag = 'Magnitude'
main.rake = 'Rake'
main.dip = 'Dip'
main.strike = 'Strike'
main.maximum_distance = 'Maximum distance in km'
main.trt = 'Tectonic region type'
main.truncation_level = 'Truncation level'
main.number_of_ground_motion_fields = 'Number of ground motion fields'
main.asset_hazard_distance = 'Asset hazard distance'
main.ses_seed = 'SES seed'

if __name__ == '__main__':
    sap.run(main)
