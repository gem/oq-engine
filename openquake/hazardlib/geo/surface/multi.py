# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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
import numpy
from copy import deepcopy
from scipy.spatial.distance import pdist, squareform
from openquake.hazardlib.geo.surface.base import (BaseSurface,
                                                  downsample_trace)
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo import utils
from openquake.hazardlib.geo.surface import (
    PlanarSurface, SimpleFaultSurface, ComplexFaultSurface)
from openquake.hazardlib.geo.surface.gridded import GriddedSurface


class MultiSurface(BaseSurface):
    """
    Represent a surface as a collection of independent surface elements.

    :param surfaces:
        List of instances of subclasses of
        :class:`~openquake.hazardlib.geo.surface.base.BaseSurface`
        each representing a surface geometry element.

    :param edge_set:
        Retains list of upper edges from all of the surfaces, with each
        edge given as a numpy array of [longitude, latitude, depth]

    :param cartesian_edges:
        For GC2, this holds the list of edge sets in an orthographic projection
        such that the coordinates are all cartesian.

    :param cartesian_endpoints:
        For GC2, this hold the list of end-points of the edges in an
        orthographic projection

    :param proj:
        For GC2, instance of :class:
        `~openquake.hazardlib.geo.utils.OrthographicProjection` instantiated
        with the bounding box limits of the fault

    :param length_set:
        List of lengths of upper edges of each surface

    :param cum_length_set:
        List of cumulative lengths of edges along fault

    :param gc2_config:
        For GC2, dictionary holding fault specific parameters for GC2
        configuration

    :param p0:
        For GC2, reference origin point of the fault

    :param gc2t:
        GC2 T-coordinate

    :param gc2u:
        GC2 U-coordinate

    :param tmp_mesh:
        If fed with the same mesh twice (e.g. calling get_rx_distance and
        then get_ry0_distance in sequence) does not repeat GC2 calculations,
        this hold the last mesh it was fed with

    :param gc_length:
        For GC2, determines the length of the fault (km) in its own GC2
        configuration
    """

    @property
    def surface_nodes(self):
        """
        :returns:
            a list of surface nodes from the underlying single node surfaces
        """
        return [surf.surface_nodes[0] for surf in self.surfaces]

    def __init__(self, surfaces, tol=0.1):
        """
        Instantiate object with list of surfaces

        :param float tol:
            If surfaces contains an instance of :class:
            `~openquake.hazardlib.geo.surface.simple_fault.SimpleFaultSurface`
            or of :class:
            `~openquake.hazardlib.geo.surface.complex_fault.ComplexFaultSurface`
            then the surface is downsampled so that only the points
            representing changes in strike are retained. This parameter sets
            the tolerance (in degrees) for defining a change in strike
            direction
        """
        self.surfaces = surfaces
        self.areas = None
        self.edge_set = self._get_edge_set(tol)
        self.cartesian_edges = []
        self.cartesian_endpoints = []
        self.proj = None
        self.length_set = []
        self.cum_length_set = []
        self.gc2_config = None
        self.p0 = None
        self.gc2t = None
        self.gc2u = None
        self.tmp_mesh = None
        self.gc_length = None

    def _get_edge_set(self, tol=0.1):
        """
        Retrieve set of top edges from all of the individual surfaces,
        downsampling the upper edge based on the specified tolerance
        """
        edges = []
        for surface in self.surfaces:
            if isinstance(surface, GriddedSurface):
                return edges.append(surface.mesh)
            elif isinstance(surface, PlanarSurface):
                # Top edge determined from two end points
                edge = []
                for pnt in [surface.top_left, surface.top_right]:
                    edge.append([pnt.longitude, pnt.latitude, pnt.depth])
                edges.append(numpy.array(edge))
            elif isinstance(surface,
                            (ComplexFaultSurface, SimpleFaultSurface)):
                # Rectangular meshes are downsampled to reduce their
                # overall size
                edges.append(downsample_trace(surface.mesh, tol))
            else:
                raise ValueError("Surface %s not recognised" % str(surface))
        return edges

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
                surf.get_min_distance(Mesh(numpy.array([longitude]),
                                           numpy.array([latitude]),
                                           None))
            )
        dists = numpy.array(dists).flatten()

        idx = dists == numpy.min(dists)
        return numpy.array(self.surfaces)[idx][0].get_middle_point()

    def get_surface_boundaries(self):
        lons = []
        lats = []
        for surf in self.surfaces:
            lons_surf, lats_surf = surf.get_surface_boundaries()
            lons.append(lons_surf[0])
            lats.append(lats_surf[0])
        return lons, lats

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

    def _get_cartesian_edge_set(self):
        """
        For the GC2 calculations a set of cartesian representations of the
        fault edges are needed. In this present case we use a common cartesian
        framework for all edges, as opposed to defining a separate orthographic
        projection per edge
        """
        # Get projection space for cartesian projection
        edge_sets = numpy.vstack(self.edge_set)
        west, east, north, south = utils.get_spherical_bounding_box(
            edge_sets[:, 0],
            edge_sets[:, 1])
        self.proj = utils.get_orthographic_projection(west, east, north, south)

        for edges in self.edge_set:
            # Project edges into cartesian space
            px, py = self.proj(edges[:, 0], edges[:, 1])
            # Store the two end-points of the trace
            self.cartesian_endpoints.append(
                numpy.array([[px[0], py[0], edges[0, 2]],
                             [px[-1], py[-1], edges[-1, 2]]])
                )
            self.cartesian_edges.append(numpy.column_stack([px, py,
                                                            edges[:, 2]]))
            # Get surface length vector for the trace - easier in cartesian
            lengths = numpy.sqrt((px[:-1] - px[1:]) ** 2. +
                                 (py[:-1] - py[1:]) ** 2.)
            self.length_set.append(lengths)
            # Get cumulative surface length vector
            self.cum_length_set.append(numpy.hstack([0.,
                                                     numpy.cumsum(lengths)]))
        return edge_sets

    def _setup_gc2_framework(self):
        """
        This method establishes the GC2 framework for a multi-segment
        (and indeed multi-typology) case based on the description in
        Spudich & Chiou (2015) - see section on Generalized Coordinate
        System for Multiple Rupture Traces
        """
        # Generate cartesian edge set
        edge_sets = self._get_cartesian_edge_set()
        self.gc2_config = {}
        # Determine furthest two points apart
        endpoint_set = numpy.vstack([cep for cep in self.cartesian_endpoints])
        dmat = squareform(pdist(endpoint_set))
        irow, icol = numpy.unravel_index(numpy.argmax(dmat), dmat.shape)
        # Join further points to form a vector (a_hat in Spudich & Chiou)
        # According to Spudich & Chiou, a_vec should be eastward trending
        if endpoint_set[irow, 0] > endpoint_set[icol, 0]:
            # Row point is to the east of column point
            beginning = endpoint_set[icol, :2]
            ending = endpoint_set[irow, :2]
        else:
            # Column point is to the east of row point
            beginning = endpoint_set[irow, :2]
            ending = endpoint_set[icol, :2]

        # Convert to unit vector
        a_vec = ending - beginning
        self.gc2_config["a_hat"] = a_vec / numpy.linalg.norm(a_vec)
        # Get e_j set
        self.gc2_config["ejs"] = []
        for c_edges in self.cartesian_edges:
            self.gc2_config["ejs"].append(
                numpy.dot(c_edges[-1, :2] - c_edges[0, :2],
                          self.gc2_config["a_hat"]))
        # A "total E" is defined as the sum of the e_j values
        self.gc2_config["e_tot"] = sum(self.gc2_config["ejs"])
        sign_etot = numpy.sign(self.gc2_config["e_tot"])
        b_vec = numpy.zeros(2)
        self.gc2_config["sign"] = []
        for i, c_edges in enumerate(self.cartesian_edges):
            segment_sign = numpy.sign(self.gc2_config["ejs"][i]) * sign_etot
            self.gc2_config["sign"].append(segment_sign)
            if segment_sign < 0:
                # Segment is discordant - reverse the points
                c_edges = numpy.flipud(c_edges)
                self.cartesian_edges[i] = c_edges
                self.cartesian_endpoints[i] = numpy.flipud(
                    self.cartesian_endpoints[i])
            b_vec += (c_edges[-1, :2] - c_edges[0, :2])

        # Get unit vector
        self.gc2_config["b_hat"] = b_vec / numpy.linalg.norm(b_vec)
        if numpy.dot(a_vec, self.gc2_config["b_hat"]) >= 0.0:
            self.p0 = beginning
        else:
            self.p0 = ending
        # To later calculate Ry0 it is necessary to determine the maximum
        # GC2-U coordinate for the fault
        self._get_gc2_coordinates_for_rupture(edge_sets)

    def _get_gc2_coordinates_for_rupture(self, edge_sets):
        """
        Calculates the GC2 coordinates for the nodes of the upper edge of the
        fault
        """

        # Establish GC2 length - for use with Ry0
        rup_gc2t, rup_gc2u = self.get_generalised_coordinates(
            edge_sets[:, 0], edge_sets[:, 1])
        # GC2 length should be the largest positive GC2 value of the edges
        self.gc_length = numpy.max(rup_gc2u)

    def _get_ut_i(self, seg, sx, sy):
        """
        Returns the U and T coordinate for a specific trace segment

        :param seg:
            End points of the segment edge

        :param sx:
            Sites longitudes rendered into coordinate system

        :param sy:
            Sites latitudes rendered into coordinate system
        """
        p0x, p0y, p1x, p1y = seg[0, 0], seg[0, 1], seg[1, 0], seg[1, 1]
        # Unit vector normal to strike
        t_i_vec = [p1y - p0y, -(p1x - p0x), 0.0]
        t_i_hat = t_i_vec / numpy.linalg.norm(t_i_vec)
        # Unit vector along strike
        u_i_vec = [p1x - p0x, p1y - p0y, 0.0]
        u_i_hat = u_i_vec / numpy.linalg.norm(u_i_vec)
        # Vectors from P0 to sites
        rsite = numpy.column_stack([sx - p0x, sy - p0y])
        return numpy.sum(u_i_hat[:-1] * rsite, axis=1),\
            numpy.sum(t_i_hat[:-1] * rsite, axis=1)

    def get_generalised_coordinates(self, lons, lats):
        """
        Transforms the site positions into the generalised coordinate form
        described by Spudich and Chiou (2015) for the multi-rupture and/or
        discordant case

        Spudich, Paul and Chiou, Brian (2015) Strike-parallel and strike-normal
        coordinate system around geometrically complicated rupture traces —
        Use by NGA-West2 and further improvements: U.S. Geological Survey
        Open-File Report 2015-1028
        """
        # If the GC2 configuration has not been setup already - do it!
        if not self.gc2_config:
            self._setup_gc2_framework()
        # Initially the weights are set to zero
        sx, sy = self.proj(lons, lats)
        sum_w_i = numpy.zeros_like(lons)
        sum_w_i_t_i = numpy.zeros_like(lons)
        sum_wi_ui_si = numpy.zeros_like(lons)
        # Find the cumulative length of the fault up until the given segment
        # Essentially calculating s_i
        general_t = numpy.zeros_like(lons)
        general_u = numpy.zeros_like(lons)
        on_segment = numpy.zeros_like(lons, dtype=bool)
        # Loop over the traces
        for j, edges in enumerate(self.cartesian_edges):
            # Loop over segments in trace
            # s_ij_total = 0.0
            for i in range(edges.shape[0] - 1):
                # Get u_i and t_i
                u_i, t_i = self._get_ut_i(edges[i:(i + 2), :], sx, sy)
                # If t_i is 0 and u_i is within the section length then site is
                # directly on the edge - therefore general_t is 0
                w_i = numpy.zeros_like(lons)
                ti0_check = numpy.fabs(t_i) < 1.0E-3  # < 1 m precision
                on_segment_range = numpy.logical_and(
                    u_i >= 0.0,
                    u_i <= self.length_set[j][i])
                # Deal with the case in which t_i is 0 and the site is inside
                # of the segment
                idx0 = numpy.logical_and(ti0_check, on_segment_range)
                # In this null case w_i is ignored - however, null sites on
                # previous segments would not be null sites on this segment,
                # so we update the list of null sites
                on_segment[numpy.logical_or(on_segment, idx0)] = True
                # Also take care of the U case this time using
                # equation 12 of Spudich and Chiou
                s_ij = self.cum_length_set[j][i] + numpy.dot(
                    (edges[0, :2] - self.p0), self.gc2_config["b_hat"])
                general_u[idx0] = u_i[idx0] + s_ij

                # In the first case, ti = 0, u_i is outside of the segment
                # this implements equation 5
                idx1 = numpy.logical_and(ti0_check,
                                         numpy.logical_not(on_segment_range))
                w_i[idx1] = ((1.0 / (u_i[idx1] - self.length_set[j][i])) -
                             (1.0 / u_i[idx1]))

                # In the last case the site is not on the edge (t != 0)
                # implements equation 4
                idx2 = numpy.logical_not(ti0_check)
                w_i[idx2] = ((1. / t_i[idx2]) * (numpy.arctan(
                             (self.length_set[j][i] - u_i[idx2]) / t_i[idx2]) -
                             numpy.arctan(-u_i[idx2] / t_i[idx2])))

                idx = numpy.logical_or(idx1, idx2)
                # Equation 3
                sum_w_i[idx] += w_i[idx]
                # Part of equation 2
                sum_w_i_t_i[idx] += (w_i[idx] * t_i[idx])
                # Part of equation 9
                sum_wi_ui_si[idx] += (w_i[idx] * (u_i[idx] + s_ij))

        # For those sites not on the segment edge itself
        idx_t = numpy.logical_not(on_segment)
        general_t[idx_t] = (1.0 / sum_w_i[idx_t]) * sum_w_i_t_i[idx_t]
        general_u[idx_t] = (1.0 / sum_w_i[idx_t]) * sum_wi_ui_si[idx_t]
        return general_t, general_u

    def get_rx_distance(self, mesh):
        """
        For each point determine the corresponding rx distance using the GC2
        configuration.

        See :meth:`superclass method
        <.base.BaseSurface.get_rx_distance>`
        for spec of input and result values.
        """
        # If the GC2 calculations have already been computed (by invoking Ry0
        # first) and the mesh is identical then class has GC2 attributes
        # already pre-calculated
        if not self.tmp_mesh or (self.tmp_mesh == mesh):
            self.gc2t, self.gc2u = self.get_generalised_coordinates(mesh.lons,
                                                                    mesh.lats)
            # Update mesh
            self.tmp_mesh = deepcopy(mesh)
        # Rx coordinate is taken directly from gc2t
        return self.gc2t

    def get_ry0_distance(self, mesh):
        """
        For each point determine the corresponding Ry0 distance using the GC2
        configuration.

        See :meth:`superclass method
        <.base.BaseSurface.get_ry0_distance>`
        for spec of input and result values.
        """
        # If the GC2 calculations have already been computed (by invoking Ry0
        # first) and the mesh is identical then class has GC2 attributes
        # already pre-calculated
        if not self.tmp_mesh or (self.tmp_mesh == mesh):
            # If that's not the case, or the mesh is different then
            # re-compute GC2 configuration
            self.gc2t, self.gc2u = self.get_generalised_coordinates(mesh.lons,
                                                                    mesh.lats)
            # Update mesh
            self.tmp_mesh = deepcopy(mesh)

        # Default value ry0 (for sites within fault length) is 0.0
        ry0 = numpy.zeros_like(self.gc2u, dtype=float)

        # For sites with negative gc2u (off the initial point of the fault)
        # take the absolute value of gc2u
        neg_gc2u = self.gc2u < 0.0
        ry0[neg_gc2u] = numpy.fabs(self.gc2u[neg_gc2u])

        # Sites off the end of the fault have values shifted by the
        # GC2 length of the fault
        pos_gc2u = self.gc2u >= self.gc_length
        ry0[pos_gc2u] = self.gc2u[pos_gc2u] - self.gc_length
        return ry0
