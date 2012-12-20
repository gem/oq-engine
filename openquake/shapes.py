# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""Collection of base classes for processing spatially-related data."""

import hashlib
import json
import math
import numpy

from itertools import izip
from numpy import zeros

from numpy import allclose
from numpy import sin, cos, arctan2, sqrt, radians

from shapely import geometry
from scipy.interpolate import interp1d

from nhlib import geo as nhlib_geo
from openquake.utils import round_float
from openquake import logs

LOGGER = logs.LOG

logs.set_logger_level(LOGGER, logs.LEVELS.get('debug'))


class Region(object):
    """A container of polygons, used for bounds checking."""

    def __init__(self, polygon):
        self._grid = None
        self.cell_size = 0.1
        self.polygon = polygon

    @classmethod
    def from_coordinates(cls, coordinates):
        """
        Build a region from a list of polygon coordinates.

        :param coordinates:
            List of 2-tuples (lon, lat). Example ::

                [(-118.25, 34.07), (-118.22, 34.07), (-118.22, 34.04), \
(-118.25, 34.04)]

        :returns:
            :class:`openquake.shapes.Region` instance
        """

        # Constrain the precision for the coordinates:
        coordinates = [(round_float(pt[0]), round_float(pt[1]))
                for pt in coordinates]

        return cls(geometry.Polygon(coordinates))

    @classmethod
    def from_simple(cls, top_left, bottom_right):
        """
        Build a rectangular region from two corner points (top left, bottom
        right).

        :param top_left: tuple of two floats (longitude, latitude)
        :param top_right: tuple of two floats (longitude, latitude)

        :returns: :py:class:`openquake.shapes.Region` instance
        """
        points = [top_left, (top_left[0], bottom_right[1]),
                bottom_right, (bottom_right[0], top_left[1])]

        return cls.from_coordinates(points)

    @property
    def bounds(self):
        """Return a bounding box containing the whole region."""
        return self.polygon.bounds

    @property
    def lower_left_corner(self):
        """
        Lower left corner of the containing bounding box.

        :returns: :py:class:`openquake.shapes.Site` instance representing the
            lower left corner of this region.
        """
        (minx, miny, _maxx, _maxy) = self.bounds
        return Site(minx, miny)

    @property
    def lower_right_corner(self):
        """
        Lower right corner of the containing bounding box.

        :returns: :py:class:`openquake.shapes.Site` instance representing the
            lower right corner of this region.
        """
        (_minx, miny, maxx, _maxy) = self.bounds
        return Site(maxx, miny)

    @property
    def upper_left_corner(self):
        """
        Upper left corner of the containing bounding box.

        :returns: :py:class:`openquake.shapes.Site` instance representing the
            upper left corner of this region.
        """
        (minx, _miny, _maxx, maxy) = self.bounds
        return Site(minx, maxy)

    @property
    def upper_right_corner(self):
        """
        Upper right corner of the containing bounding box.

        :returns: :py:class:`openquake.shapes.Site` instance representing the
            upper right corner of this region.
        """
        (_minx, _miny, maxx, maxy) = self.bounds
        return Site(maxx, maxy)

    @property
    def grid(self):
        """
        Return a proxy interface that maps lat/lon
        to col/row based on a specific cellsize. Proxy is
        also iterable.
        """

        if not self.cell_size:
            raise Exception(
                "Can't generate grid without cell_size being set")

        if not self._grid:
            self._grid = Grid(self, self.cell_size)

        return self._grid


class RegionConstraint(Region):
    """Extends a basic region to work as a constraint on parsers"""

    def match(self, point):
        """Point (specified by Point class or tuple) is contained?"""
        if isinstance(point, Site):
            point = point.point
        if not isinstance(point, geometry.Point):
            point = geometry.Point(point[0], point[1])
        test = self.polygon.contains(point) or self.polygon.touches(point)
        return test


class GridPoint(object):
    """Simple (trivial) point class"""

    def __init__(self, grid, column, row):
        self.column = column
        self.row = row
        self.grid = grid

    def __eq__(self, other):
        if isinstance(other, Site):
            other = self.grid.point_at(other)
        test = (self.column == other.column
                and self.row == other.row
                and self.grid == other.grid)
        return test

    @property
    def site(self):
        """Trivial accessor for Site at Grid point"""
        return self.grid.site_at(self)

    def hash(self):
        """Ugly hashing function"""
        # TODO(jmc): Fixme
        return self.__hash__()

    def __repr__(self):
        return str(self.__hash__())

    def __hash__(self):
        #, int(self.grid.cell_size)
        return self.column * 1000000000 + self.row

    def __str__(self):
        return self.__repr__()


