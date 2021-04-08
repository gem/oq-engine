# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2021 GEM Foundation
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
import io
import pathlib
import logging
import json
import zipfile

import numpy
from openquake.baselib.general import CallableDict
from openquake.baselib.node import node_from_xml
from openquake.hazardlib.shakemap.shape import shapefile_to_shakemap


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
        try:
            return z.open(fname)
        except KeyError:
            # for instance the ShakeMap ci3031111 has inside a file
            # data/verified_atlas2.0/reviewed/19920628115739/output/
            # uncertainty.xml
            # instead of just uncertainty.xml
            zinfo = z.filelist[0]
            if zinfo.filename.endswith(fname):
                return z.open(zinfo)
            else:
                raise


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
        else:
            raise FileNotFoundError(
                'The following path could not be found: %s' % url)
    return url


get_array = CallableDict()


@get_array.add('shapefile')
def get_array_shapefile(kind, fname):
    if not fname.startswith('http'):
        fname = 'file:' + pathname2url(str(pathlib.Path(fname).absolute()))
    return shapefile_to_shakemap(fname)


@get_array.add('usgs_xml')
def get_array_usgs_xml(kind, grid_url, uncertainty_url=None):

    grid_url = path2url(grid_url)

    if uncertainty_url is None:
        with urlopen(grid_url) as f:
            return get_shakemap_array(f)
    else:
        with urlopen(grid_url) as f1, urlextract(
                path2url(uncertainty_url), 'uncertainty.xml') as f2:
            return get_shakemap_array(f1, f2)


@get_array.add('usgs_id')
def get_array_usgs_id(kind, id):
    url = SHAKEMAP_URL.format(id)
    logging.info('Downloading %s', url)
    contents = json.loads(urlopen(url).read())[
        'properties']['products']['shakemap'][-1]['contents']
    grid = contents.get('download/grid.xml')
    if grid is None:
        raise MissingLink('Could not find grid.xml link in %s' % url)
    uncertainty = contents.get('download/uncertainty.xml.zip') or contents.get(
        'download/uncertainty.xml')
    return get_array('usgs_xml', grid['url'],
                     uncertainty['url'] if uncertainty else None)


@get_array.add('file_npy')
def get_array_file_npy(kind, fname):
    return numpy.load(fname)


def _get_shakemap_array(xml_file):
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
