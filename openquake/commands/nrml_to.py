# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
Convert a source model file in .xml format into a bunch of .csv files,
one per geometry type, being

1 = point
2 = linestring
3 = polygon
4 = multipoint
5 = multilinestring
6 = multipolygon
"""
import os
import time
import logging
import collections
import shapely.wkt
from openquake.hazardlib import nrml, sourceconverter
from openquake.hazardlib.geo.packager import GeoPackager, fiona
from openquake.commonlib.writers import write_csv


converter = sourceconverter.RowConverter()


def to_str(coords, ndim=2):
    coords[0][0]  # sanity check
    if ndim == 2:
        return ', '. join('%.5f %5f' % tuple(point) for point in coords)
    else:  # 3D
        return ', '. join('%.5f %.5f %.5f' % tuple(p) for p in coords)


def multi_str(coords, ndim=2):
    coords[0][0][0]  # sanity check
    if ndim == 2:
        return ', '. join('(%s)' % to_str(p, 2) for p in coords)
    else:  # 3D
        return ', '. join('(%s)' % to_str(p, 3) for p in coords)


def to_wkt(geom, coords):
    """
    Convert a fiona geometry string and a set of coordinates into WKT:

    >>> to_wkt('Point', [1, 2])
    'POINT(1.00000 2.00000)'
    >>> to_wkt('3D Point', [1, 2, 3])
    'POINT Z(1.00000 2.00000 3.00000)'
    >>> to_wkt('LineString', [[1, 2], [3, 4]])
    'LINESTRING(1.00000 2.000000, 3.00000 4.000000)'
    >>> to_wkt('3D LineString', [[1, 2, 3], [4, 5, 6]])
    'LINESTRING Z(1.00000 2.00000 3.00000, 4.00000 5.00000 6.00000)'
    >>> to_wkt('MultiPoint', [[1, 2], [4, 5]])
    'MULTIPOINT(1.00000 2.000000, 4.00000 5.000000)'
    >>> to_wkt('3D MultiLineString', [[[1, 2, 3], [4, 5, 6]],
    ...        [[.1, .2, .3], [.4, .5, .6]]])
    'MULTILINESTRING Z((1.00000 2.00000 3.00000, 4.00000 5.00000 6.00000), (0.10000 0.20000 0.30000, 0.40000 0.50000 0.60000))'
    >>> to_wkt('3D MultiPolygon', [[[[1, 2, 3], [4, 5, 6]],
    ...        [[.1, .2, .3], [.4, .5, .6]]]])
    'MULTIPOLYGON Z(((1.00000 2.00000 3.00000, 4.00000 5.00000 6.00000), (0.10000 0.20000 0.30000, 0.40000 0.50000 0.60000)))'
    """
    if geom == 'Point':
        return 'POINT(%.5f %.5f)' % tuple(coords)
    elif geom == '3D Point':
        return 'POINT Z(%.5f %.5f %.5f)' % tuple(coords)
    elif geom == 'LineString':
        return 'LINESTRING(%s)' % to_str(coords)
    elif geom == '3D LineString':
        return 'LINESTRING Z(%s)' % to_str(coords, 3)
    elif geom == 'Polygon':
        return 'POLYGON(%s)' % multi_str(coords)
    elif geom == 'MultiPoint':
        return 'MULTIPOINT(%s)' % to_str(coords)
    elif geom == '3D MultiLineString':
        return 'MULTILINESTRING Z(%s)' % multi_str(coords, 3)
    elif geom == '3D MultiPolygon':
        return 'MULTIPOLYGON Z((%s))' % multi_str(coords[0], 3)
    else:
        raise NotImplementedError(geom)


# https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry
def appendrow(row, rows, chatty):
    wkt = to_wkt(row.geom, row.coords)
    if wkt.startswith('POINT'):
        rows[row.code + '1'].append(row)
    elif wkt.startswith('LINESTRING'):
        rows[row.code + '2'].append(row)
    elif wkt.startswith('POLYGON'):
        rows[row.code + '3'].append(row)
    elif wkt.startswith('MULTIPOINT'):
        rows[row.code + '4'].append(row)
    elif wkt.startswith('MULTILINESTRING'):
        rows[row.code + '5'].append(row)
    elif wkt.startswith('MULTIPOLYGON'):
        rows[row.code + '6'].append(row)
    if chatty:
        print('=' * 79)
        for col in row._fields:
            print(col, getattr(row, col))
        try:
            shapely.wkt.loads(wkt)  # sanity check
        except Exception as exc:
            raise exc.__class__(wkt)


def main(what, fnames, chatty=False, *, outdir='.'):
    """
    Convert source models into CSV files (or geopackages, if fiona is
    installed).
    """
    t0 = time.time()
    for fname in fnames:
        logging.info('Reading %s', fname)
        converter.fname = fname
        name, _ext = os.path.splitext(os.path.basename(fname))
        root = nrml.read(fname)
        srcs = collections.defaultdict(list)  # geom_index -> rows
        if 'nrml/0.4' in root['xmlns']:
            for srcnode in root.sourceModel:
                appendrow(converter.convert_node(srcnode), srcs, chatty)
        else:
            for srcgroup in root.sourceModel:
                trt = srcgroup['tectonicRegion']
                for srcnode in srcgroup:
                    srcnode['tectonicRegion'] = trt
                    appendrow(converter.convert_node(srcnode), srcs, chatty)
        if what == 'csv':
            for kind, rows in srcs.items():
                dest = os.path.join(outdir, '%s_%s.csv' % (name, kind))
                logging.info('Saving %d sources on %s', len(rows), dest)
                tups = []
                for row in rows:
                    tup = row[:-2] + (to_wkt(*row[-2:]),)
                    tups.append(tup)
                header = rows[0]._fields[:-2] + ('wkt',)
                write_csv(dest, tups, header=header)
        else:  # gpkg
            gpkg = GeoPackager(name + '.gpkg')
            for kind, rows in srcs.items():
                logging.info('Saving %d sources on layer %s', len(rows), kind)
                gpkg.save_layer(kind, rows)
    logging.info('Finished in %d seconds', time.time() - t0)


main.what = dict(help='csv or gpkg',
                 choices=['csv', 'gpkg'] if fiona else ['csv'])
main.fnames = dict(help='source model files in XML', nargs='+')
main.chatty = 'display sources in progress'
main.outdir = 'output directory'
