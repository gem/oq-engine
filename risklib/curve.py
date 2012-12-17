# coding=utf-8
# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from collections import OrderedDict
import numpy
from scipy.interpolate import interp1d
from risklib.range import range_clip


class Curve(object):
    """This class defines a curve (discrete function)
    used in the risk domain."""

    @classmethod
    def from_list(cls, values):
        """Construct a curve from a dictionary.

        The dictionary keys can be unordered and of
        whatever type can be converted to float with float().
        """

        data = []

        for x, y in values:
            data.append((x, y))

        return cls(data)

    def __init__(self, values):
        """Construct a curve from a sequence of tuples.

        The value on the first position of the tuple is the x value,
        the value(s) on the second position is the y value(s). This class
        supports multiple y values for the same x value, for example:

        Curve([(0.1, 1.0), (0.2, 2.0)]) # single y value
        Curve([(0.1, (1.0, 0.5)), (0.2, (2.0, 0.5))]) # multiple y values

        You can also pass lists instead of tuples, like:

        Curve([(0.1, [1.0, 0.5]), (0.2, [2.0, 0.5])])
        """

        # sort the values on x axis
        values = sorted(values)

        elements = len(values)
        self.x_values = numpy.empty(elements)
        self.y_values = numpy.empty(elements)

        if elements and type(values[0][1]) in (tuple, list):
            self.y_values = numpy.empty((elements, len(values[0][1])))

        for index, (key, val) in enumerate(values):
            self.x_values[index] = key
            self.y_values[index] = val

    def __eq__(self, other):
        return numpy.allclose(self.x_values, other.x_values)\
        and numpy.allclose(self.y_values, other.y_values)

    def __str__(self):
        return "X Values: %s\nY Values: %s" % (
            self.x_values.__str__(), self.y_values.__str__())

    def rescale_abscissae(self, value):
        """Return a new curve with each abscissa value multiplied
        by the value passed as parameter."""

        result = Curve(())
        result.x_values = self.x_values * value
        result.y_values = self.y_values

        return result

    @property
    def abscissae(self):
        """Return the abscissa values of this curve in ascending order."""
        return self.x_values

    @property
    def is_empty(self):
        """Return true if this curve is numpy.empty, false otherwise."""
        return self.abscissae.size == 0

    @property
    def ordinates(self):
        """Return the ordinate values of this curve in ascending order
        of the corresponding abscissa values."""
        return self.y_values

    @property
    def is_multi_value(self):
        """Return true if this curve describes multiple ordinate values,
        false otherwise."""
        return self.y_values.ndim > 1

    def ordinate_for(self, x_value, y_index=0):
        """
            Return the y value corresponding to the given x value.
            interp1d parameters can be a list of x_values, y_values
            this is very useful to speed up the computation and feed
            "directly" numpy
        """

        x_value = range_clip(x_value, self.x_values)

        y_values = self.y_values

        if self.y_values.ndim > 1:
            y_values = self.y_values[:, y_index]

        return interp1d(self.x_values, y_values)(x_value)

    def abscissa_for(self, y_value):
        """Return the x value corresponding to the given y value."""

        # inverting the function
        inverted_func = [(ordinate, x_value) for ordinate, x_value in
                         zip(self.ordinate_for(self.abscissae),
                             self.abscissae)]

        return Curve(inverted_func).ordinate_for(y_value)

    def ordinate_out_of_bounds(self, y_value):
        """Check if the given value is outside the Y values boundaries."""
        ordinates = list(self.ordinates)
        ordinates.sort()

        return y_value < ordinates[0] or y_value > ordinates[-1]

    def with_unique_ordinates(self):
        """
        Given `curve` return a new curve with unique ordinates. Points
        are just copied except for points with the same ordinate for
        which only the last one is kept.
        """
        seen = OrderedDict()

        for ordinate, abscissa in zip(self.ordinates, self.abscissae):
            seen[ordinate] = abscissa

        return self.__class__(zip(seen.values(), seen.keys()))

EMPTY_CURVE = Curve(())
