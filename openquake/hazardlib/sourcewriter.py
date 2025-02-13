# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
Source model XML Writer
"""

import os
import toml
import operator
import numpy
from openquake.baselib import hdf5
from openquake.baselib.general import CallableDict, groupby
from openquake.baselib.node import Node, node_to_dict
from openquake.hazardlib import nrml, sourceconverter, pmf, valid
from openquake.hazardlib.source import (
    NonParametricSeismicSource, check_complex_fault, PointSource)
from openquake.hazardlib.tom import NegativeBinomialTOM

obj_to_node = CallableDict(lambda obj: obj.__class__.__name__)


def r4(x):
    """
    Round lon, lat to 4 digits (11 meters)
    """
    return round(x, 4)


def build_area_source_geometry(area_source):
    """
    Returns the area source geometry as a Node

    :param area_source:
        Area source model as an instance of the :class:
        `openquake.hazardlib.source.area.AreaSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    geom = []
    for lon, lat in zip(area_source.polygon.lons, area_source.polygon.lats):
        # NB: converting numpy.float64 -> float is good for TOML
        geom.extend((float(lon), float(lat)))
    poslist_node = Node("gml:posList", text=geom)
    linear_ring_node = Node("gml:LinearRing", nodes=[poslist_node])
    exterior_node = Node("gml:exterior", nodes=[linear_ring_node])
    polygon_node = Node("gml:Polygon", nodes=[exterior_node])
    upper_depth_node = Node(
        "upperSeismoDepth", text=area_source.upper_seismogenic_depth)
    lower_depth_node = Node(
        "lowerSeismoDepth", text=area_source.lower_seismogenic_depth)
    return Node(
        "areaGeometry",
        nodes=[polygon_node, upper_depth_node, lower_depth_node])


def build_point_source_geometry(point_source):
    """
    Returns the poing source geometry as a Node

    :param point_source:
        Point source model as an instance of the :class:
        `openquake.hazardlib.source.point.PointSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    xy = point_source.location.x, point_source.location.y
    pos_node = Node("gml:pos", text=xy)
    point_node = Node("gml:Point", nodes=[pos_node])
    upper_depth_node = Node(
        "upperSeismoDepth", text=point_source.upper_seismogenic_depth)
    lower_depth_node = Node(
        "lowerSeismoDepth", text=point_source.lower_seismogenic_depth)
    return Node(
        "pointGeometry",
        nodes=[point_node, upper_depth_node, lower_depth_node])


def build_linestring_node(line, with_depth=False):
    """
    Parses a line to a Node class

    :param line:
        Line as instance of :class:`openquake.hazardlib.geo.line.Line`
    :param bool with_depth:
        Include the depth values (True) or not (False):
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    geom = []
    for p in line.points:
        if with_depth:
            geom.extend((r4(p.x), r4(p.y), r4(p.z)))
        else:
            geom.extend((r4(p.x), r4(p.y)))
    poslist_node = Node("gml:posList", text=geom)
    return Node("gml:LineString", nodes=[poslist_node])


def build_simple_fault_geometry(fault_source):
    """
    Returns the simple fault source geometry as a Node

    :param fault_source:
        Simple fault source model as an instance of the :class:
        `openquake.hazardlib.source.simple_fault.SimpleFaultSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    linestring_node = build_linestring_node(fault_source.fault_trace,
                                            with_depth=False)
    dip_node = Node("dip", text=fault_source.dip)
    upper_depth_node = Node(
        "upperSeismoDepth", text=fault_source.upper_seismogenic_depth)
    lower_depth_node = Node(
        "lowerSeismoDepth", text=fault_source.lower_seismogenic_depth)
    return Node("simpleFaultGeometry",
                nodes=[linestring_node, dip_node, upper_depth_node,
                       lower_depth_node])


def build_complex_fault_geometry(fault_source):
    """
    Returns the complex fault source geometry as a Node

    :param fault_source:
        Complex fault source model as an instance of the :class:
        `openquake.hazardlib.source.complex_fault.ComplexFaultSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    num_edges = len(fault_source.edges)
    edge_nodes = []
    for iloc, edge in enumerate(fault_source.edges):
        if iloc == 0:
            # Top Edge
            node_name = "faultTopEdge"

        elif iloc == (num_edges - 1):
            # Bottom edge
            node_name = "faultBottomEdge"
        else:
            # Intermediate edge
            node_name = "intermediateEdge"
        edge_nodes.append(
            Node(node_name,
                 nodes=[build_linestring_node(edge, with_depth=True)]))
    return Node("complexFaultGeometry", nodes=edge_nodes)


