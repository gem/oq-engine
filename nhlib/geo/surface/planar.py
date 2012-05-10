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
Module :mod:`nhlib.geo.surface.planar` contains :class:`PlanarSurface`.
"""
import numpy

from nhlib.geo import Point
from nhlib.geo.surface.base import BaseSurface
from nhlib.geo.mesh import RectangularMesh
from nhlib.geo import geodetic
from nhlib.geo.nodalplane import NodalPlane
from nhlib.geo import _utils as geo_utils


class PlanarSurface(BaseSurface):
    """
    Planar rectangular surface with two sides parallel to the Earth surface.

    :param mesh_spacing:
        The desired distance between two adjacent points in the surface mesh
        in both horizontal and vertical directions, in km.
    :param strike:
        Strike of the surface is the azimuth from ``top_left`` to ``top_right``
        points.
    :param dip:
        Dip is the angle between the surface itself and the earth surface.

    Other parameters are points (instances of :class:`~nhlib.geo.point.Point`)
    defining the surface corners in clockwise direction starting from top
    left corner. Top and bottom edges of the polygon must be parallel
    to earth surface and to each other.

    See :class:`~nhlib.geo.nodalplane.NodalPlane` for more detailed definition
    of ``strike`` and ``dip``. Note that these parameters are supposed
    to match the factual surface geometry (defined by corner points), but
    this is not enforced or even checked.

    :raises ValueError:
        If either top or bottom points differ in depth or if top edge
        is not parallel to the bottom edge, if top edge differs in length
        from the bottom one, or if mesh spacing is not positive.
    """
    #: Maximum difference in surface's rectangle side lengths, maximum offset
    #: of a bottom right corner from a plane that contains other corners,
    #: as well as maximum offset of a bottom left corner from a line drawn
    #: downdip perpendicular to top edge from top left corner, in kilometers.
    IMPERFECT_RECTANGLE_TOLERANCE = 0.3

    def __init__(self, mesh_spacing, strike, dip,
                 top_left, top_right, bottom_right, bottom_left):
        super(PlanarSurface, self).__init__()
        if not (top_left.depth == top_right.depth
                and bottom_left.depth == bottom_right.depth):
            raise ValueError("top and bottom edges must be parallel "
                             "to the earth surface")

        if not mesh_spacing > 0:
            raise ValueError("mesh spacing must be positive")
        self.mesh_spacing = mesh_spacing

        NodalPlane.check_dip(dip)
        NodalPlane.check_strike(strike)
        self.dip = dip
        self.strike = strike

        self.top_left = top_left
        self.top_right = top_right
        self.bottom_right = bottom_right
        self.bottom_left = bottom_left

        self.corner_lons = numpy.array([
            top_left.longitude, top_right.longitude,
            bottom_left.longitude, bottom_right.longitude
        ])
        self.corner_lats = numpy.array([
            top_left.latitude, top_right.latitude,
            bottom_left.latitude, bottom_right.latitude
        ])
        self.corner_depths = numpy.array([
            top_left.depth, top_right.depth,
            bottom_left.depth, bottom_right.depth
        ])
        tl, tr, bl, br = geo_utils.spherical_to_cartesian(
            self.corner_lons, self.corner_lats, self.corner_depths
        )

        # these two parameters define the plane that contains the surface
        # (in 3d Cartesian space): a normal unit vector,
        self.normal = geo_utils.normalized(numpy.cross(tl - tr, tl - bl))
        # ... and scalar "d" parameter from the plane equation (uses
        # an equation (3) from http://mathworld.wolfram.com/Plane.html)
        self.d = - (self.normal * tl).sum()

        # these two 3d vectors together with a zero point represent surface's
        # coordinate space (the way to translate 3d Cartesian space with
        # a center in earth's center to 2d space centered in surface's top
        # left corner with basis vectors directed to top right and bottom left
        # corners. see :meth:`_project`.
        self.uv1 = geo_utils.normalized(tr - tl)
        self.uv2 = numpy.cross(self.normal, self.uv1)
        self.zero_zero = tl

        # now we can check surface for validity
        dists, xx, yy = self._project(self.corner_lons, self.corner_lats,
                                      self.corner_depths)
        length1, length2 = xx[1] - xx[0], xx[3] - xx[2]
        width1, width2 = yy[2] - yy[0], yy[3] - yy[1]
        if numpy.max(numpy.abs(dists)) > self.IMPERFECT_RECTANGLE_TOLERANCE \
                or abs(width1 - width2) > self.IMPERFECT_RECTANGLE_TOLERANCE \
                or width2 < 0 \
                or abs(xx[0] - xx[2]) > self.IMPERFECT_RECTANGLE_TOLERANCE \
                or abs(length1 - length2) > self.IMPERFECT_RECTANGLE_TOLERANCE:
            raise ValueError("planar surface corners must "
                             "represent a rectangle")
        self.width = (width1 + width2) / 2.0
        self.length = (length1 + length2) / 2.0

    def _create_mesh(self):
        """
        See :meth:`nhlib.surface.base.BaseSurface._create_mesh`.
        """
        llons, llats, ldepths = geodetic.intervals_between(
            self.top_left.longitude, self.top_left.latitude,
            self.top_left.depth,
            self.bottom_left.longitude, self.bottom_left.latitude,
            self.bottom_left.depth,
            self.mesh_spacing
        )
        rlons, rlats, rdepths = geodetic.intervals_between(
            self.top_right.longitude, self.top_right.latitude,
            self.top_right.depth,
            self.bottom_right.longitude, self.bottom_right.latitude,
            self.bottom_right.depth,
            self.mesh_spacing
        )
        mlons, mlats, mdepths = [], [], []
        for i in xrange(len(llons)):
            lons, lats, depths = geodetic.intervals_between(
                llons[i], llats[i], ldepths[i], rlons[i], rlats[i], rdepths[i],
                self.mesh_spacing
            )
            mlons.append(lons)
            mlats.append(lats)
            mdepths.append(depths)
        return RectangularMesh(numpy.array(mlons), numpy.array(mlats),
                               numpy.array(mdepths))

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

    def _project(self, lons, lats, depths):
        """
        Project points to a surface's plane.

        Parameters are lists or numpy arrays of coordinates of points
        to project.

        :returns:
            A tuple of three items: distances between original points
            and surface's plane in km, "x" and "y" coordinates of points'
            projections to the plane (in a surface's coordinate space).
        """
        points = geo_utils.spherical_to_cartesian(lons, lats, depths)

        # uses method from http://www.9math.com/book/projection-point-plane
        dists = (self.normal * points).sum(axis=-1) + self.d
        t0 = - dists
        projs = points + self.normal * t0.reshape(t0.shape + (1, ))

        # translate projected points' to surface's coordinate space
        vectors2d = projs - self.zero_zero
        xx = (vectors2d * self.uv1).sum(axis=-1)
        yy = (vectors2d * self.uv2).sum(axis=-1)
        return dists, xx, yy

    def get_min_distance(self, mesh):
        """
        See :meth:`superclass' method
        <nhlib.geo.surface.base.get_min_distance>`.

        This is an optimized version specific to planar surface that doesn't
        make use of the mesh.
        """
        dists, xx, yy = self._project(mesh.lons, mesh.lats, mesh.depths)
        dists2d = []

        for i in xrange(len(xx)):
            x = xx[i]
            y = yy[i]
            # consider nine possible relative positions of surface rectangle
            # and a point and collect distances in ``dists2d`` list. note
            # that some of those distances can be negative, but that doesn't
            # matter since we use them in Pythagorean formula anyway
            if y < 0:
                if x < 0:
                    # *
                    #   0---
                    #   |  |
                    #   ----
                    dist = (x ** 2 + y ** 2) ** 0.5
                elif x > self.length:
                    #      *
                    # 0---
                    # |  |
                    # ----
                    dist = ((x - self.length) ** 2 + y ** 2) ** 0.5
                else:
                    #  *
                    # 0---
                    # |  |
                    # ----
                    dist = y
            elif y > self.width:
                if x < 0:
                    #   0---
                    #   |  |
                    #   ----
                    # *
                    dist = (x ** 2 + (y - self.width) ** 2) ** 0.5
                elif x > self.length:
                    # 0---
                    # |  |
                    # ----
                    #      *
                    dist = ((x - self.length) ** 2
                            + (y - self.width) ** 2) ** 0.5
                else:
                    # 0---
                    # |  |
                    # ----
                    #  *
                    dist = y - self.width
            elif x < 0:
                #   0---
                # * |  |
                #   ----
                dist = x
            elif x > self.length:
                # 0---
                # |  | *
                # ----
                dist = x - self.length
            else:
                # 0---
                # | *|
                # ----
                dist = 0.0

            dists2d.append(dist)

        # the actual minimum distance between a point and a surface is
        # a Pythagorean combination of distance between a point and a plane
        # and distance between point's projection on a surface's plane
        # and a surface rectangle.
        return numpy.sqrt(dists ** 2 + numpy.array(dists2d) ** 2)

    def _get_top_edge_centroid(self):
        """
        Overrides :meth:`superclass' method
        <nhlib.geo.surface.BaseSurface._get_top_edge_centroid>`
        in order to avoid creating a mesh.
        """
        lon, lat = geo_utils.get_middle_point(
            self.top_left.longitude, self.top_left.latitude,
            self.top_right.longitude, self.top_right.latitude
        )
        return Point(lon, lat, self.top_left.depth)

    def get_top_edge_depth(self):
        """
        Overrides :meth:`superclass' method
        <nhlib.geo.surface.BaseSurface.get_top_edge_depth>`
        in order to avoid creating a mesh.
        """
        return self.top_left.depth

    def get_joyner_boore_distance(self, mesh):
        """
        See :meth:`superclass' method
        <nhlib.geo.surface.base.get_joyner_boore_distance>`.

        This is an optimized version specific to planar surface that doesn't
        make use of the mesh.
        """
        # TODO: document the code
        arcs_lons = [self.top_left.longitude, self.bottom_left.longitude,
                     self.top_left.longitude, self.top_right.longitude]
        arcs_lats = [self.top_left.latitude, self.bottom_left.latitude,
                     self.top_left.latitude, self.top_right.latitude]
        downdip_azimuth = (self.strike + 90) % 360
        arcs_azimuths = [self.strike, self.strike,
                         downdip_azimuth, downdip_azimuth]
        mesh_lons = mesh.lons.reshape((-1, 1))
        mesh_lats = mesh.lats.reshape((-1, 1))
        dists_to_arcs = geodetic.distance_to_arc(
            arcs_lons, arcs_lats, arcs_azimuths, mesh_lons, mesh_lats
        )
        dists_to_corners = geodetic.geodetic_distance(
            self.corner_lons, self.corner_lats, mesh_lons, mesh_lats
        ).min(axis=-1)

        dists = numpy.zeros(len(mesh))
        dists_to_arcs_signs = numpy.sign(dists_to_arcs)
        dists_to_arcs = numpy.abs(dists_to_arcs).reshape(-1, 2, 2).min(axis=-1)
        for i, (ds1, ds2, ds3, ds4) in enumerate(dists_to_arcs_signs):
            if ds1 == ds2:
                if ds3 == ds4:
                    dists[i] = dists_to_corners[i]
                else:
                    dists[i] = dists_to_arcs[i][0]
            else:
                if ds3 == ds4:
                    dists[i] = dists_to_arcs[i][1]
                else:
                    dists[i] = 0

        return dists