class Grid(object):
    """
    A proxy interface to Region.

    It translates geographical points identified
    by longitude and latitude to the corresponding grid points
    according to the grid spacing given.
    """

    def __init__(self, region, cell_size):
        self.cell_size = cell_size

        # center of the lower left cell of this grid
        self.llc = region.lower_left_corner

        self.columns = self._longitude_to_column(
                region.upper_right_corner.longitude) + 1

        self.rows = self._latitude_to_row(
                region.upper_right_corner.latitude) + 1

        self.polygon = self._build_polygon()

    def _build_polygon(self):
        """
        Create the polygon underlying this grid.
        """

        # since we are always considering the center of the
        # cells, we must include half of the cell size
        # to the borders
        half_cell_size = self.cell_size / 2.0

        min_lon = self.llc.longitude - half_cell_size
        max_lon = (self.llc.longitude + (self.columns * self.cell_size)
                + half_cell_size)

        min_lat = self.llc.latitude - half_cell_size
        max_lat = (self.llc.latitude + (self.rows * self.cell_size)
                + half_cell_size)

        coords = [(min_lon, max_lat), (max_lon, max_lat),
                  (max_lon, min_lat), (min_lon, min_lat)]

        return geometry.Polygon([(round_float(pt[0]),
                round_float(pt[1])) for pt in coords])

    def site_inside(self, site):
        """
        Confirm that the point is within the polygon
        underlying the gridded region.
        """

        if self.polygon.contains(site.point):
            return True

        if self.polygon.touches(site.point):
            return True

        return False

    def _latitude_to_row(self, latitude):
        """
        Return the corresponding grid row for the given
        latitude, according to grid spacing.
        """

        latitude_offset = math.fabs(
            latitude - self.llc.latitude)

        return int(round(latitude_offset / self.cell_size))

    def _row_to_latitude(self, row):
        """
        Return the corresponding latitude for the given
        grid row, according to grid spacing.
        """

        return self.llc.latitude + (row * self.cell_size)

    def _longitude_to_column(self, longitude):
        """
        Return the corresponding grid column for the given
        longitude, according to grid spacing.
        """

        longitude_offset = longitude - self.llc.longitude
        return int(round(longitude_offset / self.cell_size))

    def _column_to_longitude(self, column):
        """
        Return the corresponding longitude for the given
        grid column, according to grid spacing.
        """

        return self.llc.longitude + (column * self.cell_size)

    def site_at(self, point):
        """
        Return the site corresponding to the center of the
        cell identified by the given grid point.
        """

        return Site(self._column_to_longitude(point.column),
                self._row_to_latitude(point.row))

    def point_at(self, site):
        """
        Return the grid point where the given site falls in.
        """

        if not self.site_inside(site):
            raise ValueError("Site <%s> is outside region." % site)

        row = self._latitude_to_row(site.latitude)
        column = self._longitude_to_column(site.longitude)

        return GridPoint(self, column, row)

    def __iter__(self):
        for row in range(0, self.rows):
            for col in range(0, self.columns):
                point = GridPoint(self, col, row)
                yield point

    def centers(self):
        """
        Return the set of sites defining the center of
        the cells contained in this grid.
        """

        return [point.site for point in self]


class Site(nhlib_geo.Point):
    """Site is a dictionary-keyable point"""

    def __init__(self, longitude, latitude, depth=0.0):
        nhlib_geo.Point.__init__(
            self, round_float(longitude), round_float(latitude), depth=depth)

        self.point = geometry.Point(self.longitude, self.latitude)

    @property
    def coords(self):
        """Return a tuple with the coordinates of this point"""
        return (self.longitude, self.latitude)

    def __eq__(self, other):
        """
        Compare lat and lon values to determine equality.

        :param other: another Site
        :type other: :py:class:`openquake.shapes.Site`
        """
        return (self.longitude == other.longitude
                and self.latitude == other.latitude
                and self.depth == other.depth)

    def __ne__(self, other):
        return not self == other

    def equals(self, other):
        """Verbose wrapper around =="""
        return self == other

    def hash(self):
        """Needed e.g. for comparing dictionaries whose keys are sites."""
        return self.__hash__()

    def __hash__(self):
        return hash(
            hashlib.md5(
                repr((self.longitude, self.latitude, self.depth))).hexdigest())

    def __cmp__(self, other):
        return self.hash() == other.hash()


