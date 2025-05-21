# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
import math
import logging
import numpy
import numba
from openquake.baselib.node import Node
from openquake.baselib.performance import compile
from openquake.hazardlib.geo.geodetic import (
    point_at, spherical_to_cartesian, fast_spherical_to_cartesian)
from openquake.hazardlib.geo import Point, Line
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
IMPERFECT_RECTANGLE_TOLERANCE = 0.004

planar_array_dt = numpy.dtype([
    ('corners', (float, 4)),
    ('xyz', (float, 4)),
    ('normal', float),
    ('uv1', float),
    ('uv2', float),
    ('wlr', float),
    ('sdr', float),
    ('hypo', float)])


planin_dt = numpy.dtype([
    ('mag', float),
    ('strike', float),
    ('dip', float),
    ('rake', float),
    ('rate', float),
    ('lon', float),
    ('lat', float),
    ('area', float),
])


@compile("(f8, f8, f8, f8, f8)")
def get_rupdims(usd, lsd, rar, area, dip):
    """
    :param usd: upper seismogenic depth
    :param lsd: lower seismogenic depth
    :param rar: rupture aspect ratio
    :param area: area of the surface
    :param dip: dip angle
    :returns:
        array of shape 3with rupture length, width and height

    The rupture area is calculated using the method
    :meth:`~openquake.hazardlib.scalerel.base.BaseMSR.get_median_area`.
    If the calculated rupture width, inclined by the nodal plane's
    dip angle, would not fit in between upper and lower seismogenic
    depth, the rupture width is shrunken to the maximum possible
    and the rupture length is extended to preserve the same area.
    """
    rdip = math.radians(dip)
    sindip = math.sin(rdip)
    cosdip = math.cos(rdip)
    max_width = (lsd - usd) / sindip
    rup_length = math.sqrt(area * rar)
    rup_width = area / rup_length
    if rup_width > max_width:
        rup_width = max_width
        rup_length = area / rup_width
    return numpy.array([rup_length, rup_width * cosdip, rup_width * sindip])


# From the rupture center we can compute the coordinates of the
# four coorners by moving along the diagonals of the plane. This seems
# to be better then moving along the perimeter, because in this case
# errors are accumulated that induce distorsions in the shape with
# consequent raise of exceptions when creating PlanarSurface objects;
# theta is the angle between the diagonal of the surface projection
# and the line passing through the rupture center and parallel to the
# top and bottom edges. Theta is zero for vertical ruptures (because
# rup_proj_width is zero)
@compile("(f8, f8, f8, f8, f8, f8, f8, f8, f8, f8, f8[:])")
def _build_corners(usd, lsd, rar, area, mag, strike, dip, rake,
                   clon, clat, cdeps):
    half_length, half_width, half_height = get_rupdims(
        usd, lsd, rar, area, dip) / 2.
    # precalculate azimuth values for horizontal and vertica moves
    # from one point to another on the plane defined by strike and dip
    azimuth_right = strike
    azimuth_down = azimuth_right + 90
    azimuth_left = azimuth_down + 90
    azimuth_up = azimuth_left + 90
    theta = math.degrees(math.atan(half_width / half_length))
    hor_dist = math.sqrt(half_length ** 2 + half_width ** 2)
    vshifts = numpy.zeros_like(cdeps)
    for d, cdep in enumerate(cdeps):
        # half height of the vertical component of rupture width
        # is the vertical distance between the rupture geometrical
        # center and it's upper and lower borders:
        # calculate how much shallower the upper border of the rupture
        # is than the upper seismogenic depth:
        vshift = usd - cdep + half_height
        # if it is shallower (vshift > 0) than we need to move the rupture
        # by that value vertically.
        if vshift < 0:
            # the top edge is below the upper seismogenic depth: we need
            # to check that we do not cross the lower border
            vshift = lsd - cdep - half_height
            if vshift > 0:
                # the bottom edge of the rupture is above the lower depth;
                # that means that we don't need to move the rupture
                # as it fits inside seismogenic layer.
                vshift = 0
        vshifts[d] = vshift
    if (vshifts == 0).any():
        lonlat = numpy.empty((4, 2))
        lonlat[0] = geodetic.fast_point_at(
            clon, clat, strike + 180 + theta, hor_dist)
        lonlat[1] = geodetic.fast_point_at(
            clon, clat, strike - theta, hor_dist)
        lonlat[2] = geodetic.fast_point_at(
            clon, clat, strike + 180 - theta, hor_dist)
        lonlat[3] = geodetic.fast_point_at(
            clon, clat, strike + theta, hor_dist)

    # build corners
    corners = numpy.zeros((6, len(cdeps), 3))
    for d, cdep in enumerate(cdeps):
        vshift = vshifts[d]
        # now we need to find the position of rupture's geometrical center.
        # in any case the hypocenter point must lie on the surface, however
        # the rupture center might be off (below or above) along the dip
        if vshift == 0:
            corners[:4, d, 0:2] = lonlat
        else:
            # we need to move the rupture center to make the rupture fit
            # inside the seismogenic layer
            lon, lat = geodetic.fast_point_at(
                clon, clat, azimuth_up if vshift < 0 else azimuth_down,
                abs(vshift / half_height * half_width))
            cdep += vshift
            corners[0, d, 0:2] = geodetic.fast_point_at(
                lon, lat, strike + 180 + theta, hor_dist)
            corners[1, d, 0:2] = geodetic.fast_point_at(
                lon, lat, strike - theta, hor_dist)
            corners[2, d, 0:2] = geodetic.fast_point_at(
                lon, lat, strike + 180 - theta, hor_dist)
            corners[3, d, 0:2] = geodetic.fast_point_at(
                lon, lat, strike + theta, hor_dist)
        corners[0:2, d, 2] = cdep - half_height
        corners[2:4, d, 2] = cdep + half_height
        corners[4, d, 0] = strike
        corners[4, d, 1] = dip
        corners[4, d, 2] = rake
        corners[5, d, 0] = clon
        corners[5, d, 1] = clat
        corners[5, d, 2] = cdep
    return corners


