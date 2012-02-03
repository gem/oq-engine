# encoding: utf-8
"""
Module providing geographical classes and functions.
"""

import numpy
import pyproj
import math

import shapely.geometry

#: Tolerance used for latitude and longitude to identify
#: when two sites are equal (it corresponds to about 1 m at the equator)
LAT_LON_TOLERANCE = 1e-5

#: Tolerance used for depth to identify
#: when two sites are equal (it corresponds to 1 m)
DEPTH_TOLERANCE = 1e-3

#: Geod object to be used whenever we need to deal with
#: spherical coordinates.
GEOD = pyproj.Geod(ellps='sphere')


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
            raise RuntimeError("Longitude %.5f outside range!" % longitude)

        if latitude < -90.0 or latitude > 90.0:
            raise RuntimeError("Latitude %.5f outside range!" % latitude)

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
            Instance of :class:`nhe.geo.Point`
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
            Instance of :class:`nhe.geo.Point`
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
        """
        >>> str(Point(1, 2, 3))
        '<Latitude=2.00000, Longitude=1.00000, Depth=3.000>'
        >>> str(Point(1.0 / 3.0, -39.999999999, 1.6666666666))
        '<Latitude=-40.00000, Longitude=0.33333, Depth=1.667>'
        """
        return "<Latitude=%.5f, Longitude=%.5f, Depth=%.3f>" % (
                self.latitude, self.longitude, self.depth)

    def __repr__(self):
        """
        >>> str(Point(1, 2, 3)) == repr(Point(1, 2, 3))
        True
        """
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
        self.points = _clean_points(points)

        if len(self.points) < 1:
            raise RuntimeError("One point needed to create a line!")

        lats = [point.latitude for point in self.points]
        lons = [point.longitude for point in self.points]
        if _line_intersects_itself(lons, lats):
            raise RuntimeError("Line intersects itself!")

    def __eq__(self, other):
        """
        >>> points = [Point(1, 2), Point(3, 4)]; Line(points) == Line(points)
        True
        >>> Line(points) == Line(list(reversed(points)))
        False
        """
        return self.points == other.points

    def __ne__(self, other):
        """
        >>> Line([Point(1, 2)]) != Line([Point(1, 2)])
        False
        >>> Line([Point(1, 2)]) != Line([Point(2, 1)])
        True
        """
        return not self.__eq__(other)

    def __len__(self):
        return len(self.points)

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


def _clean_points(points):
    """
    Given a list of :class:`Point` objects, return a new list with adjacent
    duplicate points removed.

    >>> a, b, c = Point(1, 2, 3), Point(3, 4, 5), Point(5, 6, 7)
    >>> _clean_points([a, a, a, b, a, c, c]) == [a, b, a, c]
    True
    """
    if not points:
        return points

    result = [points[0]]
    for point in points:
        if point != result[-1]:
            result.append(point)
    return result


def _line_intersects_itself(lons, lats, closed_shape=False):
    """
    Return ``True`` if line of points intersects itself.
    Line with the last point repeating the first one considered
    intersecting itself.

    The line is defined by lists (or numpy arrays) of points'
    longitudes and latitudes (depth is not taken into account).

    :param closed_shape:
        If ``True`` the line will be checked twice: first time with its
        original shape and second time with the points sequence being
        shifted by one point (the last point becomes first, the first
        turns second and so on). This is useful for checking that
        the sequence of points defines a valid :class:`Polygon`.
    """
    assert len(lons) == len(lats)

    if len(lons) <= 3:
        # line can not intersect itself unless there are
        # at least four points
        return False

    west, east, north, south = _get_spherical_bounding_box(lons, lats)
    proj = _get_stereographic_projection(west, east, north, south)

    xx, yy = proj(lons, lats)
    if not shapely.geometry.LineString(zip(xx, yy)).is_simple:
        return True

    if closed_shape:
        xx, yy = proj(numpy.roll(lons, 1), numpy.roll(lats, 1))
        if not shapely.geometry.LineString(zip(xx, yy)).is_simple:
            return True

    return False


