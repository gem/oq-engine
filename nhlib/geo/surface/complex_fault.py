# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
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
Module :mod:`nhlib.geo.surface.complex_fault` defines
:class:`ComplexFaultSurface`.
"""
from nhlib.geo.line import Line
from nhlib.geo.surface.base import BaseSurface
from nhlib.geo.mesh import RectangularMesh
from nhlib.geo._utils import ensure


class ComplexFaultSurface(BaseSurface):
    """
    Represent a complex fault surface as 3D mesh of points (not necessarily
    uniformly spaced across the surface area).

    :param mesh:
        Instance of :class:`~nhlib.geo.mesh.RectangularMesh` representing
        surface geometry.

    Another way to construct the surface object is to call
    :meth:`from_fault_data`.
    """
    def __init__(self, mesh):
        super(ComplexFaultSurface, self).__init__()
        self.mesh = mesh
        assert not 1 in self.mesh.shape
        self.strike = self.dip = None

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
        :meth:`nhlib.geo.mesh.RectangularMesh.get_mean_inclination_and_azimuth`

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
        :meth:`nhlib.geo.mesh.RectangularMesh.get_mean_inclination_and_azimuth`

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
        ensure(len(edges) >= 2, "at least two edges are required")
        ensure(all(len(edge) >= 2 for edge in edges),
               "at least two points must be defined in each edge")
        ensure(mesh_spacing > 0.0, "mesh spacing must be positive")
        # TODO: more strict/sophisticated checks for edges?

    @classmethod
    def from_fault_data(cls, edges, mesh_spacing):
        """
        Create and return a fault surface using fault source data.

        :param fault_trace:
            Geographical line representing the intersection between
            the fault surface and the earth surface, an instance
            of :class:`nhlib.Line`.
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
        cls.check_fault_data(edges, mesh_spacing)

        edges_lengths = []
        for edge in edges:
            length = edge.get_length()
            edges_lengths.append(length)
        mean_length = sum(edges_lengths) / len(edges)
        num_hor_segments = int(round(mean_length / mesh_spacing))
        assert num_hor_segments >= 1
        edges = [edge.resample(edges_lengths[i] / num_hor_segments).points
                 for i, edge in enumerate(edges)]

        vert_edges = [Line(v_edge) for v_edge in zip(*edges)]
        vert_edges_lengths = [v_edge.get_length() for v_edge in vert_edges]
        mean_width = sum(vert_edges_lengths) / (num_hor_segments + 1)
        num_vert_segments = int(round(mean_width / mesh_spacing))
        assert num_vert_segments >= 1

        points = zip(*[
            v_edge.resample(vert_edges_lengths[i] / num_vert_segments).points
            for v_edge in vert_edges
        ])
        mesh = RectangularMesh.from_points_list(points)
        assert 1 not in mesh.shape
        return cls(mesh)
