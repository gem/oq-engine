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
import numpy.typing as npt
import matplotlib.pyplot as plt
from scipy import stats
from shapely.geometry import Polygon

from openquake.baselib.node import Node
from openquake.baselib.general import cached_property
from openquake.hazardlib.geo import geodetic
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.line import _resample, Line
from openquake.hazardlib.geo.mesh import RectangularMesh
from openquake.hazardlib.geo import utils as geo_utils
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.geodetic import (
    npoints_towards, distance, azimuth)
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.geo.surface.gridded import GriddedSurface

TOL = 0.4
SMALL = 1e-5
VERY_SMALL = 1e-20
VERY_BIG = 1e20
ALMOST_RIGHT_ANGLE = 89.9


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

    @cached_property
    # this is cached since it can be called multiple times for the same
    # surface (in multi fault sources)
    def tor(self):
        """
        Provides longitude and latitude coordinates of the vertical surface
        projection of the top of rupture. This is used in the GC2 method to
        compute the Rx and Ry0 distances. NB: keep_corners is used to reduce
        the line, with a tolerance of 1 km.

        One important note here. The kite fault surface uses a rectangular
        mesh to describe the geometry of the rupture; some nodes can be NaN.

        :returns:
            Two :class:`numpy.ndarray` instances with the longitudes and
            latitudes
        """
        chk = np.isfinite(self.mesh.lons)
        iro = chk.argmax(axis=0)
        ico = np.arange(self.mesh.lons.shape[1])
        ico = ico[iro <= 1]
        iro = iro[iro <= 1]
        # top_left, top_right coordinates
        lo, la = self.mesh.lons[iro, ico], self.mesh.lats[iro, ico]
        return Line.from_vectors(lo, la).keep_corners(delta=1.)

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
            tmp = npt(slo, sla, 0.0, strike - 90, dlt, 0, 2)
            lo.append(tmp[0][1])
            la.append(tmp[1][1])
            tmp = npt(slo, sla, 0.0, strike + 90, dlt, 0, 2)
            lo.append(tmp[0][1])
            la.append(tmp[1][1])
            tmp = npt(elo, ela, 0.0, strike + 90, dlt, 0, 2)
            lo.append(tmp[0][1])
            la.append(tmp[1][1])
            tmp = npt(elo, ela, 0.0, strike - 90, dlt, 0, 2)
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
        for i in range(iul[-1, 0] + 1, iul[-1, 1]):
            bnd.append([i, ilr[i, 1]])
        # Bottom
        for i in range(self.mesh.lons.shape[1] - 1, -1, -1):
            bnd.append([iul[i, 1], i])
        # Left
        for i in range(iul[0, 1] - 1, iul[0, 0], -1):
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
        proj = geo_utils.OrthographicProjection.from_(blo, bla)

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
            if np.all(np.isfinite(self.mesh.lons[irow:irow + 2,
                                                 icol:icol + 2])):
                found = True
            else:
                icol += 1
                if (icol + 1) >= self.mesh.lons.shape[1]:
                    irow += 1
                    icol = 1
                    if (irow + 1) >= self.mesh.lons.shape[0]:
                        break
        if found:
            azi_strike = azimuth(self.mesh.lons[irow, icol],
                                 self.mesh.lats[irow, icol],
                                 self.mesh.lons[irow, icol + 1],
                                 self.mesh.lats[irow, icol + 1])
            azi_dip = azimuth(self.mesh.lons[irow, icol],
                              self.mesh.lats[irow, icol],
                              self.mesh.lons[irow + 1, icol],
                              self.mesh.lats[irow + 1, icol])

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
                tmpb = (tmpa[1:] - tmpa[:-1] == 1).nonzero()[0]
                idxs_low = tmpa[tmpb.astype(int)]
                tmp = distance(self.mesh.lons[idxs_low, col_idx],
                               self.mesh.lats[idxs_low, col_idx],
                               self.mesh.depths[idxs_low, col_idx],
                               self.mesh.lons[idxs_low + 1, col_idx],
                               self.mesh.lats[idxs_low + 1, col_idx],
                               self.mesh.depths[idxs_low + 1, col_idx])
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
                hdists = distance(self.mesh.lons[jjj + 1, col_idx],
                                  self.mesh.lats[jjj + 1, col_idx],
                                  zeros,
                                  self.mesh.lons[jjj, col_idx],
                                  self.mesh.lats[jjj, col_idx],
                                  zeros)
                vdists = (self.mesh.depths[jjj + 1, col_idx] -
                          self.mesh.depths[jjj, col_idx])

                ok = np.logical_and(np.isfinite(hdists), np.isfinite(vdists))
                hdists = hdists[ok]
                vdists = vdists[ok]
                if len(vdists) > 0:
                    tmp = np.ones_like(vdists) * 90.
                    idx = hdists > VERY_SMALL
                    tmp[idx] = np.degrees(np.arctan(vdists[idx] / hdists[idx]))
                    dips.append(np.mean(tmp))
                    lens.append(np.sum((hdists**2 + vdists**2)**0.5))
            lens = np.array(lens)
            self.dip = np.sum(np.array(dips) * lens / np.sum(lens))

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
            self.strike = np.mean((azi + 0.001) % 360)
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
        msh = _create_mesh(rprof, ref_idx, edge_sd, idl, align)

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
        irow = int(np.round(mesh.shape[0] / 2))
        icol = int(np.round(mesh.shape[1] / 2))
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

    def __str__(self):
        if hasattr(self, 'idx'):  # multisurface index
            idx = ' idx=%d' % self.idx
        else:
            idx = ''
        return '<%s%s>' % (self.__class__.__name__, idx)


