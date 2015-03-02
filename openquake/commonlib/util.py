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


def _max_rel_diff(curve1, curve2, min_value=0.01):
    assert len(curve1) == len(curve2), (len(curve1), len(curve2))
    assert len(curve1), 'The curves are empty!'
    max_diff = 0
    for c1, c2 in zip(curve1, curve2):
        if c1 >= min_value and c2 >= min_value:
            rel_diff = abs(c1 - c2) / (c1 + c2) * 2
            max_diff = max(max_diff, rel_diff)
    return max_diff


def max_rel_diff(curve1, curve2, min_value=0.01):
    """
    Compute the maximum relative difference between two curves. Only values
    greather or equal than the min_value are considered.

    >>> curve1 = [0.01, 0.02, 0.03, 0.05, 1.0]
    >>> curve2 = [0.011, 0.021, 0.031, 0.051, 1.0]
    >>> round(max_rel_diff(curve1, curve2), 3)
    0.095
    """
    assert len(curve1) == len(curve2), (len(curve1), len(curve2))
    assert len(curve1), 'The curves are empty!'
    if hasattr(curve1[0], '__len__'):
        return max(_max_rel_diff(c1, c2, min_value)
                   for c1, c2 in zip(curve1, curve2))
    # else assume scalars
    return _max_rel_diff(curve1, curve2, min_value)
