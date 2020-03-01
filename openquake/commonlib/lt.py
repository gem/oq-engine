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

from openquake.baselib.general import CallableDict
from openquake.hazardlib import geo
from openquake.hazardlib.sourceconverter import (
    split_coords_2d, split_coords_3d)

parse_uncertainty = CallableDict(
    keymissing=lambda utype, node: float(node.text.strip()))


@parse_uncertainty.add('sourceModel', 'extendModel')
def smodel(utype, node):
    return node.text.strip()


@parse_uncertainty.add('abGRAbsolute')
def abGR(utype, node):
    [a, b] = node.text.strip().split()
    return float(a), float(b)


@parse_uncertainty.add('incrementalMFDAbsolute')
def incMFD(utype, node):
    min_mag, bin_width = (node.incrementalMFD["minMag"],
                          node.incrementalMFD["binWidth"])
    return min_mag,  bin_width, ~node.incrementalMFD.occurRates


@parse_uncertainty.add('simpleFaultGeometryAbsolute')
def simpleGeom(utype, node):
    return _parse_simple_fault_geometry_surface(node.simpleFaultGeometry)


@parse_uncertainty.add('complexFaultGeometryAbsolute')
def complexGeom(utype, node):
    return _parse_complex_fault_geometry_surface(node.complexFaultGeometry)


@parse_uncertainty.add('characteristicFaultGeometryAbsolute')
def charGeom(utype, node):
    surfaces = []
    for geom_node in node.surface:
        if "simpleFaultGeometry" in geom_node.tag:
            trace, usd, lsd, dip, spacing =\
                _parse_simple_fault_geometry_surface(geom_node)
            surfaces.append(geo.SimpleFaultSurface.from_fault_data(
                trace, usd, lsd, dip, spacing))
        elif "complexFaultGeometry" in geom_node.tag:
            edges, spacing =\
                _parse_complex_fault_geometry_surface(geom_node)
            surfaces.append(geo.ComplexFaultSurface.from_fault_data(
                edges, spacing))
        elif "planarSurface" in geom_node.tag:
            surfaces.append(
                _parse_planar_geometry_surface(geom_node))
        else:
            pass
    if len(surfaces) > 1:
        return geo.MultiSurface(surfaces)
    else:
        return surfaces[0]


def _parse_simple_fault_geometry_surface(node):
    spacing = node["spacing"]
    usd, lsd, dip = (~node.upperSeismoDepth, ~node.lowerSeismoDepth,
                     ~node.dip)
    # Parse the geometry
    coords = split_coords_2d(~node.LineString.posList)
    trace = geo.Line([geo.Point(*p) for p in coords])
    return trace, usd, lsd, dip, spacing


def _parse_complex_fault_geometry_surface(node):
    spacing = node["spacing"]
    edges = []
    for edge_node in node.nodes:
        coords = split_coords_3d(~edge_node.LineString.posList)
        edges.append(geo.Line([geo.Point(*p) for p in coords]))
    return edges, spacing


def _parse_planar_geometry_surface(node):
    nodes = []
    for key in ["topLeft", "topRight", "bottomRight", "bottomLeft"]:
        nodes.append(geo.Point(getattr(node, key)["lon"],
                               getattr(node, key)["lat"],
                               getattr(node, key)["depth"]))
    top_left, top_right, bottom_right, bottom_left = tuple(nodes)
    return geo.PlanarSurface.from_corner_points(
        top_left, top_right, bottom_right, bottom_left)