def geom_to_kite(geom):
    """
    :returns: KiteSurface described by the given geometry array
    """
    shape_y, shape_z = int(geom[1]), int(geom[2])
    array = geom[3:].astype(np.float64).reshape(3, shape_y, shape_z)
    return KiteSurface(RectangularMesh(*array))


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
        fault_trace, upper_seismogenic_depth, lower_seismogenic_depth,
        dip, rupture_mesh_spacing * 1.01)

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


def fix_idl(lon, idl):
    """
    Fix the longitude in proximity of the international date line
    """
    return lon + 360 if idl and lon < 0 else lon


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


def kite_surface_node(profiles):
    """
    :param profiles: a list of lists of points
    :returns: a Node of kind complexFaultGeometry
    """
    node = Node('kiteSurface')
    for profile in profiles:
        node.append(profile_node(profile))
    return node


def kite_to_geom(surface):
    """
    :returns: the geometry array describing the KiteSurface
    """
    shape_y, shape_z = surface.mesh.array.shape[1:]
    coords = np.float32(surface.mesh.array.flat)
    return np.concatenate([np.float32([1, shape_y, shape_z]), coords])


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


def _check_distances(coo, sampling_dist):
    # Check the distances along the profile
    for i in range(coo.shape[0] - 1):
        dst = distance(coo[i, 0], coo[i, 1], coo[i, 2],
                       coo[i + 1, 0], coo[i + 1, 1], coo[i + 1, 2])
        if abs(dst - sampling_dist) > 0.1 * sampling_dist:
            msg = 'Distance between points along the profile larger than 10%'

            fmt = '\n   Expected {:.2f} Computed {:.2f}'
            msg += fmt.format(sampling_dist, dst)

            fmt = '\n   Point {:.2f} {:.2f} {:.2f}'
            msg += fmt.format(*[coo[i, j] for j in range(3)])
            msg += fmt.format(*[coo[i + 1, j] for j in range(3)])

            msg += '\n   Please, change the sampling distance or the'
            msg += ' points along the profile'
            raise ValueError(msg)


def _get_proj_from_profiles(rprof):
    # Compute information needed for the geographic projection
    west = 1e10
    south = 1e10
    east = -1e10
    north = -1e10
    for pro in rprof:
        idx = np.nonzero(np.isfinite(pro[:, 0]))
        west = np.minimum(west, np.min(pro[idx, 0]))
        south = np.minimum(south, np.min(pro[idx, 1]))
        east = np.maximum(east, np.max(pro[idx, 0]))
        north = np.maximum(north, np.max(pro[idx, 1]))
    return geo_utils.OrthographicProjection(west, east, north, south)


