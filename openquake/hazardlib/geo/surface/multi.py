# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2023 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.surface.multi` defines
:class:`MultiSurface`.
"""
import numpy as np
from shapely.geometry import Polygon
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo import utils
from openquake.hazardlib import geo
from openquake.hazardlib.geo.surface import (
    PlanarSurface, SimpleFaultSurface, ComplexFaultSurface)
from openquake.hazardlib.geo.multiline import get_tu, MultiLine


class MultiSurface(BaseSurface):
    """
    Represent a surface as a collection of independent surface elements.

    :param surfaces:
        List of instances of subclasses of
        :class:`~openquake.hazardlib.geo.surface.base.BaseSurface`
        each representing a surface geometry element.
    """

    @property
    def surface_nodes(self):
        """
        :returns:
            a list of surface nodes from the underlying single node surfaces
        """
        if type(self.surfaces[0]).__name__ == 'PlanarSurface':
            return [surf.surface_nodes[0] for surf in self.surfaces]
        return [surf.surface_nodes for surf in self.surfaces]

    @classmethod
    def from_csv(cls, fname: str):
        """
        :param fname:
            path to a CSV file with header (lon, lat, dep) and 4 x P
            rows describing planes in terms of corner points in the order
            topleft, topright, bottomright, bottomleft
        :returns:
            a MultiSurface made of P planar surfaces
        """
        surfaces = []
        tmp = np.genfromtxt(fname, delimiter=',', comments='#', skip_header=1)
        tmp = tmp.reshape(-1, 4, 3, order='A')
        for i in range(tmp.shape[0]):
            arr = tmp[i, :, :]
            surfaces.append(PlanarSurface.from_ucerf(arr))
        return cls(surfaces)

    @property
    def mesh(self):
        """
        :returns: mesh corresponding to the whole multi surface
        """
        lons = []
        lats = []
        deps = []
        for m in [surface.mesh for surface in self.surfaces]:
            ok = np.isfinite(m.lons) & np.isfinite(m.lats)
            lons.append(m.lons[ok])
            lats.append(m.lats[ok])
            deps.append(m.depths[ok])
        return Mesh(np.concatenate(lons), np.concatenate(lats),
                    np.concatenate(deps))

    def __init__(self, surfaces: list, tol: float = 1):
        """
        Intialize a multi surface object from a list of surfaces
        :param list surfaces:
            A list of instances of subclasses of
            :class:`openquake.hazardlib.geo.surface.BaseSurface`
        :param float tol:
            A float in decimal degrees representing the tolerance admitted in
            representing the rupture trace.
        """
        self.surfaces = surfaces
        self.tol = tol
        self._set_tor()
        self.areas = None
        self.tut = None
        self.uut = None
        self.site_mesh = None

    def _set_tor(self):
        """
        Computes the list of the vertical surface projections of the top of
        the ruptures from the set of surfaces defining the multi fault.
        We represent the surface projection of each top of rupture with an
        instance of a :class:`openquake.hazardlib.geo.multiline.Multiline`
        """
        tors = []
        classes = (ComplexFaultSurface, SimpleFaultSurface)

        for srfc in self.surfaces:

            if isinstance(srfc, geo.surface.kite_fault.KiteSurface):
                lo, la = srfc.get_tor()
                line = geo.Line.from_vectors(lo, la)
                line.keep_corners(self.tol)
                tors.append(line)

            elif isinstance(srfc, PlanarSurface):
                lo = []
                la = []
                for pnt in [srfc.top_left, srfc.top_right]:
                    lo.append(pnt.longitude)
                    la.append(pnt.latitude)
                tors.append(geo.line.Line.from_vectors(lo, la))

            elif isinstance(srfc, classes):
                lons = srfc.mesh.lons[0, :]
                lats = srfc.mesh.lats[0, :]
                coo = np.array([[lo, la] for lo, la in zip(lons, lats)])
                line = geo.line.Line.from_vectors(coo[:, 0], coo[:, 1])
                line.keep_corners(self.tol)
                tors.append(line)

            else:
                raise ValueError(f"Surface {str(srfc)} not supported")

        # Set the multiline representing the rupture traces i.e. vertical
        # projections at the surface of the top of ruptures
        self.tors = geo.MultiLine(tors)

    def get_min_distance(self, mesh):
        """
        For each point in ``mesh`` compute the minimum distance to each
        surface element and return the smallest value.
        See :meth:`superclass method
        <.base.BaseSurface.get_min_distance>`
        for spec of input and result values.
        """
        dists = [surf.get_min_distance(mesh) for surf in self.surfaces]
        return np.min(dists, axis=0)

    def get_closest_points(self, mesh):
        """
        For each point in ``mesh`` find the closest surface element, and return
        the corresponding closest point.
        See :meth:`superclass method
        <.base.BaseSurface.get_closest_points>`
        for spec of input and result values.
        """
        # first, for each point in mesh compute minimum distance to each
        # surface. The distance matrix is flattend, because mesh can be of
        # an arbitrary shape. By flattening we obtain a ``distances`` matrix
        # for which the first dimension represents the different surfaces
        # and the second dimension the mesh points.
        dists = np.array(
            [surf.get_min_distance(mesh).flatten() for surf in self.surfaces]
        )

        # find for each point in mesh the index of closest surface
        idx = dists == np.min(dists, axis=0)

        # loop again over surfaces. For each surface compute the closest
        # points, and associate them to the mesh points for which the surface
        # is the closest. Note that if a surface is not the closest to any of
        # the mesh points then the calculation is skipped
        lons = np.empty_like(mesh.lons.flatten())
        lats = np.empty_like(mesh.lats.flatten())

        depths = None if mesh.depths is None else \
            np.empty_like(mesh.depths.flatten())

        # the centroid info for the sites must be evaluated and populated
        # one site at a time
        for jdx in idx.T:
            i = np.where(jdx)[0][0]
            surf = self.surfaces[i]
            cps = surf.get_closest_points(mesh)
            idx_i = idx[i, :]
            lons[idx_i] = cps.lons[idx_i]
            lats[idx_i] = cps.lats[idx_i]
            if depths is not None:
                depths[idx_i] = cps.depths[idx_i]
        lons = lons.reshape(mesh.lons.shape)
        lats = lats.reshape(mesh.lats.shape)
        if depths is not None:
            depths = depths.reshape(mesh.depths.shape)
        return Mesh(lons, lats, depths)

    def get_joyner_boore_distance(self, mesh):
        """
        For each point in mesh compute the Joyner-Boore distance to all the
        surface elements and return the smallest value.
        See :meth:`superclass method
        <.base.BaseSurface.get_joyner_boore_distance>`
        for spec of input and result values.
        """
        # For each point in mesh compute the Joyner-Boore distance to all the
        # surfaces and return the shortest one.
        dists = [
            surf.get_joyner_boore_distance(mesh) for surf in self.surfaces]
        return np.min(dists, axis=0)

    def get_top_edge_depth(self):
        """
        Compute top edge depth of each surface element and return area-weighted
        average value (in km).
        """
        areas = self._get_areas()
        depths = np.array([np.mean(surf.get_top_edge_depth()) for surf
                           in self.surfaces])
        ted = np.sum(areas * depths) / np.sum(areas)
        assert np.isfinite(ted).all()
        return ted

    def get_strike(self):
        """
        Compute strike of each surface element and return area-weighted average
        value (in range ``[0, 360]``) using formula from:
        http://en.wikipedia.org/wiki/Mean_of_circular_quantities
        Note that the original formula has been adapted to compute a weighted
        rather than arithmetic mean.
        """
        areas = self._get_areas()
        strikes = np.array([surf.get_strike() for surf in self.surfaces])
        w = areas / areas.sum()  # area weights
        s = np.radians(strikes)
        v1 = w @ np.sin(s)
        v2 = w @ np.cos(s)
        return np.degrees(np.arctan2(v1, v2)) % 360

    def get_dip(self):
        """
        Compute dip of each surface element and return area-weighted average
        value (in range ``(0, 90]``).
        Given that dip values are constrained in the range (0, 90], the simple
        formula for weighted mean is used.
        """
        areas = self._get_areas()
        dips = np.array([surf.get_dip() for surf in self.surfaces])
        ok = np.logical_and(np.isfinite(dips), np.isfinite(areas))[0]
        dips = dips[ok]
        areas = areas[ok]
        dip = np.sum(areas * dips) / np.sum(areas)
        return dip

    def get_width(self):
        """
        Compute width of each surface element, and return area-weighted
        average value (in km).
        """
        areas = self._get_areas()
        widths = np.array([surf.get_width() for surf in self.surfaces])
        return np.sum(areas * widths) / np.sum(areas)

    def get_area(self):
        """
        Return sum of surface elements areas (in squared km).
        """
        return np.sum(self._get_areas())

    def get_bounding_box(self):
        """
        Compute bounding box for each surface element, and then return
        the bounding box of all surface elements' bounding boxes.

        :return:
           A tuple of four items. These items represent western, eastern,
           northern and southern borders of the bounding box respectively.
           Values are floats in decimal degrees.
        """
        lons = []
        lats = []
        for surf in self.surfaces:
            west, east, north, south = surf.get_bounding_box()
            lons.extend([west, east])
            lats.extend([north, south])
        return utils.get_spherical_bounding_box(lons, lats)

    def get_middle_point(self):
        """
        If :class:`MultiSurface` is defined by a single surface, simply
        returns surface's middle point, otherwise find surface element closest
        to the surface's bounding box centroid and return corresponding
        middle point.
        Note that the concept of middle point for a multi surface is ambiguous
        and alternative definitions may be possible. However, this method is
        mostly used to define the hypocenter location for ruptures described
        by a multi surface
        (see :meth:`openquake.hazardlib.source.characteristic.CharacteristicFaultSource.iter_ruptures`).
        This is needed because when creating fault based sources, the rupture's
        hypocenter locations are not explicitly defined, and therefore an
        automated way to define them is required.
        """
        if len(self.surfaces) == 1:
            return self.surfaces[0].get_middle_point()
        west, east, north, south = self.get_bounding_box()
        longitude, latitude = utils.get_middle_point(west, north, east, south)
        dists = []
        for surf in self.surfaces:
            dists.append(
               surf.get_min_distance(Mesh(np.array([longitude]),
                                          np.array([latitude]),
                                          None)))
        dists = np.array(dists).flatten()
        idx = dists == np.min(dists)
        return np.array(self.surfaces)[idx][0].get_middle_point()

    def get_surface_boundaries(self):
        los, las = self.surfaces[0].get_surface_boundaries()
        poly = Polygon((lo, la) for lo, la in zip(los, las))
        for i in range(1, len(self.surfaces)):
            los, las = self.surfaces[i].get_surface_boundaries()
            polyt = Polygon([(lo, la) for lo, la in zip(los, las)])
            poly = poly.union(polyt)
        coo = np.array([[lo, la] for lo, la in list(poly.exterior.coords)])
        return coo[:, 0], coo[:, 1]

    def get_surface_boundaries_3d(self):
        lons = []
        lats = []
        deps = []
        for surf in self.surfaces:
            lons_surf, lats_surf, deps_surf = surf.get_surface_boundaries_3d()
            lons.extend(lons_surf)
            lats.extend(lats_surf)
            deps.extend(deps_surf)
        return lons, lats, deps

    def _get_areas(self):
        """
        Return surface elements area values in a numpy array.
        """
        if self.areas is None:
            self.areas = []
            for surf in self.surfaces:
                self.areas.append(surf.get_area())
            self.areas = np.array(self.areas)
        return self.areas

    def _set_tu(self, mesh: Mesh):
        """
        Set the values of T and U
        """
        self._set_tor()
        if self.tors.shift is None:
            self.tors._set_coordinate_shift()
        tupps = []
        uupps = []
        weis = []
        for line in self.tors.lines:
            tu, uu, we = line.get_tu(mesh)
            tupps.append(tu)
            uupps.append(uu)
            weis.append(np.squeeze(np.sum(we, axis=0)))

        # `get_tu` is a function in the multiline module
        uut, tut = get_tu(self.tors.shift, tupps, uupps, weis)
        self.uut = uut
        self.tut = tut
        self.site_mesh = mesh

    def get_rx_distance(self, mesh):
        """
        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh` with the
            coordinates of the sites.
        :returns:
            A :class:`numpy.ndarray` instance with the Rx distance. Note that
            the Rx distance is directly taken from the GC2 t-coordinate.
        """
        # This checks that the info stored is consistent with the mesh of
        # points used
        condition2 = (self.site_mesh is not None and self.site_mesh != mesh)
        if (self.uut is None) or condition2:
            self._set_tu(mesh)
        rx = self.tut[0] if len(self.tut[0].shape) > 1 else self.tut
        return rx

    def get_ry0_distance(self, mesh):
        """
        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh` with the
            coordinates of the sites.
        """
        self._set_tor()
        return self.tors.get_ry0_distance(mesh)


def _multi_distances(surface, sites, param):
    if param == 'rrup':
        dist = surface.get_min_distance(sites)
    elif param == 'rjb':
        dist = surface.get_joyner_boore_distance(sites)
    elif param in ['rx', 'ry0']:
        # In this case we compute the GC2 coordinates for the surface
        tor_lo, tor_la = surface.get_tor()
        tor = geo.line.Line.from_vectors(tor_lo, tor_la)
        t_upp, u_upp, wei = tor.get_tu(sites)
        wei_sum = np.squeeze(np.sum(wei, axis=0))
        # Get the u-coordinate on the last vertex of the trace
        mesh = Mesh(tor_lo[[0, -1]], tor_la[[0, -1]])
        _, uu, _ = tor.get_tu(mesh)
        # Save data
        dists = {'tor': tor, 't_upp': t_upp, 'u_upp': u_upp, 'wei': wei_sum,
                 'umax': max(uu)}
    else:
        raise ValueError(f'Unknown distance measure {param}')
    if param in ['rrup', 'rjb']:
        dists = {param: dist}
    return dists


def _multi_rx_ry0(dcache, suids, param):

    # Get the multiline used to compute distances
    multil = _get_multi_line(dcache, suids)

    # Get GC coordinates
    multil.set_tu()

    # Get Rx and Ry0
    if param == 'rx':
        return multil.get_rx_distance()
    elif param == 'ry0':
        return multil.get_ry0_distance()
    else:
        raise ValueError('%s is not rx or ry0' % param)


def _get_multi_line(dcache, suids):

    # Retrieve info from the cache
    lines = [dcache[key, 'tor'] for key in suids]

    # Create the multiline
    multil = MultiLine(lines)
    revert = multil.set_overall_strike()
    soidx = multil._set_origin()
    revert = revert[soidx]

    # Load data in cache
    tupps = [dcache[suids[i], 't_upp'] for i in soidx]
    uupps = [dcache[suids[i], 'u_upp'] for i in soidx]
    weis = [dcache[suids[i], 'wei'] for i in soidx]
    umax = [dcache[suids[i], 'umax'] for i in soidx]

    # Change sign to the reverted surface traces
    for i, flag in enumerate(revert):
        if flag:
            tupps[i] = -tupps[i]
            uupps[i] = -(uupps[i] - umax[i])

    # Fixing shift
    multil._set_coordinate_shift()
    multil.set_u_max()
    multil.tupps = tupps
    multil.uupps = uupps
    multil.weis = np.array(weis)  # shape (N, 3)
    multil.weis.flags.writeable = False  # nobody must change the weights
    return multil
