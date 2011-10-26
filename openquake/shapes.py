# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""Collection of base classes for processing spatially-related data."""

import hashlib
import json
import math
import numpy

from itertools import izip
from numpy import zeros
from numpy import empty
from numpy import allclose
from numpy import sin, cos, arctan2, sqrt, radians

from shapely import geometry
from scipy.interpolate import interp1d

from openquake import flags
from openquake import java
from openquake.utils import round_float

FLAGS = flags.FLAGS

LineString = geometry.LineString  # pylint: disable=C0103
Point = geometry.Point            # pylint: disable=C0103


class Region(object):
    """A container of polygons, used for bounds checking"""

    def __init__(self, polygon):
        self._grid = None
        # TODO(JMC): Make this a multipolygon instead?
        self.polygon = polygon
        self.cell_size = 0.1

    @classmethod
    def from_coordinates(cls, coordinates):
        """
        Build a region from a list of polygon coordinates.

        :param coordinates: List of 2-tuples (lon, lat). Example::
            [(-118.25, 34.07), (-118.22, 34.07), (-118.22, 34.04),
             (-118.25, 34.04)]

        :returns: :py:class:`openquake.shapes.Region` instance
        """

        # Constrain the precision for the coordinates:
        coordinates = \
            [(round_float(pt[0]), round_float(pt[1])) for pt in coordinates]
        polygon = geometry.Polygon(coordinates)
        return cls(polygon)

    @classmethod
    def from_simple(cls, top_left, bottom_right):
        """
        Build a rectangular region from two corner points (top left, bottom
        right).

        :param top_left: tuple of two floats (longitude, latitude)
        :param top_right: tuple of two floats (longitude, latitude)

        :returns: :py:class:`openquake.shapes.Region` instance
        """
        points = [top_left,
                  (top_left[0], bottom_right[1]),
                  bottom_right,
                  (bottom_right[0], top_left[1])]

        return cls.from_coordinates(points)

    @property
    def bounds(self):
        """Returns a bounding box containing the whole region"""
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
        """Returns a proxy interface that maps lat/lon
        to col/row based on a specific cellsize. Proxy is
        also iterable."""
        if not self._grid:
            if not self.cell_size:
                raise Exception(
                    "Can't generate grid without cell_size being set")
            self._grid = Grid(self, self.cell_size)
        return self._grid

    @property
    def sites(self):
        """ Returns a list of sites created from iterating over self """
        sites = []

        for site in self:
            sites.append(site)

        return sites

    def __iter__(self):
        if not self.cell_size:
            raise Exception(
                "Can't generate grid without cell_size being set")
        for gridpoint in self.grid:
            yield gridpoint.site


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
        """Ugly hashing function
        TODO(jmc): Fixme"""
        return self.__hash__()

    def __repr__(self):
        return str(self.__hash__())

    def __hash__(self):
        #, int(self.grid.cell_size)
        return self.column * 1000000000 + self.row

    def __str__(self):
        return self.__repr__()


class BoundsException(Exception):
    """Point is outside of region"""
    pass


