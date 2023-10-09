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
import numpy as np
from pyproj import Geod
from shapely.geometry import Polygon

from openquake.baselib.node import Node
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo import geodetic
from openquake.hazardlib.geo.mesh import RectangularMesh
from openquake.hazardlib.geo import utils as geo_utils
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.geodetic import (
    npoints_towards, distance, azimuth)

TOL = 0.4
VERY_SMALL = 1e-20
ALMOST_RIGHT_ANGLE = 89.9

def fix_idl(lon, idl):
    """
    Fix the longitude in proximity of the international date line
    """
    return lon + 360 if idl and lon < 0 else lon


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

    def __init__(self, mesh, profiles=None, sec_id=''):
        self.mesh = mesh

        # Clean the mesh
        success = self._clean()
        if not success:
            msg = f"Error while initialising section (id: {sec_id})"
            raise ValueError(msg)

        # Save profiles
        self.profiles = profiles
        assert 1 not in self.mesh.shape, (
            "Mesh must have at least 2 nodes along strike and dip.")

        # Make sure the mesh respects the right hand rule
        self._fix_right_hand()
        self.strike = self.dip = None
        self.width = None

    def _clean(self):
        """
        Removes from the mesh the rows and columns containing just NaNs
        """
        # Rows
        rm = []
        for i in range(0, self.mesh.lons.shape[0]):
            if np.all(np.isnan(self.mesh.lons[i, :])):
                rm.append(i)
        lons = np.delete(self.mesh.lons, rm, axis=0)
        lats = np.delete(self.mesh.lats, rm, axis=0)
        deps = np.delete(self.mesh.depths, rm, axis=0)
        # Cols
        rm = []
        for i in range(0, lons.shape[1]):
            if np.all(np.isnan(lons[:, i])):
                rm.append(i)
        lons = np.delete(lons, rm, axis=1)
        lats = np.delete(lats, rm, axis=1)
        deps = np.delete(deps, rm, axis=1)

        success = True
        if not lons.size > 0:
            success = False
            return success

        mesh = RectangularMesh(lons, lats, deps)
        self.mesh = mesh
        return success

    @property
    def surface_nodes(self):
        """
        A single element list containing a kiteSurface node
        """
        # TODO if the object is created without profiles we must extract them
        # from the mesh
        return kite_surface_node(self.profiles)

    def get_surface_boundaries(self):
        return self._get_external_boundary()

    def get_tor(self):
        """
        Provides longitude and latitude coordinates of the vertical surface
        projection of the top of rupture. This is used in the GC2 method to
        compute the Rx and Ry0 distances.

        One important note here. The kite fault surface uses a rectangular
        mesh to describe the geometry of the rupture; some nodes can be NaN.

        :returns:
            Two :class:`numpy.ndarray` instances with the longitudes and
            latitudes
        """
        chk = np.isfinite(self.mesh.lons)
        iro = (chk).argmax(axis=0)
        ico = np.arange(0, self.mesh.lons.shape[1])
        ico = ico[iro <= 1]
        iro = iro[iro <= 1]
        return self.mesh.lons[iro, ico], self.mesh.lats[iro, ico]

    def is_vertical(self):
        """ True if all the profiles, and hence the surface, are vertical """
        mgd = geodetic.min_geodetic_distance
        check = []
        for icol in range(self.mesh.lons.shape[1]):
            idx = np.isfinite(self.mesh.lons[:, icol])
            lons = self.mesh.lons[idx, icol]
            lats = self.mesh.lats[idx, icol]
            deps = self.mesh.depths[idx, icol]
            dve = deps[1:] - deps[:-1]
            dho = mgd((lons[:-1], lats[:-1]), (lons[1:], lats[1:]))
            tmp = np.ones_like(dve) * 90.0
            idx = dho > VERY_SMALL
            tmp[idx] = np.degrees(np.arctan(dve[idx] / dho[idx]))
            check.append(np.all(tmp > ALMOST_RIGHT_ANGLE))
        return np.all(check)

    def _get_external_boundary(self):
        """
        Provides the surface projection of the external boundary of the
        rupture surface.

        :returns:
            Two :class:`numpy.ndarray` instances containing longitudes and
            latitudes, respectively
        """
        if self.is_vertical():

            lo = []
            la = []
            idx = np.min(np.where(np.isfinite(self.mesh.lons[:, 0])))
            slo = self.mesh.lons[idx, 0]
            sla = self.mesh.lats[idx, 0]
            idx = np.min(np.where(np.isfinite(self.mesh.lons[:, -1])))
            elo = self.mesh.lons[idx, -1]
            ela = self.mesh.lats[idx, -1]
            strike = azimuth(slo, sla, elo, ela)

            npt = npoints_towards
            dlt = 0.1
            tmp = npt(slo, sla, 0.0, strike-90, dlt, 0, 2)
            lo.append(tmp[0][1])
            la.append(tmp[1][1])
            tmp = npt(slo, sla, 0.0, strike+90, dlt, 0, 2)
            lo.append(tmp[0][1])
            la.append(tmp[1][1])
            tmp = npt(elo, ela, 0.0, strike+90, dlt, 0, 2)
            lo.append(tmp[0][1])
            la.append(tmp[1][1])
            tmp = npt(elo, ela, 0.0, strike-90, dlt, 0, 2)
            lo.append(tmp[0][1])
            la.append(tmp[1][1])

        else:

            idxs = self._get_external_boundary_indexes()
            lo = []
            la = []
            for i in idxs:
                lo.append(self.mesh.lons[i[0], i[1]])
                la.append(self.mesh.lats[i[0], i[1]])

        return np.array(lo), np.array(la)

    def _get_external_boundary_indexes(self):
        """
        Computes the indexes of the points composing the boundary of the
        surface
        """
        iul = []
        ilr = []
        for i in range(0, self.mesh.lons.shape[1]):
            idx = np.where(np.isfinite(self.mesh.lons[:, i]))[0]
            if len(idx) == 0:
                continue
            iul.append([min(idx), max(idx)])
        for i in range(0, self.mesh.lons.shape[0]):
            idx = np.where(np.isfinite(self.mesh.lons[i, :]))[0]
            if len(idx) == 0:
                continue
            ilr.append([min(idx), max(idx)])
        iul = np.array(iul)
        ilr = np.array(ilr)
        bnd = []
        # Top
        for i in range(0, self.mesh.lons.shape[1]):
            bnd.append([iul[i, 0], i])
        # Right
        for i in range(iul[-1, 0]+1, iul[-1, 1]):
            bnd.append([i, ilr[i, 1]])
        # Bottom
        for i in range(self.mesh.lons.shape[1]-1, -1, -1):
            bnd.append([iul[i, 1], i])
        # Left
        for i in range(iul[0, 1]-1, iul[0, 0], -1):
            bnd.append([i, ilr[i, 0]])
        return bnd

    def get_joyner_boore_distance(self, mesh) -> np.ndarray:
        """
        Computes the Rjb distance between the rupture and the points included
        in the mesh provided.

        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh`
        :returns:
            A :class:`numpy.ndarray` instance with the Rjb values
        """

        blo, bla = self._get_external_boundary()
        distances = geodetic.min_geodetic_distance(
            (blo, bla), (mesh.lons, mesh.lats))

        idxs = (distances < 40).nonzero()[0]  # indices on the first dimension
        if len(idxs) < 1:
            # no point is close enough, return distances as they are
            return distances

        # Get the projection
        proj = geo_utils.OrthographicProjection(
            *geo_utils.get_spherical_bounding_box(blo, bla))

        # Mesh projected coordinates
        mesh_xx, mesh_yy = proj(mesh.lons[idxs], mesh.lats[idxs])

        # Create the shapely Polygon using projected coordinates
        xp, yp = proj(blo, bla)
        polygon = Polygon([[x, y] for x, y in zip(xp, yp)])

        # Calculate the distances
        distances[idxs] = geo_utils.point_to_polygon_distance(
            polygon, mesh_xx, mesh_yy)

        return distances

    def _fix_right_hand(self):
        """
        This method fixes the mesh used to represent the grid surface so
        that it complies with the right hand rule.
        """
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
                                 self.mesh.lons[irow, icol+1],
                                 self.mesh.lats[irow, icol+1])
            azi_dip = azimuth(self.mesh.lons[irow, icol],
                              self.mesh.lats[irow, icol],
                              self.mesh.lons[irow+1, icol],
                              self.mesh.lats[irow+1, icol])

            if abs((azi_strike - 90) % 360 - azi_dip) < 40:
                tlo = np.fliplr(self.mesh.lons)
                tla = np.fliplr(self.mesh.lats)
                tde = np.fliplr(self.mesh.depths)
                mesh = RectangularMesh(tlo, tla, tde)
                self.mesh = mesh
        else:
            msg = 'Could not find a valid quadrilateral for strike calculation'
            raise ValueError(msg)

    def get_width(self) -> float:
        # TODO this method is provisional.  It works correctly for simple and
        # regular geometries defined using profiles parallel to the dip
        # direction
        """
        Compute the width of the kite surface.

        Defining a width for a kite surface is quite difficult. At present we
        compute it as the mean width for all the columns of the mesh defining
        the surface.
        """
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
        # TODO this method is provisional. It works correctly for simple and
        # regular geometries defined using profiles parallel to the dip
        # direction
        """
        Computes the fault dip as the average dip over the surface.

        :returns:
            The average dip, in decimal degrees.
        """
        if self.dip is None:
            dips = []
            lens = []
            for col_idx in range(self.mesh.lons.shape[1]):

                # For the calculation of the overall dip we use just the dip
                # values of contiguous points along a profile
                iii = np.isfinite(self.mesh.lons[1:, col_idx])
                kkk = np.isfinite(self.mesh.lons[:-1, col_idx])
                jjj = np.where(np.logical_and(kkk, iii))[0]

                zeros = np.zeros_like(self.mesh.depths[jjj, col_idx])
                hdists = distance(self.mesh.lons[jjj+1, col_idx],
                                  self.mesh.lats[jjj+1, col_idx],
                                  zeros,
                                  self.mesh.lons[jjj, col_idx],
                                  self.mesh.lats[jjj, col_idx],
                                  zeros)
                vdists = (self.mesh.depths[jjj+1, col_idx] -
                          self.mesh.depths[jjj, col_idx])

                ok = np.logical_and(np.isfinite(hdists), np.isfinite(vdists))
                hdists = hdists[ok]
                vdists = vdists[ok]
                if len(vdists) > 0:
                    tmp = np.ones_like(vdists) * 90.
                    idx = hdists > VERY_SMALL
                    tmp[idx] = np.degrees(np.arctan(vdists[idx]/hdists[idx]))
                    dips.append(np.mean(tmp))
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
            idx = np.nonzero(np.isfinite(self.mesh.lons[0, :]))[0]
            azi = azimuth(self.mesh.lons[0, idx[:-1]],
                          self.mesh.lats[0, idx[:-1]],
                          self.mesh.lons[0, idx[1:]],
                          self.mesh.lats[0, idx[1:]])
            self.strike = np.mean((azi+0.001) % 360)
        return self.strike

    def get_top_edge_depth(self):
        """
        Return minimum depth of surface's top edge.

        :returns:
            Float value, the vertical distance between the earth surface
            and the shallowest point in surface's top edge in km.
        """
        ok = np.isfinite(self.mesh.lons[0, :])
        return np.amin(self.mesh.depths[0, ok])

    @classmethod
    def from_profiles(cls, profiles, profile_sd, edge_sd, idl=False,
                      align=False, sec_id=''):
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

        # Fix profiles
        rprof, ref_idx = _fix_profiles(profiles, profile_sd, align, idl)

        # Create mesh
        msh = _create_mesh(rprof, ref_idx, edge_sd, idl)

        return cls(RectangularMesh(msh[:, :, 0], msh[:, :, 1], msh[:, :, 2]),
                   profiles, sec_id)

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
        return self._get_external_boundary()

    def get_area(self):
        _, _, _, cell_area = self.get_cell_dimensions()
        idx = np.isfinite(cell_area)
        return np.sum(cell_area[idx])

    def get_cell_dimensions(self):
        """
        Compute the area [km2] of the cells representing the surface.
        """
        lo = self.mesh.lons
        la = self.mesh.lats
        de = self.mesh.depths

        # Calculating cells dimensions
        lo0 = lo[:-1, :]
        la0 = la[:-1, :]
        de0 = de[:-1, :]
        lo1 = lo[1:, :]
        la1 = la[1:, :]
        de1 = de[1:, :]
        idx = np.logical_and(np.isfinite(lo0), np.isfinite(lo1))
        dy = np.full_like(lo0, np.nan)
        dy[idx] = distance(lo0[idx], la0[idx], de0[idx],
                           lo1[idx], la1[idx], de1[idx])

        lo0 = lo[:, 1:]
        la0 = la[:, 1:]
        de0 = de[:, 1:]
        lo1 = lo[:, :-1]
        la1 = la[:, :-1]
        de1 = de[:, :-1]
        idx = np.logical_and(np.isfinite(lo0), np.isfinite(lo1))
        dx = np.full_like(lo0, np.nan)
        dx[idx] = distance(lo0[idx], la0[idx], de0[idx],
                           lo1[idx], la1[idx], de1[idx])

        lo0 = lo[1:, 1:]
        la0 = la[1:, 1:]
        de0 = de[1:, 1:]
        lo1 = lo[:-1, :-1]
        la1 = la[:-1, :-1]
        de1 = de[:-1, :-1]
        idx = np.logical_and(np.isfinite(lo0), np.isfinite(lo1))
        dd = np.full_like(lo0, np.nan)
        dd[idx] = distance(lo0[idx], la0[idx], de0[idx],
                           lo1[idx], la1[idx], de1[idx])

        # Compute the area of the upper left triangles in each cell
        s = (dx[:-1, :] + dy[:, :-1] + dd) * 0.5
        upp = (s * (s - dx[:-1, :]) * (s - dy[:, :-1]) * (s - dd))**0.5

        # Compute the area of the lower right triangles in each cell
        s = (dx[1:, :] + dy[:, 1:] + dd) * 0.5
        low = (s * (s - dx[1:, :]) * (s - dy[:, 1:]) * (s - dd))**0.5

        # Compute the area of each cell
        area = np.full_like(dd, np.nan)
        idx = np.logical_and(np.isfinite(upp), np.isfinite(low))
        area[idx] = upp[idx] + low[idx]

        # Retain the same output of the original function which provided for
        # each cell the centroid as 3d vector in a Cartesian space, the length
        # width (size along column of points) in km and the area in km2.
        return None, None, None, area


