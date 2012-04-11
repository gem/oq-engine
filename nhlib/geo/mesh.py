# coding: utf-8
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
Module :mod:`nhlib.geo.mesh` defines classes :class:`Mesh` and its subclass
:class:`RectangularMesh`.
"""
import numpy
import shapely.geometry

from nhlib.geo.point import Point
from nhlib.geo import _utils as geo_utils


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
            List of :class:`~nhlib.geo.point.Point` objects.
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

    @property
    def shape(self):
        """
        Return the shape of this mesh.

        :returns:
            The shape of this mesh.
        :rtype:
            tuple in the following format (rows, columns)
        """
        return self.lons.shape

    def __iter__(self):
        """
        Generate :class:`~nhlib.geo.point.Point` objects the mesh is composed
        of.

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
        # here the same approach as in :meth:`nhlib.geo.point.Point.distance`
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
    A specification of :class:`Mesh` that requires coordinate numpy-arrays
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
            List of lists of :class:`~nhlib.geo.point.Point` objects.
        """
        assert points is not None and len(points) > 0 and len(points[0]) > 0, \
               'list of at least one non-empty list of points is required'
        lons = numpy.zeros((len(points), len(points[0])), dtype=float)
        lats = lons.copy()
        depths = lons.copy()
        num_cols = len(points[0])
        for i, row in enumerate(points):
            assert len(row) == num_cols, \
                   'lists of points are not of uniform length'
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

        If the original mesh is purely vertical (with point in all the
        rows different only by their depths), and ``with_depths == False``,
        the resulting bounding mesh is filtered from duplicates.

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

        # if depths are ignored and there is only one row (or the top row
        # is equal to last one), consider only that top row. this way
        # we avoid duplicating each point for purely vertical rectangular
        # meshes.
        if (not with_depths
            and (len(self.lons) == 1
                 or ((self.lons[0] == self.lons[-1]).all()
                     and (self.lats[0] == self.lats[-1]).all()))):
            return Mesh(self.lons[0], self.lats[0], None)

        # we need to perform the same operations on all three coordinate
        # components (lons, lats and depths).
        components_bounding = []
        components_all = [self.lons, self.lats]
        if with_depths:
            components_all.append(self.depths)
        for coords in components_all:
            # the resulting coordinates are composed of four parts:
            components_bounding.append(numpy.concatenate((
                # the first row,
                coords[0],
                # the last column (excluding two corner points),
                coords[1:-1, -1],
                # the last row (in backward direction),
                coords[-1][::-1],
                # and the first column (backwards, excluding corner points).
                coords[-2:0:-1, 0]
            )))
        if not with_depths:
            components_bounding.append(None)
        return Mesh(*components_bounding)

    def get_joyner_boore_distance(self, point):
        """
        Compute and return Joyner-Boore distance to ``point``.
        Point's depth is ignored.

        See :meth:`nhlib.geo.surface.BaseSurface.get_joyner_boore_distance`
        for definition of this distance.

        :returns:
            Distance in km. Value is considered to be zero if ``point``
            lies inside the polygon enveloping the projection of the mesh
            or on one of its edges.
        """
        bounding_mesh = self._get_bounding_mesh(with_depths=False)
        assert bounding_mesh.depths is None
        lons, lats = bounding_mesh.lons, bounding_mesh.lats
        proj = geo_utils.get_orthographic_projection(
            *geo_utils.get_spherical_bounding_box(lons, lats)
        )
        point_2d = shapely.geometry.Point(*proj(point.longitude,
                                                point.latitude))
        xx, yy = proj(lons, lats)
        mesh_2d = numpy.array([xx, yy], dtype=float).transpose().copy()
        if len(xx) == 2:
            mesh_2d = shapely.geometry.LineString(mesh_2d)
        elif len(xx) == 1:
            mesh_2d = shapely.geometry.Point(*mesh_2d)
        elif len(xx) > 2:
            mesh_2d = shapely.geometry.Polygon(mesh_2d)
        dist = mesh_2d.distance(point_2d)
        if dist < 500:
            # if the distance is below threshold of 500 kilometers, consider
            # the distance measured on the projection accurate enough.
            return dist
        else:
            # ... otherwise get the precise distance between bounding mesh
            # projection and the point projection using pure numerical way
            return bounding_mesh.get_min_distance(Point(point.longitude,
                                                        point.latitude))

    def get_middle_point(self):
        """
        Return the middle point of the mesh.

        :returns:
            An instance of :class:`~nhlib.geo.point.Point`.

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

    def get_mean_inclination_and_azimuth(self):
        """
        Calculate weighted average inclination and azimuth of the mesh surface.

        :returns:
            Tuple of two float numbers: inclination angle in a range [0, 90]
            and azimuth in range [0, 360) (in decimal degrees).

        The mesh is triangulated, the inclination and azimuth for each triangle
        is computed and average values weighted on each triangle's area
        are calculated. Azimuth is always defined in a way that inclination
        angle doesn't exceed 90 degree.
        """
        assert not 1 in self.lons.shape, (
            "inclination and azimuth are only defined for mesh of more than "
            "one row and more than one column of points"
        )

        if self.depths is not None:
            assert ((self.depths[1:] - self.depths[:-1]) >= 0).all(), (
                "get_mean_inclination_and_azimuth() requires next mesh row "
                "to be not shallower than the previous one"
            )

        points, along_azimuth, updip, diag = self.triangulate()

        # define planes that are perpendicular to each point's vector
        # as normals to those planes
        earth_surface_tangent_normal = geo_utils.normalized(points)

        # calculating triangles' area and normals for top-left triangles
        e1 = along_azimuth[:-1]
        e2 = updip[:, :-1]
        tl_area = geo_utils.triangle_area(e1, e2, diag)
        tl_normal = geo_utils.normalized(numpy.cross(e1, e2))
        # ... and bottom-right triangles
        e1 = along_azimuth[1:]
        e2 = updip[:, 1:]
        br_area = geo_utils.triangle_area(e1, e2, diag)
        br_normal = geo_utils.normalized(numpy.cross(e1, e2))

        if self.depths is None:
            # mesh is on earth surface, inclination is zero
            inclination = 0
        else:
            # inclination calculation
            # top-left triangles
            en = earth_surface_tangent_normal[:-1, :-1]
            # cosine of inclination of the triangle is scalar product
            # of vector normal to triangle plane and (normalized) vector
            # pointing to top left corner of a triangle from earth center
            incl_cos = numpy.sum(en * tl_normal, axis=-1).clip(-1.0, 1.0)
            # we calculate average angle using mean of circular quantities
            # formula: define 2d vector for each triangle where length
            # of the vector corresponds to triangle's weight (we use triangle
            # area) and angle is equal to inclination angle. then we calculate
            # the angle of vector sum of all those vectors and that angle
            # is the weighted average.
            xx = numpy.sum(tl_area * incl_cos)
            # express sine via cosine using Pythagorean trigonometric identity,
            # this is a bit faster than sin(arccos(incl_cos))
            yy = numpy.sum(tl_area * numpy.sqrt(1 - incl_cos * incl_cos))

            # bottom-right triangles
            en = earth_surface_tangent_normal[1:, 1:]
            # we need to clip scalar product values because in some cases
            # they might exceed range where arccos is defined ([-1, 1])
            # because of floating point imprecision
            incl_cos = numpy.sum(en * br_normal, axis=-1).clip(-1.0, 1.0)
            # weighted angle vectors are calculated independently for top-left
            # and bottom-right triangles of each cell in a mesh. here we
            # combine both and finally get the weighted mean angle
            xx += numpy.sum(br_area * incl_cos)
            yy += numpy.sum(br_area * numpy.sqrt(1 - incl_cos * incl_cos))
            inclination = numpy.degrees(numpy.arctan2(yy, xx))

        # azimuth calculation is done similar to one for inclination. we also
        # do separate calculations for top-left and bottom-right triangles
        # and also combine results using mean of circular quantities approach

        # unit vector along z axis
        z_unit = numpy.array([0.0, 0.0, 1.0])

        # unit vectors pointing west from each point of the mesh, they define
        # planes that contain meridian of respective point
        norms_west = geo_utils.normalized(numpy.cross(points + z_unit, points))
        # unit vectors parallel to planes defined by previous ones. they are
        # directed from each point to a point lying on z axis on the same
        # distance from earth center
        norms_north = geo_utils.normalized(numpy.cross(points, norms_west))
        # need to normalize triangles' azimuthal edges because we will project
        # them on other normals and thus calculate an angle in between
        along_azimuth = geo_utils.normalized(along_azimuth)

        # process top-left triangles
        # here we identify the sign of direction of the triangles' azimuthal
        # edges: is edge pointing west or east? for finding that we project
        # those edges to vectors directing to west by calculating scalar
        # product and get the sign of resulting value: if it is negative
        # than the resulting azimuth should be negative as top edge is pointing
        # west.
        sign = numpy.sign(numpy.sign(
            numpy.sum(along_azimuth[:-1] * norms_west[:-1, :-1], axis=-1))
            # we run numpy.sign(numpy.sign(...) + 0.1) to make resulting values
            # be only either -1 or 1 with zero values (when edge is pointing
            # strictly north or south) expressed as 1 (which means "don't
            # change the sign")
            + 0.1
        )
        # the length of projection of azimuthal edge on norms_north is cosine
        # of edge's azimuth
        az_cos = numpy.sum(along_azimuth[:-1] * norms_north[:-1, :-1], axis=-1)
        # use the same approach for finding the weighted mean
        # as for inclination (see above)
        xx = numpy.sum(tl_area * az_cos)
        # the only difference is that azimuth is defined in a range
        # [0, 360), so we need to have two reference planes and change
        # sign of projection on one normal to sign of projection to another one
        yy = numpy.sum(tl_area * numpy.sqrt(1 - az_cos * az_cos) * sign)

        # bottom-right triangles
        sign = numpy.sign(numpy.sign(
            numpy.sum(along_azimuth[1:] * norms_west[1:, 1:], axis=-1))
            + 0.1
        )
        az_cos = numpy.sum(along_azimuth[1:] * norms_north[1:, 1:], axis=-1)
        xx += numpy.sum(br_area * az_cos)
        yy += numpy.sum(br_area * numpy.sqrt(1 - az_cos * az_cos) * sign)

        azimuth = numpy.degrees(numpy.arctan2(yy, xx))
        if azimuth < 0:
            azimuth += 360

        if inclination > 90:
            # average inclination is over 90 degree, that means that we need
            # to reverse azimuthal direction in order for inclination to be
            # in range [0, 90]
            inclination = 180 - inclination
            azimuth = (azimuth + 180) % 360

        return inclination, azimuth

    def triangulate(self):
        """
        Convert mesh points to vectors in Cartesian space.

        :returns:
            Tuple of four elements, each being 2d numpy array of 3d vectors
            (the same structure and shape as the mesh itself). Those tuples
            are:

            #. points vectors,
            #. vectors directed from each point (excluding the last column)
               to the next one in a same row →,
            #. vectors directed from each point (excluding the first row)
               to the previous one in a same column ↑,
            #. vectors pointing from a bottom left point of each mesh cell
               to top right one ↗.

            So the last three arrays of vectors allow to construct triangles
            covering the whole mesh.
        """
        points = geo_utils.spherical_to_cartesian(self.lons, self.lats,
                                                  self.depths)
        # triangulate the mesh by defining vectors of triangles edges:
        # →
        along_azimuth = points[:, 1:] - points[:, :-1]
        # ↑
        updip = points[:-1] - points[1:]
        # ↗
        diag = points[:-1, 1:] - points[1:, :-1]

        return points, along_azimuth, updip, diag
