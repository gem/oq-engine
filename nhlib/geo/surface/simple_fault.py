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
Module :mod:`nhlib.surface.simple_fault` contains :class:`SimpleFaultSurface`.
"""
import math
import numpy

from nhlib.geo.surface.base import BaseSurface
from nhlib.geo.line import Line
from nhlib.geo.mesh import RectangularMesh
from nhlib.geo._utils import spherical_to_cartesian, ensure


class SimpleFaultSurface(BaseSurface):
    """
    Represent a fault surface as regular (uniformly spaced) 3D mesh of points.

    :param fault_trace:
        Geographical line representing the intersection between
        the fault surface and the earth surface.
    :type fault_trace:
        instance of :class:`nhlib.Line`
    :param upper_seismo_depth:
        Minimum depth ruptures can reach, in km (i.e. depth
        to fault's top edge).
    :type upper_seismo_depth:
        float
    :param lower_seismo_depth:
        Maximum depth ruptures can reach, in km (i.e. depth
        to fault's bottom edge).
    :type lower_seismo_depth:
        float
    :param dip:
        Dip angle (i.e. angle between fault surface
        and earth surface), in degrees.
    :type dip:
        float
    """

    def __init__(self, fault_trace, upper_seismo_depth,
            lower_seismo_depth, dip, mesh_spacing):

        super(SimpleFaultSurface, self).__init__()

        ensure(len(fault_trace) >= 2,
                "The fault trace must have at least two points!")

        ensure(fault_trace.on_surface(),
                "The fault trace must be defined on the surface!")

        ensure(0.0 < dip <= 90.0, "Dip must be between 0.0 and 90.0!")

        ensure(lower_seismo_depth > upper_seismo_depth,
                "Lower seismo depth must be > than upper seismo dept!")

        ensure(upper_seismo_depth >= 0.0,
                "Upper seismo depth must be >= 0.0!")

        ensure(mesh_spacing > 0.0, "Mesh spacing must be > 0.0!")

        self.dip = dip
        self.fault_trace = fault_trace
        self.mesh_spacing = mesh_spacing
        self.upper_seismo_depth = upper_seismo_depth
        self.lower_seismo_depth = lower_seismo_depth

    def _create_mesh(self):
        """
        See :meth:`nhlib.surface.base.BaseSurface.get_mesh`.
        """
        # Loops over points in the top edge, for each point
        # on the top edge compute corresponding point on the bottom edge, then
        # computes equally spaced points between top and bottom points.

        vertical_distance = (self.lower_seismo_depth - self.upper_seismo_depth)

        horizontal_distance = vertical_distance / math.tan(
                math.radians(self.dip))

        strike = self.fault_trace[0].azimuth(self.fault_trace[-1])
        azimuth = (strike + 90.0) % 360

        mesh = []
        for point in self._fault_top_edge(azimuth):
            bottom = point.point_at(
                horizontal_distance, vertical_distance, azimuth)
            mesh.append(point.equally_spaced_points(bottom, self.mesh_spacing))

        # number of rows corresponds to number of points along dip
        # number of columns corresponds to number of points along strike
        surface_points = numpy.array(mesh).transpose().tolist()
        return RectangularMesh.from_points_list(surface_points)

    def get_dip(self):
        """
        Return the fault dip as the average dip over the fault surface mesh.

        It is computed as the average value of the dip values of the mesh cells
        in the first row of the surface mesh (in case of a simple fault surface
        the dip is constant over depth, so there is not need to compute the dip
        angle along width).

        The dip of each mesh cell is obtained by calculating the vector normal
        to the vertical surface that cell's top segment lies in (this vector
        is parallel to earth surface and pointing towards dip direction) and
        vector pointing from top to bottom points in a same column of points
        in the mesh. The dot product of these two vectors is the dip angle
        of a cell.

        If the surface mesh has only one location along width or one along
        strike, it returns the dip value describing this fault surface.

        :returns:
            The average dip, in decimal degrees.
        """
        mesh = self.get_mesh()
        if 1 in mesh.shape:
            # mesh has one row and/or one column, no need to calc any mean
            return self.dip

        # mesh of the top row of points
        line0 = mesh[0:1]
        # mesh of the second row of points
        line1 = mesh[1:2]
        # Cartesian 3d-coordinates of points in the top row
        coords0 = spherical_to_cartesian(
            line0.lons, line0.lats, line0.depths
        ).reshape(3, -1).transpose()
        # Cartesian coordinates of points in the second row
        coords1 = spherical_to_cartesian(
            line1.lons, line1.lats, line1.depths
        ).reshape(3, -1).transpose()
        # Cartesian coordinates of points just below ones in the first row.
        # that is, the same lons and lats but deeper depth
        coords2 = spherical_to_cartesian(
            line0.lons, line0.lats, line0.depths + 1.0
        ).reshape(3, -1).transpose()
        # vectors, normal to planes defined by pairs of vectors, where first
        # one is the one between subsequent points in the top row and the
        # second is directed downwards from one of those
        normals = numpy.cross((coords0[:-1] - coords0[1:]),
                              (coords2[:-1] - coords0[:-1]))
        # normalize these normal vectors by dividing all coordinate components
        # by vector's length
        normals /= numpy.sqrt(numpy.sum(normals ** 2, axis=1)).reshape((-1, 1))
        # vectors along the dip direction
        downdip = coords1[:-1] - coords0[:-1]
        # we need both ``normals`` and ``downdip`` normalized because we will
        # use dot product of those for calculating angle in between
        downdip /= numpy.sqrt(numpy.sum(downdip ** 2, axis=1)).reshape((-1, 1))

        dot_products = numpy.sum(normals * downdip, axis=1)
        return numpy.degrees(numpy.mean(numpy.arccos(dot_products)))

    def get_strike(self):
        """
        Return the fault strike as the average strike along the fault trace.

        The average strike is defined as the average of the
        azimuth values for all the fault trace segments.

        :returns:
            The average strike, in decimal degrees.
        :rtype:
            float
        """
        return self.fault_trace.average_azimuth()

    def _fault_top_edge(self, azimuth):
        """
        Line representing the fault top edge.

        It is obtained by translating the fault trace from the earth surface
        to the upper seismogenic depth, with an inclination equal to
        the dip angle, and along a direction perpendicular the fault strike
        (computed as the azimuth between the fault trace's first
        and last points). The line is then resampled in equal length segments
        (length equal to ``mesh_spacing``).

        :param azimuth:
            The azimuth perpendicular to the fault strike (the direction along
            dip) in decimal degrees.
        :returns:
            List of points (instances of :class:`~nhlib.geo.point.Point`)
            of the fault top edge.
        """
        horizontal_distance = 0.0
        if self.dip < 90.0:
            horizontal_distance = self.upper_seismo_depth / math.tan(
                    math.radians(self.dip))

        vertical_distance = self.upper_seismo_depth
        top_edge_points = [
            point.point_at(horizontal_distance, vertical_distance, azimuth)
            for point in self.fault_trace
        ]
        return Line(top_edge_points).resample(self.mesh_spacing).points
