# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
import numpy as np
from openquake.baselib.general import cached_property
from openquake.baselib.performance import compile
from openquake.hazardlib.geo import geodetic, utils, Point

TOLERANCE = 0.1
SMALL = 1e-2


def _update(rtra, rtra_prj, proj, pnt):
    xg, yg = proj(np.array([pnt[0]]), np.array([pnt[1]]), reverse=True)
    rtra.append(np.array([xg[0], yg[0], pnt[2]]))
    rtra_prj.append(pnt)


def _resample(line, sect_len, orig_extremes):
    # Returns array of resampled trace coordinates
    #
    # :param coo:
    #   A :class:`numpy.ndarray` instance with three columns and n-lines
    #   containing the coordinates of the polyline to be resampled.
    # :param sect_len:
    #   The resampling distance [km]
    # :param orig_extremes:
    #   A boolean. When true the last point in coo is also added.

    # Project the coordinates of the trace and save them in `txy`
    txy = line.proj(line.coo[:, 0], line.coo[:, 1], line.coo[:, 2]).T

    # Compute the total length of the original trace
    # tot_len = sum(utils.get_dist(txy[i], txy[i - 1]) for i in range(1, N))
    inc_len = 0.

    # Initialize the lists with the coordinates of the resampled trace
    rtra_prj = [txy[0]]
    rtra = [line.coo[0]]

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

            pnt = find_t(txy[idx + 1, :], txy[idx, :], rtra_prj[-1], sect_len)
            if np.isnan(pnt).any():
                raise ValueError('Did not find the intersection')
            _update(rtra, rtra_prj, line.proj, pnt)
            inc_len += sect_len

            # Adding more points still on the same segment
            delta = txy[idx + 1] - rtra_prj[-1]
            chk_dst = utils.get_dist(txy[idx + 1], rtra_prj[-1])
            rat = delta / chk_dst
            while chk_dst > sect_len * 0.9999:
                _update(rtra, rtra_prj, line.proj,
                        rtra_prj[-1] + sect_len * rat)
                inc_len += sect_len
                # This is the distance between the last resampled point
                # and the second vertex of the segment
                chk_dst = utils.get_dist(txy[idx + 1], rtra_prj[-1])
        else:

            same_dir = True
            if len(rtra) > 1:
                same_dir = _get_same_dir(rtra, line.coo)

            # This is the distance between the last sampled point and the last
            # point on the original edge
            dist_from_last = utils.get_dist(rtra_prj[-1], txy[-1])

            # We are processing the last point
            # if tot_len - inc_len > 0.5 * sect_len and not orig_extremes:
            if ((dist_from_last > sect_len / 2 and not orig_extremes and
                    same_dir) or
                (dist_from_last < sect_len / 2 and not orig_extremes and
                    not same_dir)):

                # Adding more points still on the same segment
                delta = txy[-1] - txy[-2]
                chk_dst = utils.get_dist(txy[-1], txy[-2])
                _update(rtra, rtra_prj, line.proj, rtra_prj[-1] +
                        sect_len * delta / chk_dst)
                inc_len += sect_len

            elif orig_extremes:
                # Adding last point
                rtra.append(line.coo[-1])
            break

        # Updating index
        idx_vtx = idx + 1

    return np.array(utils.clean_points(rtra))


def _get_same_dir(rtra, coo):

    # If the line is vertical
    if (np.abs(rtra[-2][0] - rtra[-1][0]) < SMALL and
            np.abs(rtra[-2][1] - rtra[-1][1]) < SMALL):
        same_dir = True
        if coo[-1, 2] < rtra[-1][2]:
            same_dir = False
        return same_dir

    # Azimuth of the resampled edge
    azim_rsmp_edge = geodetic.azimuth(rtra[-2][0], rtra[-2][1],
                                      rtra[-1][0], rtra[-1][1])
    # Azimuth from the last resampled edge and the last point on
    # the original edge
    azim_orig_edge = geodetic.azimuth(rtra[-1][0], rtra[-1][1],
                                      coo[-1, 0], coo[-1, 1])
    # Check
    same_dir = np.abs(azim_rsmp_edge - azim_orig_edge) < 30

    return same_dir


@compile('(f8[:,:],f8[:,:],f8[:],f8[:,:])')
def line_get_tu(ui, ti, sl, weights):
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
    # Sum of weights - This has shape equal to the number of sites
    weight_sum = weights.sum(axis=0)

    # Compute T
    t_upp = (ti * weights / weight_sum.T).sum(axis=0)

    # Compute U
    u_upp = ui[0] * weights[0]
    for i in range(1, len(sl)):
        delta = np.sum(sl[:i])
        u_upp += (ui[i] + delta) * weights[i]
    u_upp = (u_upp / weight_sum.T).T
    return t_upp, u_upp


