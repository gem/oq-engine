# nhlib: A New Hazard Library
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
Package-private module :mod:`nhlib.geo._utils` contains functions that are
common to several geographical primitives.
"""
import numpy
import pyproj
import shapely.geometry


#: Geod object to be used whenever we need to deal with
#: spherical coordinates.
GEOD = pyproj.Geod(ellps='sphere')

#: Earth radius in km.
EARTH_RADIUS = 6371.0


def clean_points(points):
    """
    Given a list of :class:`~nhlib.geo.point.Point` objects, return a new list
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
        if not all((get_longitudinal_extent(west, lon) >= 0
                    and get_longitudinal_extent(lon, east) >= 0)
                   for lon in lons):
            raise ValueError('points collection has longitudinal extent '
                             'wider than 180 deg')
    return west, east, north, south


def get_orthographic_projection(west, east, north, south):
    """
    Create and return a projection object for a given bounding box.

    :returns:
        A pyproj's projection object. See
        `http://pyproj.googlecode.com/svn/trunk/docs/pyproj.Proj-class.html`_.

    Parameters are given as floats, representing decimal degrees (first two
    are longitudes and last two are latitudes). They define a bounding box
    in a spherical coordinates of the collection of points that is about
    to be projected. The center point of the projection (coordinates (0, 0)
    in Cartesian space) is set to the middle point of that bounding box.
    The resulting projection is defined for spherical coordinates that are
    not further from the bounding box center than 90 degree on the great
    circle arc.

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


def spherical_to_cartesian(lons, lats, depths):
    """
    Return the position vectors (in Cartesian coordinates) of list of spherical
    coordinates.

    For equations see: http://mathworld.wolfram.com/SphericalCoordinates.html.

    Parameters are components of spherical coordinates in a form of scalars,
    lists or numpy arrays. ``depths`` can be ``None`` in which case it's
    considered zero for all points.

    :returns:
        ``numpy.array`` of shape (3, n), where n is the number of points
        in original spherical coordinates lists. Those three rows in the
        returned array are the Cartesian coordinates x, y and z.
    """
    phi = numpy.radians(lons)
    theta = numpy.radians(lats)
    if depths is None:
        rr = EARTH_RADIUS
    else:
        rr = EARTH_RADIUS - numpy.array(depths)
    cos_theta_r = rr * numpy.cos(theta)
    xx = cos_theta_r * numpy.cos(phi)
    yy = cos_theta_r * numpy.sin(phi)
    zz = rr * numpy.sin(theta)
    return numpy.array([xx, yy, zz])


def ensure(expr, msg):
    """
    Utility method that raises an error if the
    given condition is not true.
    """

    if not expr:
        raise ValueError(msg)


def triangle_area(e1, e2, e3):
    """
    Get the area of triangle formed by three vectors.

    Parameters are three three-dimensional numpy arrays representing
    vectors of triangle's edges in Cartesian space.

    :returns:
        Float number, the area of the triangle in squared units of coordinates,
        or numpy array of shape of edges with one dimension less.

    Uses Heron formula, see `http://mathworld.wolfram.com/HeronsFormula.html`_.
    """
    # calculating edges length
    e1_length = numpy.sqrt(numpy.sum(e1 * e1, axis=-1))
    e2_length = numpy.sqrt(numpy.sum(e2 * e2, axis=-1))
    e3_length = numpy.sqrt(numpy.sum(e3 * e3, axis=-1))
    # calculating half perimeter
    s = (e1_length + e2_length + e3_length) / 2.0
    # applying Heron's formula
    return numpy.sqrt(s * (s - e1_length) * (s - e2_length) * (s - e3_length))


def normalized(vector):
    """
    Get unit vector for a given one.

    :param vector:
        Numpy vector as coordinates in Cartesian space, or an array of such.
    :returns:
        Numpy array of the same shape and structure where all vectors are
        normalized. That is, each coordinate component is divided by its
        vector's length.
    """
    length = numpy.sum(vector * vector, axis=-1)
    length = numpy.sqrt(length.reshape(length.shape + (1, )))
    return vector / length
