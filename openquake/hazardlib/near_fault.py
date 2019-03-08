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
Module :mod:`openquake.hazardlib.nearfault` provides methods for near fault
PSHA calculation.
"""

import math
import numpy as np
from openquake.hazardlib.geo import geodetic as geod
import scipy.spatial.distance as dst


def get_xyz_from_ll(projected, reference):
    """
    This method computes the x, y and z coordinates of a set of points
    provided a reference point

    :param projected:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the coordinates of target point to be projected
    :param reference:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the coordinates of the reference point.

    :returns:
            x
            y
            z
    """

    azims = geod.azimuth(reference.longitude, reference.latitude,
                         projected.longitude, projected.latitude)
    depths = np.subtract(reference.depth, projected.depth)
    dists = geod.geodetic_distance(reference.longitude,
                                   reference.latitude,
                                   projected.longitude,
                                   projected.latitude)
    return (dists * math.sin(math.radians(azims)),
            dists * math.cos(math.radians(azims)),
            depths)


def get_plane_equation(p0, p1, p2, reference):
    '''
    Define the equation of target fault plane passing through 3 given points
    which includes two points on the fault trace and one point on the
    fault plane but away from the fault trace. Note: in order to remain the
    consistency of the fault normal vector direction definition, the order
    of the three given points is strickly defined.

    :param p0:
        The fault trace and is the closer points from the starting point of
        fault trace.
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the one vertex of the fault patch.
    :param p1:
        The fault trace and is the further points from the starting point of
        fault trace.
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the one vertex of the fault patch.
    :param p2:
        The point on the fault plane but away from the fault trace.
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the one vertex of the fault patch.
    :param reference:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the origin of the cartesian system used the represent
        objects in a projected reference
    :returns:
        normal: normal vector of the plane (a,b,c)
        dist_to_plane: d in the plane equation, ax + by + cz = d
    '''

    p0_xyz = get_xyz_from_ll(p0, reference)
    p1_xyz = get_xyz_from_ll(p1, reference)
    p2_xyz = get_xyz_from_ll(p2, reference)

    p0 = np.array(p0_xyz)
    p1 = np.array(p1_xyz)
    p2 = np.array(p2_xyz)

    u = p1 - p0
    v = p2 - p0

    # vector normal to plane, ax+by+cy = d, normal=(a,b,c)
    normal = np.cross(u, v)

    # Define the d for the plane equation
    dist_to_plane = np.dot(p0, normal)

    return normal, dist_to_plane


def projection_pp(site, normal, dist_to_plane, reference):
    '''
    This method finds the projection of the site onto the plane containing
    the slipped area, defined as the Pp(i.e. 'perpendicular projection of
    site location onto the fault plane' Spudich et al. (2013) - page 88)
    given a site.

    :param site:
        Location of the site, [lon, lat, dep]
    :param normal:
        Normal to the plane including the fault patch,
        describe by a normal vector[a, b, c]
    :param dist_to_plane:
        D in the plane equation,  ax + by + cz = d
    :param reference:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of project reference point
    :returns:
        pp, the projection point, [ppx, ppy, ppz], in xyz domain
        , a numpy array.
    '''

    # Transform to xyz coordinate
    [site_x, site_y, site_z] = get_xyz_from_ll(site, reference)

    a = np.array([(1, 0, 0, -normal[0]),
                  (0, 1, 0, -normal[1]),
                  (0, 0, 1, -normal[2]),
                  (normal[0], normal[1], normal[2], 0)])
    b = np.array([site_x, site_y, site_z, dist_to_plane])

    x = np.linalg.solve(a, b)
    pp = np.array([x[0], x[1], x[2]])
    return pp


def vectors2angle(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'.

    :param v1:
        vector, a numpy array
    :param v2:
        vector, a numpy array
    :returns:
        the angle in radians between the two vetors
    """
    cosang = np.dot(v1, v2)
    sinang = np.linalg.norm(np.cross(v1, v2))
    return np.arctan2(sinang, cosang)


