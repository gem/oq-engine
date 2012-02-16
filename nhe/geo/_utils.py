"""
Package-private module :mod:`nhe.geo._utils` contains functions that are
common to several geographical primitives.
"""
import numpy
import pyproj
import shapely.geometry

#: Geod object to be used whenever we need to deal with
#: spherical coordinates.
GEOD = pyproj.Geod(ellps='sphere')


def clean_points(points):
    """
    Given a list of :class:`~nhe.geo.point.Point` objects, return a new list
    with adjacent duplicate points removed.
    """
    if not points:
        return points

    result = [points[0]]
    for point in points:
        if point != result[-1]:
            result.append(point)
    return result


def line_intersects_itself(lons, lats, closed_shape=False):
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

    west, east, north, south = get_spherical_bounding_box(lons, lats)
    proj = get_orthographic_projection(west, east, north, south)

    xx, yy = proj(lons, lats)
    if not shapely.geometry.LineString(zip(xx, yy)).is_simple:
        return True

    if closed_shape:
        xx, yy = proj(numpy.roll(lons, 1), numpy.roll(lats, 1))
        if not shapely.geometry.LineString(zip(xx, yy)).is_simple:
            return True

    return False


def get_longitudinal_extent(lon1, lon2):
    """
    Return the distance between two longitude values as an angular measure.
    Parameters represent two longitude values in degrees.

    :return:
        Float, the angle between ``lon1`` and ``lon2`` in degrees. Value
        is positive if ``lon2`` is on the east from ``lon1`` and negative
        otherwise. Absolute value of the result doesn't exceed 180 for
        valid parameters values.
    """
    extent = lon2 - lon1
    if extent > 180:
        extent = -360 + extent
    elif extent < -180:
        extent = 360 + extent
    return extent


def get_spherical_bounding_box(lons, lats):
    """
    Given a collection of points find and return the bounding box,
    as a pair of longitudes and a pair of latitudes.

    Parameters define longitudes and latitudes of a point collection
    respectively in a form of lists or numpy arrays.

    :return:
        A tuple of four items. These items represent western, eastern,
        northern and southern borders of the bounding box respectively.
        Values are floats in decimal degrees.
    :raises ValueError:
        If points collection has the longitudinal extent of more than
        180 degrees (it is impossible to define a single hemisphere
        bound to poles that would contain the whole collection).
    """
    north, south = numpy.max(lats), numpy.min(lats)
    west, east = numpy.min(lons), numpy.max(lons)
    assert (-180 < west <= 180) and (-180 < east <= 180)
    if get_longitudinal_extent(west, east) < 0:
        # points are lying on both sides of the international date line
        # (meridian 180). the actual west longitude is the lowest positive
        # longitude and east one is the highest negative.
        west = min(lon for lon in lons if lon > 0)
        east = max(lon for lon in lons if lon < 0)
        if not all ((get_longitudinal_extent(west, lon) >= 0
                     and get_longitudinal_extent(lon, east) >= 0)
                    for lon in lons):
            raise ValueError('points collection has longitudinal extent '
                             'wider than 180 deg')
    return west, east, north, south


def get_orthographic_projection(west, east, north, south):
    """
    Create and return a projection object for a given bounding box.

    Parameters define a bounding box in a spherical coordinates of the
    collection of points that is about to be projected. The center point
    of the projection (coordinates (0, 0) in Cartesian space) is set
    to the middle point of that bounding box. The resulting projection
    is defined for spherical coordinates that are not further from the
    bounding box center than 90 degree on the great circle arc.

    The result projection is of type `Orthographic
    <http://www.remotesensing.org/geotiff/proj_list/orthographic.html>`_.
    This projection is prone to distance, area and angle distortions
    everywhere outside of the center point, but still can be used for
    checking shapes: verifying if line intersects itself (like in
    :func:`_line_intersects_itself`) or if point is inside of a polygon
    (like in :meth:`Polygon.discretize`). It can be also used for measuring
    distance to an extent of around 700 kilometers (error doesn't exceed
    1 km up until then).
    """
    middle_lon, middle_lat = get_middle_point(west, north, east, south)
    return pyproj.Proj(proj='ortho', lat_0=middle_lat, lon_0=middle_lon,
                       units='km', preserve_units=True)


def get_middle_point(lon1, lat1, lon2, lat2):
    """
    Given two points return the point exactly in the middle lying on the same
    great circle arc.

    Parameters are point coordinates in degrees.

    :returns:
        Tuple of longitude and latitude of the point in the middle.
    """
    if lon1 == lon2 and lat1 == lat2:
        return lon1, lat1
    [[lon, lat]] = GEOD.npts(lon1, lat1, lon2, lat2, 1)
    if lon <= -180:
        lon += 360
    return lon, lat
