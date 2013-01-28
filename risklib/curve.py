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
        self._inverse = None  # set by abscissa_for

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

    @property
    def inverse(self):
        """Cached attribute. Returns the inverse function."""
        if self._inverse is None:
            with_unique_ys = dict(zip(self.ordinates, self.abscissae))
            self._inverse = self.__class__(with_unique_ys.iteritems())
        return self._inverse

    # so that the curve is pickeable even if self.interp has been instantiated
    def __getstate__(self):
        return dict(abscissae=self.abscissae, ordinates=self.ordinates,
                    _interp=None, _inverse=self._inverse)

    def __eq__(self, other):
        return numpy.allclose(self.abscissae, other.abscissae)\
            and numpy.allclose(self.ordinates, other.ordinates)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return len(self.abscissae)

    def __str__(self):
        return "X Values: %s\nY Values: %s" % (self.abscissae, self.ordinates)

    def rescale_abscissae(self, value):
        """
        Return a new curve with each abscissa value multiplied
        by the value passed as parameter.
        """
        newcurve = Curve(())
        newcurve.abscissae = self.abscissae * value
        newcurve.ordinates = self.ordinates
        return newcurve

    def ordinate_diffs(self, xs):
        """
        Returns the differences y_i - y_{i+1} for the given x_i
        """
        ys = self.ordinate_for(xs)
        return [i - j for i, j in zip(ys, ys[1:])]

    def abscissa_for(self, y_value):
        """
        Return the x value corresponding to the given y value.
        Notice that non-invertible function are inverted by
        discarding duplicated y values for the same x!
        Mathematicians would cry.
        """
        return self.inverse.ordinate_for(y_value)

    def ordinate_out_of_bounds(self, y_value):
        """
        Check if the given value is outside the Y values boundaries.
        """
        return y_value < min(self.ordinates) or y_value > max(self.ordinates)

EMPTY_CURVE = Curve(())
