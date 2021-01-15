# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.surface.kite_fault` defines
:class:`KiteSurface`.
"""

import copy
import numpy as np

from pyproj import Geod
from openquake.baselib.node import Node
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.mesh import RectangularMesh
from openquake.hazardlib.geo import utils as geo_utils
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.geodetic import npoints_towards
from openquake.hazardlib.geo.geodetic import distance, azimuth

TOL = 0.2


def profile_node(points):
    """
    :param points: a list of Point objects
    :returns: a Node of kind profile
    """
    line = []
    for point in points:
        line.append(point.longitude)
        line.append(point.latitude)
        line.append(point.depth)
    pos = Node('gml:posList', {}, line)
    node = Node('profile', nodes=[Node('gml:LineString', nodes=[pos])])
    return node


def kite_surface_node(profiles):
    """
    :param profiles: a list of lists of points
    :returns: a Node of kind complexFaultGeometry
    """
    node = Node('kiteSurface')
    for profile in profiles:
        node.append(profile_node(profile))
    return node


class KiteSurface(BaseSurface):
    """
    The Kite Fault Surface allows the construction of faults with variable
    width along the strike, variable dip angle along the dip and strike
    composed by several disaligned segments. Thrust faults and listric faults
    can be easily implemented.
    """
    def __init__(self, mesh, profiles=None):
        self.mesh = mesh
        self.profiles = profiles
        assert 1 not in self.mesh.shape, (
            "Mesh must have at least 2 nodes along both length and width.")
        # Make sure the mesh respects the right hand rule
        self._fix_right_hand()
        self.strike = self.dip = None
        self.width = None

    @property
    def surface_nodes(self):
        """
        A single element list containing a kiteSurface node
        """
        # TODO if the object is created without profiles we must extract them
        # from the mesh
        return kite_surface_node(self.profiles)

    def _fix_right_hand(self):
        # This method fixes the mesh used to represent the grid surface so
        # that it complies with the right hand rule.
        found = False
        irow = 0
        icol = 0
        while not found:
            if np.all(np.isfinite(self.mesh.lons[irow:irow+2, icol:icol+2])):
                found = True
            else:
                icol += 1
                if (icol+1) >= self.mesh.lons.shape[1]:
                    irow += 1
                    icol = 1
                    if (irow+1) >= self.mesh.lons.shape[0]:
                        break
        if found:
            azi_strike = azimuth(self.mesh.lons[irow, icol],
                                 self.mesh.lats[irow, icol],
                                 self.mesh.lons[irow+1, icol],
                                 self.mesh.lats[irow+1, icol])
            azi_dip = azimuth(self.mesh.lons[irow, icol],
                              self.mesh.lats[irow, icol],
                              self.mesh.lons[irow, icol+1],
                              self.mesh.lats[irow, icol+1])

            if abs((azi_strike + 90) % 360 - azi_dip) < 10:
                tlo = np.fliplr(self.mesh.lons)
                tla = np.fliplr(self.mesh.lats)
                tde = np.fliplr(self.mesh.depths)
                mesh = RectangularMesh(tlo, tla, tde)
                self.mesh = mesh
        else:
            msg = 'Could not find a valid quadrilateral for strike calculation'
            raise ValueError(msg)

    def get_width(self) -> float:
        if self.width is None:
            widths = []
            for col_idx in range(self.mesh.lons.shape[1]):
                tmpa = np.nonzero(np.isfinite(self.mesh.lons[:, col_idx]))[0]
                tmpb = (tmpa[1:]-tmpa[:-1] == 1).nonzero()[0]
                idxs_low = tmpa[tmpb.astype(int)]
                tmp = distance(self.mesh.lons[idxs_low, col_idx],
                               self.mesh.lats[idxs_low, col_idx],
                               self.mesh.depths[idxs_low, col_idx],
                               self.mesh.lons[idxs_low+1, col_idx],
                               self.mesh.lats[idxs_low+1, col_idx],
                               self.mesh.depths[idxs_low+1, col_idx])
                if len(tmp) > 0:
                    widths.append(np.sum(tmp))
            self.width = np.mean(np.array(widths))
        return self.width

    def get_dip(self) -> float:
        """
        Return the fault dip as the average dip over the fault surface mesh.

        :returns:
            The average dip, in decimal degrees.
        """
        if self.dip is None:
            dips = []
            lens = []
            for col_idx in range(self.mesh.lons.shape[1]):
                hdists = distance(self.mesh.lons[:-1, col_idx],
                                  self.mesh.lats[:-1, col_idx],
                                  np.zeros_like(self.mesh.depths[1:, col_idx]),
                                  self.mesh.lons[1:, col_idx],
                                  self.mesh.lats[1:, col_idx],
                                  np.zeros_like(self.mesh.depths[1:, col_idx]))
                vdists = (self.mesh.depths[1:, col_idx] -
                          self.mesh.depths[:-1, col_idx])

                ok = np.logical_and(np.isfinite(hdists), np.isfinite(vdists))
                hdists = hdists[ok]
                vdists = vdists[ok]

                dips.append(np.mean(np.degrees(np.arctan(vdists/hdists))))
                lens.append(np.sum((hdists**2 + vdists**2)**0.5))
            lens = np.array(lens)
            self.dip = np.sum(np.array(dips) * lens/np.sum(lens))
        return self.dip

    def get_strike(self) -> float:
        """
        Return the fault strike as the average strike along the top of the
        fault surface.

        :returns:
            The average strike, in decimal degrees.
        """
        if self.strike is None:
            idx = np.isfinite(self.mesh.lons)
            azi = azimuth(self.mesh.lons[:-1, :], self.mesh.lats[:-1, :],
                          self.mesh.lons[1:, :], self.mesh.lats[1:, :])
            self.strike = np.mean(((azi[idx[:-1, :]]+0.001) % 360))
        return self.strike

    def get_top_edge_depth(self):
        """
        Return minimum depth of surface's top edge.

        :returns:
            Float value, the vertical distance between the earth surface
            and the shallowest point in surface's top edge in km.
        """
        ok = np.isfinite(self.mesh.lons[0, :])
        return self.mesh.depths[0, ok]

    @classmethod
    def from_profiles(cls, profiles, profile_sd, edge_sd, idl=False,
                      align=False):
        # TODO split this function into smaller components.
        """
        This method creates a quadrilateral mesh from a set of profiles. The
        construction of the mesh is done trying to get quadrilaterals as much
        as possible close to a square. Nonetheless some distorsions are
        possible and admitted.

        :param list profiles:
            A list of :class:`openquake.hazardlib.geo.Line.line` instances
        :param float profile_sd:
            The desired sampling distance along the profiles [dd] CHECK
        :param edge_sd:
            The desired sampling distance along the edges [dd] CHECK
        :param idl:
            Boolean true if IDL
        :param align:
            A boolean used to decide if profiles should or should not be
            aligned at the top.
        :returns:
            A :class:`numpy.ndarray` instance with the coordinates of nodes
            of the mesh representing the fault surface. The cardinality of
            this array is: number of edges x number of profiles x 3.
            The coordinate of the point at [0, 0, :] is first point along the
            trace defined using the right-hand rule.

                        [0, 0, :]            [0, -1, :]
            Upper edge  |--------------------|
                        |         V          | Fault dipping toward the
                        |                    | observer
            Lower edge  |____________________|

        """
        # Resample profiles using the resampling distance provided
        rprofiles = []
        for prf in profiles:
            rprofiles.append(_resample_profile(prf, profile_sd))

        # Set the reference profile i.e. the longest one
        ref_idx = None
        max_length = -1e10
        for idx, prf in enumerate(rprofiles):
            length = prf.get_length()
            if length > max_length:
                max_length = length
                ref_idx = idx

        # Check that in each profile the points are equally spaced
        for pro in rprofiles:
            pnts = [(p.longitude, p.latitude, p.depth) for p in pro.points]
            pnts = np.array(pnts)

            # Check that the profile is not crossing the IDL and compute the
            # distance between consecutive points along the profile
            assert np.all(pnts[:, 0] <= 180) & np.all(pnts[:, 0] >= -180)
            dst = distance(pnts[:-1, 0], pnts[:-1, 1], pnts[:-1, 2],
                           pnts[1:, 0], pnts[1:, 1], pnts[1:, 2])

            # Check that all the distances are within a tolerance
            np.testing.assert_allclose(dst, profile_sd, rtol=1.)

        # Find the delta needed to align profiles if requested
        shift = np.zeros(len(rprofiles)-1)
        if align is True:
            for i in range(0, len(rprofiles)-1):
                shift[i] = profiles_depth_alignment(rprofiles[i],
                                                    rprofiles[i+1])
        shift = np.array([0] + list(shift))

        # Find the maximum back-shift
        ccsum = [shift[0]]
        for i in range(1, len(shift)):
            ccsum.append(shift[i] + ccsum[i-1])
        add = ccsum - min(ccsum)

        # Create resampled profiles. Now the profiles should be all aligned
        # from the top (if align option is True)
        rprof = []
        maxnum = 0
        for i, pro in enumerate(rprofiles):
            j = int(add[i])
            coo = get_coords(pro, idl)
            tmp = [[np.nan, np.nan, np.nan] for a in range(0, j)]
            if len(tmp) > 0:
                points = tmp + coo
            else:
                points = coo
            rprof.append(points)
            maxnum = max(maxnum, len(rprof[-1]))

        # Now profiles will have the same number of samples (some of them can
        # be nan). This is needed to have an array to store the surface.
        for i, pro in enumerate(rprof):
            while len(pro) < maxnum:
                pro.append([np.nan, np.nan, np.nan])
            rprof[i] = np.array(pro)

        # Create mesh the in the forward direction
        prfr = get_mesh(rprof, ref_idx, edge_sd, idl)

        # Create the mesh in the backward direction
        if ref_idx > 0:
            prfl = get_mesh_back(rprof, ref_idx, edge_sd, idl)
        else:
            prfl = []
        prf = prfl + prfr
        msh = np.array(prf)

        # Convert from profiles to edges
        msh = msh.swapaxes(0, 1)
        msh = fix_mesh(msh)
        return cls(RectangularMesh(msh[:, :, 0], msh[:, :, 1], msh[:, :, 2]),
                   profiles)

    def get_center(self):
        """
        Finds a point on the mesh in proximity of the surface center. Can be
        used as a first guess of hypocenter position (in absence of better
        info).

        :returns:
            The point on the mesh closer to its center
        """
        mesh = self.mesh
        irow = int(np.round(mesh.shape[0]/2))
        icol = int(np.round(mesh.shape[1]/2))
        return Point(mesh.lons[irow, icol], mesh.lats[irow, icol],
                     mesh.depths[irow, icol])

    @property
    def surface_projection(self):
        """
        Provides the coordinates of the surface projection of the rupture
        surface.

        :returns:
            Two lists with the coordinates of the longitude and latitude
        """

        los = self.mesh.lons
        las = self.mesh.lats
        ro, co = np.mgrid[0:los.shape[0], 0:los.shape[1]]

        plos = []
        plas = []

        tmp = np.amax(ro, where=~np.isnan(los), initial=np.amin(ro)-1, axis=0)
        for j, i in enumerate(tmp):
            if i >= np.amin(ro):
                plos.append(los[i, j])
                plas.append(las[i, j])

        tlo = []
        tla = []
        tmp = np.amin(ro, where=~np.isnan(los), initial=len(los)+1, axis=0)
        for j, i in enumerate(tmp):
            if i <= len(los):
                tlo.append(los[i, j])
                tla.append(las[i, j])

        plos.extend(tlo[::-1])
        plas.extend(tla[::-1])

        return plos, plas

    def get_cell_dimensions(self):
        """
        Calculate centroid, width, length and area of each mesh cell.

        NOTE: The original verison of this method is in the class
        :class:`openquake.hazardlib.geo.mesh.Mesh`. It is duplicated here
        because it required ad-hoc modifications to support kite fault
        surfaces

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
        points, along_azimuth, updip, diag = self.mesh.triangulate()
        top = along_azimuth[:-1]
        left = updip[:, :-1]
        tl_area = geo_utils.triangle_area(top, left, diag)
        top_length = np.sqrt(np.sum(top * top, axis=-1))
        left_length = np.sqrt(np.sum(left * left, axis=-1))

        bottom = along_azimuth[1:]
        right = updip[:, 1:]
        br_area = geo_utils.triangle_area(bottom, right, diag)
        bottom_length = np.sqrt(np.sum(bottom * bottom, axis=-1))
        right_length = np.sqrt(np.sum(right * right, axis=-1))

        # Remove cells without a finite area
        np.nan_to_num(tl_area, nan=0.0, copy=False)
        np.nan_to_num(br_area, nan=0.0, copy=False)
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

        np.nan_to_num(cell_length, nan=0.0, copy=False)
        np.nan_to_num(cell_width, nan=0.0, copy=False)

        return cell_center, cell_length, cell_width, cell_area