def _create_mesh(rprof, ref_idx, edge_sd, idl):
    """
    Create the mesh in the forward and backward direction (from the reference
    profile)

    :param rprof:
        A list of profiles
    :param ref_idx:
        Index indicating the reference profile
    :param edge_sd:
        A float defining the sampling distance [km] for the edges
    :param idl:
        A boolean. When true the profiles cross the international date li
    :returns:
        An instance of  :class:`openquake.hazardlib.geo.Mesh`
    """

    # Create the mesh in the forward direction
    prfr = []
    if ref_idx < len(rprof)-1:
        prfr = get_mesh(rprof, ref_idx, edge_sd, idl)

    # Create the mesh in the backward direction
    prfl = []
    last = False if ref_idx < len(rprof) - 1 else True
    if ref_idx > 0:
        prfl = get_mesh_back(rprof, ref_idx, edge_sd, idl, last)
    prf = prfl + prfr

    # Create the whole mesh
    if len(prf) > 1:

        msh = np.array(prf)

    else:

        # Check the profiles have the same number of samples
        chk1 = np.all(np.array([len(p) for p in rprof]) == len(rprof[0]))
        top_depths = np.array([p[0, 0] for p in rprof])

        # Check profiles have the same top depth
        chk2 = np.all(np.abs(top_depths - rprof[0][0, 0]) < 0.1*edge_sd)

        if chk1 and chk2:
            msh = np.array(rprof)
        else:
            raise ValueError('Cannot build the mesh')

    # Convert from profiles to edges
    msh = msh.swapaxes(0, 1)
    msh = fix_mesh(msh)

    return msh


