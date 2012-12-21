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


def range_clip(val, val_range):
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
    :param val_range: This is the range we 'clip' the input value(s) to. The
        range values should be arranged in ascending order with no duplicates.
        The length of the range must be at least 2 elements.
    :type val_range: 1-dimensional :py:class:`numpy.ndarray`

    :returns: Clipped value(s).
        If the input type is a single value, return a numpy numeric type (such
        as numpy.float64).
        If the input val is a sequence (list, tuple or
        :py:class:`numpy.ndarray`), return a :py:class:`numpy.ndarray` of
        clipped values.
    """
    assert len(val_range) >= 2, "val_range must contain at least 2 elements"

    min_val, max_val = min(val_range), max(val_range)

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
