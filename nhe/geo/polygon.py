"""
Module :mod:`nhe.geo.polygon` defines :class:`Polygon`.
"""
import numpy
import shapely.geometry

from nhe.geo.point import Point
from nhe.geo._utils import GEOD
from nhe.geo import _utils as utils


class Polygon(object):
    """
    Polygon objects represent an area on the Earth surface.

    :param points:
        The list of :class:`Point` objects defining the polygon vertices.
        The points are connected by great circle arcs in order of appearance.
        Polygon segment should not cross another polygon segment. At least
        three points must be defined.
    :raises ValueError:
        If ``points`` contains less than three unique points or if polygon
        perimeter intersects itself.
    """
    #: The angular measure of longitudinally-extended lines resampling
    #: in decimal degrees. See :meth:`_get_resampled_coordinates`.
    LONGITUDINAL_DISCRETIZATION = 1

    def __init__(self, points):
        points = utils.clean_points(points)

        if not len(points) >= 3:
            raise ValueError('polygon must have at least 3 unique vertices')

        self.lons = numpy.array([float(point.longitude) for point in points])
        self.lats = numpy.array([float(point.latitude) for point in points])
        self.num_points = len(points)

        if utils.line_intersects_itself(self.lons, self.lats,
                                        closed_shape=True):
            raise ValueError('polygon perimeter intersects itself')

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