@obj_to_node.add('KiteSurface')
def build_kite_surface(ksurface):
    """
    Returns the KiteSurface instance as a Node

    :param ksurface:
        Kite fault source model as an instance of the :class:
        `openquake.hazardlib.source.kite_fault.KiteFaultSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    profile_nodes = []
    for profile in ksurface.profiles:
        node = build_linestring_node(profile, with_depth=True)
        profile_nodes.append(Node("profile", nodes=[node]))
    return Node("kiteSurface", nodes=profile_nodes)


@obj_to_node.add('EvenlyDiscretizedMFD')
def build_evenly_discretised_mfd(mfd):
    """
    Returns the evenly discretized MFD as a Node

    :param mfd:
        MFD as instance of :class:
        `openquake.hazardlib.mfd.evenly_discretized.EvenlyDiscretizedMFD`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    occur_rates = Node("occurRates", text=mfd.occurrence_rates)
    return Node("incrementalMFD",
                {"binWidth": mfd.bin_width, "minMag": mfd.min_mag},
                nodes=[occur_rates])


@obj_to_node.add('TruncatedGRMFD')
def build_truncated_gr_mfd(mfd):
    """
    Parses the truncated Gutenberg Richter MFD as a Node

    :param mfd:
        MFD as instance of :class:
        `openquake.hazardlib.mfd.truncated_gr.TruncatedGRMFD`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    if hasattr(mfd, 'slip_rate'):
        return Node("truncGutenbergRichterMFD",
                    {"bValue": mfd.b_val, "slipRate": mfd.slip_rate,
                     "rigidity": mfd.rigidity,
                     "minMag": mfd.min_mag, "maxMag": mfd.max_mag})
    return Node("truncGutenbergRichterMFD",
                {"aValue": mfd.a_val, "bValue": mfd.b_val,
                 "minMag": mfd.min_mag, "maxMag": mfd.max_mag})


@obj_to_node.add('TaperedGRMFD')
def build_tapered_gr_mfd(mfd):
    """
    Parses the truncated Gutenberg Richter MFD as a Node

    :param mfd:
        MFD as instance of :class:
        `openquake.hazardlib.mfd.tapered_gr_mfd.TaperedGRMFD`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    return Node(
        "taperedGutenbergRichterMFD", {
            "aValue": mfd.a_val,
            "bValue": mfd.b_val,
            "cornerMag": mfd.corner_mag,
            "minMag": mfd.min_mag,
            "maxMag": mfd.max_mag
        })


@obj_to_node.add('ArbitraryMFD')
def build_arbitrary_mfd(mfd):
    """
    Parses the arbitrary MFD as a Node

    :param mfd:
        MFD as instance of :class:
        `openquake.hazardlib.mfd.arbitrary.ArbitraryMFD`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    magnitudes = Node("magnitudes", text=mfd.magnitudes)
    occur_rates = Node("occurRates", text=mfd.occurrence_rates)
    return Node("arbitraryMFD", nodes=[magnitudes, occur_rates])


@obj_to_node.add("YoungsCoppersmith1985MFD")
def build_youngs_coppersmith_mfd(mfd):
    """
    Parses the Youngs & Coppersmith MFD as a node. Note that the MFD does
    not hold the total moment rate, but only the characteristic rate. Therefore
    the node is written to the characteristic rate version regardless of
    whether or not it was originally created from total moment rate

    :param mfd:
        MFD as instance of :class:
        `openquake.hazardlib.mfd.youngs_coppersmith_1985.
        YoungsCoppersmith1985MFD`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    return Node("YoungsCoppersmithMFD",
                {"minMag": mfd.min_mag, "bValue": mfd.b_val,
                 "characteristicMag": mfd.char_mag,
                 "characteristicRate": mfd.char_rate,
                 "binWidth": mfd.bin_width})


