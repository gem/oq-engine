# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2023 GEM Foundation
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

import tempfile
import io
import os
import pathlib
import logging
import json
import zipfile
import pytz
import pandas as pd
from datetime import datetime
from shapely.geometry import Polygon
import numpy
from json.decoder import JSONDecodeError
from openquake.baselib.node import (
    node_from_xml, Node)
from openquake.hazardlib.source.rupture import get_multiplanar
from openquake.hazardlib import nrml, sourceconverter

NOT_FOUND = 'No file with extension \'.%s\' file found'
US_GOV = 'https://earthquake.usgs.gov'
SHAKEMAP_URL = US_GOV + '/fdsnws/event/1/query?eventid={}&format=geojson'
F32 = numpy.float32
SHAKEMAP_FIELDS = set(
    'LON LAT SVEL MMI PGA PSA03 PSA10 PSA30 '
    'STDMMI STDPGA STDPSA03 STDPSA10 STDPSA30'
    .split())
FIELDMAP = {
    'LON': 'lon',
    'LAT': 'lat',
    'SVEL': 'vs30',
    'MMI': ('val', 'MMI'),
    'PGA': ('val', 'PGA'),
    'PSA03': ('val', 'SA(0.3)'),
    'PSA10': ('val', 'SA(1.0)'),
    'PSA30': ('val', 'SA(3.0)'),
    'STDMMI': ('std', 'MMI'),
    'STDPGA': ('std', 'PGA'),
    'STDPSA03': ('std', 'SA(0.3)'),
    'STDPSA10': ('std', 'SA(1.0)'),
    'STDPSA30': ('std', 'SA(3.0)'),
}
REQUIRED_IMTS = {'PGA', 'PSA03', 'PSA10'}


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
    Convert USGS json into an hazardlib rupture
    """
    ftype = rup_json['features'][0]['geometry']['type']
    assert ftype == 'MultiPolygon', ftype
    multicoords = rup_json['features'][0]['geometry']['coordinates'][0]
    hyp_depth = rup_json['metadata']['depth']
    rake = rup_json['metadata'].get('rake', 0)
    trt = 'Active Shallow Crust' if hyp_depth < 50 else 'Subduction IntraSlab'
    Mw = rup_json['metadata']['mag']
    rup = get_multiplanar(multicoords, Mw, rake, trt)
    return rup


# Convert rupture to file
def rup_to_file(rup, outfile, commentstr):
    # Determine geometry
    geom = rup.surface.surface_nodes[0].tag
    name = ""
    if len(rup.surface.surface_nodes) > 1:
        name = 'multiPlanesRupture'
    elif geom == 'planarSurface':
        name = 'singlePlaneRupture'
    elif geom == 'simpleFaultGeometry':
        name = 'simpleFaultRupture'
    elif geom == 'complexFaultGeometry':
        name = 'complexFaultRupture'
    elif geom == 'griddedSurface':
        name = 'griddedRupture'
    elif geom == 'kiteSurface':
        name = 'kiteSurface'
    # Arrange node
    h = rup.hypocenter
    hp_dict = dict(lon=h.longitude, lat=h.latitude, depth=h.depth)
    geom_nodes = [Node('magnitude', {}, rup.mag),
                  Node('rake', {}, rup.rake),
                  Node('hypocenter', hp_dict)]
    geom_nodes.extend(rup.surface.surface_nodes)
    rupt_nodes = [Node(name, nodes=geom_nodes)]
    node = Node('nrml', nodes=rupt_nodes)
    # Write file
    with open(outfile, 'wb') as f:
        # adding a comment like:
        # <!-- Rupture XML automatically generated from USGS (us7000f93v).
        #      Reference: Source: USGS NEIC Rapid Finite Fault
        #      Event ID: 7000f93v Model created: 2021-09-08 03:53:15.-->
        nrml.write(node, f, commentstr=commentstr)
    return outfile


def utc_to_local_time(utc_timestamp, lon, lat):
    try:
        # NOTE: optional dependency needed for ARISTOTLE
        from timezonefinder import TimezoneFinder
    except ImportError:
        raise ImportError(
            'The python package "timezonefinder" is not installed. It is'
            ' required in order to convert the UTC time to the local time of'
            ' the event. You can install it running:'
            ' pip install timezonefinder==6.5.2')
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str is None:
        logging.warning(
            'Could not determine the timezone. Using the UTC time')
        return utc_timestamp
    utc_time = datetime.strptime(utc_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    utc_zone = pytz.utc
    utc_time = utc_zone.localize(utc_time)
    local_zone = pytz.timezone(timezone_str)
    local_timestamp = utc_time.astimezone(local_zone)
    return local_timestamp


def local_time_to_time_event(local_time):
    if 9 <= local_time.hour < 17:
        return 'day'
    if local_time.hour >= 21 or local_time.hour < 5:
        return 'night'
    return 'transit'


def read_usgs_stations_json(stations_json_str):
    try:
        stations_json_str = stations_json_str.decode('utf8')
    except UnicodeDecodeError:
        stations_json_str = stations_json_str.decode('latin1')
    sj = json.loads(stations_json_str)
    if 'features' not in sj or not sj['features']:
        raise LookupError(
            'stationlist.json was downloaded, but it contains no features')
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


def download_station_data_file(usgs_id, save_to_home=False):
    """
    Download station data from the USGS site given a ShakeMap ID.

    :param usgs_id: ShakeMap ID
    :param save_to_home: for debugging purposes you may want to check the
        contents of the station data before and after the conversion from the
        usgs format to the oq format
    :returns: the path of a csv file with station data converted to a format
        compatible with OQ
    """
    # NOTE: downloading twice from USGS, but with a clearer workflow
    url = SHAKEMAP_URL.format(usgs_id)
    logging.info('Downloading %s' % url)
    js = json.loads(urlopen(url).read())
    products = js['properties']['products']
    station_data_file = None
    try:
        shakemap = products['shakemap']
    except KeyError:
        msg = 'No shakemap was found'
        logging.info(msg)
        raise
    for shakemap in reversed(shakemap):
        contents = shakemap['contents']
        if 'download/stationlist.json' in contents:
            stationlist_url = contents.get('download/stationlist.json')['url']
            logging.info('Downloading stationlist.json')
            stations_json_str = urlopen(stationlist_url).read()
            try:
                stations = read_usgs_stations_json(stations_json_str)
            except (LookupError, UnicodeDecodeError, JSONDecodeError) as exc:
                logging.info(str(exc))
                raise
            original_len = len(stations)
            try:
                seismic_len = len(
                    stations[stations['station_type'] == 'seismic'])
            except KeyError:
                msg = (f'{original_len} stations were found, but the'
                       f' "station_type" is not specified, so we can not'
                       f' identify the "seismic" stations.')
                logging.info(msg)
                raise LookupError(msg)
            df = usgs_to_ecd_format(stations, exclude_imts=('SA(3.0)',))
            if save_to_home:
                homedir = os.path.expanduser('~')
                stations_usgs = os.path.join(homedir, 'stations_usgs.csv')
                stations.to_csv(stations_usgs, index=False)
                stations_oq = os.path.join(homedir, 'stations_oq.csv')
                df.to_csv(stations_oq, index=False)
            if len(df) < 1:
                if original_len > 1:
                    if seismic_len > 1:
                        msg = (f'{original_len} stations were found, but the'
                               f' {seismic_len} seismic stations were all'
                               f' discarded')
                        logging.info(msg)
                        raise LookupError(msg)
                    else:
                        msg = (f'{original_len} stations were found, but none'
                               f' of them are seismic')
                        logging.info(msg)
                        raise LookupError(msg)
                else:
                    msg = 'No stations were found'
                    logging.info(msg)
                    raise LookupError(msg)
            else:
                with tempfile.NamedTemporaryFile(
                        delete=False, mode='w+', newline='',
                        suffix='.csv') as temp_file:
                    station_data_file = temp_file.name
                    df.to_csv(station_data_file, encoding='utf8', index=False)
                    logging.info(f'Wrote stations to {station_data_file}')
                    return station_data_file


def load_rupdic_from_finite_fault(usgs_id, mag, products):
    try:
        ff = products['finite-fault']
    except KeyError:
        raise MissingLink('There is no finite-fault info for %s' % usgs_id)
    logging.info('Getting finite-fault properties')
    if isinstance(ff, list):
        if len(ff) > 1:
            logging.warning(f'The finite-fault list contains {len(ff)}'
                            f' elements. We are using the first one.')
        ff = ff[0]
    p = ff['properties']
    lon = float(p['longitude'])
    lat = float(p['latitude'])
    utc_time = p['eventtime']
    local_time = utc_to_local_time(utc_time, lon, lat)
    time_event = local_time_to_time_event(local_time)
    rupdic = {'lon': lon, 'lat': lat, 'dep': float(p['depth']),
              'mag': mag, 'rake': 0.,
              'local_timestamp': str(local_time), 'time_event': time_event,
              'is_point_rup': True, 'usgs_id': usgs_id, 'rupture_file': None}
    return rupdic


def download_rupture_dict(usgs_id, ignore_shakemap=False):
    """
    Download a rupture from the USGS site given a ShakeMap ID.

    :param usgs_id: ShakeMap ID
    :param ignore_shakemap: for testing purposes, only consider finite-fault
    :returns: a dictionary with keys lon, lat, dep, mag, rake
    """
    url = SHAKEMAP_URL.format(usgs_id)
    logging.info('Downloading %s' % url)
    try:
        js = json.loads(urlopen(url).read())
    except URLError as exc:
        raise URLError(f'Unable to download from the USGS website: {str(exc)}')
    mag = js['properties']['mag']
    products = js['properties']['products']
    try:
        if ignore_shakemap:
            raise KeyError
        shakemap = products['shakemap']
    except KeyError:
        try:
            products['finite-fault']
        except KeyError:
            raise MissingLink(
                'There is no shakemap nor finite-fault info for %s' % usgs_id)
        else:
            shakemap = []
    for shakemap in reversed(shakemap):
        contents = shakemap['contents']
        if 'download/rupture.json' in contents:
            break
    else:  # missing rupture.json
        return load_rupdic_from_finite_fault(usgs_id, mag, products)
    url = contents.get('download/rupture.json')['url']
    logging.info('Downloading rupture.json')
    rup_data = json.loads(urlopen(url).read())
    feats = rup_data['features']
    is_point_rup = len(feats) == 1 and feats[0]['geometry']['type'] == 'Point'
    md = rup_data['metadata']
    lon = md['lon']
    lat = md['lat']
    utc_time = md['time']
    local_time = utc_to_local_time(utc_time, lon, lat)
    time_event = local_time_to_time_event(local_time)
    if is_point_rup:
        return {'lon': lon, 'lat': lat, 'dep': md['depth'],
                'mag': md['mag'], 'rake': md['rake'],
                'local_timestamp': str(local_time), 'time_event': time_event,
                'is_point_rup': is_point_rup,
                'usgs_id': usgs_id, 'rupture_file': None}
    try:
        oq_rup = convert_to_oq_rupture(rup_data)
    except Exception as exc:
        logging.error('', exc_info=True)
        error_msg = (
            f'Unable to convert the rupture from the USGS format: {exc}')
        # TODO: we can try to handle also cases that currently are not properly
        # converted, then raise an exception here in case of failure
        return {'lon': lon, 'lat': lat, 'dep': md['depth'],
                'mag': md['mag'], 'rake': md['rake'],
                'local_timestamp': str(local_time), 'time_event': time_event,
                'is_point_rup': True,
                'usgs_id': usgs_id, 'rupture_file': None, 'error': error_msg}
    comment_str = (
        f"<!-- Rupture XML automatically generated from USGS ({md['id']})."
        f" Reference: {md['reference']}.-->\n")
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    rupture_file = rup_to_file(oq_rup, temp_file.name, comment_str)
    try:
        [rup_node] = nrml.read(rupture_file)
        conv = sourceconverter.RuptureConverter(rupture_mesh_spacing=5.)
        conv.convert_node(rup_node)
    except ValueError as exc:
        logging.error('', exc_info=True)
        error_msg = (
            f'Unable to convert the rupture from the USGS format: {exc}')
        # TODO: we can try to handle also cases that currently are not properly
        # converted, then raise an exception here in case of failure
        return {'lon': lon, 'lat': lat, 'dep': md['depth'],
                'mag': md['mag'], 'rake': md['rake'],
                'local_timestamp': str(local_time), 'time_event': time_event,
                'is_point_rup': True,
                'usgs_id': usgs_id, 'rupture_file': None, 'error': error_msg}
    return {'lon': lon, 'lat': lat, 'dep': md['depth'],
            'mag': md['mag'], 'rake': md['rake'],
            'local_timestamp': str(local_time), 'time_event': time_event,
            'is_point_rup': False,
            'trt': oq_rup.tectonic_region_type,
            'usgs_id': usgs_id, 'rupture_file': rupture_file}


def get_array_usgs_id(kind, usgs_id):
    """
    Download a ShakeMap from the USGS site.

    :param kind: the string "usgs_id", for API compatibility
    :param usgs_id: ShakeMap ID
    """
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
    if not uncertainty and missing:
        raise RuntimeError('Missing %s in %s' % (missing, fname))
    for name in idx:
        i = idx[name]
        if name in FIELDMAP:
            out[name].append([float(row[i]) for row in rows])
    dt = sorted((imt[1], F32) for key, imt in FIELDMAP.items()
                if imt[0] == 'val')
    dtlist = [('lon', F32), ('lat', F32), ('vs30', F32),
              ('val', dt), ('std', dt)]
    data = numpy.zeros(len(rows), dtlist)
    for name, field in sorted(FIELDMAP.items()):
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
