"""
Module :mod:`nhe.geo.surface.base` implements :class:`BaseSurface`.
"""
import abc

import math

from nhe.geo import _utils as geo_utils


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

    def get_min_distance(self, point):
        """
        Compute and return the minimum distance from the surface to ``point``.
        This distance is sometimes called ``Rrup``.

        :returns:
            Distance in km.

        Base class implementation calls the :meth:`corresponding
        <nhe.geo.mesh.Mesh.get_min_distance>` method of the
        surface's :meth:`mesh <get_mesh>`.

        Subclasses may override this method in order to make use
        of knowledge of a specific surface shape and thus perform
        better.
        """
        return self.get_mesh().get_min_distance(point)

    def get_joyner_boore_distance(self, point):
        """
        Compute and return Joyner-Boore (also known as ``Rjb``) distance
        to ``point``.

        :returns:
            The closest distance between the projections of the point
            and the surface to the earth surface.

        Base class calls surface mesh's method
        :meth:`~nhe.geo.mesh.RectangularMesh.get_joyner_boore_distance`.
        """
        return self.get_mesh().get_joyner_boore_distance(point)

    def get_rx_distance(self, point):
        """
        Compute distance between ``point`` and surface's great circle arc.

        Distance is measured perpendicular to the rupture strike, from
        the surface projection of the updip edge of the rupture, with
        the down dip direction being positive (this distance is usually
        called ``Rx``).

        In other words, is the horizontal distance to top edge of rupture
        measured perpendicular to the strike. Values on the hanging wall
        are positive, values on the footwall are negative.

        :returns:
            Distance in km.

        Base class implementation gives reasonable precision (mistake
        of less than 1 km) up to the distance of six hundred kilometers
        between the point and the surface.
        """
        # Here we find the distance (in linear units) between the target
        # point and the top edge centroid, an angle between the surface
        # strike and azimuth from top edge centroid to the target point
        # and treat those values as ones in a Cartesian space -- find
        # the projection of vector directed from top edge centroid
        # pointing to the target point to the line perpendicular to the
        # surface plane. Better way would be using spherical law of cosines
        # but that would require expressing distances in angular units.
        top_edge_centroid = self._get_top_edge_centroid()
        azimuth_to_target, _, distance_to_target = geo_utils.GEOD.inv(
            top_edge_centroid.longitude, top_edge_centroid.latitude,
            point.longitude, point.latitude
        )
        azimuth = azimuth_to_target - self.get_strike()
        if azimuth <= -180:
            azimuth += 360
        # distance to target is returned in meters, so multiply it by 0.001
        return math.sin(math.radians(azimuth)) * distance_to_target * 1e-3

    def _get_top_edge_centroid(self):
        """
        Return :class:`~nhe.geo.point.Point` representing the surface's
        top edge centroid.

        .. warning::
            Base surface class implementation requires the :meth:`mesh
            <get_mesh>` to be constructed "top-to-bottom". That's it,
            the first row of points should be the shallowest.
        """
        mesh = self.get_mesh()
        assert len(mesh.depths) == 1 or mesh.depths[0][0] < mesh.depths[-1][0]
        top_edge = mesh[0:1]
        return top_edge.get_middle_point()

    def get_mesh(self):
        """
        Return surface's mesh.

        Uses :meth:`_create_mesh` for creating the mesh for the first time.
        All subsequent calls to :meth:`get_mesh` return the same mesh object.
        """
        if self._mesh is None:
            self._mesh = self._create_mesh()
        return self._mesh

    @abc.abstractmethod
    def _create_mesh(self):
        """
        Create and return the mesh of points covering the surface.

        :returns:
            An instance of :class:`nhe.geo.mesh.RectangularMesh`.
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
