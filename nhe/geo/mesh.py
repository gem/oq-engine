"""
Module :mod:`nhe.geo.mesh` defines classes :class:`Mesh` and its subclass
:class:`RectangularMesh`.
"""
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
        # here the same approach as in :meth:`nhe.geo.point.Point.distance`
        # is used. we find the great circle distance between the target
        # point and each point of the mesh, independently calculate
        # the vertical distance (just subtracting values) and combine
        # these distances using Pythagoras theorem.
        target_lons = numpy.repeat(point.longitude, len(self))
        target_lats = numpy.repeat(point.latitude, len(self))
        _, _, hor_distances = geo_utils.GEOD.inv(
            self.lons.flatten(), self.lats.flatten(), target_lons, target_lats
        )
        if self.depths is None:
            min_hor_distance = numpy.min(hor_distances) * 1e-3
            if point.depth == 0:
                # mesh and point have no depth, the actual distance
                # is the horizontal one
                return min_hor_distance
            else:
                # mesh is lying on earth surface and point has some depth
                return (min_hor_distance ** 2 + point.depth ** 2) ** 0.5
        elif point.depth == 0:
            # point is lying on earth surface and the mesh is below
            vert_distances = self.depths
        else:
            # both point and mesh are below earth surface
            vert_distances = self.depths - point.depth
        vert_distances = vert_distances.flatten()
        hor_distances *= 1e-3
        return numpy.min(hor_distances ** 2 + vert_distances ** 2) ** 0.5


class RectangularMesh(Mesh):
    """
    A specification of :class:`Mesh` that requires coordinate arrays
    to be two-dimensional.

    Rectangular mesh is meant to represent not just an unordered collection
    of points but rather a sort of table of points, where index of the point
    in a mesh is related to it's position with respect to neighbouring points.
    """
    def __init__(self, lons, lats, depths):
        super(RectangularMesh, self).__init__(lons, lats, depths)
        assert lons.ndim == 2

    @classmethod
    def from_points_list(cls, points):
        """
        Create a rectangular mesh object from a list of lists of points.
        Lists in a list are supposed to have the same length.

        :param point:
            List of lists of :class:`~nhe.geo.point.Point` objects.
        """
        assert points and points[0]
        lons = numpy.zeros((len(points), len(points[0])), dtype=float)
        lats = lons.copy()
        depths = lons.copy()
        num_cols = len(points[0])
        for i, row in enumerate(points):
            assert len(row) == num_cols
            for j, point in enumerate(row):
                lons[i][j] = point.longitude
                lats[i][j] = point.latitude
                depths[i][j] = point.depth
        if not depths.any():
            depths = None
        return cls(lons, lats, depths)

    def _get_bounding_mesh(self, with_depths=True):
        """
        Create and return a :class:`Mesh` object that contains a subset
        of points of this mesh. Only those points that lie on the borders
        of the rectangular mesh are included in the result one.

        :param with_depths:
            If set ``False`` the new mesh will have depths array
            set to ``None``.
        """
        if self.depths is None:
            with_depths = False

        if 1 in self.lons.shape:
            # the original mesh either has one row or one column of points.
            # the result mesh should have the same points.
            return Mesh(self.lons.flatten(), self.lats.flatten(),
                        self.depths.flatten() if with_depths else None)

        # we need to perform the same operations on all three coordinate
        # components (lons, lats and depths).
        components_bounding = []
        components_all = [self.lons, self.lats]
        if with_depths:
            components_all.append(self.depths)
        for coords in components_all:
            transposed = coords.transpose()
            # the resulting coordinates are composed of four parts:
            components_bounding.append(numpy.concatenate((
                # the first row,
                coords[0],
                # the last column (excluding two corner points),
                transposed[-1][1:-1],
                # the last row (in backward direction),
                coords[-1][::-1],
                # and the first column (backwards, excluding corner points).
                transposed[0][-2:0:-1]
            )))
        if not with_depths:
            components_bounding.append(None)
        return Mesh(*components_bounding)

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
        if mesh_2d.contains(point_2d) or mesh_2d.distance(point_2d) < 500:
            # if the point is closer than half km to the mesh, or lies
            # inside, return zero distance.
            return 0
        else:
            return bounding_mesh.get_min_distance(Point(point.longitude,
                                                        point.latitude))

    def get_middle_point(self):
        """
        Return the middle point of the mesh.

        :returns:
            An instance of :class:`~nhe.geo.point.Point`.

        The middle point is taken from the middle row and a middle column
        of the mesh if there are odd number of both. Otherwise the geometric
        mean point of two or four middle points.
        """
        num_rows, num_cols = self.lons.shape
        mid_row = num_rows // 2
        depth = 0
        if num_rows & 1 == 1:
            # there are odd number of rows
            mid_col = num_cols // 2
            if num_cols & 1 == 1:
                # odd number of columns, we can easily take
                # the middle point
                if self.depths is not None:
                    depth = self.depths[mid_row][mid_col]
                return Point(self.lons[mid_row][mid_col],
                             self.lats[mid_row][mid_col], depth)
            else:
                # even number of columns, need to take two middle
                # points on the middle row
                lon1, lon2 = self.lons[mid_row][mid_col - 1 : mid_col + 1]
                lat1, lat2 = self.lats[mid_row][mid_col - 1 : mid_col + 1]
                if self.depths is not None:
                    depth1 = self.depths[mid_row][mid_col - 1]
                    depth2 = self.depths[mid_row][mid_col]
        else:
            # there are even number of rows. take the row just above
            # and the one just below the middle and find middle point
            # of each
            submesh1 = self[mid_row - 1 : mid_row]
            submesh2 = self[mid_row : mid_row + 1]
            p1, p2 = submesh1.get_middle_point(), submesh2.get_middle_point()
            lon1, lat1, depth1 = p1.longitude, p1.latitude, p1.depth
            lon2, lat2, depth2 = p2.longitude, p2.latitude, p2.depth

        # we need to find the middle between two points
        if self.depths is not None:
            depth = (depth1 + depth2) / 2.0
        lon, lat = geo_utils.get_middle_point(lon1, lat1, lon2, lat2)
        return Point(lon, lat, depth)
