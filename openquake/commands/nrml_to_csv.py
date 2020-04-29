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
from openquake.baselib import sap
from openquake.hazardlib import nrml, sourceconverter
from openquake.commonlib.writers import write_csv


converter = sourceconverter.RowConverter()


# https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry
def appendrow(row, rows):
    wkt = row.wkt
    if wkt.startswith('POINT'):
        rows[1].append(row)
    elif wkt.startswith('LINESTRING'):
        rows[2].append(row)
    elif wkt.startswith('POLYGON'):
        rows[3].append(row)
    elif wkt.startswith('MULTIPOINT'):
        rows[4].append(row)
    elif wkt.startswith('MULTILINESTRING'):
        rows[5].append(row)
    elif wkt.startswith('MULTIPOLYGON'):
        rows[6].append(row)
    print('=' * 79)
    for col in row._fields:
        print(col, getattr(row, col))


@sap.Script
def nrml_to_csv(fnames, outdir='.'):
    for fname in fnames:
        name = os.path.basename(fname)[:-4]  # strip .xml
        root = nrml.read(fname)
        srcs = collections.defaultdict(list)  # geom_index -> rows
        if 'nrml/0.4' in root['xmlns']:
            for srcnode in root.sourceModel:
                appendrow(converter.convert_node(srcnode), srcs)
        else:
            for srcgroup in root.sourceModel:
                trt = srcgroup['tectonicRegion']
                for srcnode in srcgroup:
                    srcnode['tectonicRegion'] = trt
                    appendrow(converter.convert_node(srcnode), srcs)
        for idx, rows in srcs.items():
            dest = os.path.join(outdir, '%s_%d.csv' % (name, idx))
            logging.info('Saving %s', dest)
            write_csv(dest, rows, header=rows[0]._fields)


nrml_to_csv.arg('fnames', 'source model files in XML', nargs='+')
nrml_to_csv.arg('outdir', 'output directory')
