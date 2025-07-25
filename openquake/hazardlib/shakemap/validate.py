# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025, GEM Foundation
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

from openquake.baselib import config, general, hdf5, performance
from openquake.hazardlib import valid
from openquake.commonlib import readinput
from openquake.commonlib.calc import get_close_mosaic_models
from openquake.hazardlib.shakemap.parsers import get_rup_dic
from openquake.qa_tests_data import mosaic
from openquake.hazardlib.geo.utils import SiteAssociationError
from openquake.hazardlib.scalerel import get_available_magnitude_scalerel
from openquake.hazardlib.nrml import validators as nrml_validators

MOSAIC_DIR = config.directory.mosaic_dir or os.path.dirname(mosaic.__file__)


@dataclass
class AristotleParam:
    rupture_dict: dict
    time_event: str
    maximum_distance: float
    truncation_level: float
    number_of_ground_motion_fields: int
    asset_hazard_distance: float
    ses_seed: int
    local_timestamp: str = None
    rupture_file: str = None
    station_data_file: str = None
    mmi_file: str = None
    maximum_distance_stations: float = None
    mosaic_model: str = None
    trt: str = None
    description: str = None

    def get_oqparams(self, usgs_id, mosaic_models, trts, use_shakemap):
        """
        :returns: job_ini dictionary
        """
        if not hasattr(self, 'exposure_hdf5'):
            self.exposure_hdf5 = os.path.join(MOSAIC_DIR, 'exposure.hdf5')
        inputs = {'exposure': [self.exposure_hdf5], 'job_ini': '<in-memory>'}
        rupdic = self.rupture_dict
        if (not self.rupture_file and 'rupture_file' in rupdic
                and rupdic['rupture_was_loaded']):
            self.rupture_file = rupdic['rupture_file']
        if self.rupture_file:
            inputs['rupture_model'] = self.rupture_file
        if self.station_data_file:
            inputs['station_data'] = self.station_data_file
        if self.mmi_file:
            inputs['mmi'] = self.mmi_file
        if not self.mosaic_model:
            self.mosaic_model = mosaic_models[0]
            if len(mosaic_models) > 1:
                logging.info('Using the "%s" model' % self.mosaic_model)

        if not self.trt:
            # NOTE: using the first tectonic region type
            self.trt = next(iter(trts[self.mosaic_model]))
        shakemap_array = rupdic.pop('shakemap_array', ())
        params = dict(
            description=self.description,
            calculation_mode='scenario_risk',
            rupture_dict=str(rupdic),
            time_event=self.time_event,
            maximum_distance=str(self.maximum_distance),
            mosaic_model=self.mosaic_model,
            tectonic_region_type=self.trt,
            truncation_level=str(self.truncation_level),
            number_of_ground_motion_fields=str(
                self.number_of_ground_motion_fields),
            asset_hazard_distance=str(self.asset_hazard_distance),
            ses_seed=str(self.ses_seed),
            inputs=inputs)
        if use_shakemap:
            fname = general.gettemp(suffix='.npy')
            numpy.save(fname, shakemap_array)
            params['shakemap_uri'] = str(dict(kind='file_npy', fname=fname))
            params['gsim'] = '[FromFile]'
        if self.local_timestamp is not None:
            params['local_timestamp'] = self.local_timestamp
        if self.maximum_distance_stations is not None:
            params['maximum_distance_stations'] = str(
                self.maximum_distance_stations)
        if not params['description']:
            if 'title' in rupdic:
                params['description'] = (
                    f'{rupdic["usgs_id"]}: {rupdic["title"]}')
            else:
                params['description'] = (
                    f'{rupdic["usgs_id"]}: M {rupdic["mag"]}'
                    f' ({rupdic["lat"]}, {rupdic["lon"]})')
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
        return params


IMPACT_FORM_LABELS = {
    'usgs_id': 'Rupture identifier',
    'rupture_from_usgs': 'Rupture from USGS',
    'rupture_file': 'Rupture model XML',
    'use_shakemap': 'Use the ShakeMap',
    'shakemap_version': 'ShakeMap version',
    'lon': 'Longitude (degrees)',
    'lat': 'Latitude (degrees)',
    'dep': 'Depth (km)',
    'mag': 'Magnitude (Mw)',
    'aspect_ratio': 'Aspect ratio',
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
    'nodal_plane': 'Nodal plane',
    'msr': 'Magnitude scaling relationship',
    'description': 'Description',
}

IMPACT_FORM_PLACEHOLDERS = {
    'usgs_id': 'USGS ID or custom',
    'rupture_from_usgs': '',
    'rupture_file': 'Rupture model XML',
    'lon': '-180 ≤ float ≤ 180',
    'lat': '-90 ≤ float ≤ 90',
    'dep': 'float ≥ 0',
    'mag': 'float ≥ 0',
    'aspect_ratio': 'float ≥ 0',
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
    'nodal_plane': '',
    'msr': '',
    'description': 'Leave blank to set automatically',
}

IMPACT_FORM_DEFAULTS = {
    'usgs_id': '',
    'rupture_from_usgs': '',
    'rupture_file': '',
    'lon': '',
    'lat': '',
    'dep': '',
    'mag': '',
    'aspect_ratio': '2',
    'rake': '',
    'local_timestamp': '',
    'time_event': 'day',
    'dip': '90',
    'strike': '0',
    'maximum_distance': '300',
    'truncation_level': '3',
    'number_of_ground_motion_fields': '100',
    'asset_hazard_distance': '15',
    'ses_seed': '42',
    'station_data_file_from_usgs': '',
    'station_data_file': '',
    'maximum_distance_stations': '',
    'msr': 'WC1994',
    'rupture_was_loaded': '',
    'rupture_file_input': '',
    'station_data_file_input': '',
    'station_data_file_loaded': '',
    'description': '',
}

