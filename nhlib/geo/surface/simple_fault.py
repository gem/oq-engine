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
Module :mod:`nhlib.geo.surface.simple_fault` defines
:class:`SimpleFaultSurface`.
"""
import math
import numpy

from nhlib.geo.surface.base import BaseSurface
from nhlib.geo.line import Line
from nhlib.geo.mesh import RectangularMesh
from nhlib.geo._utils import ensure


class SimpleFaultSurface(BaseSurface):
    """
    Represent a fault surface as regular (uniformly spaced) 3D mesh of points.

    :param mesh:
        Instance of :class:`~nhlib.geo.mesh.RectangularMesh` representing
        surface geometry.

    Another way to construct the surface object is to call
    :meth:`from_fault_data`.
    """
    def __init__(self, mesh):
        super(SimpleFaultSurface, self).__init__()
        self.mesh = mesh

    def _create_mesh(self):
        """
        Return a mesh provided to object's constructor.
        """
        return self.mesh

    def get_dip(self):
        """
        Return the fault dip as the average dip over the fault surface mesh.

        It is computed as the weighted average mean of the top row of the
        surface's mesh (in case of a simple fault surface the dip is constant
        over depth, so there is no need to compute the dip angle along width).
        See :meth:`nhlib.geo.mesh.RectangularMesh.get_mean_dip`.

        :returns:
            The average dip, in decimal degrees.
        """
        return self.get_mesh()[0:2].get_mean_dip()

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
        return Line(list(self.get_mesh()[0:1])).average_azimuth()

    @classmethod
    def check_fault_data(cls, fault_trace, upper_seismogenic_depth,
                         lower_seismogenic_depth, dip, mesh_spacing):
        """
        Verify the fault data and raise ``ValueError`` if anything is wrong.

        This method doesn't have to be called by hands before creating the
        surface object, because it is called from :meth:`from_fault_data`.
        """
        ensure(len(fault_trace) >= 2,
               "The fault trace must have at least two points!")
        ensure(fault_trace.on_surface(),
               "The fault trace must be defined on the surface!")
        ensure(0.0 < dip <= 90.0, "Dip must be between 0.0 and 90.0!")
        ensure(lower_seismogenic_depth > upper_seismogenic_depth,
               "Lower seismo depth must be > than upper seismo dept!")
        ensure(upper_seismogenic_depth >= 0.0,
               "Upper seismo depth must be >= 0.0!")
        ensure(mesh_spacing > 0.0, "Mesh spacing must be > 0.0!")

    @classmethod
    def from_fault_data(cls, fault_trace, upper_seismogenic_depth,
                        lower_seismogenic_depth, dip, mesh_spacing):
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
        cls.check_fault_data(fault_trace, upper_seismogenic_depth,
                             lower_seismogenic_depth, dip, mesh_spacing)
        # Loops over points in the top edge, for each point
        # on the top edge compute corresponding point on the bottom edge, then
        # computes equally spaced points between top and bottom points.

        vdist_top = upper_seismogenic_depth
        vdist_bottom = lower_seismogenic_depth

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
        assert 1 not in mesh.shape
        return cls(mesh)
