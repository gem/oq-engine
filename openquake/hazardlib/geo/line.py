# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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
 Module :mod:`openquake.hazardlib.geo.line` defines :class:`Line`.
"""
import copy
import numpy as np
from openquake.hazardlib.geo import geodetic
from openquake.hazardlib.geo import utils
from openquake.hazardlib.geo import Point

TOLERANCE = 0.1


def _update(rtra, rtra_prj, proj, pnt):
    xg, yg = proj(np.array([pnt[0]]), np.array([pnt[1]]), reverse=True)
    rtra.append(np.array([xg[0], yg[0], pnt[2]]))
    rtra_prj.append(pnt)


def _resample(coo, sect_len, orig_extremes):
    # Returns array of resampled trace coordinates
    #
    # :param coo:
    #   A :class:`numpy.ndarray` instance with three columns and n-lines
    #   containing the coordinates of the polyline to be resampled.
    # :param sect_len:
    #   The resampling distance [km]
    # :param orig_extremes:
    #   A boolean. When true the last point in coo is also added.

    N = len(coo)

    # Project the coordinates of the trace and save them in `txy`
    sbb = utils.get_spherical_bounding_box(coo[:, 0], coo[:, 1])
    proj = utils.OrthographicProjection(*sbb)
    txy = coo.copy()
    txy[:, 0], txy[:, 1] = proj(coo[:, 0], coo[:, 1])

    # Compute the total length of the original trace
    # tot_len = sum(utils.get_dist(txy[i], txy[i - 1]) for i in range(1, N))
    inc_len = 0.

    # Initialize the lists with the coordinates of the resampled trace
    rtra_prj = [txy[0]]
    rtra = [coo[0]]

    # Resampling
    idx_vtx = -1
    while True:

        # Computing distances from the reference point
        dis = utils.get_dist(txy, rtra_prj[-1])
        if idx_vtx > 0:
            # Fixing distances for points before the index
            dis[0:idx_vtx] = 100000

        # Index of the point on the trace with a distance just below the
        # sampling distance
        idx = np.where(dis <= sect_len, dis, -np.inf).argmax()

        # If the pick a point that is not the last one on the trace we
        # compute the new sample by interpolation
        if idx < len(dis) - 1:

            pnt = find_t(
                txy[idx + 1, :], txy[idx, :], rtra_prj[-1], sect_len)
            if pnt is None:
                raise ValueError('Did not find the intersection')
            _update(rtra, rtra_prj, proj, pnt)
            inc_len += sect_len

            # Adding more points still on the same segment
            delta = txy[idx + 1] - rtra_prj[-1]
            chk_dst = utils.get_dist(txy[idx + 1], rtra_prj[-1])
            rat = delta / chk_dst
            while chk_dst > sect_len * 0.9999:
                _update(rtra, rtra_prj, proj, rtra_prj[-1] + sect_len * rat)
                inc_len += sect_len
                # This is the distance between the last resampled point
                # and the second vertex of the segment
                chk_dst = utils.get_dist(txy[idx + 1], rtra_prj[-1])
        else:

            if len(rtra) > 1:

                # Azimuth of the resampled edge
                azim_rsmp_edge = geodetic.azimuth(rtra[-2][0], rtra[-2][1],
                                                  rtra[-1][0], rtra[-1][1])
                # Azimuth from the last resampled edge and the last point on
                # the original edge
                azim_orig_edge = geodetic.azimuth(rtra[-1][0], rtra[-1][1],
                                                  coo[-1, 0], coo[-1, 1])
                # Check
                assert np.abs(azim_rsmp_edge - azim_orig_edge) < 30

            # This is the distance between the last sampled point and the last
            # point on the original edge
            dist_from_last = utils.get_dist(rtra_prj[-1], txy[-1])

            # We are processing the last point
            # if tot_len - inc_len > 0.5 * sect_len and not orig_extremes:
            if dist_from_last > sect_len / 2 and not orig_extremes:
                # Adding more points still on the same segment
                delta = txy[-1] - txy[-2]
                chk_dst = utils.get_dist(txy[-1], txy[-2])
                _update(rtra, rtra_prj, proj, rtra_prj[-1] +
                        sect_len * delta / chk_dst)
                inc_len += sect_len
            elif orig_extremes:
                # Adding last point
                rtra.append(coo[-1])
            break

        # Updating index
        idx_vtx = idx + 1

    return np.array(utils.clean_points(rtra))


class Line(object):
    """
    This class represents a geographical line, which is basically
    a sequence of geographical points.

    A line is defined by at least two points.

    :param points:
        The sequence of points defining this line.
    :type points:
        list of :class:`~openquake.hazardlib.geo.point.Point` instances
    """

    @classmethod
    def from_coo(cls, coo):
        """
        Build a Line object for an array of coordinates, assuming they have
        e been cleaned already, i.e. there are no adjacent duplicate points
        """
        self = cls.__new__(cls)
        self.coo = coo
        self.coo.flags.writeable = False  # avoid dirty coding
        return self

    def __init__(self, points):
        points = utils.clean_points(points)  # can remove points!
        self.coo = np.array([[p.x, p.y, p.z] for p in points])
        self.coo.flags.writeable = False  # avoid dirty coding

    @property
    def points(self):
        return [self[i] for i in range(len(self.coo))]

    def __eq__(self, other):
        """
        >>> from openquake.hazardlib.geo.point import Point
        >>> points = [Point(1, 2), Point(3, 4)]; Line(points) == Line(points)
        True
        >>> Line(points) == Line(list(reversed(points)))
        False
        """
        return np.allclose(self.coo, other.coo, atol=1E-6)

    def __ne__(self, other):
        """
        >>> from openquake.hazardlib.geo.point import Point
        >>> Line([Point(1,2), Point(1,3)]) != Line([Point(1,2), Point(1,3)])
        False
        >>> Line([Point(1,2), Point(1,3)]) != Line([Point(1,2), Point(1,4)])
        True
        """
        return not self.__eq__(other)

    def __len__(self):
        return len(self.coo)

    def __getitem__(self, i):
        return Point(*self.coo[i])

    def flip(self):
        """
        Inverts the order of the points composing the line
        """
        self.coo = np.flip(self.coo, axis=0)

    @classmethod
    def from_vectors(cls, lons, lats, deps=None):
        """
        Creates a line from three numpy.ndarray instances containing
        longitude, latitude and depths values
        """
        arrs = lons, lats
        if deps is not None:
            arrs = lons, lats, deps
        return cls([Point(*coo) for coo in zip(*arrs)])

    def on_surface(self):
        """
        Check if this line is defined on the surface (i.e. all points
        are on the surfance, depth=0.0).

        :returns bool:
            True if this line is on the surface, false otherwise.
        """
        return all(point.on_surface() for point in self)

    def horizontal(self):
        """
        Check if this line is horizontal (i.e. all depths of points
        are equal).

        :returns bool:
            True if this line is horizontal, false otherwise.
        """
        return all(p.depth == self.coo[0, 2] for p in self)

    def get_azimuths(self):
        """
        Return the azimuths of all the segments omposing the polyline
        """
        if len(self.coo) == 2:
            return self[0].azimuth(self[1])
        lons = self.coo[:, 0]
        lats = self.coo[:, 1]
        return geodetic.azimuth(lons[:-1], lats[:-1], lons[1:], lats[1:])

    def average_azimuth(self):
        """
        Calculate and return weighted average azimuth of all line's segments
        in decimal degrees.
        Uses formula from
        http://en.wikipedia.org/wiki/Mean_of_circular_quantities
        >>> from openquake.hazardlib.geo.point import Point as P
        >>> '%.1f' % Line([P(0, 0), P(1e-5, 1e-5)]).average_azimuth()
        '45.0'
        >>> '%.1f' % Line([P(0, 0), P(0, 1e-5), P(1e-5, 1e-5)]).average_azimuth()
        '45.0'
        >>> line = Line([P(0, 0), P(-2e-5, 0), P(-2e-5, 1.154e-5)])
        >>> '%.1f' % line.average_azimuth()
        '300.0'
        """
        azimuths = self.get_azimuths()
        lons = self.coo[:, 0]
        lats = self.coo[:, 1]
        distances = geodetic.geodetic_distance(lons[:-1], lats[:-1],
                                               lons[1:], lats[1:])
        return get_average_azimuth(azimuths, distances)

    def resample_old(self, section_length):
        """
        Resample this line into sections.  The first point in the resampled
        line corresponds to the first point in the original line.  Starting
        from the first point in the original line, a line segment is defined as
        the line connecting the last point in the resampled line and the next
        point in the original line.  The line segment is then split into
        sections of length equal to ``section_length``. The resampled line is
        obtained by concatenating all sections.  The number of sections in a
        line segment is calculated as follows: ``round(segment_length /
        section_length)``.  Note that the resulting line has a length that is
        an exact multiple of ``section_length``, therefore its length is in
        general smaller or greater (depending on the rounding) than the length
        of the original line.  For a straight line, the difference between the
        resulting length and the original length is at maximum half of the
        ``section_length``.  For a curved line, the difference may be larger,
        because of corners getting cut.

        :param section_length:
            The length of the section, in km.
        :type section_length:
            float
        :returns:
            A new line resampled into sections based on the given length.
        :rtype:
            An instance of :class:`Line`
        """
        resampled_points = []
        # 1. Resample the first section. 2. Loop over the remaining points
        # in the line and resample the remaining sections.
        # 3. Extend the list with the resampled points, except the first one
        # (because it's already contained in the previous set of
        # resampled points).
        resampled_points.extend(
            self[0].equally_spaced_points(self[1], section_length))

        # Skip the first point, it's already resampled
        for i in range(2, len(self)):
            points = resampled_points[-1].equally_spaced_points(
                self[i], section_length)
            resampled_points.extend(points[1:])

        return Line(resampled_points)

    def resample(self, sect_len: float, orig_extremes=False):
        """
        Resample this line into sections.  The first point in the resampled
        line corresponds to the first point in the original line.  Starting
        from the first point in the original line, a line segment is defined as
        the line connecting the last point in the resampled line and the next
        point in the original line.


        :param float sect_len:
            The length of the section, in km.
        :param bool original_extremes:
            A boolean controlling the way in which the last point is added.
            When true the first and last point match the original extremes.
            When false the last point is at a `sect_len` distance from the
            previous one, before or after the last point.
        :returns:
            A new line resampled into sections based on the given length.
        """
        return Line.from_coo(_resample(self.coo, sect_len, orig_extremes))

    def get_lengths(self) -> np.ndarray:
        """
        Calculate a numpy.ndarray instance with the length
        of the segments composing the polyline.

        :returns:
            Segments length in km.
        """
        lengths = []
        for i, point in enumerate(self):
            if i != 0:
                lengths.append(point.distance(self[i - 1]))
        return np.array(lengths)

    def get_length(self) -> float:
        """
        Calculate the length of the line as a sum of lengths of all its
        segments.

        :returns:
            Total length in km.
        """
        return np.sum(self.get_lengths())

    def keep_corners(self, delta):
        """
        Removes the points where the change in direction is lower than a
        tolerance value.

        :param delta:
            An angle in decimal degrees
        """
        coo = self.coo
        # Compute the azimuth of all the segments
        azim = geodetic.azimuth(coo[:-1, 0], coo[:-1, 1],
                                coo[1:, 0], coo[1:, 1])
        pidx = set([0, coo.shape[0] - 1])
        idx = np.nonzero(np.abs(np.diff(azim)) > delta)[0]
        pidx = sorted(list(pidx.union(set(idx + 1))))
        self.coo = coo[pidx]

    def resample_to_num_points(self, num_points):
        """
        Resample the line to a specified number of points.

        :param num_points:
            Integer number of points the resulting line should have.
        :returns:
            A new line with that many points as requested.
        """
        assert len(self) > 1, "can not resample the line of one point"
        section_length = self.get_length() / (num_points - 1)
        resampled_points = [self[0]]
        segment = 0
        acc_length = 0
        last_segment_length = 0
        points = self.points
        for i in range(num_points - 1):
            tot_length = (i + 1) * section_length
            while tot_length > acc_length and segment < len(points) - 1:
                last_segment_length = points[segment].distance(
                    points[segment + 1])
                acc_length += last_segment_length
                segment += 1
            p1, p2 = points[segment - 1:segment + 1]
            offset = tot_length - (acc_length - last_segment_length)
            if offset < 1e-5:
                # forward geodetic transformations for very small distances
                # are very inefficient (and also unneeded). if target point
                # is just 1 cm away from original (non-resampled) line vertex,
                # don't even bother doing geodetic calculations.
                resampled = p1
            else:
                resampled = p1.equally_spaced_points(p2, offset)[1]
            resampled_points.append(resampled)

        return Line(resampled_points)

    def get_tu(self, mesh):
        """
        Computes the U and T coordinates of the GC2 method for a mesh of
        points.

        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh`
        """

        # Sites
        mlo = mesh.lons
        mla = mesh.lats

        # Projection
        lons = list(mlo.flatten()) + list(self.coo[:, 0])
        lats = list(mla.flatten()) + list(self.coo[:, 1])
        west, east, north, south = utils.get_spherical_bounding_box(lons, lats)
        proj = utils.OrthographicProjection(west, east, north, south)

        # Projected coordinates for the trace
        tcoo = self.coo[:, 0], self.coo[:, 1]
        txy = np.zeros_like(self.coo)
        txy[:, 0], txy[:, 1] = proj(*tcoo)

        # Projected coordinates for the sites
        sxy = np.zeros((len(mla), 2))
        sxy[:, 0], sxy[:, 1] = proj(mlo, mla)

        # Compute u hat and t hat for each segment. tmp has shape
        # (num_segments x 3)
        slen, uhat, that = self.get_tu_hat()

        # Lengths of the segments
        segments_len = slen

        # Get local coordinates for the sites
        ui, ti = self.get_ui_ti(mesh, uhat, that)

        # Compute the weights
        weights, iot = get_ti_weights(ui, ti, segments_len)

        # Now compute T and U
        t_upp, u_upp = get_tu(ui, ti, segments_len, weights)
        t_upp[iot] = 0.0
        return t_upp, u_upp, weights

    def get_ui_ti(self, mesh, uhat, that):
        """
        Compute the t and u coordinates. ti and ui have shape
        (num_segments x num_sites).
        """

        # Creating the projection
        if not hasattr(self, 'proj'):
            oprj = utils.OrthographicProjection
            proj = oprj.from_lons_lats(self.coo[:, 0], self.coo[:, 1])
            self.proj = proj
        proj = self.proj

        # Sites projected coordinates
        sxy = np.zeros((len(mesh.lons), 2))
        sxy[:, 0], sxy[:, 1] = proj(mesh.lons, mesh.lats)

        # Polyline projected coordinates
        txy = np.zeros_like(self.coo)
        txy[:, 0], txy[:, 1] = proj(self.coo[:, 0], self.coo[:, 1])

        # Initializing ti and ui coordinates
        ui = np.zeros((txy.shape[0] - 1, sxy.shape[0]))
        ti = np.zeros((txy.shape[0] - 1, sxy.shape[0]))

        # For each section
        for i in range(ui.shape[0]):
            tmp = copy.copy(sxy)
            tmp[:, 0] -= txy[i, 0]
            tmp[:, 1] -= txy[i, 1]
            ui[i, :] = np.dot(tmp, uhat[i, 0:2])
            ti[i, :] = np.dot(tmp, that[i, 0:2])
        return ui, ti

    def get_tu_hat(self):
        """
        Return the unit vectors defining the local origin for each segment of
        the trace.

        :param sx:
            The vector with the x coordinates of the trace
        :param sy:
            The vector with the y coordinates of the trace
        :returns:
            Two arrays of size n x 3 (when n is the number of segments
            composing the trace
        """

        # Creating the projection
        if not hasattr(self, 'proj'):
            oprj = utils.OrthographicProjection
            proj = oprj.from_lons_lats(self.coo[:, 0], self.coo[:, 1])
            self.proj = proj

        # Projected coordinates
        sx, sy = self.proj(self.coo[:, 0], self.coo[:, 1])

        slen = ((sx[1:] - sx[:-1])**2 + (sy[1:] - sy[:-1])**2)**0.5
        sg = np.zeros((len(sx) - 1, 3))
        sg[:, 0] = sx[1:] - sx[:-1]
        sg[:, 1] = sy[1:] - sy[:-1]
        uhat = get_versor(sg)
        that = get_versor(np.cross(sg, np.array([0, 0, 1])))
        return slen, uhat, that


def get_average_azimuth(azimuths, distances) -> float:
    """
    Computes the average azimuth.

    :param azimuths:
        A :class:`numpy.ndarray` instance
    :param distances:
        A :class:`numpy.ndarray` instance
    :return:
        A float with the mean azimuth in decimal degrees
    """
    azimuths = np.radians(azimuths)
    # convert polar coordinates to Cartesian ones and calculate
    # the average coordinate of each component
    avg_x = np.mean(distances * np.sin(azimuths))
    avg_y = np.mean(distances * np.cos(azimuths))
    # find the mean azimuth from that mean vector
    azimuth = np.degrees(np.arctan2(avg_x, avg_y))
    if azimuth < 0:
        azimuth += 360
    return azimuth


def get_tu(ui, ti, sl, weights):
    """
    Compute the T and U quantitities.

    :param ui:
        A :class:`numpy.ndarray` instance of cardinality (num segments x num
        sites)
    :param ti:
        A :class:`numpy.ndarray` instance of cardinality (num segments x num
        sites)
    :param sl:
        A :class:`numpy.ndarray` instance with the segments' length
    :param weights:
        A :class:`numpy.ndarray` instance of cardinality (num segments x num
        sites)
    """
    assert ui.shape == ti.shape == weights.shape

    # Sum of weights - This has shape equal to the number of sites
    weight_sum = np.sum(weights, axis=0)

    # Compute T
    t_upp = ti * weights
    t_upp = np.divide(t_upp, weight_sum.T).T
    t_upp = np.sum(t_upp, axis=1)

    # Compute U
    u_upp = ui[0] * weights[0]
    for i in range(1, len(sl)):
        delta = np.sum(sl[:i])
        u_upp += ((ui[i] + delta) * weights[i])
    u_upp = np.divide(u_upp, weight_sum.T).T
    return t_upp, u_upp


def get_ti_weights(ui, ti, segments_len):
    """
    Compute the weights
    """
    weights = np.zeros_like(ui)
    terma = np.zeros_like(ui)
    term1 = np.zeros_like(ui)
    term2 = np.zeros_like(ui)
    idx_on_trace = np.zeros_like(ui[0, :], dtype=bool)

    for i in range(ti.shape[0]):

        # More general case
        cond0 = np.abs(ti[i, :]) >= TOLERANCE
        if len(cond0):
            terma[i, cond0] = segments_len[i] - ui[i, cond0]
            term1[i, cond0] = np.arctan(terma[i, cond0] / ti[i, cond0])
            term2[i, cond0] = np.arctan(-ui[i, cond0] / ti[i, cond0])
            weights[i, cond0] = ((term1[i, cond0] - term2[i, cond0]) /
                                 ti[i, cond0])

        # Case for sites on the extension of one segment
        cond1 = np.abs(ti[i, :]) < TOLERANCE
        cond2 = np.logical_or(ui[i, :] < (0. - TOLERANCE),
                              ui[i, :] > (segments_len[i] + TOLERANCE))
        iii = np.logical_and(cond1, cond2)
        if len(iii):
            weights[i, iii] = (1. / (ui[i, iii] - segments_len[i])
                               - 1. / ui[i, iii])

        # Case for sites on one segment
        cond3 = np.logical_and(ui[i, :] >= (0. - TOLERANCE),
                               ui[i, :] <= (segments_len[i] + TOLERANCE))
        jjj = np.logical_and(cond1, cond3)
        weights[i, jjj] = 1 / (-0.01 - segments_len[i]) + 1 / 0.01
        idx_on_trace[jjj] = 1.0

    return weights, idx_on_trace


def get_versor(arr):
    """
    Returns the versor (i.e. a unit vector) of a vector
    """
    return np.divide(arr.T, np.linalg.norm(arr, axis=1)).T


def find_t(pnt0, pnt1, ref_pnt, distance):
    """
    Find the point on the segment within `pnt0` and `pnt1` at `distance` from
    `ref_pnt`. See https://tinyurl.com/meyt4ft3

    :param pnt0:
        A 1D :class:`numpy.ndarray` instance of length 3
    :param pnt1:
        A 1D :class:`numpy.ndarray` instance of length 3
    :param ref_pnt:
        A 1D :class:`numpy.ndarray` instance of length 3
    :param distance:
        A float with the distance in km from `ref_pnt` to the point on the
        segment.
    :returns:
        A 1D :class:`numpy.ndarray` instance of length 3
    """

    x1 = pnt0[0]
    y1 = pnt0[1]
    z1 = pnt0[2]

    x2 = pnt1[0]
    y2 = pnt1[1]
    z2 = pnt1[2]

    x3 = ref_pnt[0]
    y3 = ref_pnt[1]
    z3 = ref_pnt[2]

    r = distance

    pa = (x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2
    pb = 2 * ((x2 - x1) * (x1 - x3) + (y2 - y1) *
              (y1 - y3) + (z2 - z1) * (z1 - z3))
    pc = (x3**2 + y3**2 + z3**2 + x1**2 + y1**2 + z1**2 -
          2 * (x3 * x1 + y3 * y1 + z3 * z1) - r**2)

    chk = pb * pb - 4 * pa * pc

    # In this case the line is not intersecting the sphere
    if chk < 0:
        return None

    # Computing the points of intersection
    pu = (-pb + (pb**2 - 4 * pa * pc)**0.5) / (2 * pa)
    x = x1 + pu * (x2 - x1)
    y = y1 + pu * (y2 - y1)
    z = z1 + pu * (z2 - z1)

    if (x >= np.min([x1, x2]) and x <= np.max([x1, x2]) and
            y >= np.min([y1, y2]) and y <= np.max([y1, y2]) and
            z >= np.min([z1, z2]) and z <= np.max([z1, z2])):
        out = [x, y, z]
    else:
        pu = (-pb - (pb**2 - 4 * pa * pc)**0.5) / (2 * pa)
        x = x1 + pu * (x2 - x1)
        y = y1 + pu * (y2 - y1)
        z = z1 + pu * (z2 - z1)
        out = [x, y, z]

    return np.array(out)
