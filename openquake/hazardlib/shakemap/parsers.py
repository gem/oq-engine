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

import io
import os
import sys
import pathlib
import logging
import json
import base64
import zipfile
import tempfile
from dataclasses import dataclass
from urllib.request import urlopen, pathname2url
from urllib.error import URLError
from collections import defaultdict
from xml.parsers.expat import ExpatError
from datetime import datetime
from zoneinfo import ZoneInfo

from shapely.geometry import shape, Point, Polygon
import pandas as pd
import numpy
import fiona

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import math

from openquake.baselib import performance, config
from openquake.baselib.general import gettemp
from openquake.baselib.node import node_from_xml
from openquake.hazardlib import nrml, sourceconverter, valid
from openquake.hazardlib.source.rupture import (
    build_planar_rupture_from_dict, get_ruptures)

NOT_FOUND = 'No file with extension \'.%s\' file found'
US_GOV = 'https://earthquake.usgs.gov'
# NOTE: remove the includesuperseded parameter to download less data for testing
QUERY_PARAMS = '?eventid={}&format=geojson&includesuperseded=True'
SHAKEMAP_URL = US_GOV + '/fdsnws/event/1/query' + QUERY_PARAMS
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
    :returns: the parsed url
    """
    if not url.startswith('file:') and not url.startswith('http'):
        file = pathlib.Path(url)
        if file.is_file():
            return f'file:{pathname2url(str(file.absolute()))}'
        raise FileNotFoundError(
            'The following path could not be found: %s' % url)
    return url


def get_array(**kw):
    """
    :param kw: a dictionary with a key 'kind' and various parameters
    :returns: ShakeMap as a numpy array, dowloaded or read in various ways
    """
    kind = kw['kind']
    if kind == 'shapefile':
        return get_array_shapefile(kind, kw['fname'])
    elif kind == 'usgs_xml':
        return get_array_usgs_xml(kind, kw['grid_url'],
                                  kw.get('uncertainty_url'))
    elif kind == 'usgs_id':
        # NOTE: _get_contents uses the 'usgs_preferred' ShakeMap version by default
        # This is called when there is the shakemap_id inside the job.ini
        contents, err = _get_contents(kw['id'])
        if err:
            raise RuntimeError(err['error_msg'])
        return get_array_usgs_id(kind, kw['id'], contents)
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
    if fname.startswith('file:'):
        fname = fname[5:]  # strip file:
    if fname.endswith('.zip'):
        if sys.platform == 'win32':
            # fiona cannot automatically unzip, so unzip manually
            targetdir = tempfile.mkdtemp(
                dir=config.directory.custom_tmp or None)
            with zipfile.ZipFile(fname) as archive:
                archive.extractall(targetdir)
            [fname] = [os.path.join(targetdir, f)
                       for f in os.listdir(targetdir) if f.endswith('.shp')]
        else:
            fname = 'zip://' + fname
    polygons = []
    data = defaultdict(list)
    with fiona.open(fname) as f:
        for feature in f:
            polygons.append(shape(feature.geometry))
            for k, v in feature.properties.items():
                data[k.upper()].append(v)
            # append bounding box for later use
            data['bbox'].append(polygons[-1].bounds)
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


def sort_vertices(vertices):
    # Sort vertices by depth (ascending)
    sorted_by_depth = sorted(vertices, key=lambda v: v[2])
    # Reorder vertices to topLeft, topRight, bottomRight, bottomLeft
    top_vertices = sorted(
        sorted_by_depth[:2], key=lambda v: v[0]
    )  # Sort by longitude
    bottom_vertices = sorted(
        sorted_by_depth[2:], key=lambda v: v[0]
    )  # Sort by longitude
    sorted_vertices = [
        top_vertices[0],  # topLeft
        top_vertices[1],  # topRight
        bottom_vertices[1],  # bottomRight
        bottom_vertices[0],  # bottomLeft
    ]
    return sorted_vertices


# Calculate strike and dip from the vertices
def calculate_strike_and_dip(vertices):
    # Determine the top edge by finding the two vertices with the smallest depth
    top_vertices = vertices[:2]
    # bottom_vertices = vertices[2:]  # unused

    # Calculate the top edge vector
    top_edge = [
        top_vertices[1][0] - top_vertices[0][0],
        top_vertices[1][1] - top_vertices[0][1],
    ]

    # Calculate strike (angle of top edge with respect to north)
    strike = math.degrees(math.atan2(top_edge[1], top_edge[0]))
    if strike < 0:
        strike += 360

    # Calculate dip (angle between top and bottom edges in depth)
    vertical_diff = abs(vertices[0][2] - vertices[2][2])
    horizontal_diff = math.sqrt(
        (vertices[0][0] - vertices[2][0]) ** 2 + (vertices[0][1] - vertices[2][1]) ** 2
    )
    dip = math.degrees(math.atan2(vertical_diff, horizontal_diff))

    return strike, dip


def add_point_elements(nrml, metadata, coordinates):
    rupture = SubElement(nrml, "pointRupture")
    magnitude = SubElement(rupture, "magnitude")
    magnitude.text = str(metadata["mag"])
    SubElement(
        rupture,
        "hypocenter",
        {
            "lon": str(coordinates[0]),
            "lat": str(coordinates[1]),
            "depth": str(coordinates[2]),
        },
    )


def add_single_and_multi_plane_elements(nrml, metadata, polygons):
    rupture = (
        SubElement(nrml, "singlePlaneRupture")
        if len(polygons) == 1
        else SubElement(nrml, "multiPlanesRupture")
    )
    magnitude = SubElement(rupture, "magnitude")
    magnitude.text = str(metadata["mag"])

    rake = SubElement(rupture, "rake")
    rake.text = str(metadata.get("rake", 0))

    SubElement(
        rupture,
        "hypocenter",
        {
            "lon": str(metadata["lon"]),
            "lat": str(metadata["lat"]),
            "depth": str(metadata["depth"]),
        },
    )

    for polygon in polygons:
        # Check if the last vertex is identical to the first
        # (closing the polygon)
        if polygon[-1] == polygon[0]:
            # Discard the last vertex
            vertices = polygon[:-1]
        else:
            vertices = polygon

        sorted_vertices = sort_vertices(vertices)

        strike, dip = calculate_strike_and_dip(sorted_vertices)

        planar_surface = SubElement(
            rupture,
            "planarSurface",
            {
                "strike": f"{strike:.2f}",
                "dip": f"{dip:.2f}",
            },
        )

        # Assign vertices based on depth
        SubElement(
            planar_surface,
            "topLeft",
            {
                "lon": str(sorted_vertices[0][0]),
                "lat": str(sorted_vertices[0][1]),
                "depth": str(sorted_vertices[0][2]),
            },
        )
        SubElement(
            planar_surface,
            "topRight",
            {
                "lon": str(sorted_vertices[1][0]),
                "lat": str(sorted_vertices[1][1]),
                "depth": str(sorted_vertices[1][2]),
            },
        )
        SubElement(
            planar_surface,
            "bottomRight",
            {
                "lon": str(sorted_vertices[2][0]),
                "lat": str(sorted_vertices[2][1]),
                "depth": str(sorted_vertices[2][2]),
            },
        )
        SubElement(
            planar_surface,
            "bottomLeft",
            {
                "lon": str(sorted_vertices[3][0]),
                "lat": str(sorted_vertices[3][1]),
                "depth": str(sorted_vertices[3][2]),
            },
        )


def add_complex_fault_elements(nrml, metadata, polygons):
    rupture = SubElement(nrml, "complexFaultRupture")
    magnitude = SubElement(rupture, "magnitude")
    magnitude.text = str(metadata["mag"])

    rake = SubElement(rupture, "rake")
    rake.text = str(metadata.get("rake", 0))

    SubElement(
        rupture,
        "hypocenter",
        {
            "lon": str(metadata["lon"]),
            "lat": str(metadata["lat"]),
            "depth": str(metadata["depth"]),
        },
    )

    for polygon in polygons:
        geometry = SubElement(rupture, "complexFaultGeometry")
        # Split the polygon into top and bottom edges based on depth
        sorted_vertices = sorted(polygon[:-1], key=lambda v: v[2])
        mid_index = len(sorted_vertices) // 2
        top_edge_vertices = sorted_vertices[:mid_index]
        bottom_edge_vertices = sorted_vertices[mid_index:][::-1]

        # Create faultTopEdge
        indent_str = "\n            "
        fault_top_edge = SubElement(geometry, "faultTopEdge")
        top_line_string = SubElement(fault_top_edge, "gml:LineString")
        top_pos_list = SubElement(top_line_string, "gml:posList")
        top_pos_list.text = (
            indent_str
            + indent_str.join(
                f"{v[0]:.4f} {v[1]:.4f} {v[2]:.1f}" for v in top_edge_vertices
            )
            + "\n          "
        )

        # Create faultBottomEdge
        fault_bottom_edge = SubElement(geometry, "faultBottomEdge")
        bottom_line_string = SubElement(fault_bottom_edge, "gml:LineString")
        bottom_pos_list = SubElement(bottom_line_string, "gml:posList")
        bottom_pos_list.text = (
            indent_str
            + indent_str.join(
                f"{v[0]:.4f} {v[1]:.4f} {v[2]:.1f}"
                for v in bottom_edge_vertices
            )
            + "\n          "
        )


def add_multipolygon_elements(nrml, metadata, coordinates):
    polygons = coordinates[0]

    # Handle Single-plane ruptures and Multi-plane ruptures
    # in the same if block
    if all(len(polygon) == 5 for polygon in polygons):
        add_single_and_multi_plane_elements(nrml, metadata, polygons)
    elif any(len(polygon) > 5 for polygon in polygons):
        # Complex fault rupture with one or more geometries
        add_complex_fault_elements(nrml, metadata, polygons)


def convert_to_oq_xml(input_json_file, output_xml_file):
    with open(input_json_file, "r") as f:
        data = json.load(f)

    geometry_type = data["features"][0]["geometry"]["type"]
    coordinates = data["features"][0]["geometry"]["coordinates"]
    metadata = data["metadata"]
    logging.info(metadata["reference"])

    nrml = Element(
        "nrml",
        xmlns="http://openquake.org/xmlns/nrml/0.5",
        attrib={"xmlns:gml": "http://www.opengis.net/gml"},
    )

    if geometry_type == "Point":
        # TODO: as soon as OQ will be able to handle xml files with Point sources,
        # convert also this to xml
        return input_json_file
        add_point_elements(nrml, metadata, coordinates)
    elif geometry_type == "MultiPolygon":
        add_multipolygon_elements(nrml, metadata, coordinates)
    else:
        raise ValueError(f"Unsupported geometry type: {geometry_type}")

    # Convert the ElementTree to a string
    rough_string = tostring(nrml, "utf-8")
    # Use minidom to pretty print the XML
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")

    # Write the pretty-printed XML to the output file
    with open(output_xml_file, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    return output_xml_file


def utc_to_local_time(utc_timestamp, lon, lat):
    """
    Convert a timestamp '%Y-%m-%dT%H:%M:%S.%fZ' into a datetime object
    """
    utc_time = datetime.strptime(utc_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    try:
        from timezonefinder import TimezoneFinder
    except ImportError:
        timezone_str = None
    else:
        timezone_str = TimezoneFinder().timezone_at(lng=lon, lat=lat)
    if timezone_str is None:
        logging.warning('Could not determine the timezone. Using the UTC time')
        return utc_time
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
    # cases, take the component with maximum PGA (and in absence of PGA, the
    # first IM reported).
    channels = pd.DataFrame(stations.channels.to_list())
    vals = pd.Series([], dtype='object')
    for row, rec_station in channels.iterrows():
        rec_station.dropna(inplace=True)
        # Iterate over different columns. Each column can be a component
        data = []
        pgas = []
        for _, chan in rec_station.items():
            if chan["name"].endswith(("z", "Z", "u", "U")):
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
            max_component = pgas.index(max(pgas))
            vals[row] = data[max_component]
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
                # Column already exist. Combine values in unique column
                values[col] = values[col].combine_first(df[col])
            else:
                values = pd.concat([values, df[col]], axis=1)
    values.sort_index(axis=1, inplace=True)
    # Add recording to main DataFrame
    stations = pd.concat([stations, values], axis=1)
    return stations


def usgs_stations_to_oq_format(stations, exclude_imts=(), seismic_only=False):
    '''
    Convert from ShakeMap stations format to the OpenQuake format
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
        if ('_VALUE' in col or '_LN_SIGMA' in col or
                '_STDDEV' in col and col != 'DISTANCE_STDDEV'):
            imt = col.split('_')[0]
            if imt not in exclude_imts:
                assert col not in imts
                imts.append(col)
    # Identify relevant columns
    cols = ['STATION_ID', 'STATION_NAME', 'LONGITUDE', 'LATITUDE',
            'STATION_TYPE', 'DISTANCE', 'VS30'] + imts
    df = stations[cols].copy()
    # Add missing columns
    df.loc[:, 'VS30_TYPE'] = 'inferred'
    df.loc[:, 'REFERENCES'] = 'Stations_USGS'
    # Adjust PGA and SA units to [g]. USGS uses [% g]
    adj_cols = [imt for imt in imts
                if '_VALUE' in imt and
                'PGV' not in imt and
                'MMI' not in imt]
    df.loc[:, adj_cols] = round(df.loc[:, adj_cols].
                                apply(pd.to_numeric, errors='coerce') / 100, 6)
    if seismic_only:
        df = df.loc[df.STATION_TYPE == 'seismic'].dropna()
    return df


def _get_usgs_preferred_item(items):
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
    err = {}
    if 'download/stationlist.json' in contents:
        stationlist_url = contents.get('download/stationlist.json')['url']
        # fname = os.path.join(user.testdir, f'{usgs_id}-stations.json')
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
            err = {"status": "failed", "error_msg": msg}
            return None, 0, err
        original_len = len(stations)
        try:
            seismic_len = len(
                stations[stations['station_type'] == 'seismic'])
        except KeyError:
            msg = (f'{original_len} stations were found, but the'
                   f' "station_type" is not specified, so we can not'
                   f' identify the "seismic" stations.')
            err = {"status": "failed", "error_msg": msg}
            return None, 0, err
        df = usgs_stations_to_oq_format(
            stations, exclude_imts=('SA(3.0)',), seismic_only=True)
        if len(df) < 1:
            if original_len > 1:
                if seismic_len > 1:
                    msg = (f'{original_len} stations were found, but the'
                           f' {seismic_len} seismic stations were all'
                           f' discarded')
                    err = {"status": "failed", "error_msg": msg}
                    return None, 0, err
                else:
                    msg = (f'{original_len} stations were found, but none'
                           f' of them are seismic')
                    err = {"status": "failed", "error_msg": msg}
                    return None, 0, err
            else:
                msg = 'No stations were found'
                err = {"status": "failed", "error_msg": msg}
                return None, 0, err
        else:
            station_data_file = gettemp(
                prefix='stations', suffix='.csv', remove=False)
            df.to_csv(station_data_file, encoding='utf8', index=False)
            n_stations = len(df)
            return station_data_file, n_stations, err


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
    ff = _get_usgs_preferred_item(ffs)
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
    origin = _get_usgs_preferred_item(origins)
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
        logging.error(f"Error: Unable to fetch data for event {usgs_id} - {e}")
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
        logging.error(f"No ShakeMap found for event {usgs_id}")
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
            logging.error(f"Error: Unable to download the {what} image - {e}")
            return None
    else:
        logging.error("Error: Could not retrieve the ShakeMap version ID.")
        return None


# NB: this is always available but sometimes the geometry is Point
# or a MultiPolygon not convertible to an engine rupture geometry
def download_shakemap_rupture_data(usgs_id, shakemap_contents, user):
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


def extract_event_details(ffm):
    # Extract event details from the geojson metadata
    # and return a data object with the event details
    epicenter = ffm["metadata"]["epicenter"]
    mag = epicenter.get("mag")
    lon = epicenter.get("lon")
    lat = epicenter.get("lat")
    dep = epicenter.get("depth")
    event_details = {
        "mag": mag,
        "lon": lon,
        "lat": lat,
        "dep": dep,
    }
    return event_details


def parse_basic_inversion_params(basic_inversion):
    # Extract fault segment data
    fault_segments = []
    segment = None
    for line in basic_inversion.split('\n'):
        if line.startswith("#Fault_segment"):
            if segment:
                fault_segments.append(segment)
            segment = {"vertices": [], "strike": None, "dip": None}
        elif line.startswith("#Boundary of Fault_segment"):
            continue
        elif line.strip().startswith("#Lat. Lon. depth"):
            continue
        elif line.strip().startswith("#"):
            continue
        elif segment is not None:
            parts = line.split()
            if len(parts) == 3:  # Vertex line
                lon, lat, depth = map(float, parts)
                segment["vertices"].append({"lon": lon, "lat": lat, "depth": depth})
            elif len(parts) >= 8:  # Strike and dip line
                segment["strike"] = float(parts[5])
                segment["dip"] = float(parts[6])
    if segment:
        fault_segments.append(segment)
    return fault_segments


def create_rupture_xml_from_ffm(event_details, fault_segments, output_filepath):
    # create an OpenQuake rupture XML file from FFM data
    nrml = Element(
        "nrml",
        xmlns="http://openquake.org/xmlns/nrml/0.4",
        attrib={"xmlns:gml": "http://www.opengis.net/gml"},
    )
    if len(fault_segments) == 1:
        multi_planes_rupture = SubElement(nrml, "singlePlaneRupture")
    else:
        multi_planes_rupture = SubElement(nrml, "multiPlanesRupture")

    mag = event_details["mag"]
    lon = event_details["lon"]
    lat = event_details["lat"]
    dep = event_details["dep"]

    SubElement(multi_planes_rupture, "magnitude").text = str(mag)
    rake = 0
    SubElement(multi_planes_rupture, "rake").text = str(rake)
    SubElement(
        multi_planes_rupture, "hypocenter", lat=str(lat), lon=str(lon), depth=str(dep)
    )

    for segment in fault_segments:
        planar_surface = SubElement(
            multi_planes_rupture,
            "planarSurface",
            strike=str(segment["strike"]),
            dip=str(segment["dip"]),
        )
        if len(segment["vertices"]) >= 4:
            # Remove the last vertex if it is a duplicate of the first vertex
            if segment["vertices"][-1] == segment["vertices"][0]:
                segment["vertices"].pop()

            # Sort vertices by depth (ascending)
            sorted_vertices = sorted(segment["vertices"], key=lambda v: v["depth"])

            # Top edge: vertices with lower depth
            top_vertices = sorted_vertices[:2]
            # Bottom edge: vertices with higher depth
            bottom_vertices = sorted_vertices[2:]

            # Ensure clockwise order
            if top_vertices[0]["lon"] > top_vertices[1]["lon"]:
                top_vertices.reverse()
            if bottom_vertices[0]["lon"] > bottom_vertices[1]["lon"]:
                bottom_vertices.reverse()

            # Assign vertices
            SubElement(
                planar_surface,
                "topLeft",
                lon=str(top_vertices[0]["lon"]),
                lat=str(top_vertices[0]["lat"]),
                depth=str(top_vertices[0]["depth"]),
            )
            SubElement(
                planar_surface,
                "topRight",
                lon=str(top_vertices[1]["lon"]),
                lat=str(top_vertices[1]["lat"]),
                depth=str(top_vertices[1]["depth"]),
            )
            SubElement(
                planar_surface,
                "bottomRight",
                lon=str(bottom_vertices[1]["lon"]),
                lat=str(bottom_vertices[1]["lat"]),
                depth=str(bottom_vertices[1]["depth"]),
            )
            SubElement(
                planar_surface,
                "bottomLeft",
                lon=str(bottom_vertices[0]["lon"]),
                lat=str(bottom_vertices[0]["lat"]),
                depth=str(bottom_vertices[0]["depth"]),
            )

    xml_str = tostring(nrml, encoding="utf-8")
    pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")

    with open(output_filepath, "w", encoding="utf-8") as file:
        file.write(pretty_xml_str)
    return output_filepath


def download_finite_fault_rupture(usgs_id, user, monitor):
    err = {}
    properties, err = _get_properties(usgs_id, user, monitor)
    try:
        finite_fault = _get_usgs_preferred_item(properties['products']['finite-fault'])
    except KeyError:
        err = {"status": "failed", "error_msg": 'The finite-fault was not found'}
        return None, err
    ffm_url = finite_fault['contents']['FFM.geojson']['url']
    basic_inversion_url = finite_fault['contents']['basic_inversion.param']['url']

    # fname = os.path.join(user.testdir, f'{usgs_id}-ffm.geojson')
    # with open(fname, 'wb') as f:
    #     f.write(urlopen(ffm_url).read())
    # fname = os.path.join(user.testdir, f'{usgs_id}-basic_inversion.param')
    # with open(fname, 'wb') as f:
    #     f.write(urlopen(basic_inversion_url).read())

    if user.testdir:
        ffm_fname = os.path.join(user.testdir, f'{usgs_id}-ffm.geojson')
        ffm_str = open(ffm_fname, 'rb').read()
        basic_inversion_fname = os.path.join(
            user.testdir, f'{usgs_id}-basic_inversion.param')
        basic_inversion_bytes = open(basic_inversion_fname, 'rb').read()
    else:
        logging.info('Downloading FFM.geojson')
        ffm_str = urlopen(ffm_url).read()
        logging.info('Downloading basic_inversion.param')
        basic_inversion_bytes = urlopen(basic_inversion_url).read()
    ffm = json.loads(ffm_str)
    basic_inversion_str = basic_inversion_bytes.decode('utf8')

    event_details = extract_event_details(ffm)
    fault_segments = parse_basic_inversion_params(basic_inversion_str)
    output_rupture_xml = gettemp(suffix='.xml')
    output_rupture_xml = create_rupture_xml_from_ffm(
        event_details, fault_segments, output_rupture_xml)
    return output_rupture_xml, err


def download_mmi(usgs_id, shakemap_contents, user):
    shape = shakemap_contents.get('download/shape.zip')
    if shape is None:
        return None
    url = shape['url']
    if user.testdir:  # in parsers_test
        mmi_file = os.path.join(user.testdir, f'{usgs_id}-shp.zip')
        logging.info(f'Using {mmi_file}')
    else:
        logging.info('Downloading shape.zip (mmi_file)')
        mmi_file = gettemp(prefix='mmi_', suffix='.zip')
        with urlopen(url) as resp, open(mmi_file, 'wb') as f:
            f.write(resp.read())
    return mmi_file


def convert_rup_data(rup_data, usgs_id, rup_path, shakemap_array=None):
    """
    Convert JSON data coming from the USGS into a rupdic with keys
    lon, lat, dep, mag, rake, local_timestamp, shakemap, usgs_id, rupture_file
    """
    md = rup_data['metadata']
    lon = md['lon']
    lat = md['lat']
    utc_time = md['time']
    local_time = utc_to_local_time(utc_time, lon, lat)
    time_event = local_time_to_time_event(local_time)
    rupdic = {'lon': lon, 'lat': lat, 'dep': md['depth'],
              'mag': md['mag'], 'rake': md['rake'],
              'local_timestamp': str(local_time), 'time_event': time_event,
              'shakemap_array': shakemap_array,
              'usgs_id': usgs_id, 'rupture_file': rup_path}
    return rupdic


def _get_properties(usgs_id, user=User(), monitor=performance.Monitor()):
    # returns the properties for the usgs_id event or an error dictionary
    properties = {}
    usgs_event_data, err = _get_usgs_event_data(usgs_id, user, monitor)
    if usgs_event_data:
        properties = usgs_event_data['properties']
    return properties, err


def _get_contents(usgs_id, shakemap_version='usgs_preferred',
                  user=User(), monitor=performance.Monitor()):
    # returns the _contents dictionary or an error dictionary
    properties, err = _get_properties(usgs_id, user, monitor)
    shakemaps = properties['products']['shakemap']
    if shakemap_version == 'usgs_preferred':
        shakemap = _get_usgs_preferred_item(shakemaps)
    else:
        [shakemap] = [shm for shm in shakemaps if shm['id'] == shakemap_version]
    return shakemap['contents'], err


def _get_usgs_event_data(usgs_id, user=User(), monitor=performance.Monitor()):
    # with open(f'/tmp/{usgs_id}.json', 'wb') as f:
    #     url = SHAKEMAP_URL.format(usgs_id)
    #     f.write(urlopen(url).read())
    #     # NOTE: remove the includesuperseded parameter to download less
    #             data for testing
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
            return None, err
    usgs_event_data = json.loads(text)
    return usgs_event_data, err


def _contents_properties_shakemap(usgs_id, user, get_grid, monitor,
                                  shakemap_version='usgs_preferred'):
    err = {}
    usgs_event_data, err = _get_usgs_event_data(usgs_id, user, monitor)
    if err:
        return None, None, None, None, err

    properties = usgs_event_data['properties']

    # NB: currently we cannot find a case with missing shakemap
    shakemaps = properties['products']['shakemap']
    if shakemap_version == 'usgs_preferred':
        shakemap = _get_usgs_preferred_item(shakemaps)
    else:
        [shakemap] = [shm for shm in shakemaps if shm['id'] == shakemap_version]
    contents = shakemap['contents']

    if get_grid and 'download/grid.xml' in contents:
        if user.testdir:  # in parsers_test
            grid_fname = f'{user.testdir}/{usgs_id}-grid.xml'
            shakemap_array = get_shakemap_array(grid_fname)
        else:  # download the shakemap
            shakemap_array = get_array_usgs_id("usgs_id", usgs_id, contents)
    else:
        shakemap_array = None
    # NOTE: shakemap version numbers look like '1'
    # shakemap ids look like 'urn:usgs-product:us:shakemap:us6000phrk:1735953132990'
    shakemap_version_number = shakemap['properties']['version']
    utc_date_time = ms_to_utc_date_time(shakemap['updateTime'])
    shakemap_desc = f'v{shakemap_version_number}: {utc_date_time}'
    return contents, properties, shakemap_array, shakemap_desc, err


def get_nodal_planes_and_info(usgs_id, user=User(), monitor=performance.Monitor()):
    """
    Retrieve the nodal planes and a dict with lon, lat, dep and mag,
    for the given USGS id

    :param usgs_id: ShakeMap ID
    :returns (a dictionary with nodal planes information,
              a dictionary with lon, lat, dep and mag,
              error dictionary or {})
    """
    properties, err = _get_properties(usgs_id, user, monitor)
    if err:
        return None, err
    nodal_planes, err = _get_nodal_planes_from_properties(properties)
    info = _get_earthquake_info_from_properties(properties)
    return nodal_planes, info, err


def _get_earthquake_info_from_properties(properties):
    origin = _get_usgs_preferred_item(properties['products']['origin'])
    props = origin['properties']
    info = dict(lon=props['longitude'], lat=props['latitude'], dep=props['depth'],
                mag=props['magnitude'])
    return info


def _get_nodal_planes_from_properties(properties):
    # in parsers_test
    nodal_planes = {}
    err = {}
    # try reading from the moment tensor, if available. If nodal planes can not
    # be collected, fallback attempting to read them from the focal mechanism
    if 'moment-tensor' in properties['products']:
        moment_tensor = _get_usgs_preferred_item(
            properties['products']['moment-tensor'])
        nodal_planes = _get_nodal_planes_from_product(moment_tensor)
    if not nodal_planes and 'focal-mechanism' in properties['products']:
        focal_mechanism = _get_usgs_preferred_item(
            properties['products']['focal-mechanism'])
        nodal_planes = _get_nodal_planes_from_product(focal_mechanism)
    if not nodal_planes:
        err = {'status': 'failed', 'error_msg':
               'Unable to retrieve information about the nodal options'}
        return None, err
    return nodal_planes, err


def _get_nodal_planes_from_product(product):
    props = product['properties']
    nodal_planes = {}
    for key, value in props.items():
        if key.startswith('nodal-plane-'):
            parts = key.split('-')
            plane = f'NP{parts[2]}'
            attr = parts[3]  # Get the attribute (i.e. 'dip', 'rake' or 'strike')
            if plane not in nodal_planes:
                nodal_planes[plane] = {}
            nodal_planes[plane][attr] = float(value)
    return nodal_planes


def adjust_hypocenter(rup):
    """
    If the hypocenter is outside the surface of the rupture (e.g. us7000pwkn v6),
    reposition it to the middle of the surface

    :param rup: an instance of openquake.hazardlib.source.rupture.BaseRupture
    :returns: (the rupture with possibly adjusted hypocenter, a warning message if the
    hypocenter was moved to the middle of the surface (or None))
    """
    initial_hypocenter = rup.hypocenter
    surf_lons, surf_lats, surf_depths = rup.surface.get_surface_boundaries_3d()
    boundary_coords = list(zip(surf_lons, surf_lats, surf_depths))
    surface_polygon = Polygon(boundary_coords)
    hypocenter_point = Point(rup.hypocenter.x, rup.hypocenter.y, rup.hypocenter.z)
    warn = None
    if not surface_polygon.covers(hypocenter_point):
        surface_middle_point = rup.surface.get_middle_point()
        rup.hypocenter = surface_middle_point
        # removing '<' and '>' to avoid problems rendering the string in html
        initial_hypocenter_str = str(
            initial_hypocenter).replace('<', '').replace('>', '')
        surface_middle_point_str = str(
            surface_middle_point).replace('<', '').replace('>', '')
        warn = (f'The hypocenter ({initial_hypocenter_str}) was outside the surface'
                f' of the rupture, so it was moved to the middle point of the surface'
                f' ({surface_middle_point_str})')
        logging.warning(warn)
    return rup, warn


def _get_rup_dic_from_xml(usgs_id, user, rupture_file):
    err = {}
    try:
        [rup_node] = nrml.read(os.path.join(user.testdir, rupture_file)
                               if user.testdir else rupture_file)
    except ExpatError as exc:
        err = {"status": "failed",
               "error_msg": f'Unable to convert the rupture: {exc}'}
        return None, {}, err
    try:
        rup = sourceconverter.RuptureConverter(
            rupture_mesh_spacing=5.).convert_node(rup_node)
    except ValueError as exc:
        err = {"status": "failed",
               "error_msg": f'Unable to convert the rupture: {exc}'}
        return None, {}, err
    rup.tectonic_region_type = '*'
    rup, hypocenter_warning = adjust_hypocenter(rup)
    hp = rup.hypocenter
    rupdic = dict(lon=float(hp.x), lat=float(hp.y), dep=float(hp.z),
                  mag=float(rup.mag), rake=float(rup.rake),
                  strike=float(rup.surface.get_strike()),
                  dip=float(rup.surface.get_dip()),
                  usgs_id=usgs_id,
                  rupture_file=rupture_file)
    if hypocenter_warning:
        rupdic['warning_msg'] = hypocenter_warning
    return rup, rupdic, err


def _get_rup_dic_from_csv(usgs_id, user, rupture_file):
    err = {}
    try:
        [rup] = get_ruptures(os.path.join(user.testdir, rupture_file)
                             if user.testdir else rupture_file)
    except Exception as exc:
        err = {"status": "failed", "error_msg": str(exc)}
        return None, {}, err
    hp = rup.hypocenter
    rupdic = dict(lon=float(hp.x), lat=float(hp.y), dep=float(hp.z),
                  mag=float(rup.mag), rake=float(rup.rake),
                  strike=float(rup.surface.get_strike()),
                  dip=float(rup.surface.get_dip()),
                  usgs_id=usgs_id,
                  rupture_file=rupture_file)
    return rup, rupdic, err


def get_stations_from_usgs(usgs_id, user=User(), monitor=performance.Monitor(),
                           shakemap_version='usgs_preferred'):
    err = {}
    n_stations = 0
    try:
        usgs_id = valid.simple_id(usgs_id)
    except ValueError as exc:
        err = {'status': 'failed', 'error_msg': str(exc)}
        return None, n_stations, err
    contents, _properties, _shakemap, _shakemap_desc, err = \
        _contents_properties_shakemap(usgs_id, user, False, monitor, shakemap_version)
    if err:
        return None, n_stations, err
    with monitor('Downloading stations'):
        station_data_file, n_stations, err = download_station_data_file(
            usgs_id, contents, user)
    return station_data_file, n_stations, err


def ms_to_utc_date_time(ms):
    # convert from milliseconds to utc date time
    dt = datetime.utcfromtimestamp(ms / 1000)  # convert to seconds
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_shakemap_versions(usgs_id, user=User(), monitor=performance.Monitor()):
    err = {}
    usgs_preferred_version = None
    try:
        usgs_id = valid.simple_id(usgs_id)
    except ValueError as exc:
        err = {'status': 'failed', 'error_msg': str(exc)}
        return None, None, err
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
            return None, None, err

    js = json.loads(text)
    properties = js['properties']
    shakemaps = properties['products']['shakemap']
    usgs_preferred_shakemap = _get_usgs_preferred_item(shakemaps)
    usgs_preferred_version = usgs_preferred_shakemap['id']
    sorted_shakemaps = sorted(
        shakemaps, key=lambda x: x["updateTime"], reverse=True)
    shakemap_versions = [
        {'id': shakemap['id'],
         'number': shakemap['properties']['version'],
         'utc_date_time': ms_to_utc_date_time(shakemap['updateTime'])}
        for shakemap in sorted_shakemaps
        if 'version' in shakemap['properties']]
    return shakemap_versions, usgs_preferred_version, err


def _convert_rupture_file(inputdic, rupture_file, usgs_id, user):
    rup = None
    rupdic = {}
    rup_data = {}
    rupture_issue = {}
    if rupture_file.endswith('.json'):
        rupture_file_xml = gettemp(prefix='rup_', suffix='.xml')
        try:
            # replacing the input json file with the output xml if possible
            # NOTE: in case of failure, returns the input rupture_file (e.g. in case
            # of a Point rupture)
            rupture_file = convert_to_oq_xml(rupture_file, rupture_file_xml)
        except ValueError as exc:
            err = {"status": "failed", "error_msg": str(exc)}
            return None, {}, err
    if rupture_file.endswith('.xml'):
        rup, rupdic, rupture_issue = _get_rup_dic_from_xml(usgs_id, user, rupture_file)
    elif rupture_file.endswith('.csv'):
        rup, rupdic, rupture_issue = _get_rup_dic_from_csv(usgs_id, user, rupture_file)
    elif rupture_file.endswith('.json') and usgs_id != 'FromFile':
        with open(rupture_file) as f:
            rup_data = json.load(f)
    for key in inputdic:
        if inputdic[key] is not None and key not in rupdic:
            rupdic[key] = inputdic[key]
    return rup, rupdic, rup_data, rupture_issue


def make_rup_from_dic(inputdic, rupture_file):
    rup = None
    rupture_issue = None
    rupdic = inputdic.copy()
    rupdic.update(rupture_file=rupture_file)
    try:
        rup = build_planar_rupture_from_dict(rupdic)
    except ValueError as exc:
        rupture_issue = {"status": "failed", "error_msg": str(exc)}
    return rup, rupdic, rupture_issue


def get_rup_dic(inputdic, user=User(), use_shakemap=False,
                shakemap_version='usgs_preferred', rupture_file=None,
                monitor=performance.Monitor()):
    """
    If the rupture_file is None, download a rupture from the USGS site given
    the ShakeMap ID, else build the rupture locally with the given usgs_id.

    NOTE: this function is called twice by impact_validate: first when
    retrieving rupture data, then when running the job.

    :param inputdic:
        dictionary with ShakeMap ID and other parameters
    :param user:
       User instance
    :param use_shakemap:
        download the ShakeMap only if True
    :param shakemap_version:
        id of the ShakeMap to be used (if the ShakeMap is used)
    :param rupture_file:
        None
    :returns:
        (rupture object or None, rupture dictionary, error dictionary or {})
    """
    rupdic = {}
    rup_data = {}
    err = {}
    usgs_id = inputdic['usgs_id']
    approach = inputdic['approach']
    rup = None
    rupture_issue = None
    if approach == 'provide_rup_params':
        return make_rup_from_dic(inputdic, rupture_file)
    if rupture_file:
        rup, rupdic, rup_data, rupture_issue = _convert_rupture_file(
            inputdic, rupture_file, usgs_id, user)
        if rupture_issue or usgs_id == 'FromFile':
            return rup, rupdic, rupture_issue
    assert usgs_id
    get_grid = user.level == 1 or use_shakemap
    contents, properties, shakemap, shakemap_desc, err = \
        _contents_properties_shakemap(usgs_id, user, get_grid, monitor,
                                      shakemap_version)
    if err:
        return None, None, err
    if approach in ['use_pnt_rup_from_usgs', 'build_rup_from_usgs']:
        if inputdic.get('lon') is None:  # don't override user-inserted values
            rupdic, err = load_rupdic_from_origin(
                usgs_id, properties['products'])
            if err:
                return None, None, err
        else:
            rupdic = inputdic.copy()
    elif 'download/rupture.json' not in contents:
        # happens for us6000f65h in parsers_test
        rupdic, err = load_rupdic_from_finite_fault(
            usgs_id, properties['mag'], properties['products'])
        if err:
            return None, None, err
    if not rup_data and approach not in ['use_pnt_rup_from_usgs',
                                         'build_rup_from_usgs']:
        if approach in ['use_shakemap_from_usgs', 'use_shakemap_fault_rup_from_usgs',
                        'use_finite_fault_model_from_usgs']:
            if approach == 'use_finite_fault_model_from_usgs':
                with monitor('Download finite fault rupture'):
                    rupture_file, err = download_finite_fault_rupture(
                        usgs_id, user, monitor)
                    if err:
                        return None, None, err
            else:  # 'use_shakemap_from_usgs' or 'use_shakemap_fault_rup_from_usgs'
                with monitor('Downloading rupture json'):
                    rup_data, rupture_file = download_shakemap_rupture_data(
                        usgs_id, contents, user)
            if rupture_file:
                rup, rupdic, updated_rup_data, rupture_issue = _convert_rupture_file(
                    inputdic, rupture_file, usgs_id, user)
                if updated_rup_data:
                    rup_data = updated_rup_data
            elif approach in ['use_shakemap_fault_rup_from_usgs',
                              'use_finite_fault_model_from_usgs']:
                err = {"status": "failed",
                       "error_msg": 'Unable to retrieve rupture geometries'}
                return None, None, err
    if 'lon' not in rupdic:  # rupdic was incompletely filled
        rupdic = convert_rup_data(rup_data, usgs_id, rupture_file, shakemap)
    for key in inputdic:
        if inputdic[key] is not None and key not in rupdic:
            rupdic[key] = inputdic[key]
    if 'mmi_file' not in rupdic:
        rupdic['mmi_file'] = download_mmi(usgs_id, contents, user)
    if approach == 'use_shakemap_from_usgs':
        rupdic['shakemap_array'] = shakemap
    rupdic['title'] = properties['title']
    rupdic['shakemap_desc'] = shakemap_desc
    if not rup and not rup_data:  # in parsers_test
        if approach == 'use_pnt_rup_from_usgs':
            rupdic['msr'] = 'PointMSR'
        try:
            rup = build_planar_rupture_from_dict(rupdic)
        except ValueError as exc:
            err = {"status": "failed", "error_msg": str(exc)}
        return rup, rupdic, err
    elif (not rup and len(rup_data['features']) == 1
            and rup_data['features'][0]['geometry']['type'] == 'Point'):
        # TODO: we can remove this when OQ can handle xml with Point ruptures
        rupdic['msr'] = 'PointMSR'
        try:
            rup = build_planar_rupture_from_dict(rupdic)
        except ValueError as exc:
            rupture_issue = {"status": "failed", "error_msg": str(exc)}
    if rupture_issue and user.level > 1:  # in parsers_test for us6000jllz
        # NOTE: hiding rupture-related issues to level 1 users
        rupdic['rupture_issue'] = rupture_issue['error_msg']
    return rup, rupdic, err


# tested in the nightly tests aristotle_run
# the default argument is needed to avoid an
# error in is_valid_shakemap
def get_array_usgs_id(kind, id, contents={}):
    """
    Download a ShakeMap from the USGS site.

    :param kind: the string "usgs_id", for API compatibility
    :param id: ShakeMap ID
    :param contents: a dictionary containing 'download/grid.xml'
    """
    grid = contents.get('download/grid.xml')
    if not grid:
        raise MissingLink('Could not find grid.xml link for %s' % id)
    uncertainty = contents.get('download/uncertainty.xml.zip') or contents.get(
        'download/uncertainty.xml')
    if not uncertainty:
        logging.warning('No uncertainty.xml file')
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
    if (uncertainty and 'STDPSA06' not in idx) or (
            not uncertainty and 'PSA06' not in idx):
        # old shakemap
        fieldmap = {f: FIELDMAP[f] for f in FIELDMAP if f != 'PSA06'}
    else:  # new shakemap
        fieldmap = FIELDMAP
        missing = REQUIRED_IMTS - set(idx)
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
