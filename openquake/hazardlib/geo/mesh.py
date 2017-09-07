# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.mesh` defines classes :class:`Mesh` and
its subclass :class:`RectangularMesh`.
"""
import numpy
import shapely.geometry
import shapely.ops

from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo import geodetic
from openquake.hazardlib.geo import utils as geo_utils

F32 = numpy.float32
point3d = numpy.dtype([('lon', F32), ('lat', F32), ('depth', F32)])


def sqrt(array):
    # due to numerical errors an array of positive values can become negative;
    # for instance: 1 - array([[ 0.99999989,  1.00000001,  1.        ]]) =
    # array([[  1.08272703e-07,  -5.19256105e-09,  -3.94126065e-10]])
    # here we replace the small negative values with zeros
    array[array < 0] = 0
    return numpy.sqrt(array)


def build_array(lons_lats_depths):
    """
    Convert a list of n triples into a composite numpy array with fields
    lon, lat, depth and shape (n,) + lons.shape.
    """
    shape = (len(lons_lats_depths),) + lons_lats_depths[0][0].shape
    arr = numpy.zeros(shape, point3d)
    for i, (lons, lats, depths) in enumerate(lons_lats_depths):
        arr['lon'][i] = lons
        arr['lat'][i] = lats
        arr['depth'][i] = depths
    return arr


def surface_to_mesh(surface):
    """
    :param surface: a Surface object
    :returns: a 3D array of dtype point3d
    """
    if hasattr(surface, 'surfaces'):  # multiplanar surfaces
        n = len(surface.surfaces)
        arr = build_array([[s.corner_lons, s.corner_lats, s.corner_depths]
                           for s in surface.surfaces]).reshape(n, 2, 2)
    else:
        mesh = surface.mesh
        if mesh is None:  # planar surface
            arr = build_array([[surface.corner_lons,
                                surface.corner_lats,
                                surface.corner_depths]]).reshape(1, 2, 2)
        else:  # general surface
            shp = (1,) + mesh.lons.shape
            arr = build_array(
                [[mesh.lons, mesh.lats, mesh.depths]]).reshape(shp)
    return arr


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
    #: Tolerance level to be used in various spatial operations when
    #: approximation is required -- set to 5 meters.
    DIST_TOLERANCE = 0.005

    def __init__(self, lons, lats, depths=None):
        assert (isinstance(lons, numpy.ndarray) and
                isinstance(lats, numpy.ndarray) and
                (depths is None or isinstance(depths, numpy.ndarray))
                ), (type(lons), type(lats), type(depths))
        assert ((lons.shape == lats.shape) and
                (depths is None or depths.shape == lats.shape)
                ), (lons.shape, lats.shape)
        assert lons.size > 0
        self.lons = lons
        self.lats = lats
        self.depths = depths

    @classmethod
    def from_coords(cls, coords):
        """
        Create a mesh object from a list of 3D coordinates (by sorting them)

        :params coords: list of coordinates
        :returns: a :class:`Mesh` instance
        """
        lons, lats, depths = zip(*sorted(coords))
        return cls(numpy.array(lons), numpy.array(lats), numpy.array(depths))

    @classmethod
    def from_points_list(cls, points):
        """
        Create a mesh object from a collection of points.

        :param point:
            List of :class:`~openquake.hazardlib.geo.point.Point` objects.
        :returns:
            An instance of :class:`Mesh` with one-dimensional arrays
            of coordinates from ``points``.
        """
        lons = numpy.zeros(len(points), dtype=float)
        lats = lons.copy()
        depths = lons.copy()
        for i in range(len(points)):
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

        :returns tuple:
            The shape of this mesh as (rows, columns)
        """
        return self.lons.shape

    def __iter__(self):
        """
        Generate :class:`~openquake.hazardlib.geo.point.Point` objects the mesh
        is composed of.

        Coordinates arrays are processed sequentially (as if they were
        flattened).
        """
        lons = self.lons.flat
        lats = self.lats.flat
        if self.depths is not None:
            depths = self.depths.flat
            for i in range(self.lons.size):
                yield Point(lons[i], lats[i], depths[i])
        else:
            for i in range(self.lons.size):
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
        if isinstance(item, int):
            raise ValueError('You must pass a slice, not an index: %s' % item)
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

    def __eq__(self, mesh, tol=1.0E-7):
        """
        Compares the mesh with another returning True if all elements are
        equal to within the specific tolerance, False otherwise

        :param mesh:
            Mesh for comparison as instance of :class:
            openquake.hazardlib.geo.mesh.Mesh

        :param float tol:
            Numerical precision for equality
        """
        if self.depths is not None:
            if mesh.depths is not None:
                # Both meshes have depth values - compare equality
                return numpy.allclose(self.lons, mesh.lons, atol=tol) and\
                    numpy.allclose(self.lats, mesh.lats, atol=tol) and\
                    numpy.allclose(self.depths, mesh.depths, atol=tol)
            else:
                # Second mesh missing depths - not equal
                return False
        else:
            if mesh.depths is None:
                return False
            else:
                return numpy.allclose(self.lons, mesh.lons, atol=tol) and\
                    numpy.allclose(self.lats, mesh.lats, atol=tol)

    def get_min_distance(self, mesh):
        """
        Compute and return the minimum distance from the mesh to each point
        in another mesh.

        :returns:
            numpy array of distances in km of the same shape as ``mesh``.

        Method doesn't make any assumptions on arrangement of the points
        in either mesh and instead calculates the distance from each point of
        this mesh to each point of the target mesh and returns the lowest found
        for each.
        """
        return self._min_idx_dst(mesh)[1]

    def get_closest_points(self, mesh):
        """
        Find closest point of this mesh for each one in ``mesh``.

        :returns:
            :class:`Mesh` object of the same shape as ``mesh`` with closest
            points from this one at respective indices.
        """
        min_idx, min_dst = self._min_idx_dst(mesh)
        lons = self.lons.take(min_idx)
        lats = self.lats.take(min_idx)
        if self.depths is None:
            depths = None
        else:
            depths = self.depths.take(min_idx)
        return Mesh(lons, lats, depths)

    def _min_idx_dst(self, mesh):
        if self.depths is None:
            depths1 = numpy.zeros_like(self.lons)
        else:
            depths1 = self.depths
        if mesh.depths is None:
            depths2 = numpy.zeros_like(mesh.lons)
        else:
            depths2 = mesh.depths
        return geodetic.min_idx_dst(
            self.lons, self.lats, depths1, mesh.lons, mesh.lats, depths2)

    def get_distance_matrix(self):
        """
        Compute and return distances between each pairs of points in the mesh.

        This method requires that all the points lie on Earth surface (have
        zero depth) and coordinate arrays are one-dimensional.

        .. warning::
            Because of its quadratic space and time complexity this method
            is safe to use for meshes of up to several thousand points. For
            mesh of 10k points it needs ~800 Mb for just the resulting matrix
            and four times that much for intermediate storage.

        :returns:
            Two-dimensional numpy array, square matrix of distances. The matrix
            has zeros on main diagonal and positive distances in kilometers
            on all other cells. That is, value in cell (3, 5) is the distance
            between mesh's points 3 and 5 in km, and it is equal to value
            in cell (5, 3).

        Uses :func:`openquake.hazardlib.geo.geodetic.geodetic_distance`.
        """
        assert self.lons.ndim == 1
        assert self.depths is None or (self.depths == 0).all()
        distances = geodetic.geodetic_distance(
            self.lons.reshape(self.lons.shape + (1, )),
            self.lats.reshape(self.lats.shape + (1, )),
            self.lons,
            self.lats
        )
        return numpy.matrix(distances, copy=False)

    def _get_proj_convex_hull(self):
        """
        Create a projection centered in the center of this mesh and define
        a convex polygon in that projection, enveloping all the points
        of the mesh.

        :returns:
            Tuple of two items: projection function and shapely 2d polygon.
            Note that the result geometry can be line or point depending
            on number of points in the mesh and their arrangement.
        """
        # create a projection centered in the center of points collection
        proj = geo_utils.get_orthographic_projection(
            *geo_utils.get_spherical_bounding_box(self.lons, self.lats)
        )
        # project all the points and create a shapely multipoint object.
        # need to copy an array because otherwise shapely misinterprets it
        coords = numpy.transpose(proj(self.lons.flatten(),
                                      self.lats.flatten())).copy()
        multipoint = shapely.geometry.MultiPoint(coords)
        # create a 2d polygon from a convex hull around that multipoint.
        polygon2d = multipoint.convex_hull
        return proj, polygon2d

    def _get_proj_enclosing_polygon(self):
        """
        Create a projection centered in the center of this mesh and define
        a minimum polygon in that projection, enveloping all the points
        of the mesh.

        In :class:`Mesh` this is equivalent to :meth:`_get_proj_convex_hull`.
        """
        return self._get_proj_convex_hull()

    def get_convex_hull(self):
        """
        Get a convex polygon object that contains projections of all the points
        of the mesh.

        :returns:
            Instance of :class:`openquake.hazardlib.geo.polygon.Polygon` that
            is a convex hull around all the points in this mesh. If the
            original mesh had only one point, the resulting polygon has a
            square shape with a side length of 10 meters. If there were only
            two points, resulting polygon is a stripe 10 meters wide.
        """
        proj, polygon2d = self._get_proj_convex_hull()
        # if mesh had only one point, the convex hull is a point. if there
        # were two, it is a line string. we need to return a convex polygon
        # object, so extend that area-less geometries by some arbitrarily
        # small distance.
        if isinstance(polygon2d, (shapely.geometry.LineString,
                                  shapely.geometry.Point)):
            polygon2d = polygon2d.buffer(self.DIST_TOLERANCE, 1)

        # avoid circular imports
        from openquake.hazardlib.geo.polygon import Polygon
        return Polygon._from_2d(polygon2d, proj)


