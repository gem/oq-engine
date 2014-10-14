"""
Correct complex fault sources to comply with Aki and Richards convention.
"""
import sys
import numpy

from openquake.nrmllib.hazard.parsers import SourceModelParser
from openquake.nrmllib.hazard.writers import SourceModelXMLWriter
from openquake.nrmllib.models import ComplexFaultSource, SourceModel

from openquake.commonlib.source import NrmlHazardlibConverter

AKI_RICH_ERR_MSG = 'Surface does not conform with Aki & Richards convention'
WRONG_ORDER_ERR_MSG = 'Edges points are not in the right order'


def _revert_edge(edge_wkt):
    """
    Revert edge in WKT format
    """
    edge = edge_wkt.replace('LINESTRING(', '')
    edge = edge.replace(')', '')
    edge = edge.replace(',', '')

    edge = numpy.array(edge.split(), dtype=float)
    edge = edge.reshape(-1, 3)

    # revert
    edge = edge[::-1]

    # place reverted edge in WKT format
    edge = ','.join('%s %s %s' % (lon, lat, depth) for lon, lat, depth in edge)
    edge = 'LINESTRING(%s)' % edge

    return edge


if __name__ == '__main__':

    converter = NrmlHazardlibConverter(
        investigation_time=50, rupture_mesh_spacing=4,
        width_of_mfd_bin=0.2, area_source_discretization=10)

    srcm = SourceModelParser(sys.argv[1]).parse()

    srcs = []
    for src in srcm:
        if isinstance(src, ComplexFaultSource):
            try:
                hazlib_src = converter(src)
            except ValueError, excp:
                if AKI_RICH_ERR_MSG in str(excp):
                    print str(excp)
                    print 'Reverting edges ...'
                    top_edge = _revert_edge(src.geometry.top_edge_wkt)
                    bottom_edge = _revert_edge(src.geometry.bottom_edge_wkt)

                    # replace old edges with reverted edges
                    src.geometry.top_edge_wkt = top_edge
                    src.geometry.bottom_edge_wkt = bottom_edge

                elif WRONG_ORDER_ERR_MSG in str(excp):
                    print str(excp)
                    print 'reverting bottom edge ...'

                    assert len(src.geometry.int_edges) == 0
                    # revert just the bottom edge
                    bottom_edge = _revert_edge(src.geometry.bottom_edge_wkt)
                    src.geometry.bottom_edge_wkt = bottom_edge

                else:
                    raise excp
            finally:
                srcs.append(src)
        else:
            srcs.append(src)

    new_srcm = SourceModel(srcm.name, srcs)

    w = SourceModelXMLWriter(sys.argv[1])
    w.serialize(new_srcm)
