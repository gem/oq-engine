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

import io
import os
import pathlib
import logging
import json
import zipfile
from shapely.geometry import Polygon
import numpy
from openquake.baselib.node import node_from_xml


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


def get_array_usgs_id(kind, id):
    """
    Download a ShakeMap from the USGS site
    """
    url = SHAKEMAP_URL.format(id)
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
