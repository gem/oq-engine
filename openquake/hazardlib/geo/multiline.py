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
from openquake.baselib.performance import compile
from openquake.hazardlib.geo import utils
from openquake.hazardlib.geo.line import get_tuws, get_tuw
from openquake.hazardlib.geo.geodetic import fast_distance, fast_azimuth


def get_endpoints(lines):
    """
    :returns a mesh of shape 2L
    """
    lons = np.array([ln.coo[[0, -1], 0] for ln in lines])  # shape (L, 2)
    lats = np.array([ln.coo[[0, -1], 1] for ln in lines])  # shape (L, 2)
    return lons.flatten(), lats.flatten()


@compile('(f8,f8,f8[:],f8[:],f8)')
def get_origin(lam0, phi0, lons, lats, avg_strike):
    """
    Compute the origin necessary to calculate the coordinate shift

    :returns:
        The longitude and latitude coordinates of the origin and an array with
        the indexes used to sort the lines according to the origin
    """
    # Project the endpoints
    px, py = utils.project_direct(lam0, phi0, lons, lats)

    # Find the index of the eastmost (or westmost) point depending on the
    # prevalent direction of the strike
    DELTA = 0.1
    strike_to_east = (avg_strike > 0) & (avg_strike <= 180)
    if strike_to_east or abs(avg_strike) < DELTA:
        idx = np.argmin(px)
    else:
        idx = np.argmax(px)

    # Find for each 'line' the endpoint closest to the origin
    eps = np.zeros(len(lons) // 2)
    for i, j in enumerate(range(0, len(px), 2)):
        eps[i] = min([px[j], px[j + 1]])

    # Find the indexes needed to sort the segments according to the prevalent
    # direction of the strike
    sort_idxs = np.argsort(eps)
    if not (strike_to_east or abs(avg_strike) < DELTA):
        sort_idxs = np.flipud(sort_idxs)

    # Set the origin to be used later for the calculation of the
    # coordinate shift
    x = np.array([px[idx]])
    y = np.array([py[idx]])
    olon, olat = utils.project_reverse(lam0, phi0, x, y)

    return olon[0], olat[0], sort_idxs


@compile('(f8[:],f8[:],f8,f8,f8[:,:],f8[:,:])')
def _flipped_soidx_shift(llenghts, azimuths, lam0, phi0, lons, lats):

    # Find general azimuth trend
    ave = utils.angular_mean_weighted(azimuths, llenghts) % 360

    # Find the sections whose azimuth direction is not consistent with the
    # average one
    flipped = np.zeros((len(azimuths)), dtype=np.bool_)
    if (ave >= 90) & (ave <= 270):
        # This is the case where the average azimuth in the second or third
        # quadrant
        idx = (azimuths >= (ave - 90) % 360) & (azimuths < (ave + 90) % 360)
    else:
        # In this case the average azimuth points toward the northern emisphere
        idx = (azimuths >= (ave - 90) % 360) | (azimuths < (ave + 90) % 360)

    delta = np.abs(azimuths - ave)
    scale = np.abs(np.cos(np.radians(delta)))
    ratio = np.sum(llenghts[idx] * scale[idx]) / np.sum(llenghts * scale)

    strike_to_east = ratio > 0.5
    if strike_to_east:
        flipped[~idx] = True
    else:
        flipped[idx] = True

    # Compute the average azimuth
    for i in np.nonzero(flipped)[0]:
        azimuths[i] = (azimuths[i] + 180) % 360  # opposite azimuth
    avg_azim = utils.angular_mean_weighted(azimuths, llenghts) % 360
    olon, olat, soidx = get_origin(
        lam0, phi0, lons.flatten(), lats.flatten(), avg_azim)

    # if the line is flipped take the last point instead of the first
    olons = np.array([lons[idx, int(flipped[idx])] for idx in soidx])
    olats = np.array([lats[idx, int(flipped[idx])] for idx in soidx])
    
    # Distances and azimuths between the origin of the multiline and the
    # first endpoint
    distances = fast_distance(olon, olat, olons, olats)
    azimuths = fast_azimuth(olon, olat, olons, olats)
    
    # Calculate the shift along the average strike direction
    shift = np.cos(np.radians(avg_azim - azimuths)) * distances
    
    return flipped, soidx, shift.astype(np.float32)


class MultiLine(object):
    """
    A collection of polylines with associated methods and attributes. For the
    most part, these are used to compute distances according to the GC2
    method.
    """
    def __init__(self, lines, u_max=None, ry0=False):
        self.lines = lines
        self.u_max = u_max
        llenghts = np.array([ln.length for ln in lines])
        azimuths = np.array([line.azimuth for line in lines])
        lons = np.array([ln.coo[[0, -1], 0] for ln in lines])
        lats = np.array([ln.coo[[0, -1], 1] for ln in lines])
        proj = utils.OrthographicProjection.from_lons_lats(lons, lats)
        self.flipped, self.soidx, self.shift = _flipped_soidx_shift(
            llenghts, azimuths, proj.lam0, proj.phi0, lons, lats)
        if ry0:
            self.set_u_max(lons.flatten(), lats.flatten())

    # used in event based too
    def get_tu(self, lons, lats):
        """
        Given a mesh, computes the T and U coordinates for the multiline
        """
        return get_tu(self.shift, self.gen_tuws(lons, lats), len(lons))

    def __str__(self):
        return ';'.join(str(ln) for ln in self.lines)

    def set_u_max(self, lons, lats):
        """
        If not already computed, compute .u_max, set it and return it.
        """
        if self.u_max is None:
            lons, lats = get_endpoints(self.lines)
            t, u = get_tu(self.shift, self.gen_tuws(lons, lats))
            self.u_max = np.abs(u).max()
        assert self.u_max > 0
        return self.u_max

    def gen_tuws(self, lons, lats):
        """
        :returns: L arrays of shape (N, 2) or a single array (L, N, 2)
        """
        nsegs = [len(ln) - 1 for ln in self.lines]  # segments per line
        if len(set(nsegs)) == 1:
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
                lam0s[i] = line.proj.lam0
                phi0s[i] = line.proj.phi0
                slens[i], uhat, that = line.tu_hat
                if self.flipped[idx]:
                    coos[i] = np.flipud(line.coo[:, 0:2])
                    uhats[i] = -uhat
                    thats[i] = -that
                else:
                    coos[i] = line.coo[:, 0:2]
                    uhats[i] = uhat
                    thats[i] = that
            out = get_tuws(lam0s, phi0s, coos, slens, uhats, thats,
                           lons, lats)
        else:
            # slow lane
            out = []
            for idx in self.soidx:
                line = self.lines[idx]
                slen, uhat, that = line.tu_hat
                if self.flipped[idx]:
                    coo = np.flipud(line.coo[:, 0:2])
                    uhat = -uhat
                    that = -that
                else:
                    coo = line.coo[:, :2]
                tuw = get_tuw(line.proj.lam0, line.proj.phi0, coo,
                              slen, uhat, that,  lons, lats)
                out.append(tuw)
        return out

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


# called by contexts.py
def get_tu(shift, tuws):
    """
    :param shift: multiline shift array of float32
    :param tuws: list of float32 arrays of shape (N, 3)
    :param N: number of sites
    """
    # `shift` has shape L and `tuws` shape (L, N, 3)
    N = len(tuws[0])
    ts = np.zeros(N, np.float32)
    us = np.zeros(N, np.float32)
    ws = np.zeros(N, np.float32)
    for i, tuw in enumerate(tuws):
        t, u, w = tuw[:, 0], tuw[:, 1], tuw[:, 2]
        ts += t * w
        us += (u + shift[i]) * w
        ws += w
    return ts / ws, us / ws
