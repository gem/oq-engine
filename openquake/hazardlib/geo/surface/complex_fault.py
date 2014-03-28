# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.geo.surface.complex_fault` defines
:class:`ComplexFaultSurface`.
"""
import numpy
import shapely

from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.surface.base import BaseQuadrilateralSurface
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh


class ComplexFaultSurface(BaseQuadrilateralSurface):
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
        super(ComplexFaultSurface, self).__init__()
        self.mesh = mesh
        assert not 1 in self.mesh.shape
        self.strike = self.dip = None

        # A common user error is to create a ComplexFaultSourceSurface
        # from invalid fault data (e.g. mixing the order of
        # vertexes for top and bottom edges). Therefore, we want to
        # restrict every complex source to have a projected enclosing
        # polygon that is not a multipolygon.
        if isinstance(
                self.get_mesh()._get_proj_enclosing_polygon()[1],
                shapely.geometry.multipolygon.MultiPolygon):
            raise ValueError("Invalid surface. "
                             "The projected enclosing polygon "
                             "must be a simple polygon. "
                             "Check the geometry definition of the "
                             "fault source")

    def _create_mesh(self):
        """
        Return a mesh provided to object's constructor.
        """
        return self.mesh

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
            mesh = self.get_mesh()
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

        mean_length = numpy.mean([edge.get_length() for edge in edges])
        num_hor_points = int(round(mean_length / mesh_spacing)) + 1
        if num_hor_points <= 1:
            raise ValueError(
                'mesh spacing %.1f km is too big for mean length %.1f km' %
                (mesh_spacing, mean_length)
            )
        edges = [edge.resample_to_num_points(num_hor_points).points
                 for i, edge in enumerate(edges)]

        vert_edges = [Line(v_edge) for v_edge in zip(*edges)]
        mean_width = numpy.mean([v_edge.get_length() for v_edge in vert_edges])
        num_vert_points = int(round(mean_width / mesh_spacing)) + 1
        if num_vert_points <= 1:
            raise ValueError(
                'mesh spacing %.1f km is too big for mean width %.1f km' %
                (mesh_spacing, mean_width)
            )

        points = zip(*[v_edge.resample_to_num_points(num_vert_points).points
                       for v_edge in vert_edges])
        mesh = RectangularMesh.from_points_list(points)
        assert 1 not in mesh.shape
        return cls(mesh)

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
