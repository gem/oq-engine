# encoding: utf-8
"""
Module providing geographical classes and functions.
"""

import numpy
import pyproj
import math

import shapely.geometry

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
            The azimuth, value in a range ``[0, 360)``.
        :rtype:
            float
        """

        forward_azimuth, _, _ = pyproj.Geod(ellps="sphere").inv(
            self.longitude, self.latitude, point.longitude, point.latitude)

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

        Distance is calculated using pythagoras theorem, where the
        hypotenuse is the distance and the other two sides are the
        horizontal distance (great circle distance) and vertical
        distance (depth difference between the two locations).

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
        if other == None:
            return False

        return numpy.allclose([self.longitude, self.latitude],
                [other.longitude, other.latitude], LAT_LON_TOLERANCE) and \
                numpy.allclose(self.depth, other.depth, DEPTH_TOLERANCE)

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
            # if positive -> pointing downwards
            # if negative -> pointing upwards
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

    A line is defined by at least one point. The surface projection
    of a line cannot intersect itself (depth dimension is neglected
    to check if a line intersects itself or not).

    :param points:
        The sequence of points defining this line.
    :type points:
        list of :class:`nhe.geo.Point` instances
    """

    def __init__(self, points):
        self.points = points

        self._remove_duplicates()

        if len(self.points) < 1:
            raise RuntimeError("One point needed to create a line!")

        if self._intersect_itself():
            raise RuntimeError("Line intersects itself!")

    def __eq__(self, other):
        return self.points == other.points

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return len(self.points)

    def _remove_duplicates(self):
        """
        Remove adjacent duplicates.
        """

        last = None
        points = []

        for point in self.points:
            if point != last:
                last = point
                points.append(point)

        self.points = points

    def _intersect_itself(self):
        """
        Check if this line intersects itself.

        :returns:
            True if this line intersects itself, false otherwise.
        :rtype:
            boolean
        """

        if len(self.points) < 2:
            return False

        values = []

        for point in self.points:
            values.append((point.longitude, point.latitude))

        return not shapely.geometry.LineString(values).is_simple

    def resample(self, section_length):
        """
        Resample this line into sections.

        The first point in the resampled line corresponds
        to the first point in the original line.

        Starting from the first point in the original line, a line
        segment is defined as the line connecting the last point in the
        resampled line and the next point in the original line.
        The line segment is then split into sections of length equal to
        ``section_length``. The resampled line is obtained
        by concatenating all sections.

        The number of sections in a line segment is calculated as follows:
        ``round(segment_length / section_length)``.

        Note that the resulting line has a length that is an exact multiple of
        ``section_length``, therefore its length is in general smaller
        or greater (depending on the rounding) than the length
        of the original line.

        For a straight line, the difference between the resulting length
        and the original length is at maximum half of the ``section_length``.
        For a curved line, the difference my be larger,
        because of corners getting cut.

        :param section_length:
            The length of the section, in km.
        :type section_length:
            float
        :returns:
            A new line resampled into sections based on the given length.
        :rtype:
            An instance of :class:`nhe.geo.Line`
        """

        if len(self.points) < 2:
            return Line(self.points)

        resampled_points = []

        # 1. Resample the first section. 2. Loop over the remaining points
        # in the line and resample the remaining sections.
        # 3. Extend the list with the resampled points, except the first one
        # (because it's already contained in the previous set of
        # resampled points).

        resampled_points.extend(self.points[0].equally_spaced_points(
                self.points[1], section_length))

        # Skip the first point, it's already resampled
        for i in range(2, len(self.points)):
            points = resampled_points[-1].equally_spaced_points(
                    self.points[i], section_length)

            resampled_points.extend(points[1:])

        return Line(resampled_points)


