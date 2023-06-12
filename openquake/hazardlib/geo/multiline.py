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
        self.lines = [copy.copy(ln) for ln in lines]
        self.strike_to_east = None
        self.overall_strike = None
        self.olon = None
        self.olat = None
        self.shift = None
        self.u_max = None
        self.tupps = None
        self.uupps = None
        self.uut = None
        self.tut = None
        self.weis = None

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

        :return:

        """
        # Get lenghts and average azimuths
        llenghts = self.get_lengths()
        avgaz = self.get_average_azimuths()

        gos = get_overall_strike
        revert, strike_east, avg_azim, nl = gos(self.lines, llenghts, avgaz)

        self.strike_to_east = strike_east
        self.overall_strike = avg_azim
        self.lines = nl

        return revert

    def _set_origin(self):
        """
        Compute the origin necessary to calculate the coordinate shift and sort
        the information accordingly
        """

        # If missing, set the overall strike direction
        if self.strike_to_east is None:
            _ = self.set_overall_strike()

        # Calculate the origin
        olo, ola, soidx = get_origin(
            self.lines, self.strike_to_east, self.overall_strike)
        self.olon = olo
        self.olat = ola

        # Reorder the lines and the shift according to the origin
        self.lines = [self.lines[i] for i in soidx]
        if self.shift is not None:
            self.shift = self.shift[soidx]

        return soidx

    def _set_coordinate_shift(self):
        """
        Computes the coordinate shift for each line in the multiline. This is
        used to compute coordinates in the GC2 system
        """
        # If not defined, compute the origin of the multiline
        if self.olon is None:
            _ = self._set_origin()

        # Set the shift param
        self.shift = get_coordinate_shift(self.lines, self.olon, self.olat,
                                          self.overall_strike)

    def set_tu(self, mesh: Mesh = None):
        """
        Computes the T and U coordinates for the multiline. If a mesh is
        given first we compute the required info.
        """
        if self.shift is None:
            self._set_coordinate_shift()

        if self.tupps is None:
            assert mesh is not None
            tupps, uupps, weis = get_tus(self.lines, mesh)
        else:
            tupps = self.tupps
            uupps = self.uupps
            weis = self.weis

        uut, tut = get_tu(self.shift, tupps, uupps, weis)
        self.uut = uut
        self.tut = tut

    def set_u_max(self):
        """
        This is needed to compute Ry0
        """

        # This is the same in both cases
        if self.shift is None:
            self._set_coordinate_shift()

        # Get the mesh with the endpoints of each polyline
        mesh = self.get_endpoints_mesh()

        if self.tupps is None:
            tupps, uupps, weis = get_tus(self.lines, mesh)
        else:
            tupps = self.tupps
            uupps = self.uupps
            weis = self.weis

        uut, _ = get_tu(self.shift, tupps, uupps, weis)

        # Maximum U value
        self.u_max = max(abs(uut))

    def get_endpoints_mesh(self) -> Mesh:
        """
        Build mesh with end points
        """
        lons = []
        lats = []
        for line in self.lines:
            lons.extend([line.coo[0, 0], line.coo[-1, 0]])
            lats.extend([line.coo[0, 1], line.coo[-1, 1]])
        mesh = Mesh(np.array(lons), np.array(lats))
        return mesh

    def get_rx_distance(self, mesh: Mesh = None):
        """
        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh` with the
            coordinates of the sites.
        :returns:
            A :class:`numpy.ndarray` instance with the Rx distance. Note that
            the Rx distance is directly taken from the GC2 t-coordinate.
        """
        if self.uut is None:
            assert mesh is not None
            self.set_tu(mesh)
        rx = self.tut[0] if len(self.tut[0].shape) > 1 else self.tut
        return rx

    def get_ry0_distance(self, mesh: Mesh = None):
        """
        :param mesh:
            An instance of :class:`openquake.hazardlib.geo.mesh.Mesh`
        """
        if self.uut is None:
            assert mesh is not None
            self.set_tu(mesh)

        if self.u_max is None:
            self.set_u_max()

        assert len(self.uut) == len(mesh), (len(self.uut), len(mesh))

        ry0 = np.zeros_like(self.uut)
        ry0[self.uut < 0] = abs(self.uut[self.uut < 0])

        condition = self.uut > self.u_max
        ry0[condition] = self.uut[condition] - self.u_max

        out = ry0[0] if len(ry0.shape) > 1 else ry0
        return out


def get_tus(lines: list, mesh: Mesh):
    """
    Computes the T and U coordinates for all the polylines in `lines` and the
    sites in the `mesh`

    :param lines:
        A list of :class:`openquake.hazardlib.geo.line.Line` instances
    :param mesh:
        An instance of :class:`openquake.hazardlib.geo.mesh.Mesh` with the
        sites location.
    """
    uupps = []
    tupps = []
    weis = []
    for line in lines:
        tupp, uupp, wei = line.get_tu(mesh)
        wei_sum = np.squeeze(np.sum(wei, axis=0))
        uupps.append(uupp)
        tupps.append(tupp)
        weis.append(wei_sum)
    return tupps, uupps, weis


def get_lengths(lines: list) -> np.ndarray:
    """
    Computes the total lenght for each polyline composing the multiline

    :returns:
        A :class:`numpy.ndarray` instance
    """
    return np.array([line.get_length() for line in lines])


def get_average_azimuths(lines: list) -> np.ndarray:
    """
    Computes the average azimuth for each polyline composing the multiline

    :returns:
        A :class:`numpy.ndarray` instance
    """
    return np.array([line.average_azimuth() for line in lines])


def get_overall_strike(lines: list, llens: list = None, avgaz: list = None):
    """
    Computes the overall strike direction for the multiline

    :param lines:
        A list of :class:`openquake.hazardlib.geo.line.Line` instances
    """

    # Get lenghts and average azimuths
    if llens is None:
        llens = get_lengths(lines)
    if avgaz is None:
        avgaz = get_average_azimuths(lines)

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


def get_origin(lines: list, strike_to_east: bool, avg_strike: float):
    """
    Compute the origin necessary to calculate the coordinate shift

    :returns:
        The longitude and latitude coordinates of the origin and an array with
        the indexes used to sort the lines according to the origin
    """

    # Create the list of endpoints
    endp = []
    for line in lines:
        endp.append([line.coo[0, 0], line.coo[0, 1]])
        endp.append([line.coo[-1, 0], line.coo[-1, 1]])
    endp = np.array(endp)

    # Project the endpoints
    proj = utils.OrthographicProjection.from_lons_lats(endp[:, 0], endp[:, 1])
    px, py = proj(endp[:, 0], endp[:, 1])

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


def get_tu(shifts, tupps, uupps, weis):
    """
    Given a mesh, computes the T and U coordinates for the multiline
    """
    for i, (shift, tupp, uupp, wei_sum) in enumerate(
            zip(shifts, tupps, uupps, weis)):
        if len(wei_sum.shape) > 1:
            wei_sum = np.squeeze(wei_sum)
        if i == 0:  # initialize
            uut = (uupp + shift) * wei_sum
            tut = tupp * wei_sum
            wet = copy.copy(wei_sum)
        else:  # update the values
            uut += (uupp + shift) * wei_sum
            tut += tupp * wei_sum
            wet += wei_sum

    # Normalize by the sum of weights
    uut /= wet
    tut /= wet

    return uut, tut
