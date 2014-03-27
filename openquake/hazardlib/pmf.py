# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.pmf` implements :class:`PMF`.
"""
from openquake.hazardlib.slots import with_slots


@with_slots
class PMF(object):
    """
    Probability mass function is a function that gives the probability
    that a discrete random variable is exactly equal to some value.

    :param data:
        The PMF data in a form of list of tuples. Each tuple must contain
        two items with the first item being the probability of the implied
        random variable to take value of the second item.

        There must be at least one tuple in the list. All probabilities
        must sum up to 1. In order to guarantee that regardless of float
        values representation on a machine in use using of type Decimal
        is recommended.

        The type of values (second items in tuples) is not strictly defined,
        those can be objects of any (mixed or homogeneous) type.

    :raises ValueError:
        If probabilities do not sum up to 1 or there is zero or negative
        probability.
    """
    __slots__ = ['data']

    def __init__(self, data):
        if not data or (sum(prob for (prob, value) in data) != 1.0):
            raise ValueError('values do not sum up to 1.0')
        if any(prob <= 0 for (prob, value) in data):
            raise ValueError('probability is not positive')
        self.data = data