@compile("(f8, f8, f8, f8[:, :], f8[:, :], f8[:, :], "
         "f8[:, :], f8[:, :], f8[:, :], f8, f8)")
def build_corners(usd, lsd, rar, area, mag, strike,
                  dip, rake, hdd, lon, lat):
    M, N = mag.shape
    corners = numpy.zeros((6, M, N, len(hdd), 3))
    # 0,1,2,3: tl, tr, bl, br
    # 4: (strike, dip, rake)
    # 5: hypo
    for m in range(M):
        for n in range(N):
            corners[:, m, n]  = _build_corners(
                usd, lsd, rar, area[m, n], mag[m, n], strike[m, n],
                dip[m, n], rake[m, n], lon, lat, hdd[:, 1])
    return corners


# not numbified but fast anyway
def build_planar(planin, hdd, lon, lat, usd, lsd, rar, shift_hypo=False):
    """
    :param planin:
        Surface input parameters as an array of shape (M, N)
    :param hdd:
        Hypocenter depths
    :param lon, lat:
        Longitude and latitude of the hypocenters (scalars)
    :return:
        an array of shape (M, N, D, 3)
    """
    corners = build_corners(
        usd, lsd, rar, planin.area, planin.mag,
        planin.strike, planin.dip, planin.rake, hdd, lon, lat)
    planar_array = build_planar_array(corners[:4], corners[4], corners[5])
    for d, (drate, dep) in enumerate(hdd):
        planar_array.wlr[:, :, d, 2] = planin.rate * drate
        if not shift_hypo:  # use the original hypocenter
            planar_array.hypo[:, :, d, 0] = lon
            planar_array.hypo[:, :, d, 1] = lat
            planar_array.hypo[:, :, d, 2] = dep
    return planar_array


def dot(a, b):
    return (a[..., 0] * b[..., 0] +
            a[..., 1] * b[..., 1] +
            a[..., 2] * b[..., 2])