def get_profiles_from_simple_fault_data(
        fault_trace, upper_seismogenic_depth,
        lower_seismogenic_depth, dip, rupture_mesh_spacing):
    """
    Using the same information used for the construction of a simple fault
    surface, creates a set of profiles that can be used to instantiate a
    kite surface.

    :param fault_trace:
        A :class:`openquake.hazardlib.geo.line.Line` instance
    :param upper_seismogenic_depth:
        The upper seismmogenic depth [km]
    :param lower_seismogenic_depth:
        The lower seismmogenic depth [km]
    :param dip:
        The dip angle [degrees]
    :param rupture_mesh_spacing:
        The size of the mesh used to represent the fault surface. In our case
        the spacing between profiles [km]
    """

    # Avoids singularity
    if (dip-90.) < 1e-5:
        dip = 89.9

    # Get simple fault surface
    srfc = SimpleFaultSurface.from_fault_data(fault_trace,
                                              upper_seismogenic_depth,
                                              lower_seismogenic_depth,
                                              dip,
                                              rupture_mesh_spacing*1.01)
    # Creating profiles
    profiles = []
    for i in range(srfc.mesh.shape[1]):
        tmp = [Point(lo, la, de) for lo, la, de
               in zip(srfc.mesh.lons[:, i], srfc.mesh.lats[:, i],
                      srfc.mesh.depths[:, i])]
        profiles.append(Line(tmp))

    return profiles


