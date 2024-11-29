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

import logging
from urllib.error import HTTPError
from json.decoder import JSONDecodeError
from openquake.hazardlib import nrml, valid
from openquake.hazardlib import sourceconverter
from openquake.hazardlib.shakemap.parsers import (
    download_station_data_file, download_rup_rupdic)

ARISTOTLE_FORM_LABELS = {
    'usgs_id': 'Rupture identifier',
    'rupture_file_from_usgs': 'Rupture from USGS',
    'rupture_file': 'Rupture model XML',
    'lon': 'Longitude (degrees)',
    'lat': 'Latitude (degrees)',
    'dep': 'Depth (km)',
    'mag': 'Magnitude (Mw)',
    'rake': 'Rake (degrees)',
    'local_timestamp': 'Local timestamp of the event',
    'time_event': 'Time of the event',
    'dip': 'Dip (degrees)',
    'strike': 'Strike (degrees)',
    'maximum_distance': 'Maximum source-to-site distance (km)',
    'mosaic_model': 'Mosaic model',
    'trt': 'Tectonic region type',
    'truncation_level': 'Level of truncation',
    'number_of_ground_motion_fields': 'Number of ground motion fields',
    'asset_hazard_distance': 'Asset hazard distance (km)',
    'ses_seed': 'Random seed (ses_seed)',
    'station_data_file_from_usgs': 'Station data from USGS',
    'station_data_file': 'Station data CSV',
    'maximum_distance_stations': 'Maximum distance of stations (km)',
}

validators = {
    'usgs_id': valid.simple_id,
    'lon': valid.longitude,
    'lat': valid.latitude,
    'dep': valid.positivefloat,
    'mag': valid.positivefloat,
    'rake': valid.rake_range,
    'dip': valid.dip_range,
    'strike': valid.strike_range,
    'local_timestamp': valid.local_timestamp,
    # NOTE: 'avg' is used for probabilistic seismic risk, not for scenarios
    'time_event': valid.Choice('day', 'night', 'transit'),
    'maximum_distance': valid.positivefloat,
    'mosaic_model': valid.utf8,
    'trt': valid.utf8,
    'truncation_level': valid.positivefloat,
    'number_of_ground_motion_fields': valid.positiveint,
    'asset_hazard_distance': valid.positivefloat,
    'ses_seed': valid.positiveint,
    'maximum_distance_stations': valid.positivefloat,
}


def _validate(POST, rupture_path=None):
    validation_errs = {}
    invalid_inputs = []
    params = {}
    dic = dict(usgs_id=None, rupture_file=rupture_path, lon=None, lat=None,
               dep=None, mag=None, rake=None, dip=None, strike=None)
    for fieldname, validation_func in validators.items():
        if fieldname not in POST:
            continue
        try:
            value = validation_func(POST.get(fieldname))
        except Exception as exc:
            blankable_fields = ['maximum_distance_stations', 'dip', 'strike',
                                'local_timestamp']
            # NOTE: valid.positivefloat, valid_dip_range and
            #       valid_strike_range raise errors if their
            #       value is blank or None
            if (fieldname in blankable_fields and
                    POST.get(fieldname) == ''):
                if fieldname in dic:
                    dic[fieldname] = None
                else:
                    params[fieldname] = None
                continue
            validation_errs[ARISTOTLE_FORM_LABELS[fieldname]] = str(exc)
            invalid_inputs.append(fieldname)
            continue
        if fieldname in dic:
            dic[fieldname] = value
        else:
            params[fieldname] = value

    if 'is_point_rup' in POST:
        dic['is_point_rup'] = POST['is_point_rup'] == 'true'

    if validation_errs:
        err_msg = 'Invalid input value'
        err_msg += 's\n' if len(validation_errs) > 1 else '\n'
        err_msg += '\n'.join(
            [f'{field.split(" (")[0]}: "{validation_errs[field]}"'
             for field in validation_errs])
        logging.error(err_msg)
        err = {"status": "failed", "error_msg": err_msg,
               "invalid_inputs": invalid_inputs}
    else:
        err = {}
    return dic, params, err


def aristotle_validate(POST, rupture_path=None, station_data_path=None, datadir=None):
    """
    This is called by `aristotle_get_rupture_data` and `aristotle_run`.
    In the first case the form contains only usgs_id and rupture_file and
    returns (rup, rupdic, [station_file], error).
    In the second case the form contains all fields and returns
    (rup, rupdic, params, error).
    """
    dic, params, err = _validate(POST, rupture_path)
    if err:
        return None, {}, [], err
    try:

        usgs_id = dic['usgs_id']
        rupture_file = dic['rupture_file']
        if rupture_file:
            [rup_node] = nrml.read(rupture_file)
            conv = sourceconverter.RuptureConverter(rupture_mesh_spacing=5.)
            rup = conv.convert_node(rup_node)
            rup.tectonic_region_type = '*'
            hp = rup.hypocenter
            rup, rupdic = None, dict(lon=hp.x, lat=hp.y, dep=hp.z,
                                     mag=rup.mag, rake=rup.rake,
                                     strike=rup.surface.get_strike(),
                                     dip=rup.surface.get_dip(),
                                     usgs_id=usgs_id,
                                     rupture_file=rupture_file)
        else:
            rup, rupdic = download_rup_rupdic(usgs_id, datadir)

    except Exception as exc:
        logging.error('', exc_info=True)
        msg = f'Unable to retrieve rupture data: {str(exc)}'
        # signs '<>' would not be properly rendered in the popup notification
        msg = msg.replace('<', '"').replace('>', '"')
        return None, {}, [], {"status": "failed", "error_msg": msg,
                              "error_cls": type(exc).__name__}

    if station_data_path is not None:
        # giving precedence to the user-uploaded station data file
        params['station_data_file'] = station_data_path
    elif POST.get('station_data_file_from_usgs'):
        params['station_data_file'] = POST.get(
            'station_data_file_from_usgs')
    else:
        try:
            station_data_file = download_station_data_file(dic['usgs_id'], datadir)
        except HTTPError as exc:
            logging.info(f'Station data is not available: {exc}')
            params['station_data_file'] = None
        except (KeyError, LookupError, UnicodeDecodeError,
                JSONDecodeError) as exc:
            logging.info(str(exc))
            # NOTE: saving the error instead of the file path, then we need to
            # check if that is a file or not
            params['station_data_file'] = str(exc)
        else:
            params['station_data_file'] = station_data_file
    return rup, rupdic, list(params.values()), {}
