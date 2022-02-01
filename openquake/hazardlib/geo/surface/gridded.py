# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
from numpy import (array, dot, arccos, arctan, arcsin, clip)
from numpy.linalg import norm
from openquake.hazardlib.geo.geodetic import spherical_to_cartesian
from openquake.hazardlib.geo.utils import plane_fit


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
        :returns: (lons, lats) for the 5 points of the bounding box
        """
        # FIXME: implement real boundaries, not bounding box
        xs, ys = zip(*utils.bbox2poly(self.get_bounding_box()))
        return xs, ys

    def get_surface_boundaries_3d(self):
        """
        :returns: (lons, lats, depths) for the 5 points of the bounding box
        """
        # FIXME: implement real boundaries, not bounding box
        xs, ys = zip(*utils.bbox2poly(self.get_bounding_box()))
        return xs, ys, (0, 0, 0, 0, 0)

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
        return self.mesh.depths.min()

    def get_nproj(self):
        """
        params:
        p, n = points on the plane and perpendicular to the plane
        returns:
        n_proj = projection of the vector 'n' on XY plane 
        """
        # import pdb; pdb.set_trace()
        lat = self.mesh.lats.flatten()
        lon = self.mesh.lons.flatten()
        depth = self.mesh.depths.flatten()
        p, n = plane_fit(spherical_to_cartesian(lon, lat, depth))
        nproj = np.zeros(shape=(3,))
        if n[2] < 0:##check if z component is positive so that dip angle lies between 0 and 90
            nproj[0] = -n[0]
            nproj[1] = -n[1]
            nproj[2] = -n[2]
        else:
            nproj = n
        
        return nproj

 
    def get_strike(self):
        """
        params:
            n = unit vector normal to the plane; 3X1 matrix with x, y and z components
            n_proj = projection of the vector 'n' on XY plane 
        returns:    
            the function calculates the strike for gridded surface
        """
        nproj = self.get_nproj()   

        (x, y, z) = (nproj[0], nproj[1], nproj[2])
        if ((x>=0) and (y>0)):
            a = arctan(abs(x)/abs(y))
            strike_deg = 360-np.rad2deg(a)
        elif ((x<0) and (y>=0)):
            a = 3*np.pi*0.5+arctan(abs(y)/abs(x))
            strike_deg = np.rad2deg(a)-90
        elif ((x<=0) and (y<0)):
            a = np.pi+arctan(abs(x)/abs(y))
            strike_deg = np.rad2deg(a)-90
        else:
            a = np.pi*0.5+arctan(abs(y)/abs(x))
            strike_deg = np.rad2deg(a)-90
        return strike_deg

        
    def get_dip(self):
        """
        params:
            n = unit vector normal to the plane; 3X1 matrix with x, y and z components
            n_proj = projection of the vector 'n' on XY plane 
        returns:    
            the function calculates the dip angle for gridded surface
        """

        nproj = self.get_nproj()     

        (x, y, z) = (nproj[0], nproj[1], nproj[2])
        dip_r = (np.pi*0.5)-arcsin(z)
        dip_deg = np.rad2deg(dip_r)

        return dip_deg

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
