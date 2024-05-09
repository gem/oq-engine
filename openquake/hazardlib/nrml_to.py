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
import numpy
import shapely.wkt
from openquake.baselib.writers import write_csv
from openquake.hazardlib import nrml, sourceconverter
from openquake.hazardlib.geo.packager import GeoPackager


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
def appendrow(row, rows, chatty, sections=(), s2i={}):
    if row.code == 'F':
        # row.coords is a multiFaultSource
        # in this case the gpkg is not a complete representation,
        # it just contains the top of rupture coordinates
        rupture_idxs = [tuple(s2i[idx] for idx in idxs)
                        for idxs in row.coords._rupture_idxs]
        row.coords = []
        for idxs in rupture_idxs:
            coos = [sections[idx].tor.coo[:, 0:2] for idx in idxs]
            row.coords.append(numpy.concatenate(coos))
    row.wkt = wkt = to_wkt(row.geom, row.coords)
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
        for col in row.__class__.__annotations__:
            print(col, getattr(row, col))
        try:
            shapely.wkt.loads(wkt)  # sanity check
        except Exception as exc:
            raise exc.__class__(wkt)


def to_tuple(row):
    """
    Convert a source Row into a tuple
    """
    ns = [a for a in row.__class__.__annotations__ if a not in 'geom coords']
    return tuple(getattr(row, n) for n in ns)

def convert_to_csv(name, srcs, srcmodel_attrib, srcgroups_attribs, outdir):
    for kind, rows in srcs.items():
        dest = os.path.join(outdir, '%s_%s.csv' % (name, kind))
        logging.info('Saving %d sources on %s', len(rows), dest)
        header = [a for a in rows[0].__class__.__annotations__
                  if a not in 'geom coords']
        write_csv(dest, map(to_tuple, rows), header=header)
        logging.info('%s was created' % dest)
    if srcmodel_attrib:
        dest = os.path.join(outdir, 'source_model.csv')
        header = [k for k in srcmodel_attrib.keys()
                  if k != 'kind']
        logging.info('Saving source model information')
        srcmodel_rows = [(srcmodel_attrib[k] for k in header)]
        write_csv(dest, srcmodel_rows, header=header)
        logging.info('%s was created' % dest)
    if srcgroups_attribs:
        dest = os.path.join(outdir, 'source_groups.csv')
        header = [k for k in srcgroups_attribs[0].keys()
                  if k != 'kind']
        logging.info('Saving source groups information')
        srcgroups_attribs_no_kind = [
            {k: v for (k, v) in srcgroups_attribs[i].items()
             if k != 'kind'}
            for i in range(len(srcgroups_attribs))]
        srcgroups_rows = [
            tuple(srcgroups_attribs_no_kind[i].values())
            for i in range(len(srcgroups_attribs_no_kind))]
        write_csv(dest, srcgroups_rows, header=header)
        logging.info('%s was created' % dest)


def convert_to_gpkg(name, srcs, srcmodel_attrib, srcgroups_attribs, outdir):
    dest = os.path.join(outdir, name + '.gpkg')
    gpkg = GeoPackager(dest)
    for kind, rows in srcs.items():
        logging.info('Saving %d sources on layer %s', len(rows), kind)
        gpkg.save_layer(kind, rows)
    if srcmodel_attrib:
        logging.info('Saving source model information')
        gpkg.save_table('source_model', [srcmodel_attrib])
    if srcgroups_attribs:
        logging.info('Saving source groups information')
        gpkg.save_table('source_groups', srcgroups_attribs)
    logging.info('%s was created' % dest)

    
def convert_to(fmt, fnames, chatty=False, *, outdir='.', geometry=''):
    """
    Convert source models into CSV files (or geopackages, if fiona is
    installed).
    """
    t0 = time.time()
    if geometry:
        fnames = [geometry] + fnames
    sections = []
    i, s2i = 0, {}
    for fname in fnames:
        logging.info('Reading %s', fname)
        converter.fname = fname
        name, _ext = os.path.splitext(os.path.basename(fname))
        root = nrml.read(fname)
        srcs = collections.defaultdict(list)  # geom_index -> rows
        srcgroups_attribs = []
        srcmodel_attrib = {}
        if fname == geometry:
            for srcnode in root.geometryModel:
                sec = converter.convert_node(srcnode)
                sections.append(sec)
                s2i[srcnode['id']] = i
                i += 1
        else:
            srcmodel_attrib = root.sourceModel.attrib
            srcmodel_attrib['kind'] = 'sourceModel'
            if 'nrml/0.4' in root['xmlns']:
                for srcnode in root.sourceModel:
                    row = converter.convert_node(srcnode)
                    appendrow(row, srcs, chatty, sections, s2i)
            else:  # nrml/0.5
                for idx, srcgroup in enumerate(root.sourceModel):
                    attrib = srcgroup.attrib
                    attrib['kind'] = 'sourceGroup'
                    # NOTE: in some cases the source group has no name, so we
                    #       need to assign it a unique name
                    if 'name' not in attrib:
                        attrib['name'] = str(idx)  # let name always be a str
                    srcgroups_attribs.append(attrib)
                    try:
                        grp_trt = attrib['tectonicRegion']
                    except KeyError:
                        grp_trt = None
                    for srcnode in srcgroup:
                        try:
                            srcnode['groupname'] = srcgroup.attrib['name']
                        except KeyError:
                            srcnode['groupname'] = ''

                        # NOTE: the following condition would avoid duplicating
                        # tectonicRegion into each source of a group for which
                        # the tectonicRegion is already specified. We are
                        # intentionally keeping the duplication in order to
                        # make it possible to read the information directly
                        # from the source section via old scripts.
                        # if (not srcnode['groupname'] and
                        #     grp_trt and not srcnode.get('tectonicRegion')):
                        if grp_trt and not srcnode.get('tectonicRegion'):
                            srcnode['tectonicRegion'] = grp_trt
                        row = converter.convert_node(srcnode)
                        appendrow(row, srcs, chatty, sections, s2i)
        if fmt == 'csv':
            convert_to_csv(name, srcs, srcmodel_attrib, srcgroups_attribs, outdir)
        else:  # gpkg
            convert_to_gpkg(name, srcs, srcmodel_attrib, srcgroups_attribs, outdir)
    logging.info('Finished in %d seconds', time.time() - t0)
