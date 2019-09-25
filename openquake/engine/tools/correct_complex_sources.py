# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Correct complex fault sources to comply with Aki and Richards convention.
"""
import sys
import numpy

from openquake.hazardlib import nrml

from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.surface import ComplexFaultSurface

AKI_RICH_ERR_MSG = 'Surface does not conform with Aki & Richards convention'
WRONG_ORDER_ERR_MSG = 'Edges points are not in the right order'


def make_edge(edge):
    ls = ~edge.LineString.posList
    coords = numpy.array(ls).reshape(-1, 3)
    return Line([Point(*coord) for coord in coords])


def reverse(edge):
    poslist = ~edge.LineString.posList
    coords = numpy.array(poslist).reshape(-1, 3)[::-1]  # reversing
    text = '\n'.join('%s %s %s' % tuple(coord) for coord in coords)
    edge.LineString.posList.text = text


def fix_source_node(node):
    if node.tag.endswith('complexFaultSource'):
        geom = node.complexFaultGeometry
        top = geom.faultTopEdge
        intermediate = [edge for edge in geom.getnodes('intermediateEdge')]
        bottom = geom.faultBottomEdge
        edges = list(map(make_edge, [top] + intermediate + [bottom]))
        try:
            ComplexFaultSurface.from_fault_data(edges, mesh_spacing=4.)
        except ValueError as excp:
            if AKI_RICH_ERR_MSG in str(excp):
                print(excp)
                print('Reverting edges ...')
                reverse(geom.faultTopEdge)
                reverse(geom.faultBottomEdge)
            elif WRONG_ORDER_ERR_MSG in str(excp):
                print(excp)
                print('reverting bottom edge ...')
                reverse(geom.faultBottomEdge)
            else:
                raise


def fix(fname, outname=None):
    root = nrml.read(fname)
    xmlns = root['xmlns']
    if xmlns == u'http://openquake.org/xmlns/nrml/0.4':
        for src_node in root.sourceModel:
            fix_source_node(src_node)
    else:  # nrml/0.5+
        for src_grp in root.sourceModel:
            for src_node in src_grp:
                fix_source_node(src_node)
    with open(outname or fname, 'wb') as out:
        nrml.write([root.sourceModel], out, xmlns=xmlns)

if __name__ == '__main__':
    fname = sys.argv[1]
    fix(fname)
