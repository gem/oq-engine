#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
Correct complex fault sources to comply with Aki and Richards convention.
"""
import numpy

from openquake.risklib import valid
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.surface import ComplexFaultSurface
from openquake.hazardlib import mfd

AKI_RICH_ERR_MSG = 'Surface does not conform with Aki & Richards convention'
WRONG_ORDER_ERR_MSG = 'Edges points are not in the right order'


def node_to_edge(edge_node):
    """

    """
    # LS Nodes
    ls_node = edge_node.nodes[0]
    poslist_node = ls_node.nodes[0]
    pos_list = numpy.array(map(float,
                           poslist_node.text.split())).reshape(-1, 3)
    return Line([Point(*crd) for crd in pos_list])


def get_complex_fault_geometry(node, mesh_spacing=5.):
    """

    """
    assert "complexFaultGeometry" in node.tag
    intermediate_edges = []
    for edge in node.nodes:
        if "faultTopEdge" in edge.tag:
            top_edge = [node_to_edge(edge)]
        elif "faultBottomEdge" in edge.tag:
            bottom_edge = [node_to_edge(edge)]
        elif "intermediateEdge" in edge.tag:
            intermediate_edges.append(node_to_edge(edge))
        else:
            pass
    edges = top_edge + intermediate_edges + bottom_edge
    try:
        surface = ComplexFaultSurface.from_fault_data(edges, mesh_spacing)
    except ValueError as excp:
        if AKI_RICH_ERR_MSG in str(excp):
            # Reverse top and bottom edges
            edges[0].points = edges[0].points[::-1]
            edges[-1].points = edges[-1].points[::-1]
        elif WRONG_ORDER_ERR_MSG in str(excp):
            # Revese bottom edge only
            edges[-1].points = edges[-1].points[::-1]
        else:
            raise
        surface = ComplexFaultSurface.from_fault_data(edges, mesh_spacing)
    return edges


def get_complex_fault_source(cflt, tom, mfd_bin_width=0.1, mesh_spacing=4.0):
    """

    """
    (i_d, name, trt) = (cflt.attrib["id"], cflt.attrib["name"],
                        cflt.attrib["tectonicRegion"])
    for node in cflt.nodes:
        if "complexFaultGeometry" in node.tag:
            geom = get_complex_fault_geometry(node, mesh_spacing)
        elif "magScaleRel" in node.tag:
            msr = valid.SCALEREL[node.text.strip()]
        elif "ruptAspectRatio" in node.tag:
            aspect = float(node.text.strip())
        elif "incrementalMFD" in node.tag:
            mfd0 = mfd.EvenlyDiscretizedMFD(
                min_mag=node.attrib["minMag"],
                bin_width=node.attrib["binWidth"],
                occurrence_rates=map(float, node.nodes[0].text.split()))
        elif "truncGutenbergRichterMFD" in node.tag:
            mfd0 = mfd.TruncatedGRMFD(
                a_val=node.attrib["aValue"],
                b_val=node.attrib["bValue"],
                min_mag=node.attrib["minMag"],
                max_mag=node.attrib["maxMag"],
                bin_width=mfd_bin_width)
        elif "rake" in node.tag:
            rake = float(node.text.strip())
        else:
            # There shouldn't be anything else, but pass anyway
            pass
    return ComplexFaultsource(
        source_id=i_d,
        name=name,
        tectonic_region_type=trt,
        mfd=mfd0,
        rupture_mesh_spacing=mesh_spacing,
        magnitude_scaling_relationship=msr,
        rupture_aspect_ratio=aspect,
        edges=geom,
        rake=rake,
        temporal_occurrence_model=tom)


def make_edge(edge):
    ls = edge.LineString.posList.text
    coords = numpy.array(map(float, ls)).reshape(-1, 3)
    return Line([Point(*coord) for coord in coords])


def reverse(edge):
    poslist = map(float, edge.LineString.posList.text)
    coords = numpy.array(poslist).reshape(-1, 3)[::-1]  # reversing
    edge.LineString.posList.text = coords


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
