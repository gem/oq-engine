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
from openquake.hazardlib import geo, nrml, sourceconverter
from openquake.hazardlib.shakemap.parsers import download_rupture_dict
from openquake.commonlib import readinput
from openquake.engine import engine

CDIR = os.path.dirname(__file__)  # openquake/engine


def get_trts_around(rupdic, mosaic_dir):
    """
    :returns: list of TRTs for the mosaic model covering lon, lat
    """
    lon, lat = rupdic['lon'], rupdic['lat']
    usgs_id = rupdic.get('usgs_id', '')
    lonlats = numpy.array([[lon, lat]])
    mosaic_df = readinput.read_mosaic_df(buffer=1)
    [mosaic_model] = geo.utils.geolocate(lonlats, mosaic_df)
    if mosaic_model == '???':
        raise ValueError(f'({lon}, {lat}) is not covered by the mosaic!')
    smodel = os.path.join(mosaic_dir, 'site_model.hdf5')
    with hdf5.File(smodel) as f:
        df = f.read_df('model_trt_gsim_weight',
                       sel={'model': mosaic_model.encode()})
    logging.info('Considering %s[%s]: (%s, %s)',
                 usgs_id, mosaic_model, lon, lat)
    trts = [trt.decode('utf8') for trt in df.trt.unique()]
    return trts, mosaic_model


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
        job_id, params, job_owner_email=None, outputs_uri=None, exc=None):
    if exc:
        logging.error('', exc_info=True)
        sys.exit('There was an error: %s' % exc)
    print('Finished job(s) %d correctly. Params: %s' % (job_id, params))


def get_rupture_dict(dic):
    """
    :param dic: a dictionary with keys usgs_id and rupture_file
    :returns: a new dictionary with keys usgs_id, rupture_file, lon, lat...
    """
    usgs_id = dic['usgs_id']
    rupture_file = dic['rupture_file']
    if rupture_file:
        [rup_node] = nrml.read(rupture_file)
        conv = sourceconverter.RuptureConverter(rupture_mesh_spacing=5.)
        rup = conv.convert_node(rup_node)
        rup.tectonic_region_type = '*'
        hp = rup.hypocenter
        rupdic = dict(lon=hp.x, lat=hp.y, dep=hp.z,
                      mag=rup.mag, rake=rup.rake,
                      strike=rup.surface.get_strike(),
                      dip=rup.surface.get_dip(),
                      usgs_id=usgs_id,
                      rupture_file=rupture_file)
    elif dic.get('lon') is not None:  # when called from `oq mosaic aristotle`
        rupdic = dic
    else:
        rupdic = download_rupture_dict(usgs_id)
    return rupdic


def get_aristotle_allparams(rupture_dict, maximum_distance, trt,
                            truncation_level, number_of_ground_motion_fields,
                            asset_hazard_distance, ses_seed, mosaic_dir):
    """
    :returns: a list of dictionaries suitable for an Aristotle calculation
    """
    smodel = os.path.join(mosaic_dir, 'site_model.hdf5')
    expo = os.path.join(mosaic_dir, 'exposure.hdf5')
    inputs = {'exposure': [expo],
              'site_model': [smodel],
              'job_ini': '<in-memory>'}
    rupdic = get_rupture_dict(rupture_dict)
    rupture_file = rupdic.pop('rupture_file')
    if trt is None:
        trts, _ = get_trts_around(rupdic, mosaic_dir)
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
    if rupture_file:
        inputs['rupture_model'] = rupture_file
    oq = readinput.get_oqparam(params)
    sitecol, assetcol, discarded, exp = readinput.get_sitecol_assetcol(oq)
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
            f'{rupdic["usgs_id"]} ({rupdic["lat"]}, {rupdic["lon"]})'
            f' M{rupdic["mag"]} {countries_per_tmap}')
        allparams.append(params.copy())
    return allparams


def main_web(allparams, jobctxs,
             job_owner_email=None, outputs_uri=None,
             callback=trivial_callback):
    """
    This script is meant to be called from the WebUI
    """
    for params, job in zip(allparams, jobctxs):
        try:
            engine.run_jobs([job])
        except Exception as exc:
            callback(job.calc_id, params, job_owner_email,
                     outputs_uri, exc=exc)
        else:  # success
            callback(job.calc_id, params, job_owner_email, outputs_uri)


def main_cmd(usgs_id, rupture_file=None, rupture_dict=None,
             callback=trivial_callback, *,
             maximum_distance='300', trt=None, truncation_level='3',
             number_of_ground_motion_fields='10', asset_hazard_distance='15',
             ses_seed='42', mosaic_dir=config.directory.mosaic_dir):
    """
    This script is meant to be called from the command-line
    """
    if rupture_dict is None:
        rupture_dict = dict(usgs_id=usgs_id, rupture_file=rupture_file)
    try:
        allparams = get_aristotle_allparams(
            rupture_dict, maximum_distance, trt, truncation_level,
            number_of_ground_motion_fields, asset_hazard_distance,
            ses_seed, mosaic_dir)
    except Exception as exc:
        callback(None, dict(usgs_id=usgs_id), exc=exc)
        return
    # in  testing mode create new job contexts
    user = getpass.getuser()
    jobctxs = engine.create_jobs(
        allparams, config.distribution.log_level, None, user, None)
    for params, job in zip(allparams, jobctxs):
        try:
            engine.run_jobs([job])
        except Exception as exc:
            callback(job.calc_id, params, exc=exc)
        else:
            callback(job.calc_id, params, exc=None)


main_cmd.usgs_id = 'ShakeMap ID'  # i.e. us6000m0xl
main_cmd.rupture_file = 'XML file with the rupture model (optional)'
main_cmd.rupture_dict = 'Used by the command `oq mosaic aristotle`'
main_cmd.callback = ''
main_cmd.maximum_distance = 'Maximum distance in km'
main_cmd.trt = 'Tectonic region type'
main_cmd.truncation_level = 'Truncation level'
main_cmd.number_of_ground_motion_fields = 'Number of ground motion fields'
main_cmd.asset_hazard_distance = 'Asset hazard distance'
main_cmd.ses_seed = 'SES seed'

if __name__ == '__main__':
    sap.run(main_cmd)