def _create_mesh(rprof, ref_idx, edge_sd, idl, align):
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
    # Compute information needed for the geographic projection
    proj = _get_proj_from_profiles(rprof)

    # Check the profiles have the same number of samples
    chk1 = np.all(np.array([len(p) for p in rprof]) == len(rprof[0]))

    # Check profiles have the same top depth. Note that this check is currently
    # not used since it applies only in some cases.
    if not align:
        top_depths = np.array([p[0, 2] for p in rprof])
        _ = np.all(np.abs(top_depths - rprof[0][0, 2]) < 0.1 * edge_sd)

    # Checks
    if chk1:
        msh = np.array(rprof)
    else:
        msg = 'Cannot build the mesh.'
        if not chk1:
            msg += ' Profiles do not have the same num. samples.'
        raise ValueError(msg)

    # Create the mesh in the forward direction
    prfr = []
    cond = ref_idx >= 0 and ref_idx < len(rprof) - 1
    if cond:
        prfr = _get_resampled_profs(prfr, rprof, edge_sd, proj, idl, ref_idx)

    # Create the mesh in the backward direction
    prfl = []
    cond = ref_idx > 0 and ref_idx <= len(rprof) - 1
    last = False if cond else True
    if ref_idx > 0:
        prfl = _get_resampled_profs(
            prfl, rprof, edge_sd, proj, idl, ref_idx, last)

    # Remove the reference profile from the second subset of profiles
    if len(prfr) > 0 and len(prfl) > 0:
        _align_profiles(prfr, prfl)
        prfl = prfl[1:]

    # Final profiles
    prf = prfr[::-1] + prfl

    # Create the whole mesh
    if len(prf) > 1:
        msh = np.array(prf)
    else:
        raise ValueError('Not enough profiles. Decrease the spacing')

    # Convert from profiles to edges
    msh = msh.swapaxes(0, 1)
    msh = fix_mesh(msh)

    # Sort the edges composing the mesh using their average depth
    _edges_sort_by_mean_depth(msh)

    # Adjust the sorting
    _edges_fix_sorting(msh)

    # Fix the orientation of the mesh
    msh = _fix_right_hand(msh)

    # INFO: this is just for debugging
    # _dbg_plot_mesh(msh)

    return msh


def _edges_fix_sorting(msh):
    for i_row_u in range(0, msh.shape[0] - 1):
        for i_row_l in range(i_row_u, msh.shape[0] - 1):
            i_cols = np.logical_and(np.isfinite(msh[i_row_u, :, 2]),
                                    np.isfinite(msh[i_row_l, :, 2]))
            if np.any(msh[i_row_l, i_cols, 2] - msh[i_row_u, i_cols, 2] < 0):
                # Swapping
                tmpl = copy.copy(msh[i_row_l, :, :])
                tmpu = copy.copy(msh[i_row_u, :, :])
                msh[i_row_u, :, :] = tmpl
                msh[i_row_l, :, :] = tmpu


def _edges_sort_by_mean_depth(msh):
    mdep = []
    for irow in range(msh.shape[0]):
        tidx = np.isfinite(msh[irow, :, 2])
        mdep.append(np.mean(msh[irow, tidx, 2]))
    mdep = np.array(mdep)
    idx = mdep.argsort()
    msh[:, :, 0] = msh[idx, :, 0]
    msh[:, :, 1] = msh[idx, :, 1]
    msh[:, :, 2] = msh[idx, :, 2]


def _dbg_plot_mesh(mesh):

    from openquake.hazardlib.tests.geo.surface.kite_fault_test import (
        set_axes_equal)

    scl = 0.01
    ax = plt.figure().add_subplot(projection='3d')
    ax.plot(mesh[:, :, 0].flatten(),
            mesh[:, :, 1].flatten(),
            mesh[:, :, 2].flatten() * scl, '.')
    ax.invert_zaxis()
    set_axes_equal(ax)
    plt.show()


