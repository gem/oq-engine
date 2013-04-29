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
        self._interp = None  # set by ordinate_for

    @property
    def ordinate_for(self):
        """
        Cached attribute. Returns the interpolated function.
        This is very useful to speed up the computation and feed
        "directly" numpy.
        """
        if self._interp is None:
            i1d = interp1d(self.abscissae, self.ordinates)
            self._interp = lambda x: i1d(self.range_clip(x, self.abscissae))
        return self._interp

    @staticmethod
    def range_clip(val, a_range):
        """
        'Clip' a value (or sequence of values) to the
        specified range.

        Consider the example IML range [0.005, 0.007, 0.009].

        If the input IML value is less than the min value (0.005), return the
        min value.

        If the input IML value is greater than the max value (0.009), return
        the max value.

        Otherwise, the IML will not change.

        :param val: numeric value(s) to clip
        :type val: float, list/tuple of floats, or :py:class:`numpy.ndarray` of
            floats
        :param a_range: This is the range we 'clip' the input
            value(s) to. The range values should be arranged in
            ascending order with no duplicates. The length of the
            range must be at least 2 elements.
        :type a_range: 1-dimensional :py:class:`numpy.ndarray`

        :returns: Clipped value(s).
            If the input type is a single value, return a numpy
            numeric type (such as numpy.float64). If the input val is
            a sequence (list, tuple or :py:class:`numpy.ndarray`),
            return a :py:class:`numpy.ndarray` of clipped values.
        """
        assert len(a_range) >= 2, "a_range must contain at least 2 elements"

        min_val, max_val = min(a_range), max(a_range)

        if hasattr(val, '__len__'):  # a sequence
            # convert to numpy.array so we can use numpy.putmask:
            val = numpy.array(val)
            numpy.putmask(val, val < min_val, min_val)
            numpy.putmask(val, val > max_val, max_val)
            return val

        # else val is a single (float) value
        if val < min_val:
            return min_val
        elif val > max_val:
            return max_val
        return val

    def ordinate_diffs(self, xs):
        """
        Returns the differences y_i - y_{i+1} for the given x_i
        """
        ys = self.ordinate_for(xs)
        return [i - j for i, j in zip(ys, ys[1:])]
