# encoding: utf-8
"""
Module providing geographical classes and functions.
"""

import numpy
import pyproj
import math

# Tolerance used for latitude and longitude to identify
# when two sites are equal (it corresponds to about 1 m at the equator)
LAT_LON_TOLERANCE = 1e-5

# Tolerance used for depth to identify
# when two sites are equal (it corresponds to 1 m)
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
            raise RuntimeError("Longitude %.13f outside range!" % longitude)

        if latitude < -90.0 or latitude > 90.0:
            raise RuntimeError("Latitude %.13f outside range!" % latitude)

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
            Instance of :class:`nhe.geo.Point`
        """

        # 1e-3 is needed to convert from km to m
        longitude, latitude, _ = pyproj.Geod(ellps="sphere").fwd(
            self.longitude, self.latitude, azimuth, horizontal_distance * 1e3)

        return Point(longitude, latitude, self.depth + vertical_increment)

    def azimuth(self, point):
        """
        Compute the azimuth (in decimal degrees) between this point
        and the given point.

        :param point:
            Destination point.
        :type point:
            Instance of :class:`nhe.geo.Point`
        :returns:
            The azimuth.
        :rtype:
            float
        """

        forward_azimuth, _, _ = pyproj.Geod(ellps="sphere").inv(
            self.longitude, self.latitude, point.longitude, point.latitude)

        return forward_azimuth

    def horizontal_distance(self, point):
        """
        Compute the horizontal distance (great circle distance, in km) between
        this point and the given point.

        :param point:
            Destination point.
        :type point:
            Instance of :class:`nhe.geo.Point`
        :returns:
            The horizontal distance.
        :rtype:
            float
        """

        _, _, horizontal_distance = pyproj.Geod(ellps="sphere").inv(
            self.longitude, self.latitude, point.longitude, point.latitude)
        
        # 1e-3 is needed to convert from m to km
        return horizontal_distance * 1e-3 

    def distance(self, point):
        """
        Compute the distance (in km) between this point and the given point.

        Distance is calculated using pythagoras theorem, where the hypotenuse is
        the distance and the other two sides are the horizontal distance
        (great circle distance) and vertical distance (depth difference between
        the two locations).

        :param point:
            Destination point.
        :type point:
            Instance of :class:`nhe.geo.Point`
        :returns:
            The distance.
        :rtype:
            float
        """

        vertical_distance = point.depth - self.depth
        horizontal_distance = self.horizontal_distance(point)
        return math.sqrt(horizontal_distance ** 2 + vertical_distance ** 2)

    def __str__(self):
        return "<Latitude=%.13f, Longitude=%.13f, Depth=%.13f>" % (
                self.latitude, self.longitude, self.depth)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return numpy.allclose([self.longitude, self.latitude], [other.longitude,
                other.latitude], LAT_LON_TOLERANCE) and numpy.allclose(
                self.depth, other.depth, DEPTH_TOLERANCE)

    def __ne__(self, other):
        return not self.__eq__(other)

    def equally_spaced_points(self, point, distance):
        """
        Compute the set of points equally spaced between this point
        and the given point.

        :param point:
            Destination point.
        :type point:
            Instance of :class:`nhe.geo.Point`
        :param distance:
            Distance between points (in km).
        :type distance:
            float
        :returns:
            The list of equally spaced points.
        :rtype:
            list of :class:`nhe.geo.Point` instances
        """

        if self == point:
            return [self]

        points = []
        points.append(self)

        total_distance = self.distance(point)
        horizontal_distance = self.horizontal_distance(point)
        azimuth = self.azimuth(point)

        bearing_angle = math.asin(horizontal_distance / total_distance)
        sign = 1

        if point.depth != self.depth:
            # if positive -> pointing downwards, if negative -> pointing upwards
            sign = (point.depth - self.depth) / math.fabs(
                    point.depth - self.depth)

        vertical_increment = sign * distance * math.cos(bearing_angle)
        horizontal_increment = distance * math.sin(bearing_angle)

        locations = int(round(total_distance / distance) + 1)

        for _ in xrange(1, locations):
            last = points[-1]
            points.append(last.point_at(
                    horizontal_increment, vertical_increment, azimuth))

        return points


class Line(object):
    """
    This class represents a geographical line, which is basically
    a sequence of geographical points.

    :param points:
        The sequence of points definining this line.
    :type points:
        list of :class:`nhe.geo.Point` instances
    """

    def __init__(self, points):
        if len(points) < 2:
            raise RuntimeError("Two points are needed to create a line!")

        if len(points) == 2 and points[0] == points[1]:
            raise RuntimeError(
                "Two different points are needed to create a line!")

# TODO(ac): Check that the line does not intersect itself
        self._points = points

    def __eq__(self, other):
        return self.points == other.points

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def points(self):
        """
        Return the sequence of points defined in this line.
        
        :returns:
            The sequence of points defined in this line.
        :rtype:
            list of :class:`nhe.geo.Point` instances
        """
# TODO(ac): Should we return a copy of the points?
        return self._points

    def resample(self, section_length):
        """
        Resample this line into sections.

        :param section_length:
            The length of the section.
        :type section_length:
            float
        :returns:
            A new line resampled into sections based on the given length.
        :rtype:
            An instance of :class:`nhe.geo.Line`
        """

        resampled_points = []

        # 1. Resample the first section. 2. Loop over the remaining points
        # in the fault trace and resample the remaining sections.
        # 3. Extend the list with the resampled points, except the first one
        # (because it's already contained in the previous set of
        # resampled points).

        resampled_points.extend(self._points[0].equally_spaced_points(
                self._points[1], section_length))

        # Skip the first point, it's already resampled
        for i in range(2, len(self._points)):
            points = resampled_points[-1].equally_spaced_points(
                    self._points[i], section_length)

            resampled_points.extend(points[1: ])

        return Line(resampled_points)