@compile('(f8,f8,f8[:,:],f8[:],f8[:],f8[:,:],f8[:,:])')
def get_ui_ti(lam0, phi0, coo, lons, lats, uhat, that):
    """
    Compute the t and u coordinates. ti and ui have shape
    (num_segments x num_sites).
    """
    N = len(lons)
    L = len(coo)

    # Sites projected coordinates
    sx, sy = utils.project_direct(lam0, phi0, lons, lats)

    # Polyline projected coordinates
    tx, ty = utils.project_direct(lam0, phi0, coo[:, 0], coo[:, 1])

    # Initializing ti and ui coordinates
    ui = np.zeros((L - 1, N))
    ti = np.zeros((L - 1, N))

    # For each segment
    for i in range(L-1):
        dx = sx - tx[i]
        dy = sy - ty[i]
        ui[i] = dx * uhat[i, 0] + dy * uhat[i, 1]
        ti[i] = dx * that[i, 0] + dy * that[i, 1]
    return ui, ti


# has effect on case_65 with multifaultsources and rx0 distance
# affects the performance of ~/oq-risk-tests/test/disaggregation/NZ
@compile('(f8[:,:],f8[:,:],f8[:])')
def get_ti_weights(ui, ti, segments_len):
    """
    :returns: (weights, idx_on_trace)
    """
    S1, S2 = ui.shape
    weights = np.zeros_like(ui)
    terma = np.zeros_like(ui)
    term1 = np.zeros_like(ui)
    term2 = np.zeros_like(ui)
    idx_on_trace = np.zeros(S2, dtype=np.bool_)
    for i in range(S1):
        ti_ = ti[i]
        ui_ = ui[i]
        terma_ = terma[i]
        term1_ = term1[i]
        term2_ = term2[i]
        ws = weights[i]
        seglen = segments_len[i]

        # More general case
        cond0 = np.abs(ti_) >= TOLERANCE
        if cond0.any():
            terma_[cond0] = seglen - ui_[cond0]
            term1_[cond0] = np.arctan(terma_[cond0] / ti_[cond0])
            term2_[cond0] = np.arctan(-ui_[cond0] / ti_[cond0])
            ws[cond0] = (term1_[cond0] - term2_[cond0]) / ti_[cond0]

        # Case for sites on the extension of one segment
        cond1 = np.abs(ti_) < TOLERANCE
        cond2 = np.logical_or(ui_ < 0. - TOLERANCE, ui_ > seglen + TOLERANCE)
        iii = np.logical_and(cond1, cond2)
        if len(iii):
            ws[iii] = 1. / (ui_[iii] - seglen) - 1. / ui_[iii]

        # Case for sites on one segment
        cond3 = np.logical_and(ui_ >= - TOLERANCE, ui_ <= seglen + TOLERANCE)
        jjj = np.logical_and(cond1, cond3)
        ws[jjj] = 1 / (-0.01 - seglen) + 1 / 0.01
        idx_on_trace[jjj] = 1.0

    return weights, idx_on_trace