# not numbified but fast anyway
def build_planar_array(corners, sdr=None, hypo=None, check=False):
    """
    :param corners: array of shape (4, M, N, D, 3)
    :param hypo: None or array of shape (M, N, D, 3)
    :returns: a planar_array array of length (M, N, D, 3)
    """
    shape = corners.shape[:-1]  # (4, M, N, D)
    planar_array = numpy.zeros(corners.shape[1:], planar_array_dt).view(
        numpy.recarray)
    if sdr is not None:
        planar_array['sdr'] = sdr  # strike, dip, rake
    if hypo is not None:
        planar_array['hypo'] = hypo
    tl, tr, bl, _br = xyz = spherical_to_cartesian(
        corners[..., 0], corners[..., 1], corners[..., 2])
    for i, corner in enumerate(corners):
        planar_array['corners'][..., i] = corner
        planar_array['xyz'][..., i] = xyz[i]
    # these two parameters define the plane that contains the surface
    # (in 3d Cartesian space): a normal unit vector,
    planar_array['normal'] = n = geo_utils.normalized(
        numpy.cross(tl - tr, tl - bl))

    # these two 3d vectors together with a zero point represent surface's
    # coordinate space (the way to translate 3d Cartesian space with
    # a center in earth's center to 2d space centered in surface's top
    # left corner with basis vectors directed to top right and bottom left
    # corners. see :meth:`_project`.
    planar_array['uv1'] = uv1 = geo_utils.normalized(tr - tl)
    planar_array['uv2'] = uv2 = numpy.cross(n, uv1)

    # translate projected points to surface coordinate space, shape (N, 3)
    delta = xyz - xyz[0]
    dists, xx, yy = numpy.zeros(shape), numpy.zeros(shape), numpy.zeros(shape)
    for i in range(1, 4):
        mat = delta[i]
        dists[i], xx[i], yy[i] = dot(mat, n), dot(mat, uv1), dot(mat, uv2)

    # "length" of the rupture is measured along the top edge
    length1, length2 = xx[1] - xx[0], xx[3] - xx[2]
    # "width" of the rupture is measured along downdip direction
    width1, width2 = yy[2] - yy[0], yy[3] - yy[1]
    width = (width1 + width2) / 2.0
    length = (length1 + length2) / 2.0
    wlr = planar_array['wlr']
    wlr[..., 0] = width
    wlr[..., 1] = length

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


# numbified below
def project(planar, points):
    """
    :param planar: a planar recarray of shape (U, 3)
    :param points: an array of euclidean coordinates of shape (N, 3)
    :returns: (3, U, N) values
    """
    out = numpy.zeros((3, len(planar), len(points)))

    def dot(a, v):  # array @ vector
        return a[:, 0] * v[0] + a[:, 1] * v[1] + a[:, 2] * v[2]
    for u, pla in enumerate(planar):
        width, length, _ = pla.wlr
        # we project all the points of the mesh on a plane that contains
        # the surface (translating coordinates of the projections to a local
        # 2d space) and at the same time calculate the distance to that
        # plane.
        mat = points - pla.xyz[:, 0]
        dists = dot(mat, pla.normal)
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
            default=0.
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
        out[0, u] = numpy.sqrt(dists ** 2 + mxx ** 2 + myy ** 2)
        out[1, u] = xx
        out[2, u] = yy
    return out


# numbified below
def project_back(planar, xx, yy):
    """
    :param planar: a planar recarray of shape (U, 3)
    :param xx: an array of of shape (U, N)
    :param yy: an array of of shape (U, N)
    :returns: (3, U, N) values
    """
    U, N = xx.shape
    arr = numpy.zeros((3, U, N))
    for u in range(U):
        arr3N = numpy.zeros((3, N))
        mxx = numpy.clip(xx[u], 0., planar.wlr[u, 1])
        myy = numpy.clip(yy[u], 0., planar.wlr[u, 0])
        for i in range(3):
            arr3N[i] = (planar.xyz[u, i, 0] +
                        planar.uv1[u, i] * mxx +
                        planar.uv2[u, i] * myy)
        arr[:, u] = geo_utils.cartesian_to_spherical(arr3N.T)
    return arr


