# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
import toml
import numpy
import scipy.stats
from openquake.baselib.performance import compile

registry = {}
F64 = numpy.float64


class BaseTOM(object):
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

    def __init__(self, time_span):
        if time_span <= 0:
            raise ValueError('time_span must be positive')
        self.time_span = time_span

    def get_probability_one_or_more_occurrences(self):
        """
        Calculate and return the probability of event to happen one or more
        times within the time range defined by constructor's ``time_span``
        parameter value.
        """
        raise NotImplementedError

    def get_probability_n_occurrences(self):
        """
        Calculate the probability of occurrence of a number of events in the
        constructor's ``time_span``.
        """
        raise NotImplementedError

    def sample_number_of_occurrences(self, seeds=None):
        """
        Draw a random sample from the distribution and return a number
        of events to occur.

        The method uses the numpy random generator, which needs a seed
        in order to get reproducible results. If the seed is None, it
        should be set outside of this method.
        """

    def get_probability_no_exceedance(self):
        """
        Compute and return, for a number of ground motion levels and sites,
        the probability that a rupture with annual occurrence rate given by
        ``occurrence_rate`` and able to cause ground motion values higher than
        a given level at a site with probability ``poes``, does not cause any
        exceedance in the time window specified by the ``time_span`` parameter
        given in the constructor.
        """
        raise NotImplementedError

    def __str__(self):
        return toml.dumps({self.__class__.__name__: self.__dict__})


class FatedTOM(BaseTOM):

    def __init__(self, time_span):
        self.time_span = time_span

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


class ClusterPoissonTOM(PoissonTOM):
    """
    Poissonian temporal occurrence model with an occurrence rate
    """
    def __init__(self, time_span, occurrence_rate):
        self.time_span = time_span
        self.occurrence_rate = occurrence_rate


@compile(["(float64, float64[:], float64[:], float64)",
          "(float64, float64[:], float64[:,:,:], float64)"])
def get_pnes(rate, probs, poes, time_span):
    """
    :param rate: occurrence rate in case of a poissonian rupture
    :param probs: probabilities of occurrence in the nonpoissonian case
    :param poes: array of PoEs of shape 1D or 3D
    :param time_span: time span in the poissonian case (0. for FatedTOM)

    Fast way to return probabilities of no exceedence given an array
    of PoEs and some parameter.
    """
    # NB: the NegativeBinomialTOM creates probs_occur with a rate not NaN
    if time_span == 0.:  # FatedTOM
        return 1. - poes
    elif len(probs) == 0:  # poissonian
        return numpy.exp(- rate * time_span * poes)
    else:
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
        pnes = numpy.full(poes.shape, probs[0])
        for p, prob in enumerate(probs[1:], 1):
            pnes[:] += prob * (1 - poes) ** p
        return pnes.clip(0., 1.)  # avoid numeric issues


class NegativeBinomialTOM(BaseTOM):
    """
    Negative Binomial temporal occurrence model.
    """
    def __init__(self, time_span, mu, alpha):
        """
        :param time_span:
            The time interval of interest, in years.
        :param mu, alpha:
            (list/np.ndarray) Parameters of the negbinom temporal model, in
            form of mean rate/dispersion (μ / α)  Kagan and Jackson, (2010)

                                    k
                   Γ(τ + k)      μ           1
            f(k) = -------- . -------- . --------
                     Γ(τ)            k            1/α
                              (μ + τ)    (1 + μ/τ)

            where τ=1/α
        """

        super().__init__(time_span)
        self.mu = mu
        self.alpha = alpha
        if numpy.any(self.mu <= 0) or numpy.any(self.alpha <= 0):
            raise ValueError('Mean rate and rate dispersion must be greater '
                             'than 0')
        self.time_span = time_span

    def get_probability_one_or_more_occurrences(self, mean_rate=None):
        """

        :param mean_rate:
            The mean rate, or mean number of events per year
        :return:
            Float value between 0 and 1 inclusive.
        """
        if mean_rate is None:
            mean_rate = self.mu
        tau = 1 / self.alpha
        theta = tau / (tau + (mean_rate * self.time_span))

        return 1 - scipy.stats.nbinom.cdf(1, tau, theta)

    def get_probability_n_occurrences(self, num):
        """
        Calculate the probability of occurrence  of ``num`` events in the
        constructor's ``time_span``.

        :param num:
            Number of events
        :return:
            Probability of occurrence
        """
        tau = 1 / self.alpha
        theta = tau / (tau + (self.mu * self.time_span))

        return scipy.stats.nbinom.pmf(num, tau, theta)

    def sample_number_of_occurrences(self, mean_rate=None, seed=None):
        """
        Draw a random sample from the distribution and return a number
        of events to occur.

        The method uses the numpy random generator, which needs a seed
        in order to get reproducible results. If the seed is None, it
        should be set outside of this method.

        :param mean_rate:
            The mean rate, or mean number of events per year
        :param seed:
            Random number generator seed
        :return:
            Sampled integer number of events to occur within model's
            time span.
        """
        if mean_rate is None:
            mean_rate = self.mu

        tau = 1 / self.alpha
        theta = tau / (tau + (mean_rate * self.time_span))

        if isinstance(seed, int):
            numpy.random.seed(seed)

        return scipy.stats.nbinom.rvs(tau, theta)

    def get_pmf(self, mean_rate, tol=1-1e-14, n_max=None):
        """
        :param mean_rate:
            The average number of events per year.
        :param tol:
            Quantile value up to which calculate the pmf
        :returns:
            1D numpy array containing the probability mass distribution,
            up to tolerance level.
        """
        # Gets dispersion from source object
        alpha = self.alpha
        # Recovers NB2 parametrization (tau/theta or n,p in literature)
        tau = 1 / alpha
        theta = tau / (tau + numpy.array(mean_rate).flatten()*self.time_span)
        if not n_max:
            n_max = numpy.max(
                scipy.stats.nbinom.ppf(tol, tau, theta).astype(int))
            if n_max < 4:
                # minimum n_max for which the hazard equation is integrated,
                # to avoid precision issues for probabilities of occur (<1e-6)
                n_max = 4
        pmf = scipy.stats.nbinom.pmf(
            numpy.arange(0, n_max), tau, theta[:, None])
        return pmf

    def get_probability_no_exceedance(self, mean_rate, poes):
        """
        :param mean_rate:
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

        """

        # Gets dispersion from source object
        alpha = self.alpha
        # Recovers NB2 parametrization (tau/theta or n,p in literature)
        tau = 1 / alpha
        theta = tau / (tau + mean_rate*self.time_span)

        # Defines tol for the max quantile value, up to which the infinite series is calculated.
        tol = 1 - 1e-14

        n_max = scipy.stats.nbinom.ppf(tol, tau, theta)
        pdf = scipy.stats.nbinom.pmf(numpy.arange(0, n_max), tau, theta)
        poes_1 = 1 - poes
        prob_no_exceed = numpy.zeros(poes.shape)
        for k, prob in enumerate(pdf):
            prob_no_exceed += prob * numpy.power(poes_1, k)

        return prob_no_exceed

