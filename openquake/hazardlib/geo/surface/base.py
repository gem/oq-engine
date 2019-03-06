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
Module :mod:`openquake.hazardlib.geo.surface.base` implements
:class:`BaseSurface` and :class:`BaseSurface`.
"""
import numpy
import math
from openquake.hazardlib.geo import geodetic, utils, Point, Line,\
    RectangularMesh


def _find_turning_points(mesh, tol=1.0):
    """
    Identifies the turning points in a rectangular mesh based on the
    deviation in the azimuth between successive points on the upper edge.
    A turning point is flagged if the change in azimuth change is greater than
    the specified tolerance (in degrees)

    :param mesh:
        Mesh for downsampling as instance of :class:
        openquake.hazardlib.geo.mesh.RectangularMesh

    :param float tol:
        Maximum difference in azimuth (decimal degrees) between successive
        points to identify a turning point

    :returns:
        Column indices of turning points (as numpy array)
    """
    assert isinstance(mesh, RectangularMesh)
    azimuths = geodetic.azimuth(mesh.lons[0, :-1], mesh.lats[0, :-1],
                                mesh.lons[0, 1:], mesh.lats[0, 1:])
    naz = len(azimuths)
    azim = azimuths[0]
    # Retain initial point
    idx = [0]
    for i in range(1, naz):
        if numpy.fabs(azimuths[i] - azim) > tol:
            idx.append(i)
            azim = azimuths[i]
    # Add on last point - if not already in the set
    if idx[-1] != mesh.lons.shape[1] - 1:
        idx.append(mesh.lons.shape[1] - 1)
    return numpy.array(idx)


def downsample_mesh(mesh, tol=1.0):
    """
    Returns a mesh sampled at a lower resolution - if the difference
    in azimuth is larger than the specified tolerance a turn is assumed

    :returns:
        Downsampled mesh as instance of :class:
        openquake.hazardlib.geo.mesh.RectangularMesh
    """
    idx = _find_turning_points(mesh, tol)
    if mesh.depths is not None:
        return RectangularMesh(lons=mesh.lons[:, idx],
                               lats=mesh.lats[:, idx],
                               depths=mesh.depths[:, idx])
    else:
        return RectangularMesh(lons=mesh.lons[:, idx],
                               lats=mesh.lats[:, idx])


def downsample_trace(mesh, tol=1.0):
    """
    Downsamples the upper edge of a fault within a rectangular mesh, retaining
    node points only if changes in direction on the order of tol are found

    :returns:
        Downsampled edge as a numpy array of [long, lat, depth]
    """
    idx = _find_turning_points(mesh, tol)
    if mesh.depths is not None:
        return numpy.column_stack([mesh.lons[0, idx],
                                   mesh.lats[0, idx],
                                   mesh.depths[0, idx]])
    else:
        return numpy.column_stack([mesh.lons[0, idx], mesh.lats[0, idx]])


class BaseSurface:
    """
    Base class for a surface in 3D-space.
    """

    def __init__(self, mesh=None):
        self.mesh = mesh

    def get_min_distance(self, mesh):
        """
        Compute and return the minimum distance from the surface to each point
        of ``mesh``. This distance is sometimes called ``Rrup``.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate
            minimum distance to.
        :returns:
            A numpy array of distances in km.
        """
        return self.mesh.get_min_distance(mesh)

    def get_closest_points(self, mesh):
        """
        For each point from ``mesh`` find a closest point belonging to surface.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to find
            closest points to.
        :returns:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of the same shape as
            ``mesh`` with closest surface's points on respective indices.
        """
        return self.mesh.get_closest_points(mesh)

    def get_joyner_boore_distance(self, mesh):
        """
        Compute and return Joyner-Boore (also known as ``Rjb``) distance
        to each point of ``mesh``.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate
            Joyner-Boore distance to.
        :returns:
            Numpy array of closest distances between the projections of surface
            and each point of the ``mesh`` to the earth surface.
        """
        return self.mesh.get_joyner_boore_distance(mesh)

    def get_ry0_distance(self, mesh):
        """
        Compute the minimum distance between each point of a mesh and the great
        circle arcs perpendicular to the average strike direction of the
        fault trace and passing through the end-points of the trace.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate
            Ry0-distance to.
        :returns:
            Numpy array of distances in km.
        """
        # This computes ry0 by using an average strike direction
        top_edge = self.mesh[0:1]
        mean_strike = self.get_strike()

        dst1 = geodetic.distance_to_arc(top_edge.lons[0, 0],
                                        top_edge.lats[0, 0],
                                        (mean_strike + 90.) % 360,
                                        mesh.lons, mesh.lats)

        dst2 = geodetic.distance_to_arc(top_edge.lons[0, -1],
                                        top_edge.lats[0, -1],
                                        (mean_strike + 90.) % 360,
                                        mesh.lons, mesh.lats)
        # Find the points on the rupture

        # Get the shortest distance from the two lines
        idx = numpy.sign(dst1) == numpy.sign(dst2)
        dst = numpy.zeros_like(dst1)
        dst[idx] = numpy.fmin(numpy.abs(dst1[idx]), numpy.abs(dst2[idx]))

        return dst

    def get_rx_distance(self, mesh):
        """
        Compute distance between each point of mesh and surface's great circle
        arc.

        Distance is measured perpendicular to the rupture strike, from
        the surface projection of the updip edge of the rupture, with
        the down dip direction being positive (this distance is usually
        called ``Rx``).

        In other words, is the horizontal distance to top edge of rupture
        measured perpendicular to the strike. Values on the hanging wall
        are positive, values on the footwall are negative.

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points to calculate
            Rx-distance to.
        :returns:
            Numpy array of distances in km.
        """
        top_edge = self.mesh[0:1]

        dists = []
        if top_edge.lons.shape[1] < 3:

            i = 0
            p1 = Point(
                top_edge.lons[0, i],
                top_edge.lats[0, i],
                top_edge.depths[0, i]
            )
            p2 = Point(
                top_edge.lons[0, i + 1], top_edge.lats[0, i + 1],
                top_edge.depths[0, i + 1]
            )
            azimuth = p1.azimuth(p2)
            dists.append(
                geodetic.distance_to_arc(
                    p1.longitude, p1.latitude, azimuth,
                    mesh.lons, mesh.lats
                )
            )

        else:

            for i in range(top_edge.lons.shape[1] - 1):
                p1 = Point(
                    top_edge.lons[0, i],
                    top_edge.lats[0, i],
                    top_edge.depths[0, i]
                )
                p2 = Point(
                    top_edge.lons[0, i + 1],
                    top_edge.lats[0, i + 1],
                    top_edge.depths[0, i + 1]
                )
                # Swapping
                if i == 0:
                    pt = p1
                    p1 = p2
                    p2 = pt

                # Computing azimuth and distance
                if i == 0 or i == top_edge.lons.shape[1] - 2:
                    azimuth = p1.azimuth(p2)
                    tmp = geodetic.distance_to_semi_arc(p1.longitude,
                                                        p1.latitude,
                                                        azimuth,
                                                        mesh.lons, mesh.lats)
                else:
                    tmp = geodetic.min_distance_to_segment(
                        numpy.array([p1.longitude, p2.longitude]),
                        numpy.array([p1.latitude, p2.latitude]),
                        mesh.lons, mesh.lats)
                # Correcting the sign of the distance
                if i == 0:
                    tmp *= -1
                dists.append(tmp)

        # Computing distances
        dists = numpy.array(dists)
        iii = abs(dists).argmin(axis=0)
        dst = dists[iii, list(range(dists.shape[1]))]

        return dst

    def get_top_edge_depth(self):
        """
        Return minimum depth of surface's top edge.

        :returns:
            Float value, the vertical distance between the earth surface
            and the shallowest point in surface's top edge in km.
        """
        top_edge = self.mesh[0:1]
        if top_edge.depths is None:
            return 0
        else:
            return numpy.min(top_edge.depths)

    def _get_top_edge_centroid(self):
        """
        Return :class:`~openquake.hazardlib.geo.point.Point` representing the
        surface's top edge centroid.
        """
        top_edge = self.mesh[0:1]
        return top_edge.get_middle_point()

    def get_area(self):
        """
        Compute area as the sum of the mesh cells area values.
        """
        mesh = self.mesh
        _, _, _, area = mesh.get_cell_dimensions()

        return numpy.sum(area)

    def get_bounding_box(self):
        """
        Compute surface bounding box from surface mesh representation. That is
        extract longitudes and latitudes of mesh points and calls:
        :meth:`openquake.hazardlib.geo.utils.get_spherical_bounding_box`

        :return:
            A tuple of four items. These items represent western, eastern,
            northern and southern borders of the bounding box respectively.
            Values are floats in decimal degrees.
        """
        mesh = self.mesh
        return utils.get_spherical_bounding_box(mesh.lons, mesh.lats)

    def get_middle_point(self):
        """
        Compute coordinates of surface middle point.

        The actual definition of ``middle point`` depends on the type of
        surface geometry.

        :return:
            instance of :class:`openquake.hazardlib.geo.point.Point`
            representing surface middle point.
        """
        return self.mesh.get_middle_point()

    def get_surface_boundaries(self):
        """
        Returns the boundaries in the same format as a multiplanar
        surface, with two one-element lists of lons and lats
        """
        mesh = self.mesh
        lons = numpy.concatenate((mesh.lons[0, :],
                                  mesh.lons[1:, -1],
                                  mesh.lons[-1, :-1][::-1],
                                  mesh.lons[:-1, 0][::-1]))
        lats = numpy.concatenate((mesh.lats[0, :],
                                  mesh.lats[1:, -1],
                                  mesh.lats[-1, :-1][::-1],
                                  mesh.lats[:-1, 0][::-1]))
        return [lons], [lats]

    def get_resampled_top_edge(self, angle_var=0.1):
        """
        This methods computes a simplified representation of a fault top edge
        by removing the points that are not describing a change of direction,
        provided a certain tolerance angle.

        :param float angle_var:
            Number representing the maximum deviation (in degrees) admitted
            without the creation of a new segment
        :returns:
            A :class:`~openquake.hazardlib.geo.line.Line` representing the
            rupture surface's top edge.
        """
        mesh = self.mesh
        top_edge = [Point(mesh.lons[0][0], mesh.lats[0][0], mesh.depths[0][0])]

        for i in range(len(mesh.triangulate()[1][0]) - 1):
            v1 = numpy.asarray(mesh.triangulate()[1][0][i])
            v2 = numpy.asarray(mesh.triangulate()[1][0][i + 1])
            cosang = numpy.dot(v1, v2)
            sinang = numpy.linalg.norm(numpy.cross(v1, v2))
            angle = math.degrees(numpy.arctan2(sinang, cosang))

            if abs(angle) > angle_var:

                top_edge.append(Point(mesh.lons[0][i + 1],
                                      mesh.lats[0][i + 1],
                                      mesh.depths[0][i + 1]))

        top_edge.append(Point(mesh.lons[0][-1],
                              mesh.lats[0][-1], mesh.depths[0][-1]))
        line_top_edge = Line(top_edge)

        return line_top_edge

    def get_hypo_location(self, mesh_spacing, hypo_loc=None):
        """
        The method determines the location of the hypocentre within the rupture

        :param mesh:
            :class:`~openquake.hazardlib.geo.mesh.Mesh` of points
        :param mesh_spacing:
            The desired distance between two adjacent points in source's
            ruptures' mesh, in km. Mainly this parameter allows to balance
            the trade-off between time needed to compute the distance
            between the rupture surface and a site and the precision of that
            computation.
        :param hypo_loc:
            Hypocentre location as fraction of rupture plane, as a tuple of
            (Along Strike, Down Dip), e.g. a hypocentre located in the centroid
            of the rupture would be input as (0.5, 0.5), whereas a
            hypocentre located in a position 3/4 along the length, and 1/4 of
            the way down dip of the rupture plane would be entered as
            (0.75, 0.25).
        :returns:
            Hypocentre location as instance of
            :class:`~openquake.hazardlib.geo.point.Point`
        """
        mesh = self.mesh
        centroid = mesh.get_middle_point()
        if hypo_loc is None:
            return centroid

        total_len_y = (len(mesh.depths) - 1) * mesh_spacing
        y_distance = hypo_loc[1] * total_len_y
        y_node = int(numpy.round(y_distance / mesh_spacing))
        total_len_x = (len(mesh.lons[y_node]) - 1) * mesh_spacing
        x_distance = hypo_loc[0] * total_len_x
        x_node = int(numpy.round(x_distance / mesh_spacing))
        hypocentre = Point(mesh.lons[y_node][x_node],
                           mesh.lats[y_node][x_node],
                           mesh.depths[y_node][x_node])
        return hypocentre

    def get_azimuth(self, mesh):
        """
        This method computes the azimuth of a set of points in a
        :class:`openquake.hazardlib.geo.mesh` instance. The reference used for
        the calculation of azimuth is the middle point and the strike of the
        rupture. The value of azimuth computed corresponds to the angle
        measured in a clockwise direction from the strike of the rupture.

        :parameter mesh:
            An instance of  :class:`openquake.hazardlib.geo.mesh`
        :return:
            An instance of `numpy.ndarray`
        """
        # Get info about the rupture
        strike = self.get_strike()
        hypocenter = self.get_middle_point()
        # This is the azimuth from the north of each point Vs. the middle of
        # the rupture
        azim = geodetic.azimuth(hypocenter.longitude, hypocenter.latitude,
                                mesh.lons, mesh.lats)
        # Compute the azimuth from the fault strike
        rel_azi = (azim - strike) % 360
        return rel_azi