def get_longitudal_extent(lon1, lon2):
    """
    Return the distance between two longitude values as an angular measure.
    Parameters represent two longitude values in degrees.

    :return:
        Float, the angle between ``lon1`` and ``lon2`` in degrees. Value
        is positive if ``lon2`` is on the east from ``lon1`` and negative
        otherwise. Absolute value of the result doesn't exceed 180 for
        valid parameters values.

    >>> get_longitudal_extent(10, 20)
    10
    >>> get_longitudal_extent(20, 10)
    -10
    >>> get_longitudal_extent(-10, -15)
    -5
    >>> get_longitudal_extent(-120, 30)
    150
    >>> get_longitudal_extent(-178.3, 177.7)
    -4.0
    >>> get_longitudal_extent(178.3, -177.7)
    4.0
    >>> get_longitudal_extent(95, -180 + 94)
    179
    >>> get_longitudal_extent(95, -180 + 96)
    -179
    """
    extent = lon2 - lon1
    if extent > 180:
        extent = -360 + extent
    elif extent < -180:
        extent = 360 + extent
    return extent


class Polygon(object):
    """
    Polygon objects represent an area on the Earth surface.

    :param points:
        The list of :class:`Point` objects defining the polygon vertices.
        The points are connected by great circle arcs in order of appearance.
        Polygon segment should not cross another polygon segment. At least
        three points must be defined.
    """
    LONGITUDAL_DISCRETIZATION = 1

    def __init__(self, points):
        # TODO: unittest this
        if not len(points) >= 3:
            raise RuntimeError('polygon must have at least 3 points')
        # verify this points define a correct line which doesn't
        # intersect itself (and also get the list of points this
        # is freed of duplicates)
        points = Line(points).points
        # verify this the polygon doesn't intersect itself after
        # being closed
        Line(points[1:] + [points[0]])

        self.lons = numpy.array([point.longitude for point in points])
        self.lats = numpy.array([point.latitude for point in points])
        self.num_points = len(points)

    def discretize(self, mesh_spacing):
        """
        Get a generator of uniformly spaced points inside the polygon area
        with distance of ``mesh_spacing`` km between.
        """
        # cast from km to m
        mesh_spacing *= 1e3

        geod = pyproj.Geod(ellps='sphere')

        # TODO: document this
        resampled_lons = [self.lons[0]]
        resampled_lats = [self.lats[0]]
        for i in xrange(self.num_points):
            next_point = (i + 1) % self.num_points
            lon1, lat1 = self.lons[i], self.lats[i]
            lon2, lat2 = self.lons[next_point], self.lats[next_point]
            longitudal_extent = get_longitudal_extent(lon1, lon2)
            num_segments = longitudal_extent / self.LONGITUDAL_DISCRETIZATION
            if num_segments <= 1:
                resampled_lons.append(lon2)
                resampled_lats.append(lat2)
            else:
                lons, lats = geod._npts(lon1, lat1, lon2, lat2, num_segments)
                resampled_lons.extend(lons)
                resampled_lats.extend(lats)
        resampled_lons = numpy.array(resampled_lons)
        resampled_lats = numpy.array(resampled_lats)

        # find the bounding box of a polygon in a spherical coordinates
        left_lon = numpy.min(resampled_lons)
        right_lon = numpy.max(resampled_lons)
        if get_longitudal_extent(left_lon, right_lon) < 0:
            # the polygon crosses the international date line (meridian 180).
            # the actual left longitude is the lowest positive longitude
            # and right one is the highest negative.
            left_lon = min(lon for lon in resampled_lons if lon > 0)
            right_lon = max(lon for lon in resampled_lons if lon < 0)
        bottom_lat = numpy.min(resampled_lats)
        top_lat = numpy.max(resampled_lats)

        # create a projection this is attached to a polygon.
        proj = pyproj.Proj(proj='stere', lat_0=resampled_lats[0],
                           lon_0=resampled_lons[0])

        # project polygon vertices to the Cartesian space and create
        # a shapely polygon object
        xx, yy = proj(resampled_lons, resampled_lats)
        polygon2d = shapely.geometry.Polygon(zip(xx, yy))

        del xx, yy, resampled_lats, resampled_lons

        # TODO: document this
        latitude = top_lat
        while latitude > bottom_lat:
            longitude = left_lon
            while get_longitudal_extent(longitude, right_lon) > 0:
                x, y = proj(longitude, latitude)
                if polygon2d.contains(shapely.geometry.Point(x, y)):
                    yield Point(longitude, latitude)
                longitude, _, _ = geod.fwd(longitude, latitude,
                                           90, mesh_spacing)
            _, latitude, _ = geod.fwd(left_lon, latitude, 180, mesh_spacing)
