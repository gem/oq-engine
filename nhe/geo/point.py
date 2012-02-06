"""
Module :mod:`nhe.geo.point` defines :class:`Point`.
"""
import math

import numpy

from nhe.geo import GEOD


#: Tolerance used for latitude and longitude to identify when two points
#: are equal (it corresponds to about 1 m at the equator).
LAT_LON_TOLERANCE = 1e-5

#: Tolerance used for depth to identify when two points are equal
# (it corresponds to 1 m).
DEPTH_TOLERANCE = 1e-3


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
    def __init__(self, longitude, latitude, depth=0.0):
        if longitude < -180.0 or longitude > 180.0:
            raise RuntimeError("Longitude %.6f outside range!" % longitude)

        if latitude < -90.0 or latitude > 90.0:
            raise RuntimeError("Latitude %.6f outside range!" % latitude)

        self.depth = depth
        self.latitude = latitude
        self.longitude = longitude

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
        # 1e-3 is needed to convert from km to m
        longitude, latitude, _ = GEOD.fwd(self.longitude, self.latitude,
                                          azimuth, horizontal_distance * 1e3)
        return Point(longitude, latitude, self.depth + vertical_increment)

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
        forward_azimuth, _, _ = GEOD.inv(self.longitude, self.latitude,
                                         point.longitude, point.latitude)
        if forward_azimuth < 0:
            return 360 + forward_azimuth

        return forward_azimuth

    def horizontal_distance(self, point):
        """
        Compute the horizontal distance (great circle distance, in km) between
        this point and the given point.

        :param point:
            Destination point.
        :type point:
            Instance of :class:`Point`
        :returns:
            The horizontal distance.
        :rtype:
            float
        """
        _, _, horizontal_distance = GEOD.inv(self.longitude, self.latitude,
                                             point.longitude, point.latitude)
        # 1e-3 is needed to convert from m to km
        return horizontal_distance * 1e-3

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
        vertical_distance = point.depth - self.depth
        horizontal_distance = self.horizontal_distance(point)
        return math.sqrt(horizontal_distance ** 2 + vertical_distance ** 2)

    def __str__(self):
        """
        >>> str(Point(1, 2, 3))
        '<Latitude=2.000000, Longitude=1.000000, Depth=3.0000>'
        >>> str(Point(1.0 / 3.0, -39.999999999, 1.6666666666))
        '<Latitude=-40.000000, Longitude=0.333333, Depth=1.6667>'
        """
        return "<Latitude=%.6f, Longitude=%.6f, Depth=%.4f>" % (
                self.latitude, self.longitude, self.depth)

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
        >>> Point(1e-5, 1e-5) == Point(0, 0)
        True
        >>> Point(0, 0, 1) == Point(0, 0, 0)
        False
        >>> Point(4, 5, 1e-3) == Point(4, 5, 0)
        True
        """
        if other == None:
            return False

        coord1 = [self.longitude, self.latitude]
        coord2 = [other.longitude, other.latitude]
        # need to disable relative comparison to make __eq__() depend only
        # on the distance between points and not on distance to equator
        # or Greenwich meridian.
        if not numpy.allclose(coord1, coord2, atol=LAT_LON_TOLERANCE, rtol=0):
            return False
        if not abs(self.depth - other.depth) <= DEPTH_TOLERANCE:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

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
        points = [self]

        if self == point:
            return points

        total_distance = self.distance(point)
        horizontal_distance = self.horizontal_distance(point)
        azimuth = self.azimuth(point)

        bearing_angle = math.acos(horizontal_distance / total_distance)

        vertical_increment_step = distance * math.sin(bearing_angle)
        horizontal_increment_step = distance * math.cos(bearing_angle)

        if self.depth > point.depth:
            # the depth is decreasing
            vertical_increment_step *= -1

        locations = int(round(total_distance / distance) + 1)

        horizontal_increment = vertical_increment = 0
        for _ in xrange(1, locations):
            horizontal_increment += horizontal_increment_step
            vertical_increment += vertical_increment_step
            points.append(self.point_at(
                    horizontal_increment, vertical_increment, azimuth))

        return points
