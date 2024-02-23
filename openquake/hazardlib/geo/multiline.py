# The Hazard Library
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
Module :mod:`openquake.hazardlib.geo.multiline` defines
:class:`openquake.hazardlib.geo.multiline.Multiline`.
"""

import numpy as np
import pandas as pd
from openquake.hazardlib.geo import utils
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.line import get_tuws, get_tuw
from openquake.hazardlib.geo.geodetic import geodetic_distance, azimuth


def get_endpoints(lines):
    """
    :returns a mesh of shape 2L
    """
    lons = np.concatenate([ln.coo[[0, -1], 0] for ln in lines])  # shape 2L
    lats = np.concatenate([ln.coo[[0, -1], 1] for ln in lines])  # shape 2L
    return lons, lats


def get_flipped(llens, azimuths):
    """
    :returns: a boolean array with the flipped lines
    """
    # Find general azimuth trend
    ave = utils.angular_mean(azimuths, llens) % 360

    # Find the sections whose azimuth direction is not consistent with the
    # average one
    flipped = np.zeros((len(azimuths)), dtype=bool)
    if (ave >= 90) & (ave <= 270):
        # This is the case where the average azimuth in the second or third
        # quadrant
        idx = (azimuths >= (ave - 90) % 360) & (azimuths < (ave + 90) % 360)
    else:
        # In this case the average azimuth points toward the northern emisphere
        idx = (azimuths >= (ave - 90) % 360) | (azimuths < (ave + 90) % 360)

    delta = abs(azimuths - ave)
    scale = np.abs(np.cos(np.radians(delta)))
    ratio = np.sum(llens[idx] * scale[idx]) / np.sum(llens * scale)

    strike_to_east = ratio > 0.5
    if strike_to_east:
        flipped[~idx] = True
    else:
        flipped[idx] = True
    return flipped


def get_avg_azim_flipped(lines):
    # compute the overall strike and the origin of the multiline
    # get lenghts and average azimuths
    llenghts = np.array([ln.length for ln in lines])
    azimuths = np.array([line.azimuth for line in lines])

    # determine the flipped lines
    flipped = get_flipped(llenghts, azimuths)
    
    # Compute the average azimuth
    for i in np.nonzero(flipped)[0]:
        if not hasattr(lines[i], 'flipped'):
            lines[i].flipped = lines[i].flip()
        azimuths[i] = (azimuths[i] + 180) % 360  # opposite azimuth
    avg_azim = utils.angular_mean(azimuths, llenghts) % 360
    return avg_azim, flipped


def MultiLine(lines, u_max=None):
    avg_azim, flipped = get_avg_azim_flipped(lines)
    lons, lats = get_endpoints(lines)
    olon, olat, soidx = get_origin(lons, lats, avg_azim)
    
    # compute the shift with respect to the origins
    origins = np.zeros((len(lines), 2))
    for i, idx in enumerate(soidx):
        flip = -1 if flipped[idx] else 0
        # if the line is flipped take the final point as origin
        origins[i] = lines[idx].coo[flip, 0:2]
    shift = get_coordinate_shift(origins, olon, olat, avg_azim)
    u_max = u_max

    nsegs = [len(ln) - 1 for ln in lines]  # segments per line
    if len(set(nsegs)) == 1:
        # fast lane, when the number of segments is constant
        return MultiLineFast(lines, soidx, flipped, shift, u_max)
    else:
        # slow lane
        return MultiLineSlow(lines, soidx, flipped, shift, u_max)


class MultiLineBase(object):
    """
    A collection of polylines with associated methods and attributes. For the
    most part, these are used to compute distances according to the GC2
    method.
    """
    def __init__(self, lines, soidx, flipped, shift, u_max):
        self.lines = lines
        self.soidx = soidx
        self.flipped = flipped
        self.shift = shift
        self.u_max = u_max

    def gen_tuws(self, lons, lats):
        pass

    def set_u_max(self):
        pass

    # used in event based too
    def get_tu(self, lons, lats):
        """
        Given a mesh, computes the T and U coordinates for the multiline
        """
        return get_tu(self.shift, self.gen_tuws(lons, lats), len(lons))

    def __str__(self):
        return ';'.join(str(ln) for ln in self.lines)


class MultiLineSlow(MultiLineBase):
    def set_u_max(self):
        """
        If not already computed, compute .u_max, set it and return it.
        """
        if self.u_max is None:
            lons, lats = get_endpoints(self.lines)
            N = 2 * len(self.lines)
            t, u = get_tu(self.shift, self.gen_tuws(lons, lats), N)
            self.u_max = np.abs(u).max()
        assert self.u_max > 0
        return self.u_max

    def gen_tuws(self, lons, lats):
        """
        :yields: L arrays of shape (N, 3)
        """
        for idx in self.soidx:
            line = self.lines[idx]
            if self.flipped[idx]:
                line = line.flipped
            slen, uhat, that = line.tu_hat
            yield get_tuw(line.proj.lam0, line.proj.phi0, line.coo[:, :2],
                          slen, uhat, that,  lons, lats)

    def get_tuw_df(self, sites):
        # debug method to be called in genctxs
        sids = []
        ls = []
        ts = []
        us = []
        ws = []
        for li, tuw in enumerate(self.gen_tuws()):
            for s, sid in enumerate(sites.sids):
                sids.append(sid)
                ls.append(li)
                ts.append(tuw[s, 0])
                us.append(tuw[s, 1])
                ws.append(tuw[s, 2])
        dic = dict(sid=sids, li=ls, t=ts, u=us, w=ws)
        return pd.DataFrame(dic)


class MultiLineFast(MultiLineBase):
    def set_u_max(self):
        """
        If not already computed, compute .u_max, set it and return it.
        """
        if self.u_max is None:
            lons, lats = get_endpoints(self.lines)
            N = 2 * len(self.lines)
            t, u = get_tu(self.shift, self.gen_tuws(lons, lats), N)
            self.u_max = np.abs(u).max()
        assert self.u_max > 0
        return self.u_max

    def gen_tuws(self, lons, lats):
        """
        :yields: L arrays of shape (N, 3)
        """
        # fast lane, when the number of segments is constant
        ns = len(self.lines[0]) - 1
        L = len(self.lines)
        lam0s = np.empty(L)
        phi0s = np.empty(L)
        coos = np.empty((L, ns + 1, 2))
        slens = np.empty((L, ns))
        uhats = np.empty((L, ns, 3))
        thats = np.empty((L, ns, 3))
        for i, idx in enumerate(self.soidx):
            line = self.lines[idx]
            if self.flipped[idx]:
                line = line.flipped
            lam0s[i] = line.proj.lam0
            phi0s[i] = line.proj.phi0
            coos[i] = line.coo[:, 0:2]
            slen, uhat, that = line.tu_hat
            slens[i] = slen
            uhats[i] = uhat
            thats[i] = that
        return get_tuws(lam0s, phi0s, coos, slens, uhats, thats,
                        lons, lats)


def get_origin(lons, lats, avg_strike):
    """
    Compute the origin necessary to calculate the coordinate shift

    :returns:
        The longitude and latitude coordinates of the origin and an array with
        the indexes used to sort the lines according to the origin
    """

    # Project the endpoints
    proj = utils.OrthographicProjection.from_lons_lats(lons, lats)
    px, py = proj(lons, lats)

    # Find the index of the eastmost (or westmost) point depending on the
    # prevalent direction of the strike
    DELTA = 0.1
    strike_to_east = (avg_strike > 0) & (avg_strike <= 180)
    if strike_to_east or abs(avg_strike) < DELTA:
        idx = np.argmin(px)
    else:
        idx = np.argmax(px)

    # Find for each 'line' the endpoint closest to the origin
    eps = []
    for i in range(0, len(px), 2):
        eps.append(min([px[i], px[i+1]]))

    # Find the indexes needed to sort the segments according to the prevalent
    # direction of the strike
    sort_idxs = np.argsort(eps)
    if not (strike_to_east or abs(avg_strike) < DELTA):
        sort_idxs = np.flipud(sort_idxs)

    # Set the origin to be used later for the calculation of the
    # coordinate shift
    x = np.array([px[idx]])
    y = np.array([py[idx]])
    olon, olat = proj(x, y, reverse=True)

    return olon[0], olat[0], sort_idxs


def get_coordinate_shift(origins: list, olon: float, olat: float,
                         overall_strike: float) -> np.ndarray:
    """
    Computes the coordinate shift for each line in the multiline. This is
    used to compute coordinates in the GC2 system

    :returns:
        A :class:`np.ndarray`instance with cardinality equal to the number of
        sections (i.e. the length of the lines list in input)
    """
    # Distances and azimuths between the origin of the multiline and the
    # first endpoint
    distances = geodetic_distance(olon, olat, origins[:, 0], origins[:, 1])
    azimuths = azimuth(olon, olat, origins[:, 0], origins[:, 1])

    # Calculate the shift along the average strike direction
    return np.float32(np.cos(np.radians(overall_strike - azimuths)) * distances)


# called by contexts.py
def get_tu(shift, tuws, N):
    """
    :param shift: multiline shift array
    :param tuws: iterator producing arrays of shape (N, 3)
    :param N: number of sites
    """
    # `shift` has shape L and `tuws` shape (L, N, 3)
    ts = np.zeros(N, np.float32)
    us = np.zeros(N, np.float32)
    ws = np.zeros(N, np.float32)
    for i, tuw in enumerate(tuws):
        assert len(tuw) == N, (len(tuw), N)
        t, u, w = tuw[:, 0], tuw[:, 1], tuw[:, 2]
        ts += t * w
        us += (u + shift[i]) * w
        ws += w
    return ts / ws, us / ws