class Field(object):
    """Uses a 2 dimensional numpy array to store a field of values."""

    def __init__(self, field=None, rows=1, cols=1):
        if field is not None:
            self.field = field
        else:
            self.field = zeros((rows, cols))

    def get(self, row, col):
        """ Return the value at self.field[row][col]
            :param row
            :param col
        """
        try:
            return self.field[row][col]
        except IndexError:
            print "Field with shape [%s] doesn't have value at [%s][%s]" % (
                self.field.shape, row, col)

    @classmethod
    def from_json(cls, json_str, grid=None):
        """Construct a field from a serialized version in
        json format."""
        assert grid
        as_dict = json.JSONDecoder().decode(json_str)
        return cls.from_dict(as_dict, grid=grid)

    @classmethod
    def from_dict(cls, values, transform=math.exp, grid=None):
        """Construct a field from a dictionary.
        """
        assert grid
        assert grid.cell_size
        field = zeros((grid.rows, grid.columns))

        for _key, field_site in values.items():
            point = grid.point_at(
                Site(field_site['lon'], field_site['lat']))
            field[point.row][point.column] = transform(
                    float(field_site['mag']))

        return cls(field)


class FieldSet(object):
    """ An iterator for a set of fields """

    def __init__(self, as_dict, grid):
        assert grid
        self.grid = grid
        self.fields = as_dict.values()[0]  # NOTE: There's a junk wrapper

    @classmethod
    def from_json(cls, json_str, grid=None):
        """ Construct a field set from a serialized version in json format """
        assert grid
        as_dict = json.JSONDecoder().decode(json_str)
        return cls(as_dict, grid=grid)

    def __iter__(self):
        """Pop off the fields sequentially"""
        for field in self.fields.values():
            yield Field.from_dict(field, grid=self.grid)


def multipoint_ewkt_from_coords(coords):
    '''
    Convert a string list of coordinates to SRS 4326 MULTIPOINT EWKT.

    For more information about EWKT, see:
    http://en.wikipedia.org/wiki/Well-known_text

    NOTE: Input coordinates are expected in the order (lat, lon). The ordering
    for SRS 4326 is (lon, lat).

    NOTE 2: All coordinate values will be rounded using
    :func:`openquake.utils.round_float`

    >>> multipoint_ewkt_from_coords("38.113, -122.0, 38.113, -122.114")
    'SRID=4326;MULTIPOINT((-122.0 38.113), (-122.114 38.113))'
    '''
    coord_list = [round_float(x) for x in coords.split(",")]
    points = ['(%s %s)' % (coord_list[i + 1], coord_list[i]) for i in
              xrange(0, len(coord_list), 2)]

    ewkt = 'SRID=4326;MULTIPOINT(%s)'
    ewkt %= ', '.join(points)

    return ewkt


def polygon_ewkt_from_coords(coords):
    '''
    Convert a string list of coordinates to SRS 4326 POLYGON EWKT.

    For more information about EWKT, see:
    http://en.wikipedia.org/wiki/Well-known_text

    NOTE: Input coordinates are expected in the order (lat, lon). The ordering
    for SRS 4326 is (lon, lat).

    NOTE 2: All coordinate values will be rounded using
    :func:`openquake.utils.round_float`

    >>> polygon_ewkt_from_coords(
    ...     "38.113, -122.0, 38.113, -122.114, 38.111, -122.57")
    'SRID=4326;POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, \
-122.0 38.113))'
    '''
    coord_list = [round_float(x) for x in coords.split(",")]
    vertices = ['%s %s' % (coord_list[i + 1], coord_list[i]) for i in
                xrange(0, len(coord_list), 2)]

    ewkt = 'SRID=4326;POLYGON((%s, %s))'
    # The polygon needs to form a closed loop, so the first & last coord must
    # be the same:
    ewkt %= (', '.join(vertices), vertices[0])

    return ewkt


def hdistance(lat1, lon1, lat2, lon2):
    """Compute the great circle surface distance between two points
    using the Haversine formula.

    :param lat1, lon1: first point coordinates
    :param lat2, lon2: second point coordinates
    :rtype: float
    """

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    lon1 = radians(lon1)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (sin(dlat / 2)) ** 2 + cos(lat1) * cos(lat2) * (sin(dlon / 2.0)) ** 2
    c = 2.0 * arctan2(sqrt(a), sqrt(1.0 - a))

    # earth's mean radius
    return 6371.0072 * c
