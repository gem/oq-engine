#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy


def max_rel_diff(curve_ref, curve, min_value=0.01):
    """
    Compute the maximum relative difference between two curves. Only values
    greather or equal than the min_value are considered.

    >>> curve_ref = [0.01, 0.02, 0.03, 0.05, 1.0]
    >>> curve = [0.011, 0.021, 0.031, 0.051, 1.0]
    >>> round(max_rel_diff(curve_ref, curve), 2)
    0.1
    """
    assert len(curve_ref) == len(curve), (len(curve_ref), len(curve))
    assert len(curve), 'The curves are empty!'
    max_diff = 0
    for c1, c2 in zip(curve_ref, curve):
        if c1 >= min_value:
            max_diff = max(max_diff, abs(c1 - c2) / c1)
    return max_diff


def max_rel_diff_index(curve_ref, curve, min_value=0.01):
    """
    Compute the maximum relative difference between two sets of curves.
    Only values greather or equal than the min_value are considered.
    Return both the maximum difference and its location (array index).

    >>> curve_refs = [[0.01, 0.02, 0.03, 0.05], [0.01, 0.02, 0.04, 0.06]]
    >>> curves = [[0.011, 0.021, 0.031, 0.051], [0.012, 0.022, 0.032, 0.051]]
    >>> max_rel_diff_index(curve_refs, curves)
    (0.2, 1)
    """
    assert len(curve_ref) == len(curve), (len(curve_ref), len(curve))
    assert len(curve), 'The curves are empty!'
    diffs = [max_rel_diff(c1, c2, min_value)
             for c1, c2 in zip(curve_ref, curve)]
    maxdiff = max(diffs)
    maxindex = diffs.index(maxdiff)
    return maxdiff, maxindex


def rmsep(curve_ref, curve):
    """
    Root Mean Square Error Percentage

    :param numpy.array curve_ref: reference curve
    :param numpy.array curve: a curve

    >>> curve_ref = numpy.array([0.01, 0.02, 0.03, 0.05, 1.0])
    >>> curve = numpy.array([0.011, 0.021, 0.031, 0.051, 1.0])
    >>> rmsep(curve_ref, curve)
    0.052936020082947469
    """
    reldiffsquare = (1. - curve / curve_ref) ** 2
    return numpy.sqrt(reldiffsquare.mean())


def rmsep_index(curves_ref, curves):
    """
    Root Mean Square Error Percentage for a set of curves

    :param numpy.array curve_ref: reference curves
    :param numpy.array curve: curves
    :returns: the maximum difference and the curve index

    >>> curve_ref = numpy.array([[0.01, 0.02, 0.03, 0.05],
    ... [0.01, 0.02, 0.04, 0.06]])
    >>> curve = numpy.array([[0.011, 0.021, 0.031, 0.051],
    ... [0.012, 0.022, 0.032, 0.051]])
    >>> rmsep_index(curve_ref, curve)
    (0.16770509831248417, 1)
    """
    assert len(curves_ref) == len(curves), (len(curves_ref), len(curves))
    assert len(curves), 'The curves are empty!'
    diffs = [rmsep(c1, c2) for c1, c2 in zip(curves_ref, curves)]
    maxdiff = max(diffs)
    maxindex = diffs.index(maxdiff)
    return maxdiff, maxindex
