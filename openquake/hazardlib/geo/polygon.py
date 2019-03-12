# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.polygon` defines :class:`Polygon`.
"""
import numpy
import shapely.geometry
import shapely.wkt

from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo import geodetic
from openquake.hazardlib.geo import utils
from openquake.baselib.slots import with_slots

#: Polygon upsampling step for long edges, in kilometers.
#: See :func:`get_resampled_coordinates`.
UPSAMPLING_STEP_KM = 100


@with_slots
class Polygon(object):
    """
    Polygon objects represent an area on the Earth surface.

    :param points:
        The list of :class:`~openquake.hazardlib.geo.point.Point` objects
        defining the polygon vertices. The points are connected by great circle
        arcs in order of appearance. Polygon segment should not cross another
        polygon segment. At least three points must be defined.
    :raises ValueError:
        If ``points`` contains less than three unique points or if polygon
        perimeter intersects itself.
    """
    _slots_ = 'lons lats _bbox _projection _polygon2d'.split()
    _bbox = None

    def __init__(self, points):
        points = utils.clean_points(points)
        if len(points) < 3:
            raise ValueError('polygon must have at least 3 unique vertices')

        self.lons = numpy.array([float(point.longitude) for point in points])
        self.lats = numpy.array([float(point.latitude) for point in points])
        if utils.line_intersects_itself(self.lons, self.lats, closed_shape=1):
            raise ValueError('polygon perimeter intersects itself')

        self._projection = None
        self._polygon2d = None

    @property
    def wkt(self):
        """
        Generate WKT (Well-Known Text) to represent this polygon.
        """
        pairs = ['%s %s' % (lon, lat)
                 for lon, lat in zip(self.lons, self.lats)]
        # the polygon must form a closed loop; first and last coord pairs
        # are the same
        pairs.append(pairs[0])
        return 'POLYGON((%s))' % ', '.join(pairs)

    @classmethod
    def from_wkt(cls, wkt_string):
        """
        Create a polygon object from a WKT (Well-Known Text) string.

        :param wkt_string:
            A standard WKT polygon string.
        :returns:
            New :class:`Polygon` object.
        """
        # Avoid calling class' constructor
        polygon = object.__new__(cls)

        # Read WKT polygon and extract coordinates
        wkt_poly = shapely.wkt.loads(wkt_string)
        xx, yy = numpy.transpose(wkt_poly.exterior.coords)

        # Inflate polygon object
        polygon.lons = xx[:-1]
        polygon.lats = yy[:-1]
        polygon._projection = None
        polygon._polygon2d = None

        return polygon

    @classmethod
    def _from_2d(cls, polygon2d, proj):
        """
        Create a polygon object from a 2d polygon and a projection.

        :param polygon2d:
            Instance of ``shapely.geometry.Polygon``.
        :param proj:
            Projection object created
            by
            :class:`~openquake.hazardlib.geo.utils.OrthographicProjection`
            that was used to project ``polygon2d``. That projection
            will be used for projecting it back to get spherical
            coordinates from Cartesian ones.
        :returns:
            New :class:`Polygon` object. Note that spherical coordinates
            of that polygon do not get upsampled even for longer edges.
        """
        # avoid calling class' constructor
        polygon = object.__new__(cls)
        # project polygon2d back on the sphere
        # NOTE(LB): We use 'exterior' here in case the `polygon2d` has
        # interiors (holes) defined. In our use cases, we don't care about
        # polygon interiors, so we simply discard these exteriors.
        xx, yy = numpy.transpose(polygon2d.exterior.coords)
        # need to cut off the last point -- it repeats the first one
        polygon.lons, polygon.lats = proj(xx[:-1], yy[:-1], reverse=True)
        # initialize the instance (as constructor would do)
        polygon._bbox = utils.get_spherical_bounding_box(
            polygon.lons, polygon.lats)
        polygon._polygon2d = polygon2d
        polygon._projection = proj
        return polygon

    def get_bbox(self):
        """
        Returns a simple 2D bounding box from the extrema of lons and lats
        """
        min_lon, max_lon = self.lons.min(), self.lons.max()
        if utils.cross_idl(min_lon, max_lon):
            lons = self.lons % 360
            min_lon, max_lon = lons.min(), lons.max()
        return (min_lon, self.lats.min(), max_lon, self.lats.max())

    def _init_polygon2d(self):
        """
        Spherical bounding box, projection, and Cartesian polygon are all
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
            self._projection = utils.OrthographicProjection(*self._bbox)

            # project polygon vertices to the Cartesian space and create
            # a shapely polygon object:
            xx, yy = self._projection(lons, lats)
            self._polygon2d = shapely.geometry.Polygon(list(zip(xx, yy)))

    def dilate(self, dilation):
        """
        Extend the polygon to a specified buffer distance.

        .. note::
            In extreme cases where dilation of a polygon creates holes, thus
            resulting in a multi-polygon, we discard the holes and simply
            return the 'exterior' of the shape.

        :param dilation:
            Distance in km to extend polygon borders to.
        :returns:
            New :class:`Polygon` object with (in general) more vertices
            and border that is approximately ``dilation`` km far
            (measured perpendicularly to edges and circularly to vertices)
            from the border of original polygon.
        """
        assert dilation > 0, dilation
        self._init_polygon2d()
        newpoly2d = self._polygon2d.buffer(dilation)
        return self.__class__._from_2d(newpoly2d, self._projection)

    def intersects(self, mesh):
        """
        Check for intersection with each point of the ``mesh``.

        Mesh coordinate values are in decimal degrees.

        :param mesh:
            :class:`openquake.hazardlib.geo.mesh.Mesh` instance.
        :returns:
            Numpy array of `bool` values in the same shapes in the input
            coordinate arrays with ``True`` on indexes of points that
            lie inside the polygon or on one of its edges and ``False``
            for points that neither lie inside nor touch the boundary.
        """
        self._init_polygon2d()
        pxx, pyy = self._projection(mesh.lons, mesh.lats)
        return utils.point_to_polygon_distance(self._polygon2d, pxx, pyy) == 0

    def discretize(self, mesh_spacing):
        """
        Get a mesh of uniformly spaced points inside the polygon area
        with distance of ``mesh_spacing`` km between.

        :returns:
            An instance of :class:`~openquake.hazardlib.geo.mesh.Mesh` that
            holds the points data. Mesh is created with no depth information
            (all the points are on the Earth surface).
        """
        self._init_polygon2d()
        west, east, north, south = self._bbox
        lons, lats = [], []
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

        return Mesh(numpy.array(lons), numpy.array(lats), depths=None)


