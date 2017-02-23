# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
import math

import numpy
import scipy.stats

from openquake.baselib.slots import with_slots


@with_slots
class PoissonTOM(object):
    """
    Poissonian temporal occurrence model.

    :param time_span:
        The time interval of interest, in years.
    :raises ValueError:
        If ``time_span`` is not positive.
    """
    _slots_ = ['time_span']

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
        Compute and return, for a number of ground motion levels and sites,
        the probability that a rupture with annual occurrence rate given by
        ``occurrence_rate`` and able to cause ground motion values higher than
        a given level at a site with probability ``poes``, does not cause any
        exceedance in the time window specified by the ``time_span`` parameter
        given in the constructor.

        The probability is computed using the following formula ::

            (1 - e ** (-occurrence_rate * time_span)) ** poes

        :param occurrence_rate:
            The average number of events per year.
        :param poes:
            2D numpy array containing conditional probabilities the the a
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