def _fix_profiles(profiles, profile_sd, align, idl):
    """
    Resample and align profiles

    :param profiles:
        A list of :class:`openquake.hazardlib.geo.Line` instances
    :param profile_sd:
        A float [km] defining the sampling distance for profiles
    :param align:
        A boolean controlling the alignment of profiles
    :param idl:
        A boolean. When true the profiles cross the international date line
    """

    # Resample profiles using the resampling distance provided
    rprofiles = []
    for prf in profiles:
        rprofiles.append(_resample_profile(prf, profile_sd))

    # Set the reference profile i.e. the longest one
    ref_idx = 0
    lengths = np.array([prf.get_length() for prf in rprofiles])
    if np.max(lengths) - np.min(lengths) > profile_sd*0.1:
        ref_idx = np.argmax(lengths)

    # Check that in each profile the points are equally spaced
    for pro in rprofiles:
        pnts = pro.coo

        # Check that the profile is not crossing the IDL and compute the
        # distance between consecutive points along the profile
        assert np.all(pnts[:, 0] <= 180) & np.all(pnts[:, 0] >= -180)
        dst = distance(pnts[:-1, 0], pnts[:-1, 1], pnts[:-1, 2],
                       pnts[1:, 0], pnts[1:, 1], pnts[1:, 2])

        # Check that all the distances are within a given tolerance
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

    return rprof, ref_idx


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
    if np.abs(dip - 90.) < 1e-5:
        dip = 89.9

    # Get simple fault surface
    srfc = SimpleFaultSurface.from_fault_data(
        fault_trace, upper_seismogenic_depth,lower_seismogenic_depth,
        dip, rupture_mesh_spacing*1.01)

    # Creating profiles
    profiles = []
    n, m = srfc.mesh.shape
    for i in range(m):
        coo = np.zeros((n, 3))
        coo[:, 0] = srfc.mesh.lons[:, i]
        coo[:, 1] = srfc.mesh.lats[:, i]
        coo[:, 2] = srfc.mesh.depths[:, i]
        profiles.append(Line.from_coo(coo))

    return profiles


