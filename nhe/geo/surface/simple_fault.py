# encoding: utf-8
"""
Module :mod:`nhe.surface.simple_fault` contains :class:`SimpleFaultSurface`.
"""

import math
import numpy

from nhe.geo.surface.base import BaseSurface
from nhe.geo.line import Line


def _ensure(expr, msg):
    """
    Utility method that raises an error if the
    given condition is not true.
    """

    if not expr:
        raise ValueError(msg)


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

        _ensure(len(fault_trace) >= 2,
                "The fault trace must have at least two points!")

        _ensure(fault_trace.on_surface(),
                "The fault trace must be defined on the surface!")

        _ensure(0.0 < dip <= 90.0, "Dip must be between 0.0 and 90.0!")

        _ensure(lower_seismo_depth > upper_seismo_depth,
                "Lower seismo depth must be > than upper seismo dept!")

        _ensure(upper_seismo_depth >= 0.0,
                "Upper seismo depth must be >= 0.0!")

        _ensure(mesh_spacing > 0.0, "Mesh spacing must be > 0.0!")

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

        top_edge = self._fault_top_edge(mesh_spacing)

        for point in top_edge:

            bottom = point.point_at(
                horizontal_distance, vertical_distance, azimuth)

            points = point.equally_spaced_points(bottom, mesh_spacing)
            mesh.extend(points)

        # number of rows corresponds to number of points along dip
        # number of columns corresponds to number of points along strike
        surface = numpy.array(mesh)
        surface = surface.reshape(len(top_edge), len(mesh) / len(top_edge))
        surface = numpy.transpose(surface)

        lons = numpy.map(surface, lambda x: x.longitude)
        

        return surface.tolist()

    def get_dip(self):
        pass

    def get_strike(self):
        pass

    def _fault_top_edge(self, mesh_spacing):
        """
        Line representing the fault top edge.

        It's obtained by translating the fault trace from the earth surface
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

            top_edge = Line(top_edge).resample(mesh_spacing).points

        return top_edge
