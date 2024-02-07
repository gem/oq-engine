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

    # NB: without a cache, get_closest_points calls it
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

    def __init__(self, surfaces, tor=None, tol=1.):
        """
        Intialize a multi surface object from a list of surfaces

        :param surfaces:
            A list of instances of subclasses of
            :class:`openquake.hazardlib.geo.surface.BaseSurface`
        :param tol:
            A float in decimal degrees representing the tolerance admitted in
            representing the rupture trace.
        """
        self.surfaces = surfaces
        self.tol = tol
        self.tor = tor
        self.areas = None

    # called at each instantiation
    def _set_tor(self):
        """
        Computes the list of the vertical surface projections of the top of
        the ruptures from the set of surfaces defining the multi fault.
        We represent the surface projection of each top of rupture with an
        instance of a :class:`openquake.hazardlib.geo.multiline.Multiline`
        """
        tors = []

        for srfc in self.surfaces:

            if isinstance(srfc, geo.surface.kite_fault.KiteSurface):
                # in classical/case_62 there are KiteSurfaces and
                # PlanarSurfaces together in NonParametricSources
                # the `idx` is used only in MultiFaultSources
                # srfc.tor_line.idx = getattr(srfc, 'idx', None)
                tors.append(srfc.tor_line.keep_corners(self.tol))

            elif isinstance(srfc, PlanarSurface):
                lo = []
                la = []
                for pnt in [srfc.top_left, srfc.top_right]:
                    lo.append(pnt.longitude)
                    la.append(pnt.latitude)
                tors.append(geo.line.Line.from_vectors(lo, la))

            elif isinstance(srfc, (ComplexFaultSurface, SimpleFaultSurface)):
                lons = srfc.mesh.lons[0, :]
                lats = srfc.mesh.lats[0, :]
                coo = np.array([[lo, la] for lo, la in zip(lons, lats)])
                line = geo.line.Line.from_vectors(coo[:, 0], coo[:, 1])
                tors.append(line.keep_corners(self.tol))

            else:
                raise ValueError(f"Surface {str(srfc)} not supported")

        # Set the multiline representing the rupture traces i.e. vertical
        # projections at the surface of the top of ruptures
        self.tor = geo.MultiLine(tors)

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
        return utils.get_spherical_bounding_box(np.array(lons), np.array(lats))

    # NB: this is only called by CharacteristicSources, see logictree/case_20
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
                                          np.array([latitude]))))
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
        conc = np.concatenate
        for surf in self.surfaces:
            coo = surf.get_surface_boundaries_3d()
            lons.append(coo[0])
            lats.append(coo[1])
            deps.append(coo[2])
        return conc(lons), conc(lats), conc(deps)

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

    def get_rx_distance(self, mesh):
        """
        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh` with the
            coordinates of the sites.
        :returns:
            A :class:`numpy.ndarray` instance with the Rx distance. Note that
            the Rx distance is directly taken from the GC2 t-coordinate.
        """
        if self.tor is None:
            self._set_tor()
        uut, tut = self.tor.get_uts(mesh)
        rx = tut[0] if len(tut[0].shape) > 1 else tut
        return rx

    def get_ry0_distance(self, mesh):
        """
        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh` with the
            coordinates of the sites.
        """
        if self.tor is None:
            self._set_tor()

        uut, tut = self.tor.get_uts(mesh)
        ry0 = np.zeros_like(uut)
        ry0[uut < 0] = np.abs(uut[uut < 0])
        condition = uut > self.tor.u_max
        ry0[condition] = uut[condition] - self.tor.u_max
        return ry0