class RectangularMesh(Mesh):
    """
    A specification of :class:`Mesh` that requires coordinate numpy-arrays
    to be two-dimensional.

    Rectangular mesh is meant to represent not just an unordered collection
    of points but rather a sort of table of points, where index of the point
    in a mesh is related to it's position with respect to neighbouring points.
    """
    def __init__(self, lons, lats, depths=None):
        super(RectangularMesh, self).__init__(lons, lats, depths)
        assert lons.ndim == 2

    @classmethod
    def from_points_list(cls, points):
        """
        Create a rectangular mesh object from a list of lists of points.
        Lists in a list are supposed to have the same length.

        :param point:
            List of lists of :class:`~openquake.hazardlib.geo.point.Point`
            objects.
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

    def get_joyner_boore_distance(self, mesh):
        """
        Compute and return Joyner-Boore distance to each point of ``mesh``.
        Point's depth is ignored.

        See
        :meth:`openquake.hazardlib.geo.surface.base.BaseQuadrilateralSurface.get_joyner_boore_distance`
        for definition of this distance.

        :returns:
            numpy array of distances in km of the same shape as ``mesh``.
            Distance value is considered to be zero if a point
            lies inside the polygon enveloping the projection of the mesh
            or on one of its edges.
        """
        # we perform a hybrid calculation (geodetic mesh-to-mesh distance
        # and distance on the projection plane for close points). first,
        # we find the closest geodetic distance for each point of target
        # mesh to this one. in general that distance is greater than
        # the exact distance to enclosing polygon of this mesh and it
        # depends on mesh spacing. but the difference can be neglected
        # if calculated geodetic distance is over some threshold.
        # get the highest slice from the 3D mesh
        distances = geodetic.min_geodetic_distance(
            self.lons, self.lats, mesh.lons, mesh.lats)
        # here we find the points for which calculated mesh-to-mesh
        # distance is below a threshold. this threshold is arbitrary:
        # lower values increase the maximum possible error, higher
        # values reduce the efficiency of that filtering. the maximum
        # error is equal to the maximum difference between a distance
        # from site to two adjacent points of the mesh and distance
        # from site to the line connecting them. thus the error is
        # a function of distance threshold and mesh spacing. the error
        # is maximum when the site lies on a perpendicular to the line
        # connecting points of the mesh and that passes the middle
        # point between them. the error then can be calculated as
        # ``err = trsh - d = trsh - \sqrt(trsh^2 - (ms/2)^2)``, where
        # ``trsh`` and ``d`` are distance to mesh points (the one
        # we found on the previous step) and distance to the line
        # connecting them (the actual distance) and ``ms`` is mesh
        # spacing. the threshold of 40 km gives maximum error of 314
        # meters for meshes with spacing of 10 km and 5.36 km for
        # meshes with spacing of 40 km. if mesh spacing is over
        # ``(trsh / \sqrt(2)) * 2`` then points lying in the middle
        # of mesh cells (that is inside the polygon) will be filtered
        # out by the threshold and have positive distance instead of 0.
        # so for threshold of 40 km mesh spacing should not be more
        # than 56 km (typical values are 5 to 10 km).

        [idxs] = (distances < 40).nonzero()
        if not len(idxs):
            # no point is close enough, return distances as they are
            return distances

        # for all the points that are closer than the threshold we need
        # to recalculate the distance and set it to zero, if point falls
        # inside the enclosing polygon of the mesh. for doing that we
        # project both this mesh and the points of the second mesh--selected
        # by distance threshold--to the same Cartesian space, define
        # minimum shapely polygon enclosing the mesh and calculate point
        # to polygon distance, which gives the most accurate value
        # of distance in km (and that value is zero for points inside
        # the polygon).
        proj, polygon = self._get_proj_enclosing_polygon()
        if not isinstance(polygon, shapely.geometry.Polygon):
            # either line or point is our enclosing polygon. draw
            # a square with side of 10 m around in order to have
            # a proper polygon instead.
            polygon = polygon.buffer(self.DIST_TOLERANCE, 1)
        mesh_xx, mesh_yy = proj(mesh.lons[idxs], mesh.lats[idxs])
        # replace geodetic distance values for points-closer-than-the-threshold
        # by more accurate point-to-polygon distance values.
        distances[idxs] = geo_utils.point_to_polygon_distance(
            polygon, mesh_xx, mesh_yy)

        return distances

    def _get_proj_enclosing_polygon(self):
        """
        See :meth:`Mesh._get_proj_enclosing_polygon`.

        :class:`RectangularMesh` contains an information about relative
        positions of points, so it allows to define the minimum polygon,
        containing the projection of the mesh, which doesn't necessarily
        have to be convex (in contrast to :class:`Mesh` implementation).

        :returns:
            Same structure as :meth:`Mesh._get_proj_convex_hull`.
        """
        if self.lons.size < 4:
            # the mesh doesn't contain even a single cell, use :class:`Mesh`
            # method implementation (which would dilate the point or the line)
            return super(RectangularMesh, self)._get_proj_enclosing_polygon()

        proj = geo_utils.get_orthographic_projection(
            *geo_utils.get_spherical_bounding_box(self.lons.flatten(),
                                                  self.lats.flatten())
        )
        mesh2d = numpy.array(proj(self.lons.transpose(),
                                  self.lats.transpose())).transpose()
        lines = iter(mesh2d)
        # we iterate over horizontal stripes, keeping the "previous"
        # line of points. we keep it reversed, such that together
        # with the current line they define the sequence of points
        # around the stripe.
        prev_line = next(lines)[::-1]
        polygons = []
        for i, line in enumerate(lines):
            coords = numpy.concatenate((prev_line, line, prev_line[0:1]))
            # create the shapely polygon object from the stripe
            # coordinates and simplify it (remove redundant points,
            # if there are any lying on the straight line).
            stripe = shapely.geometry.LineString(coords) \
                                     .simplify(self.DIST_TOLERANCE) \
                                     .buffer(self.DIST_TOLERANCE, 2)
            polygons.append(shapely.geometry.Polygon(stripe.exterior))
            prev_line = line[::-1]
        try:
            # create a final polygon as the union of all the stripe ones
            polygon = shapely.ops.cascaded_union(polygons) \
                                 .simplify(self.DIST_TOLERANCE)
        except ValueError:
            # NOTE(larsbutler): In some rare cases, we've observed ValueErrors
            # ("No Shapely geometry can be created from null value") with very
            # specific sets of polygons such that there are two unique
            # and many duplicates of one.
            # This bug is very difficult to reproduce consistently (except on
            # specific platforms) so the work around here is to remove the
            # duplicate polygons. In fact, we only observed this error on our
            # CI/build machine. None of our dev environments or production
            # machines has encountered this error, at least consistently. >:(
            polygons = [shapely.wkt.loads(x) for x in
                        list(set(p.wkt for p in polygons))]
            polygon = shapely.ops.cascaded_union(polygons) \
                                 .simplify(self.DIST_TOLERANCE)
        return proj, polygon

    def get_middle_point(self):
        """
        Return the middle point of the mesh.

        :returns:
            An instance of :class:`~openquake.hazardlib.geo.point.Point`.

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
                lon1, lon2 = self.lons[mid_row][mid_col - 1: mid_col + 1]
                lat1, lat2 = self.lats[mid_row][mid_col - 1: mid_col + 1]
                if self.depths is not None:
                    depth1 = self.depths[mid_row][mid_col - 1]
                    depth2 = self.depths[mid_row][mid_col]
        else:
            # there are even number of rows. take the row just above
            # and the one just below the middle and find middle point
            # of each
            submesh1 = self[mid_row - 1: mid_row]
            submesh2 = self[mid_row: mid_row + 1]
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
        assert 1 not in self.lons.shape, (
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
            yy = numpy.sum(tl_area * sqrt(1 - incl_cos * incl_cos))

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
            yy += numpy.sum(br_area * sqrt(1 - incl_cos * incl_cos))
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
        yy = numpy.sum(tl_area * sqrt(1 - az_cos * az_cos) * sign)
        # bottom-right triangles
        sign = numpy.sign(numpy.sign(
            numpy.sum(along_azimuth[1:] * norms_west[1:, 1:], axis=-1))
            + 0.1
        )
        az_cos = numpy.sum(along_azimuth[1:] * norms_north[1:, 1:], axis=-1)
        xx += numpy.sum(br_area * az_cos)
        yy += numpy.sum(br_area * sqrt(1 - az_cos * az_cos) * sign)

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

    def get_cell_dimensions(self):
        """
        Calculate centroid, width, length and area of each mesh cell.

        :returns:
            Tuple of four elements, each being 2d numpy array.
            Each array has both dimensions less by one the dimensions
            of the mesh, since they represent cells, not vertices.
            Arrays contain the following cell information:

            #. centroids, 3d vectors in a Cartesian space,
            #. length (size along row of points) in km,
            #. width (size along column of points) in km,
            #. area in square km.
        """
        points, along_azimuth, updip, diag = self.triangulate()
        top = along_azimuth[:-1]
        left = updip[:, :-1]
        tl_area = geo_utils.triangle_area(top, left, diag)
        top_length = numpy.sqrt(numpy.sum(top * top, axis=-1))
        left_length = numpy.sqrt(numpy.sum(left * left, axis=-1))

        bottom = along_azimuth[1:]
        right = updip[:, 1:]
        br_area = geo_utils.triangle_area(bottom, right, diag)
        bottom_length = numpy.sqrt(numpy.sum(bottom * bottom, axis=-1))
        right_length = numpy.sqrt(numpy.sum(right * right, axis=-1))

        cell_area = tl_area + br_area

        tl_center = (points[:-1, :-1] + points[:-1, 1:] + points[1:, :-1]) / 3
        br_center = (points[:-1, 1:] + points[1:, :-1] + points[1:, 1:]) / 3

        cell_center = ((tl_center * tl_area.reshape(tl_area.shape + (1, ))
                        + br_center * br_area.reshape(br_area.shape + (1, )))
                       / cell_area.reshape(cell_area.shape + (1, )))

        cell_length = ((top_length * tl_area + bottom_length * br_area)
                       / cell_area)
        cell_width = ((left_length * tl_area + right_length * br_area)
                      / cell_area)

        return cell_center, cell_length, cell_width, cell_area

    def triangulate(self):
        """
        Convert mesh points to vectors in Cartesian space.

        :returns:
            Tuple of four elements, each being 2d numpy array of 3d vectors
            (the same structure and shape as the mesh itself). Those arrays
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

    def get_mean_width(self):
        """
        Calculate and return (weighted) mean width (km) of a mesh surface.

        The length of each mesh column is computed (summing up the cell widths
        in a same column), and the mean value (weighted by the mean cell
        length in each column) is returned.
        """
        assert 1 not in self.lons.shape, (
            "mean width is only defined for mesh of more than "
            "one row and more than one column of points")

        _, cell_length, cell_width, cell_area = self.get_cell_dimensions()

        # compute widths along each mesh column
        widths = numpy.sum(cell_width, axis=0)

        # compute (weighted) mean cell length along each mesh column
        column_areas = numpy.sum(cell_area, axis=0)
        mean_cell_lengths = numpy.sum(cell_length * cell_area, axis=0) / \
            column_areas

        # compute and return weighted mean
        return numpy.sum(widths * mean_cell_lengths) / \
            numpy.sum(mean_cell_lengths)
