# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.point` defines :class:`Point`.
"""
import numpy
import shapely.geometry

from openquake.hazardlib.geo import geodetic
from openquake.hazardlib.geo import utils as geo_utils


class Point(object):
    """
    This class represents a geographical point in terms of
    longitude, latitude, and depth (with respect to the Earth surface).

    :param longitude:
        Point longitude, in decimal degrees.
    :type longitude:
        float
    :param latitude:
        Point latitude, in decimal degrees.
    :type latitude:
        float
    :param depth:
        Point depth (default to 0.0), in km. Depth > 0 indicates a point
        below the earth surface, and depth < 0 above the earth surface.
    :type depth:
        float
    """
    #: The distance between two points for them to be considered equal,
    #: in km.
    EQUALITY_DISTANCE = 1e-3

    def __init__(self, longitude, latitude, depth=0.0):
        if not depth < geodetic.EARTH_RADIUS:
            raise ValueError("The depth must be less than "
                             "the Earth's radius (6371.0 km)")

        if not depth > geodetic.EARTH_ELEVATION:
            raise ValueError("The depth must be greater than the maximum "
                             "elevation on Earth's surface (-8.848 km)")

        if not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude %.6f outside range" % longitude)

        if not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude %.6f outside range" % latitude)

        self.depth = float(depth)
        self.latitude = float(latitude)
        self.longitude = float(longitude)

    @property
    def x(self):
        """Alias for .longitude"""
        return self.longitude

    @property
    def y(self):
        """Alias for .latitude"""
        return self.latitude

    @property
    def z(self):
        """Alias for .depth"""
        return self.depth

    @property
    def wkt2d(self):
        """
        Generate WKT (Well-Known Text) to represent this point in 2 dimensions
        (ignoring depth).
        """
        return 'POINT(%s %s)' % (self.longitude, self.latitude)

    def round(self, digits=5):
        """
        :returns: a new Point with lon, lat, depth rounded to 5 digits
        """
        lon = round(self.longitude, digits)
        lat = round(self.latitude, digits)
        dep = round(self.depth, digits)
        return Point(lon, lat, dep)

    def point_at(self, horizontal_distance, vertical_increment, azimuth):
        """
        Compute the point with given horizontal, vertical distances
        and azimuth from this point.

        :param horizontal_distance:
            Horizontal distance, in km.
        :type horizontal_distance:
            float
        :param vertical_increment:
            Vertical increment, in km. When positive, the new point
            has a greater depth. When negative, the new point
            has a smaller depth.
        :type vertical_increment:
            float
        :type azimuth:
            Azimuth, in decimal degrees.
        :type azimuth:
            float
        :returns:
            The point at the given distances.
        :rtype:
            Instance of :class:`Point`
        """
        lon, lat = geodetic.point_at(self.longitude, self.latitude,
                                     azimuth, horizontal_distance)
        return Point(lon, lat, self.depth + vertical_increment)

    def azimuth(self, point):
        """
        Compute the azimuth (in decimal degrees) between this point
        and the given point.

        :param point:
            Destination point.
        :type point:
            Instance of :class:`Point`
        :returns:
            The azimuth, value in a range ``[0, 360)``.
        :rtype:
            float
        """
        return geodetic.azimuth(self.longitude, self.latitude,
                                point.longitude, point.latitude)

    def distance(self, point):
        """
        Compute the distance (in km) between this point and the given point.

        Distance is calculated using pythagoras theorem, where the
        hypotenuse is the distance and the other two sides are the
        horizontal distance (great circle distance) and vertical
        distance (depth difference between the two locations).

        :param point:
            Destination point.
        :type point:
            Instance of :class:`Point`
        :returns:
            The distance.
        :rtype:
            float
        """
        return geodetic.distance(self.longitude, self.latitude, self.depth,
                                 point.longitude, point.latitude, point.depth)

    def distance_to_mesh(self, mesh, with_depths=True):
        """
        Compute distance (in km) between this point and each point of ``mesh``.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate
            distance to.
        :param with_depths:
            If ``True`` (by default), distance is calculated between actual
            point and the mesh, geodetic distance of projections is combined
            with vertical distance (difference of depths). If this is set
            to ``False``, only geodetic distance between projections
            is calculated.
        :returns:
            Numpy array of floats of the same shape as ``mesh`` with distance
            values in km in respective indices.
        """
        if with_depths:
            if mesh.depths is None:
                mesh_depths = numpy.zeros_like(mesh.lons)
            else:
                mesh_depths = mesh.depths
            return geodetic.distance(self.longitude, self.latitude, self.depth,
                                     mesh.lons, mesh.lats, mesh_depths)
        else:
            return geodetic.geodetic_distance(self.longitude, self.latitude,
                                              mesh.lons, mesh.lats)

    def __str__(self):
        """
        >>> str(Point(1, 2, 3))
        '<Latitude=2.000000, Longitude=1.000000, Depth=3.0000>'
        >>> str(Point(1.0 / 3.0, -39.999999999, 1.6666666666))
        '<Latitude=-40.000000, Longitude=0.333333, Depth=1.6667>'
        """
        return "<Latitude=%.6f, Longitude=%.6f, Depth=%.4f>" % (
            self.latitude, self.longitude, self.depth
        )

    def __repr__(self):
        """
        >>> str(Point(1, 2, 3)) == repr(Point(1, 2, 3))
        True
        """
        return self.__str__()

    def __eq__(self, other):
        """
        >>> Point(1e-4, 1e-4) == Point(0, 0)
        False
        >>> Point(1e-6, 1e-6) == Point(0, 0)
        True
        >>> Point(0, 0, 1) == Point(0, 0, 0)
        False
        >>> Point(4, 5, 1e-3) == Point(4, 5, 0)
        True
        >>> Point(-180 + 1e-7, 0) == Point(180 - 1e-7, 0)
        True
        """
        if other is None:
            return False
        return abs(self.distance(other)) <= self.EQUALITY_DISTANCE

    def __ne__(self, other):
        return not self.__eq__(other)

    def on_surface(self):
        """
        Check if this point is defined on the surface (depth is 0.0).

        :returns bool:
            True if this point is on the surface, false otherwise.
        """
        return self.depth == 0.0

    def equally_spaced_points(self, point, distance):
        """
        Compute the set of points equally spaced between this point
        and the given point.

        :param point:
            Destination point.
        :type point:
            Instance of :class:`Point`
        :param distance:
            Distance between points (in km).
        :type distance:
            float
        :returns:
            The list of equally spaced points.
        :rtype:
            list of :class:`Point` instances
        """
        lons, lats, depths = geodetic.intervals_between(
            self.longitude, self.latitude, self.depth,
            point.longitude, point.latitude, point.depth,
            distance)
        return [Point(lons[i], lats[i], depths[i]) for i in range(len(lons))]

    def to_polygon(self, radius):
        """
        Create a circular polygon with specified radius centered in the point.

        :param radius:
            Required radius of a new polygon, in km.
        :returns:
            Instance of :class:`~openquake.hazardlib.geo.polygon.Polygon` that
            approximates a circle around the point with specified radius.
        """
        assert radius > 0
        # avoid circular imports
        from openquake.hazardlib.geo.polygon import Polygon

        # get a projection that is centered in the point
        proj = geo_utils.OrthographicProjection(
            self.longitude, self.longitude, self.latitude, self.latitude)

        # create a shapely object from a projected point coordinates,
        # which are supposedly (0, 0)
        point = shapely.geometry.Point(*proj(self.longitude, self.latitude))

        # extend the point to a shapely polygon using buffer()
        # and create openquake.hazardlib.geo.polygon.Polygon object from it
        return Polygon._from_2d(point.buffer(radius), proj)

    def closer_than(self, mesh, radius):
        """
        Check for proximity of points in the ``mesh``.

        :param mesh:
            :class:`openquake.hazardlib.geo.mesh.Mesh` instance.
        :param radius:
            Proximity measure in km.
        :returns:
            Numpy array of boolean values in the same shape as the mesh
            coordinate arrays with ``True`` on indexes of points that
            are not further than ``radius`` km from this point. Function
            :func:`~openquake.hazardlib.geo.geodetic.distance` is used to
            calculate distances to points of the mesh. Points of the mesh that
            lie exactly ``radius`` km away from this point also have
            ``True`` in their indices.
        """
        dists = geodetic.distance(self.longitude, self.latitude, self.depth,
                                  mesh.lons, mesh.lats,
                                  0 if mesh.depths is None else mesh.depths)
        return dists <= radius

    @classmethod
    def from_vector(cls, vector):
        """
        Create a point object from a 3d vector in Cartesian space.

        :param vector:
            Tuple, list or numpy array of three float numbers representing
            point coordinates in Cartesian 3d space.
        :returns:
            A :class:`Point` object created from those coordinates.
        """
        return cls(*geo_utils.cartesian_to_spherical(vector))
