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
from openquake.hazardlib import geo
from openquake.hazardlib.geo import utils


class MultiLine(object):
    """
    A collection of polylines with associated methods and attributes. These
    are for the most part used to compute distances according to the GC2
    method.
    """

    def __init__(self, lines):
        self.lines = lines

    def get_lengths(self) -> np.ndarray:
        """
        Computes the total lenght for each polyline composing the multiline

        :returns:
            A :class:`numpy.ndarray` instance
        """
        llenghts = []
        for line in self.lines:
            llenghts.append(line.get_length())
        return np.array(llenghts)

    def get_average_azimuths(self) -> np.ndarray:
        """
        Computes the average azimuth for each polyline composing the multiline

        :returns:
            A :class:`numpy.ndarray` instance
        """
        avgazims = []
        for line in self.lines:
            avgazims.append(line.average_azimuth())
        return np.array(avgazims)

    def set_overall_strike(self):
        """
        Computes the overall strike direction for the multiline

        :param lines:
            A list of :class:`openquake.hazardlib.geo.line.Line` instances
        """

        # Get lenghts and average azimuths
        llenghts = self.get_lengths()
        avgaz = self.get_average_azimuths()

        # Find general trend
        tmp = copy.copy(avgaz)
        idx = tmp > 180
        tmp[idx] = tmp[idx] - 180.
        ave = geo.line.get_average_azimuth(tmp, llenghts)

        # Computing the azimuth direction (i.e. towards east or west)
        #idx = (avgaz >= 0) & (avgaz < 180)
        revert = np.zeros((len(self.lines)), dtype=bool)
        if (ave > 90) & (ave < 270):
            idx = (avgaz >= (ave - 90) % 360) & (avgaz < (ave + 90) % 360)
        else:
            idx = (avgaz >= (ave - 90) % 360) | (avgaz < (ave + 90) % 360)
        delta = abs(avgaz - ave)
        scale = np.abs(np.cos(np.radians(delta)))
        ratio = np.sum(llenghts[idx] * scale[idx]) / np.sum(llenghts * scale)

        # ratio = np.sum(llenghts[idx]) / sum(llenghts)
        strike_to_east = True if ratio > 0.5 else False
        if strike_to_east:
            revert[np.invert(idx)] = True
        else:
            revert[idx] = True

        # Compute the prevalent azimuth
        avgazims_corr = copy.copy(avgaz)
        for i in np.nonzero(revert)[0]:
            self.lines[i].flip()
            avgazims_corr[i] = self.lines[i].average_azimuth()
        azimuth = geo.line.get_average_azimuth(avgazims_corr, llenghts)

        # Update info
        self.strike_to_east = strike_to_east
        self.overall_strike = azimuth

        return revert

    def _set_origin(self):
        """
        Compute the origin necessary to calculate the coordinate shift
        """

        # Create the list of endpoints
        endp = []
        for line in self.lines:
            endp.append([line.coo[0, 0], line.coo[0, 1]])
            endp.append([line.coo[-1, 0], line.coo[-1, 1]])
        endp = np.array(endp)

        # Project the endpoints
        oprj = utils.OrthographicProjection
        proj = oprj.from_lons_lats(endp[:, 0], endp[:, 1])
        px, py = proj(endp[:, 0], endp[:, 1])

        # If missing, set the overall strike direction
        if not hasattr(self, 'strike_to_east'):
            _ = self.set_overall_strike()

        # Find the index of the eastmost (or westmost) point depending on the
        # prevalent direction of the strike
        if self.strike_to_east:
            idx = np.argmin(px)
        else:
            idx = np.argmax(px)

        # Set the origin to be used later for the calculation of the
        # coordinate shift
        x = np.array([px[idx]])
        y = np.array([py[idx]])
        olon, olat = proj(x, y, reverse=True)
        self.olon = olon[0]
        self.olat = olat[0]

    def _set_coordinate_shift(self) -> np.ndarray:
        """
        Computes the coordinate shift for each line in the multiline. This is
        used to compute coordinates in the GC2 system
        """

        # If not defined, compute the origin of the multiline
        if not hasattr(self, 'olon'):
            self._set_origin()

        # For each line in the multi line, get the distance along the average
        # strike between the origin of the multiline and the first endnode
        origins = np.array([[l.coo[0, 0], l.coo[0, 1]] for l in self.lines])

        # Distances and azimuths between the origin of the multiline and the
        # first endpoint
        ggdst = geo.geodetic.geodetic_distance
        ggazi = geo.geodetic.azimuth
        distances = ggdst(self.olon, self.olat, origins[:, 0], origins[:, 1])
        azimuths = ggazi(self.olon, self.olat, origins[:, 0], origins[:, 1])

        # Calculate the shift along the average strike direction
        shift = np.cos(np.radians(self.overall_strike - azimuths))*distances
        self.shift = shift

    def get_tu(self, mesh: geo.Mesh):
        """
        Given a mesh, computes the T and U coordinates for the multiline
        """

        # Set the coordinate shift
        self._set_coordinate_shift()
        shift = self.shift

        # Processing
        for i, line in enumerate(self.lines):

            # Compute (or retrieve) the T and U coordinates. T and U have
            # cardinality <number_sites>. The weights have cardinality equal
            # to <number_of_segments> x <number of_sites>
            if not hasattr(self, 'tupp'):
                tupp, uupp, wei = line.get_tu(mesh)
                wei_sum = np.sum(wei, axis=0)
            else:
                tupp = self.tupp
                uupp = self.uupp

            # Update the uupp values
            if i == 0:
                uut = (uupp + shift[i]) * wei_sum
                tut = tupp * wei_sum
                wet = wei_sum
            else:
                uut += (uupp + shift[i]) * wei_sum
                tut += tupp * wei_sum
                wet += wei_sum

        # Normalize by the sum of weights
        uut /= wet
        tut /= wet

        return uut, tut
