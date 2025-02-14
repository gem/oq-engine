# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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
A converter from Shakemap files (see
https://earthquake.usgs.gov/scenario/product/shakemap-scenario/sclegacyshakeout2full_se/us/1465655085705/about_formats.html)
to numpy composite arrays.
"""

from urllib.request import urlopen, pathname2url
from urllib.error import URLError
from collections import defaultdict
from xml.parsers.expat import ExpatError
import io
import os
import pathlib
import logging
import json
import zipfile
import base64
from dataclasses import dataclass
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from shapely.geometry import Polygon
import numpy

from openquake.baselib import performance
from openquake.baselib.general import gettemp
from openquake.baselib.node import node_from_xml
from openquake.hazardlib import nrml, sourceconverter
from openquake.hazardlib.source.rupture import (
    get_multiplanar, is_matrix, build_planar_rupture_from_dict)
from openquake.hazardlib.scalerel import get_available_magnitude_scalerel

NOT_FOUND = 'No file with extension \'.%s\' file found'
US_GOV = 'https://earthquake.usgs.gov'
SHAKEMAP_URL = US_GOV + '/fdsnws/event/1/query?eventid={}&format=geojson'
F32 = numpy.float32
SHAKEMAP_FIELDS = set(
    'LON LAT SVEL MMI PGA PSA03 PSA06 PSA10 PSA30 '
    'STDMMI STDPGA STDPSA03 STDPSA06 STDPSA10 STDPSA30'
    .split())
FIELDMAP = {
    'LON': 'lon',
    'LAT': 'lat',
    'SVEL': 'vs30',
    'MMI': ('val', 'MMI'),
    'PGA': ('val', 'PGA'),
    'PSA03': ('val', 'SA(0.3)'),
    'PSA06': ('val', 'SA(0.6)'),
    'PSA10': ('val', 'SA(1.0)'),
    'PSA30': ('val', 'SA(3.0)'),
    'STDMMI': ('std', 'MMI'),
    'STDPGA': ('std', 'PGA'),
    'STDPSA03': ('std', 'SA(0.3)'),
    'STDPSA06': ('std', 'SA(0.6)'),
    'STDPSA10': ('std', 'SA(1.0)'),
    'STDPSA30': ('std', 'SA(3.0)'),
}
REQUIRED_IMTS = {'PGA', 'PSA03', 'PSA10'}


@dataclass
class User:
    level: int = 0
    testdir: str = ''


class MissingLink(Exception):
    """Could not find link in web page"""


def urlextract(url, fname):
    """
    Download and unzip an archive and extract the underlying fname
    """
    if not url.endswith('.zip'):
        return urlopen(url)
    with urlopen(url) as f:
        data = io.BytesIO(f.read())
    with zipfile.ZipFile(data) as z:
        for zinfo in z.filelist:
            if zinfo.filename.endswith(fname):
                return z.open(zinfo)
        raise FileNotFoundError


def path2url(url):
    """
    If a relative path is given for the file, parse it so it can be
    read with 'urlopen'.
    :param url: path/url to be parsed
    """
    if not url.startswith('file:') and not url.startswith('http'):
        file = pathlib.Path(url)
        if file.is_file():
            return 'file:{}'.format(pathname2url(str(file.absolute())))
        raise FileNotFoundError(
            'The following path could not be found: %s' % url)
    return url


def get_array(**kw):
    """
    :param kw: a dictionary with a key 'kind' and various parameters
    :returs: ShakeMap as a numpy array, dowloaded or read in various ways
    """
    kind = kw['kind']
    if kind == 'shapefile':
        return get_array_shapefile(kind, kw['fname'])
    elif kind == 'usgs_xml':
        return get_array_usgs_xml(kind, kw['grid_url'],
                                  kw.get('uncertainty_url'))
    elif kind == 'usgs_id':
        return get_array_usgs_id(kind, kw['id'])
    elif kind == 'file_npy':
        return get_array_file_npy(kind, kw['fname'])
    else:
        raise KeyError(kw)


def get_array_shapefile(kind, fname):
    """
    Download and parse data saved as a shapefile.
    :param fname: url or filepath for the shapefiles,
    either a zip or the location of one of the files,
    *.shp and *.dbf are necessary, *.prj and *.shx optional
    """
    import shapefile  # optional dependency
    fname = path2url(fname)

    extensions = ['shp', 'dbf', 'prj', 'shx']
    f_dict = {}

    if fname.endswith('.zip'):
        # files are saved in a zip
        for ext in extensions:
            try:
                f_dict[ext] = urlextract(fname, '.' + ext)
            except FileNotFoundError:
                f_dict[ext] = None
                logging.warning(NOT_FOUND, ext)
    else:
        # files are saved as plain files
        fname = os.path.splitext(fname)[0]
        for ext in extensions:
            try:
                f_dict[ext] = urlopen(fname + '.' + ext)
            except URLError:
                f_dict[ext] = None
                logging.warning(NOT_FOUND, ext)

    polygons = []
    data = defaultdict(list)

    try:
        sf = shapefile.Reader(**f_dict)
        fieldnames = [f[0].upper() for f in sf.fields[1:]]

        for rec in sf.shapeRecords():
            # save shapes as polygons
            polygons.append(Polygon(rec.shape.points))
            # create dict of lists from data
            for k, v in zip(fieldnames, rec.record):
                data[k].append(v)
            # append bounding box for later use
            data['bbox'].append(polygons[-1].bounds)
    except shapefile.ShapefileException as e:
        raise shapefile.ShapefileException(
            'Necessary *.shp and/or *.dbf file not found.') from e

    return get_shapefile_arrays(polygons, data)


def get_array_usgs_xml(kind, grid_url, uncertainty_url=None):
    """
    Read a ShakeMap in XML format from the local file system
    """
    try:
        grid_url = path2url(grid_url)
        if uncertainty_url is None:
            if grid_url.endswith('.zip'):
                # see if both are in the same file, naming must be correct
                try:
                    with urlextract(grid_url, 'grid.xml') as f1, urlextract(
                            path2url(grid_url),
                            'uncertainty.xml') as f2:
                        return get_shakemap_array(f1, f2)
                except FileNotFoundError:
                    pass

            # if not just return the grid and log a warning
            logging.warning(
                'No Uncertainty grid found, please check your input files.')
            with urlextract(grid_url, '.xml') as f:
                return get_shakemap_array(f)

        # both files present, return them both
        with urlextract(grid_url, '.xml') as f1, urlextract(
                path2url(uncertainty_url), '.xml') as f2:
            return get_shakemap_array(f1, f2)

    except FileNotFoundError as e:
        raise FileNotFoundError(
            'USGS xml grid file could not be found at %s' % grid_url) from e


def convert_to_oq_rupture(rup_json):
    """
    Convert USGS json (output of download_rupture_data) into an hazardlib rupture

    :returns: None if not convertible
    """
    ftype = rup_json['features'][0]['geometry']['type']
    multicoords = rup_json['features'][0]['geometry']['coordinates'][0]
    if (ftype == 'MultiPolygon' and is_matrix(multicoords) and len(multicoords[0]) == 5
            and multicoords[0][0] == multicoords[0][4]):
        # convert only if there are 4 vertices (the fifth coordinate closes the loop)
        hyp_depth = rup_json['metadata']['depth']
        rake = rup_json['metadata'].get('rake', 0)
        trt = 'Active Shallow Crust' if hyp_depth < 50 else 'Subduction IntraSlab'
        mag = rup_json['metadata']['mag']
        rup = get_multiplanar(multicoords, mag, rake, trt)
        return rup


def utc_to_local_time(utc_timestamp, lon, lat):
    """
    Convert a timestamp '%Y-%m-%dT%H:%M:%S.%fZ' into a datetime object
    """
    try:
        # NOTE: mandatory dependency for ARISTOTLE
        from timezonefinder import TimezoneFinder
    except ImportError:
        raise ImportError(
            'The python package "timezonefinder" is not installed. It is'
            ' required in order to convert the UTC time to the local time of'
            ' the event. You can install it from'
            ' https://wheelhouse.openquake.org/v3/linux/ choosing the one'
            ' corresponding to the installed python version.')
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str is None:
        logging.warning(
            'Could not determine the timezone. Using the UTC time')
        return utc_timestamp
    utc_time = datetime.strptime(utc_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    local_timestamp = utc_time.astimezone(ZoneInfo(timezone_str))
    # NOTE: the validated timestamp format has no microseconds
    return local_timestamp.replace(microsecond=0)


def local_time_to_time_event(local_time):
    if 9 <= local_time.hour < 17:
        return 'day'
    if local_time.hour >= 21 or local_time.hour < 5:
        return 'night'
    return 'transit'


def read_usgs_stations_json(js: bytes):
    # tested in validate_test.py
    try:
        stations_json_str = js.decode('utf8')
    except UnicodeDecodeError:
        # not tested yet
        stations_json_str = js.decode('latin1')
    sj = json.loads(stations_json_str)
    if 'features' not in sj or not sj['features']:
        # tested in validate_test.py #4
        return []
    stations = pd.json_normalize(sj, 'features')
    try:
        stations['eventid'] = sj['metadata']['eventid']
    except KeyError:
        # the eventid is not essential
        pass
    # Rename columns
    stations.columns = [
        col.replace('properties.', '') for col in stations.columns]
    # Extract lon and lat
    stations[['lon', 'lat']] = pd.DataFrame(
        stations['geometry.coordinates'].to_list())
    # Get values for available IMTs (PGA and SA)
    # ==========================================
    # The "channels/amplitudes" dictionary contains the values recorded at
    # the seismic stations. The values could report the 3 components, in such
    # cases, take the componet with maximum PGA (and in absence of PGA, the
    # first IM reported).
    channels = pd.DataFrame(stations.channels.to_list())
    vals = pd.Series([], dtype='object')
    for row, rec_station in channels.iterrows():
        rec_station.dropna(inplace=True)
        # Iterate over different columns. Each colum can be a component
        data = []
        pgas = []
        for _, chan in rec_station.items():
            if chan["name"].endswith("Z") or chan["name"].endswith("U"):
                continue
            # logging.info(chan["name"])
            df = pd.DataFrame(chan["amplitudes"])
            if 'pga' in df.name.unique():
                pga = df.loc[df['name'] == 'pga', 'value'].values[0]
            else:
                pga = df['value'][0]
            if pga is None or pga == "null":
                continue
            if isinstance(pga, str):
                pga = float(pga)
            pgas.append(pga)
            data.append(chan["amplitudes"])
        # get values for maximum component
        if pgas:
            max_componet = pgas.index(max(pgas))
            vals[row] = data[max_componet]
        else:
            vals[row] = None
    # The "pgm_from_mmi" dictionary contains the values estimated from MMI.
    # Combine both dictionaries to extract the values.
    # They are generally mutually exclusive (if mixed, the priority is given
    # to the station recorded data).
    try:
        # Some events might not have macroseismic data, then skip them
        vals = vals.combine_first(stations['pgm_from_mmi']).apply(pd.Series)
    except Exception:
        vals = vals.apply(pd.Series)
    # Arrange columns since the data can include mixed positions for the IMTs
    values = pd.DataFrame()
    for col in vals.columns:
        df = vals[col].apply(pd.Series)
        df.set_index(['name'], append=True, inplace=True)
        df.drop(columns=['flag', 'units'], inplace=True)
        if 0 in df.columns:
            df.drop(columns=[0], inplace=True)
        df = df.unstack('name')
        df.dropna(axis=1, how='all', inplace=True)
        df.columns = [col[1]+'_'+col[0] for col in df.columns.values]
        for col in df.columns:
            if col in values:
                # Colum already exist. Combine values in unique column
                values[col] = values[col].combine_first(df[col])
            else:
                values = pd.concat([values, df[col]], axis=1)
    values.sort_index(axis=1, inplace=True)
    # Add recording to main DataFrame
    stations = pd.concat([stations, values], axis=1)
    return stations


def usgs_to_ecd_format(stations, exclude_imts=()):
    '''
    Adjust USGS format to match the ECD (Earthquake Consequence Database)
    format
    '''
    # Adjust column names to match format
    stations.columns = stations.columns.str.upper()
    stations.rename(columns={
        'CODE': 'STATION_ID',
        'NAME': 'STATION_NAME',
        'LON': 'LONGITUDE',
        'LAT': 'LATITUDE',
        'INTENSITY': 'MMI_VALUE',
        'INTENSITY_STDDEV': 'MMI_STDDEV',
        }, inplace=True)
    # Identify columns for IMTs:
    imts = []
    for col in stations.columns:
        if 'DISTANCE_STDDEV' == col:
            continue
        if '_VALUE' in col or '_LN_SIGMA' in col or '_STDDEV' in col:
            for imt in exclude_imts:
                if imt in col:
                    break
            else:
                imts.append(col)
    # Identify relevant columns
    cols = ['STATION_ID', 'STATION_NAME', 'LONGITUDE', 'LATITUDE',
            'STATION_TYPE', 'VS30'] + imts
    df = stations[cols].copy()
    # Add missing columns
    df.loc[:, 'VS30_TYPE'] = 'inferred'
    df.loc[:, 'REFERENCES'] = 'Stations_USGS'
    # Adjust PGA and SA untis to [g]. USGS uses [% g]
    adj_cols = [imt for imt in imts
                if '_VALUE' in imt and
                'PGV' not in imt and
                'MMI' not in imt]
    df.loc[:, adj_cols] = round(df.loc[:, adj_cols].
                                apply(pd.to_numeric, errors='coerce') / 100, 6)
    df_seismic = df[df['STATION_TYPE'] == 'seismic']
    df_seismic_non_null = df_seismic.dropna()
    return df_seismic_non_null


def _get_preferred_item(items):
    # items can be for instance shakemaps, moment tensors or finite faults
    preferred_weights = [item['preferredWeight'] for item in items]
    preferred_idxs = [idx for idx, val in enumerate(preferred_weights)
                      if val == max(preferred_weights)]
    preferred_items = [items[idx] for idx in preferred_idxs]
    if len(preferred_items) > 1:
        update_times = [item['updateTime'] for item in preferred_items]
        latest_idx = update_times.index(max(update_times))
        item = preferred_items[latest_idx]
    else:
        item = preferred_items[0]
    return item


def download_station_data_file(usgs_id, contents, user):
    """
    Download station data from the USGS site given a ShakeMap ID.

    :param usgs_id: ShakeMap ID
    :returns: (path_to_csv, error)
    """
    if 'download/stationlist.json' in contents:
        stationlist_url = contents.get('download/stationlist.json')['url']
        # fname = os.path.join(user, f'{usgs_id}-stations.json')
        # with open(fname, 'wb') as f:
        #     f.write(urlopen(stationlist_url).read())
        if user.testdir:
            fname = os.path.join(user.testdir, f'{usgs_id}-stations.json')
            json_bytes = open(fname, 'rb').read()
        else:
            logging.info('Downloading stationlist.json')
            json_bytes = urlopen(stationlist_url).read()
        stations = read_usgs_stations_json(json_bytes)
        if len(stations) == 0:
            msg = 'stationlist.json was downloaded, but it contains no features'
            return None, msg
        original_len = len(stations)
        try:
            seismic_len = len(
                stations[stations['station_type'] == 'seismic'])
        except KeyError:
            msg = (f'{original_len} stations were found, but the'
                   f' "station_type" is not specified, so we can not'
                   f' identify the "seismic" stations.')
            return None, msg
        df = usgs_to_ecd_format(stations, exclude_imts=('SA(3.0)',))
        if len(df) < 1:
            if original_len > 1:
                if seismic_len > 1:
                    msg = (f'{original_len} stations were found, but the'
                           f' {seismic_len} seismic stations were all'
                           f' discarded')
                    return None, msg
                else:
                    msg = (f'{original_len} stations were found, but none'
                           f' of them are seismic')
                    return None, msg
            else:
                return None, 'No stations were found'
        else:
            station_data_file = gettemp(
                prefix='stations', suffix='.csv', remove=False)
            df.to_csv(station_data_file, encoding='utf8', index=False)
            return station_data_file, None


def load_rupdic_from_finite_fault(usgs_id, mag, products):
    """
    Extract the finite fault properties from products.
    NB: if the finite-fault list contains multiple elements we take the
    preferred one.
    """
    err = {}
    logging.info('Getting finite-fault properties')
    if 'finite-fault' not in products:
        # e.g. us6000phrk
        # FIXME: not tested
        err_msg = f'There is no finite-fault info for {usgs_id}'
        err = {"status": "failed", "error_msg": err_msg}
        return None, err
    ffs = products['finite-fault']
    ff = _get_preferred_item(ffs)
    p = ff['properties']
    # TODO: we probably need to get the rupture coordinates from shakemap_polygon.txt
    # if 'shakemap_polygon.txt' in ff['contents']:
    #     # with open(f'/tmp/{usgs_id}-shakemap_polygon.txt', 'wb') as f:
    #     #       f.write(urlopen(url).read())
    #     if user.testdir:  # in parsers_test
    #         fname = os.path.join(user.testdir, f'{usgs_id}-shakemap_polygon.txt')
    #         text = open(fname).read()
    #     else:
    #         url = ff['contents']['shakemap_polygon.txt']['url']
    #         logging.info('Downloading shakemap_polygon.txt')
    #         text = urlopen(url).read()
    #         lines = text.decode('utf8').split("\n")
    #         numerical_data = [line for line in lines
    #                           if line and not line.startswith("#")]
    #         coords = [tuple(map(float, line.split()))
    #                   for line in numerical_data if line]
    lon = float(p['longitude'])
    lat = float(p['latitude'])
    utc_time = p['eventtime']
    local_time = utc_to_local_time(utc_time, lon, lat)
    time_event = local_time_to_time_event(local_time)
    rupdic = {'lon': lon, 'lat': lat, 'dep': float(p['depth']),
              'mag': mag, 'rake': 0.,
              'local_timestamp': str(local_time), 'time_event': time_event,
              'require_dip_strike': True,
              'pga_map_png': None, 'mmi_map_png': None,
              'usgs_id': usgs_id, 'rupture_file': None}
    return rupdic, err


def load_rupdic_from_origin(usgs_id, products):
    """
    Extract the origin properties from products.
    NB: if the origin list contains multiple elements we take the
    preferred one.
    """
    # TODO: we may try to unify this with the very similar
    # load_rupdic_from_finite_fault
    err = {}
    logging.info('Getting origin properties')
    if 'origin' not in products:
        # FIXME: not tested
        err_msg = f'There is no origin info for {usgs_id}'
        err = {"status": "failed", "error_msg": err_msg}
        return None, err
    origins = products['origin']
    origin = _get_preferred_item(origins)
    p = origin['properties']
    mag = float(p['magnitude'])
    lon = float(p['longitude'])
    lat = float(p['latitude'])
    dep = float(p['depth'])
    rake = 0.
    utc_time = p['eventtime']
    local_time = utc_to_local_time(utc_time, lon, lat)
    time_event = local_time_to_time_event(local_time)
    rupdic = {'lon': lon, 'lat': lat, 'dep': dep,
              'mag': mag, 'rake': rake,
              'local_timestamp': str(local_time), 'time_event': time_event,
              'require_dip_strike': True,
              'pga_map_png': None, 'mmi_map_png': None,
              'usgs_id': usgs_id, 'rupture_file': None}
    return rupdic, err


# NB: not used right now
def get_shakemap_version(usgs_id):
    # USGS event page to get ShakeMap details
    product_url = US_GOV + f"/earthquakes/feed/v1.0/detail/{usgs_id}.geojson"
    # Get the JSON data for the earthquake event
    try:
        with urlopen(product_url) as response:
            event_data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error: Unable to fetch data for event {usgs_id} - {e}")
        return None
    if ("properties" in event_data and "products" in event_data["properties"] and
            "shakemap" in event_data["properties"]["products"]):
        shakemap_data = event_data["properties"]["products"]["shakemap"][0]
        # e.g.: 'https://earthquake.usgs.gov/product/shakemap/'
        #       'us7000n7n8/us/1726699735514/download/intensity.jpg'
        version_id = shakemap_data["contents"]["download/intensity.jpg"]["url"].split(
            '/')[-3]
        return version_id
    else:
        print(f"No ShakeMap found for event {usgs_id}")
        return None


# NB: not used
def download_jpg(usgs_id, what):
    """
    It can be used to download a jpg file from the USGS service, returning it in a
    base64 format that can be easily passed to a Django template
    """
    version_id = get_shakemap_version(usgs_id)
    if version_id:
        intensity_url = (f'{US_GOV}/product/shakemap/{usgs_id}/us/'
                         f'{version_id}/download/{what}.jpg')
        try:
            with urlopen(intensity_url) as img_response:
                img_data = img_response.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                return img_base64
        except Exception as e:
            print(f"Error: Unable to download the {what} image - {e}")
            return None
    else:
        print("Error: Could not retrieve the ShakeMap version ID.")
        return None


# NB: this is always available but sometimes the geometry is Point
# or a MultiPolygon not convertible to an engine rupture geometry
def download_rupture_data(usgs_id, shakemap_contents, user):
    """
    :returns: a JSON dictionary with a format like this:

{'features': [{'geometry': {'coordinates': [[[[22.93, 38.04, 0.0],
                                              [23.13, 38.06, 0.0],
                                              [23.11, 38.16, 12.0],
                                              [22.9, 38.14, 12.0],
                                              [22.93, 38.04, 0.0]]]],
                            'type': 'MultiPolygon'},
               'properties': {'rupture type': 'rupture extent'},
               'type': 'Feature'}],
 'metadata': {'depth': 33.0,
              'id': 'usp0001ccb',
              'lat': 38.222,
              'locstring': 'Greece',
              'lon': 22.934,
              'mag': 6.7,
              'mech': 'ALL',
              'netid': 'us',
              'network': 'USGS National Earthquake Information Center, PDE',
              'productcode': 'usp0001ccb',
              'rake': 0.0,
              'reference': 'Source: Strios, Psimoulis, and Pitharouli.  '
                           'Geodetic constraints to the kinematics of the '
                           'Kapareli fault, reactivated during the 1981, Gulf '
                           'of Corinth earthquakes. Tectonophysics Issue 440 '
                           'pp. 105-119. 2007.',
              'time': '1981-02-24T20:53:38.000000Z'},
 'type': 'FeatureCollection'}
    """
    rup_json = shakemap_contents.get('download/rupture.json')
    if rup_json is None:
        return None, None
    url = rup_json['url']
    # with open(f'/tmp/{usgs_id}-rup.json', 'wb') as f:
    #       f.write(urlopen(url).read())
    if user.testdir:  # in parsers_test
        fname = os.path.join(user.testdir, f'{usgs_id}-rup.json')
        text = open(fname).read()
    else:
        logging.info('Downloading rupture.json')
        text = urlopen(url).read()
    rup_data = json.loads(text)
    return rup_data, gettemp(text, prefix='rup_', suffix='.json')


def convert_rup_data(rup_data, usgs_id, rup_path, shakemap_array=None):
    """
    Convert JSON data coming from the USGS into a rupdic with keys
    lon, lat, dep, mag, rake, local_timestamp, require_dip_strike, shakemap,
    usgs_id, rupture_file
    """
    # geometry is Point for us7000n05d
    feats = rup_data['features']
    require_dip_strike = len(feats) == 1 and feats[0]['geometry']['type'] == 'Point'
    md = rup_data['metadata']
    lon = md['lon']
    lat = md['lat']
    utc_time = md['time']
    local_time = utc_to_local_time(utc_time, lon, lat)
    time_event = local_time_to_time_event(local_time)
    rupdic = {'lon': lon, 'lat': lat, 'dep': md['depth'],
              'mag': md['mag'], 'rake': md['rake'],
              'local_timestamp': str(local_time), 'time_event': time_event,
              'require_dip_strike': require_dip_strike,
              'shakemap_array': shakemap_array,
              'usgs_id': usgs_id, 'rupture_file': rup_path}
    return rupdic


def _contents_properties_shakemap(usgs_id, user, use_shakemap, monitor):
    # with open(f'/tmp/{usgs_id}.json', 'wb') as f:
    #     url = SHAKEMAP_URL.format(usgs_id)
    #     f.write(urlopen(url).read())
    err = {}
    if user.testdir:  # in parsers_test
        fname = os.path.join(user.testdir, usgs_id + '.json')
        text = open(fname).read()
    else:
        url = SHAKEMAP_URL.format(usgs_id)
        logging.info('Downloading %s' % url)
        try:
            with monitor('Downloading USGS json'):
                text = urlopen(url).read()
        except URLError as exc:
            # in parsers_test
            err_msg = f'Unable to download from {url}: {exc}'
            err = {"status": "failed", "error_msg": err_msg}
            return None, None, None, err

    js = json.loads(text)
    properties = js['properties']

    # NB: currently we cannot find a case with missing shakemap
    shakemap = _get_preferred_item(properties['products']['shakemap'])
    contents = shakemap['contents']

    if (user.level == 1 or use_shakemap) and 'download/grid.xml' in contents:
        # only for Aristotle users try to download the shakemap
        url = contents.get('download/grid.xml')['url']
        # grid_fname = gettemp(urlopen(url).read(), suffix='.xml')
        if user.testdir:  # in parsers_test
            grid_fname = f'{user.testdir}/{usgs_id}-grid.xml'
        else:
            logging.info('Downloading grid.xml')
            with monitor('Downloading grid.xml'):
                grid_fname = gettemp(urlopen(url).read(), suffix='.xml')
        shakemap_array = get_shakemap_array(grid_fname)
    else:
        shakemap_array = None
    return contents, properties, shakemap_array, err


def _get_nodal_planes(properties):
    # in parsers_test
    err = {}
    if 'moment-tensor' not in properties['products']:
        err = {'status': 'failed',
               'error_msg': 'Unable to retrieve information about the nodal options'}
        return None, err
    moment_tensor = _get_preferred_item(properties['products']['moment-tensor'])
    props = moment_tensor['properties']
    nodal_planes = {}
    for key, value in props.items():
        if key.startswith('nodal-plane-'):
            parts = key.split('-')
            plane = f'NP{parts[2]}'
            attr = parts[3]  # Get the attribute (i.e. 'dip', 'rake' or 'strike')
            if plane not in nodal_planes:
                nodal_planes[plane] = {}
            nodal_planes[plane][attr] = float(value)
    return nodal_planes, err


def _get_rup_dic_from_xml(usgs_id, user, rupture_file, station_data_file):
    err = {}
    try:
        [rup_node] = nrml.read(os.path.join(user.testdir, rupture_file)
                               if user.testdir else rupture_file)
    except ExpatError as exc:
        err = {"status": "failed", "error_msg": str(exc)}
        return None, {}, err
    rup = sourceconverter.RuptureConverter(
        rupture_mesh_spacing=5.).convert_node(rup_node)
    rup.tectonic_region_type = '*'
    hp = rup.hypocenter
    rupdic = dict(lon=hp.x, lat=hp.y, dep=hp.z,
                  mag=rup.mag, rake=rup.rake,
                  strike=rup.surface.get_strike(),
                  dip=rup.surface.get_dip(),
                  usgs_id=usgs_id,
                  rupture_file=rupture_file,
                  station_data_file=station_data_file)
    return rup, rupdic, err


def get_rup_dic(dic, user=User(), approach='use_shakemap_from_usgs',
                use_shakemap=False, rupture_file=None,
                station_data_file=None, monitor=performance.Monitor()):
    """
    If the rupture_file is None, download a rupture from the USGS site given
    the ShakeMap ID, else build the rupture locally with the given usgs_id.

    :param dic: dictionary with ShakeMap ID and other parameters
    :param user: User instance
    :param approach: the workflow selected by the user
        (default: 'use_shakemap_from_usgs')
    :param use_shakemap: download the ShakeMap only if True
    :param rupture_file: None
    :param station_data_file: None
    :returns: (rupture object or None, rupture dictionary, error dictionary or {})
    """
    rupdic = {}
    rup_data = {}
    err = {}
    usgs_id = dic['usgs_id']
    rup = None
    if approach == 'provide_rup_params':
        rupdic = dic.copy()
        rupdic.update(rupture_file=rupture_file,
                      station_data_file=station_data_file,
                      require_dip_strike=True)
        return rup, rupdic, err

    if rupture_file and rupture_file.endswith('.xml'):
        rup, rupdic, err = _get_rup_dic_from_xml(
            usgs_id, user, rupture_file, station_data_file)
        if err or usgs_id == 'FromFile':
            return rup, rupdic, err
    elif rupture_file and rupture_file.endswith('.json'):
        with open(rupture_file) as f:
            rup_data = json.load(f)
        if usgs_id == 'FromFile':
            rupdic = convert_rup_data(rup_data, usgs_id, rupture_file)
            rupdic['station_data_file'] = station_data_file
            rup = convert_to_oq_rupture(rup_data)
            return rup, rupdic, err

    assert usgs_id
    contents, properties, shakemap, err = _contents_properties_shakemap(
        usgs_id, user, use_shakemap, monitor)
    if err:
        return None, None, err
    if approach in ['use_pnt_rup_from_usgs', 'build_rup_from_usgs']:
        rupdic, err = load_rupdic_from_origin(usgs_id, properties['products'])
        if err:
            return None, None, err
    elif ('download/rupture.json' not in contents
          or approach == 'use_finite_rup_from_usgs'):
        # happens for us6000f65h in parsers_test
        rupdic, err = load_rupdic_from_finite_fault(
            usgs_id, properties['mag'], properties['products'])
        if err:
            return None, None, err

    if approach == 'build_rup_from_usgs':
        rupdic['nodal_planes'], err = _get_nodal_planes(properties)
        rupdic['msrs'] = [msr.__class__.__name__
                          for msr in get_available_magnitude_scalerel()]
        if err:
            return None, rupdic, err

    if not rup_data and approach != 'use_pnt_rup_from_usgs':
        with monitor('Downloading rupture json'):
            rup_data, rupture_file = download_rupture_data(
                usgs_id, contents, user)
    if not rupdic:
        rupdic = convert_rup_data(rup_data, usgs_id, rupture_file, shakemap)
    if (user.level == 2 and not station_data_file
            and approach != 'use_shakemap_from_usgs'):
        with monitor('Downloading stations'):
            rupdic['station_data_file'], rupdic['station_data_issue'] = (
                download_station_data_file(usgs_id, contents, user))
        rupdic['station_data_file_from_usgs'] = True
    else:
        rupdic['station_data_file'], rupdic['station_data_issue'] = (
            station_data_file, None)
        rupdic['station_data_file_from_usgs'] = False
    if not rup_data:
        # in parsers_test
        rup = build_planar_rupture_from_dict(rupdic)
        return rup, rupdic, err

    rup = convert_to_oq_rupture(rup_data)
    if rup is None:
        # in parsers_test for us6000jllz
        rupdic['rupture_issue'] = 'Unable to convert the rupture from the USGS format'
        rupdic['require_dip_strike'] = True
    # in parsers_test for usp0001ccb
    return rup, rupdic, err


def get_array_usgs_id(kind, usgs_id):
    """
    Download a ShakeMap from the USGS site.

    :param kind: the string "usgs_id", for API compatibility
    :param usgs_id: ShakeMap ID
    """
    # not tested on purpose
    url = SHAKEMAP_URL.format(usgs_id)
    logging.info('Downloading %s', url)
    contents = json.loads(urlopen(url).read())[
        'properties']['products']['shakemap'][-1]['contents']
    grid = contents.get('download/grid.xml')
    if grid is None:
        raise MissingLink('Could not find grid.xml link in %s' % url)
    uncertainty = contents.get('download/uncertainty.xml.zip') or contents.get(
        'download/uncertainty.xml')
    return get_array(
        kind='usgs_xml', grid_url=grid['url'],
        uncertainty_url=uncertainty['url'] if uncertainty else None)


def get_array_file_npy(kind, fname):
    """
    Read a ShakeMap in .npy format from the local file system
    """
    return numpy.load(fname)


def get_shapefile_arrays(polygons, records):
    dt = sorted((imt[1], F32) for key, imt in FIELDMAP.items()
                if imt[0] == 'val' and key in records.keys())
    bbox = [('minx', F32), ('miny', F32), ('maxx', F32), ('maxy', F32)]
    dtlist = [('bbox', bbox), ('vs30', F32), ('val', dt), ('std', dt)]

    data = numpy.zeros(len(polygons), dtlist)

    for name, field in sorted([('bbox', bbox), *FIELDMAP.items()]):
        if name not in records:
            continue
        if name == 'bbox':
            data[name] = numpy.array(records[name], dtype=bbox)
        elif isinstance(field, tuple):
            # for ('val', IMT) or ('std', IMT)
            data[field[0]][field[1]] = F32(records[name])
        else:
            # for lon, lat, vs30
            data[field] = F32(records[name])

    return polygons, data


def _get_shakemap_array(xml_file):
    if isinstance(xml_file, str):
        fname = xml_file
    elif hasattr(xml_file, 'fp'):
        fname = xml_file.fp.name
    else:
        fname = xml_file.name
    if hasattr(xml_file, 'read'):
        data = io.BytesIO(xml_file.read())
    else:
        data = open(xml_file)
    grid_node = node_from_xml(data)
    fields = grid_node.getnodes('grid_field')
    lines = grid_node.grid_data.text.strip().splitlines()
    rows = [line.split() for line in lines]

    # the indices start from 1, hence the -1 below
    idx = {f['name']: int(f['index']) - 1 for f in fields
           if f['name'] in SHAKEMAP_FIELDS}
    out = {name: [] for name in idx}
    uncertainty = any(imt.startswith('STD') for imt in out)
    missing = sorted(REQUIRED_IMTS - set(out))
    if 'PSA06' in missing:  # old shakemap
        fieldmap = {f: FIELDMAP[f] for f in FIELDMAP if f != 'PSA06'}
    else:  # new shakemap
        fieldmap = FIELDMAP
        if not uncertainty and missing:
            raise RuntimeError('Missing %s in %s' % (missing, fname))
    for name in idx:
        i = idx[name]
        if name in fieldmap:
            out[name].append([float(row[i]) for row in rows])
    dt = sorted((imt[1], F32) for key, imt in fieldmap.items()
                if imt[0] == 'val')
    dtlist = [('lon', F32), ('lat', F32), ('vs30', F32),
              ('val', dt), ('std', dt)]
    data = numpy.zeros(len(rows), dtlist)
    for name, field in sorted(fieldmap.items()):
        if name not in out:
            continue
        if isinstance(field, tuple):
            # for ('val', IMT) or ('std', IMT)
            data[field[0]][field[1]] = F32(out[name])
        else:
            # for lon, lat, vs30
            data[field] = F32(out[name])
    return data


def get_shakemap_array(grid_file, uncertainty_file=None):
    """
    :param grid_file: a shakemap grid file
    :param uncertainty_file: a shakemap uncertainty_file file
    :returns: array with fields lon, lat, vs30, val, std
    """
    data = _get_shakemap_array(grid_file)
    if uncertainty_file:
        data2 = _get_shakemap_array(uncertainty_file)
        # sanity check: lons and lats must be the same
        for coord in ('lon', 'lat'):
            numpy.testing.assert_equal(data[coord], data2[coord])
        # copy the stddevs from the uncertainty array
        for imt in data2['std'].dtype.names:
            data['std'][imt] = data2['std'][imt]
    return data
