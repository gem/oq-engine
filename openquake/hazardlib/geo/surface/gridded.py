# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.surface.gridded` defines
:class:`GriddedSurface`.
"""
import numpy as np

from openquake.baselib.node import Node
from openquake.hazardlib.geo import utils
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.mesh import Mesh


class GriddedSurface(BaseSurface):
    """
    Gridded surface defined by an unstructured cloud of points. This surface
    type is required for a proper implementation of some subduction interface
    surfaces included int the Japan 2012 model.

    Note that currently we support only one rupture-site typology i.e. since
    this the only one that can be unambiguosly computed.

    :param mesh:
        An unstructured mesh of points ideally representing a rupture surface.
        Must be an instance of :class:`~openquake.hazardlib.geo.mesh.Mesh`
    """
    @property
    def surface_nodes(self):
        """
        :param points: a list of Point objects
        :returns: a Node of kind 'griddedSurface'
        """
        line = []
        for point in self.mesh:
            line.append(point.longitude)
            line.append(point.latitude)
            line.append(point.depth)
        return [Node('griddedSurface', nodes=[Node('gml:posList', {}, line)])]

    @classmethod
    def from_points_list(cls, points):
        """
        Create a gridded surface from a list of points.

        :parameter points:
            A list of :class:`~openquake.hazardlib.geo.Point`
        :returns:
            An instance of
            :class:`~openquake.hazardlib.geo.surface.gridded.GriddedSurface`
        """
        return cls(Mesh.from_points_list(points))

    def get_bounding_box(self):
        """
        Compute surface geographical bounding box.

        :return:
            A tuple of four items. These items represent western, eastern,
            northern and southern borders of the bounding box respectively.
            Values are floats in decimal degrees.
        """
        return utils.get_spherical_bounding_box(self.mesh.lons, self.mesh.lats)

    def get_surface_boundaries(self):
        """
        :returns: (min_max lons, min_max lats)
        """
        min_lon, min_lat, max_lon, max_lat = self.get_bounding_box()
        return [[min_lon, max_lon]], [[min_lat, max_lat]]

    def get_rx_distance(self, mesh):
        """
        Compute distance between each point of mesh and surface's great circle
        arc.

        Distance is measured perpendicular to the rupture strike, from
        the surface projection of the updip edge of the rupture, with
        the down dip direction being positive (this distance is usually
        called ``Rx``).

        In other words, is the horizontal distance to top edge of rupture
        measured perpendicular to the strike. Values on the hanging wall
        are positive, values on the footwall are negative.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate
            Rx-distance to.
        :returns:
            Numpy array of distances in km.
        """
        raise NotImplementedError('GriddedSurface')

    def get_top_edge_depth(self):
        """
        Compute minimum depth of surface's top edge.

        :returns:
            Float value, the vertical distance between the earth surface
            and the shallowest point in surface's top edge in km.
        """
        raise NotImplementedError('GriddedSurface')

    def get_strike(self):
        """
        Compute surface's strike as decimal degrees in a range ``[0, 360)``.

        The actual definition of the strike might depend on surface geometry.

        :returns:
            numpy.nan, not available for this kind of surface (yet)
        """
        return np.nan

    def get_dip(self):
        """
        Compute surface's dip as decimal degrees in a range ``(0, 90]``.

        The actual definition of the dip might depend on surface geometry.

        :returns:
            numpy.nan, not available for this kind of surface (yet)
        """
        return np.nan

    def get_width(self):
        """
        Compute surface's width (that is surface extension along the
        dip direction) in km.

        The actual definition depends on the type of surface geometry.

        :returns:
            Float value, the surface width
        """
        raise NotImplementedError('GriddedSurface')

    def get_area(self):
        """
        Compute surface's area in squared km.

        :returns:
            Float value, the surface area
        """
        raise NotImplementedError('GriddedSurface')

    def get_middle_point(self):
        """
        Compute coordinates of surface middle point.

        The actual definition of ``middle point`` depends on the type of
        surface geometry.

        :return:
            instance of :class:`openquake.hazardlib.geo.point.Point`
            representing surface middle point.
        """
        lons = self.mesh.lons.squeeze()
        lats = self.mesh.lats.squeeze()
        depths = self.mesh.depths.squeeze()
        lon_bar = lons.mean()
        lat_bar = lats.mean()
        idx = np.argmin((lons - lon_bar)**2 + (lats - lat_bar)**2)
        return Point(lons[idx], lats[idx], depths[idx])

    def get_ry0_distance(self, mesh):
        """
        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points
        """
        raise NotImplementedError('GriddedSurface')