def _resample_profile(line, sampling_dist):
    # TODO split this function into smaller components.
    """
    :parameter line:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    :parameter sampling_dist:
        A scalar definining the distance [km] used to sample the profile
    :returns:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    """
    lo = [pnt.longitude for pnt in line.points]
    la = [pnt.latitude for pnt in line.points]
    de = [pnt.depth for pnt in line.points]

    # Set projection
    g = Geod(ellps='WGS84')

    # Add a tolerance length to the last point of the profile
    # check that final portion of the profile is not vertical
    if abs(lo[-2]-lo[-1]) > 1e-5 and abs(la[-2]-la[-1]) > 1e-5:
        az12, _, odist = g.inv(lo[-2], la[-2], lo[-1], la[-1])
        odist /= 1e3
        slope = np.arctan((de[-1] - de[-2]) / odist)
        hdist = TOL * sampling_dist * np.cos(slope)
        vdist = TOL * sampling_dist * np.sin(slope)
        endlon, endlat, _ = g.fwd(lo[-1], la[-1], az12, hdist*1e3)
        lo[-1] = endlon
        la[-1] = endlat
        de[-1] = de[-1] + vdist
        az12, _, odist = g.inv(lo[-2], la[-2], lo[-1], la[-1])

        # Checking
        odist /= 1e3
        slopec = np.arctan((de[-1] - de[-2]) / odist)
        assert abs(slope-slopec) < 1e-3
    else:
        de[-1] = de[-1] + TOL * sampling_dist

    # Initialise the cumulated distance
    cdist = 0.

    # Get the azimuth of the profile
    azim = azimuth(lo[0], la[0], lo[-1], la[-1])

    # Initialise the list with the resampled nodes
    idx = 0
    resampled_cs = [Point(lo[idx], la[idx], de[idx])]

    # Set the starting point
    slo = lo[idx]
    sla = la[idx]
    sde = de[idx]

    # Resampling
    while 1:

        # Check loop exit condition
        if idx > len(lo)-2:
            break

        # Compute the distance between the starting point and the next point
        # on the profile
        segment_len = distance(slo, sla, sde, lo[idx+1], la[idx+1], de[idx+1])

        # Search for the point
        if cdist+segment_len > sampling_dist:

            # This is the lenght of the last segment-fraction needed to
            # obtain the sampling distance
            delta = sampling_dist - cdist

            # Compute the slope of the last segment and its horizontal length.
            # We need to manage the case of a vertical segment TODO
            segment_hlen = distance(slo, sla, 0., lo[idx+1], la[idx+1], 0.)
            if segment_hlen > 1e-5:
                segment_slope = np.arctan((de[idx+1] - sde) / segment_hlen)
            else:
                segment_slope = 90.

            # Horizontal and vertical lenght of delta
            delta_v = delta * np.sin(segment_slope)
            delta_h = delta * np.cos(segment_slope)

            # Add a new point to the cross section
            pnts = npoints_towards(slo, sla, sde, azim, delta_h, delta_v, 2)

            # Update the starting point
            slo = pnts[0][-1]
            sla = pnts[1][-1]
            sde = pnts[2][-1]
            resampled_cs.append(Point(slo, sla, sde))

            # Reset the cumulative distance
            cdist = 0.

        else:
            cdist += segment_len
            idx += 1
            slo = lo[idx]
            sla = la[idx]
            sde = de[idx]

    # Check the distances along the profile
    coo = [[pnt.longitude, pnt.latitude, pnt.depth] for pnt in resampled_cs]
    coo = np.array(coo)
    for i in range(0, coo.shape[0]-1):
        dst = distance(coo[i, 0], coo[i, 1], coo[i, 2],
                       coo[i+1, 0], coo[i+1, 1], coo[i+1, 2])
        if abs(dst-sampling_dist) > 0.1*sampling_dist:
            raise ValueError('Wrong distance between points along the profile')

    return Line(resampled_cs)