class Grid(object):
    """Grid is a proxy interface to Region, which translates
    lat/lon to col/row"""

    def __init__(self, region, cell_size):
        self.region = region
        self.cell_size = cell_size
        self.lower_left_corner = self.region.lower_left_corner
        self.columns = self._longitude_to_column(
                    self.region.upper_right_corner.longitude) + 1
        self.rows = self._latitude_to_row(
                    self.region.upper_right_corner.latitude) + 1

    def check_site(self, site):
        """Confirm that the site is contained by the region"""
        return self.check_point(site.point)

    def check_point(self, point):
        """ Confirm that the point is within the polygon
        underlying the gridded region"""
        if (self.region.polygon.contains(point)):
            return True
        if self.region.polygon.touches(point):
            return True
        raise BoundsException("Point is not on the Grid")

    def check_gridpoint(self, gridpoint):
        """Confirm that the point is contained by the region"""
        point = Point(round_float(self._column_to_longitude(gridpoint.column)),
                      round_float(self._row_to_latitude(gridpoint.row)))
        return self.check_point(point)

    def _latitude_to_row(self, latitude):
        """Calculate row from latitude value"""
        latitude_offset = math.fabs(latitude - self.lower_left_corner.latitude)
        return int(round(latitude_offset / self.cell_size))

    def _row_to_latitude(self, row):
        """Determine latitude from given grid row"""
        return self.lower_left_corner.latitude + ((row) * self.cell_size)

    def _longitude_to_column(self, longitude):
        """Calculate column from longitude value"""
        longitude_offset = longitude - self.lower_left_corner.longitude
        return int(round(longitude_offset / self.cell_size))

    def _column_to_longitude(self, column):
        """Determine longitude from given grid column"""
        return self.lower_left_corner.longitude + ((column) * self.cell_size)

    def point_at(self, site):
        """Translates a site into a matrix bidimensional point."""
        self.check_site(site)
        row = self._latitude_to_row(site.latitude)
        column = self._longitude_to_column(site.longitude)
        return GridPoint(self, column, row)

    def site_at(self, gridpoint):
        """Construct a site at the given grid point"""
        return Site(self._column_to_longitude(gridpoint.column),
                             self._row_to_latitude(gridpoint.row))

    def __iter__(self):
        for row in range(0, self.rows):
            for col in range(0, self.columns):
                try:
                    point = GridPoint(self, col, row)
                    self.check_gridpoint(point)
                    yield point
                except BoundsException:
                    print "Point (col %s row %s) at %s %s isnt on grid" % \
                        (col, row, point.site.longitude, point.site.latitude)


def c_mul(val_a, val_b):
    """Ugly method of hashing string to integer
    TODO(jmc): Get rid of points as dict keys!"""
    return eval(hex((long(val_a) * val_b) & 0xFFFFFFFFL)[:-1])


class Site(object):
    """Site is a dictionary-keyable point"""

    def __init__(self, longitude, latitude):
        longitude = round_float(longitude)
        latitude = round_float(latitude)
        self.point = geometry.Point(longitude, latitude)

    @property
    def coords(self):
        """Return a tuple with the coordinates of this point"""
        return (self.longitude, self.latitude)

    @property
    def longitude(self):
        """Point x value is longitude"""
        return self.point.x

    @property
    def latitude(self):
        """Point y value is latitude"""
        return self.point.y

    def __eq__(self, other):
        """
        Compare lat and lon values to determine equality.

        :param other: another Site
        :type other: :py:class:`openquake.shapes.Site`
        """
        return self.longitude == other.longitude \
            and self.latitude == other.latitude

    def __ne__(self, other):
        return not self == other

    def equals(self, other):
        """Verbose wrapper around =="""
        return self == other

    def __hash__(self):
        return hash(
            hashlib.md5(repr((self.longitude, self.latitude))).hexdigest())

    def to_java(self):
        """Converts to a Java Site object"""
        jpype = java.jvm()
        loc_class = jpype.JClass("org.opensha.commons.geo.Location")
        site_class = jpype.JClass("org.opensha.commons.data.Site")
        # TODO(JMC): Support named sites?
        return site_class(loc_class(self.latitude, self.longitude))

    def __cmp__(self, other):
        return self.hash() == other.hash()

    def __repr__(self):
        return "Site(%s, %s)" % (self.longitude, self.latitude)

    def __str__(self):
        return self.__repr__()


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