@compile('(f8,f8,f8[:,:],f8[:],f8[:,:],f8[:,:],f8[:],f8[:])')
def get_tuw(lam0, phi0, coo, slen, uhat, that, lons, lats):
    """
    :returns: array of float32 of shape (N, 3)
    """
    N = len(lons)
    out = np.empty((N, 3), np.float32)
    ui, ti = get_ui_ti(lam0, phi0, coo, lons, lats, uhat, that)
    weights, iot = get_ti_weights(ui, ti, slen)
    t, u = line_get_tu(ui, ti, slen, weights)
    t[iot] = 0.0
    out[:, 0] = t
    out[:, 1] = u
    out[:, 2] = weights.sum(axis=0)
    return out


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
        self.init(coo)
        return self

    def __init__(self, points):
        points = utils.clean_points(points)  # can remove points!
        self.init(np.array([[p.x, p.y, p.z] for p in points]))

    def init(self, coo):
        self.coo = coo
        self.proj = utils.OrthographicProjection.from_(
            self.coo[:, 0], self.coo[:, 1])
        if len(coo) == 2:  # segment
            p0, p1 = self.points
            self.length = p0.distance(p1)
            self.azimuth = p0.azimuth(p1)
        else:
            self.length = np.sum(self.get_lengths())
            azimuths = self.get_azimuths()
            distances = geodetic.geodetic_distance(
                coo[:-1, 0], coo[:-1, 1], coo[1:, 0], coo[1:, 1])
            self.azimuth = utils.angular_mean(azimuths, distances) % 360

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
        Returns a new line with the points flipped. Here is an example,
        taking advantage of the string representation of Lines in terms
        of geohashes of 5 letters (~2 km of precision):

        >>> line = Line([Point(1, 2), Point(1, 3)])
        >>> print(line)
        s02eq_s089n
        >>> print(line.flip())
        s089n_s02eq
        >>> line.get_azimuths()
        [0.0]
        >>> line.flip().get_azimuths()
        [180.0]
        >>> line = Line([Point(1, 0), Point(2, 0)])
        >>> line.get_azimuths()
        [90.0]
        >>> line.flip().get_azimuths()
        [270.0]
        """
        return self.from_coo(np.flip(self.coo, axis=0))

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
        Return the azimuths of all the segments composing the polyline
        """
        if len(self.coo) == 2:
            return [self[0].azimuth(self[1])]
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
        >>> '%.1f' % Line([P(0, 0), P(0, 1e-5), P(1e-5, 1e-5)]
        ... ).average_azimuth()
        '45.0'
        >>> line = Line([P(0, 0), P(-2e-5, 0), P(-2e-5, 1.154e-5)])
        >>> '%.1f' % line.average_azimuth()
        '300.0'
        """
        return self.azimuth

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
        return Line.from_coo(_resample(self, sect_len, orig_extremes))

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
        return self.length

    def keep_corners(self, delta):
        """
        Removes the points where the change in direction is lower than a
        tolerance value and returns a new line.

        :param delta:
            An angle in decimal degrees
        """
        coo = self.coo
        # Compute the azimuth of all the segments
        azim = geodetic.azimuth(coo[:-1, 0], coo[:-1, 1],
                                coo[1:, 0], coo[1:, 1])
        pidx = {0, coo.shape[0] - 1}
        idx, = np.nonzero(np.abs(np.diff(azim)) > delta)
        pidx = sorted(pidx | set(idx + 1))
        return self.from_coo(coo[pidx])

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

    def get_tuw(self, mesh):
        """
        Computes the U and T coordinates of the GC2 method for a mesh of
        points.

        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh`
        """
        slen, uhat, that = self.sut_hat
        tuw = get_tuw(self.proj.lam0, self.proj.phi0,
                      self.coo, slen, uhat, that,
                      mesh.lons, mesh.lats)
        return tuw[:, 0], tuw[:, 1], tuw[:, 2]

    def get_ui_ti(self, mesh, uhat, that):
        """
        Compute the t and u coordinates. ti and ui have shape
        (num_segments x num_sites).
        """
        return get_ui_ti(self.proj.lam0, self.proj.phi0,
                         self.coo, mesh.lons, mesh.lats, uhat, that)

    @cached_property
    def sut_hat(self):
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
        # Projected coordinates
        sx, sy = self.proj(self.coo[:, 0], self.coo[:, 1])
        slen = ((sx[1:] - sx[:-1])**2 + (sy[1:] - sy[:-1])**2)**0.5
        sg = np.zeros((len(sx) - 1, 3))
        sg[:, 0] = sx[1:] - sx[:-1]
        sg[:, 1] = sy[1:] - sy[:-1]
        uhat = get_versor(sg)
        that = get_versor(np.cross(sg, np.array([0, 0, 1])))
        return slen, uhat, that

    def __str__(self):
        return utils.geohash5(self.coo)


def get_versor(arr):
    """
    Returns the versor (i.e. a unit vector) of a vector
    """
    norm = np.linalg.norm(arr, axis=1)
    assert (norm > 0).all(), norm
    return (arr.T / norm).T


@compile("(f8[:],f8[:],f8[:],f8)")
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
        return np.array([np.nan, np.nan, np.nan])

    # Computing the points of intersection
    pu = (-pb + (pb**2 - 4 * pa * pc)**0.5) / (2 * pa)
    x = x1 + pu * (x2 - x1)
    y = y1 + pu * (y2 - y1)
    z = z1 + pu * (z2 - z1)

    if (x >= min(x1, x2) and x <= max(x1, x2) and
            y >= min(y1, y2) and y <= max(y1, y2) and
            z >= min(z1, z2) and z <= max(z1, z2)):
        out = [x, y, z]
    else:
        pu = (-pb - (pb**2 - 4 * pa * pc)**0.5) / (2 * pa)
        x = x1 + pu * (x2 - x1)
        y = y1 + pu * (y2 - y1)
        z = z1 + pu * (z2 - z1)
        out = [x, y, z]

    return np.array(out)