def average_s_rad(site, hypocenter, reference, pp,
                  normal, dist_to_plane, e, p0, p1, delta_slip):
    """
    Gets the average S-wave radiation pattern given an e-path as described in:
    Spudich et al. (2013) "Final report of the NGA-West2 directivity working
    group", PEER report, page 90- 92 and computes: the site to the direct point
    distance, rd, and the hypocentral distance, r_hyp.

    :param site:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the target site
    :param hypocenter:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of hypocenter
    :param reference:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location
        of the reference point for coordinate projection within the
        calculation. The suggested reference point is Epicentre.
    :param pp:
        the projection point pp on the patch plane,
        a numpy array
    :param normal:
        normal of the plane, describe by a normal vector[a, b, c]
    :param dist_to_plane:
        d is the constant term in the plane equation, e.g., ax + by + cz = d
    :param e:
        a float defining the E-path length, which is the distance from
        Pd(direction) point to hypocentre. In km.
    :param p0:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the starting point on fault segment
    :param p1:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the ending point on fault segment.
    :param delta_slip:
        slip direction away from the strike direction, in decimal degrees.
        A positive angle is generated by a counter-clockwise rotation.
    :returns:
        fs, float value of the average S-wave radiation pattern.
        rd, float value of the distance from site to the direct point.
        r_hyp, float value of the hypocetre distance.
    """
    # Obtain the distance of Ps and Pp. If Ps is above the fault plane
    # zs is positive, and negative when Ps is below the fault plane
    site_xyz = get_xyz_from_ll(site, reference)
    zs = dst.pdist([pp, site_xyz])

    if site_xyz[0] * normal[0] + site_xyz[1] * normal[1] + site_xyz[2] * \
       normal[2] - dist_to_plane > 0:
        zs = -zs

    # Obtain the distance of Pp and hypocentre
    hyp_xyz = get_xyz_from_ll(hypocenter, reference)
    hyp_xyz = np.array(hyp_xyz).reshape(1, 3).flatten()
    l2 = dst.pdist([pp, hyp_xyz])

    rd = ((l2 - e) ** 2 + zs ** 2) ** 0.5
    r_hyp = (l2 ** 2 + zs ** 2) ** 0.5
    p0_xyz = get_xyz_from_ll(p0, reference)
    p1_xyz = get_xyz_from_ll(p1, reference)
    u = (np.array(p1_xyz) - np.array(p0_xyz))
    v = pp - hyp_xyz
    phi = vectors2angle(u, v) - np.deg2rad(delta_slip)
    ix = np.cos(phi) * (2 * zs * (l2 / r_hyp - (l2 - e) / rd) -
                        zs * np.log((l2 + r_hyp) / (l2 - e + rd)))
    inn = np.cos(phi) * (-2 * zs ** 2 * (1 / r_hyp - 1 / rd)
                         - (r_hyp - rd))
    iphi = np.sin(phi) * (zs * np.log((l2 + r_hyp) / (l2 - e + rd)))

    # Obtain the final average radiation pattern value
    fs = (ix ** 2 + inn ** 2 + iphi ** 2) ** 0.5 / e

    return fs, rd, r_hyp


def isochone_ratio(e, rd, r_hyp):
    """
    Get the isochone ratio as described in Spudich et al. (2013) PEER
    report, page 88.

    :param e:
        a float defining the E-path length, which is the distance from
        Pd(direction) point to hypocentre. In km.
    :param rd:
        float, distance from the site to the direct point.
    :param r_hyp:
        float, the hypocentre distance.
    :returns:
        c_prime, a float defining the isochone ratio
    """

    if e == 0.:
        c_prime = 0.8
    elif e > 0.:
        c_prime = 1. / ((1. / 0.8) - ((r_hyp - rd) / e))

    return c_prime