def profiles_depth_alignment(pro1, pro2):
    """
    Find the indexes needed to align the profiles i.e. define profiles whose
    edges are as much as possible horizontal. Note that this method expects
    that the two profiles had been already resampled, therefore, vertexes in
    each profile should be equally spaced.

    :param pro1:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    :param pro2:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    :returns:
        An integer
    """

    # Create two numpy.ndarray with the coordinates of the two profiles
    coo1 = [(pnt.longitude, pnt.latitude, pnt.depth) for pnt in pro1.points]
    coo2 = [(pnt.longitude, pnt.latitude, pnt.depth) for pnt in pro2.points]
    coo1 = np.array(coo1)
    coo2 = np.array(coo2)

    # Set the profile with the smaller number of points as the first one
    swap = 1
    if coo2.shape[0] < coo1.shape[0]:
        coo1, coo2 = coo2, coo1
        swap = -1

    # Process the profiles. Note that in the ideal case the two profiles
    # require at least 5 points
    if len(coo1) > 5 and len(coo2) > 5:
        #
        # create two arrays of the same lenght
        coo1 = np.array(coo1)
        coo2 = np.array(coo2[:coo1.shape[0]])
        #
        indexes = np.arange(-2, 3)
        dff = np.zeros_like(indexes)
        for i, shf in enumerate(indexes):
            if shf < 0:
                dff[i] = np.mean(abs(coo1[:shf, 2] - coo2[-shf:, 2]))
            elif shf == 0:
                dff[i] = np.mean(abs(coo1[:, 2] - coo2[:, 2]))
            else:
                dff[i] = np.mean(abs(coo1[shf:, 2] - coo2[:-shf, 2]))
        amin = np.amin(dff)
        res = indexes[np.amax(np.nonzero(dff == amin))] * swap
    else:
        d1 = np.zeros((len(coo2)-len(coo1)+1, len(coo1)))
        d2 = np.zeros((len(coo2)-len(coo1)+1, len(coo1)))
        for i in np.arange(0, len(coo2)-len(coo1)+1):
            d2[i, :] = [coo2[d, 2] for d in range(i, i+len(coo1))]
            d1[i, :] = coo1[:, 2]
        res = np.argmin(np.sum(abs(d2-d1), axis=1))
    return res


