# encoding: utf-8
"""
Module providing geographical classes and functions.
"""
import numpy
import pyproj
import shapely.geometry

from nhe.geo import _utils as utils

#: Geod object to be used whenever we need to deal with
#: spherical coordinates.
GEOD = pyproj.Geod(ellps='sphere')


from nhe.geo.point import Point


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
        list of :class:`~nhe.geo.point.Point` instances
    """

    def __init__(self, points):
        self.points = utils.clean_points(points)

        if len(self.points) < 1:
            raise RuntimeError("One point needed to create a line!")

        lats = [point.latitude for point in self.points]
        lons = [point.longitude for point in self.points]
        if utils.line_intersects_itself(lons, lats):
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
        points = utils.clean_points(points)

        if not len(points) >= 3:
            raise RuntimeError('polygon must have at least 3 unique vertices')

        self.lons = numpy.array([float(point.longitude) for point in points])
        self.lats = numpy.array([float(point.latitude) for point in points])
        self.num_points = len(points)

        if utils.line_intersects_itself(self.lons, self.lats,
                                        closed_shape=True):
            raise RuntimeError('polygon perimeter intersects itself')

    def _get_resampled_coordinates(self):
        """
        Resample segments the polygon consists of and return new vertices
        coordinates.

        :return:
            A tuple of two numpy arrays: longitudes and latitudes
            of resampled vertices. The last point repeats the first one.

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
            lon_extent = abs(utils.get_longitudinal_extent(lon1, lon2))
            num_points = int(lon_extent / self.LONGITUDINAL_DISCRETIZATION) - 1
            if num_points > 0:
                for lon, lat in GEOD.npts(lon1, lat1, lon2, lat2, num_points):
                    # sometimes pyproj geod object may return values
                    # that are slightly out of range and that can
                    # break _get_spherical_bounding_box().
                    if lon <= -180:
                        lon += 360
                    elif lon > 180:
                        lon -= 360
                    assert -90 <= lat <= 90
                    resampled_lons.append(lon)
                    resampled_lats.append(lat)
            # since npts() accepts the last argument as the number of points
            # in the middle, we need to add the last point unconditionally
            resampled_lons.append(lon2)
            resampled_lats.append(lat2)
        # we don't cut off the last point so it repeats the first one.
        # shapely polygon is ok with that (we even save it from extra
        # work of copying the last point for us).
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
        west, east, north, south = utils.get_spherical_bounding_box(lons, lats)

        # create a projection that is centered in a polygon center:
        proj = utils.get_stereographic_projection(west, east, north, south)

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
            while utils.get_longitudinal_extent(longitude, east) > 0:
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