def _intersection(seg1_start, seg1_end, seg2_start, seg2_end):
    """
    Get the intersection point between two segments. The calculation is in
    Catestian coordinate system.

    :param seg1_start:
        A numpy array,
        representing one end point of a segment(e.g. segment1)
        segment.
    :param seg1_end:
        A numpy array,
        representing the other end point of the first segment(e.g. segment1)
    :param seg2_start:
        A numpy array,
        representing one end point of the other segment(e.g. segment2)
        segment.
    :param seg2_end:
        A numpy array,
        representing the other end point of the second segment(e.g. segment2)
    :returns:
        p_intersect, :a numpy ndarray.
        representing the location of intersection point of the two
        given segments
        vector1, a numpy array, vector defined by intersection point and
        seg2_end
        vector2, a numpy array, vector defined by seg2_start and seg2_end
        vector3, a numpy array, vector defined by seg1_start and seg1_end
        vector4, a numpy array, vector defined by intersection point
        and seg1_start
    """

    pa = np.array([seg1_start, seg2_start])
    pb = np.array([seg1_end, seg2_end])

    si = pb - pa

    ni = si / np.power(
        np.dot(np.sum(si ** 2, axis=1).reshape(2, 1),
               np.ones((1, 3))), 0.5)

    nx = ni[:, 0].reshape(2, 1)
    ny = ni[:, 1].reshape(2, 1)
    nz = ni[:, 2].reshape(2, 1)
    sxx = np.sum(nx ** 2 - 1)
    syy = np.sum(ny ** 2 - 1)
    szz = np.sum(nz ** 2 - 1)
    sxy = np.sum(nx * ny)
    sxz = np.sum(nx * nz)
    syz = np.sum(ny * nz)
    s = np.array([sxx, sxy, sxz, sxy, syy, syz, sxz, syz,
                 szz]).reshape(3, 3)

    cx = np.sum(pa[:, 0].reshape(2, 1) * (nx ** 2 - 1) +
                pa[:, 1].reshape(2, 1) * [nx * ny] +
                pa[:, 2].reshape(2, 1) * (nx * nz))
    cy = np.sum(pa[:, 0].reshape(2, 1) * [nx * ny] +
                pa[:, 1].reshape(2, 1) * [ny ** 2 - 1] +
                pa[:, 2].reshape(2, 1) * [ny * nz])
    cz = np.sum(pa[:, 0].reshape(2, 1) * [nx * nz] +
                pa[:, 1].reshape(2, 1) * [ny * nz] +
                pa[:, 2].reshape(2, 1) * [nz ** 2 - 1])
    c = np.array([cx, cy, cz]).reshape(3, 1)
    p_intersect = np.linalg.solve(s, c)

    vector1 = (p_intersect.flatten() - seg2_end) / \
        sum((p_intersect.flatten() - seg2_end) ** 2) ** 0.5
    vector2 = (seg2_start - seg2_end) / \
        sum((seg2_start - seg2_end) ** 2) ** 0.5
    vector3 = (seg1_end - seg1_start) / \
        sum((seg1_end - seg1_start) ** 2) ** 0.5
    vector4 = (p_intersect.flatten() - seg1_start) / \
        sum((p_intersect.flatten() - seg1_start) ** 2) ** 0.5

    return p_intersect, vector1, vector2, vector3, vector4