def range_clip(val, val_range):
    """
    'Clip' a value (or sequence of values) to the
    specified range.

    Consider the example IML range [0.005, 0.007, 0.009].

    If the input IML value is less than the min value (0.005), return the
    min value.

    If the input IML value is greater than the max value (0.009), return
    the max value.

    Otherwise, the IML will not change.

    :param val: numeric value(s) to clip
    :type val: float, list/tuple of floats, or :py:class:`numpy.ndarray` of
        floats
    :param val_range: This is the range we 'clip' the input value(s) to. The
        range values should be arranged in ascending order with no duplicates.
        The length of the range must be at least 2 elements.
    :type val_range: 1-dimensional :py:class:`numpy.ndarray`

    :returns: Clipped value(s).
        If the input type is a single value, return a numpy numeric type (such
        as numpy.float64).
        If the input val is a sequence (list, tuple or
        :py:class:`numpy.ndarray`), return a :py:class:`numpy.ndarray` of
        clipped values.
    """
    assert len(val_range) >= 2, "val_range must contain at least 2 elements"
    assert list(val_range) == sorted(set(val_range)), \
        "val_range must be arranged in ascending order with no duplicates"

    if isinstance(val, (list, tuple, numpy.ndarray)):
        # convert to numpy.array so we can use numpy.putmask:
        val = numpy.array(val)

        # clip low values:
        numpy.putmask(val, val < val_range[0], val_range[0])

        # clip high values:
        numpy.putmask(val, val > val_range[-1], val_range[-1])

    else:
        # should be a single (float) value
        if val < val_range[0]:
            val = val_range[0]
        elif val > val_range[-1]:
            val = val_range[-1]

    return val


class Curve(object):
    """This class defines a curve (discrete function)
    used in the risk domain."""

    @classmethod
    def from_json(cls, json_str):
        """Construct a curve from a serialized version in
        json format."""
        as_dict = json.JSONDecoder().decode(json_str)
        return cls.from_dict(as_dict)

    @classmethod
    def from_dict(cls, values):
        """Construct a curve from a dictionary.

        The dictionary keys can be unordered and of
        whatever type can be converted to float with float().
        """

        data = []

        for key, val in values.items():
            data.append((float(key), val))

        return cls(data)

    def __init__(self, values):
        """Construct a curve from a sequence of tuples.

        The value on the first position of the tuple is the x value,
        the value(s) on the second position is the y value(s). This class
        supports multiple y values for the same x value, for example:

        Curve([(0.1, 1.0), (0.2, 2.0)]) # single y value
        Curve([(0.1, (1.0, 0.5)), (0.2, (2.0, 0.5))]) # multiple y values

        You can also pass lists instead of tuples, like:

        Curve([(0.1, [1.0, 0.5]), (0.2, [2.0, 0.5])])
        """

        # sort the values on x axis
        values = sorted(values, key=lambda data: data[0])

        elements = len(values)
        self.x_values = empty(elements)
        self.y_values = empty(elements)

        if elements and type(values[0][1]) in (tuple, list):
            self.y_values = empty((elements, len(values[0][1])))

        for index, (key, val) in enumerate(values):
            self.x_values[index] = key
            self.y_values[index] = val

    def __eq__(self, other):
        return allclose(self.x_values, other.x_values) \
                and allclose(self.y_values, other.y_values)

    def __str__(self):
        return "X Values: %s\nY Values: %s" % (
                self.x_values.__str__(), self.y_values.__str__())

    def rescale_abscissae(self, value):
        """Return a new curve with each abscissa value multiplied
        by the value passed as parameter."""

        result = Curve(())
        result.x_values = self.x_values * value
        result.y_values = self.y_values

        return result

    @property
    def abscissae(self):
        """Return the abscissa values of this curve in ascending order."""
        return self.x_values

    @property
    def is_empty(self):
        """Return true if this curve is empty, false otherwise."""
        return self.abscissae.size == 0

    @property
    def ordinates(self):
        """Return the ordinate values of this curve in ascending order
        of the corresponding abscissa values."""
        return self.y_values

    @property
    def is_multi_value(self):
        """Return true if this curve describes multiple ordinate values,
        false otherwise."""
        return self.y_values.ndim > 1

    def ordinate_for(self, x_value, y_index=0):
        """
            Return the y value corresponding to the given x value.
            interp1d parameters can be a list of x_values, y_values
            this is very useful to speed up the computation and feed
            "directly" numpy
        """

        x_value = range_clip(x_value, self.x_values)

        y_values = self.y_values

        if self.y_values.ndim > 1:
            y_values = self.y_values[:, y_index]

        return interp1d(self.x_values, y_values)(x_value)

    def abscissa_for(self, y_value):
        """Return the x value corresponding to the given y value."""

        # inverting the function
        inverted_func = [(ordinate, x_value) for ordinate, x_value in
                zip(self.ordinate_for(self.abscissae), self.abscissae)]

        return Curve(inverted_func).ordinate_for(y_value)

    def ordinate_out_of_bounds(self, y_value):
        """Check if the given value is outside the Y values boundaries."""
        ordinates = list(self.ordinates)
        ordinates.sort()

        return y_value < ordinates[0] or y_value > ordinates[-1]

    def to_json(self):
        """Serialize this curve in json format."""
        as_dict = {}

        for index, x_value in enumerate(self.x_values):
            if self.y_values.ndim > 1:
                as_dict[str(x_value)] = list(self.y_values[index])
            else:
                as_dict[str(x_value)] = self.y_values[index]

        return json.JSONEncoder().encode(as_dict)


