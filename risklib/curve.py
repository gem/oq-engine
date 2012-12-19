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

import numpy
from scipy.interpolate import interp1d
from risklib.range import range_clip


class Curve(object):
    """
    This class defines a curve (discrete function)
    used in the risk domain.
    """
    def __init__(self, values):
        """
        Construct a curve from a sequence of tuples.

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
        self.abscissae = numpy.empty(elements)
        self.ordinates = numpy.empty(elements)

        if elements and type(values[0][1]) in (tuple, list):
            self.ordinates = numpy.empty((elements, len(values[0][1])))

        for index, (key, val) in enumerate(values):
            self.abscissae[index] = key
            self.ordinates[index] = val

    def __eq__(self, other):
        return numpy.allclose(self.abscissae, other.abscissae)\
            and numpy.allclose(self.ordinates, other.ordinates)

    def __str__(self):
        return "X Values: %s\nY Values: %s" % (self.abscissae, self.ordinates)

    def rescale_abscissae(self, value):
        """Return a new curve with each abscissa value multiplied
        by the value passed as parameter."""

        result = Curve(())
        result.abscissae = self.abscissae * value
        result.ordinates = self.ordinates
        return result

    def with_unique_ordinates(self):
        """
        Given `curve` return a new curve with unique ordinates. Points
        are just copied except for points with the same ordinate for
        which only the last one is kept.
        """
        reverse = dict(zip(self.ordinates, self.abscissae))
        return self.__class__((v, k) for k, v in reverse.iteritems())

    @property
    def is_empty(self):
        """Return true if this curve is numpy.empty, false otherwise."""
        return self.abscissae.size == 0

    @property
    def is_multi_value(self):
        """Return true if this curve describes multiple ordinate values,
        false otherwise."""
        return self.ordinates.ndim > 1

    def ordinate_for(self, x_value, y_index=0):
        """
        Return the y value corresponding to the given x value.
        interp1d parameters can be a list of abscissae, ordinates
        this is very useful to speed up the computation and feed
        "directly" numpy.
        """
        x_value = range_clip(x_value, self.abscissae)
        if self.ordinates.ndim > 1:
            ordinates = self.ordinates[:, y_index]
        else:
            ordinates = self.ordinates
        return interp1d(self.abscissae, ordinates)(x_value)

    def abscissa_for(self, y_value):
        """Return the x value corresponding to the given y value."""

        # inverting the function
        inverted_func = [(ordinate, x_value) for ordinate, x_value in
                         zip(self.ordinate_for(self.abscissae),
                             self.abscissae)]

        return Curve(inverted_func).ordinate_for(y_value)

    def ordinate_out_of_bounds(self, y_value):
        """Check if the given value is outside the Y values boundaries."""
        return y_value < min(self.ordinates) or y_value > max(self.ordinates)


EMPTY_CURVE = Curve(())