def directp(node0, node1, node2, node3, hypocenter, reference, pp):
    """
    Get the Direct Point and the corresponding E-path as described in
    Spudich et al. (2013). This method also provides a logical variable
    stating if the DPP calculation must consider the neighbouring patch.
    To define the intersection point(Pd) of PpPh line segment and fault plane,
    we obtain the intersection points(Pd) with each side of fault plan, and
    check which intersection point(Pd) is the one fitting the definition in
    the Chiou and Spudich(2014) directivity model.
    Two possible locations for Pd, the first case, Pd locates on the side of
    the fault patch when Pp is not inside the fault patch. The second case is
    when Pp is inside the fault patch, then Pd=Pp.

    For the first case, it follows three conditions:
    1. the PpPh and PdPh line vector are the same,
    2. PpPh >= PdPh,
    3. Pd is not inside the fault patch.

    If we can not find solution for all the four possible intersection points
    for the first case, we check if the intersection point fit the second case
    by checking if Pp is inside the fault patch.

    Because of the coordinate system mapping(from geographic system to
    Catestian system), we allow an error when we check the location. The allow
    error will keep increasing after each loop when no solution in the two
    cases are found, until the solution get obtained.

    :param node0:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of one vertices on the target fault
        segment.
    :param node1:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of one vertices on the target fault
        segment. Note, the order should be clockwise.
    :param node2:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of one vertices on the target fault
        segment. Note, the order should be clockwise.
    :param node3:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of one vertices on the target fault
        segment. Note, the order should be clockwise.
    :param hypocenter:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of floating hypocenter on each segment
        calculation. In the method, we take the direction point of the
        previous fault patch as hypocentre for the current fault patch.
    :param reference:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of reference point for projection
    :param pp:
        the projection of the site onto the plane containing the fault
        slipped area. A numpy array.
    :returns:
        Pd, a numpy array, representing the location of direction point
        E, the distance from direction point to hypocentre.
        go_next_patch, flag indicates if the calculation goes on the next
        fault patch. 1: yes, 0: no.
    """

    # Find the intersection point Pd, by checking if the PdPh share the
    # same vector with PpPh,  and PpPh >= PdPh
    # Transform to xyz coordinate

    node0_xyz = get_xyz_from_ll(node0, reference)
    node1_xyz = get_xyz_from_ll(node1, reference)
    node2_xyz = get_xyz_from_ll(node2, reference)
    node3_xyz = get_xyz_from_ll(node3, reference)
    hypocenter_xyz = get_xyz_from_ll(hypocenter, reference)
    hypocenter_xyz = np.array(hypocenter_xyz).flatten()

    pp_xyz = pp

    e = []

    # Loop each segments on the patch to find Pd
    segment_s = [node0_xyz, node1_xyz, node2_xyz, node3_xyz]
    segment_e = [node1_xyz, node2_xyz, node3_xyz, node0_xyz]

    # set buffering bu
    buf = 0.0001
    atol = 0.0001

    loop = True
    exit_flag = False
    looptime = 0.
    while loop:
        x_min = np.min(np.array([node0_xyz[0], node1_xyz[0], node2_xyz[0],
                                node3_xyz[0]])) - buf
        x_max = np.max(np.array([node0_xyz[0], node1_xyz[0], node2_xyz[0],
                                node3_xyz[0]])) + buf
        y_min = np.min(np.array([node0_xyz[1], node1_xyz[1], node2_xyz[1],
                                node3_xyz[1]])) - buf
        y_max = np.max(np.array([node0_xyz[1], node1_xyz[1], node2_xyz[1],
                                node3_xyz[1]])) + buf
        n_seg = 0
        exit_flag = False
        for (seg_s, seg_e) in zip(segment_s, segment_e):
            seg_s = np.array(seg_s).flatten()
            seg_e = np.array(seg_e).flatten()
            p_intersect, vector1, vector2, vector3, vector4 = _intersection(
                seg_s, seg_e, pp_xyz, hypocenter_xyz)

            ppph = dst.pdist([pp, hypocenter_xyz])
            pdph = dst.pdist([p_intersect.flatten(), hypocenter_xyz])
            n_seg = n_seg + 1

            # Check that the direction of the hyp-pp and hyp-pd vectors
            # have are the same.
            if (np.allclose(vector1.flatten(), vector2,
                            atol=atol, rtol=0.)):
                if ((np.allclose(vector3.flatten(), vector4, atol=atol,
                                 rtol=0.))):

                    # Check if ppph >= pdph.
                    if (ppph >= pdph):
                        if (p_intersect[0] >= x_min) & (p_intersect[0] <=
                                                        x_max):
                            if (p_intersect[1] >= y_min) & (p_intersect[1]
                                                            <= y_max):
                                e = pdph
                                pd = p_intersect
                                exit_flag = True
                                break
            # when the pp located within the fault rupture plane, e = ppph
            if not e:
                if (pp_xyz[0] >= x_min) & (pp_xyz[0] <= x_max):
                    if (pp_xyz[1] >= y_min) & (pp_xyz[1] <= y_max):
                        pd = pp_xyz
                        e = ppph
                        exit_flag = True
        if exit_flag:
            break

        if not e:
            looptime += 1
            atol = 0.0001 * looptime
            buf = 0.0001 * looptime
    # if pd is located at 2nd fault segment, then the DPP calculation will
    # keep going on the next fault patch
    if n_seg == 2:
        go_next_patch = True
    else:
        go_next_patch = False

    return pd, e, go_next_patch