@obj_to_node.add('MultiMFD')
def build_multi_mfd(mfd):
    """
    Parses the MultiMFD as a Node

    :param mfd:
        MFD as instance of :class:
        `openquake.hazardlib.mfd.multi_mfd.MultiMFD`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    node = Node("multiMFD", dict(kind=mfd.kind, size=mfd.size))
    for name in sorted(mfd.kwargs):
        values = mfd.kwargs[name]
        if name in ('magnitudes', 'occurRates'):
            values = sum(values, [])
        node.append(Node(name, text=values))
    if 'occurRates' in mfd.kwargs:
        lengths = [len(rates) for rates in mfd.kwargs['occurRates']]
        node.append(Node('lengths', text=lengths))
    return node


def build_nodal_plane_dist(npd):
    """
    Returns the nodal plane distribution as a Node instance

    :param npd:
        Nodal plane distribution as instance of :class:
        `openquake.hazardlib.pmf.PMF`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    npds = []
    dist = []
    for prob, npd in npd.data:
        dist.append((prob, (npd.dip, npd.strike, npd.rake)))
        nodal_plane = Node(
            "nodalPlane", {"dip": npd.dip, "probability": prob,
                           "strike": npd.strike, "rake": npd.rake})
        npds.append(nodal_plane)
    sourceconverter.fix_dupl(dist)
    return Node("nodalPlaneDist", nodes=npds)