def get_resampled_coordinates(lons, lats):
    """
    Resample polygon line segments and return the coordinates of the new
    vertices. This limits distortions when projecting a polygon onto a
    spherical surface.

    Parameters define longitudes and latitudes of a point collection in the
    form of lists or numpy arrays.

    :return:
        A tuple of two numpy arrays: longitudes and latitudes
        of resampled vertices.
    """
    num_coords = len(lons)
    assert num_coords == len(lats)

    lons1 = numpy.array(lons)
    lats1 = numpy.array(lats)
    lons2 = numpy.concatenate((lons1[1:], lons1[:1]))
    lats2 = numpy.concatenate((lats1[1:], lats1[:1]))
    distances = geodetic.geodetic_distance(lons1, lats1, lons2, lats2)

    resampled_lons = [lons[0]]
    resampled_lats = [lats[0]]
    for i in range(num_coords):
        next_point = (i + 1) % num_coords
        lon1, lat1 = lons[i], lats[i]
        lon2, lat2 = lons[next_point], lats[next_point]
        distance = distances[i]
        num_points = int(distance / UPSAMPLING_STEP_KM) + 1
        if num_points >= 2:
            # We need to increase the resolution of this arc by adding new
            # points.
            new_lons, new_lats, _ = geodetic.npoints_between(
                lon1, lat1, 0, lon2, lat2, 0, num_points)
            resampled_lons.extend(new_lons[1:])
            resampled_lats.extend(new_lats[1:])
        else:
            resampled_lons.append(lon2)
            resampled_lats.append(lat2)

    # NB: we cut off the last point because it repeats the first one
    return numpy.array(resampled_lons[:-1]), numpy.array(resampled_lats[:-1])