def _lo_la_de(line, sampling_dist, g):
    lo = line.coo[:, 0].copy()
    la = line.coo[:, 1].copy()
    de = line.coo[:, 2].copy()
    # Add a tolerance length to the last point of the profile
    # check that final portion of the profile is not vertical
    if abs(lo[-2] - lo[-1]) > 1e-5 and abs(la[-2] - la[-1]) > 1e-5:
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
    return lo, la, de

    
def _resample_profile(line, sampling_dist):
    """
    :parameter line:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    :parameter sampling_dist:
        A scalar defining the distance [km] used to sample the profile
    :returns:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    """
    # Set projection
    g = Geod(ellps='WGS84')

    # Initialize lo, la, de
    lo, la, de = _lo_la_de(line, sampling_dist, g)

    # Initialize the cumulated distance
    cdist = 0.

    # Get the azimuth of the profile
    azim = azimuth(lo[0], la[0], lo[-1], la[-1])

    # Initialise the list with the resampled nodes
    idx = 0
    resampled_cs = [(lo[idx], la[idx], de[idx])]

    # Set the starting point
    slo = lo[idx]
    sla = la[idx]
    sde = de[idx]

    # Resampling
    while idx <= len(lo) - 2:
        # Compute the distance between the starting point and the next point
        # on the profile
        segment_len = distance(slo, sla, sde, lo[idx+1], la[idx+1], de[idx+1])
        azim = azimuth(slo, sla, lo[idx+1], la[idx+1])

        # Search for the point along the profile
        if cdist + segment_len > sampling_dist:
            # This is the length of the last segment-fraction needed to
            # obtain the sampling distance
            delta = sampling_dist - cdist

            # Compute the slope of the last segment and its horizontal length.
            # We need to manage the case of a vertical segment TODO
            segment_hlen = distance(slo, sla, 0., lo[idx+1], la[idx+1], 0.)
            if segment_hlen > 1e-5:
                segment_slope = np.arctan((de[idx+1] - sde) / segment_hlen)
            else:
                segment_slope = 90.

            # Horizontal and vertical length of delta
            if segment_slope > ALMOST_RIGHT_ANGLE:
                delta_v = delta
                delta_h = 0.0
            else:
                delta_v = delta * np.sin(segment_slope)
                delta_h = delta * np.cos(segment_slope)

            # Add a new point to the cross section
            if segment_slope > ALMOST_RIGHT_ANGLE:
                pnts = [np.array([slo, slo]),
                        np.array([sla, sla]),
                        np.array([sde, sde + delta_v])]
            else:
                pnts = npoints_towards(slo, sla, sde, azim, delta_h, delta_v, 2)

            # Update the starting point
            slo = pnts[0][-1]
            sla = pnts[1][-1]
            sde = pnts[2][-1]
            resampled_cs.append((slo, sla, sde))

            # Reset the cumulative distance
            cdist = 0.
        else:
            cdist += segment_len
            idx += 1
            slo = lo[idx]
            sla = la[idx]
            sde = de[idx]

    coo = np.array(resampled_cs)
    _check_distances(coo, sampling_dist)
    return Line.from_coo(coo)


