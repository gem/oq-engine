# Copyright (c) 2010-2013, GEM Foundation.
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

################### string manipulation routines for NRML ####################

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