# NB: we define four great circle arcs that contain four sides
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
def get_rjb(planar, points):  # numbified below
    """
    :param planar: a planar recarray of shape (U, 3)
    :param points: an array of of shape (N, 3)
    :returns: (U, N) values
    """
    lons, lats, _deps = geo_utils.cartesian_to_spherical(points)
    out = numpy.zeros((len(planar), len(points)))
    for u, pla in enumerate(planar):
        strike, _dip, _rake = pla['sdr']
        downdip = (strike + 90) % 360
        corners = pla.corners
        clons, clats = numpy.zeros(4), numpy.zeros(4)
        clons[:], clats[:] = corners[0], corners[1]
        dists_to_arcs = numpy.zeros((len(lons), 4))  # shape (N, 4)
        # calculate distances from all the target points to all four arcs
        dists_to_arcs[:, 0] = geodetic.distances_to_arc(
            clons[2], clats[2], strike, lons, lats)
        dists_to_arcs[:, 1] = geodetic.distances_to_arc(
            clons[0], clats[0], strike, lons, lats)
        dists_to_arcs[:, 2] = geodetic.distances_to_arc(
            clons[0], clats[0], downdip, lons, lats)
        dists_to_arcs[:, 3] = geodetic.distances_to_arc(
            clons[1], clats[1], downdip, lons, lats)

        # distances from all the target points to each of surface's
        # corners' projections (we might not need all of those but it's
        # better to do that calculation once for all).
        corners = fast_spherical_to_cartesian(clons, clats, numpy.zeros(4))
        # shape (4, 3) and (N, 3) -> (4, N) -> N
        dists_to_corners = numpy.array([geo_utils.min_distance(point, corners)
                                        for point in points])

        # extract from ``dists_to_arcs`` signs (represent relative positions
        # of an arc and a point: +1 means on the left hand side, 0 means
        # on arc and -1 means on the right hand side) and minimum absolute
        # values of distances to each pair of parallel arcs.
        ds1, ds2, ds3, ds4 = numpy.sign(dists_to_arcs).transpose()
        dta = numpy.abs(dists_to_arcs).reshape(-1, 2, 2)
        dists_to_arcs0 = numpy.array([d2[0].min() for d2 in dta])
        dists_to_arcs1 = numpy.array([d2[1].min() for d2 in dta])

        out[u] = numpy.select(
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
                dists_to_arcs0,
                # case "III": closest distance is distance to either
                # arc "3" or "4"
                dists_to_arcs1
            ],

            # default -- case "IV"
            default=0.)
    return out


# numbified below
def get_rx(planar, points):
    """
    :param planar: a planar recarray of shape (U, 3)
    :param points: an array of of shape (N, 3)
    :returns: (U, N) distances
    """
    lons, lats, _deps = geo_utils.cartesian_to_spherical(points)
    out = numpy.zeros((len(planar), len(points)))
    for u, pla in enumerate(planar):
        clon, clat, _ = pla.corners[:, 0]
        strike = pla.sdr[0]
        out[u] = geodetic.distances_to_arc(clon, clat, strike, lons, lats)
    return out


# numbified below
def get_ry0(planar, points):
    """
    :param planar: a planar recarray of shape (U, 3)
    :param points: an array of of shape (N, 3)
    :returns: (U, N) distances
    """
    lons, lats, _deps = geo_utils.cartesian_to_spherical(points)
    out = numpy.zeros((len(planar), len(points)))
    for u, pla in enumerate(planar):
        llon, llat, _ = pla.corners[:, 0]  # top left
        rlon, rlat, _ = pla.corners[:, 1]  # top right
        strike = (pla.sdr[0] + 90.) % 360.

        dst1 = geodetic.distances_to_arc(llon, llat, strike, lons, lats)
        dst2 = geodetic.distances_to_arc(rlon, rlat, strike, lons, lats)

        # Get the shortest distance from the two lines
        idx = numpy.sign(dst1) == numpy.sign(dst2)
        out[u][idx] = numpy.fmin(numpy.abs(dst1[idx]), numpy.abs(dst2[idx]))
    return out


# numbified below
def get_rhypo(planar, points):
    """
    :param planar: a planar recarray of shape (U, 3)
    :param points: an array of of shape (N, 3)
    :returns: (U, N) distances
    """
    out = numpy.zeros((len(planar), len(points)))
    lons, lats, deps = geo_utils.cartesian_to_spherical(points)
    hypo = planar.hypo
    for u, pla in enumerate(planar):
        hdist = geodetic.distances(
            math.radians(hypo[u, 0]), math.radians(hypo[u, 1]),
            numpy.radians(lons), numpy.radians(lats))
        vdist = hypo[u, 2] - deps
        out[u] = numpy.sqrt(hdist ** 2 + vdist ** 2)
    return out