def build_hypo_depth_dist(hdd):
    """
    Returns the hypocentral depth distribution as a Node instance

    :param hdd:
        Hypocentral depth distribution as an instance of :class:
        `openquake.hzardlib.pmf.PMF`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    hdds = []
    dist = []
    for (prob, depth) in hdd.data:
        dist.append((prob, depth))
        hdds.append(Node("hypoDepth", {"depth": depth, "probability": prob}))
    sourceconverter.fix_dupl(dist)
    return Node("hypoDepthDist", nodes=hdds)


def get_distributed_seismicity_source_nodes(source):
    """
    Returns list of nodes of attributes common to all distributed seismicity
    source classes

    :param source:
        Seismic source as instance of :class:
        `openquake.hazardlib.source.area.AreaSource` or :class:
        `openquake.hazardlib.source.point.PointSource`
    :returns:
        List of instances of :class:`openquake.baselib.node.Node`
    """
    source_nodes = []
    #  parse msr
    source_nodes.append(
        Node("magScaleRel",
             text=source.magnitude_scaling_relationship.__class__.__name__))
    # Parse aspect ratio
    source_nodes.append(
        Node("ruptAspectRatio", text=source.rupture_aspect_ratio))
    # Parse MFD
    source_nodes.append(obj_to_node(source.mfd))
    # Parse nodal plane distribution
    source_nodes.append(
        build_nodal_plane_dist(source.nodal_plane_distribution))
    # Parse hypocentral depth distribution
    source_nodes.append(
        build_hypo_depth_dist(source.hypocenter_distribution))
    return source_nodes


def build_hypo_list_node(hypo_list):
    """
    :param hypo_list:
       an array of shape (N, 3) with columns (alongStrike, downDip, weight)
    :returns:
        a hypoList node containing N hypo nodes
    """
    hypolist = Node('hypoList', {})
    for row in hypo_list:
        n = Node(
            'hypo', dict(alongStrike=row[0], downDip=row[1], weight=row[2]))
        hypolist.append(n)
    return hypolist


def build_slip_list_node(slip_list):
    """
    :param slip_list:
       an array of shape (N, 2) with columns (slip, weight)
    :returns:
        a hypoList node containing N slip nodes
    """
    sliplist = Node('slipList', {})
    for row in slip_list:
        sliplist.append(
            Node('slip', dict(weight=row[1]), row[0]))
    return sliplist


def get_fault_source_nodes(source):
    """
    Returns list of nodes of attributes common to all fault source classes

    :param source:
        Fault source as instance of :class:
        `openquake.hazardlib.source.simple_fault.SimpleFaultSource` or :class:
        `openquake.hazardlib.source.complex_fault.ComplexFaultSource`
    :returns:
        List of instances of :class:`openquake.baselib.node.Node`
    """
    source_nodes = []
    #  parse msr
    source_nodes.append(
        Node(
            "magScaleRel",
            text=source.magnitude_scaling_relationship.__class__.__name__))
    # Parse aspect ratio
    source_nodes.append(
        Node("ruptAspectRatio", text=source.rupture_aspect_ratio))
    # Parse MFD
    source_nodes.append(obj_to_node(source.mfd))
    # Parse Rake
    source_nodes.append(Node("rake", text=source.rake))
    if len(getattr(source, 'hypo_list', [])):
        source_nodes.append(build_hypo_list_node(source.hypo_list))
    if len(getattr(source, 'slip_list', [])):
        source_nodes.append(build_slip_list_node(source.slip_list))
    return source_nodes


def get_source_attributes(source):
    """
    Retreives a dictionary of source attributes from the source class

    :param source:
        Seismic source as instance of :class:
        `openquake.hazardlib.source.base.BaseSeismicSource`
    :returns:
        Dictionary of source attributes
    """
    attrs = {"id": source.source_id, "name": source.name}
    if isinstance(source, NonParametricSeismicSource):
        rup = source.data[0][0]  # from [(rup, pmf), ...] pairs
        if not hasattr(rup, 'weight'):
            # happens in test_non_parametric_src
            return attrs
        elif rup.weight is not None:
            weights = [rup.weight for rup, pmf in source.data]
            attrs['rup_weights'] = numpy.array(weights)
    elif isinstance(source, PointSource):
        tom = source.temporal_occurrence_model
        if isinstance(tom, NegativeBinomialTOM):
            attrs['tom'] = 'NegativeBinomialTOM'
            attrs['mu'] = tom.mu
            attrs['alpha'] = tom.alpha
    return attrs


@obj_to_node.add('AreaSource')
def build_area_source_node(area_source):
    """
    Parses an area source to a Node class

    :param area_source:
        Area source as instance of :class:
        `openquake.hazardlib.source.area.AreaSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    # parse geometry
    source_nodes = [build_area_source_geometry(area_source)]
    # parse common distributed attributes
    source_nodes.extend(get_distributed_seismicity_source_nodes(area_source))
    return Node(
        "areaSource", get_source_attributes(area_source), nodes=source_nodes)


@obj_to_node.add('CharacteristicFaultSource')
def build_characteristic_fault_source_node(source):
    source_nodes = [obj_to_node(source.mfd)]
    source_nodes.append(Node("rake", text=source.rake))
    surface_node = Node('surface', nodes=source.surface.surface_nodes)
    source_nodes.append(surface_node)
    return Node('characteristicFaultSource',
                get_source_attributes(source),
                nodes=source_nodes)


@obj_to_node.add('NonParametricSeismicSource')
def build_nonparametric_source_node(source):
    rup_nodes = []
    for rup, p in source.data:
        probs = [prob for (prob, no) in p.data]
        rup_nodes.append(build_rupture_node(rup, probs))
    return Node('nonParametricSeismicSource',
                get_source_attributes(source), nodes=rup_nodes)


def build_rupture_node(rupt, probs_occur):
    """
    :param rupt: a hazardlib rupture object
    :param probs_occur: a list of floats with sum 1
    """
    s = sum(probs_occur)
    if abs(s - 1) > pmf.PRECISION:
        raise ValueError('The sum of %s is not 1: %s' % (probs_occur, s))
    h = rupt.hypocenter
    hp_dict = dict(lon=h.longitude, lat=h.latitude, depth=h.depth)
    rupt_nodes = [Node('magnitude', {}, rupt.mag),
                  Node('rake', {}, rupt.rake),
                  Node('hypocenter', hp_dict)]
    rupt_nodes.extend(rupt.surface.surface_nodes)
    geom = rupt.surface.surface_nodes[0].tag
    if len(rupt.surface.surface_nodes) > 1:
        name = 'multiPlanesRupture'
    elif geom == 'planarSurface':
        name = 'singlePlaneRupture'
    elif geom == 'simpleFaultGeometry':
        name = 'simpleFaultRupture'
    elif geom == 'complexFaultGeometry':
        name = 'complexFaultRupture'
    elif geom == 'griddedSurface':
        name = 'griddedRupture'
    elif geom == 'kiteSurface':
        name = 'kiteSurface'
    return Node(name, {'probs_occur': probs_occur}, nodes=rupt_nodes)


@obj_to_node.add('MultiPointSource')
def build_multi_point_source_node(multi_point_source):
    """
    Parses a point source to a Node class

    :param point_source:
        MultiPoint source as instance of :class:
        `openquake.hazardlib.source.point.MultiPointSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    # parse geometry
    pos = []
    for p in multi_point_source.mesh:
        # converting numpy.float64 -> float is good for TOML
        pos.append(float(p.x))
        pos.append(float(p.y))
    mesh_node = Node('gml:posList', text=pos)
    upper_depth_node = Node(
        "upperSeismoDepth", text=multi_point_source.upper_seismogenic_depth)
    lower_depth_node = Node(
        "lowerSeismoDepth", text=multi_point_source.lower_seismogenic_depth)
    source_nodes = [Node(
        "multiPointGeometry",
        nodes=[mesh_node, upper_depth_node, lower_depth_node])]
    # parse common distributed attributes
    source_nodes.extend(
        get_distributed_seismicity_source_nodes(multi_point_source))
    return Node("multiPointSource",
                get_source_attributes(multi_point_source),
                nodes=source_nodes)


