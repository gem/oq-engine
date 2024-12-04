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

import os
import logging
from dataclasses import dataclass
import numpy

from openquake.baselib import config, hdf5
from openquake.hazardlib import valid
from openquake.commonlib import readinput
from openquake.commonlib.calc import get_close_mosaic_models
from openquake.hazardlib.shakemap.parsers import get_rup_dic
from openquake.qa_tests_data import mosaic


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
    rupture_file: str = None
    station_data_file: str = None
    maximum_distance_stations: float = None

    def get_params(self):
        """
        :returns: job_ini dictionary
        """
        if self.exposure_hdf5 is None:
            self.exposure_hdf5 = os.path.join(
                config.directory.mosaic_dir, 'exposure.hdf5')
        inputs = {'exposure': [self.exposure_hdf5], 'job_ini': '<in-memory>'}
        rupdic = self.rupture_dict
        if 'shakemap_array' in rupdic:
            del rupdic['shakemap_array']
        if self.rupture_file:
            inputs['rupture_model'] = self.rupture_file
        if self.station_data_file:
            inputs['station_data'] = self.station_data_file
        if not self.mosaic_model:
            lon, lat = rupdic['lon'], rupdic['lat']
            mosaic_models = get_close_mosaic_models(lon, lat, 5)
            # NOTE: using the first mosaic model
            self.mosaic_model = mosaic_models[0]
            if len(mosaic_models) > 1:
                logging.info('Using the "%s" model' % self.mosaic_model)

        if self.trt is None:
            # NOTE: using the first tectonic region type
            self.trt = get_trts_around(self.mosaic_model, self.exposure_hdf5)[0]
        params = dict(
            calculation_mode='scenario_risk',
            rupture_dict=str(rupdic),
            time_event=self.time_event,
            maximum_distance=str(self.maximum_distance),
            mosaic_model=self.mosaic_model,
            tectonic_region_type=self.trt,
            truncation_level=str(self.truncation_level),
            number_of_ground_motion_fields=str(self.number_of_ground_motion_fields),
            asset_hazard_distance=str(self.asset_hazard_distance),
            ses_seed=str(self.ses_seed),
            inputs=inputs)
        if self.local_timestamp is not None:
            params['local_timestamp'] = self.local_timestamp
        if self.maximum_distance_stations is not None:
            params['maximum_distance_stations'] = str(self.maximum_distance_stations)
        oq = readinput.get_oqparam(params)
        # NB: fake h5 to cache `get_site_model` and avoid multiple associations
        _sitecol, assetcol, _discarded, _exp = readinput.get_sitecol_assetcol(
            oq, h5={'performance_data': hdf5.FakeDataset()})
        id0s = numpy.unique(assetcol['ID_0'])
        countries = set(assetcol.tagcol.ID_0[i] for i in id0s)
        tmap_keys = get_tmap_keys(self.exposure_hdf5, countries)
        if not tmap_keys:
            raise LookupError(f'No taxonomy mapping was found for {countries}')
        logging.root.handlers = []  # avoid breaking the logs
        params['description'] = (
            f'{rupdic["usgs_id"]} ({rupdic["lat"]}, {rupdic["lon"]})'
            f' M{rupdic["mag"]}')
        return params


ARISTOTLE_FORM_LABELS = {
    'usgs_id': 'Rupture identifier',
    'rupture_from_usgs': 'Rupture from USGS',
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

ARISTOTLE_FORM_PLACEHOLDERS = {
    'usgs_id': 'USGS ID or custom',
    'rupture_from_usgs': '',
    'rupture_file': 'Rupture model XML',
    'lon': '-180 ≤ float ≤ 180',
    'lat': '-90 ≤ float ≤ 90',
    'dep': 'float ≥ 0',
    'mag': 'float ≥ 0',
    'rake': '-180 ≤ float ≤ 180',
    'local_timestamp': '',
    'time_event': 'day|night|transit',
    'dip': '0 ≤ float ≤ 90',
    'strike': '0 ≤ float ≤ 360',
    'maximum_distance': 'float ≥ 0',
    'mosaic_model': 'Mosaic model',
    'trt': 'Tectonic region type',
    'truncation_level': 'float ≥ 0',
    'number_of_ground_motion_fields': 'float ≥ 1',
    'asset_hazard_distance': 'float ≥ 0',
    'ses_seed': 'int ≥ 0',
    'station_data_file_from_usgs': '',
    'station_data_file': 'Station data CSV',
    'maximum_distance_stations': 'float ≥ 0',
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


def _validate(POST):
    validation_errs = {}
    invalid_inputs = []
    params = {}
    dic = dict(usgs_id=None, lon=None, lat=None, dep=None,
               mag=None, rake=None, dip=None, strike=None)
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


def aristotle_validate(POST, rupture_file=None, station_data_file=None, datadir=None):
    """
    This is called by `aristotle_get_rupture_data` and `aristotle_run`.
    In the first case the form contains only usgs_id and rupture_file and
    returns (rup, rupdic, [station_file], error).
    In the second case the form contains all fields and returns
    (rup, rupdic, params, error).
    """
    dic, params, err = _validate(POST)
    if err:
        breakpoint()
        return None, dic, params, err
    try:
        rup, rupdic = get_rup_dic(dic['usgs_id'], datadir,
                                  rupture_file, station_data_file)
    except Exception as exc:
        # FIXME: not tested
        logging.error('', exc_info=True)
        msg = f'Unable to retrieve rupture data: {str(exc)}'
        # signs '<>' would not be properly rendered in the popup notification
        msg = msg.replace('<', '"').replace('>', '"')
        return None, {}, params, {"status": "failed", "error_msg": msg,
                                  "error_cls": type(exc).__name__}
    # round floats
    for k, v in rupdic.items():
        if isinstance(v, float):  # lon, lat, dep, strike, dip
            rupdic[k] = round(v, 5)

    issue = rupdic.get('station_data_issue')
    if issue:
        err['station_data_issue'] = issue
    trts = {}
    mosaic_models = get_close_mosaic_models(rupdic['lon'], rupdic['lat'], 5)
    mosaic_dir = config.directory.mosaic_dir or os.path.dirname(mosaic.__file__)
    for mosaic_model in mosaic_models:
        trts[mosaic_model] = get_trts_around(
            mosaic_model, os.path.join(mosaic_dir, 'exposure.hdf5'))
    rupdic['trts'] = trts
    rupdic['mosaic_models'] = mosaic_models
    rupdic['rupture_from_usgs'] = rup is not None
    if len(params) > 1:  # called by aristotle_run
        params['rupture_dict'] = rupdic
        params['station_data_file'] = rupdic['station_data_file']
        return rup, rupdic, AristotleParam(**params).get_params(), err
    else:  # called by aristotle_get_rupture_data
        return rup, rupdic, params, err
