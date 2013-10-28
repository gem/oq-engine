# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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
Module :mod:`openquake.hazardlib.tom` contains implementations of probability
density functions for earthquake temporal occurrence modeling.
"""
import math

import numpy
import scipy.stats

from openquake.hazardlib.slots import with_slots


@with_slots
class PoissonTOM(object):
    """
    Poissonian temporal occurrence model.

    :param time_span:
        The time interval of interest, in years.
    :raises ValueError:
        If ``time_span`` is not positive.
    """
    __slots__ = ['time_span']

    def __init__(self, time_span):
        if time_span <= 0:
            raise ValueError('time_span must be positive')
        self.time_span = time_span

    def get_probability_one_or_more_occurrences(self, occurrence_rate):
        """
        Calculate and return the probability of event to happen one or more
        times within the time range defined by constructor's ``time_span``
        parameter value.

        Calculates probability as ``1 - e ** (-occurrence_rate*time_span)``.

        :param occurrence_rate:
            The average number of events per year.
        :return:
            Float value between 0 and 1 inclusive.
        """
        return 1 - math.exp(- occurrence_rate * self.time_span)

    def get_probability_one_occurrence(self, occurrence_rate):
        """
        Calculate and return the probability of event to occur once
        within the time range defined by the constructor's ``time_span``
        parameter value.
        """
        return scipy.stats.poisson(occurrence_rate * self.time_span).pmf(1)

    def sample_number_of_occurrences(self, occurrence_rate):
        """
        Draw a random sample from the distribution and return a number
        of events to occur.

        Method uses numpy random generator, which needs to be seeded
        outside of this method in order to get reproducible results.

        :param occurrence_rate:
            The average number of events per year.
        :return:
            Sampled integer number of events to occur within model's
            time span.
        """
        return numpy.random.poisson(occurrence_rate * self.time_span)
