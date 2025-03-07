# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
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
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
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

from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.scalerel import get_available_scalerel
from openquake.hazardlib.scalerel.base import BaseMSR
from openquake.hazardlib.scalerel.wc1994 import WC1994

SCALE_RELS = get_available_scalerel()


def render_aspect_ratio(aspect_ratio, use_default=False):
    """
    Returns the aspect ratio if one is defined for the source, otherwise
    if defaults are accepted a default value of 1.0 is returned or else
    a ValueError is raised

    :param float aspect_ratio:
        Ratio of along strike-length to down-dip width of the rupture

    :param bool use_default:
        If true, when aspect_ratio is undefined will return default value of
        1.0, otherwise will raise an error.
    """
    if aspect_ratio:
        assert aspect_ratio > 0.0
        return aspect_ratio
    else:
        if use_default:
            return 1.0
        else:
            raise ValueError("Rupture aspect ratio not defined!")


def mag_scale_rel_to_hazardlib(mag_scale_rel, use_default=False):
    """
    Returns the magnitude scaling relation in a format readable by
    openquake.hazardlib
    """
    if isinstance(mag_scale_rel, BaseMSR):
        return mag_scale_rel
    elif isinstance(mag_scale_rel, str):
        if mag_scale_rel not in SCALE_RELS:
            raise ValueError(
                "Magnitude scaling relation %s not supported!" % mag_scale_rel
            )
        else:
            return SCALE_RELS[mag_scale_rel]()
    else:
        if use_default:
            # Returns the Wells and Coppersmith string
            return WC1994()
        else:
            raise ValueError("Magnitude Scaling Relation Not Defined!")


def npd_to_pmf(nodal_plane_dist, use_default=False):
    """
    Returns the nodal plane distribution as an instance of the PMF class
    """
    if isinstance(nodal_plane_dist, PMF):
        # Aready in PMF format - return
        return nodal_plane_dist
    else:
        if use_default:
            return PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))])
        else:
            raise ValueError("Nodal Plane distribution not defined")


def hdd_to_pmf(hypo_depth_dist, use_default=False):
    """
    Returns the hypocentral depth distribtuion as an instance of the :class:
    openquake.hazardlib.pmf.
    """
    if isinstance(hypo_depth_dist, PMF):
        # Is already instance of PMF
        return hypo_depth_dist
    else:
        if use_default:
            # Default value of 10 km accepted
            return PMF([(1.0, 10.0)])
        else:
            # Out of options - raise error!
            raise ValueError("Hypocentral depth distribution not defined!")


def simple_trace_to_wkt_linestring(trace):
    """
    Coverts a simple fault trace to well-known text format

    :param trace:
        Fault trace as instance of :class: openquake.hazardlib.geo.line.Line

    :returns:
        Well-known text (WKT) Linstring representation of the trace
    """
    trace_str = ""
    for point in trace:
        trace_str += " %s %s," % (point.longitude, point.latitude)
    trace_str = trace_str.lstrip(" ")
    return "LINESTRING (" + trace_str.rstrip(",") + ")"


def simple_edge_to_wkt_linestring(edge):
    """
    Coverts a simple fault trace to well-known text format

    :param trace:
        Fault trace as instance of :class: openquake.hazardlib.geo.line.Line

    :returns:
        Well-known text (WKT) Linstring representation of the trace
    """
    trace_str = ""
    for point in edge:
        trace_str += " %s %s %s," % (
            point.longitude,
            point.latitude,
            point.depth,
        )
    trace_str = trace_str.lstrip(" ")
    return "LINESTRING (" + trace_str.rstrip(",") + ")"
