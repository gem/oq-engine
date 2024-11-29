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
from dataclasses import dataclass
import numpy
from json.decoder import JSONDecodeError
from urllib.error import HTTPError
from openquake.baselib import config, hdf5, sap
from openquake.hazardlib import nrml, sourceconverter
from openquake.hazardlib.shakemap.parsers import (
    download_rup_rupdic, download_station_data_file)
from openquake.commonlib import readinput
from openquake.commonlib.calc import get_close_mosaic_models
from openquake.engine import engine

CDIR = os.path.dirname(__file__)  # openquake/engine


@dataclass
class AristotleParam:
    rupture_dict: dict
    time_event: str
    maximum_distance: float
    mosaic_model: str
    trt: str
    truncation_level: float
    number_of_ground_motion_fields: int
    asset_hazard_distance: float
    ses_seed: int
    local_timestamp: str = None
    exposure_hdf5: str = None
    station_data_file: str = None
    maximum_distance_stations: float = None


def get_trts_around(mosaic_model, exposure_hdf5):
    """
    :returns: list of TRTs for the given mosaic model
    """
    with hdf5.File(exposure_hdf5) as f:
        df = f.read_df('model_trt_gsim_weight',
                       sel={'model': mosaic_model.encode()})
    trts = [trt.decode('utf8') for trt in df.trt.unique()]
    return trts


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
    else:
        _rup, rupdic = download_rup_rupdic(usgs_id)
    return rupdic


def get_aristotle_params(arist):
    """
    :param arist: an instance of AristotleParam
    :returns: a list of dictionaries suitable for an Aristotle calculation
    """
    if arist.exposure_hdf5 is None:
        arist.exposure_hdf5 = os.path.join(
            config.directory.mosaic_dir, 'exposure.hdf5')
    inputs = {'exposure': [arist.exposure_hdf5],
              'job_ini': '<in-memory>'}
    rupdic = get_rupture_dict(arist.rupture_dict)
    if 'shakemap_array' in rupdic:
        del rupdic['shakemap_array']
    if arist.station_data_file is None:
        # NOTE: giving precedence to the station_data_file uploaded via form
        try:
            arist.station_data_file = download_station_data_file(
                arist.rupture_dict['usgs_id'])
        except HTTPError as exc:
            logging.info(f'Station data is not available: {exc}')
        except (KeyError, LookupError, UnicodeDecodeError,
                JSONDecodeError) as exc:
            logging.info(str(exc))
    rupture_file = rupdic.pop('rupture_file')
    if rupture_file:
        inputs['rupture_model'] = rupture_file
    if arist.station_data_file:
        inputs['station_data'] = arist.station_data_file
    if not arist.mosaic_model:
        lon, lat = rupdic['lon'], rupdic['lat']
        mosaic_models = get_close_mosaic_models(lon, lat, 5)
        # NOTE: using the first mosaic model
        arist.mosaic_model = mosaic_models[0]
        if len(mosaic_models) > 1:
            logging.info('Using the "%s" model' % arist.mosaic_model)

    if arist.trt is None:
        # NOTE: using the first tectonic region type
        arist.trt = get_trts_around(arist.mosaic_model, arist.exposure_hdf5)[0]
    params = dict(
        calculation_mode='scenario_risk',
        rupture_dict=str(rupdic),
        time_event=arist.time_event,
        maximum_distance=str(arist.maximum_distance),
        mosaic_model=arist.mosaic_model,
        tectonic_region_type=arist.trt,
        truncation_level=str(arist.truncation_level),
        number_of_ground_motion_fields=str(arist.number_of_ground_motion_fields),
        asset_hazard_distance=str(arist.asset_hazard_distance),
        ses_seed=str(arist.ses_seed),
        inputs=inputs)
    if arist.local_timestamp is not None:
        params['local_timestamp'] = arist.local_timestamp
    if arist.maximum_distance_stations is not None:
        params['maximum_distance_stations'] = str(arist.maximum_distance_stations)
    oq = readinput.get_oqparam(params)
    # NB: fake h5 to cache `get_site_model` and avoid multiple associations
    _sitecol, assetcol, _discarded, _exp = readinput.get_sitecol_assetcol(
        oq, h5={'performance_data': hdf5.FakeDataset()})
    id0s = numpy.unique(assetcol['ID_0'])
    countries = set(assetcol.tagcol.ID_0[i] for i in id0s)
    tmap_keys = get_tmap_keys(arist.exposure_hdf5, countries)
    if not tmap_keys:
        raise LookupError(f'No taxonomy mapping was found for {countries}')
    logging.root.handlers = []  # avoid breaking the logs
    params['description'] = (
        f'{rupdic["usgs_id"]} ({rupdic["lat"]}, {rupdic["lon"]})'
        f' M{rupdic["mag"]}')
    return params


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
             time_event='day',
             maximum_distance='300', mosaic_model=None, trt=None,
             truncation_level='3',
             number_of_ground_motion_fields='10', asset_hazard_distance='15',
             ses_seed='42',
             local_timestamp=None, exposure_hdf5=None, station_data_file=None,
             maximum_distance_stations=None):
    """
    This script is meant to be called from the command-line
    """
    if rupture_dict is None:
        rupture_dict = dict(usgs_id=usgs_id, rupture_file=rupture_file)
    try:
        arist = AristotleParam(
            rupture_dict, time_event, maximum_distance, mosaic_model,
            trt, truncation_level,
            number_of_ground_motion_fields, asset_hazard_distance,
            ses_seed, local_timestamp, exposure_hdf5, station_data_file,
            maximum_distance_stations)
        oqparams = get_aristotle_params(arist)
    except Exception as exc:
        callback(None, dict(usgs_id=usgs_id), exc=exc)
        return
    # in  testing mode create new job contexts
    user = getpass.getuser()
    [job] = engine.create_jobs([oqparams], 'warn', None, user, None)
    try:
        engine.run_jobs([job])
    except Exception as exc:
        callback(job.calc_id, oqparams, exc=exc)
    else:
        callback(job.calc_id, oqparams, exc=None)


main_cmd.usgs_id = 'ShakeMap ID'  # i.e. us6000m0xl
main_cmd.rupture_file = 'XML file with the rupture model (optional)'
main_cmd.rupture_dict = 'Used by the command `oq mosaic aristotle`'
main_cmd.callback = ''
main_cmd.time_event = 'Time of the event (avg, day, night or transit)'
main_cmd.maximum_distance = 'Maximum distance in km'
main_cmd.mosaic_model = 'Mosaic model 3-characters code (optional)'
main_cmd.trt = 'Tectonic region type'
main_cmd.truncation_level = 'Truncation level'
main_cmd.number_of_ground_motion_fields = 'Number of ground motion fields'
main_cmd.asset_hazard_distance = 'Asset hazard distance'
main_cmd.ses_seed = 'SES seed'
main_cmd.local_timestamp = 'Local timestamp of the event (optional)'
main_cmd.station_data_file = 'CSV file with the station data'
main_cmd.maximum_distance_stations = 'Maximum distance from stations in km'
main_cmd.exposure_hdf5 = ('File containing the exposure, site model '
                          'and vulnerability functions')

if __name__ == '__main__':
    sap.run(main_cmd)
