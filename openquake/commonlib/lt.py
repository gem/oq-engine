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

import copy

from openquake.baselib.general import CallableDict
from openquake.hazardlib import geo
from openquake.hazardlib.sourceconverter import (
    split_coords_2d, split_coords_3d)


class LogicTreeError(Exception):
    """
    Logic tree file contains a logic error.

    :param node:
        XML node object that causes fail. Used to determine
        the affected line number.

    All other constructor parameters are passed to :class:`superclass'
    <LogicTreeError>` constructor.
    """
    def __init__(self, node, filename, message):
        self.filename = filename
        self.message = message
        self.lineno = node if isinstance(node, int) else getattr(
            node, 'lineno', '?')

    def __str__(self):
        return "filename '%s', line %s: %s" % (
            self.filename, self.lineno, self.message)


#                           parse_uncertainty                              #


def unknown(utype, node, filename):
    try:
        return float(node.text)
    except (TypeError, ValueError):
        raise LogicTreeError(node, filename, 'expected single float value')


parse_uncertainty = CallableDict(keymissing=unknown)


@parse_uncertainty.add('sourceModel', 'extendModel')
def smodel(utype, node, filename):
    return node.text.strip()


@parse_uncertainty.add('abGRAbsolute')
def abGR(utype, node, filename):
    try:
        [a, b] = node.text.split()
        return float(a), float(b)
    except ValueError:
        raise LogicTreeError(
            node, filename, 'expected a pair of floats separated by space')


@parse_uncertainty.add('incrementalMFDAbsolute')
def incMFD(utype, node, filename):
    min_mag, bin_width = (node.incrementalMFD["minMag"],
                          node.incrementalMFD["binWidth"])
    return min_mag,  bin_width, ~node.incrementalMFD.occurRates


@parse_uncertainty.add('simpleFaultGeometryAbsolute')
def simpleGeom(utype, node, filename):
    if hasattr(node, 'simpleFaultGeometry'):
        node = node.simpleFaultGeometry
    _validate_simple_fault_geometry(utype, node, filename)
    spacing = node["spacing"]
    usd, lsd, dip = (~node.upperSeismoDepth, ~node.lowerSeismoDepth,
                     ~node.dip)
    coords = split_coords_2d(~node.LineString.posList)
    trace = geo.Line([geo.Point(*p) for p in coords])
    return trace, usd, lsd, dip, spacing


@parse_uncertainty.add('complexFaultGeometryAbsolute')
def complexGeom(utype, node, filename):
    if hasattr(node, 'complexFaultGeometry'):
        node = node.complexFaultGeometry
    _validate_complex_fault_geometry(utype, node, filename)
    spacing = node["spacing"]
    edges = []
    for edge_node in node.nodes:
        coords = split_coords_3d(~edge_node.LineString.posList)
        edges.append(geo.Line([geo.Point(*p) for p in coords]))
    return edges, spacing


@parse_uncertainty.add('characteristicFaultGeometryAbsolute')
def charGeom(utype, node, filename):
    surfaces = []
    for geom_node in node.surface:
        if "simpleFaultGeometry" in geom_node.tag:
            _validate_simple_fault_geometry(utype, geom_node, filename)
            trace, usd, lsd, dip, spacing = parse_uncertainty(
                'simpleFaultGeometryAbsolute', geom_node, filename)
            surfaces.append(geo.SimpleFaultSurface.from_fault_data(
                trace, usd, lsd, dip, spacing))
        elif "complexFaultGeometry" in geom_node.tag:
            _validate_complex_fault_geometry(utype, geom_node, filename)
            edges, spacing = parse_uncertainty(
                'complexFaultGeometryAbsolute', geom_node, filename)
            surfaces.append(geo.ComplexFaultSurface.from_fault_data(
                edges, spacing))
        elif "planarSurface" in geom_node.tag:
            _validate_planar_fault_geometry(utype, geom_node, filename)
            nodes = []
            for key in ["topLeft", "topRight", "bottomRight", "bottomLeft"]:
                nodes.append(geo.Point(getattr(geom_node, key)["lon"],
                                       getattr(geom_node, key)["lat"],
                                       getattr(geom_node, key)["depth"]))
            top_left, top_right, bottom_right, bottom_left = tuple(nodes)
            surface = geo.PlanarSurface.from_corner_points(
                top_left, top_right, bottom_right, bottom_left)
            surfaces.append(surface)
        else:
            raise LogicTreeError(
                geom_node, filename, "Surface geometry type not recognised")
    if len(surfaces) > 1:
        return geo.MultiSurface(surfaces)
    else:
        return surfaces[0]


# validations