def get_coords(line, idl):
    """
    Create a list with the coordinates of the points describing a line

    :param line:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    :returns:
        A list with the 3D coordinates of the line.
    """
    tmp = []
    for p in line.points:
        if p is not None:
            if idl:
                p.longitude = (p.longitude+360 if p.longitude < 0
                               else p.longitude)
            tmp.append([p.longitude, p.latitude, p.depth])
    return tmp


def get_mesh(pfs, rfi, sd, idl):
    """
    From a set of profiles creates the mesh in the forward direction from the
    reference profile.

    :param pfs:
        List of :class:`openquake.hazardlib.geo.line.Line` instances
    :param rfi:
        Index of the reference profile
    :param sd:
        Sampling distance [km] for the edges
    :param idl:
        Boolean indicating the need to account for the IDL
    :returns:
        An updated list of the profiles i.e. a list of
        :class:`openquake.hazardlib.geo.line.Line` instances
    """
    g = Geod(ellps='WGS84')

    # Residual distance, last index
    rdist = [0 for _ in range(0, len(pfs[0]))]
    laidx = [0 for _ in range(0, len(pfs[0]))]

    # New profiles
    npr = list([copy.copy(pfs[rfi])])

    # Run for all the profiles 'after' the reference one
    for i in range(rfi, len(pfs)-1):

        # Profiles
        pr = pfs[i+1]
        pl = pfs[i]

        # Fixing IDL case
        if idl:
            for ii in range(0, len(pl)):
                ptmp = pl[ii][0]
                ptmp = ptmp+360 if ptmp < 0 else ptmp
                pl[ii][0] = ptmp

        # Point in common on the two profiles
        cmm = np.logical_and(np.isfinite(pr[:, 2]), np.isfinite(pl[:, 2]))
        cmmi = np.nonzero(cmm)[0].astype(int)

        # Update last profile index
        mxx = 0
        for ll in laidx:
            if ll is not None:
                mxx = max(mxx, ll)

        # Loop over the points in the right profile
        for x in range(0, len(pr[:, 2])):

            # This edge is in common between the last and the current profiles
            if x in cmmi and laidx[x] is None:
                iii = []
                for li, lv in enumerate(laidx):
                    if lv is not None:
                        iii.append(li)
                iii = np.array(iii)
                minidx = np.argmin(abs(iii-x))
                laidx[x] = mxx
                rdist[x] = rdist[minidx]
            elif x not in cmmi:
                laidx[x] = None
                rdist[x] = 0

        # Loop over profiles
        for k in list(np.nonzero(cmm)[0]):

            # Compute distance and azimuth between the corresponding points
            # on the two profiles
            az12, _, hdist = g.inv(pl[k, 0], pl[k, 1], pr[k, 0], pr[k, 1])
            hdist /= 1e3
            vdist = pr[k, 2] - pl[k, 2]
            tdist = (vdist**2 + hdist**2)**.5
            ndists = int(np.floor((tdist+rdist[k])/sd))

            ll = g.npts(pl[k, 0], pl[k, 1], pr[k, 0], pr[k, 1],
                        np.ceil(tdist)*20)
            ll = np.array(ll)
            lll = np.ones_like(ll)
            lll[:, 0] = pl[k, 0]
            lll[:, 1] = pl[k, 1]

            _, _, hdsts = g.inv(lll[:, 0], lll[:, 1], ll[:, 0], ll[:, 1])
            hdsts /= 1e3
            deps = np.linspace(pl[k, 2], pr[k, 2], ll.shape[0], endpoint=True)
            tdsts = (hdsts**2 + (pl[k, 2]-deps)**2)**0.5
            assert len(deps) == ll.shape[0]

            # Compute distance between consecutive profiles
            dd = distance(pl[k, 0], pl[k, 1], pl[k, 2],
                          pr[k, 0], pr[k, 1], pr[k, 2])

            # Check distance
            if abs(dd-tdist) > 0.1*tdist:
                print('dd:', dd)
                tmps = 'Error while building the mesh'
                tmps += '\nDistances: {:f} {:f}'
                raise ValueError(tmps.format(dd, tdist))

            # Adding new points along the edge with index k
            for j in range(ndists):

                # Add new profile
                if len(npr)-1 < laidx[k]+1:
                    npr = add_empty_profile(npr)

                # Compute the coordinates of intermediate points along the
                # current edge
                tmp = (j+1)*sd - rdist[k]
                lo, la, _ = g.fwd(pl[k, 0], pl[k, 1], az12,
                                  tmp*hdist/tdist*1e3)

                tidx = np.argmin(abs(tdsts-tmp))
                lo = ll[tidx, 0]
                la = ll[tidx, 1]

                # Fix longitudes
                if idl:
                    lo = lo+360 if lo < 0 else lo

                # Computing depths
                de = pl[k, 2] + tmp*vdist/hdist
                de = deps[tidx]

                npr[laidx[k]+1][k] = [lo, la, de]
                if (k > 0 and np.all(np.isfinite(npr[laidx[k]+1][k])) and
                        np.all(np.isfinite(npr[laidx[k]][k]))):

                    p1 = npr[laidx[k]][k]
                    p2 = npr[laidx[k]+1][k]
                    d = distance(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])

                    # Check
                    if abs(d-sd) > 0.1*sd:
                        tmpf = 'd: {:f} diff: {:f} tol: {:f} sd:{:f}'
                        tmpf += '\nresidual: {:f}'
                        tmps = tmpf.format(d, d-sd, TOL*sd, sd, rdist[k])
                        raise ValueError(tmps)
                laidx[k] += 1

            rdist[k] = tdist - sd*ndists + rdist[k]
            assert rdist[k] < sd

    return npr


