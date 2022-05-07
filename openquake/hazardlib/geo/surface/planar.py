# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2022 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.surface.planar` contains
:class:`PlanarSurface`.
"""
import logging
import numpy
from openquake.baselib.node import Node
from openquake.baselib.performance import numba, compile
from openquake.hazardlib.geo.geodetic import point_at
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo import geodetic
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo import utils as geo_utils

# Maximum difference in surface's rectangle side lengths, maximum offset
# of a bottom right corner from a plane that contains other corners,
# as well as maximum offset of a bottom left corner from a line drawn
# downdip perpendicular to top edge from top left corner, expressed
# as a fraction of the surface's area.
IMPERFECT_RECTANGLE_TOLERANCE = 0.002

planar_array_dt = numpy.dtype([
    ('corners', (float, 4)),
    ('xyz', (float, 4)),
    ('normal', float),
    ('uv1', float),
    ('uv2', float),
    ('wld', float),
    ('hypo', float)])


def dot(a, b):
    return (a[..., 0] * b[..., 0] +
            a[..., 1] * b[..., 1] +
            a[..., 2] * b[..., 2])


def build_planar_array(corners, hypo=None, check=False):
    """
    :param corners: array of shape (4, M, N, D, 3)
    :param hypo: None or array of shapee (M, N, D, 3)
    :returns: a planar_array array of length (M, N, D)
    """
    shape = corners.shape[:-1]  # (4, M, N, D)
    planar_array = numpy.zeros(corners.shape[1:], planar_array_dt).view(
        numpy.recarray)
    if hypo is not None:
        planar_array['hypo'] = hypo
    tl, tr, bl, br = xyz = geo_utils.spherical_to_cartesian(
        corners[..., 0], corners[..., 1], corners[..., 2])
    for i, corner in enumerate(corners):
        planar_array['corners'][..., i] = corner
        planar_array['xyz'][..., i] = xyz[i]
    # these two parameters define the plane that contains the surface
    # (in 3d Cartesian space): a normal unit vector,
    planar_array['normal'] = n = geo_utils.normalized(
        numpy.cross(tl - tr, tl - bl))
    # ... and scalar "d" parameter from the plane equation (uses
    # an equation (3) from http://mathworld.wolfram.com/Plane.html)
    d = - dot(n, tl)
    # these two 3d vectors together with a zero point represent surface's
    # coordinate space (the way to translate 3d Cartesian space with
    # a center in earth's center to 2d space centered in surface's top
    # left corner with basis vectors directed to top right and bottom left
    # corners. see :meth:`_project`.
    planar_array['uv1'] = uv1 = geo_utils.normalized(tr - tl)
    planar_array['uv2'] = uv2 = numpy.cross(n, uv1)

    # translate projected points to surface coordinate space, shape (N, 3)
    dists = dot(xyz, n) + d
    xx, yy = numpy.zeros(shape), numpy.zeros(shape)
    for i in range(4):
        mat = xyz[i] - tl
        xx[i], yy[i] = dot(mat, uv1), dot(mat, uv2)

    # "length" of the rupture is measured along the top edge
    length1, length2 = xx[1] - xx[0], xx[3] - xx[2]
    # "width" of the rupture is measured along downdip direction
    width1, width2 = yy[2] - yy[0], yy[3] - yy[1]
    width = (width1 + width2) / 2.0
    length = (length1 + length2) / 2.0
    wld = planar_array['wld']
    wld[..., 0] = width
    wld[..., 1] = length
    wld[..., 2] = d

    if check:
        # calculate the imperfect rectangle tolerance
        # relative to surface's area
        dists = (xyz - tl) @ n
        tolerance = width * length * IMPERFECT_RECTANGLE_TOLERANCE
        if numpy.abs(dists).max() > tolerance:
            logging.warning("corner points do not lie on the same plane")
        if length2 < 0:
            raise ValueError("corners are in the wrong order")
        if numpy.abs(length1 - length2).max() > tolerance:
            raise ValueError("top and bottom edges have different lengths")
    return planar_array


def _project(self, points):
    """
    Project points (as an array of shape (N, 3)) to a surface's plane.

    Parameters are lists or numpy arrays of coordinates of points
    to project.

    :returns:
        A tuple of three arrays: distances between original points
        and surface's plane in km, "x" and "y" coordinates of points'
        projections to the plane (in a surface's coordinate space).
    """
    # uses method from http://www.9math.com/book/projection-point-plane
    dists = points @ self.normal + self.wld[2]
    # translate projected points to surface coordinate space, shape (N, 3)
    mat = points - self.xyz[:, 0]
    return dists, mat @ self.uv1, mat @ self.uv2


# numbified below
def get_rrup(planar, points):
    """
    :param planar: a planar recarray of shape (U, 3)
    :param points: an array of euclidean coordinates of shape (N, 3)
    :returns: (U, N) distances for the surface to the points.
    """
    distances = numpy.zeros((len(planar), len(points)))

    def dot(a, v):  # array @ vector
        return a[:, 0] * v[0] + a[:, 1] * v[1] + a[:, 2] * v[2]
    for p, pla in enumerate(planar):
        width, length, d = pla.wld
        # we project all the points of the mesh on a plane that contains
        # the surface (translating coordinates of the projections to a local
        # 2d space) and at the same time calculate the distance to that
        # plane.
        dists = dot(points, pla.normal) + d
        mat = points - pla.xyz[:, 0]
        xx = dot(mat, pla.uv1)
        yy = dot(mat, pla.uv2)

        # the actual resulting distance is a square root of squares
        # of a distance from a point to a plane that contains the surface
        # and a distance from a projection of that point on that plane
        # and a surface rectangle. we have former (``dists``), now we need
        # to find latter.
        #
        # we process separately two coordinate components of the point
        # projection. for abscissa we consider three possible cases:
        #
        #  I  . III .  II
        #     .     .
        #     0-----+                → x axis direction
        #     |     |
        #     +-----+
        #     .     .
        #     .     .
        #
        mxx = numpy.select(
            condlist=[
                # case "I": point on the left hand side from the rectangle
                xx < 0,
                # case "II": point is on the right hand side
                xx > length
                # default -- case "III": point is in between vertical sides
            ],
            choicelist=[
                # case "I": we need to consider distance between a point
                # and a line containing left side of the rectangle
                xx,
                # case "II": considering a distance between a point and
                # a line containing the right side
                xx - length
            ],
            # case "III": abscissa doesn't have an effect on a distance
            # to the rectangle
            default=0
        )
        # for ordinate we do the same operation (again three cases):
        #
        #    I
        #  - - - 0---+ - - -         ↓ y axis direction
        #   III  |   |
        #  - - - +---+ - - -
        #    II
        #
        myy = numpy.select(
            condlist=[
                # case "I": point is above the rectangle top edge
                yy < 0,
                # case "II": point is below the rectangle bottom edge
                yy > width
                # default -- case "III": point is in between lines containing
                # top and bottom edges
            ],
            choicelist=[
                # case "I": considering a distance to a line containing
                # a top edge
                yy,
                # case "II": considering a distance to a line containing
                # a bottom edge
                yy - width
            ],
            # case "III": ordinate doesn't affect the distance
            default=0
        )
        # combining distance on a plane with distance to a plane
        distances[p] = numpy.sqrt(dists ** 2 + mxx ** 2 + myy ** 2)
    return distances


if numba:
    planar_nt = numba.from_dtype(planar_array_dt)
    sig = numba.float64[:, :](planar_nt[:, :], numba.float64[:, :])
    get_rrup = compile(sig)(get_rrup)


class PlanarSurface(BaseSurface):
    """
    Planar rectangular surface with two sides parallel to the Earth surface.

    :param strike:
        Strike of the surface is the azimuth from ``top_left`` to ``top_right``
        points.
    :param dip:
        Dip is the angle between the surface itself and the earth surface.

    Other parameters are points (instances of
    :class:`~openquake.hazardlib.geo.point.Point`) defining the surface
    corners in clockwise direction starting from top left corner. Top and
    bottom edges of the polygon must be parallel to earth surface and to each
    other.

    See :class:`~openquake.hazardlib.geo.nodalplane.NodalPlane` for more
    detailed definition of ``strike`` and ``dip``. Note that these parameters
    are supposed to match the factual surface geometry (defined by corner
    points), but this is not enforced or even checked.

    :raises ValueError:
        If either top or bottom points differ in depth or if top edge
        is not parallel to the bottom edge, if top edge differs in length
        from the bottom one, or if mesh spacing is not positive.
    """
    @property
    def surface_nodes(self):
        """
        A single element list containing a planarSurface node
        """
        node = Node('planarSurface')
        for name, lon, lat, depth in zip(
                'topLeft topRight bottomLeft bottomRight'.split(),
                self.corner_lons, self.corner_lats, self.corner_depths):
            node.append(Node(name, dict(lon=lon, lat=lat, depth=depth)))
        return [node]

    @property
    def mesh(self):
        """
        :returns: a mesh with the 4 corner points tl, tr, bl, br
        """
        return Mesh(*self.corners)

    @property
    def corner_lons(self):
        return self.corners[0]

    @property
    def corner_lats(self):
        return self.corners[1]

    @property
    def corner_depths(self):
        return self.corners[2]

    def __init__(self, strike, dip,
                 top_left, top_right, bottom_right, bottom_left, check=True):
        if check:
            if not (top_left.depth == top_right.depth and
                    bottom_left.depth == bottom_right.depth):
                raise ValueError("top and bottom edges must be parallel "
                                 "to the earth surface")
            NodalPlane.check_dip(dip)
            NodalPlane.check_strike(strike)
        self.dip = dip
        self.strike = strike
        self.corners = numpy.array([[
            top_left.longitude, top_right.longitude,
            bottom_left.longitude, bottom_right.longitude
        ], [top_left.latitude, top_right.latitude,
            bottom_left.latitude, bottom_right.latitude], [
                top_left.depth, top_right.depth,
                bottom_left.depth, bottom_right.depth]]).T  # shape (4, 3)
        # now set the attributes normal, d, uv1, uv2, tl
        self._init_plane(check)

    @classmethod
    def from_corner_points(cls, top_left, top_right,
                           bottom_right, bottom_left):
        """
        Create and return a planar surface from four corner points.

        The azimuth of the line connecting the top left and the top right
        corners define the surface strike, while the angle between the line
        connecting the top left and bottom left corners and a line parallel
        to the earth surface defines the surface dip.

        :param openquake.hazardlib.geo.point.Point top_left:
            Upper left corner
        :param openquake.hazardlib.geo.point.Point top_right:
            Upper right corner
        :param openquake.hazardlib.geo.point.Point bottom_right:
            Lower right corner
        :param openquake.hazardlib.geo.point.Point bottom_left:
            Lower left corner
        :returns:
            An instance of :class:`PlanarSurface`.
        """
        strike = top_left.azimuth(top_right)
        dist = top_left.distance(bottom_left)
        vert_dist = bottom_left.depth - top_left.depth
        dip = numpy.degrees(numpy.arcsin(vert_dist / dist))
        self = cls(strike, dip, top_left, top_right,
                   bottom_right, bottom_left)
        return self

    @classmethod
    def from_hypocenter(cls, hypoc, msr, mag, aratio, strike, dip, rake):
        """
        Create and return a planar surface given the hypocenter location
        and other rupture properties.

        :param hypoc:
            An instance of :class: `openquake.hazardlib.geo.point.Point`
        :param msr:
            The magnitude scaling relationship
            e.g. an instance of :class: `openquake.hazardlib.scalerel.WC1994`
        :param mag:
            The magnitude
        :param aratio:
            The rupture aspect ratio
        :param strike:
            The rupture strike
        :param dip:
            The rupture dip
        :param rake:
            The rupture rake

        """
        lon = hypoc.longitude
        lat = hypoc.latitude
        depth = hypoc.depth

        area = msr.get_median_area(mag, rake)
        width = (area / aratio) ** 0.5
        length = width * aratio

        height = width * numpy.sin(numpy.radians(dip))
        hdist = width * numpy.cos(numpy.radians(dip))
        # Move hor. 1/2 hdist in direction -90
        mid_top = point_at(lon, lat, strike - 90, hdist / 2)
        # Move hor. 1/2 hdist in direction +90
        mid_bot = point_at(lon, lat, strike + 90, hdist / 2)

        # compute corner points at the surface
        top_right = point_at(mid_top[0], mid_top[1], strike, length / 2)
        top_left = point_at(mid_top[0], mid_top[1], strike + 180, length / 2)
        bot_right = point_at(mid_bot[0], mid_bot[1], strike, length/2)
        bot_left = point_at(mid_bot[0], mid_bot[1], strike + 180, length / 2)

        # compute corner points in 3D
        pbl = Point(bot_left[0], bot_left[1], depth + height / 2)
        pbr = Point(bot_right[0], bot_right[1], depth + height / 2)
        hei = depth - height / 2
        ptl = Point(top_left[0], top_left[1], hei)
        ptr = Point(top_right[0], top_right[1], hei)

        return cls(strike, dip, ptl, ptr, pbr, pbl)

    @classmethod
    def from_(cls, planar_array, strike, dip):
        self = object.__new__(PlanarSurface)
        self.strike = strike
        self.dip = dip
        self.array = planar_array
        for par in planar_array.dtype.names:
            setattr(self, par, planar_array[par])
        return self

    @classmethod
    def from_array(cls, array34):
        """
        :param array34: an array of shape (3, 4) in order tl, tr, bl, br
        :returns: a :class:`PlanarSurface` instance
        """
        # this is used in event based calculations
        # when the planar surface geometry comes from an array
        # in the datastore, which means it is correct and there is no need
        # to check it again; also the check would fail because of a bug,
        # https://github.com/gem/oq-engine/issues/3392
        # NB: this different from the ucerf order below, bl<->br!
        tl, tr, bl, br = [Point(*p) for p in array34.T]
        strike = tl.azimuth(tr)
        dip = numpy.degrees(
            numpy.arcsin((bl.depth - tl.depth) / tl.distance(bl)))
        return cls(strike, dip, tl, tr, br, bl, check=False)

    @classmethod
    def from_ucerf(cls, array43):
        """
        :param array43: an array of shape (4, 3) in order tl, tr, br, bl
        :returns: a :class:`PlanarSurface` instance
        """
        tl, tr, br, bl = [Point(*p) for p in array43]
        strike = tl.azimuth(tr)
        dip = numpy.degrees(
            numpy.arcsin((bl.depth - tl.depth) / tl.distance(bl)))
        self = cls(strike, dip, tl, tr, br, bl, check=False)
        return self

    def _init_plane(self, check=False):
        """
        Prepare everything needed for projecting arbitrary points on a plane
        containing the surface.
        """
        self.array = build_planar_array(self.corners, check=check)
        for par in self.array.dtype.names:
            setattr(self, par, self.array[par])

    def translate(self, p1, p2):
        """
        Translate the surface for a specific distance along a specific azimuth
        direction.

        Parameters are two points (instances of
        :class:`openquake.hazardlib.geo.point.Point`) representing the
        direction and an azimuth for translation. The resulting surface corner
        points will be that far along that azimuth from respective corner
        points of this surface as ``p2`` is located with respect to ``p1``.

        :returns:
            A new :class:`PlanarSurface` object with the same mesh spacing,
            dip, strike, width, length and depth but with corners longitudes
            and latitudes translated.
        """
        azimuth = geodetic.azimuth(p1.longitude, p1.latitude,
                                   p2.longitude, p2.latitude)
        distance = geodetic.geodetic_distance(p1.longitude, p1.latitude,
                                              p2.longitude, p2.latitude)
        # avoid calling PlanarSurface's constructor
        nsurf = object.__new__(PlanarSurface)
        nsurf.corners = numpy.zeros((4, 3))
        for i, (lon, lat) in enumerate(
                zip(self.corner_lons, self.corner_lats)):
            lo, la = geodetic.point_at(lon, lat, azimuth, distance)
            nsurf.corners[i, 0] = lo
            nsurf.corners[i, 1] = la
            nsurf.corners[i, 2] = self.corner_depths[i]
        nsurf.dip = self.dip
        nsurf.strike = self.strike
        nsurf._init_plane()
        return nsurf

    @property
    def top_left(self):
        return Point(self.corner_lons[0], self.corner_lats[0],
                     self.corner_depths[0])

    @property
    def top_right(self):
        return Point(self.corner_lons[1], self.corner_lats[1],
                     self.corner_depths[1])

    @property
    def bottom_left(self):
        return Point(self.corner_lons[2], self.corner_lats[2],
                     self.corner_depths[2])

    @property
    def bottom_right(self):
        return Point(self.corner_lons[3], self.corner_lats[3],
                     self.corner_depths[3])

    def get_strike(self):
        """
        Return strike value that was provided to the constructor.
        """
        return self.strike

    def get_dip(self):
        """
        Return dip value that was provided to the constructor.
        """
        return self.dip

    def _project_back(self, dists, xx, yy):
        """
        Convert coordinates in plane's Cartesian space back to spherical
        coordinates.

        Parameters are numpy arrays, as returned from :meth:`_project`, which
        this method does the opposite to.

        :return:
            Tuple of longitudes, latitudes and depths numpy arrays.
        """
        vectors = (self.xyz[:, 0] +
                   self.uv1 * xx.reshape(xx.shape + (1, )) +
                   self.uv2 * yy.reshape(yy.shape + (1, )) +
                   self.normal * dists.reshape(dists.shape + (1, )))
        return geo_utils.cartesian_to_spherical(vectors)

    def get_min_distance(self, mesh):
        """
        See :meth:`superclass' method
        <openquake.hazardlib.geo.surface.base.BaseSurface.get_min_distance>`.

        This is an optimized version specific to planar surface that doesn't
        make use of the mesh.
        """
        return get_rrup(self.array.reshape(1, 3), mesh.xyz)[0]

    def get_closest_points(self, mesh):
        """
        See :meth:`superclass' method
        <openquake.hazardlib.geo.surface.base.BaseSurface.get_closest_points>`.

        This is an optimized version specific to planar surface that doesn't
        make use of the mesh.
        """
        dists, xx, yy = _project(self, mesh.xyz)
        mxx = xx.clip(0, self.wld[1])
        myy = yy.clip(0, self.wld[0])
        dists.fill(0)
        lons, lats, depths = self._project_back(dists, mxx, myy)
        return Mesh(lons, lats, depths)

    def _get_top_edge_centroid(self):
        """
        Overrides :meth:`superclass' method
        <openquake.hazardlib.geo.surface.base.BaseSurface._get_top_edge_centroid>`
        in order to avoid creating a mesh.
        """
        lon, lat = geo_utils.get_middle_point(
            self.corner_lons[0], self.corner_lats[0],
            self.corner_lons[1], self.corner_lats[1])
        return Point(lon, lat, self.corner_depths[0])

    def get_top_edge_depth(self):
        """
        Overrides :meth:`superclass' method
        <openquake.hazardlib.geo.surface.base.BaseSurface.get_top_edge_depth>`
        in order to avoid creating a mesh.
        """
        return self.corner_depths[0]

    def get_joyner_boore_distance(self, mesh):
        """
        See :meth:`superclass' method
        <openquake.hazardlib.geo.surface.base.BaseSurface.get_joyner_boore_distance>`.

        This is an optimized version specific to planar surface that doesn't
        make use of the mesh.
        """
        # we define four great circle arcs that contain four sides
        # of projected planar surface:
        #
        #       ↓     II    ↓
        #    I  ↓           ↓  I
        #       ↓     +     ↓
        #  →→→→→TL→→→→1→→→→TR→→→→→     → azimuth direction →
        #       ↓     -     ↓
        #       ↓           ↓
        # III  -3+   IV    -4+  III             ↓
        #       ↓           ↓            downdip direction
        #       ↓     +     ↓                   ↓
        #  →→→→→BL→→→→2→→→→BR→→→→→
        #       ↓     -     ↓
        #    I  ↓           ↓  I
        #       ↓     II    ↓
        #
        # arcs 1 and 2 are directed from left corners to right ones (the
        # direction has an effect on the sign of the distance to an arc,
        # as it shown on the figure), arcs 3 and 4 are directed from top
        # corners to bottom ones.
        #
        # then we measure distance from each of the points in a mesh
        # to each of those arcs and compare signs of distances in order
        # to find a relative positions of projections of points and
        # projection of a surface.
        #
        # then we consider four special cases (labeled with Roman numerals)
        # and either pick one of distances to arcs or a closest distance
        # to corner.
        #
        # indices 0, 2 and 1 represent corners TL, BL and TR respectively.
        arcs_lons = self.corner_lons.take([0, 2, 0, 1])
        arcs_lats = self.corner_lats.take([0, 2, 0, 1])
        downdip_azimuth = (self.strike + 90) % 360
        arcs_azimuths = [self.strike, self.strike,
                         downdip_azimuth, downdip_azimuth]
        mesh_lons = mesh.lons.reshape((-1, 1))
        mesh_lats = mesh.lats.reshape((-1, 1))
        # calculate distances from all the target points to all four arcs
        dists_to_arcs = geodetic.distance_to_arc(
            arcs_lons, arcs_lats, arcs_azimuths, mesh_lons, mesh_lats
        )
        # ... and distances from all the target points to each of surface's
        # corners' projections (we might not need all of those but it's
        # better to do that calculation once for all).
        dists_to_corners = geodetic.min_geodetic_distance(
            (self.corner_lons, self.corner_lats), mesh.xyz)

        # extract from ``dists_to_arcs`` signs (represent relative positions
        # of an arc and a point: +1 means on the left hand side, 0 means
        # on arc and -1 means on the right hand side) and minimum absolute
        # values of distances to each pair of parallel arcs.
        ds1, ds2, ds3, ds4 = numpy.sign(dists_to_arcs).transpose()
        dists_to_arcs = numpy.abs(dists_to_arcs).reshape(-1, 2, 2).min(axis=-1)

        jb_dists = numpy.select(
            # consider four possible relative positions of point and arcs:
            condlist=[
                # signs of distances to both parallel arcs are the same
                # in both pairs, case "I" on a figure above
                (ds1 == ds2) & (ds3 == ds4),
                # sign of distances to two parallels is the same only
                # in one pair, case "II"
                ds1 == ds2,
                # ... or another (case "III")
                ds3 == ds4
                # signs are different in both pairs (this is a "default"),
                # case "IV"
            ],

            choicelist=[
                # case "I": closest distance is the closest distance to corners
                dists_to_corners,
                # case "II": closest distance is distance to arc "1" or "2",
                # whichever is closer
                dists_to_arcs[:, 0],
                # case "III": closest distance is distance to either
                # arc "3" or "4"
                dists_to_arcs[:, 1]
            ],

            # default -- case "IV"
            default=0
        )

        return jb_dists.reshape(mesh.lons.shape)

    def get_rx_distance(self, mesh):
        """
        See :meth:`superclass method
        <.base.BaseSurface.get_rx_distance>`
        for spec of input and result values.

        This is an optimized version specific to planar surface that doesn't
        make use of the mesh.
        """
        return geodetic.distance_to_arc(
            self.corner_lons[0], self.corner_lats[0], self.strike,
            mesh.lons, mesh.lats)

    def get_ry0_distance(self, mesh):
        """
        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate
            Ry0-distance to.
        :returns:
            Numpy array of distances in km.

        See also :meth:`superclass method <.base.BaseSurface.get_ry0_distance>`
        for spec of input and result values.

        This is version specific to the planar surface doesn't make use of the
        mesh
        """
        dst1 = geodetic.distance_to_arc(self.top_left.longitude,
                                        self.top_left.latitude,
                                        (self.strike + 90.) % 360,
                                        mesh.lons, mesh.lats)

        dst2 = geodetic.distance_to_arc(self.top_right.longitude,
                                        self.top_right.latitude,
                                        (self.strike + 90.) % 360,
                                        mesh.lons, mesh.lats)
        # Find the points on the rupture

        # Get the shortest distance from the two lines
        idx = numpy.sign(dst1) == numpy.sign(dst2)
        dst = numpy.zeros_like(dst1)
        dst[idx] = numpy.fmin(numpy.abs(dst1[idx]), numpy.abs(dst2[idx]))
        return dst

    def get_width(self):
        """
        Return surface's width value (in km) as computed in the constructor
        (that is mean value of left and right surface sides).
        """
        return self.wld[0]

    def get_area(self):
        """
        Return surface's area value (in squared km) obtained as the product
        of surface length and width.
        """
        return self.wld[0] * self.wld[1]

    def get_bounding_box(self):
        """
        Compute surface bounding box from plane's corners coordinates. Calls
        :meth:`openquake.hazardlib.geo.utils.get_spherical_bounding_box`

        :return:
            A tuple of four items. These items represent western, eastern,
            northern and southern borders of the bounding box respectively.
            Values are floats in decimal degrees.
        """

        return geo_utils.get_spherical_bounding_box(self.corner_lons,
                                                    self.corner_lats)

    def get_middle_point(self):
        """
        Compute middle point from surface's corners coordinates. Calls
        :meth:`openquake.hazardlib.geo.utils.get_middle_point`
        """
        # compute middle point between upper left and bottom right corners
        lon, lat = geo_utils.get_middle_point(self.corner_lons[0],
                                              self.corner_lats[0],
                                              self.corner_lons[3],
                                              self.corner_lats[3])
        depth = (self.corner_depths[0] + self.corner_depths[3]) / 2.

        return Point(lon, lat, depth)

    def get_surface_boundaries(self):
        """
        The corners lons/lats in WKT-friendly order (clockwise)
        """
        return (self.corner_lons.take([0, 1, 3, 2, 0]),
                self.corner_lats.take([0, 1, 3, 2, 0]))

    def get_surface_boundaries_3d(self):
        """
        The corners lons/lats/depths in WKT-friendly order (clockwise)
        """
        return (self.corner_lons.take([0, 1, 3, 2, 0]),
                self.corner_lats.take([0, 1, 3, 2, 0]),
                self.corner_depths.take([0, 1, 3, 2, 0]))
