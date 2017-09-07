# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
import numpy as np
from openquake.baselib.slots import with_slots


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
        must sum up to 1 within the given precision.

        The type of values (second items in tuples) is not strictly defined,
        those can be objects of any (mixed or homogeneous) type.

    :param epsilon:
        the tolerance for the sum of the probabilities (default 1E-15)

    :raises ValueError:
        If probabilities do not sum up to 1 or there is zero or negative
        probability.

    NB: in the engine the sum is checked to be exactly one by using
    Decimal numbers.
    """
    _slots_ = ['data']

    def __init__(self, data, epsilon=1E-15):
        probs, values = list(zip(*data))
        if any(prob < 0 for prob in probs):
            raise ValueError('a probability in %s is not positive'
                             % list(probs))
        if abs(float(sum(probs)) - 1.0) > epsilon:
            raise ValueError('probabilities %s do not sum up to 1.0'
                             % list(probs))
        self.data = list(zip(map(float, probs), values))

    def sample(self, number_samples):
        """
        Produces a list of samples from the probability mass function.

        :param int data:
            Number of samples
        :returns:
            Samples from PMF as a list
        """
        return [pair[1] for pair in self.sample_pairs(number_samples)]

    def sample_pairs(self, number_samples):
        """
        Produces a list of samples from the probability mass function.

        :param int data:
            Number of samples
        :returns:
            Samples from PMF as a list of pairs
        """
        probs = np.cumsum([val[0] for val in self.data])
        sampler = np.random.uniform(0., 1., number_samples)
        return [self.data[ival] for ival in np.searchsorted(probs, sampler)]