def _validate_simple_fault_geometry(utype, node, filename):
    try:
        coords = split_coords_2d(~node.LineString.posList)
        trace = geo.Line([geo.Point(*p) for p in coords])
    except ValueError:
        # If the geometry cannot be created then use the LogicTreeError
        # to point the user to the incorrect node. Hence, if trace is
        # compiled successfully then len(trace) is True, otherwise it is
        # False
        trace = []
    if len(trace):
        return
    raise LogicTreeError(
        node, filename, "'simpleFaultGeometry' node is not valid")


def _validate_complex_fault_geometry(utype, node, filename):
    # NB: if the geometry does not conform to the Aki & Richards convention
    # this will not be verified here, but will raise an error when the surface
    # is created
    valid_edges = []
    for edge_node in node.nodes:
        try:
            coords = split_coords_3d(edge_node.LineString.posList.text)
            edge = geo.Line([geo.Point(*p) for p in coords])
        except ValueError:
            # See use of validation error in simple geometry case
            # The node is valid if all of the edges compile correctly
            edge = []
        if len(edge):
            valid_edges.append(True)
        else:
            valid_edges.append(False)
    if node["spacing"] and all(valid_edges):
        return
    raise LogicTreeError(
        node, filename, "'complexFaultGeometry' node is not valid")


def _validate_planar_fault_geometry(utype, node, filename):
    valid_spacing = node["spacing"]
    for key in ["topLeft", "topRight", "bottomLeft", "bottomRight"]:
        lon = getattr(node, key)["lon"]
        lat = getattr(node, key)["lat"]
        depth = getattr(node, key)["depth"]
        valid_lon = (lon >= -180.0) and (lon <= 180.0)
        valid_lat = (lat >= -90.0) and (lat <= 90.0)
        valid_depth = (depth >= 0.0)
        is_valid = valid_lon and valid_lat and valid_depth
        if not is_valid or not valid_spacing:
            raise LogicTreeError(
                node, filename, "'planarFaultGeometry' node is not valid")


#                         apply_uncertainty                                #

apply_uncertainty = CallableDict()


@apply_uncertainty.add('simpleFaultDipRelative')
def _simple_fault_dip_relative(utype, source, value):
    source.modify('adjust_dip', dict(increment=value))


@apply_uncertainty.add('simpleFaultDipAbsolute')
def _simple_fault_dip_absolute(bset, source, value):
    source.modify('set_dip', dict(dip=value))


@apply_uncertainty.add('simpleFaultGeometryAbsolute')
def _simple_fault_geom_absolute(utype, source, value):
    trace, usd, lsd, dip, spacing = value
    source.modify(
        'set_geometry',
        dict(fault_trace=trace, upper_seismogenic_depth=usd,
             lower_seismogenic_depth=lsd, dip=dip, spacing=spacing))


@apply_uncertainty.add('complexFaultGeometryAbsolute')
def _complex_fault_geom_absolute(utype, source, value):
    edges, spacing = value
    source.modify('set_geometry', dict(edges=edges, spacing=spacing))


@apply_uncertainty.add('characteristicFaultGeometryAbsolute')
def _char_fault_geom_absolute(utype, source, value):
    source.modify('set_geometry', dict(surface=value))


@apply_uncertainty.add('abGRAbsolute')
def _abGR_absolute(utype, source, value):
    a, b = value
    source.mfd.modify('set_ab', dict(a_val=a, b_val=b))


@apply_uncertainty.add('bGRRelative')
def _abGR_relative(utype, source, value):
    source.mfd.modify('increment_b', dict(value=value))


@apply_uncertainty.add('maxMagGRRelative')
def _maxmagGR_relative(utype, source, value):
    source.mfd.modify('increment_max_mag', dict(value=value))


@apply_uncertainty.add('maxMagGRAbsolute')
def _maxmagGR_absolute(utype, source, value):
    source.mfd.modify('set_max_mag', dict(value=value))


@apply_uncertainty.add('incrementalMFDAbsolute')
def _incMFD_absolute(utype, source, value):
    min_mag, bin_width, occur_rates = value
    source.mfd.modify('set_mfd', dict(min_mag=min_mag, bin_width=bin_width,
                                      occurrence_rates=occur_rates))


# ######################### apply_uncertainties ########################### #

def apply_uncertainties(bset_values, src_group):
    """
    :param bset_value: a list of pairs (branchset, value)
        List of branch IDs
    :param src_group:
        SourceGroup instance
    """
    if not bset_values:
        return src_group
    sg = copy.copy(src_group)
    sg.sources = []
    sg.changes = 0
    for source in src_group:
        oks = [bset.filter_source(source) for bset, value in bset_values]
        if sum(oks):  # source not filtered out
            src = copy.deepcopy(source)
            for (bset, value), ok in zip(bset_values, oks):
                if ok:
                    apply_uncertainty(bset.uncertainty_type, src, value)
                    sg.changes += 1
            # redoing count_ruptures can be slow
            src.num_ruptures = src.count_ruptures()
        else:
            src = copy.copy(source)
        sg.sources.append(src)
    return sg