def _check_distances(coo, sampling_dist):
    # Check the distances along the profile
    for i in range(coo.shape[0] - 1):
        dst = distance(coo[i, 0], coo[i, 1], coo[i, 2],
                       coo[i+1, 0], coo[i+1, 1], coo[i+1, 2])
        if abs(dst - sampling_dist) > 0.1 * sampling_dist:
            msg = 'Distance between points along the profile larger than 10%'

            fmt = '\n   Expected {:.2f} Computed {:.2f}'
            msg += fmt.format(sampling_dist, dst)

            fmt = '\n   Point {:.2f} {:.2f} {:.2f}'
            msg += fmt.format(*[coo[i, j] for j in range(3)])
            msg += fmt.format(*[coo[i+1, j] for j in range(3)])

            msg += '\n   Please, change the sampling distance or the'
            msg += ' points along the profile'
            raise ValueError(msg)

    
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
    coo1 = pro1.coo
    coo2 = pro2.coo

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
        d1 = np.zeros((len(coo2)-len(coo1) + 1, len(coo1)))
        d2 = np.zeros((len(coo2)-len(coo1) + 1, len(coo1)))
        for i in np.arange(0, len(coo2) - len(coo1) + 1):
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
    for p in line:
        p.longitude = fix_idl(p.longitude, idl)
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
    n = len(pfs[0])

    # Initialize residual distance and last index
    rdist = np.zeros(n)
    angle = np.zeros(n)
    laidx = [0 for _ in range(n)]

    # Creating a new list used to collect the new profiles which will describe
    # the mesh. We start with the initial profile i.e. the one identified by
    # the reference index rfi
    npr = [pfs[rfi].copy()]

    # Run for all the profiles 'after' the reference one
    for i in range(rfi, len(pfs) - 1):

        # Profiles: left and right
        pr = pfs[i+1]
        pl = pfs[i]

        # Fixing IDL case
        for ii, vpl in enumerate(pl):
            pl[ii][0] = fix_idl(vpl[0], idl)

        # Points in common on the two profiles i.e. points with finite
        # coordinates on both of them
        cmm = np.logical_and(np.isfinite(pr[:, 2]), np.isfinite(pl[:, 2]))
        cmmi = np.nonzero(cmm)[0].astype(int)

        # Find the index of the profiles previously analysed and with at least
        # a node in common with the current profile (i.e. with a continuity in
        # the mesh)
        mxx = 0
        for ll in laidx:
            if ll is not None:
                mxx = max(mxx, ll)

        # Loop over the points in the right profile
        for x in range(0, len(pr[:, 2])):

            # If true this edge connects the right and left profiles
            if x in cmmi and laidx[x] is None:
                iii = []
                for li, lv in enumerate(laidx):
                    if lv is not None:
                        iii.append(li)
                iii = np.array(iii)
                minidx = np.argmin(abs(iii - x))
                laidx[x] = mxx
                rdist[x] = rdist[minidx]
                angle[x] = angle[minidx]
            elif x not in cmmi:
                laidx[x] = None
                rdist[x] = 0.
                angle[x] = None

        # Loop over the indexes of the edges in common for the two profiles
        # starting from the top and going down
        for k in list(np.nonzero(cmm)[0]):

            # Compute distance [km] and azimuth between the corresponding
            # points on the two consecutive profiles
            az12, _, hdist = g.inv(pl[k, 0], pl[k, 1], pr[k, 0], pr[k, 1])
            hdist /= 1e3
            # Vertical distance
            vdist = pr[k, 2] - pl[k, 2]
            # Total distance
            tdist = (vdist**2 + hdist**2)**.5

            # Update rdist
            new_rdist = rdist[k]
            if rdist[k] > 0 and abs(az12 - angle[k] > 2):
                new_rdist = update_rdist(rdist[k], az12, angle[k], sd)

            # Number of grid points
            # ndists = int(np.floor((tdist+rdist[k])/sd))
            ndists = int(np.floor((tdist+new_rdist)/sd))

            # Calculate points between the corresponding nodes on the
            # two profiles
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

            # Compute distance between nodels at depth 'k' on the two
            # consecutive profiles
            dd = distance(pl[k, 0], pl[k, 1], pl[k, 2],
                          pr[k, 0], pr[k, 1], pr[k, 2])

            # Check that the actual distance between these nodes is similar to
            # the one originally defined
            if abs(dd - tdist) > 0.1*tdist:
                print('dd:', dd)
                tmps = 'Error while building the mesh'
                tmps += '\nDistances: {:f} {:f}'
                raise ValueError(tmps.format(dd, tdist))

            # Adding new points along the edge with index k
            for j in range(ndists):

                # Add new profile to 'npr' i.e. the list containing the new
                # set of profiles
                if len(npr)-1 < laidx[k]+1:
                    add_empty_profile(npr)

                # Compute the coordinates of intermediate points along the
                # current edge. 'tmp' is the distance between the node on the
                # left edge and the j-th node on the edge. 'lo' and 'la' are
                # the coordinates of this new node
                # tmp = (j+1)*sd - rdist[k]
                tmp = (j+1)*sd - new_rdist
                # lo, la, _ = g.fwd(pl[k, 0], pl[k, 1], az12,
                #                  tmp*hdist/tdist*1e3)

                # Find the index of the closest node in the vector sampled at
                # high frequency
                tidx = np.argmin(abs(tdsts-tmp))
                lo = ll[tidx, 0]
                la = ll[tidx, 1]

                # Fix longitudes in proximity of the IDL
                lo = fix_idl(lo, idl)

                # Computing depths
                de = pl[k, 2] + tmp*vdist/hdist
                de = deps[tidx]

                # Updating the new profile
                npr[laidx[k] + 1][k] = [lo, la, de]
                if (k > 0 and np.all(np.isfinite(npr[laidx[k]+1][k])) and
                        np.all(np.isfinite(npr[laidx[k]][k]))):

                    # Computing the distance between consecutive points on
                    # one edge
                    p1 = npr[laidx[k]][k]
                    p2 = npr[laidx[k]+1][k]
                    d = distance(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])

                    # Check if the distance between consecutive points on one
                    # edge (with index k) is within a tolerance limit of the
                    # mesh distance defined by the user
                    if abs(d-sd) > TOL*sd:
                        tmpf = '\ndistance: {:f} difference: {:f} '
                        tmpf += '\ntolerance dist: {:f} sampling dist: {:f}'
                        tmpf += '\nresidual distance: {:f}'
                        tmps = tmpf.format(d, d-sd, TOL*sd, sd, new_rdist)
                        raise ValueError(tmps)
                laidx[k] += 1

            # Check that the residual distance along each edge is lower than
            # the sampling distance
            rdist[k] = tdist - sd*ndists + new_rdist
            angle[k] = az12
            assert rdist[k] < sd

    return npr


