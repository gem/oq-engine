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
Module :mod:`nhlib.geo.polygon` defines :class:`Polygon`.
"""
import numpy
import shapely.geometry

from nhlib.geo.mesh import Mesh
from nhlib.geo import geodetic
from nhlib.geo import _utils as utils


#: The distance measure of latitudinally- and longitudinally-extended
#: line resampling in kilometers. See :function:`get_resampled_coordinates`.
COORDINATE_DISCRETIZATION = 100


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

    def __init__(self, points):
        points = utils.clean_points(points)

        if not len(points) >= 3:
            raise ValueError('polygon must have at least 3 unique vertices')

        self.lons = numpy.array([float(point.longitude) for point in points])
        self.lats = numpy.array([float(point.latitude) for point in points])

        if utils.line_intersects_itself(self.lons, self.lats,
                                        closed_shape=True):
            raise ValueError('polygon perimeter intersects itself')

        self._bbox = None
        self._projection = None
        self._polygon2d = None

    def _init_polygon2d(self):
        """Spherical bounding box, projection, and Cartesian polygon are all
        cached to prevent redundant computations.

        If any of them are `None`, recalculate all of them.
        """
        if (self._polygon2d is None or self._projection is None
            or self._bbox is None):
            # resample polygon line segments:
            lons, lats = get_resampled_coordinates(self.lons, self.lats)

            # find the bounding box of a polygon in spherical coordinates:
            self._bbox = utils.get_spherical_bounding_box(lons, lats)

            # create a projection that is centered in a polygon center:
            self._projection = \
                utils.get_orthographic_projection(*self._bbox)

            # project polygon vertices to the Cartesian space and create
            # a shapely polygon object:
            xx, yy = self._projection(lons, lats)
            self._polygon2d = shapely.geometry.Polygon(zip(xx, yy))

    def contains(self, mesh):
        """Check for containment of a :class:`~nhlib.geo.mesh.Mesh` of points.

        Mesh coordinate values are in decimal degrees.

        :param mesh:
            :class:`nhlib.geo.mesh.Mesh` instance.
        :returns:
            Numpy array of `bool` values in the same shapes in the input
            coordinate arrays.
        """
        self._init_polygon2d()
        plons, plats = self._projection(mesh.lons, mesh.lats)

        result = numpy.empty(mesh.lons.shape, dtype=bool)

        for i in xrange(mesh.lons.size):
            contains = self._polygon2d.contains(
                shapely.geometry.Point(plons.item(i), plats.item(i))
            )
            result.itemset(i, contains)

        return result

    def discretize(self, mesh_spacing):
        """
        Get a mesh of uniformly spaced points inside the polygon area
        with distance of ``mesh_spacing`` km between.

        :returns:
            An instance of :class:`~nhlib.geo.mesh.Mesh` that holds
            the points data. Mesh is created with no depth information
            (all the points are on the Earth surface).
        """
        self._init_polygon2d()

        west, east, north, south = self._bbox

        lons = []
        lats = []

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
                x, y = self._projection(longitude, latitude)
                if self._polygon2d.contains(shapely.geometry.Point(x, y)):
                    lons.append(longitude)
                    lats.append(latitude)

                # move by mesh spacing along parallel...
                longitude, _, = geodetic.point_at(longitude, latitude,
                                                  90, mesh_spacing)
            # ... and by the same distance along meridian in outer one
            _, latitude = geodetic.point_at(west, latitude, 180, mesh_spacing)

        lons = numpy.array(lons)
        lats = numpy.array(lats)

        return Mesh(lons, lats, depths=None)


def get_resampled_coordinates(lons, lats):
    """
    Resample polygon line segments and return the coordinates of the new
    vertices. This limits distortions when projecting a polygon onto a
    spherical surface.

    Parameters define longitudes and latitudes of a point collection in the
    form of lists or numpy arrays.

    :return:
        A tuple of two numpy arrays: longitudes and latitudes
        of resampled vertices. The last point repeats the first one.
    """
    num_coords = len(lons)
    assert num_coords == len(lats)

    lons1 = numpy.array(lons)
    lats1 = numpy.array(lats)
    lons2 = numpy.concatenate((lons1[1:], lons1[0:1]))
    lats2 = numpy.concatenate((lats1[1:], lats1[0:1]))
    distances = geodetic.geodetic_distance(lons1, lats1, lons2, lats2)

    resampled_lons = [lons[0]]
    resampled_lats = [lats[0]]
    for i in xrange(num_coords):
        next_point = (i + 1) % num_coords
        lon1, lat1 = lons[i], lats[i]
        lon2, lat2 = lons[next_point], lats[next_point]

        # distance = geodetic.geodetic_distance(lon1, lat1, lon2, lat2)
        distance = distances[i]
        num_points = int(distance / COORDINATE_DISCRETIZATION) + 1
        if num_points >= 2:
            # We need to increase the resolution of this arc by adding new
            # points.
            new_lons, new_lats, _ = geodetic.npoints_between(
                lon1, lat1, 0, lon2, lat2, 0, num_points
            )
            resampled_lons.extend(new_lons[1:])
            resampled_lats.extend(new_lats[1:])
        else:
            resampled_lons.append(lon2)
            resampled_lats.append(lat2)
    # we don't cut off the last point so it repeats the first one.
    # shapely polygon is ok with that (we even save it from extra
    # work of copying the last point for us).
    return numpy.array(resampled_lons), numpy.array(resampled_lats)
