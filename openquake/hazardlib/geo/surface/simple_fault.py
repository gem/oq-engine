# The Hazard Library
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
Module :mod:`openquake.hazardlib.geo.surface.simple_fault` defines
:class:`SimpleFaultSurface`.
"""
import math

import numpy

from openquake.hazardlib.geo.surface.base import BaseQuadrilateralSurface
from openquake.hazardlib.geo.mesh import Mesh, RectangularMesh
from openquake.hazardlib.geo import utils as geo_utils


class SimpleFaultSurface(BaseQuadrilateralSurface):
    """
    Represent a fault surface as regular (uniformly spaced) 3D mesh of points.

    :param mesh:
        Instance of :class:`~openquake.hazardlib.geo.mesh.RectangularMesh`
        representing surface geometry.

    Another way to construct the surface object is to call
    :meth:`from_fault_data`.
    """
    def __init__(self, mesh):
        super(SimpleFaultSurface, self).__init__()
        self.mesh = mesh
        assert not 1 in self.mesh.shape, (
            "Mesh must have at least 2 nodes along both length and width."
        )
        self.strike = self.dip = None

    def _create_mesh(self):
        """
        Return a mesh provided to object's constructor.
        """
        return self.mesh

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
            top_row = self.get_mesh()[0:2]
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
        if not fault_trace.on_surface():
            raise ValueError("the fault trace must be defined on the surface")
        tlats = [point.latitude for point in fault_trace.points]
        tlons = [point.longitude for point in fault_trace.points]
        if geo_utils.line_intersects_itself(tlons, tlats):
            raise ValueError("fault trace intersects itself")
        if not 0.0 < dip <= 90.0:
            raise ValueError("dip must be between 0.0 and 90.0")
        if not lower_seismogenic_depth > upper_seismogenic_depth:
            raise ValueError("lower seismogenic depth must be greater than "
                             "upper seismogenic depth")
        if not upper_seismogenic_depth >= 0.0:
            raise ValueError("upper seismo depth must be non-negative")
        if not mesh_spacing > 0.0:
            raise ValueError("mesh spacing must be positive")

    @classmethod
    def from_fault_data(cls, fault_trace, upper_seismogenic_depth,
                        lower_seismogenic_depth, dip, mesh_spacing):
        """
        Create and return a fault surface using fault source data.

        :param openquake.hazardlib.geo.line.Line fault_trace:
            Geographical line representing the intersection between
            the fault surface and the earth surface.
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
        assert 1 not in mesh.shape, (
            "Mesh must have at least 2 nodes along both length and width."
            " Possible cause: Mesh spacing could be too large with respect to"
            " the fault length and width."
        )
        return cls(mesh)

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
        left_column = self.get_mesh()[:, 0:2]
        return left_column.get_mean_width()
