# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
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
Module :mod:`openquake.hazardlib.nearfault` provides methods for near fault
PSHA calculation.
"""

import math
import numpy as np
from openquake.hazardlib.geo import geodetic as geod
import scipy.spatial.distance as dst


def get_xyz_from_ll(projected, reference):
    """
    This method computes the x ,y and z coordinates of a set of points
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
    Define plane equation by 3 given points, p0, p1, p2, which format in
    class:`~openquake.hazardlib.geo.point.Point` object

    :param p0:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the one vertex of the fault patch.
    :param p1:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the one vertex of the fault patch.
        Note: the order of the vertex should give
        in clockwise.
    :param p2:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the one vertex of the fault patch.
        Note: the order of the vertex should give
        in clockwise.
    :param reference:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of project reference point
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
    Find the projection point Pp on the patch plane

    :param site:
        Location of the site, [lon, lat, dep]
    :param normal:
        normal of the plane, describe by a normal vector[a, b, c]
    :param dist_to_plane:
            d in the plane equation,  ax + by + cz = d
    :param reference:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of project reference point
    :returns:
        pp, the projection point, [ppx, ppy, ppz], in xyz domain
        format in numpy array
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
        vector, format in numpy array
    :param v2:
        vector, format in numpy array
    :return:
        the angle in radians between the two vetors
    """
    cosang = np.dot(v1, v2)
    sinang = np.linalg.norm(np.cross(v1, v2))
    return np.arctan2(sinang, cosang)

def average_s_rad(site, hypocenter, reference, pp,
                  normal, dist_to_plane, e, p0, p1, delta_slip):
    """
    Get the average S-wave radiation pattern over E-path desrcibed in:
    "Final report of the NGA-West2 directivity working group." (2013) by
    Spudich, Paul, et al. and publish in PEER report, page 90- 92. Also
    obtain the site to direct point distance, rd, and the hypocentre
    distance, r_hyp.

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
        format in numpy array
    :param normal:
        normal of the plane, describe by a normal vector[a, b, c]
    :param dist_to_plane:
        d in the plane equation,  ax + by + cz = d
    :param e:
        E-path, in km.
    :param p0:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the starting point on fault segment
    :param p1:
        :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of the ending point on fault segment.
    :param delta_slip:
        slip direction away from the strike direction, in decimal degrees.
        A positive angle is generated by a counter-clockwise rotation.
    :return:
        fs, float value of the average S-wave radiation pattern.
        rd, the distance from site to the direct point.
        r_hyp, the hypocetre distance. Both distance calculation has been
        sugggested in the Spudich, et al.(2013)
    """
    # zs

    site_xyz = get_xyz_from_ll(site, reference)
    zs = dst.pdist([pp, site_xyz])

    if site_xyz[0] * normal[0] + site_xyz[1] * normal[1] + site_xyz[2] * \
       normal[2] - dist_to_plane > 0:
        zs = -zs

    # l2

    hyp_xyz = get_xyz_from_ll(hypocenter, reference)
    hyp_xyz = np.array(hyp_xyz).reshape(1, 3).flatten()
    l2 = dst.pdist([pp, hyp_xyz])

    # Rd

    rd = ((l2 - e) ** 2 + zs ** 2) ** 0.5

    # Rhyp

    r_hyp = (l2 ** 2 + zs ** 2) ** 0.5

    # phi

    p0_xyz = get_xyz_from_ll(p0, reference)
    p1_xyz = get_xyz_from_ll(p1, reference)
    u = (np.array(p1_xyz) - np.array(p0_xyz))
    v = pp - hyp_xyz
    phi = vectors2angle(u, v) - np.deg2rad(delta_slip)

    # Ix

    ix = np.cos(phi) * (2 * zs * (l2 / r_hyp - (l2 - e) / rd) -
                        zs * np.log((l2 + r_hyp) / (l2 - e + rd)))

    # In

    inn = np.cos(phi) * (-2 * zs ** 2 * (1 / r_hyp - 1 / rd)
                         - (r_hyp - rd))

    # Iphi

    iphi = np.sin(phi) * (zs * np.log((l2 + r_hyp) / (l2 - e + rd)))

    # FS

    fs = (ix ** 2 + inn ** 2 + iphi ** 2) ** 0.5 / e

    return fs, rd, r_hyp

def isochone_ratio(e, rd, r_hyp):
    """
    Get the isochone ratio which desrcibed in: "Final
    report of the NGA-West2 directivity working group." (2013) by Spudich,
    Paul, et al. and publish in PEER report, page 88.
    :param e:
        E-path, in km.
    :param rd:
        float, distance from the site to the direct point.
    :param r_hyp:
        float, the hypocentre distance.
    :return:
        c_prime, float valut, the isochone ration.
    """

    if e == 0.:
        c_prime = 0.8
    elif e > 0.:
        c_prime = 1. / ((1. / 0.8) - ((r_hyp - rd) / e))

    return c_prime

def directp(node0, node1, node2, node3, hypocenter, reference, pp):
    """
    Get the Direct Point and the corresponding E-path desrcibed in: "Final
    report of the NGA-West2 directivity working group." (2013) by Spudich,
    Paul, et al. and publish in PEER report, page 85- 96. Also obtain the
    flag if the DPP calculation keep going on the next fault segment(in the
    case of multi-segment).
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
        the projection point pp on the patch plane,
        format in numpy array
    :return:
        Pd, :class:`~openquake.hazardlib.geo.point.Point` object
        representing the location of direction point
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

            pa = np.array([seg_s, pp_xyz])
            pb = np.array([seg_e, hypocenter_xyz])

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

            vector1 = (p_intersect.flatten() - hypocenter_xyz) / \
                sum((p_intersect.flatten() - hypocenter_xyz) ** 2) ** 0.5
            vector2 = (pp_xyz - hypocenter_xyz) / \
                sum((pp_xyz - hypocenter_xyz) ** 2) ** 0.5
            vector3 = (np.array(seg_e) - np.array(seg_s)) / \
                sum((np.array(seg_e) - np.array(seg_s)) ** 2) ** 0.5
            vector4 = (p_intersect.flatten() - np.array(seg_s)) / \
                sum((p_intersect.flatten() - np.array(seg_s)) ** 2) ** 0.5

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
