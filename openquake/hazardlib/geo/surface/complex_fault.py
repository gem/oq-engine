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
Module :mod:`openquake.hazardlib.geo.surface.complex_fault` defines
:class:`ComplexFaultSurface`.
"""
import numpy
import shapely

from openquake.baselib.node import Node
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.geo.utils import spherical_to_cartesian

def edge_node(name, points):
    """
    :param name: 'faultTopEdge', 'intermediateEdge' or 'faultBottomEdge'
    :param points: a list of Point objects
    :returns: a Node of kind faultTopEdge, intermediateEdge or faultBottomEdge
    """
    line = []
    for point in points:
        line.append(point.longitude)
        line.append(point.latitude)
        line.append(point.depth)
    pos = Node('gml:posList', {}, line)
    node = Node(name, nodes=[Node('gml:LineString', nodes=[pos])])
    return node


def complex_fault_node(edges):
    """
    :param edges: a list of lists of points
    :returns: a Node of kind complexFaultGeometry
    """
    node = Node('complexFaultGeometry')
    node.append(edge_node('faultTopEdge', edges[0]))
    for edge in edges[1:-1]:
        node.append(edge_node('intermediateEdge', edge))
    node.append(edge_node('faultBottomEdge', edges[-1]))
    return node


class ComplexFaultSurface(BaseSurface):
    """
    Represent a complex fault surface as 3D mesh of points (not necessarily
    uniformly spaced across the surface area).

    :param mesh:
        Instance of :class:`~openquake.hazardlib.geo.mesh.RectangularMesh`
        representing surface geometry.

    Another way to construct the surface object is to call
    :meth:`from_fault_data`.
    """
    def __init__(self, mesh):
        self.mesh = mesh
        assert 1 not in self.mesh.shape, self.mesh.shape
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
        Return the fault dip as the average dip over the mesh.

        The average dip is defined as the weighted mean inclination
        of all the mesh cells. See
        :meth:`openquake.hazardlib.geo.mesh.RectangularMesh.get_mean_inclination_and_azimuth`

        :returns:
            The average dip, in decimal degrees.
        """
        # uses the same approach as in simple fault surface
        if self.dip is None:
            mesh = self.mesh
            self.dip, self.strike = mesh.get_mean_inclination_and_azimuth()
        return self.dip

    def get_strike(self):
        """
        Return the fault strike as the average strike over the mesh.

        The average strike is defined as the weighted mean azimuth
        of all the mesh cells. See
        :meth:`openquake.hazardlib.geo.mesh.RectangularMesh.get_mean_inclination_and_azimuth`

        :returns:
            The average strike, in decimal degrees.
        """
        if self.strike is None:
            self.get_dip()  # this should cache strike value
        return self.strike

    @classmethod
    def check_aki_richards_convention(cls, edges):
        """
        Verify that surface conforms with Aki and
        Richard convention (i.e. surface dips right of surface strike)
        Test with 2 adjacent edges to allow for very large, curved surfaces

        This method doesn't have to be called by hands before creating the
        surface object, because it is called from :meth:`from_fault_data`.
        """
        # 1) extract 4 points of surface mesh from adjacent edges 
        # 2) compute cross products between left and right edges and top edge
        # (these define vectors normal to the surface)
        # 3) compute dot products between cross product results and
        # position vectors associated with upper left and right corners (if
        # both angles are less then 90 degrees then the surface is correctly
        # defined)
        ul = edges[0].points[0]
        u1 = edges[0].points[1]
        bl = edges[-1].points[0]
        b1 = edges[-1].points[1]
        
        ul, ur, bl, br = spherical_to_cartesian(
            [ul.longitude, u1.longitude, bl.longitude, b1.longitude],
            [ul.latitude, u1.latitude, bl.latitude, b1.latitude],
            [ul.depth, b1.depth, bl.depth, b1.depth])

        top_edge = ur - ul
        left_edge = bl - ul
        right_edge = br - ur
        left_cross_top = numpy.cross(left_edge, top_edge)
        right_cross_top = numpy.cross(right_edge, top_edge)
        if (left_cross_top == 0).all() or (right_cross_top == 0).all():
            return  # avoid division by zero

        left_cross_top /= numpy.sqrt(left_cross_top @ left_cross_top)
        right_cross_top /= numpy.sqrt(right_cross_top @ right_cross_top)

        ul /= numpy.sqrt(ul @ ul)
        ur /= numpy.sqrt(ur @ ur)

        # rounding to 1st digit, to avoid ValueError raised for floating point
        # imprecision
        angle_ul = numpy.round(
            numpy.degrees(numpy.arccos(ul @ left_cross_top)), 1)
        angle_ur = numpy.round(
            numpy.degrees(numpy.arccos(ur @ right_cross_top)), 1)

        if (angle_ul > 90) or (angle_ur > 90):
            raise ValueError(
                "Surface does not conform with Aki & Richards convention")
            
    @classmethod
    def check_surface_validity(cls, edges):
        """
        Check validity of the surface.

        Project edge points to vertical plane anchored to surface upper left
        edge and with strike equal to top edge strike. Check that resulting
        polygon is valid.

        This method doesn't have to be called by hands before creating the
        surface object, because it is called from :meth:`from_fault_data`.
        """
        # extract coordinates of surface boundary (as defined from edges)
        full_boundary = []
        left_boundary = []
        right_boundary = []

        for i in range(1, len(edges) - 1):
            left_boundary.append(edges[i].points[0])
            right_boundary.append(edges[i].points[-1])

        full_boundary.extend(edges[0].points)
        full_boundary.extend(right_boundary)
        full_boundary.extend(edges[-1].points[::-1])
        full_boundary.extend(left_boundary[::-1])

        lons = [p.longitude for p in full_boundary]
        lats = [p.latitude for p in full_boundary]
        depths = [p.depth for p in full_boundary]

        # define reference plane. Corner points are separated by an arbitrary
        # distance of 10 km. The mesh spacing is set to 2 km. Both corner
        # distance and mesh spacing values do not affect the algorithm results.
        ul = edges[0].points[0]
        strike = ul.azimuth(edges[0].points[-1])
        dist = 10.

        ur = ul.point_at(dist, 0, strike)
        bl = Point(ul.longitude, ul.latitude, ul.depth + dist)
        br = bl.point_at(dist, 0, strike)

        # project surface boundary to reference plane and check for
        # validity.
        ref_plane = PlanarSurface.from_corner_points(ul, ur, br, bl).array
        mat = spherical_to_cartesian(lons, lats, depths) - ref_plane.xyz[:, 0]
        xx, yy = mat @ ref_plane.uv1, mat @ ref_plane.uv2
        coords = [(x, y) for x, y in zip(xx, yy)]
        p = shapely.geometry.Polygon(coords)
        if not p.is_valid:
            raise ValueError('Edges points are not in the right order')

    @classmethod
    def check_fault_data(cls, edges, mesh_spacing):
        """
        Verify the fault data and raise ``ValueError`` if anything is wrong.

        This method doesn't have to be called by hands before creating the
        surface object, because it is called from :meth:`from_fault_data`.
        """
        if not len(edges) >= 2:
            raise ValueError("at least two edges are required")
        if not all(len(edge) >= 2 for edge in edges):
            raise ValueError("at least two points must be defined "
                             "in each edge")
        if not mesh_spacing > 0.0:
            raise ValueError("mesh spacing must be positive")

        cls.check_surface_validity(edges)
        cls.check_aki_richards_convention(edges)

    @classmethod
    def from_fault_data(cls, edges, mesh_spacing):
        """
        Create and return a fault surface using fault source data.

        :param edges:
            A list of at least two horizontal edges of the surface
            as instances of :class:`openquake.hazardlib.geo.line.Line`. The
            list should be in top-to-bottom order (the shallowest edge first).
        :param mesh_spacing:
            Distance between two subsequent points in a mesh, in km.
        :returns:
            An instance of :class:`ComplexFaultSurface` created using
            that data.
        :raises ValueError:
            If requested mesh spacing is too big for the surface geometry
            (doesn't allow to put a single mesh cell along length and/or
            width).

        Uses :meth:`check_fault_data` for checking parameters.
        """
        cls.check_fault_data(edges, mesh_spacing)
        surface_nodes = [complex_fault_node(edges)]
        mean_length = numpy.mean([edge.get_length() for edge in edges])
        num_hor_points = int(numpy.round(mean_length / mesh_spacing)) + 1
        if num_hor_points <= 1:
            raise ValueError(
                'mesh spacing %.1f km is too big for mean length %.1f km' %
                (mesh_spacing, mean_length)
            )
        edges = [edge.resample_to_num_points(num_hor_points).points
                 for i, edge in enumerate(edges)]

        vert_edges = [Line(v_edge) for v_edge in zip(*edges)]
        mean_width = numpy.mean([v_edge.get_length() for v_edge in vert_edges])
        num_vert_points = int(numpy.round(mean_width / mesh_spacing)) + 1
        if num_vert_points <= 1:
            raise ValueError(
                'mesh spacing %.1f km is too big for mean width %.1f km' %
                (mesh_spacing, mean_width)
            )

        points = zip(*[v_edge.resample_to_num_points(num_vert_points).points
                       for v_edge in vert_edges])
        mesh = RectangularMesh.from_points_list(list(points))
        assert 1 not in mesh.shape
        self = cls(mesh)
        self.surface_nodes = surface_nodes
        return self

    def check_proj_polygon(self):
        # called in ComplexFaultSource.iter_ruptures only in preclassical
        """
        A common user error is to create a ComplexFaultSourceSurface
        from invalid fault data (e.g. mixing the order of
        vertexes for top and bottom edges). Therefore, we want to
        restrict every complex source to have a projected enclosing
        polygon that is not a multipolygon.
        """
        if isinstance(self.mesh._get_proj_enclosing_polygon()[1],
                      shapely.geometry.multipolygon.MultiPolygon):
            raise ValueError("Invalid surface. "
                             "The projected enclosing polygon "
                             "must be a simple polygon. "
                             "Check the geometry definition of the "
                             "fault source")

    @classmethod
    def surface_projection_from_fault_data(cls, edges):
        """
        Get a surface projection of the complex fault surface.

        :param edges:
            A list of horizontal edges of the surface as instances
            of :class:`openquake.hazardlib.geo.line.Line`.
        :returns:
            Instance of :class:`~openquake.hazardlib.geo.polygon.Polygon`
            describing the surface projection of the complex fault.
        """
        # collect lons and lats of all the vertices of all the edges
        lons = []
        lats = []
        for edge in edges:
            for point in edge:
                lons.append(point.longitude)
                lats.append(point.latitude)
        lons = numpy.array(lons, dtype=float)
        lats = numpy.array(lats, dtype=float)

        return Mesh(lons, lats, depths=None).get_convex_hull()

    def get_width(self):
        """
        Return surface's width (that is surface extension along the
        dip direction) in km.

        The width is computed as the average width along the surface.
        See
        :meth:`openquake.hazardlib.geo.mesh.RectangularMesh.get_mean_width`
        """
        return self.mesh.get_mean_width()
