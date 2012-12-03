# Copyright (c) 2010-2012, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.

"""
General utility functions for NRML.
"""

import numpy

_LINESTRING_FMT = 'LINESTRING(%s)'
_POLYGON_FMT = 'POLYGON((%s))'


def _group_point_coords(coords, dims):
    """
    Given a 1D `list` of coordinates, group them into blocks of points with a
    block size equal to ``dims``, return a 2D `list`.

    :param list coords:
        `list` of coords, as `str` or `float` values.
    :param int dims:
        Number of dimensions for the geometry (typically 2 or 3).
    """
    coords = [str(x) for x in coords]
    return [coords[i:i + dims] for i in xrange(0, len(coords), dims)]


def _make_wkt(fmt, points):
    """
    Given a format string and a `list` of point pairs or triples, generate a
    WKT representation of the geometry.

    :param str fmt:
        Format string for the desired type of geometry to represent with WKT.
    :param points:
        Sequence of point pairs or triples, as `list` or `tuple` objects.
    """
    wkt = fmt % ', '.join(
        [' '.join(pt) for pt in points])
    return wkt


def coords_to_poly_wkt(coords, dims):
    """
    Given a 1D list of coordinates and the desired number of dimensions,
    generate POLYGON WKT.

    :param list coords:
        `list` of coords, as `str` or `float` values.
    :param int dims:
        Number of dimensions for the geometry (typically 2 or 3).
    """
    points = _group_point_coords(coords, dims)
    # Form a closed loop:
    points.append(points[0])

    return _make_wkt(_POLYGON_FMT, points)


def coords_to_linestr_wkt(coords, dims):
    """
    Given a 1D list of coordinates and the desired number of dimensions,
    generate LINESTRING WKT.

    :param list coords:
        `list` of coords, as `str` or `float` values.
    :param int dims:
        Number of dimensions for the geometry (typically 2 or 3).
    """
    points = _group_point_coords(coords, dims)

    return _make_wkt(_LINESTRING_FMT, points)


def ndenumerate(arr):
    """
    Functions much like the `enumerate` built-in, except that it yield pairs of
    `(indices, value)`, where `value` is each array value in sequence and
    `indices` is a tuple of multi-dimensional indices (with a length equal to
    the number of dimensions).

    An example: Consider a 2x3x4 array. The indices yielded for this array will
    be the following:

    * (0, 0, 0)
    * (0, 0, 1)
    * (0, 0, 2)
    * (0, 0, 3)
    * (0, 1, 0)
    * (0, 1, 1)
    * (0, 1, 2)
    * (0, 1, 3)
    * (0, 2, 0)
    * ...
    * (1, 1, 3)
    * (1, 2, 0)
    * (1, 2, 1)
    * (1, 2, 2)
    * (1, 2, 3)

    .. note::
        These index tuples can be used to retrieve items by index from a
        multi-dimensional numpy array, like so: ``arr[(1,2,3)]``.

    :param arr:
        N-dimensional numpy array.
    """
    if arr.ndim == 1:
        for i, val in enumerate(arr):
            yield (i,), val
    else:
        for flat_idx, val in enumerate(arr.flatten()):
            indices = []

            # for each value, find the multi-d index
            # this involves looping over the dimensions and doing some math to
            # figure which bin the value belongs too for a given axis
            for i in xrange(arr.ndim - 1):
                dims_tail = numpy.array(arr.shape[i + 1:])
                divisor = dims_tail.prod()
                # record the ith index
                indices.append(flat_idx / divisor)
                # reduce to find the index for the next dim
                flat_idx %= divisor

                if len(dims_tail) == 1:
                    # if there is only 1 dim left, mod to get the last index
                    indices.append(flat_idx % dims_tail[0])
                    # and we're done
                    # NOTE: If the loop is set up correctly, we shouldn't need
                    # to break; but we expect to break here, so we might as
                    # well be explicit about it.
                    break

            yield tuple(indices), val