def _get_longitudinal_extent(lon1, lon2):
    """
    Return the distance between two longitude values as an angular measure.
    Parameters represent two longitude values in degrees.

    :return:
        Float, the angle between ``lon1`` and ``lon2`` in degrees. Value
        is positive if ``lon2`` is on the east from ``lon1`` and negative
        otherwise. Absolute value of the result doesn't exceed 180 for
        valid parameters values.

    >>> _get_longitudinal_extent(10, 20)
    10
    >>> _get_longitudinal_extent(20, 10)
    -10
    >>> _get_longitudinal_extent(-10, -15)
    -5
    >>> _get_longitudinal_extent(-120, 30)
    150
    >>> _get_longitudinal_extent(-178.3, 177.7)
    -4.0
    >>> _get_longitudinal_extent(178.3, -177.7)
    4.0
    >>> _get_longitudinal_extent(95, -180 + 94)
    179
    >>> _get_longitudinal_extent(95, -180 + 96)
    -179
    """
    extent = lon2 - lon1
    if extent > 180:
        extent = -360 + extent
    elif extent < -180:
        extent = 360 + extent
    return extent


def _get_spherical_bounding_box(lons, lats):
    """
    Given a collection of points find and return the bounding box,
    as a pair of longitudes and a pair of latitudes.

    Parameters define longitudes and latitudes of a point collection
    respectively in a form of lists or numpy arrays.

    :return:
        A tuple of four items. These items represent western, eastern,
        northern and southern borders of the bounding box respectively.
        Values are floats in decimal degrees.

    >>> _get_spherical_bounding_box([10, -10], [50, 60])
    (-10, 10, 60, 50)
    >>> _get_spherical_bounding_box([20], [-40])
    (20, 20, -40, -40)
    >>> _get_spherical_bounding_box([-20, 180, 179, 178], [-1, -2, 1, 2])
    (178, -20, 2, -2)
    """
    north, south = numpy.max(lats), numpy.min(lats)
    west, east = numpy.min(lons), numpy.max(lons)
    if _get_longitudinal_extent(west, east) < 0:
        # points are lying on both sides of the international date line
        # (meridian 180). the actual west longitude is the lowest positive
        # longitude and east one is the highest negative.
        west = min(lon for lon in lons if lon > 0)
        east = max(lon for lon in lons if lon < 0)
    return west, east, north, south


def _get_stereographic_projection(west, east, north, south):
    """
    Create and return a projection object for a given bounding box.

    Parameters define a bounding box in a spherical coordinates of the
    collection of points that is about to be projected. The center point
    of the projection (coordinates (0, 0) in Cartesian space) is set
    to the middle point of that bounding box. The resulting projection
    is defined for spherical coordinates that are not further from the
    bounding box center than 90 degree on the great circle arc.

    The result projection is of type Oblique Stereographic, see
    http://www.remotesensing.org/geotiff/proj_list/oblique_stereographic.html.

    This projection is prone to distance, area and angle distortions
    everywhere outside of the center point, but still can be used for
    checking shapes: verifying if line intersects itself (like in
    :func:`_line_intersects_itself`) or if point is inside of a polygon
    (like in :meth:`Polygon.discretize`).

    >>> t = lambda *co: sorted(_get_stereographic_projection(*co).srs.split())
    >>> t(10, 16, -20, 30)
    ['+lat_0=5.0', '+lon_0=13.0', '+proj=stere', '+units=m']
    >>> t(-20, 40, 55, 56)
    ['+lat_0=55.5', '+lon_0=10.0', '+proj=stere', '+units=m']
    >>> t(177.6, -175.8, -10, 10)
    ['+lat_0=0.0', '+lon_0=-179.1', '+proj=stere', '+units=m']
    """
    middle_lat = (north + south) / 2.0
    middle_lon = west + _get_longitudinal_extent(west, east) / 2.0
    if middle_lon > 180:
        middle_lon = middle_lon - 360
    return pyproj.Proj(proj='stere', lat_0=middle_lat, lon_0=middle_lon)


