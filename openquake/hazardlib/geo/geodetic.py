# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.geodetic` contains functions for geodetic
transformations, optimized for massive calculations.
"""
from __future__ import division

import operator

import numpy
try:
    import rtree
except ImportError:
    rtree = None

from openquake.baselib.python3compat import range, round

#: Earth radius in km.
EARTH_RADIUS = 6371.0

#: Maximum elevation on Earth in km.
EARTH_ELEVATION = -8.848


def geodetic_distance(lons1, lats1, lons2, lats2, diameter=2*EARTH_RADIUS):
    """
    Calculate the geodetic distance between two points or two collections
    of points.

    Parameters are coordinates in decimal degrees. They could be scalar
    float numbers or numpy arrays, in which case they should "broadcast
    together".

    Implements http://williams.best.vwh.net/avform.htm#Dist

    :returns:
        Distance in km, floating point scalar or numpy array of such.
    """
    lons1, lats1, lons2, lats2 = _prepare_coords(lons1, lats1, lons2, lats2)
    distance = numpy.arcsin(numpy.sqrt(
        numpy.sin((lats1 - lats2) / 2.0) ** 2.0
        + numpy.cos(lats1) * numpy.cos(lats2)
        * numpy.sin((lons1 - lons2) / 2.0) ** 2.0
    ))
    return diameter * distance


def azimuth(lons1, lats1, lons2, lats2):
    """
    Calculate the azimuth between two points or two collections of points.

    Parameters are the same as for :func:`geodetic_distance`.

    Implements an "alternative formula" from
    http://williams.best.vwh.net/avform.htm#Crs

    :returns:
        Azimuth as an angle between direction to north from first point and
        direction to the second point measured clockwise in decimal degrees.
    """
    lons1, lats1, lons2, lats2 = _prepare_coords(lons1, lats1, lons2, lats2)
    cos_lat2 = numpy.cos(lats2)
    true_course = numpy.degrees(numpy.arctan2(
        numpy.sin(lons1 - lons2) * cos_lat2,
        numpy.cos(lats1) * numpy.sin(lats2)
        - numpy.sin(lats1) * cos_lat2 * numpy.cos(lons1 - lons2)
    ))
    return (360 - true_course) % 360


def distance(lons1, lats1, depths1, lons2, lats2, depths2):
    """
    Calculate a distance between two points (or collections of points)
    considering points' depth.

    Calls :func:`geodetic_distance`, finds the "vertical" distance between
    points by subtracting one depth from another and combine both using
    Pythagoras theorem.

    :returns:
        Distance in km, a square root of sum of squares of :func:`geodetic
        <geodetic_distance>` distance and vertical distance, which is just
        a difference between depths.
    """
    hdist = geodetic_distance(lons1, lats1, lons2, lats2)
    vdist = depths1 - depths2
    return numpy.sqrt(hdist ** 2 + vdist ** 2)


def min_distance_to_segment(seglons, seglats, lons, lats):
    """
    This function computes the shortest distance to a segment in a 2D reference
    system.

    :parameter seglons:
        A list or an array of floats specifying the longitude values of the two
        vertexes delimiting the segment.
    :parameter seglats:
        A list or an array of floats specifying the latitude values of the two
        vertexes delimiting the segment.
    :parameter lons:
        A list or a 1D array of floats specifying the longitude values of the
        points for which the calculation of the shortest distance is requested.
    :parameter lats:
        A list or a 1D array of floats specifying the latitude values of the
        points for which the calculation of the shortest distance is requested.
    :returns:
        An array of the same shape as lons which contains for each point
        defined by (lons, lats) the shortest distance to the segment.
        Distances are negative for those points that stay on the 'left side'
        of the segment direction and whose projection lies within the segment
        edges. For all other points, distance is positive.
    """

    # Check the size of the seglons, seglats arrays
    assert len(seglons) == len(seglats) == 2

    # Compute the azimuth of the segment
    seg_azim = azimuth(seglons[0], seglats[0], seglons[1], seglats[1])

    # Compute the azimuth of the direction obtained
    # connecting the first point defining the segment and each site
    azimuth1 = azimuth(seglons[0], seglats[0], lons, lats)

    # Compute the azimuth of the direction obtained
    # connecting the second point defining the segment and each site
    azimuth2 = azimuth(seglons[1], seglats[1], lons, lats)

    # Find the points inside the band defined by the two lines perpendicular
    # to the segment direction passing through the two vertexes of the segment.
    # For these points the closest distance is the distance from the great arc.
    idx_in = numpy.nonzero(
        (numpy.cos(numpy.radians(seg_azim-azimuth1)) >= 0.0) &
        (numpy.cos(numpy.radians(seg_azim-azimuth2)) <= 0.0))

    # Find the points outside the band defined by the two line perpendicular
    # to the segment direction passing through the two vertexes of the segment.
    # For these points the closest distance is the minimum of the distance from
    # the two point vertexes.
    idx_out = numpy.nonzero(
        (numpy.cos(numpy.radians(seg_azim-azimuth1)) < 0.0) |
        (numpy.cos(numpy.radians(seg_azim-azimuth2)) > 0.0))

    # Find the indexes of points 'on the left of the segment'
    idx_neg = numpy.nonzero(numpy.sin(numpy.radians(
        (azimuth1-seg_azim))) < 0.0)

    # Now let's compute the distances for the two cases.
    dists = numpy.zeros_like(lons)
    if len(idx_in[0]):
        dists[idx_in] = distance_to_arc(
            seglons[0], seglats[0], seg_azim, lons[idx_in], lats[idx_in])
    if len(idx_out[0]):
        dists[idx_out] = min_geodetic_distance(
            seglons, seglats, lons[idx_out], lats[idx_out])

    # Finally we correct the sign of the distances in order to make sure that
    # the points on the right semispace defined using as a reference the
    # direction defined by the segment (i.e. the direction defined by going
    # from the first point to the second one) have a positive distance and
    # the others a negative one.
    dists = abs(dists)
    dists[idx_neg] = - dists[idx_neg]

    return dists


def _reshape(array, orig_shape):
    if orig_shape:
        return array.reshape(orig_shape)
    return array[0]  # scalar array


def min_geodetic_distance(mlons, mlats, slons, slats, diameter=2*EARTH_RADIUS):
    """
    Small wrapper around :func:`pure_distances`, suitable
    for calculating the minimum distance between first mesh and each point
    of the second mesh when both are defined on the earth surface.
    """
    mlons, mlats, slons, slats = _prepare_coords(
        mlons.flatten(), mlats.flatten(), slons, slats)
    return pure_distances(mlons, mlats, slons, slats).min(axis=0) * diameter


# used to compute distances site-rupture for all sites
def pure_distances(mlons, mlats, slons, slats):
    """
    :param mlons: array of m longitudes (for the rupture)
    :param mlats: array of m latitudes (for the rupture)
    :param slons: array of s longitudes (for the sites)
    :param slats: array of s latitudes (for the sites)
    :returns: array of (m, s) distances to be multiplied by the Earth diameter
    """
    cos_mlats = numpy.cos(mlats)
    cos_slats = numpy.cos(slats)
    result = numpy.zeros((len(mlons), len(slons)))
    if len(mlons) < len(slons):  # lots of sites
        for i in range(len(mlons)):
            a = numpy.sin((mlats[i] - slats) / 2.0)
            b = numpy.sin((mlons[i] - slons) / 2.0)
            result[i, :] = numpy.arcsin(
                numpy.sqrt(a * a + cos_mlats[i] * cos_slats * b * b))
    else:  # few sites
        for j in range(len(slons)):
            a = numpy.sin((mlats - slats[j]) / 2.0)
            b = numpy.sin((mlons - slons[j]) / 2.0)
            result[:, j] = numpy.arcsin(
                numpy.sqrt(a * a + cos_mlats * cos_slats[j] * b * b))
    return result


def min_idx_dst(mlons, mlats, mdepths, slons, slats, sdepths=0,
                diameter=2*EARTH_RADIUS):
    """
    Calculate the minimum distance between a collection of points and a point.

    This function allows to calculate a closest distance to a collection
    of points for each point in another collection. Both collection can be
    of any shape, although it doesn't make sense to use scalars for the first
    one.

    Implements the same formula as in :func:`geodetic_distance` for distance
    along great circle arc and the same approach as in :func:`distance`
    for combining it with depth distance.

    :param mlons, mlats, mdepths:
        Numpy arrays of the same shape representing a first collection
        of points, the one distance to which is of interest -- longitudes,
        latitudes (both in decimal degrees) and depths (in km).
    :param slons, slats, sdepths:
        Scalars, python lists or tuples or numpy arrays of the same shape,
        representing a second collection: a list of points to find a minimum
        distance from for.
    :returns:
        Indices and distances in km of the closest points. The result value is
        a scalar if ``slons``, ``slats`` and ``sdepths`` are scalars and numpy
        array of the same shape of those three otherwise.
    """
    mlons, mlats, slons, slats = _prepare_coords(mlons, mlats, slons, slats)
    mdepths = numpy.array(mdepths, float)
    sdepths = numpy.array(sdepths, float)
    assert mlons.shape == mdepths.shape
    assert slons.shape == sdepths.shape

    orig_shape = slons.shape

    mlons = mlons.reshape(-1)
    mlats = mlats.reshape(-1)
    mdepths = mdepths.reshape(-1)
    slons = slons.reshape(-1)
    slats = slats.reshape(-1)
    sdepths = sdepths.reshape(-1)

    dst = pure_distances(mlons, mlats, slons, slats) * diameter
    delta = numpy.array([[mdepth - sdepth for sdepth in sdepths]
                         for mdepth in mdepths])
    dist_squares = dst ** 2 + delta ** 2
    min_idx = dist_squares.argmin(axis=0)  # (m, s) -> s
    min_dst = numpy.sqrt(dist_squares.min(axis=0))  # (m, s) -> s
    return _reshape(min_idx, orig_shape), _reshape(min_dst, orig_shape)


def intervals_between(lon1, lat1, depth1, lon2, lat2, depth2, length):
    """
    Find a list of points between two given ones that lie on the same
    great circle arc and are equally spaced by ``length`` km.

    :param float lon1, lat1, depth1:
        Coordinates of a point to start placing intervals from. The first
        point in the resulting list has these coordinates.
    :param float lon2, lat2, depth2:
        Coordinates of the other end of the great circle arc segment
        to put intervals on. The last resulting point might be closer
        to the first reference point than the second one or further,
        since the number of segments is taken as rounded division of
        length between two reference points and ``length``.
    :param length:
        Required distance between two subsequent resulting points, in km.
    :returns:
        Tuple of three 1d numpy arrays: longitudes, latitudes and depths
        of resulting points respectively.

    Rounds the distance between two reference points with respect
    to ``length`` and calls :func:`npoints_towards`.
    """
    assert length > 0
    hdist = geodetic_distance(lon1, lat1, lon2, lat2)
    vdist = depth2 - depth1
    # if this method is called multiple times with coordinates that are
    # separated by the same distance, because of floating point imprecisions
    # the total distance may have slightly different values (for instance if
    # the distance between two set of points is 65 km, total distance can be
    # 64.9999999999989910 and 65.0000000000020322). These two values bring to
    # two different values of num_intervals (32 in the first case and 33 in
    # the second), and this is a problem because for the same distance we
    # should have the same number of intervals. To reduce potential differences
    # due to floating point errors, we therefore round total_distance to a
    # fixed precision (7)
    total_distance = round(numpy.sqrt(hdist ** 2 + vdist ** 2), 7)
    num_intervals = int(round(total_distance / length))
    if num_intervals == 0:
        return numpy.array([lon1]), numpy.array([lat1]), numpy.array([depth1])
    dist_factor = (length * num_intervals) / total_distance
    return npoints_towards(
        lon1, lat1, depth1, azimuth(lon1, lat1, lon2, lat2),
        hdist * dist_factor, vdist * dist_factor, num_intervals + 1)


def npoints_between(lon1, lat1, depth1, lon2, lat2, depth2, npoints):
    """
    Find a list of specified number of points between two given ones that are
    equally spaced along the great circle arc connecting given points.

    :param float lon1, lat1, depth1:
        Coordinates of a point to start from. The first point in a resulting
        list has these coordinates.
    :param float lon2, lat2, depth2:
        Coordinates of a point to finish at. The last point in a resulting
        list has these coordinates.
    :param npoints:
        Integer number of points to return. First and last points count,
        so if there have to be two intervals, ``npoints`` should be 3.
    :returns:
        Tuple of three 1d numpy arrays: longitudes, latitudes and depths
        of resulting points respectively.

    Finds distance between two reference points and calls
    :func:`npoints_towards`.
    """
    hdist = geodetic_distance(lon1, lat1, lon2, lat2)
    vdist = depth2 - depth1
    rlons, rlats, rdepths = npoints_towards(
        lon1, lat1, depth1, azimuth(lon1, lat1, lon2, lat2),
        hdist, vdist, npoints
    )
    # the last point should be left intact
    rlons[-1] = lon2
    rlats[-1] = lat2
    rdepths[-1] = depth2
    return rlons, rlats, rdepths


def npoints_towards(lon, lat, depth, azimuth, hdist, vdist, npoints):
    """
    Find a list of specified number of points starting from a given one
    along a great circle arc with a given azimuth measured in a given point.

    :param float lon, lat, depth:
        Coordinates of a point to start from. The first point in a resulting
        list has these coordinates.
    :param azimuth:
        A direction representing a great circle arc together with a reference
        point.
    :param hdist:
        Horizontal (geodetic) distance from reference point to the last point
        of the resulting list, in km.
    :param vdist:
        Vertical (depth) distance between reference and the last point, in km.
    :param npoints:
        Integer number of points to return. First and last points count,
        so if there have to be two intervals, ``npoints`` should be 3.
    :returns:
        Tuple of three 1d numpy arrays: longitudes, latitudes and depths
        of resulting points respectively.

    Implements "completely general but more complicated algorithm" from
    http://williams.best.vwh.net/avform.htm#LL
    """
    assert npoints > 1
    rlon, rlat = numpy.radians(lon), numpy.radians(lat)
    tc = numpy.radians(360 - azimuth)
    hdists = numpy.arange(npoints, dtype=float)
    hdists *= (hdist / EARTH_RADIUS) / (npoints - 1)
    vdists = numpy.arange(npoints, dtype=float)
    vdists *= vdist / (npoints - 1)

    sin_dists = numpy.sin(hdists)
    cos_dists = numpy.cos(hdists)
    sin_lat = numpy.sin(rlat)
    cos_lat = numpy.cos(rlat)

    sin_lats = sin_lat * cos_dists + cos_lat * sin_dists * numpy.cos(tc)
    lats = numpy.degrees(numpy.arcsin(sin_lats))

    dlon = numpy.arctan2(numpy.sin(tc) * sin_dists * cos_lat,
                         cos_dists - sin_lat * sin_lats)
    lons = numpy.mod(rlon - dlon + numpy.pi, 2 * numpy.pi) - numpy.pi
    lons = numpy.degrees(lons)

    depths = vdists + depth

    # the first point should be left intact
    lons[0] = lon
    lats[0] = lat
    depths[0] = depth

    return lons, lats, depths


def point_at(lon, lat, azimuth, distance):
    """
    Perform a forward geodetic transformation: find a point lying at a given
    distance from a given one on a great circle arc defined by azimuth.

    :param float lon, lat:
        Coordinates of a reference point, in decimal degrees.
    :param azimuth:
        An azimuth of a great circle arc of interest measured in a reference
        point in decimal degrees.
    :param distance:
        Distance to target point in km.
    :returns:
        Tuple of two float numbers: longitude and latitude of a target point
        in decimal degrees respectively.

    Implements the same approach as :func:`npoints_towards`.
    """
    # this is a simplified version of npoints_towards().
    # code duplication is justified by performance reasons.
    lon, lat = numpy.radians(lon), numpy.radians(lat)
    tc = numpy.radians(360 - azimuth)
    sin_dists = numpy.sin(distance / EARTH_RADIUS)
    cos_dists = numpy.cos(distance / EARTH_RADIUS)
    sin_lat = numpy.sin(lat)
    cos_lat = numpy.cos(lat)

    sin_lats = sin_lat * cos_dists + cos_lat * sin_dists * numpy.cos(tc)
    lats = numpy.degrees(numpy.arcsin(sin_lats))

    dlon = numpy.arctan2(numpy.sin(tc) * sin_dists * cos_lat,
                         cos_dists - sin_lat * sin_lats)
    lons = numpy.mod(lon - dlon + numpy.pi, 2 * numpy.pi) - numpy.pi
    lons = numpy.degrees(lons)

    return lons, lats


def distance_to_semi_arc(alon, alat, aazimuth, plons, plats):
    """
    In this method we use a reference system centerd on (alon, alat) and with
    the y-axis corresponding to aazimuth direction to calculate the minimum
    distance from a semiarc with generates in (alon, alat).

    Parameters are the same as for :func:`distance_to_arc`.
    """

    if type(plons) is float:
        plons = numpy.array([plons])
        plats = numpy.array([plats])

    azimuth_to_target = azimuth(alon, alat, plons, plats)

    # Find the indexes of the points in the positive y halfspace
    idx = numpy.nonzero(numpy.cos(
        numpy.radians((aazimuth-azimuth_to_target))) > 0.0)

    # Find the indexes of the points in the negative y halfspace
    idx_not = numpy.nonzero(numpy.cos(
        numpy.radians((aazimuth-azimuth_to_target))) <= 0.0)

    idx_ll_quadr = numpy.nonzero(
        (numpy.cos(numpy.radians((aazimuth-azimuth_to_target))) <= 0.0) &
        (numpy.sin(numpy.radians((aazimuth-azimuth_to_target))) > 0.0))

    # Initialise the array containing the final distances
    distance = numpy.zeros_like(plons)

    # Compute the distance between the semi-arc with 'aazimuth' direction
    # and the set of sites in the positive half-space. The shortest distance to
    # the semi-arc in this case can be computed using the function
    # :func:`openquake.hazardlib.geo.geodetic.distance_to_arc`.
    if len(idx):
        distance_to_target = geodetic_distance(alon, alat,
                                               plons[idx], plats[idx])
        t_angle = (azimuth_to_target[idx] - aazimuth + 360) % 360
        angle = numpy.arccos((numpy.sin(numpy.radians(t_angle)) *
                              numpy.sin(distance_to_target /
                                        EARTH_RADIUS)))
        distance[idx] = (numpy.pi / 2 - angle) * EARTH_RADIUS

    # Compute the distance between the reference point and the set of sites
    # in the negative half-space. The shortest distance for the semi-arc for
    # all the points in the negative semi-space simply corresponds to the
    # shortest distance to its origin.
    if len(idx_not):
        distance[idx_not] = geodetic_distance(alon, alat,
                                              plons[idx_not], plats[idx_not])
        distance[idx_ll_quadr] = -1 * distance[idx_ll_quadr]

    return distance


def distance_to_arc(alon, alat, aazimuth, plons, plats):
    """
    Calculate a closest distance between a great circle arc and a point
    (or a collection of points).

    :param float alon, alat:
        Arc reference point longitude and latitude, in decimal degrees.
    :param azimuth:
        Arc azimuth (an angle between direction to a north and arc in clockwise
        direction), measured in a reference point, in decimal degrees.
    :param float plons, plats:
        Longitudes and latitudes of points to measure distance. Either scalar
        values or numpy arrays of decimal degrees.
    :returns:
        Distance in km, a scalar value or numpy array depending on ``plons``
        and ``plats``. A distance is negative if the target point lies on the
        right hand side of the arc.

    Solves a spherical triangle formed by reference point, target point and
    a projection of target point to a reference great circle arc.
    """
    azimuth_to_target = azimuth(alon, alat, plons, plats)
    distance_to_target = geodetic_distance(alon, alat, plons, plats)

    # find an angle between an arc and a great circle arc connecting
    # arc's reference point and a target point
    t_angle = (azimuth_to_target - aazimuth + 360) % 360

    # in a spherical right triangle cosine of the angle of a cathetus
    # augmented to pi/2 is equal to sine of an opposite angle times
    # sine of hypotenuse, see
    # http://en.wikipedia.org/wiki/Spherical_trigonometry#Napier.27s_Pentagon
    angle = numpy.arccos(
        (numpy.sin(numpy.radians(t_angle))
         * numpy.sin(distance_to_target / EARTH_RADIUS))
    )
    return (numpy.pi / 2 - angle) * EARTH_RADIUS


def _prepare_coords(lons1, lats1, lons2, lats2):
    """
    Convert two pairs of spherical coordinates in decimal degrees
    to numpy arrays of radians. Makes sure that respective coordinates
    in pairs have the same shape.
    """
    lons1 = numpy.radians(lons1)
    lats1 = numpy.radians(lats1)
    assert lons1.shape == lats1.shape
    lons2 = numpy.radians(lons2)
    lats2 = numpy.radians(lats2)
    assert lons2.shape == lats2.shape
    return lons1, lats1, lons2, lats2
