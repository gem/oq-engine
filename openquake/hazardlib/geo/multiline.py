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

import copy
import numpy as np
from openquake.baselib.performance import compile
from openquake.hazardlib.geo import utils
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.line import Line, get_average_azimuth
from openquake.hazardlib.geo.geodetic import geodetic_distance, azimuth


def get_endpoints(lines):
    """
    :returns a mesh of shape 2L
    """
    L = len(lines)
    lons = np.zeros(2*L)
    lats = np.zeros(2*L)
    for i, line in enumerate(lines):
        lons[2*i] = line.coo[0, 0]
        lons[2*i + 1] = line.coo[-1, 0]
        lats[2*i] = line.coo[0, 1]
        lats[2*i + 1] = line.coo[-1, 1]
    return Mesh(lons, lats)


class MultiLine(object):
    """
    A collection of polylines with associated methods and attributes. For the
    most part, these are used to compute distances according to the GC2
    method.
    """
    def __init__(self, lines):
        # compute the overall strike and the origin of the multiline
        # get lenghts and average azimuths
        llenghts = np.array([ln.get_length() for ln in lines])
        avgaz = np.array([line.average_azimuth() for line in lines])

        # set strike
        revert, strike_east, avg_azim, self.lines = get_overall_strike(
            lines, llenghts, avgaz)
        ep = get_endpoints(self.lines)
        olon, olat, soidx = get_origin(ep, strike_east, avg_azim)

        # Reorder the lines according to the origin and compute the shift
        lines = [self.lines[i] for i in soidx]
        self.coos = [ln.coo for ln in lines]
        self.shift = get_coordinate_shift(lines, olon, olat, avg_azim)
        self.u_max = np.abs(self.get_uts(ep)[0]).max()

    def get_uts(self, mesh):
        """
        Given a mesh, computes the T and U coordinates for the multiline
        """
        L = len(self.lines)
        N = len(mesh)
        tupps = np.zeros((L, N))
        uupps = np.zeros((L, N))
        weis = np.zeros((L, N))
        for i, coo in enumerate(self.coos):
            tu, uu, we = Line.from_coo(coo).get_tuw(mesh)
            tupps[i] = tu
            uupps[i] = uu
            weis[i] = we.sum(axis=0)
        return _get_uts(self.shift, tupps, uupps, weis)


def get_overall_strike(lines: list, llens: list = None, avgaz: list = None):
    """
    Computes the overall strike direction for the multiline

    :param lines:
        A list of :class:`openquake.hazardlib.geo.line.Line` instances
    """
    # copying the lines to avoid flipping the originals
    lines = [copy.copy(ln) for ln in lines]

    # Get lenghts and average azimuths
    if llens is None:
        llens = np.array([ln.get_length() for ln in lines])
    if avgaz is None:
        avgaz = np.array([line.average_azimuth() for line in lines])

    # Find general azimuth trend
    ave = get_average_azimuth(avgaz, llens)

    # Find the sections whose azimuth direction is not consistent with the
    # average one
    revert = np.zeros((len(avgaz)), dtype=bool)
    if (ave >= 90) & (ave <= 270):
        # This is the case where the average azimuth in the second or third
        # quadrant
        idx = (avgaz >= (ave - 90) % 360) & (avgaz < (ave + 90) % 360)
    else:
        # In this case the average azimuth points toward the northern emisphere
        idx = (avgaz >= (ave - 90) % 360) | (avgaz < (ave + 90) % 360)

    delta = abs(avgaz - ave)
    scale = np.abs(np.cos(np.radians(delta)))
    ratio = np.sum(llens[idx] * scale[idx]) / np.sum(llens * scale)

    strike_to_east = ratio > 0.5
    if strike_to_east:
        revert[np.invert(idx)] = True
    else:
        revert[idx] = True

    # Compute the prevalent azimuth
    avgazims_corr = copy.copy(avgaz)
    for i in np.nonzero(revert)[0]:
        lines[i].flip()
        avgazims_corr[i] = lines[i].average_azimuth()
    avg_azim = get_average_azimuth(avgazims_corr, llens)

    strike_to_east = (avg_azim > 0) & (avg_azim <= 180)

    return revert, strike_to_east, avg_azim, lines


def get_origin(ep, strike_to_east: bool, avg_strike: float):
    """
    Compute the origin necessary to calculate the coordinate shift

    :returns:
        The longitude and latitude coordinates of the origin and an array with
        the indexes used to sort the lines according to the origin
    """

    # Project the endpoints
    proj = utils.OrthographicProjection.from_lons_lats(ep.lons, ep.lats)
    px, py = proj(ep.lons, ep.lats)

    # Find the index of the eastmost (or westmost) point depending on the
    # prevalent direction of the strike
    DELTA = 0.1
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


def get_coordinate_shift(lines: list, olon: float, olat: float,
                         overall_strike: float) -> np.ndarray:
    """
    Computes the coordinate shift for each line in the multiline. This is
    used to compute coordinates in the GC2 system

    :returns:
        A :class:`np.ndarray`instance with cardinality equal to the number of
        sections (i.e. the length of the lines list in input)
    """
    # For each line in the multi line, get the distance along the average
    # strike between the origin of the multiline and the first endnode
    origins = np.array([[lin.coo[0, 0], lin.coo[0, 1]] for lin in lines])

    # Distances and azimuths between the origin of the multiline and the
    # first endpoint
    distances = geodetic_distance(olon, olat, origins[:, 0], origins[:, 1])
    azimuths = azimuth(olon, olat, origins[:, 0], origins[:, 1])

    # Calculate the shift along the average strike direction
    return np.cos(np.radians(overall_strike - azimuths))*distances


@compile('float64[:],float64[:,:],float64[:,:],float64[:,:]')
def _get_uts(shifts, tupps, uupps, weis):
    for i, (shift, tupp, uupp, wei) in enumerate(
            zip(shifts, tupps, uupps, weis)):
        if i == 0:  # initialize
            uut = (uupp + shift) * wei
            tut = tupp * wei
            wet = wei.copy()
        else:  # update the values
            uut += (uupp + shift) * wei
            tut += tupp * wei
            wet += wei

    # Normalize by the sum of weights
    uut /= wet
    tut /= wet

    return uut, tut