@obj_to_node.add('PointSource')
def build_point_source_node(point_source):
    """
    Parses a point source to a Node class

    :param point_source:
        Point source as instance of :class:
        `openquake.hazardlib.source.point.PointSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`

    """
    # parse geometry
    source_nodes = [build_point_source_geometry(point_source)]
    # parse common distributed attributes
    source_nodes.extend(get_distributed_seismicity_source_nodes(point_source))
    return Node("pointSource",
                get_source_attributes(point_source),
                nodes=source_nodes)


@obj_to_node.add('SimpleFaultSource')
def build_simple_fault_source_node(fault_source):
    """
    Parses a simple fault source to a Node class

    :param fault_source:
        Simple fault source as instance of :class:
        `openquake.hazardlib.source.simple_fault.SimpleFaultSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    # Parse geometry
    source_nodes = [build_simple_fault_geometry(fault_source)]
    # Parse common fault source attributes
    source_nodes.extend(get_fault_source_nodes(fault_source))
    return Node("simpleFaultSource",
                get_source_attributes(fault_source),
                nodes=source_nodes)


@obj_to_node.add('ComplexFaultSource')
def build_complex_fault_source_node(fault_source):
    """
    Parses a complex fault source to a Node class

    :param fault_source:
        Complex fault source as instance of :class:
        `openquake.hazardlib.source.complex_fault.ComplexFaultSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    list(check_complex_fault(fault_source))  # check get_dip

    # Parse geometry
    source_nodes = [build_complex_fault_geometry(fault_source)]
    # Parse common fault source attributes
    source_nodes.extend(get_fault_source_nodes(fault_source))
    return Node("complexFaultSource",
                get_source_attributes(fault_source),
                nodes=source_nodes)


@obj_to_node.add('KiteFaultSource')
def build_kite_fault_source_node(fault_source):
    """
    Parses a kite fault source to a Node class

    :param fault_source:
        Kite fault source as instance of :class:
        `openquake.hazardlib.source.kite_fault.KiteFaultSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """

    # Parse geometry
    source_nodes = [build_kite_surface(fault_source)]
    # Parse common fault source attributes
    source_nodes.extend(get_fault_source_nodes(fault_source))
    return Node("kiteFaultSource",
                get_source_attributes(fault_source),
                nodes=source_nodes)


# tested in case_65
@obj_to_node.add('MultiFaultSource')
def build_multi_fault_source_node(multi_fault_source):
    """
    Parses a MultiFaultSource to a Node class

    :param multi_fault_source:
        Multi fault source as instance of :class:
        `openquake.hazardlib.source.multi_fault.MultiFaultSource`
    :returns:
        Instance of :class:`openquake.baselib.node.Node`
    """
    rup_nodes = []  # multiPlanesRupture
    for rup_idxs, prbs, mag, rake in zip(
            multi_fault_source._rupture_idxs,
            multi_fault_source.probs_occur,
            multi_fault_source.mags,
            multi_fault_source.rakes):
        probs = ' '.join(map(str, prbs))
        nodes = [Node('magnitude', text=str(mag)),
                 Node('sectionIndexes',
                      {'indexes': ' '.join(map(str, rup_idxs))}),
                 Node('rake', text=str(rake))]
        rup_node = Node('multiPlanesRupture', {'probs_occur': probs},
                        nodes=nodes)
        rup_nodes.append(rup_node)

    return Node("multiFaultSource",
                get_source_attributes(multi_fault_source),
                nodes=rup_nodes)


@obj_to_node.add('SourceGroup')
def build_source_group(source_group):
    source_nodes = [obj_to_node(src) for src in source_group.sources]
    attrs = dict(tectonicRegion=source_group.trt)
    if source_group.name:
        attrs['name'] = source_group.name
    if source_group.src_interdep:
        attrs['src_interdep'] = source_group.src_interdep
    if source_group.rup_interdep:
        attrs['rup_interdep'] = source_group.rup_interdep
    if source_group.grp_probability != 1.0:
        attrs['grp_probability'] = source_group.grp_probability
    if source_group.cluster:
        attrs['cluster'] = 'true'
    if source_group.temporal_occurrence_model is not None:
        tom = source_group.temporal_occurrence_model
        if hasattr(tom, 'occurrence_rate'):
            attrs['tom'] = 'ClusterPoissonTOM'
            attrs['occurrence_rate'] = tom.occurrence_rate
    if source_group.src_interdep == 'mutex':
        # tested in multi_fault_test
        attrs['srcs_weights'] = ' '.join(
            '%.7f' % getattr(src, 'mutex_weight', 1 / len(source_group))
            for src in source_group)
    return Node('sourceGroup', attrs, nodes=source_nodes)


@obj_to_node.add('SourceModel')
def build_source_model_node(source_model):
    attrs = {}
    if source_model.name:
        attrs['name'] = source_model.name
    if source_model.investigation_time:
        attrs['investigation_time'] = source_model.investigation_time
    if source_model.start_time:
        attrs['start_time'] = source_model.start_time
    nodes = [obj_to_node(sg) for sg in source_model.src_groups]
    return Node('sourceModel', attrs, nodes=nodes)


@obj_to_node.add('CompositeSourceModel')
def build_source_model(csm):
    nodes = [obj_to_node(sg) for sg in csm.src_groups]
    return Node('compositeSourceModel', {}, nodes=nodes)


# ##################### generic source model writer ####################### #

def extract_gridded_attrs(src_groups):
    """
    Extract the attributes of nonparametric/multifault sources. The
    attributes are arrays or a list of strings for rupture_idxs.

    :returns: a dictionary source_id -> attr -> value
    """
    ddict = {}
    for src_group in src_groups:
        for src in src_group:
            if src.is_gridded():
                ddict[src.source_id] = src.todict()
    return ddict


def write_source_model(dest, sources_or_groups, name=None,
                       investigation_time=None, prefix=''):
    """
    Writes a source model to XML.

    :param dest:
        Destination path
    :param sources_or_groups:
        Source model in different formats
    :param name:
        Name of the source model (if missing, extracted from the filename)
    :param investigation_time:
        Investigation time (for time-dependent sources)
    :param prefix:
        Add a prefix to the rupture_idxs, if given
    :returns:
        the list of generated filenames
    """
    # first a sanity check, only a SourceModel or a sequence are accepted
    assert isinstance(sources_or_groups, (nrml.SourceModel, list, tuple))
    if isinstance(sources_or_groups, nrml.SourceModel):
        groups = sources_or_groups.src_groups
        attrs = dict(name=sources_or_groups.name,
                     investigation_time=sources_or_groups.investigation_time)
    elif isinstance(sources_or_groups[0], sourceconverter.SourceGroup):
        groups = sources_or_groups
        attrs = dict(investigation_time=investigation_time)
    else:  # passed a list of sources
        srcs_by_trt = groupby(
            sources_or_groups, operator.attrgetter('tectonic_region_type'))
        groups = [sourceconverter.SourceGroup(trt, srcs_by_trt[trt])
                  for trt in srcs_by_trt]
        attrs = dict(investigation_time=investigation_time)
    if name or 'name' not in attrs:
        attrs['name'] = name or os.path.splitext(os.path.basename(dest))[0]
    if attrs['investigation_time'] is None:
        del attrs['investigation_time']
    nodes = list(map(obj_to_node, groups))
    gridded_attrs = extract_gridded_attrs(groups)
    out = [dest]
    if gridded_attrs:
        # for nonparametric and multifault sources save attrs on HDF5 file
        # NB: this is tested in the oq-mbtk, in rupture_smooth_test
        dest5 = os.path.splitext(dest)[0] + '.hdf5'
        with hdf5.File(dest5, 'w') as h:
            for src_id, dic in gridded_attrs.items():
                for k, v in dic.items():
                    key = '%s/%s' % (src_id, k)
                    dset = h.create_dataset(key, v.shape, v.dtype,
                                            compression='gzip',
                                            compression_opts=9)
                    if key == 'rupture_idxs' and prefix:
                        dset[:] = [prefix + x for x in v]
                    else:
                        dset[:] = v
        # remove duplicate content from nodes
        for grp_node in nodes:
            for src_node in grp_node:
                if src_node["id"] in gridded_attrs:
                    src_node.nodes = []
        out.append(dest5)

    # produce a geometryModel if there are MultiFaultSources
    sections = []
    for group in groups:
        for src in group:
            if hasattr(src, 'sections'):
                sections.extend(src.sections)
    smodel = Node("sourceModel", attrs, nodes=nodes)
    with open(dest, 'wb') as f:
        nrml.write([smodel], f, '%s')
    if sections:
        # surfaces have no 'id', so we use sections instead, with an 'id'
        # starting from 0; this is necessary for conversion to hdf5
        secnodes = [Node('section', {'id': str(i)},
                         nodes=[obj_to_node(sec)])
                    for i, sec in enumerate(sections)]
        gmodel = Node("geometryModel", attrs, nodes=secnodes)
        with open(dest[:-4] + '_sections.xml', 'wb') as f:
            nrml.write([gmodel], f, '%s')
            out.append(f.name)
    return out


def tomldump(obj, fileobj=None):
    """
    Write a generic serializable object in TOML format
    """
    dic = valid._fix_toml(node_to_dict(obj_to_node(obj)))
    if fileobj is None:
        return toml.dumps(dic)
    toml.dump(dic, fileobj)