def _fix_right_hand(msh):
    # This function checks that the array describing the surface complies with
    # the right hand rule.
    #
    # :param msh:
    #   A :class:`numpy.ndarray` instance
    #

    # Compute the average azimuth for the top edge of the surface
    tmp = msh[0, :, 0]
    idx = np.isfinite(tmp)
    top = Line([Point(c[0], c[1]) for c in msh[0, idx, :]])

    # Compute the strike of the surface
    coo = msh.reshape(-1, 3)
    coo = coo[np.isfinite(coo[:, 0]), :]
    pnts = [Point(c[0], c[1], c[2]) for c in coo]
    grdd = GriddedSurface.from_points_list(pnts)
    strike = grdd.get_strike()

    # Check if we need to flip the grid
    if not np.abs(_angles_diff(strike, top.azimuth)) < 60:

        # Flip the grid to make it compliant with the right hand rule
        nmsh = np.flip(msh, axis=1)

        # Compute the average azimuth for the top edge of the surface
        tmp = nmsh[0, :, 0]
        idx = np.isfinite(tmp)
        top = Line([Point(c[0], c[1]) for c in nmsh[0, idx, :]])

        # Check again the average azimuth for the top edge of the surface
        msg = "The mesh still does not comply with the right hand rule"
        assert np.abs(_angles_diff(strike, top.azimuth)) < 60, msg
        return nmsh

    return msh


def _angles_diff(ang_a, ang_b):
    dff = ang_a - ang_b
    return (dff + 180) % 360 - 180


def _align_profiles(prfr: list, prfl: list):

    # Check that the two sets contain profiles with the same length
    lenr = len(prfr[0])
    lenl = len(prfl[0])
    assert np.all(np.array([len(pr) for pr in prfr]) - lenr) == 0.0
    assert np.all(np.array([len(pr) for pr in prfl]) - lenl) == 0.0

    # Find the alignment between left and right
    delta = 0
    if prfr[0][0][2] <= prfl[0][0][2]:
        # Initial depth of the right profile shallower
        for i_dep, dep in enumerate(prfr[0][:][2]):
            if np.abs(dep - prfl[0][0][2]) < SMALL:
                delta = i_dep
                break
            for i_pro, pro in enumerate(prfl):
                prfl[i_pro] = _fill(delta, pro)
    else:
        # Initial depth of the left profile shallower
        for i_dep, dep in enumerate(prfl[0][:][2]):
            if np.abs(dep - prfr[0][0][2]) < SMALL:
                delta = i_dep
                break
            for i_pro, pro in enumerate(prfr):
                prfr[i_pro] = _fill(delta, pro)

    # Pad at the end to get the same length
    delta = len(prfl[0]) - len(prfr[0])
    if delta > 0:
        for i_pro, pro in enumerate(prfr):
            for _ in range(abs(delta)):
                prfr[i_pro].append([np.nan, np.nan, np.nan])
    elif delta < 0:
        for i_pro, pro in enumerate(prfl):
            for _ in range(abs(delta)):
                prfl[i_pro].append([np.nan, np.nan, np.nan])