class VulnerabilityFunction(object):
    """
    This class represents a vulnerability fuction.

    A vulnerability function has IMLs (Intensity Measure Levels) as
    X values and MLRs, CVs (Mean Loss Ratio and Coefficent of Variation)
    as Y values.
    """

    def __init__(self, imls, loss_ratios, covs):
        """
        :param imls: Intensity Measure Levels for the vulnerability function.
            All values must be >= 0.0.
        :type imls: list of floats; values must be arranged in ascending order
            with no duplicates
        :param loss_ratios: Loss ratio values, where 0.0 <= value <= 1.0.
        :type loss_ratios: list of floats, equal in length to imls
        :param covs: Coefficients of Variation. All values must be >= 0.0.
        :type covs: list of floats, equal in length to imls
        """
        self._imls = imls
        self._loss_ratios = loss_ratios
        self._covs = covs

        # Check for proper IML ordering:
        assert self._imls == sorted(set(self._imls)), \
            "IML values must be in ascending order with no duplicates."

        # Check for proper IML values (> 0.0).
        assert all(x >= 0.0 for x in self._imls), \
            "IML values must be >= 0.0."

        # Check CoV and loss ratio list lengths:
        assert len(self._covs) == len(self._imls), \
            "CoV list should be the same length as the IML list."
        assert len(self._loss_ratios) == len(self._imls), \
            "Loss ratio list should be the same length as the IML list."

        # Check for proper CoV values (>= 0.0):
        assert all(x >= 0.0 for x in self._covs), \
            "CoV values must be >= 0.0."

        # Check for proper loss ratio values (0.0 <= value <= 1.0):
        assert all(x >= 0.0 and x <= 1.0 for x in self._loss_ratios), \
            "Loss ratio values must be in the interval [0.0, 1.0]."

    def __eq__(self, other):
        """
        Compares IML, loss ratio, and CoV values to determine equality.
        """
        if not isinstance(other, VulnerabilityFunction):
            return False
        return allclose(self.imls, other.imls) \
            and allclose(self.loss_ratios, other.loss_ratios) \
            and allclose(self.covs, other.covs)

    @property
    def imls(self):
        """
        IML values as a numpy.array.
        """
        return numpy.array(self._imls)

    @property
    def loss_ratios(self):
        """
        Loss ratios as a numpy.array.
        """
        return numpy.array(self._loss_ratios)

    @property
    def covs(self):
        """
        Coeffecicients of Variation as a numpy.array.
        """
        return numpy.array(self._covs)

    @property
    def is_empty(self):
        """
        True if there are no IML values in the function.
        """
        return len(self.imls) == 0

    def loss_ratio_for(self, iml):
        """
        Given 1 or more IML values, interpolate the corresponding loss ratio
        value(s) on the curve.

        Input IML value(s) is/are clipped to IML range defined for this
        vulnerability function.

        :param iml: IML value
        :type iml: float (single value), list of floats, or
            :py:class:`numpy.ndarray` of floats

        :returns: :py:class:`numpy.ndarray` containing a number of interpolated
            values equal to the size of the input (1 or many)
        """
        iml = range_clip(iml, self.imls)

        return interp1d(self.imls, self.loss_ratios)(iml)

    def cov_for(self, iml):
        """
        Given 1 or more IML values, interpolate the corresponding Coefficient
        of Variation value(s) on the curve.

        Input IML value(s) is/are clipped to IML range defined for this
        vulnerability function.

        :param iml: IML value
        :type iml: float (single value), list of floats, or
            :py:class:`numpy.ndarray` of floats

        :returns: :py:class:`numpy.ndarray` containing a number of interpolated
            values equal to the size of the input (1 or many)
        """
        iml = range_clip(iml, self.imls)

        return interp1d(self.imls, self.covs)(iml)

    def __iter__(self):
        """Iterate on the values of this function, returning triples
        in the form of (iml, mean loss ratio, cov)."""
        return izip(self.imls, self.loss_ratios, self.covs)

    def to_json(self):
        """
        Serialize this curve in JSON format.
        Given the following sample data::
            imls = [0.005, 0.007]
            loss_ratios = [0.1, 0.3]
            covs = [0.2, 0.4]

        the output will be a JSON string structured like so::
            {'0.005': [0.1, 0.2],
             '0.007': [0.3, 0.4]}
        """
        as_dict = {}

        for iml, loss_ratio, cov in self:
            as_dict[str(iml)] = [loss_ratio, cov]

        return json.JSONEncoder().encode(as_dict)

    @classmethod
    def from_dict(cls, vuln_func_dict):
        """
        Construct a VulnerabiltyFunction from a dictionary.

        The dictionary keys can be unordered and of
        whatever type can be converted to float with float().
        :param vuln_func_dict: A dictionary of [loss ratio, CoV] pairs, keyed
            by IMLs.
            The IML keys can be numbers represented as either a string or
            float.
            Example::
                {'0.005': [0.1, 0.2],
                 '0.007': [0.3, 0.4],
                 0.0098: [0.5, 0.6]}

        :type vuln_func_dict: dict

        :returns: :py:class:`openquake.shapes.VulnerabilityFunction` instance
        """
        # flatten out the dict and convert keys to floats:
        data = [(float(iml), lr_cov) for iml, lr_cov in vuln_func_dict.items()]
        # sort the data (by iml) in ascending order:
        data = sorted(data, key=lambda x: x[0])

        imls = []
        loss_ratios = []
        covs = []

        for iml, (lr, cov) in data:
            imls.append(iml)
            loss_ratios.append(lr)
            covs.append(cov)

        return cls(imls, loss_ratios, covs)

    @classmethod
    def from_json(cls, json_str):
        """Construct a curve from a serialized version in
        json format.

        :returns: :py:class:`openquake.shapes.VulnerabilityFunction` instance
        """
        as_dict = json.JSONDecoder().decode(json_str)
        return cls.from_dict(as_dict)


EMPTY_CURVE = Curve(())
EMPTY_VULN_FUNCTION = VulnerabilityFunction([], [], [])


def multipoint_ewkt_from_coords(coords):
    '''
    Convert a string list of coordinates to SRS 4326 MULTIPOINT EWKT.

    For more information about EWKT, see:
    http://en.wikipedia.org/wiki/Well-known_text

    NOTE: Input coordinates are expected in the order (lat, lon). The ordering
    for SRS 4326 is (lon, lat).

    NOTE 2: All coordinate values will be rounded using
    :py:function:`openquake.utils.round_float`

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
    :py:function:`openquake.utils.round_float`

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
