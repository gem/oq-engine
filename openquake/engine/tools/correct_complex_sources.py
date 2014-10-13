"""
Correct complex fault sources to comply with Aki and Richards convention.
"""
import sys
import numpy

from openquake.commonlib import nrml
from openquake.commonlib.node import node_from_xml

from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.surface import ComplexFaultSurface

AKI_RICH_ERR_MSG = 'Surface does not conform with Aki & Richards convention'
WRONG_ORDER_ERR_MSG = 'Edges points are not in the right order'


def make_edge(edge):
    ls = edge.LineString.posList.text.split()
    coords = numpy.array(map(float, ls)).reshape(-1, 3)
    return Line([Point(*coord) for coord in coords])


def reverse(edge):
    poslist = map(float, edge.LineString.posList.text.split())
    coords = numpy.array(poslist).reshape(-1, 3)[::-1]  # reversing
    text = '\n'.join('%s %s %s' % tuple(coord) for coord in coords)
    edge.LineString.posList.text = text


def fix_source_node(node):
    if node.tag.endswith('complexFaultSource'):
        geom = node.complexFaultGeometry
        top = geom.faultTopEdge
        intermediate = [edge for edge in geom.getnodes('intermediateEdge')]
        bottom = geom.faultBottomEdge
        edges = map(make_edge, [top] + intermediate + [bottom])
        try:
            ComplexFaultSurface.from_fault_data(edges, mesh_spacing=4.)
        except ValueError as excp:
            if AKI_RICH_ERR_MSG in str(excp):
                print str(excp)
                print 'Reverting edges ...'
                reverse(geom.faultTopEdge)
                reverse(geom.faultBottomEdge)
            elif WRONG_ORDER_ERR_MSG in str(excp):
                print str(excp)
                print 'reverting bottom edge ...'
                reverse(geom.faultBottomEdge)
            else:
                raise

if __name__ == '__main__':
    fname = sys.argv[1]
    src_model = node_from_xml(fname).sourceModel
    for node in src_model:
        fix_source_node(node)
    with open(fname, 'w') as f:
        nrml.write([src_model], f)