# numbified below
def get_repi(planar, points):
    """
    :param planar: a planar recarray of shape (U, 3)
    :param points: an array of of shape (N, 3)
    :returns: (U, N) distances
    """
    out = numpy.zeros((len(planar), len(points)))
    lons, lats, _deps = geo_utils.cartesian_to_spherical(points)
    hypo = planar.hypo
    for u, pla in enumerate(planar):
        out[u] = geodetic.distances(
            math.radians(hypo[u, 0]), math.radians(hypo[u, 1]),
            numpy.radians(lons), numpy.radians(lats))
    return out


# numbified below
def get_azimuth(planar, points):
    """
    :param planar: a planar recarray of shape (U, 3)
    :param points: an array of of shape (N, 3)
    :returns: (U, N) distances
    """
    out = numpy.zeros((len(planar), len(points)))
    lons, lats, _deps = geo_utils.cartesian_to_spherical(points)
    hypo = planar.hypo
    for u, pla in enumerate(planar):
        azim = geodetic.fast_azimuth(hypo[u, 0], hypo[u, 1], lons, lats)
        strike = planar.sdr[u, 0]
        out[u] = (azim - strike) % 360
    return out


# TODO: fix this
def get_rvolc(planar, points):
    """
    :param planar: a planar recarray of shape (U, 3)
    :param points: an array of of shape (N, 3)
    :returns: (U, N) distances
    """
    return numpy.zeros((len(planar), len(points)))


planar_nt = numba.from_dtype(planar_array_dt)
project = compile(numba.float64[:, :, :](
    planar_nt[:, :],
    numba.float64[:, :]
))(project)
project_back = compile(numba.float64[:, :, :](
    planar_nt[:, :],
    numba.float64[:, :],
    numba.float64[:, :]
))(project_back)
comp = compile(numba.float64[:, :](planar_nt[:, :], numba.float64[:, :]))
get_rjb = comp(get_rjb)
get_rx = comp(get_rx)
get_ry0 = comp(get_ry0)
get_rhypo = comp(get_rhypo)
get_repi = comp(get_repi)
get_azimuth = comp(get_azimuth)
get_rvolc = comp(get_rvolc)


