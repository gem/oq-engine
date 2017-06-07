#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2015-2017, GEM Foundation
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Parser for input in a NRML format, with partial validation
"""
import re
from copy import copy
from openquake.baselib.node import node_from_xml
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hazardlib.scalerel import get_available_scalerel
from openquake.hazardlib import mfd
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hmtk.sources.source_model import mtkSourceModel
from openquake.hmtk.sources.point_source import mtkPointSource
from openquake.hmtk.sources.area_source import mtkAreaSource
from openquake.hmtk.sources.simple_fault_source import mtkSimpleFaultSource
from openquake.hmtk.sources.complex_fault_source import mtkComplexFaultSource
from openquake.hmtk.parsers.source_model.base import BaseSourceModelParser

SCALERELS = get_available_scalerel()


def string_(string):
    """
    Returns string or None
    """
    if string:
        return string
    else:
        return None


def float_(value):
    """
    Returns float of a value, or None
    """
    if value:
        return float(value)
    else:
        return None


def int_(value):
    """
    Returns int or None
    """
    if value:
        return float(value)
    else:
        return None


def get_taglist(node):
    """
    Return a list of tags (with NRML namespace removed) representing the
    order of the nodes within a node
    """
    return [re.sub(r'\{[^}]*\}', "", copy(subnode.tag))
            for subnode in node.nodes]


def linestring_node_to_line(node, with_depth=False):
    """
    Returns an instance of a Linestring node to :class:
    openquake.hazardlib.geo.line.Line
    """
    assert "LineString" in node.tag
    crds = [float(x) for x in node.nodes[0].text.split()]
    if with_depth:
        return Line([Point(crds[iloc], crds[iloc + 1], crds[iloc + 2])
                     for iloc in range(0, len(crds), 3)])
    else:
        return Line([Point(crds[iloc], crds[iloc + 1])
                     for iloc in range(0, len(crds), 2)])


def node_to_point_geometry(node):
    """
    Reads the node and returns the point geometry, upper depth and lower depth
    """
    assert "pointGeometry" in node.tag
    for subnode in node.nodes:
        if "Point" in subnode.tag:
            # Position
            lon, lat = map(float, subnode.nodes[0].text.split())
            point = Point(lon, lat)
        elif "upperSeismoDepth" in subnode.tag:
            upper_depth = float_(subnode.text)
        elif "lowerSeismoDepth" in subnode.tag:
            lower_depth = float_(subnode.text)
        else:
            # Redundent
            pass
    assert lower_depth > upper_depth
    return point, upper_depth, lower_depth


def node_to_area_geometry(node):
    """
    Reads an area geometry node and returns the polygon, upper depth and lower
    depth
    """
    assert "areaGeometry" in node.tag
    for subnode in node.nodes:
        if "Polygon" in subnode.tag:
            crds = [float(x)
                    for x in subnode.nodes[0].nodes[0].nodes[0].text.split()]
            polygon = Polygon([Point(crds[iloc], crds[iloc + 1])
                               for iloc in range(0, len(crds), 2)])
        elif "upperSeismoDepth" in subnode.tag:
            upper_depth = float_(subnode.text)
        elif "lowerSeismoDepth" in subnode.tag:
            lower_depth = float_(subnode.text)
        else:
            # Redundent
            pass
    assert lower_depth > upper_depth
    return polygon, upper_depth, lower_depth


def node_to_simple_fault_geometry(node):
    """
    Reads a simple fault geometry node and returns an OpenQuake representation

    :returns:
        trace - Trace of fault as instance
    """
    assert "simpleFaultGeometry" in node.tag
    for subnode in node.nodes:
        if "LineString" in subnode.tag:
            trace = linestring_node_to_line(subnode, with_depth=False)
        elif "dip" in subnode.tag:
            dip = float(subnode.text)
        elif "upperSeismoDepth" in subnode.tag:
            upper_depth = float(subnode.text)
        elif "lowerSeismoDepth" in subnode.tag:
            lower_depth = float(subnode.text)
        else:
            # Redundent
            pass
    assert lower_depth > upper_depth
    return trace, dip, upper_depth, lower_depth


def node_to_complex_fault_geometry(node):
    """
    Reads a complex fault geometry node and returns an
    """
    assert "complexFaultGeometry" in node.tag
    intermediate_edges = []
    for subnode in node.nodes:
        if "faultTopEdge" in subnode.tag:
            top_edge = linestring_node_to_line(subnode.nodes[0],
                                               with_depth=True)
        elif "intermediateEdge" in subnode.tag:
            int_edge = linestring_node_to_line(subnode.nodes[0],
                                               with_depth=True)
            intermediate_edges.append(int_edge)
        elif "faultBottomEdge" in subnode.tag:
            bottom_edge = linestring_node_to_line(subnode.nodes[0],
                                                  with_depth=True)
        else:
            # Redundent
            pass
    return [top_edge] + intermediate_edges + [bottom_edge]


def node_to_scalerel(node):
    """
    Parses a node to an instance of a supported scaling relation class
    """
    if not node.text:
        return None
    return SCALERELS[node.text.strip()]()


def node_to_truncated_gr(node, bin_width=0.1):
    """
    Parses truncated GR node to an instance of the
    :class: openquake.hazardlib.mfd.truncated_gr.TruncatedGRMFD
    """
    # Parse to float dictionary
    if not all([node.attrib[key]
                for key in ["minMag", "maxMag", "aValue", "bValue"]]):
        return None
    tgr = dict((key, float_(node.attrib[key])) for key in node.attrib)
    return mfd.truncated_gr.TruncatedGRMFD(min_mag=tgr["minMag"],
                                           max_mag=tgr["maxMag"],
                                           bin_width=bin_width,
                                           a_val=tgr["aValue"],
                                           b_val=tgr["bValue"])


def node_to_evenly_discretized(node):
    """
    Parses the evenly discretized mfd node to an instance of the
    :class: openquake.hazardlib.mfd.evenly_discretized.EvenlyDiscretizedMFD,
    or to None if not all parameters are available
    """
    if not all([node.attrib["minMag"], node.attrib["binWidth"],
                node.nodes[0].text]):
        return None
    # Text to float
    rates = [float(x) for x in node.nodes[0].text.split()]
    return mfd.evenly_discretized.EvenlyDiscretizedMFD(
        float(node.attrib["minMag"]),
        float(node.attrib["binWidth"]),
        rates)


def node_to_mfd(node, taglist):
    """
    Reads the node to return a magnitude frequency distribution
    """
    if "incrementalMFD" in taglist:
        mfd = node_to_evenly_discretized(
            node.nodes[taglist.index("incrementalMFD")])
    elif "truncGutenbergRichterMFD" in taglist:
        mfd = node_to_truncated_gr(
            node.nodes[taglist.index("truncGutenbergRichterMFD")])
    else:
        mfd = None
    return mfd


def node_to_nodal_planes(node):
    """
    Parses the nodal plane distribution to a PMF
    """
    if not len(node):
        return None
    npd_pmf = []
    for plane in node.nodes:
        if not all(plane.attrib[key] for key in plane.attrib):
            # One plane fails - return None
            return None
        npd = NodalPlane(float(plane.attrib["strike"]),
                         float(plane.attrib["dip"]),
                         float(plane.attrib["rake"]))
        npd_pmf.append((float(plane.attrib["probability"]), npd))
    return PMF(npd_pmf)


def node_to_hdd(node):
    """
    Parses the node to a hpyocentral depth distribution PMF
    """
    if not len(node):
        return None
    hdds = []
    for subnode in node.nodes:
        if not all([subnode.attrib[key] for key in ["depth", "probability"]]):
            return None
        hdds.append((float(subnode.attrib["probability"]),
                     float(subnode.attrib["depth"])))
    return PMF(hdds)


def parse_point_source_node(node, mfd_spacing=0.1):
    """
    Returns an "areaSource" node into an instance of the :class:
    openquake.hmtk.sources.area.mtkAreaSource
    """
    assert "pointSource" in node.tag
    pnt_taglist = get_taglist(node)
    # Get metadata
    point_id, name, trt = (node.attrib["id"],
                           node.attrib["name"],
                           node.attrib["tectonicRegion"])
    assert point_id  # Defensive validation!
    # Process geometry
    location, upper_depth, lower_depth = node_to_point_geometry(
        node.nodes[pnt_taglist.index("pointGeometry")])
    # Process scaling relation
    msr = node_to_scalerel(node.nodes[pnt_taglist.index("magScaleRel")])
    # Process aspect ratio
    aspect = float_(node.nodes[pnt_taglist.index("ruptAspectRatio")].text)
    # Process MFD
    mfd = node_to_mfd(node, pnt_taglist)
    # Process nodal planes
    npds = node_to_nodal_planes(
        node.nodes[pnt_taglist.index("nodalPlaneDist")])
    # Process hypocentral depths
    hdds = node_to_hdd(node.nodes[pnt_taglist.index("hypoDepthDist")])
    return mtkPointSource(point_id, name, trt,
                          geometry=location,
                          upper_depth=upper_depth,
                          lower_depth=lower_depth,
                          mag_scale_rel=msr,
                          rupt_aspect_ratio=aspect,
                          mfd=mfd,
                          nodal_plane_dist=npds,
                          hypo_depth_dist=hdds)


def parse_area_source_node(node, mfd_spacing=0.1):
    """
    Returns an "areaSource" node into an instance of the :class:
    openquake.hmtk.sources.area.mtkAreaSource
    """
    assert "areaSource" in node.tag
    area_taglist = get_taglist(node)
    # Get metadata
    area_id, name, trt = (node.attrib["id"],
                          node.attrib["name"],
                          node.attrib["tectonicRegion"])
    assert area_id  # Defensive validation!
    # Process geometry
    polygon, upper_depth, lower_depth = node_to_area_geometry(
        node.nodes[area_taglist.index("areaGeometry")])
    # Process scaling relation
    msr = node_to_scalerel(node.nodes[area_taglist.index("magScaleRel")])
    # Process aspect ratio
    aspect = float_(node.nodes[area_taglist.index("ruptAspectRatio")].text)
    # Process MFD
    mfd = node_to_mfd(node, area_taglist)
    # Process nodal planes
    npds = node_to_nodal_planes(
        node.nodes[area_taglist.index("nodalPlaneDist")])
    # Process hypocentral depths
    hdds = node_to_hdd(node.nodes[area_taglist.index("hypoDepthDist")])
    return mtkAreaSource(area_id, name, trt,
                         geometry=polygon,
                         upper_depth=upper_depth,
                         lower_depth=lower_depth,
                         mag_scale_rel=msr,
                         rupt_aspect_ratio=aspect,
                         mfd=mfd,
                         nodal_plane_dist=npds,
                         hypo_depth_dist=hdds)


def parse_simple_fault_node(node, mfd_spacing=0.1, mesh_spacing=1.0):
    """
    Parses a "simpleFaultSource" node and returns an instance of the :class:
    openquake.hmtk.sources.simple_fault.mtkSimpleFaultSource
    """
    assert "simpleFaultSource" in node.tag
    sf_taglist = get_taglist(node)
    # Get metadata
    sf_id, name, trt = (node.attrib["id"],
                        node.attrib["name"],
                        node.attrib["tectonicRegion"])
    # Process geometry
    trace, dip, upper_depth, lower_depth = node_to_simple_fault_geometry(
        node.nodes[sf_taglist.index("simpleFaultGeometry")])
    # Process scaling relation
    msr = node_to_scalerel(node.nodes[sf_taglist.index("magScaleRel")])
    # Process aspect ratio
    aspect = float_(node.nodes[sf_taglist.index("ruptAspectRatio")].text)
    # Process MFD
    mfd = node_to_mfd(node, sf_taglist)
    # Process rake
    rake = float_(node.nodes[sf_taglist.index("rake")].text)
    simple_fault = mtkSimpleFaultSource(sf_id, name, trt,
                                        geometry=None,
                                        dip=dip,
                                        upper_depth=upper_depth,
                                        lower_depth=lower_depth,
                                        mag_scale_rel=msr,
                                        rupt_aspect_ratio=aspect,
                                        mfd=mfd,
                                        rake=rake)
    simple_fault.create_geometry(trace, dip, upper_depth, lower_depth,
                                 mesh_spacing)
    return simple_fault


def parse_complex_fault_node(node, mfd_spacing=0.1, mesh_spacing=4.0):
    """
    Parses a "complexFaultSource" node and returns an instance of the :class:
    openquake.hmtk.sources.complex_fault.mtkComplexFaultSource
    """
    assert "complexFaultSource" in node.tag
    sf_taglist = get_taglist(node)
    # Get metadata
    sf_id, name, trt = (node.attrib["id"],
                        node.attrib["name"],
                        node.attrib["tectonicRegion"])
    # Process geometry
    edges = node_to_complex_fault_geometry(
        node.nodes[sf_taglist.index("complexFaultGeometry")])
    # Process scaling relation
    msr = node_to_scalerel(node.nodes[sf_taglist.index("magScaleRel")])
    # Process aspect ratio
    aspect = float_(node.nodes[sf_taglist.index("ruptAspectRatio")].text)
    # Process MFD
    mfd = node_to_mfd(node, sf_taglist)
    # Process rake
    rake = float_(node.nodes[sf_taglist.index("rake")].text)
    complex_fault = mtkComplexFaultSource(sf_id, name, trt,
                                          geometry=None,
                                          mag_scale_rel=msr,
                                          rupt_aspect_ratio=aspect,
                                          mfd=mfd,
                                          rake=rake)
    complex_fault.create_geometry(edges, mesh_spacing)
    return complex_fault


class nrmlSourceModelParser(BaseSourceModelParser):
    """
    Parser for a source model in NRML format, permitting partial validation
    such that not all fields need to be specified for the file to be parsed
    """
    def read_file(self, identifier, mfd_spacing=0.1, simple_mesh_spacing=1.0,
                  complex_mesh_spacing=4.0, area_discretization=10.):
        """
        Reads in the source model in returns an instance of the :class:
        openquake.hmtk.sourcs.source_model.mtkSourceModel
        """
        node_set = node_from_xml(self.input_file)[0]
        source_model = mtkSourceModel(identifier,
                                      name=node_set.attrib["name"])
        for node in node_set:
            if "pointSource" in node.tag:
                source_model.sources.append(
                    parse_point_source_node(node, mfd_spacing))
            elif "areaSource" in node.tag:
                source_model.sources.append(
                    parse_area_source_node(node, mfd_spacing))
            elif "simpleFaultSource" in node.tag:
                source_model.sources.append(
                    parse_simple_fault_node(node, mfd_spacing,
                                            simple_mesh_spacing))
            elif "complexFaultSource" in node.tag:
                source_model.sources.append(
                    parse_complex_fault_node(node, mfd_spacing,
                                             complex_mesh_spacing))
            else:
                print("Source typology %s not recognised - skipping!"
                      % node.tag)
        return source_model