def update_rdist(rdist, az12, angle, sd):
    r"""
    Here we adjust the residual distance to make sure that the size of the
    mesh is consistent with the sampling. This is particularly needed when the
    mesh has a kink

    v1
    ------------------------------  angle[k]
             beta  \ az12-angle[k]
                    \
                     \
                      \ v2

    alpha is the angle between angle[k] and the v1 to v2 direction
    gamma is the angle between az12 (the new azimuth) and v1-v2 i.e.
    the third angle in the triangle
    """
    assert rdist > 0
    beta = 180.0 - abs(az12 - angle)
    side_b = sd
    side_a = (sd - rdist)
    ratio = side_b / np.sin(np.radians(beta))
    alpha = np.rad2deg(np.arcsin(side_a / ratio))
    gamma = 180.0 - (alpha + beta)
    assert gamma > 0
    rdist_new = ratio * np.sin(np.radians(gamma))
    assert (rdist_new) > 0
    return rdist_new


def get_coo(g, pl, az12, ndists, hdist, vdist, tdist, new_rdist, sd, idl):
    coo = np.zeros((ndists, 3))
    for j in range(ndists):
        tmp = (j+1) * sd - new_rdist
        lo, la, _ = g.fwd(pl[0], pl[1], az12,
                          tmp * hdist / tdist * 1e3)
        coo[j, 0] = fix_idl(lo, idl)
        coo[j, 1] = la
        coo[j, 2] = pl[2] + tmp*vdist/hdist
    return coo