def _fix_profiles(profiles, profile_sd, align, idl):
    """
    Resample and align profiles.

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
        rprofiles.append(prf.resample(profile_sd))

    # Set the reference profile i.e. the longest one
    ref_idx = 0
    lengths = np.array([prf.get_length() for prf in rprofiles])
    if np.max(lengths) - np.min(lengths) > profile_sd * 0.1:
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
    shift = np.zeros((len(rprofiles)))
    if align is True:

        # Find the shallower profile
        idxmin = None
        depmin = +1e10
        for iii, prf in enumerate(rprofiles):
            if np.min(prf.coo[:, 2]) < depmin:
                depmin = np.min(prf.coo[:, 2])
                idxmin = iii

        for i, _ in enumerate(rprofiles):
            if i != idxmin:
                shift[i] = profiles_depth_alignment(rprofiles[idxmin],
                                                    rprofiles[i])
    add = shift

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


def _from_prf_to_array(prfs: list, low: int, upp: int, step: int):
    # Converts a set of profiles into a numpy array
    idxs = list(range(low, upp, step))
    out = np.zeros((len(idxs), len(prfs[low]), 3))
    for i, idx in enumerate(idxs):
        out[i, :, :] = prfs[idx]
    return out


def _find_continuous_segments(mtx, i_seg: int):
    # Returns a list of lists where each element contains the index of the
    # start and end profiles and the index of the edge
    #
    # :param mtx:
    #
    # :param i_seg:
    #
    i_from = -1
    i_to = -1
    out = []
    for i in range(len(mtx)):
        if np.isfinite(mtx[i, 0]):
            if i_from < 0:
                i_from = i
                i_to = i
            else:
                i_to = i
        else:
            if i_from >= 0 and i_to >= 0 and np.abs(i_from - i_to) > 0:
                out.append([i_from, i_to + 1, i_seg])
            i_from = -1
            i_to = -1
    if i_from >= 0 and i_to >= 0 and np.abs(i_from - i_to) > 0:
        out.append([i_from, i_to + 1, i_seg])
    return out


def _get_resampled_profs(npr, profs, sd, proj, idl, ref_idx, forward=True):

    # Set the indexes of the original profiles depending on the direction
    # i.e. forward or backward
    low, upp, step = _set_indexes(forward, ref_idx, len(profs))

    # Get the array with all the profiles (resampled at a `step` distance)
    parr = _from_prf_to_array(profs, low, upp, step)

    # Process each edge obtained from the resampled profiles
    csegs = []
    for i_edge in range(parr.shape[1]):

        # Find the continuous parts of an edge
        for tmp in _find_continuous_segments(parr[:, i_edge], i_edge):

            # Here `tmp` contains many triples with the indexes of the first
            # and last profile and the index of the edge
            csegs.append(tmp)

    # Each element of the `csegs` list contains the start and end index of the
    # continuous part of an edge and the index of the edge (i.e. third element)
    csegs = np.array(csegs)

    # Sort the `csegs` array by increasing edge index, decreasing profile
    # index and starting profile index
    idxs = np.lexsort((csegs[:, 2], -csegs[:, 1], csegs[:, 0]))
    csegs = csegs[idxs]

    # Coordinates of the resampled edges
    coos = []
    new_prof_lines = []

    # This contains the unique indexes of the starting profile
    unique = np.unique(csegs[:, 0])
    cnt = 0

    # Loop over the unique-start indexes of continuous parts of an edge
    for i_from in unique:

        # Process all the sub-edges that start with index `i_from`
        for cseg in csegs[csegs[:, 0] == i_from, :]:

            # If the edge starts with the first index
            if i_from == unique[0]:
                line = Line.from_coo(parr[cseg[0]:cseg[1], cseg[2]])
                tmp = _resample(line, sd, True)

                if len(tmp) < 3:
                    tmp = tmp[:, :]
                else:
                    tmp = tmp[:-1, :]

                i_prof = 0
            else:
                edge = parr[cseg[0]:cseg[1], cseg[2]]
                tmp, i_prof = _get_intersections(edge, new_prof_lines, proj)

            cnt += 1
            coos.append([i_prof, cseg[2], tmp])

        # Update the set of lines describing the new profiles
        _compute_lines(coos, i_from, proj, new_prof_lines)

    # Build edges
    new_edges = _build_edges(coos)

    # Build profiles
    npr = _build_profiles(new_edges)

    # INFO: this is just for debugging purposes
    # monotonic, i_prof = _profiles_depth_is_monotonically_increasing(npr)

    # Check the sampled edges
    for key in new_edges:
        edg = np.array(new_edges[key])
        _check_sampling(edg, proj)

    # INFO: this is used only for debugging purposes
    #ax = _dbg_plot(new_edges, profs, npr, ref_idx)

    return npr


def _profiles_depth_is_monotonically_increasing(profs):
    # Check if the depths in all the profiles are monotonically increasing.
    # This is not a strict requirement but it's useful as a general check.
    # This function is used only for debugging purposes.
    for i_prof, prof in enumerate(profs):
        tmp = np.array(prof)
        idx = np.isfinite(tmp[:, 2])
        dff = np.diff(tmp[idx, 2])
        chk = np.all(dff > 0)
        if not chk:
            print(dff)
            return False, i_prof
    return True, None


def _check_sampling(edg, proj):
    # This function checks that the sampling along an edge is constant i.e.
    # this guaratees that the top and bottom edges of each cell have the same
    # size
    #
    # :param edg:
    #   An instance of :class:`numpy.ndarray` of shape Nx3
    # :param proj:
    #   An instance of
    #   :class:`openquake.hazardlib.geo.geo_utils.OrthographicProjection`

    # Find continuos parts
    idxs = []
    first = None
    last = None

    for i_e, e in enumerate(edg):
        if first is None and np.isfinite(e[0]):
            first = i_e
        elif first is not None and np.isfinite(e[0]):
            last = i_e
        elif first is not None and last is not None and not np.isfinite(e[0]):
            if last - first > 0:
                idxs.append([first, last])
            first = None
            last = None

    # Check the sampled edges
    for idx in idxs:
        edg = edg[idx[0]:idx[1]].T
        if edg.shape[1] == 0:
            continue
        xp, yp = proj(edg[0], edg[1])
        dsts = (np.diff(xp)**2 + np.diff(yp)**2 +
                np.diff(edg[2])**2)
        dsts = np.array([dsts[0]] + dsts.tolist())
        dsts = dsts[~np.isnan(edg[2])]

        np.testing.assert_allclose(dsts, dsts[0], rtol=2e-2)


def _dbg_plot(new_edges=None, profs=None, npr=None, ref_idx=None,
              num=False, hold=False):
    # This is a plotting function used for debugging

    ax = plt.figure().add_subplot(projection='3d')

    if new_edges is not None:
        for key in new_edges:
            edg = np.array(new_edges[key])
            plt.plot(edg[:, 0], edg[:, 1], edg[:, 2], 'g-x', lw=1)
            for ie, ee in enumerate(edg):
                ax.text(ee[0], ee[1], ee[2], s=f'{ie}')

    if profs is not None:
        for pro in profs:
            edg = np.array(pro)
            plt.plot(edg[:, 0], edg[:, 1], edg[:, 2], 'r', lw=3)
        edg = np.array(profs[ref_idx])
        plt.plot(edg[:, 0], edg[:, 1], edg[:, 2], 'y--', lw=3, zorder=100)

    if npr is not None:
        for pro in npr:
            edg = np.array(pro)
            idx = np.nonzero(np.isfinite(edg[:, 0]))
            edg = np.squeeze(edg[idx, :])
            plt.plot(edg[:, 0], edg[:, 1], edg[:, 2], 'b')

    ax.invert_zaxis()

    if not hold:
        plt.show()

    return ax


def _build_profiles(edges: list) -> list:
    # From edges builds the profiles
    #
    # :param edges:
    #   A list where each element (a list of 3d coordinates) represents and
    #   edge

    profs = []
    max_len = -1
    tc = [np.nan, np.nan, np.nan]
    for i_edge, key in enumerate(edges):
        edge = edges[key]
        max_len = max([len(edge), max_len])
        # Add the values in this edge to the profiles
        for i_r, c in enumerate(edge):
            if len(profs) == i_r and i_edge > 0:
                # Adding a new profile
                tmp = []
                if i_edge > 0 and i_r > 0:
                    tmp = [tc for i in range(len(profs[i_r - 1]) - 1)]
                profs.append(tmp + [c])
            elif len(profs) == i_r and i_edge == 0:
                profs.append([c])
            else:
                profs[i_r].append(c)

        if len(edge) < max_len:
            for i_r in range(len(edge), max_len):
                profs[i_r].append(tc)

    max_len = max([len(p) for p in profs])

    # Set the same length for all the profiles
    for i_prof, prof in enumerate(profs):
        if len(prof) < max_len:
            for i in range(len(prof), max_len):
                profs[i_prof].append([np.nan, np.nan, np.nan])
    return profs


def _build_edges(coos):
    # This function builds the edges starting from a set of continuos
    # 'sub-edges'
    #
    # :param coos:
    #   A list with a triple. The first element in the triple is the index of
    #   the column from where the subedge starts, the second in the index of
    #   the ending column and the last element is an array with the coordinates
    #
    edges = {}
    for coo in coos:
        if coo[1] not in edges:
            if coo[0] > 0:
                tmp = _fill(coo[0], coo[2])
            else:
                tmp = np.squeeze(coo[2]).tolist()
            # Check that the edge contains more than one point
            if isinstance(tmp[0], list):
                edges[coo[1]] = tmp
        else:
            if coo[0] > 0:
                tmp = _fill(coo[0] - len(edges[coo[1]]), coo[2])
            else:
                tmp = coo[2].tolist()

            # Check that the edge contains more than one point
            if isinstance(tmp[0], list):
                edges[coo[1]].extend(tmp)
    return edges


def _fill(delta, coo):
    delta = int(delta)
    add = np.empty((delta, 3))
    add[:] = np.nan
    out = np.vstack((add, coo))
    return out.tolist()


def _get_intersections(edges, lines, proj):
    pnts = []
    idxs = []
    for i_vtx in range(len(edges) - 1):

        xp, yp = proj(edges[i_vtx:i_vtx + 2, 0], edges[i_vtx:i_vtx + 2, 1])
        slope, intercept, _, _, _ = stats.linregress(xp, yp)

        for i_line, line in enumerate(lines):

            # Intersection between edge and profile
            if line[0] >= VERY_BIG:
                xi = line[1]
                yi = xi * slope + intercept
            else:
                xi = (intercept - line[1]) / (line[0] - slope)
                yi = xi * slope + intercept

            # Check if intercept is along the segment
            if (xi > np.min([xp]) and xi < np.max([xp]) and
                    yi > np.min([yp]) and yi < np.max([yp])):
                xg, yg = proj(np.array([xi]), np.array([yi]), reverse=True)
                zi = _get_point_depth([xp[0], yp[0], edges[i_vtx, 2]],
                                      [xp[1], yp[1], edges[i_vtx + 1, 2]],
                                      xi)
                pnts.append([xg[0], yg[0], zi])
                idxs.append(i_line)

    return np.array(pnts), min(idxs)


def _line3d(pnt1, pnt2):
    return [pnt2[0] - pnt1[0], pnt2[1] - pnt1[1], pnt2[2] - pnt1[2]]


def _get_point_depth(pnt1, pnt2, xco):
    vect = _line3d(pnt1, pnt2)
    ratio = (xco - pnt1[0]) / vect[0]
    return vect[2] * ratio + pnt1[2]


def _compute_lines(coos: list, i_from: int, proj, new_lines_profiles):
    # Compute the line equation representing each profile
    #
    # :param coos:
    #   A list of lists. Each element contains two intergers and one array with
    #   the coordinates of the edge. The two integers indicate the index from
    #   where this edge starts.
    # :param i_from:
    #   The index from where
    # :param proj:
    #   An instance of
    #   :class:`openquake.hazardlib.geo.utils.OrthographicProjection`
    # :param new_lines_profiles:
    #   A list containing the values of the slope and intercept for each line

    # Create the profiles
    profs = []
    for i_coo, coo in enumerate(coos):
        if coo[0] == i_from:
            for i_c, c in enumerate(coo[2]):
                if len(profs) == i_c:
                    profs.append([list(coo[2][i_c])])
                else:
                    profs[i_c].append(list(coo[2][i_c]))

    for prof in profs:
        prof = np.array(prof)
        xp, yp = proj(prof[:, 0], prof[:, 1])

        # Check if the line is vertical
        if np.all(np.abs(xp[0] - xp) < SMALL):
            slope = VERY_BIG
            intercept = xp[0]
        else:
            slope, intercept, _, _, _ = stats.linregress(xp, yp)
        new_lines_profiles.append([slope, intercept])


def _set_indexes(forward: bool, ref_idx: int, len_profs: int):
    # Defines the indexes of the original profiles to be investigated
    step = 1
    low = ref_idx
    upp = len_profs
    if not forward:
        step = -1
        low = ref_idx
        upp = -1
    return low, upp, step


def fix_mesh(msh: npt.ArrayLike) -> np.ndarray:
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
        ru = i + 1
        rl = i - 1

        for j in range(msh.shape[1]):
            cu = j + 1
            cl = j - 1

            trl = False if cl < 0 else np.isfinite(msh[i, cl, 0])
            tru = (False if cu > msh.shape[1] - 1 else
                   np.isfinite(msh[i, cu, 0]))
            tcl = False if rl < 0 else np.isfinite(msh[rl, j, 0])
            tcu = (False if ru > msh.shape[0] - 1 else
                   np.isfinite(msh[ru, j, 0]))

            check_row = trl or tru
            check_col = tcl or tcu

            if not (check_row and check_col):
                msh[i, j, :] = np.nan
    return msh


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
    minwdt = 2

    # Arrays with coordinates
    coo1 = pro1.coo
    coo2 = pro2.coo

    # Compute the shift with the minimum difference
    mindff = 1e20
    minidx = None
    for i1 in range(0, len(coo1) - minwdt):
        lle = np.min([len(coo1[i1:, 2]), len(coo2[:, 2])])
        dff = np.sum(np.abs(coo1[i1:i1 + lle, 2] - coo2[0:lle, 2]))
        if mindff > dff:
            minidx = i1
            mindff = dff
    return minidx
