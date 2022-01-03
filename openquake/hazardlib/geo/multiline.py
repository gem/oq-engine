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
from openquake.hazardlib.geo import utils
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.line import get_average_azimuth
from openquake.hazardlib.geo.geodetic import geodetic_distance, azimuth


class MultiLine():
    """
    A collection of polylines with associated methods and attributes. For the
    most part, these are used to compute distances according to the GC2
    method.
    """

    def __init__(self, lines):
        self.lines = lines
        self.strike_to_east = None
        self.overall_strike = None
        self.olon = None
        self.olat = None
        self.shift = None

    def get_lengths(self) -> np.ndarray:
        """
        Computes the total lenght for each polyline composing the multiline

        :returns:
            A :class:`numpy.ndarray` instance
        """
        return get_lengths(self.lines)

    def get_average_azimuths(self) -> np.ndarray:
        """
        Computes the average azimuth for each polyline composing the multiline

        :returns:
            A :class:`numpy.ndarray` instance
        """
        return get_average_azimuths(self.lines)

    def set_overall_strike(self):
        """
        Computes the overall strike direction for the multiline and revert the
        lines with strike direction opposite to the prevalent one

        :param lines:
            A list of :class:`openquake.hazardlib.geo.line.Line` instances
        """
        # Get lenghts and average azimuths
        llenghts = self.get_lengths()
        avgaz = self.get_average_azimuths()

        sos = get_overall_strike
        revert, strike_to_east, avg_azim = sos(self.lines, llenghts, avgaz)

        self.strike_to_east = strike_to_east
        self.overall_strike = avg_azim

        return revert

    def _set_origin(self):
        """
        Compute the origin necessary to calculate the coordinate shift and sort
        the information accordingly
        """

        # If missing, set the overall strike direction
        if not hasattr(self, 'strike_to_east') or self.strike_to_east is None:
            _ = self.set_overall_strike()

        # Calculate the origin
        olo, ola, soidx = get_origin(self.lines, self.strike_to_east)
        self.olon = olo
        self.olat = ola

        # Reorder the lines and the shift according to the origin
        self.lines = [self.lines[i] for i in soidx]
        if self.shift is None:
            self.shift = self.shift[soidx]

    def _set_coordinate_shift(self) -> np.ndarray:
        """
        Computes the coordinate shift for each line in the multiline. This is
        used to compute coordinates in the GC2 system
        """

        # If not defined, compute the origin of the multiline
        if not hasattr(self, 'olon') or self.olon is None:
            self._set_origin()

        # Set the shift param
        self.shift = get_coordinate_shift(self.lines, self.olon, self.olat,
                                          self.overall_strike)

    def get_tu(self, mesh: Mesh):
        """
        Given a mesh, computes the T and U coordinates for the multiline
        """

        # Set the coordinate shift
        self._set_coordinate_shift()

        # Processing
        uupps = []
        tupps = []
        weis = []

        for line in self.lines:

            # Compute (or retrieve) the T and U coordinates. T and U have
            # cardinality <number_sites>. The weights have cardinality equal
            # to <number_of_segments> x <number of_sites>
            if not hasattr(self, 'tupp'):
                tupp, uupp, wei = line.get_tu(mesh)
                wei_sum = np.sum(wei, axis=0)
                print(wei_sum)

            # else:
            #     tupp = self.tupp
            #     uupp = self.uupp

            uupps.append(uupp)
            tupps.append(tupp)
            weis.append(wei_sum)

        uut, tut = get_tu(self.shift, tupps, uupps, weis)

        return uut, tut


def get_lengths(lines: list) -> np.ndarray:
    """
    Computes the total lenght for each polyline composing the multiline

    :returns:
        A :class:`numpy.ndarray` instance
    """
    llenghts = []
    for line in lines:
        llenghts.append(line.get_length())
    return np.array(llenghts)


def get_average_azimuths(lines: list) -> np.ndarray:
    """
    Computes the average azimuth for each polyline composing the multiline

    :returns:
        A :class:`numpy.ndarray` instance
    """
    avgazims = []
    for line in lines:
        avgazims.append(line.average_azimuth())
    return np.array(avgazims)


def get_overall_strike(lines: list, llenghts: list = None, avgaz: list = None,
                       ):
    """
    Computes the overall strike direction for the multiline

    :param lines:
        A list of :class:`openquake.hazardlib.geo.line.Line` instances
    """

    # Get lenghts and average azimuths
    if llenghts is None:
        llenghts = get_lengths(lines)
    if avgaz is None:
        avgaz = get_average_azimuths(lines)

    # Find general trend
    tmp = copy.copy(avgaz)
    idx = tmp > 180
    tmp[idx] = tmp[idx] - 180.
    ave = get_average_azimuth(tmp, llenghts)

    # Computing the azimuth direction (i.e. towards east or west)
    revert = np.zeros((len(lines)), dtype=bool)
    if (ave > 90) & (ave < 270):
        idx = (avgaz >= (ave - 90) % 360) & (avgaz < (ave + 90) % 360)
    else:
        idx = (avgaz >= (ave - 90) % 360) | (avgaz < (ave + 90) % 360)
    delta = abs(avgaz - ave)
    scale = np.abs(np.cos(np.radians(delta)))
    ratio = np.sum(llenghts[idx] * scale[idx]) / np.sum(llenghts * scale)

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
    avg_azim = get_average_azimuth(avgazims_corr, llenghts)

    return revert, strike_to_east, avg_azim


def get_origin(lines: list, strike_to_east: bool):
    """
    Compute the origin necessary to calculate the coordinate shift
    """

    # Create the list of endpoints
    endp = []
    for line in lines:
        endp.append([line.coo[0, 0], line.coo[0, 1]])
        endp.append([line.coo[-1, 0], line.coo[-1, 1]])
    endp = np.array(endp)

    # Project the endpoints
    oprj = utils.OrthographicProjection
    proj = oprj.from_lons_lats(endp[:, 0], endp[:, 1])
    px, py = proj(endp[:, 0], endp[:, 1])

    # Find the index of the eastmost (or westmost) point depending on the
    # prevalent direction of the strike
    if strike_to_east:
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
    if not strike_to_east:
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
    """

    # For each line in the multi line, get the distance along the average
    # strike between the origin of the multiline and the first endnode
    origins = np.array([[lin.coo[0, 0], lin.coo[0, 1]] for lin in lines])

    # Distances and azimuths between the origin of the multiline and the
    # first endpoint
    ggdst = geodetic_distance
    ggazi = azimuth
    distances = ggdst(olon, olat, origins[:, 0], origins[:, 1])
    azimuths = ggazi(olon, olat, origins[:, 0], origins[:, 1])

    # Calculate the shift along the average strike direction
    return np.cos(np.radians(overall_strike - azimuths))*distances


def get_tu(shifts, tupps, uupps, weis):
    """
    Given a mesh, computes the T and U coordinates for the multiline
    """

    # Processing
    arg = zip(shifts, tupps, uupps, weis)
    for i, (shift, tupp, uupp, wei_sum) in enumerate(arg):

        # Weights
        # wei_sum = np.sum(wei, axis=0)

        # Update the uupp values
        if i == 0:
            uut = (uupp + shift) * wei_sum
            tut = tupp * wei_sum
            wet = wei_sum
        else:
            uut += (uupp + shift) * wei_sum
            tut += tupp * wei_sum
            wet += wei_sum

    # Normalize by the sum of weights
    uut /= wet
    tut /= wet

    return uut, tut