class Polygon(object):
    """
    Polygon objects represent an area on the Earth surface.

    :param points:
        The list of :class:`Point` objects defining the polygon vertices.
        The points are connected by great circle arcs in order of appearance.
        Polygon segment should not cross another polygon segment. At least
        three points must be defined.
    :raises RuntimeError:
        If ``points`` contains less than three unique points or if polygon
        perimeter intersects itself.
    """
    #: The angular measure of longitudinally-extended lines resampling
    #: in decimal degrees. See :meth:`_get_resampled_coordinates`.
    LONGITUDINAL_DISCRETIZATION = 1

    def __init__(self, points):
        points = _clean_points(points)

        if not len(points) >= 3:
            raise RuntimeError('polygon must have at least 3 unique vertices')

        self.lons = numpy.array([float(point.longitude) for point in points])
        self.lats = numpy.array([float(point.latitude) for point in points])
        self.num_points = len(points)

        if _line_intersects_itself(self.lons, self.lats, closed_shape=True):
            raise RuntimeError('polygon perimeter intersects itself')

    def _get_resampled_coordinates(self):
        """
        Resample segments the polygon consists of and return new vertices
        coordinates.

        :return:
            A tuple of two numpy arrays: longitudes and latitudes
            of resampled vertices.

        In order to find the higher and lower latitudes that the polygon
        touches we need to connect vertices by great circle arcs. If two
        points lie on the same parallel, the points in between that are
        forming the great circle arc deviate in latitude and are closer
        to pole than parallel corner points lie on (except the special
        case of equator). We need to break all longitudinally extended
        line to smaller pieces so we would not miss the area in between
        the great circle arc that connects two points and a parallel
        they share.

        We don't need to resample latitudinally-extended lines because
        all meridians are great circles.
        """
        resampled_lons = [self.lons[0]]
        resampled_lats = [self.lats[0]]
        for i in xrange(self.num_points):
            next_point = (i + 1) % self.num_points
            lon1, lat1 = self.lons[i], self.lats[i]
            lon2, lat2 = self.lons[next_point], self.lats[next_point]
            lon_extent = _get_longitudinal_extent(lon1, lon2)
            num_segments = lon_extent / self.LONGITUDINAL_DISCRETIZATION
            if num_segments <= 1:
                resampled_lons.append(lon2)
                resampled_lats.append(lat2)
            else:
                for lon, lat in GEOD.npts(lon1, lat1, lon2, lat2,
                                          num_segments):
                    resampled_lons.append(lon)
                    resampled_lats.append(lat)
        return numpy.array(resampled_lons), numpy.array(resampled_lats)

    def discretize(self, mesh_spacing):
        """
        Get a generator of uniformly spaced points inside the polygon area
        with distance of ``mesh_spacing`` km between.
        """
        # cast from km to m
        mesh_spacing *= 1e3

        # resample longitudinally-extended lines:
        lons, lats = self._get_resampled_coordinates()

        # find the bounding box of a polygon in a spherical coordinates:
        west, east, north, south = _get_spherical_bounding_box(lons, lats)

        # create a projection that is centered in a polygon center:
        proj = _get_stereographic_projection(west, east, north, south)

        # project polygon vertices to the Cartesian space and create
        # a shapely polygon object:
        xx, yy = proj(lons, lats)
        polygon2d = shapely.geometry.Polygon(zip(xx, yy))

        del xx, yy, lats, lons

        # we cover the bounding box (in spherical coordinates) from highest
        # to lowest latitude and from left to right by longitude. we step
        # by mesh spacing distance (linear measure). we check each point
        # if it is inside the polygon and yield the point object, if so.
        # this way we produce an uniformly-spaced mesh regardless of the
        # latitude.
        latitude = north
        while latitude > south:
            longitude = west
            while _get_longitudinal_extent(longitude, east) > 0:
                # we use Cartesian space just for checking if a point
                # is inside of the polygon.
                x, y = proj(longitude, latitude)
                if polygon2d.contains(shapely.geometry.Point(x, y)):
                    yield Point(longitude, latitude)

                # move by mesh spacing along parallel in inner loop...
                longitude, _, _ = GEOD.fwd(longitude, latitude,
                                           90, mesh_spacing)
            # ... and by the same distance along meridian in outer one
            _, latitude, _ = GEOD.fwd(west, latitude, 180, mesh_spacing)
