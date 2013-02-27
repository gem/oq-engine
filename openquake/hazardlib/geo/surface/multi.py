# The Hazard Library
# Copyright (C) 2013 GEM Foundation
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
Module :mod:`openquake.hazardlib.geo.surface.multi` defines
:class:`MultiSurface`.
"""
import numpy

from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.geo.mesh import Mesh


class MultiSurface(BaseSurface):
    """
    Represent a surface as a collection of independent surface elements.

    :param surfaces:
        List of instances of subclasses of
        :class:`~openquake.hazardlib.geo.surface.BaseSurface`
        each representing a surface geometry element.

    Another way to construct the surface object is to call
    :meth:`from_simple_fault_data`.
    """
    def __init__(self, surfaces):
        self.surfaces = surfaces
        self.areas = None

    def get_min_distance(self, mesh):
        """
        For each point in ``mesh`` compute the minimum distance to each
        surface element and return the smallest value.

        See :meth:`superclass method
        <.base.BaseSurface.get_min_distance>`
        for spec of input and result values.
        """
        dists = [surf.get_min_distance(mesh) for surf in self.surfaces]

        return numpy.min(dists, axis=0)

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
        dists = numpy.array(
            [surf.get_min_distance(mesh).flatten() for surf in self.surfaces]
        )

        # find for each point in mesh the index of closest surface
        idx = dists == numpy.min(dists, axis=0)

        # loop again over surfaces. For each surface compute the closest
        # points, and associate them to the mesh points for which the surface
        # is the closest. Note that if a surface is not the closest to any of
        # the mesh points then the calculation is skipped
        lons = numpy.empty_like(mesh.lons.flatten())
        lats = numpy.empty_like(mesh.lats.flatten())
        depths = None if mesh.depths is None else \
            numpy.empty_like(mesh.depths.flatten())
        for i, surf in enumerate(self.surfaces):
            if not idx[i, :].any():
                continue
            cps = surf.get_closest_points(mesh)
            lons[idx[i, :]] = cps.lons.flatten()[idx[i, :]]
            lats[idx[i, :]] = cps.lats.flatten()[idx[i, :]]
            if depths is not None:
                depths[idx[i, :]] = cps.depths.flatten()[idx[i, :]]
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
        # for each point in mesh compute the Joyner-Boore distance to all the
        # surfaces and return the shortest one.
        dists = [
            surf.get_joyner_boore_distance(mesh) for surf in self.surfaces
        ]

        return numpy.min(dists, axis=0)

    def get_rx_distance(self, mesh):
        """
        For each point in mesh find the closest surface element, and return
        the corresponding rx distance.

        See :meth:`superclass method
        <.base.BaseSurface.get_rx_distance>`
        for spec of input and result values.
        """
        # For each point in mesh compute minimum distance to all surface
        # elements. The distance matrix is flattend, because mesh can be of
        # an arbitrary shape. By flattening we obtain a ``distances`` matrix
        # for which the first dimension represents the different surfaces
        # and the second dimension the mesh points.
        dists = numpy.array(
            [surf.get_min_distance(mesh).flatten() for surf in self.surfaces]
        )

        # find for each point in mesh the index of closest surface
        idx = dists == numpy.min(dists, axis=0)

        # for each surface elements compute rx distances, and associate
        # them to the mesh points for which the surface is the closest
        rx_dists = numpy.empty_like(mesh.lons.flatten())
        for i, surf in enumerate(self.surfaces):
            if not idx[i, :].any():
                continue
            rx = surf.get_rx_distance(mesh)
            rx_dists[idx[i, :]] = rx.flatten()[idx[i, :]]

        rx_dists = rx_dists.reshape(mesh.lons.shape)

        return rx_dists

    def get_top_edge_depth(self):
        """
        Compute top edge depth of each surface element and return area-weighted
        average value (in km).
        """
        areas = self._get_areas()
        depths = numpy.array(
            [surf.get_top_edge_depth() for surf in self.surfaces]
        )

        return numpy.sum(areas * depths) / numpy.sum(areas)

    def get_strike(self):
        """
        Compute strike of each surface element and return area-weighted average
        value (in range ``[0, 360]``) using formula from:
        http://en.wikipedia.org/wiki/Mean_of_circular_quantities

        Note that the original formula has been adapted to compute a weighted
        rather than arithmetic mean.
        """
        areas = self._get_areas()
        strikes = numpy.array([surf.get_strike() for surf in self.surfaces])

        v1 = (numpy.sum(areas * numpy.sin(numpy.radians(strikes))) /
              numpy.sum(areas))
        v2 = (numpy.sum(areas * numpy.cos(numpy.radians(strikes))) /
              numpy.sum(areas))

        return numpy.degrees(numpy.arctan2(v1, v2)) % 360

    def get_dip(self):
        """
        Compute dip of each surface element and return area-weighted average
        value (in range ``(0, 90]``).

        Given that dip values are constrained in the range (0, 90], the simple
        formula for weighted mean is used.
        """
        areas = self._get_areas()
        dips = numpy.array([surf.get_dip() for surf in self.surfaces])

        return numpy.sum(areas * dips) / numpy.sum(areas)

    def get_width(self):
        """
        Compute width of each surface element, and return area-weighted
        average value (in km).
        """
        areas = self._get_areas()
        widths = numpy.array([surf.get_width() for surf in self.surfaces])

        return numpy.sum(areas * widths) / numpy.sum(areas)

    def get_area(self):
        """
        Return sum of surface elements areas (in squared km).
        """
        return numpy.sum(self._get_areas())

    def _get_areas(self):
        """
        Return surface elements area values in a numpy array.
        """
        if self.areas is None:
            self.areas = []
            for surf in self.surfaces:
                self.areas.append(surf.get_area())
            self.areas = numpy.array(self.areas)

        return self.areas