def get_mesh_back(pfs, rfi, sd, idl):
    """
    Compute resampled profiles in the backward direction from the reference
    profile and creates the portion of the mesh 'before' the reference profile.

    :param list pfs:
        Original profiles. Each profile is a :class:`numpy.ndarray` instance
        with 3 columns and as many rows as the number of points included
    :param int rfi:
        Index of the reference profile
    :param sd:
        Sampling distance [in km] along the strike
    :param boolean idl:
        A flag used to specify cases where the model crosses the IDL
    :returns:

    """

    # Projection
    g = Geod(ellps='WGS84')

    # Initialize residual distance and last index lists
    rdist = [0 for _ in range(0, len(pfs[0]))]
    laidx = [0 for _ in range(0, len(pfs[0]))]

    # Create list containing the new profiles. We start by adding the
    # reference profile
    npr = list([copy.deepcopy(pfs[rfi])])

    # Run for all the profiles from the reference one backward
    for i in range(rfi, 0, -1):

        # Set the profiles to be used for the construction of the mesh
        pr = pfs[i-1]
        pl = pfs[i]

        # Points in common on the two profiles i.e. points that in both the
        # profiles are not NaN
        cmm = np.logical_and(np.isfinite(pr[:, 2]), np.isfinite(pl[:, 2]))

        # Transform the indexes into integers and initialise the maximum
        # index of the points in common
        cmmi = np.nonzero(cmm)[0].astype(int)
        mxx = 0
        for ll in laidx:
            if ll is not None:
                mxx = max(mxx, ll)

        # Update indexes
        for x in range(0, len(pr[:, 2])):
            if x in cmmi and laidx[x] is None:
                iii = []
                for li, lv in enumerate(laidx):
                    if lv is not None:
                        iii.append(li)
                iii = np.array(iii)
                minidx = np.argmin(abs(iii-x))
                laidx[x] = mxx
                rdist[x] = rdist[minidx]
            elif x not in cmmi:
                laidx[x] = None
                rdist[x] = 0

        # Loop over the points in common between the two profiles
        for k in list(np.nonzero(cmm)[0]):

            # Compute azimuth and horizontal distance
            az12, _, hdist = g.inv(pl[k, 0], pl[k, 1], pr[k, 0], pr[k, 1])
            hdist /= 1e3
            vdist = pr[k, 2] - pl[k, 2]
            tdist = (vdist**2 + hdist**2)**.5
            ndists = int(np.floor((tdist+rdist[k])/sd))

            # Adding new points along edge with index k
            for j, _ in enumerate(range(ndists)):
                #
                # add new profile
                if len(npr)-1 < laidx[k]+1:
                    npr = add_empty_profile(npr)
                #
                # fix distance
                tmp = (j+1)*sd - rdist[k]
                lo, la, _ = g.fwd(pl[k, 0], pl[k, 1], az12,
                                  tmp*hdist/tdist*1e3)

                if idl:
                    lo = lo+360 if lo < 0 else lo

                de = pl[k, 2] + tmp*vdist/hdist
                npr[laidx[k]+1][k] = [lo, la, de]

                if (k > 0 and np.all(np.isfinite(npr[laidx[k]+1][k])) and
                        np.all(np.isfinite(npr[laidx[k]][k]))):

                    p1 = npr[laidx[k]][k]
                    p2 = npr[laidx[k]+1][k]
                    d = distance(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])
                    #
                    # >>> TOLERANCE
                    if abs(d-sd) > TOL*sd:
                        tmpf = 'd: {:f} diff: {:f} tol: {:f} sd:{:f}'
                        tmpf += '\nresidual: {:f}'
                        tmps = tmpf.format(d, d-sd, TOL*sd, sd, rdist[k])
                        msg = 'The mesh spacing exceeds the tolerance limits'
                        tmps += '\n {:s}'.format(msg)
                        raise ValueError(tmps)

                laidx[k] += 1
            rdist[k] = tdist - sd*ndists + rdist[k]
            assert rdist[k] < sd

    tmp = []
    for i in range(len(npr)-1, 0, -1):
        tmp.append(npr[i])

    return tmp


