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
import logging
import collections
import shapely.wkt
from openquake.baselib import sap
from openquake.hazardlib import nrml, sourceconverter
from openquake.commonlib.writers import write_csv


converter = sourceconverter.RowConverter()


# https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry
def appendrow(row, rows, chatty):
    wkt = row.wkt
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


@sap.Script
def nrml_to_csv(fnames, outdir='.', chatty=False):
    for fname in fnames:
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
        for kind, rows in srcs.items():
            dest = os.path.join(outdir, '%s_%s.csv' % (name, kind))
            logging.info('Saving %s', dest)
            write_csv(dest, rows, header=rows[0]._fields)


nrml_to_csv.arg('fnames', 'source model files in XML', nargs='+')
nrml_to_csv.arg('outdir', 'output directory')
nrml_to_csv.flg('chatty', 'display sources')
