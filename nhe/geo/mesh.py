"""
Module :mod:`nhe.geo.mesh` defines :class:`Mesh`.
"""
import itertools

import numpy
import shapely.geometry

from nhe.geo.point import Point
from nhe.geo import _utils as geo_utils


class Mesh(object):
    """
    Mesh object represent a collection of points and provides the most
    efficient way of keeping those collections in memory.

    :param lons:
        A numpy array of longitude values of points. Array may be
        of arbitrary shape.
    :param lats:
        Numpy array of latitude values. The array must be of the same
        shape as ``lons``.
    :param depths:
        Either ``None``, which means that all points the mesh consists
        of are lying on the earth surface (have zero depth) or numpy
        array of the same shape as previous two.

    Mesh object can also be created from a collection of points, see
    :meth:`from_points_list`.
    """
    def __init__(self, lons, lats, depths):
        assert (isinstance(lons, numpy.ndarray)
                and isinstance(lats, numpy.ndarray)
                and (depths is None or isinstance(depths, numpy.ndarray)))
        assert ((lons.shape == lats.shape)
                and (depths is None or depths.shape == lats.shape))
        assert lons.size > 0
        self.lons = lons
        self.lats = lats
        self.depths = depths

    @classmethod
    def from_points_list(cls, points):
        """
        Create a mesh object from a collection of points.

        :param point:
            List of :class:`~nhe.geo.point.Point` objects.
        :returns:
            An instance of :class:`Mesh` with one-dimensional arrays
            of coordinates from ``points``.
        """
        lons = numpy.zeros(len(points), dtype=float)
        lats = lons.copy()
        depths = lons.copy()
        for i in xrange(len(points)):
            lons[i] = points[i].longitude
            lats[i] = points[i].latitude
            depths[i] = points[i].depth
        if not depths.any():
            # all points have zero depth, no need to waste memory
            depths = None
        return cls(lons, lats, depths)

    def __iter__(self):
        """
        Generate :class:`~nhe.geo.point.Point` objects the mesh is composed of.

        Coordinates arrays are processed sequentially (as if they were
        flattened).
        """
        lons = self.lons.flat
        lats = self.lats.flat
        if self.depths is not None:
            depths = self.depths.flat
            for i in xrange(self.lons.size):
                yield Point(lons[i], lats[i], depths[i])
        else:
            for i in xrange(self.lons.size):
                yield Point(lons[i], lats[i])

    def __getitem__(self, item):
        """
        Get a submesh of this mesh.

        :param item:
            Indexing is only supported by slices. Those slices are used
            to cut the portion of coordinates (and depths if it is available)
            arrays. These arrays are then used for creating a new mesh.
        :returns:
            A new object of the same type that borrows a portion of geometry
            from this mesh (doesn't copy the array, just references it).
        """
        assert (isinstance(item, slice) or
                (isinstance(item, (list, tuple))
                 and all(isinstance(subitem, slice) for subitem in item))), \
               '%s objects can only be indexed by slices' % type(self).__name__
        lons = self.lons[item]
        lats = self.lats[item]
        depths = None
        if self.depths is not None:
            depths = self.depths[item]
        return type(self)(lons, lats, depths)

    def __len__(self):
        """
        Return the number of points in the mesh.
        """
        return self.lons.size

    def get_min_distance(self, point):
        """
        Compute and return the minimum distance from the mesh to ``point``.

        :returns:
            Distance in km.

        Method doesn't make any assumptions on arrangement of the points
        and instead calculates the distance from each point of the mesh
        to the target point and returns the lowest found. Therefore,
        the method's time complexity grows linearly with the number
        of points in the mesh.
        """
        return min(point.distance(mesh_point) for mesh_point in self)


class RectangularMesh(Mesh):
    def __init__(self, lons, lats, depths):
        super(RectangularMesh, self).__init__(lons, lats, depths)
        assert lons.ndim == 2

    def _get_bounding_mesh(self, with_depths=True):
        if self.depths is None:
            with_depths = False
        depths = None

        if 1 in self.lons.shape:
            lons, lats = self.lons.flatten(), self.lats.flatten()
            if with_depths:
                depths = self.depths.flatten()
        else:
            num_points = sum(self.lons.shape) * 2 - 4
            transposed_lons = self.lons.transpose()
            lons = numpy.fromiter(itertools.chain(
                self.lons[0],
                transposed_lons[-1][1:-1],
                self.lons[-1][::-1],
                transposed_lons[0][-2:0:-1]
            ), dtype=float, count=num_points)
            transposed_lats = self.lats.transpose()
            lats = numpy.fromiter(itertools.chain(
                self.lats[0],
                transposed_lats[-1][1:-1],
                self.lats[-1][::-1],
                transposed_lats[0][-2:0:-1]
            ), dtype=float, count=num_points)
            if with_depths:
                transposed_depths = self.depths.transpose()
                depths = numpy.fromiter(itertools.chain(
                    self.depths[0],
                    transposed_depths[-1][1:-1],
                    self.depths[-1][::-1],
                    transposed_depths[0][-2:0:-1]
                ), dtype=float, count=num_points)
        return Mesh(lons, lats, depths)

    def get_joyner_boore_distance(self, point):
        """
        Compute and return Joyner-Boore distance to ``point``.
        Point's depth is ignored.

        :returns:
            Distance in km. Value is considered to be zero if ``point``
            lies inside the polygon enveloping the projection of the mesh.
        """
        bounding_mesh = self._get_bounding_mesh(with_depths=False)
        lons, lats = bounding_mesh.lons, bounding_mesh.lats
        proj = geo_utils.get_stereographic_projection(
            *geo_utils.get_spherical_bounding_box(lons, lats)
        )
        point_2d = shapely.geometry.Point(*proj(point.longitude,
                                                point.latitude))
        xx, yy = proj(lons, lats)
        mesh_2d = shapely.geometry.Polygon(
            numpy.array([xx, yy], dtype=float).transpose().copy()
        )
        if mesh_2d.contains(point_2d):
            return 0
        else:
            return bounding_mesh.get_min_distance(Point(point.longitude,
                                                        point.latitude))