IMPACT_APPROACHES = {
    'use_shakemap_from_usgs': 'Use ShakeMap from the USGS',
    'use_pnt_rup_from_usgs': 'Use point rupture from the USGS',
    'build_rup_from_usgs': 'Build rupture from USGS nodal plane solutions',
    'use_shakemap_fault_rup_from_usgs': 'Use ShakeMap fault rupture from the USGS',
    'use_finite_fault_model_from_usgs': 'Use finite fault model from the USGS',
    'provide_rup': 'Provide earthquake rupture in OpenQuake NRML format',
    'provide_rup_params': 'Provide earthquake rupture parameters',
}


msr_choices = [msr.__class__.__name__ for msr in get_available_magnitude_scalerel()]

validators = {
    'approach': valid.Choice(*IMPACT_APPROACHES),
    'usgs_id': valid.simple_id,
    'lon': nrml_validators['lon'],
    'lat': nrml_validators['lat'],
    'dep': nrml_validators['depth'],
    'mag': nrml_validators['magnitude'],
    'msr': valid.Choice(*msr_choices),
    'aspect_ratio': nrml_validators['ruptAspectRatio'],
    'rake': nrml_validators['rake'],
    'dip': nrml_validators['dip'],
    'strike': nrml_validators['strike'],
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
    'description': valid.utf8,  # if empty, it will be set automatically
}


def _validate(POST):
    validation_errs = {}
    invalid_inputs = []
    params = {}
    inputdic = dict(approach=None, usgs_id=None, lon=None, lat=None, dep=None,
               mag=None, msr=None, aspect_ratio=None, rake=None, dip=None,
               strike=None, description=None)
    for field, validation_func in validators.items():
        if field not in POST:
            continue
        try:
            value = validation_func(POST.get(field))
        except Exception as exc:
            blankable = ['dip', 'strike', 'maximum_distance_stations',
                         'local_timestamp']
            if field in blankable and POST.get(field) == '':
                if field in inputdic:
                    inputdic[field] = None
                else:
                    params[field] = None
                continue
            validation_errs[IMPACT_FORM_LABELS[field]] = str(exc)
            invalid_inputs.append(field)
            continue
        if field in inputdic:
            inputdic[field] = value
        else:
            params[field] = value

    if validation_errs:
        err_msg = 'Invalid input value'
        err_msg += 's\n' if len(validation_errs) > 1 else '\n'
        err_msg += '\n'.join(
            [f'{field.split(" (")[0]}: "{validation_errs[field]}"'
             for field in validation_errs])
        err = {"status": "failed", "error_msg": err_msg,
               "invalid_inputs": invalid_inputs}
    else:
        err = {}
    return inputdic, params, err


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


def impact_validate(POST, user, rupture_file=None, station_data_file=None,
                    monitor=performance.Monitor()):
    """
    This is called by `impact_get_rupture_data` and `impact_run`.
    In the first case the form contains only usgs_id and rupture_file and
    returns (rup, rupdic, [station_file], error).
    In the second case the form contains all fields and returns
    (rup, rupdic, params, error).
    """
    err = {}
    inputdic, params, err = _validate(POST)
    if err:
        return None, inputdic, params, err

    # NOTE: in level 1 interface the ShakeMap has to be used.
    #       in level 2 interface it depends from the selected approach
    if user.level == 1:
        inputdic['approach'] = 'use_shakemap_from_usgs'
    else:
        inputdic['approach'] = POST['approach']
    use_shakemap = user.level == 1
    if 'use_shakemap' in POST:
        use_shakemap = POST['use_shakemap'] == 'true'
    if 'shakemap_version' in POST:
        shakemap_version = POST['shakemap_version']
    else:
        shakemap_version = 'usgs_preferred'

    rup, rupdic, err = get_rup_dic(
        inputdic, user, use_shakemap, shakemap_version, rupture_file, monitor)
    if err:
        return None, None, None, err
    # round floats
    for k, v in rupdic.items():
        if isinstance(v, float):  # lon, lat, dep, strike, dip
            rupdic[k] = round(v, 5)

    trts = {}
    expo = getattr(AristotleParam, 'exposure_hdf5',
                   os.path.join(MOSAIC_DIR, 'exposure.hdf5'))
    with monitor('get_close_mosaic_models'):
        mosaic_models = get_close_mosaic_models(rupdic['lon'], rupdic['lat'], 5)
    for mosaic_model in mosaic_models:
        trts[mosaic_model] = get_trts_around(mosaic_model, expo)
    rupdic['trts'] = trts
    rupdic['mosaic_models'] = mosaic_models
    rupdic['rupture_from_usgs'] = rupture_file
    rupdic['rupture_was_loaded'] = rup is not None
    if 'description' in inputdic and inputdic['description']:
        params['description'] = inputdic['description']
    if len(params) > 1:  # called by impact_run
        params['rupture_dict'] = rupdic
        params['station_data_file'] = station_data_file
        params['mmi_file'] = rupdic.get('mmi_file')
        with monitor('get_oqparams'):
            ap = AristotleParam(**params)
            try:
                oqparams = ap.get_oqparams(
                    inputdic['usgs_id'], mosaic_models, trts, use_shakemap)
            except SiteAssociationError as exc:
                oqparams = None
                err = {"status": "failed", "error_msg": str(exc)}
        return rup, rupdic, oqparams, err
    else:  # called by impact_get_rupture_data
        return rup, rupdic, params, err
