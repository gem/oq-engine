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
import numpy

from nhlib.geo._utils import EARTH_RADIUS


def geodetic_distance(lons1, lats1, lons2, lats2):
    """
    Calculate the geodetic distance between two points or two collections
    of points.

    Parameters are coordinates in decimal degrees. They could be scalar
    float numbers or numpy arrays, in which case the should "broadcast
    together".

    :returns:
        Distance in km, floating point scalar or numpy array of such.
    """
    lons1 = numpy.radians(lons1)
    lats1 = numpy.radians(lats1)
    assert lons1.shape == lats1.shape
    lons2 = numpy.radians(lons2)
    lats2 = numpy.radians(lats2)
    assert lons2.shape == lats2.shape
    distance = numpy.arcsin(numpy.sqrt(
        numpy.sin((lats1 - lats2) / 2.0) ** 2.0
        + numpy.cos(lats1) * numpy.cos(lats2)
          * numpy.sin((lons1 - lons2) / 2.0) ** 2.0
    ).clip(-1., 1.))
    return (2.0 * EARTH_RADIUS) * distance


def azimuth(lons1, lats1, lons2, lats2):
    """
    Calculate the azimuth between two points or two collections of points.

    Parameters are the same as for :func:`geodetic_distance`.

    :returns:
        Azimuth as an angle between direction to north from first point and
        direction to the second point measured clockwise in decimal degrees.
    """
    lons1 = numpy.radians(lons1)
    lats1 = numpy.radians(lats1)
    assert lons1.shape == lats1.shape
    lons2 = numpy.radians(lons2)
    lats2 = numpy.radians(lats2)
    assert lons2.shape == lats2.shape
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

    :returns:
        Distance in km, a square root of sum of squares of :func:`geodetic
        <geodetic_distance>` distance and vertical distance, which is just
        a difference between depths.
    """
    hdist = geodetic_distance(lons1, lats1, lons2, lats2)
    vdist = depths1 - depths2
    return numpy.sqrt(hdist ** 2 + vdist ** 2)


def min_distance(lons1, lats1, lons2, lats2):
    """
    Calculate the minimum geodetic distance between a collection of points and
    a point.

    TBD

    :returns:
        Minimum distance in km, a scalar if ``lons2`` and ``lats2`` are scalars
        and numpy array of the same shape of those two otherwise.
    """
    # TODO: add support for depth
    assert lons1.shape == lats1.shape
    lons2, lats2 = numpy.array(lons2), numpy.array(lats2)
    assert lons2.shape == lats2.shape
    orig_shape = lons2.shape
    lons1 = numpy.radians(lons1.flat)
    lats1 = numpy.radians(lats1.flat)
    lons2 = numpy.radians(lons2.flat)
    lats2 = numpy.radians(lats2.flat)
    cos_lats1 = numpy.cos(lats1)
    cos_lats2 = numpy.cos(lats2)
    distance = numpy.array([
        numpy.min(numpy.arcsin(numpy.sqrt(
            numpy.sin((lats1 - lats2[i]) / 2.0) ** 2.0
            + cos_lats1 * cos_lats2[i]
              * numpy.sin((lons1 - lons2[i]) / 2.0) ** 2.0
        ).clip(-1., 1.)))
        for i in xrange(len(lats2))
    ])
    return (2.0 * EARTH_RADIUS) * distance.reshape(orig_shape)
