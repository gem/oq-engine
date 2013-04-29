# coding=utf-8
# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.

import numpy
from scipy.interpolate import interp1d


class Curve(object):
    """
    This class defines a curve (discrete function)
    used in the risk domain.
    """

    def __init__(self, pairs):
        """
        Construct a curve from a sequence of tuples.

        The value on the first position of the tuple is the x value,
        the value(s) on the second position is the y value(s).
        """
        pairs = sorted(pairs)  # sort the pairs on x axis
        npairs = len(pairs)
        self.abscissae = numpy.empty(npairs)
        self.ordinates = numpy.empty(npairs)
        for index, (key, val) in enumerate(pairs):
            self.abscissae[index] = key
            self.ordinates[index] = val

    def ordinate_for(self, val):
        """
        Cached attribute. Returns the interpolated function.
        This is very useful to speed up the computation and feed
        "directly" numpy.
        """
        min_val, max_val = min(self.abscissae), max(self.abscissae)

        # convert to numpy.array so we can use numpy.putmask:
        val = numpy.array(val)
        numpy.putmask(val, val < min_val, min_val)
        numpy.putmask(val, val > max_val, max_val)

        return interp1d(self.abscissae, self.ordinates)(val)

    def ordinate_diffs(self, xs):
        """
        Returns the differences y_i - y_{i+1} for the given x_i
        """
        ys = self.ordinate_for(xs)
        return [i - j for i, j in zip(ys, ys[1:])]
