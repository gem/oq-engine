# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.hazardlib.tom` contains implementations of probability
density functions for earthquake temporal occurrence modeling.
"""
import abc
import math

import numpy
import scipy.stats

from openquake.baselib.slots import with_slots

registry = {}


@with_slots
class BaseTOM(metaclass=abc.ABCMeta):
    """
    Base class for temporal occurrence model.

    :param time_span:
        The time interval of interest, in years.
    :raises ValueError:
        If ``time_span`` is not positive.
    """
    _slots_ = ['time_span', 'occurrence_rate']

    @classmethod
    def __init_subclass__(cls):
        registry[cls.__name__] = cls

    def __init__(self, time_span, occurrence_rate=None):
        if time_span <= 0:
            raise ValueError('time_span must be positive')
        self.time_span = time_span
        self.occurrence_rate = occurrence_rate

    @abc.abstractmethod
    def get_probability_one_or_more_occurrences(self):
        """
        Calculate and return the probability of event to happen one or more
        times within the time range defined by constructor's ``time_span``
        parameter value.
        """

    @abc.abstractmethod
    def get_probability_n_occurrences(self):
        """
        Calculate the probability of occurrence of a number of events in the
        constructor's ``time_span``.
        """

    @abc.abstractmethod
    def sample_number_of_occurrences(self, seeds=None):
        """
        Draw a random sample from the distribution and return a number
        of events to occur.

        The method uses the numpy random generator, which needs a seed
        in order to get reproducible results. If the seed is None, it
        should be set outside of this method.
        """

    @abc.abstractmethod
    def get_probability_no_exceedance(self):
        """
        Compute and return, for a number of ground motion levels and sites,
        the probability that a rupture with annual occurrence rate given by
        ``occurrence_rate`` and able to cause ground motion values higher than
        a given level at a site with probability ``poes``, does not cause any
        exceedance in the time window specified by the ``time_span`` parameter
        given in the constructor.
        """

@with_slots
class FatedTOM(BaseTOM):

    def __init__(self, time_span, occurrence_rate=None):
        self.time_span = time_span
        self.occurrence_rate = occurrence_rate

    def get_probability_one_or_more_occurrences(self, occurrence_rate):
        return 1

    def get_probability_n_occurrences(self, occurrence_rate, num):
        if num != 1: 
            return 0
        else:
            return 1
        
    def sample_number_of_occurrences(self, seeds=None):
        return 1

    def get_probability_no_exceedance(self, occurrence_rate, poes):
        return 1-poes

@with_slots
class PoissonTOM(BaseTOM):
    """
    Poissonian temporal occurrence model.
    """

    def get_probability_one_or_more_occurrences(self, occurrence_rate):
        """
        Calculates probability as ``1 - e ** (-occurrence_rate*time_span)``.

        :param occurrence_rate:
            The average number of events per year.
        :return:
            Float value between 0 and 1 inclusive.
        """
        return 1 - math.exp(- occurrence_rate * self.time_span)

    def get_probability_n_occurrences(self, occurrence_rate, num):
        """
        Calculate the probability of occurrence  of ``num`` events in the
        constructor's ``time_span``.

        :param occurrence_rate:
            Annual rate of occurrence
        :param num:
            Number of events
        :return:
            Probability of occurrence
        """
        return scipy.stats.poisson(occurrence_rate * self.time_span).pmf(num)

    def sample_number_of_occurrences(self, occurrence_rate, seeds=None):
        """
        Draw a random sample from the distribution and return a number
        of events to occur.

        The method uses the numpy random generator, which needs a seed
        in order to get reproducible results. If the seed is None, it
        should be set outside of this method.

        :param occurrence_rate:
            The average number of events per year.
        :param seeds:
            Random number generator seeds, one per each occurrence_rate
        :return:
            Sampled integer number of events to occur within model's
            time span.
        """
        if isinstance(seeds, numpy.ndarray):  # array of seeds
            assert len(seeds) == len(occurrence_rate), (
                len(seeds), len(occurrence_rate))
            rates = occurrence_rate * self.time_span
            occ = []
            for rate, seed in zip(rates, seeds):
                numpy.random.seed(seed)
                occ.append(numpy.random.poisson(rate))
            return numpy.array(occ)
        elif isinstance(seeds, int):
            numpy.random.seed(seeds)
        return numpy.random.poisson(occurrence_rate * self.time_span)

    def get_probability_no_exceedance(self, occurrence_rate, poes):
        """
        The probability is computed using the following formula ::

            (1 - e ** (-occurrence_rate * time_span)) ** poes

        :param occurrence_rate:
            The average number of events per year.
        :param poes:
            2D numpy array containing conditional probabilities that the 
            rupture occurrence causes a ground shaking value exceeding a
            ground motion level at a site. First dimension represent sites,
            second dimension intensity measure levels. ``poes`` can be obtained
            calling the :meth:`method
            <openquake.hazardlib.gsim.base.GroundShakingIntensityModel.get_poes>`.
        :return:
            2D numpy array containing probabilities of no exceedance. First
            dimension represents sites, second dimensions intensity measure
            levels.
        """
        p = self.get_probability_one_or_more_occurrences(occurrence_rate)
        return (1 - p) ** poes