def get_distances_planar(planar, sites, dist_type):
    """
    :param planar: a planar array of shape (U, 3)
    :param sites: a filtered site collection with N sites
    :param dist_type: kind of distance to compute
    :returns: an array of distances of shape (U, N)
    """
    getdist = globals()['get_' + dist_type]
    return getdist(planar, sites.xyz)


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
    def mesh(self):  # used in event based
        """
        :returns: a mesh with the 4 corner points tl, tr, bl, br
        """
        return Mesh(*self.array.corners)

    @property
    def corner_lons(self):
        return self.array.corners[0]

    @property
    def corner_lats(self):
        return self.array.corners[1]

    @property
    def corner_depths(self):
        return self.array.corners[2]

    @property
    def tor(self):
        """
        :returns: top of rupture line
        """
        lo = []
        la = []
        for pnt in [self.top_left, self.top_right]:
            lo.append(pnt.longitude)
            la.append(pnt.latitude)
        return Line.from_vectors(lo, la)

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
        self._init_plane(check, [float(strike), float(dip), 0.])

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
    def from_hypocenter(cls, hypoc, msr, mag, aratio, strike, dip, rake,
                        ztor=None):
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
        :param ztor:
            If not None it doesn't consider the hypocentral depth constraint
        """
        lon = hypoc.longitude
        lat = hypoc.latitude
        depth = hypoc.depth

        area = msr.get_median_area(mag, rake)
        width = (area / aratio) ** 0.5
        length = width * aratio

        #
        #     .....     the dotted line is the width
        #     \      |
        #      \     |  this dashed vertical line is the height
        #       \    |
        #        \   |
        # rupture \  |
        #
        height = width * numpy.sin(numpy.radians(dip))
        hdist = width * numpy.cos(numpy.radians(dip))

        if ztor is not None:
            depth = ztor + height / 2

        # Move hor. 1/2 hdist in direction -90
        mid_top = point_at(lon, lat, strike - 90, hdist / 2)
        # Move hor. 1/2 hdist in direction +90
        mid_bot = point_at(lon, lat, strike + 90, hdist / 2)

        # compute corner points at the surface
        top_right = point_at(mid_top[0], mid_top[1], strike, length / 2)
        top_left = point_at(mid_top[0], mid_top[1], strike + 180, length / 2)
        bot_right = point_at(mid_bot[0], mid_bot[1], strike, length/2)
        bot_left = point_at(mid_bot[0], mid_bot[1], strike + 180, length / 2)

        # compute corner points in 3D; rounded to 5 digits to avoid having
        # slightly different surfaces between macos and linux
        pbl = Point(bot_left[0], bot_left[1], depth + height / 2).round()
        pbr = Point(bot_right[0], bot_right[1], depth + height / 2).round()
        ptl = Point(top_left[0], top_left[1], depth - height / 2).round()
        ptr = Point(top_right[0], top_right[1], depth - height / 2).round()
        return cls(strike, dip, ptl, ptr, pbr, pbl)

    @classmethod
    def from_(cls, planar_array):
        self = object.__new__(PlanarSurface)
        sdr = planar_array['sdr']
        self.strike = sdr[..., 0]
        self.dip = sdr[..., 1]
        self.array = planar_array
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

    def _init_plane(self, check=False, sdr=None):
        """
        Prepare everything needed for projecting arbitrary points on a plane
        containing the surface.
        """
        self.array = build_planar_array(self.corners, sdr, check=check)

    # this is not used anymore by the engine
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

    @property  # used in the SMT module of the OQ-MBTK
    def length(self):
        """
        Return length of the rupture
        """
        return self.array.wlr[1]

    @property  # used in the SMT module of the OQ-MBTK
    def width(self):
        """
        Return length of the rupture
        """
        return self.array.wlr[0]

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

    def get_min_distance(self, mesh):
        """
        See :meth:`superclass' method
        <openquake.hazardlib.geo.surface.base.BaseSurface.get_min_distance>`.
        """
        return project(self.array.reshape(1, 3), mesh.xyz)[0, 0]

    def get_closest_points(self, mesh):
        """
        See :meth:`superclass' method
        <openquake.hazardlib.geo.surface.base.BaseSurface.get_closest_points>`.
        """
        array = self.array
        mat = mesh.xyz - array.xyz[:, 0]
        xx = numpy.clip(mat @ array.uv1, 0, array.wlr[1])
        yy = numpy.clip(mat @ array.uv2, 0, array.wlr[0])
        vectors = (array.xyz[:, 0] +
                   array.uv1 * xx.reshape(xx.shape + (1, )) +
                   array.uv2 * yy.reshape(yy.shape + (1, )))
        return Mesh(*geo_utils.cartesian_to_spherical(vectors))

    def get_top_edge_centroid(self):
        """
        Overrides :meth:`superclass' method
        <openquake.hazardlib.geo.surface.base.BaseSurface.get_top_edge_centroid>`
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
        rjb = get_rjb(self.array.reshape(1, 3), mesh.xyz)[0]
        return rjb

    def get_rx_distance(self, mesh):
        """
        See :meth:`superclass method
        <.base.BaseSurface.get_rx_distance>`
        for spec of input and result values.

        This is an optimized version specific to planar surface that doesn't
        make use of the mesh.
        """
        return get_rx(self.array.reshape(1, 3), mesh.xyz)[0]

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
        return get_ry0(self.array.reshape(1, 3), mesh.xyz)[0]

    def get_width(self):
        """
        Return surface's width value (in km) as computed in the constructor
        (that is mean value of left and right surface sides).
        """
        return self.array.wlr[0]

    def get_area(self):
        """
        Return surface's area value (in squared km) obtained as the product
        of surface length and width.
        """
        return self.array.wlr[0] * self.array.wlr[1]

    def get_bounding_box(self):
        """
        Compute surface bounding box from plane's corners coordinates. Calls
        :meth:`openquake.hazardlib.geo.utils.get_spherical_bounding_box`

        :return:
            A tuple of four items. These items represent western, eastern,
            northern and southern borders of the bounding box respectively.
            Values are floats in decimal degrees.
        """
        return geo_utils.get_spherical_bounding_box(self.corner_lons, self.corner_lats)

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
