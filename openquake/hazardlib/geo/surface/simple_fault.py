# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.surface.simple_fault` defines
:class:`SimpleFaultSurface`.
"""
import math

import numpy

from openquake.baselib.node import Node
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.geo import Point, Line, utils as geo_utils
from openquake.hazardlib.near_fault import get_plane_equation


def simple_fault_node(fault_trace, dip, upper_depth, lower_depth):
    """
    :param fault_trace: an object with an attribute .points
    :param dip: dip parameter
    :param upper_depth: upper seismogenic depth
    :param lower_depth: lower seismogenic depth
    :returns: a Node of kind simpleFaultGeometry
    """
    node = Node('simpleFaultGeometry')
    line = []
    for p in fault_trace.points:
        line.append(p.longitude)
        line.append(p.latitude)
    node.append(Node('gml:LineString', nodes=[Node('gml:posList', {}, line)]))
    node.append(Node('dip', {}, dip))
    node.append(Node('upperSeismoDepth', {}, upper_depth))
    node.append(Node('lowerSeismoDepth', {}, lower_depth))
    return node


class SimpleFaultSurface(BaseSurface):
    """
    Represent a fault surface as regular (uniformly spaced) 3D mesh of points.

    :param mesh:
        Instance of :class:`~openquake.hazardlib.geo.mesh.RectangularMesh`
        representing surface geometry.

    Another way to construct the surface object is to call
    :meth:`from_fault_data`.
    """
    def __init__(self, mesh):
        self.mesh = mesh
        assert 1 not in self.mesh.shape, (
            "Mesh must have at least 2 nodes along both length and width.")
        self.strike = self.dip = None

    @property
    def tor(self):
        """
        :returns: top of rupture line
        """
        lons = self.mesh.lons[0, :]
        lats = self.mesh.lats[0, :]
        coo = numpy.array([[lo, la] for lo, la in zip(lons, lats)])
        line = Line.from_vectors(coo[:, 0], coo[:, 1])
        return line.keep_corners(1.)

    def get_dip(self):
        """
        Return the fault dip as the average dip over the fault surface mesh.

        The average dip is defined as the weighted mean inclination of top
        row of mesh cells. See
        :meth:`openquake.hazardlib.geo.mesh.RectangularMesh.get_mean_inclination_and_azimuth`

        :returns:
            The average dip, in decimal degrees.
        """
        if self.dip is None:
            # calculate weighted average dip and strike of only the top row
            # of cells since those values are uniform along dip for simple
            # faults
            top_row = self.mesh[0:2]
            self.dip, self.strike = top_row.get_mean_inclination_and_azimuth()
        return self.dip

    def get_strike(self):
        """
        Return the fault strike as the average strike along the fault trace.

        The average strike is defined as the weighted mean azimuth of top
        row of mesh cells. See
        :meth:`openquake.hazardlib.geo.mesh.RectangularMesh.get_mean_inclination_and_azimuth`

        :returns:
            The average strike, in decimal degrees.
        """
        if self.strike is None:
            self.get_dip()  # this should cache strike value
        return self.strike

    @classmethod
    def check_fault_data(cls, fault_trace, upper_seismogenic_depth,
                         lower_seismogenic_depth, dip, mesh_spacing):
        """
        Verify the fault data and raise ``ValueError`` if anything is wrong.

        This method doesn't have to be called by hands before creating the
        surface object, because it is called from :meth:`from_fault_data`.
        """
        if not len(fault_trace) >= 2:
            raise ValueError("the fault trace must have at least two points")
        if not fault_trace.horizontal():
            raise ValueError("the fault trace must be horizontal")
        tlats = numpy.array([point.latitude for point in fault_trace.points])
        tlons = numpy.array([point.longitude for point in fault_trace.points])
        if geo_utils.line_intersects_itself(tlons, tlats):
            raise ValueError("fault trace intersects itself")
        if not 0.0 < dip <= 90.0:
            raise ValueError("dip must be between 0.0 and 90.0")
        if not lower_seismogenic_depth > upper_seismogenic_depth:
            raise ValueError("lower seismogenic depth must be greater than "
                             "upper seismogenic depth")
        if not upper_seismogenic_depth >= fault_trace[0].depth:
            raise ValueError("upper seismogenic depth must be greater than "
                             "or equal to depth of fault trace")
        if not mesh_spacing > 0.0:
            raise ValueError("mesh spacing must be positive")

    @classmethod
    def from_fault_data(cls, fault_trace, upper_seismogenic_depth,
                        lower_seismogenic_depth, dip, mesh_spacing):
        """
        Create and return a fault surface using fault source data.

        :param openquake.hazardlib.geo.line.Line fault_trace:
            Geographical line representing the intersection between the fault
            surface and the earth surface. The line must be horizontal (i.e.
            all depth values must be equal). If the depths are not given, they
            are assumed to be zero, meaning the trace intersects the surface at
            sea level, e.g. fault_trace = Line([Point(1, 1), Point(1, 2)]).
        :param upper_seismo_depth:
            Minimum depth ruptures can reach, in km (i.e. depth
            to fault's top edge).
        :param lower_seismo_depth:
            Maximum depth ruptures can reach, in km (i.e. depth
            to fault's bottom edge).
        :param dip:
            Dip angle (i.e. angle between fault surface
            and earth surface), in degrees.
        :param mesh_spacing:
            Distance between two subsequent points in a mesh, in km.
        :returns:
            An instance of :class:`SimpleFaultSurface` created using that data.

        Uses :meth:`check_fault_data` for checking parameters.
        """
        cls.check_fault_data(fault_trace, upper_seismogenic_depth,
                             lower_seismogenic_depth, dip, mesh_spacing)
        # Loops over points in the top edge, for each point
        # on the top edge compute corresponding point on the bottom edge, then
        # computes equally spaced points between top and bottom points.

        vdist_top = upper_seismogenic_depth - fault_trace[0].depth
        vdist_bottom = lower_seismogenic_depth - fault_trace[0].depth

        hdist_top = vdist_top / math.tan(math.radians(dip))
        hdist_bottom = vdist_bottom / math.tan(math.radians(dip))

        strike = fault_trace[0].azimuth(fault_trace[-1])
        azimuth = (strike + 90.0) % 360

        mesh = []
        for point in fault_trace.resample(mesh_spacing):
            top = point.point_at(hdist_top, vdist_top, azimuth)
            bottom = point.point_at(hdist_bottom, vdist_bottom, azimuth)
            mesh.append(top.equally_spaced_points(bottom, mesh_spacing))

        # number of rows corresponds to number of points along dip
        # number of columns corresponds to number of points along strike
        surface_points = numpy.array(mesh).transpose().tolist()
        mesh = RectangularMesh.from_points_list(surface_points)
        assert 1 not in mesh.shape, (
            "Mesh must have at least 2 nodes along both length and width."
            " Possible cause: Mesh spacing could be too large with respect to"
            " the fault length and width.")
        self = cls(mesh)
        self.surface_nodes = [simple_fault_node(
            fault_trace, dip,
            upper_seismogenic_depth, lower_seismogenic_depth)]
        return self

    @classmethod
    def get_fault_patch_vertices(cls, rupture_top_edge,
                                 upper_seismogenic_depth,
                                 lower_seismogenic_depth, dip, index_patch=1):
        """
        Get surface main vertices.
        Parameters are the same as for :meth:`from_fault_data`, excluding
        fault_trace, and mesh spacing.

        :param rupture_top_edge:
            A instances of :class:`openquake.hazardlib.geo.line.Line`
            representing the rupture surface's top edge.
        :param index_patch:
            Indicate the patch of the fault in order to output the vertices.
            The fault patch numbering follows the same logic of the right-hand
            rule i.e. patch with index 1 is the first patch along the trace.
        :returns:
            Four :class:~openquake.hazardlib.geo.point.Point objects
            representing the four vertices of the target patch.
        """
        # Similar to :meth:`from_fault_data`, we just don't resample edges
        dip_tan = math.tan(math.radians(dip))
        hdist_bottom = (
            lower_seismogenic_depth - upper_seismogenic_depth) / dip_tan
        strike = rupture_top_edge[0].azimuth(rupture_top_edge[-1])
        azimuth = (strike + 90.0) % 360
        # Collect coordinates of vertices on the top and bottom edge
        lons = []
        lats = []
        deps = []

        t_lon = []
        t_lat = []
        t_dep = []
        for point in rupture_top_edge.points:
            top_edge_point = point
            bottom_edge_point = point.point_at(hdist_bottom, 0, azimuth)
            lons.append(top_edge_point.longitude)
            lats.append(top_edge_point.latitude)
            deps.append(upper_seismogenic_depth)
            t_lon.append(bottom_edge_point.longitude)
            t_lat.append(bottom_edge_point.latitude)
            t_dep.append(lower_seismogenic_depth)

            all_lons = numpy.array(lons + list(reversed(t_lon)), float)
            all_lats = numpy.array(lats + list(reversed(t_lat)), float)
            all_deps = numpy.array(deps + list(reversed(t_dep)), float)
        index1 = int(index_patch - 1)
        index2 = int(index_patch)
        index3 = int(2 * len(rupture_top_edge) - (index_patch + 1))
        index4 = int(2 * len(rupture_top_edge) - index_patch)
        p0 = Point(all_lons[index1], all_lats[index1], all_deps[index1])
        p1 = Point(all_lons[index2], all_lats[index2], all_deps[index2])
        p2 = Point(all_lons[index3], all_lats[index3], all_deps[index3])
        p3 = Point(all_lons[index4], all_lats[index4], all_deps[index4])
        return p0, p1, p2, p3

    @classmethod
    def hypocentre_patch_index(cls, hypocentre, rupture_top_edge,
                               upper_seismogenic_depth,
                               lower_seismogenic_depth, dip):
        """
        This methods finds the index of the fault patch including
        the hypocentre.

        :param hypocentre:
            :class:`~openquake.hazardlib.geo.point.Point` object
            representing the location of hypocentre.
        :param rupture_top_edge:
            A instances of :class:`openquake.hazardlib.geo.line.Line`
            representing the rupture surface's top edge.
        :param upper_seismo_depth:
            Minimum depth ruptures can reach, in km (i.e. depth
            to fault's top edge).
        :param lower_seismo_depth:
            Maximum depth ruptures can reach, in km (i.e. depth
            to fault's bottom edge).
        :param dip:
            Dip angle (i.e. angle between fault surface
            and earth surface), in degrees.
        :return:
            An integer corresponding to the index of the fault patch which
            contains the hypocentre.
        """
        totaln_patch = len(rupture_top_edge)
        indexlist = []
        dist_list = []
        for i, index in enumerate(range(1, totaln_patch)):
            p0, p1, p2, _p3 = cls.get_fault_patch_vertices(
                rupture_top_edge, upper_seismogenic_depth,
                lower_seismogenic_depth, dip, index_patch=index)

            [_normal, dist_to_plane] = get_plane_equation(p0, p1, p2,
                                                          hypocentre)
            indexlist.append(index)
            dist_list.append(dist_to_plane)
            if numpy.allclose(dist_to_plane, 0., atol=25., rtol=0.):
                return index
                break
        index = indexlist[numpy.argmin(dist_list)]
        return index

    @classmethod
    def get_surface_vertexes(cls, fault_trace,
                             upper_seismogenic_depth,
                             lower_seismogenic_depth, dip):
        """
        Get surface main vertexes.

        Parameters are the same as for :meth:`from_fault_data`, excluding
        mesh spacing.

        :returns:
            Instance of :class:`~openquake.hazardlib.geo.polygon.Polygon`
            describing the surface projection of the simple fault with
            specified parameters.
        """
        # Similar to :meth:`from_fault_data`, we just don't resample edges
        dip_tan = math.tan(math.radians(dip))
        hdist_top = upper_seismogenic_depth / dip_tan
        hdist_bottom = lower_seismogenic_depth / dip_tan

        strike = fault_trace[0].azimuth(fault_trace[-1])
        azimuth = (strike + 90.0) % 360

        # Collect coordinates of vertices on the top and bottom edge
        lons = []
        lats = []
        for point in fault_trace.points:
            top_edge_point = point.point_at(hdist_top, 0, azimuth)
            bottom_edge_point = point.point_at(hdist_bottom, 0, azimuth)
            lons.append(top_edge_point.longitude)
            lats.append(top_edge_point.latitude)
            lons.append(bottom_edge_point.longitude)
            lats.append(bottom_edge_point.latitude)

        lons = numpy.array(lons, float)
        lats = numpy.array(lats, float)
        return lons, lats

    @classmethod
    def surface_projection_from_fault_data(cls, fault_trace,
                                           upper_seismogenic_depth,
                                           lower_seismogenic_depth, dip):
        """
        Get a surface projection of the simple fault surface.

        Parameters are the same as for :meth:`from_fault_data`, excluding
        mesh spacing.

        :returns:
            Instance of :class:`~openquake.hazardlib.geo.polygon.Polygon`
            describing the surface projection of the simple fault with
            specified parameters.
        """
        lons, lats = cls.get_surface_vertexes(fault_trace,
                                              upper_seismogenic_depth,
                                              lower_seismogenic_depth, dip)
        return Mesh(lons, lats, depths=None).get_convex_hull()

    def get_width(self):
        """
        Return surface's width (that is surface extension along the
        dip direction) in km.

        The width is computed as the average width along the surface.
        See
        :meth:`openquake.hazardlib.geo.mesh.RectangularMesh.get_mean_width`
        """
        # calculate width only along the first mesh column, because
        # width is uniform for simple faults
        left_column = self.mesh[:, 0:2]
        return left_column.get_mean_width()
