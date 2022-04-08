# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2022 GEM Foundation
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
import numpy
import scipy.stats
from openquake.baselib.performance import compile

registry = {}
F64 = numpy.float64


class BaseTOM(metaclass=abc.ABCMeta):
    """
    Base class for temporal occurrence model.

    :param time_span:
        The time interval of interest, in years.
    :raises ValueError:
        If ``time_span`` is not positive.
    """
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
        return 1 - numpy.exp(- occurrence_rate * self.time_span)

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
        :param occurrence_rate:
            The average number of events per year.
        :param poes:
            2D numpy array containing conditional probabilities that the
            rupture occurrence causes a ground shaking value exceeding a
            ground motion level at a site. First dimension represent sites,
            second dimension intensity measure levels. ``poes`` can be obtained
            calling the :func:`func <openquake.hazardlib.gsim.base.get_poes>`.
        :returns:
            2D numpy array containing probabilities of no exceedance. First
            dimension represents sites, second dimension intensity measure
            levels.

        The probability is computed as exp(-occurrence_rate * time_span * poes)
        """
        return numpy.exp(- occurrence_rate * self.time_span * poes)


# use in calc.disagg
def get_probability_no_exceedance_rup(rup, poes, tom):
    """
    Compute and return the probability that in the time span for which the
    rupture is defined, the rupture itself never generates a ground motion
    value higher than a given level at a given site.

    Such calculation is performed starting from the conditional probability
    that an occurrence of the current rupture is producing a ground motion
    value higher than the level of interest at the site of interest.
    The actual formula used for such calculation depends on the temporal
    occurrence model the rupture is associated with.
    The calculation can be performed for multiple intensity measure levels
    and multiple sites in a vectorized fashion.

    :param rup:
        an object with a scalar attribute .occurrence_rate
    :param poes:
        array of shape (n, L, G) containing conditional probabilities that a
        rupture occurrence causes a ground shaking value exceeding a
        ground motion level at a site. First dimension represent sites,
        second dimension intensity measure levels. ``poes`` can be obtained
        calling the :func:`func <openquake.hazardlib.gsim.base.get_poes>`
    :param tom:
        temporal occurrence model (not used if the rupture is nonparametric)
    """
    if numpy.isnan(rup.occurrence_rate):  # nonparametric
        pnes = numpy.zeros_like(poes)
        set_probability_no_exceedance_np(rup.probs_occur, poes, pnes)
        return pnes
    else:  # parametric
        return tom.get_probability_no_exceedance(rup.occurrence_rate, poes)


@compile("(float64[:], float64[:,:,:], float64, float64[:,:,:])")
def calc_pnes(rates, poes, time_span, out):
    """
    Compute probabilities of no exceedance by using the poisson distribution
    (fast). Works by populating the "out" array.
    """
    for i, rate in enumerate(rates):
        out[i] = -rate * time_span * poes[i]
    numpy.exp(out, out)


def get_probability_no_exceedance(ctx, poes, probs_or_tom):
    """
    Vectorized version of :func:`get_probability_no_exceedance_rup`.

    :param ctx: a recarray of length N
    :param poes: an array of probabilities of length N
    :param tom:
        temporal occurrence model if the rupture is parametric,
        list of N probability mass functions otherwise
    """
    pnes = numpy.zeros_like(poes)
    if isinstance(probs_or_tom, FatedTOM):
        for i, rate in enumerate(ctx.occurrence_rate):
            pnes[i] = probs_or_tom.get_probability_no_exceedance(rate, poes[i])
    elif isinstance(probs_or_tom, PoissonTOM):
        calc_pnes(ctx.occurrence_rate, poes, probs_or_tom.time_span, pnes)
    else:  # nonpoissonian
        for i, probs_occur in enumerate(probs_or_tom):
            set_probability_no_exceedance_np(probs_occur, poes[i], pnes[i])
    return pnes


@compile(["(float64[:], float64[:,:], float64[:,:])",
          "(float64[:], float64[:,:,:,:], float64[:,:,:,:])"])
def set_probability_no_exceedance_np(probs_occur, poes, pnes):
    """
    :param probs_occur: an array of probabilities
    :param poes: an array of PoEs
    :paran pnes: set an array of PNEs computed as ∑ p(k|T) * p(X<x|rup)^k
    """
    # Uses the formula
    #
    #    ∑ p(k|T) * p(X<x|rup)^k
    #
    # where `p(k|T)` is the probability that the rupture occurs k times
    # in the time span `T`, `p(X<x|rup)` is the probability that a
    # rupture occurrence does not cause a ground motion exceedance, and
    # the summation `∑` is done over the number of occurrences `k`.
    #
    # `p(k|T)` is given by the attribute probs_occur and
    # `p(X<x|rup)` is computed as ``1 - poes``.
    arr = numpy.full_like(poes, probs_occur[0])
    for p, v in enumerate(probs_occur[1:], 1):
        arr += v * (1 - poes) ** p
    pnes[:] = numpy.clip(arr, 0., 1.)  # avoid numeric issues