def get_mesh_back(pfs, rfi, sd, idl, last):
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
        A list of new profiles
    """
    # Projection
    g = Geod(ellps='WGS84')
    n = len(pfs[0])

    # Initialize residual distance and last index lists
    rdist = np.zeros(n)
    angle = np.zeros(n)
    laidx = [0 for _ in range(n)]

    # Create list containing the new profiles. We start by adding the
    # reference profile
    npr = [pfs[rfi].copy()]

    # Run for all the profiles from the reference one backward
    for i in range(rfi, 0, -1):

        # Set the profiles to be used for the construction of the mesh
        pr = pfs[i-1]
        pl = pfs[i]

        # Points in common on the two profiles i.e. points that in both the
        # profiles are not NaN
        cmm = np.logical_and(np.isfinite(pr[:, 2]), np.isfinite(pl[:, 2]))

        # Transform the 'cmm' indexes into integers and calculate the index of
        # the last valid profile i.e. the index of the closest one to the
        # current left profile
        cmmi = np.nonzero(cmm)[0].astype(int)
        mxx = 0
        for ll in laidx:
            if ll is not None:
                mxx = max(mxx, ll)

        # For each edge in the right profile we compute
        for x in range(0, len(pr[:, 2])):

            # If this index is in cmmi and last index is nan the mesh at this
            # depth starts from this profile
            if x in cmmi and laidx[x] is None:
                iii = []
                for li, lv in enumerate(laidx):
                    if lv is not None:
                        iii.append(li)
                iii = np.array(iii)
                minidx = np.argmin(abs(iii-x))
                laidx[x] = mxx
                rdist[x] = rdist[minidx]
                angle[x] = angle[minidx]
            elif x not in cmmi:
                laidx[x] = None
                rdist[x] = 0
                angle[x] = None

        # Loop over the points in common between the two profiles
        for k in list(np.nonzero(cmm)[0]):

            # Compute azimuth and horizontal distance
            az12, _, hdist = g.inv(pl[k, 0], pl[k, 1], pr[k, 0], pr[k, 1])
            hdist /= 1e3
            vdist = pr[k, 2] - pl[k, 2]
            tdist = (vdist**2 + hdist**2)**.5

            # Update rdist if this is larger than 0 and the new edge has a
            # different direction than the previous one
            new_rdist = rdist[k]
            if rdist[k] > 0 and abs(az12 - angle[k] > 2):
                new_rdist = update_rdist(rdist[k], az12, angle[k], sd)

            # Calculate the number of cells
            ndists = int(np.floor((tdist+new_rdist)/sd))
            coo = get_coo(
                g, pl[k], az12, ndists, hdist, vdist, tdist, new_rdist, sd, idl)
            # Adding new points along edge with index k
            for j in range(ndists):

                # add new profile
                if len(npr)-1 < laidx[k]+1:
                    add_empty_profile(npr)
                npr[laidx[k]+1][k] = coo[j]

                if (k > 0 and np.all(np.isfinite(npr[laidx[k]+1][k])) and
                        np.all(np.isfinite(npr[laidx[k]][k]))):

                    p1 = npr[laidx[k]][k]
                    p2 = npr[laidx[k]+1][k]
                    d = distance(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])

                    # This checks that the size of each newly created cell
                    # is similar (within some tolerance) to the intial mesh
                    # size provided by the user
                    if abs(d - sd) > TOL * sd:
                        tmpf = 'd: {:f} diff: {:f} tol: {:f} sd:{:f}'
                        tmpf += '\nresidual: {:f}'
                        tmps = tmpf.format(d, d-sd, TOL*sd, sd, new_rdist)
                        msg = 'The mesh spacing exceeds the tolerance limits'
                        tmps += '\n {:s}'.format(msg)
                        raise ValueError(tmps)

                # Updating the index of the last profile in the mesh at depth
                # 'k'
                laidx[k] += 1

            # Updating residual distances and angle (i.e. azimuth)
            rdist[k] = tdist - sd * ndists + new_rdist
            angle[k] = az12

            # Checking that the residual distance is lower than the sampling
            # distance
            assert rdist[k] < sd

    return [npr[i] for i in range(len(npr) - 1, -1 if last else 0, -1)]


def add_empty_profile(npr, idx=-1):
    """
    :param npr:
        A list of profiles
    :returns:
        A list with the new empty profiles
    """
    n, m = len(npr), len(npr[0])
    tmp = [[np.nan, np.nan, np.nan] for _ in range(m)]
    if idx == -1:
        npr.append(tmp)
    elif idx == 0:
        npr.insert(0, tmp)
    else:
        ValueError('Undefined option')

    # Check that profiles have the same lenght
    for i in range(n - 1):
        assert len(npr[i]) == len(npr[i + 1])


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


def kite_to_geom(surface):
    """
    :returns: the geometry array describing the KiteSurface
    """
    shape_y, shape_z = surface.mesh.array.shape[1:]
    coords = np.float32(surface.mesh.array.flat)
    return np.concatenate([np.float32([1, shape_y, shape_z]), coords])


def geom_to_kite(geom):
    """
    :returns: KiteSurface described by the given geometry array
    """
    shape_y, shape_z = int(geom[1]), int(geom[2])
    array = geom[3:].astype(np.float64).reshape(3, shape_y, shape_z)
    return KiteSurface(RectangularMesh(*array))
