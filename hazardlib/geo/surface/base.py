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
Module :mod:`openquake.hazardlib.geo.surface.base` implements :class:`BaseSurface`.
"""
import abc

import numpy

from openquake.hazardlib.geo import geodetic


class BaseSurface(object):
    """
    Base class for surface in 3D-space.

    Subclasses must implement :meth:`_create_mesh`, :meth:`get_strike`
    and :meth:`get_dip`, and can override any others just for the sake
    of performance.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._mesh = None

    def get_min_distance(self, mesh):
        """
        Compute and return the minimum distance from the surface to each point
        of ``mesh``. This distance is sometimes called ``Rrup``.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate minimum
            distance to.
        :returns:
            A numpy array of distances in km.

        Base class implementation calls the :meth:`corresponding
        <openquake.hazardlib.geo.mesh.Mesh.get_min_distance>` method of the
        surface's :meth:`mesh <get_mesh>`.

        Subclasses may override this method in order to make use
        of knowledge of a specific surface shape and thus perform
        better.
        """
        return self.get_mesh().get_min_distance(mesh)

    def get_closest_points(self, mesh):
        """
        For each point from ``mesh`` find a closest point belonging to surface.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to find closest points to.
        :returns:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of the same shape as ``mesh`` with
            closest surface's points on respective indices.

        Base class implementation calls the :meth:`corresponding
        <openquake.hazardlib.geo.mesh.Mesh.get_closest_points>` method of the
        surface's :meth:`mesh <get_mesh>`.
        """
        return self.get_mesh().get_closest_points(mesh)

    def get_joyner_boore_distance(self, mesh):
        """
        Compute and return Joyner-Boore (also known as ``Rjb``) distance
        to each point of ``mesh``.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate Joyner-Boore
            distance to.
        :returns:
            Numpy array of closest distances between the projections of surface
            and each point of the ``mesh`` to the earth surface.

        Base class calls surface mesh's method
        :meth:`~openquake.hazardlib.geo.mesh.Mesh.get_joyner_boore_distance`.
        """
        return self.get_mesh().get_joyner_boore_distance(mesh)

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

        Base class calls :func:`openquake.hazardlib.geo.geodetic.distance_to_arc`.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate Rx-distance
            to.
        :returns:
            Numpy array of distances in km.
        """
        top_edge_centroid = self._get_top_edge_centroid()
        return geodetic.distance_to_arc(
            top_edge_centroid.longitude, top_edge_centroid.latitude,
            self.get_strike(), mesh.lons, mesh.lats
        )

    def get_top_edge_depth(self):
        """
        Return minimum depth of surface's top edge.

        :returns:
            Float value, the vertical distance between the earth surface
            and the shallowest point in surface's top edge in km.
        """
        top_edge = self.get_mesh()[0:1]
        if top_edge.depths is None:
            return 0
        else:
            return numpy.min(top_edge.depths)

    def _get_top_edge_centroid(self):
        """
        Return :class:`~openquake.hazardlib.geo.point.Point` representing the surface's
        top edge centroid.
        """
        top_edge = self.get_mesh()[0:1]
        return top_edge.get_middle_point()

    def get_mesh(self):
        """
        Return surface's mesh.

        Uses :meth:`_create_mesh` for creating the mesh for the first time.
        All subsequent calls to :meth:`get_mesh` return the same mesh object.

        .. warning::
            It is required that the mesh is constructed "top-to-bottom".
            That is, the first row of points should be the shallowest.
        """
        if self._mesh is None:
            self._mesh = self._create_mesh()
            assert (self._mesh.depths is None or len(self._mesh.depths) == 1
                    or self._mesh.depths[0][0] < self._mesh.depths[-1][0]), \
                   "the first row of points in the mesh must be the shallowest"
        return self._mesh

    @abc.abstractmethod
    def _create_mesh(self):
        """
        Create and return the mesh of points covering the surface.

        :returns:
            An instance of :class:`openquake.hazardlib.geo.mesh.RectangularMesh`.
        """

    @abc.abstractmethod
    def get_strike(self):
        """
        Return surface's strike as decimal degrees in a range ``[0, 360)``.

        The actual definition of the strike might depend on surface geometry.
        """

    @abc.abstractmethod
    def get_dip(self):
        """
        Return surface's dip as decimal degrees in a range ``(0, 90]``.

        The actual definition of the dip might depend on surface geometry.
        """

    @abc.abstractmethod
    def get_width(self):
        """
        Return surface's width (that is surface extension along the
        dip direction) in km.

        The actual definition depends on the type of surface geometry.
        """