def add_empty_profile(npr, idx=-1):
    """
    :param npr:
        An integer defining the number of points composing the profile
    :returns:
        A list with the new empty profiles
    """

    #
    tmp = [[np.nan, np.nan, np.nan] for _ in range(len(npr[0]))]
    if idx == -1:
        npr = npr + [tmp]
    elif idx == 0:
        npr = [tmp] + npr
    else:
        ValueError('Undefined option')

    # Check that profiles have the same lenght
    for i in range(0, len(npr)-1):
        assert len(npr[i]) == len(npr[i+1])

    return npr


def fix_mesh(msh):
    """
    Check that the quadrilaterals composing the final mesh are correctly
    defined i.e. all the vertexes are finite.

    :param msh:
        A :class:`numpy.ndarray` instance with the coordinates of the mesh
    :returns:
        A revised :class:`numpy.ndarray` instance with the coordinates of
        the mesh. The shape of this array num_rows x num_cols x 3
    """
    for i in range(msh.shape[0]):
        ru = i+1
        rl = i-1
        for j in range(msh.shape[1]):
            cu = j+1
            cl = j-1

            trl = False if cl < 0 else np.isfinite(msh[i, cl, 0])
            tru = False if cu > msh.shape[1]-1 else np.isfinite(msh[i, cu, 0])
            tcl = False if rl < 0 else np.isfinite(msh[rl, j, 0])
            tcu = False if ru > msh.shape[0]-1 else np.isfinite(msh[ru, j, 0])

            check_row = trl or tru
            check_col = tcl or tcu

            if not (check_row and check_col):
                msh[i, j, :] = np.nan
    return msh
