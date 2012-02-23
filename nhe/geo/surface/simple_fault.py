# encoding: utf-8
"""
Module :mod:`nhe.surface.simple_fault` contains :class:`SimpleFaultSurface`.
"""

import math
import numpy

from nhe.geo.surface.base import BaseSurface
from nhe.geo.line import Line
from nhe.geo.mesh import RectangularMesh
from nhe.geo._utils import plane_dip, ensure


class SimpleFaultSurface(BaseSurface):
    """
    Represent a fault surface as regular (uniformly spaced) 3D mesh of points.

    :param fault_trace:
        Geographical line representing the intersection between
        the fault surface and the earth surface.
    :type fault_trace:
        instance of :class:`nhe.Line`
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
        See :meth:`nhe.surface.base.BaseSurface.get_mesh`.
        """

        # Loops over points in the top edge, for each point
        # on the top edge compute corresponding point on the bottom edge, then
        # computes equally spaced points between top and bottom points.

        vertical_distance = (self.lower_seismo_depth - self.upper_seismo_depth)

        horizontal_distance = vertical_distance / math.tan(
                math.radians(self.dip))

        strike = self.fault_trace[0].azimuth(self.fault_trace[-1])
        azimuth = strike + 90.0

        mesh = []

        top_edge = self._fault_top_edge()

        for point in top_edge:

            bottom = point.point_at(
                horizontal_distance, vertical_distance, azimuth)

            points = point.equally_spaced_points(bottom, self.mesh_spacing)
            mesh.extend(points)

        # number of rows corresponds to number of points along dip
        # number of columns corresponds to number of points along strike
        surface = numpy.array(mesh)
        surface = surface.reshape(len(top_edge), len(mesh) / len(top_edge))
        surface = numpy.transpose(surface)

        return RectangularMesh.from_points_list(surface.tolist())

    def get_dip(self):
        """
        Return the fault dip as the average dip over the fault surface mesh.

        It is computed as the average value of the dip values of the mesh cells
        in the first row of the surface mesh (in case of a simple fault surface
        the dip is constant over depth, so there is not need
        to compute the dip angle along width).

        The dip of each mesh cell is obtained by calculating the vector normal
        to each mesh cell, and the vector normal to the earth surface at the
        cell location. The angle between these two vectors is the dip angle.

        If the surface mesh has only one location along width
        or one along strike, it returns the dip value
        describing this fault surface.

        :returns:
            The average dip, in decimal degrees.
        :rtype:
            float
        """

        surface = self.get_mesh()
        dip = self.dip

        # more than one row and one column in the mesh
        if surface.shape[0] > 1 and surface.shape[1] > 1:
            average_dip = 0.0

            row_1 = list(surface[0:1])
            row_2 = list(surface[1:2])

            for i in xrange(len(row_1) - 1):
                p1 = row_1[i]
                p2 = row_1[i + 1]
                p3 = row_2[i]

                dip = plane_dip(p1, p2, p3)
                average_dip = average_dip + dip

            dip = average_dip / (surface.shape[1] - 1)

        return dip

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

        average_strike = 0.0
        fault_trace_length = 0.0

        for i in xrange(len(self.fault_trace) - 1):
            current_point = self.fault_trace[i]
            next_point = self.fault_trace[i + 1]

            strike = current_point.azimuth(next_point)
            section_length = current_point.horizontal_distance(next_point)

            average_strike = average_strike + section_length * strike
            fault_trace_length = fault_trace_length + section_length

        return average_strike / fault_trace_length

    def _fault_top_edge(self):
        """
        Line representing the fault top edge.

        It is obtained by translating the fault trace from the earth surface
        to the upper seismogenic depth, with an inclination equal to
        the dip angle, and along a direction perpendicular the fault strike
        (computed as the azimuth between the fault trace's first
        and last points). The line is then resampled in equal length segments
        (length equal to ``mesh_spacing``).

        :param mesh_spacing:
            Spacing between mesh points, in km.
        :type mesh_spacing:
            float
        :returns:
            The fault top edge.
        :rtype:
            instance of :class:`nhe.Line`
        """

        top_edge = []
        horizontal_distance = 0.0

        if self.dip < 90.0:
            horizontal_distance = self.upper_seismo_depth / math.tan(
                    math.radians(self.dip))

        vertical_distance = self.upper_seismo_depth
        strike = self.fault_trace[0].azimuth(self.fault_trace[-1])
        azimuth = strike + 90.0

        for point in self.fault_trace:
            top_edge.append(point.point_at(
                    horizontal_distance, vertical_distance, azimuth))

            top_edge = Line(top_edge).resample(self.mesh_spacing).points

        return top_edge
