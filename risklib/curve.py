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

    # so that the curve is pickeable even if self.interp has been instantiated
    def __getstate__(self):
        return dict(abscissae=self.abscissae, ordinates=self.ordinates)

    def __eq__(self, other):
        return numpy.allclose(self.abscissae, other.abscissae)\
            and numpy.allclose(self.ordinates, other.ordinates)

    def __ne__(self, other):
        return not self.__eq__(other)

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

    def ordinate_for(self, x_value):
        """
        Return the y value corresponding to the given x value.
        interp1d parameters are a list of abscissae, ordinates.
        This is very useful to speed up the computation and feed
        "directly" numpy.
        """
        if hasattr(self, 'interp'):  # cached interpolated curve
            return self.interp(range_clip(x_value, self.abscissae))
        self.interp = interp1d(self.abscissae, self.ordinates)
        return self.interp(range_clip(x_value, self.abscissae))

    def abscissa_for(self, y_value):
        """
        Return the x value corresponding to the given y value.
        """
        # inverting the function
        inverted_func = [(ordinate, x_value) for ordinate, x_value in
                         zip(self.ordinate_for(self.abscissae),
                             self.abscissae)]
        return Curve(inverted_func).ordinate_for(y_value)

    def ordinate_out_of_bounds(self, y_value):
        """
        Check if the given value is outside the Y values boundaries.
        """
        return y_value < min(self.ordinates) or y_value > max(self.ordinates)

EMPTY_CURVE = Curve(())
