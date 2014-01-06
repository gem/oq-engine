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
Module :mod:`openquake.hazardlib.geo.surface.base` implements
:class:`BaseSurface` and :class:`BaseQuadrilateralSurface`.
"""
import abc

import numpy

from openquake.hazardlib.geo import geodetic, utils, Point


class BaseSurface(object):
    """
    Base class for a surface in 3D-space.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_min_distance(self, mesh):
        """
        Compute and return the minimum distance from the surface to each point
        of ``mesh``. This distance is sometimes called ``Rrup``.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate
            minimum distance to.
        :returns:
            A numpy array of distances in km.
        """

    @abc.abstractmethod
    def get_closest_points(self, mesh):
        """
        For each point from ``mesh`` find a closest point belonging to surface.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to find
            closest points to.
        :returns:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of the same shape as
            ``mesh`` with closest surface's points on respective indices.
        """

    @abc.abstractmethod
    def get_joyner_boore_distance(self, mesh):
        """
        Compute and return Joyner-Boore (also known as ``Rjb``) distance
        to each point of ``mesh``.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate
            Joyner-Boore distance to.
        :returns:
            Numpy array of closest distances between the projections of surface
            and each point of the ``mesh`` to the earth surface.
        """

    @abc.abstractmethod
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

    @abc.abstractmethod
    def get_top_edge_depth(self):
        """
        Compute minimum depth of surface's top edge.

        :returns:
            Float value, the vertical distance between the earth surface
            and the shallowest point in surface's top edge in km.
        """

    @abc.abstractmethod
    def get_strike(self):
        """
        Compute surface's strike as decimal degrees in a range ``[0, 360)``.

        The actual definition of the strike might depend on surface geometry.

        :returns:
            Float value, the azimuth (in degrees) of the surface top edge
        """

    @abc.abstractmethod
    def get_dip(self):
        """
        Compute surface's dip as decimal degrees in a range ``(0, 90]``.

        The actual definition of the dip might depend on surface geometry.

        :returns:
            Float value, the inclination (in degrees) of the surface with
            respect to the Earth surface
        """

    @abc.abstractmethod
    def get_width(self):
        """
        Compute surface's width (that is surface extension along the
        dip direction) in km.

        The actual definition depends on the type of surface geometry.

        :returns:
            Float value, the surface width
        """

    @abc.abstractmethod
    def get_area(self):
        """
        Compute surface's area in squared km.

        :returns:
            Float value, the surface area
        """

    @abc.abstractmethod
    def get_bounding_box(self):
        """
        Compute surface geographical bounding box.

        :return:
            A tuple of four items. These items represent western, eastern,
            northern and southern borders of the bounding box respectively.
            Values are floats in decimal degrees.
        """

    @abc.abstractmethod
    def get_middle_point(self):
        """
        Compute coordinates of surface middle point.

        The actual definition of ``middle point`` depends on the type of
        surface geometry.

        :return:
            instance of :class:`openquake.hazardlib.geo.point.Point`
            representing surface middle point.
        """


class BaseQuadrilateralSurface(BaseSurface):
    """
    Base class for a quadrilateral surface in 3D-space.

    Subclasses must implement :meth:`_create_mesh`, and superclass methods
    :meth:`get_strike() <.base.BaseSurface.get_strike>`,
    :meth:`get_dip() <.base.BaseSurface.get_dip>` and
    :meth:`get_width() <.base.BaseSurface.get_width>`,
    and can override any others just for the sake of performance
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._mesh = None

    def get_min_distance(self, mesh):
        """
        See :meth:`superclass method
        <.base.BaseSurface.get_min_distance>`
        for spec of input and result values.

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
        See :meth:`superclass method
        <.base.BaseSurface.get_closest_points>`
        for spec of input and result values.

        Base class implementation calls the :meth:`corresponding
        <openquake.hazardlib.geo.mesh.Mesh.get_closest_points>` method of the
        surface's :meth:`mesh <get_mesh>`.
        """
        return self.get_mesh().get_closest_points(mesh)

    def get_joyner_boore_distance(self, mesh):
        """
        See :meth:`superclass method
        <.base.BaseSurface.get_joyner_boore_distance>`
        for spec of input and result values.

        Base class calls surface mesh's method
        :meth:`~openquake.hazardlib.geo.mesh.Mesh.get_joyner_boore_distance`.
        """
        return self.get_mesh().get_joyner_boore_distance(mesh)

    def get_rx_distance(self, mesh):
        """
        See :meth:`superclass method
        <.base.BaseSurface.get_rx_distance>`
        for spec of input and result values.

        The method extracts the top edge of the surface. For each point in mesh,
        it then computes the Rx distance to each segment the top edge is made
        of. The calculation is done by calling the function
        :func:`openquake.hazardlib.geo.geodetic.distance_to_arc`. The final Rx
        distance matrix is then constructed by taking, for each point in mesh,
        the minimum Rx distance value computed.
        """
        top_edge = self.get_mesh()[0:1]

        dists = []
        for i in range(top_edge.lons.shape[1] - 1):
            p1 = Point(
                top_edge.lons[0, i], top_edge.lats[0, i], top_edge.depths[0, i]
            )
            p2 = Point(
                top_edge.lons[0, i + 1], top_edge.lats[0, i + 1],
                top_edge.depths[0, i + 1]
            )
            azimuth = p1.azimuth(p2)
            dists.append(
                geodetic.distance_to_arc(
                    p1.longitude, p1.latitude, azimuth, mesh.lons, mesh.lats
                )
            )
        dists = numpy.array(dists)

        return numpy.min(dists, axis=0)

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
        Return :class:`~openquake.hazardlib.geo.point.Point` representing the
        surface's top edge centroid.
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
            assert (
                self._mesh.depths is None or len(self._mesh.depths) == 1
                or self._mesh.depths[0][0] < self._mesh.depths[-1][0]
            ), "the first row of points in the mesh must be the shallowest"
        return self._mesh

    def get_area(self):
        """
        Compute area as the sum of the mesh cells area values.
        """
        mesh = self.get_mesh()
        _, _, _, area = mesh.get_cell_dimensions()

        return numpy.sum(area)

    def get_bounding_box(self):
        """
        Compute surface bounding box from surface mesh representation. That is
        extract longitudes and latitudes of mesh points and calls:
        :meth:`openquake.hazardlib.geo.utils.get_spherical_bounding_box`

        :return:
            A tuple of four items. These items represent western, eastern,
            northern and southern borders of the bounding box respectively.
            Values are floats in decimal degrees.
        """
        mesh = self.get_mesh()

        return utils.get_spherical_bounding_box(mesh.lons, mesh.lats)

    def get_middle_point(self):
        """
        Compute middle point from surface mesh representation. Calls
        :meth:`openquake.hazardlib.geo.mesh.RectangularMesh.get_middle_point`
        """
        mesh = self.get_mesh()

        return mesh.get_middle_point()

    @abc.abstractmethod
    def _create_mesh(self):
        """
        Create and return the mesh of points covering the surface.

        :returns:
            An instance of
            :class:`openquake.hazardlib.geo.mesh.RectangularMesh`.
        """
