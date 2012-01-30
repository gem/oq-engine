# encoding: utf-8
"""
Module :mod:`nhe.surface.simple_fault` contains :class:`SimpleFaultSurface`.
"""

import math
import numpy

from nhe.surface.base import BaseSurface
from nhe.common import geo


def _ensure(expr, msg):
    """
    Utility method that raises an error if the
    given condition is not true.
    """

    if not expr:
        raise RuntimeError(msg)


class SimpleFaultSurface(BaseSurface):

    def __init__(self, fault_trace, upper_seismo_depth,
            lower_seismo_depth, dip):

        _ensure(len(fault_trace) >= 2,
                "The fault trace must have at least two points!")

        _ensure(fault_trace.on_surface(),
                "The fault trace must be defined on the surface!")

        _ensure(0.0 < dip <= 90.0, "Dip must be between 0.0 and 90.0!")

        _ensure(lower_seismo_depth >= upper_seismo_depth,
                "Lower seismo depth must be >= than upper seismo dept!")

        _ensure(upper_seismo_depth >= 0.0,
                "Upper seismo depth must be >= 0.0!")

        self.dip = dip
        self.fault_trace = fault_trace
        self.upper_seismo_depth = upper_seismo_depth
        self.lower_seismo_depth = lower_seismo_depth

    def get_mesh(self, mesh_spacing):
        """
        See :meth:`nhe.surface.base.BaseSurface.get_mesh`.
        """

        _ensure(mesh_spacing > 0.0, "Mesh spacing must be > 0.0!")

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

        return surface.tolist()

    def _fault_top_edge(self, mesh_spacing):
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

            top_edge = geo.Line(top_edge).resample(mesh_spacing).points

        return top_edge
