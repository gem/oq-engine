# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
from scipy import constants, stats
from abc import ABC, abstractmethod
from openquake.hazardlib.imt import IMT


# ############ CrossCorrelation for the conditional spectrum ############ #

class CrossCorrelation(ABC):
    # TODO We need to specify the HORIZONTAL GMM COMPONENT used
    @abstractmethod
    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:
        """
        :param from_imt:
            An intensity measure type
        :param to_imt:
            An intensity measure type
        :return: a scalar
        """

    def get_cross_correlation_mtx(self, imts: list) -> np.ndarray:
        """
        :param imts:
            A list of :class:`openquake.hazardlib.imt.IMT` instances
        :returns:
            A :class:`numpy.ndarray` instance with shape (|imts|, |imts|)
            containing the correlation coefficients between the IMTs provided
            in the input `imts` list.
        """
        num_imts = len(imts)
        mtx = np.zeros((num_imts, num_imts))
        for i1 in range(num_imts):
            for i2 in range(i1, num_imts):
                cor = self.get_correlation(imts[i1], imts[i2])
                mtx[i1, i2] = cor
                mtx[i2, i1] = cor
        return mtx


class BakerJayaram2008(CrossCorrelation):
    """
    Implements the correlation model of Baker and Jayaram published in 2008
    on Earthquake Spectra. This model works for GMRotI50.
    """
    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:

        from_per = from_imt.period
        to_per = to_imt.period

        if np.abs(from_per-to_per) < 1e-10:
            return 1.0

        t_min = np.min([from_per, to_per])
        t_max = np.max([from_per, to_per])

        c1 = 1 - np.cos(constants.pi/2 -
                        0.366 * np.log(t_max/np.max([t_min, 0.109])))
        c2 = 0.0
        if t_max < 0.2:
            term1 = 1.0 - 1.0/(1.0+np.exp(100.0*t_max-5.0))
            term2 = (t_max-t_min) / (t_max-0.0099)
            c2 = 1 - 0.105 * term1 * term2
        c3 = c1
        if t_max < 0.109:
            c3 = c2
        c4 = c1 + 0.5 * (np.sqrt(c3) - c3) * (
            1 + np.cos(constants.pi*t_min/0.109))
        if t_max < 0.109:
            corr = c2
        elif t_min > 0.109:
            corr = c1
        elif t_max < 0.2:
            corr = np.amin([c2, c4])
        else:
            corr = c4
        return corr  # a scalar


# ######################## CrossCorrelationBetween ########################## #

class CrossCorrelationBetween(ABC):
    def __init__(self, truncation_level=99.):
        if truncation_level < 1E-9:
            truncation_level = 1E-9
        self.truncation_level = truncation_level
        self.distribution = stats.truncnorm(-truncation_level,
                                            truncation_level)

    @abstractmethod
    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:
        """
        :param from_imt:
            An intensity measure type
        :param to_imt:
            An intensity measure type
        :return: a scalar
        """
    @abstractmethod
    def get_inter_eps(self, imts, num_events, rng):
        pass


class GodaAtkinson2009(CrossCorrelationBetween):
    """
    Implements the correlation model of Goda and Atkinson published in 2009.
    This is a correlation model for between-event residuals. See
    https://doi.org/10.1785/0120090007
    """
    cache = {}  # periods -> correlation matrix

    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:
        """
        :returns: a scalar in the range 0..1
        """
        if from_imt == to_imt:
            return 1.0

        T1 = from_imt.period or 0.05  # for PGA
        T2 = to_imt.period or 0.05  # for PGA

        Tmin = min(T1, T2)
        Tmax = max(T1, T2)
        ITmin = 1.0 if Tmin < 0.25 else 0.0

        theta1 = 1.374
        theta2 = 5.586
        theta3 = 0.728

        angle = np.pi/2.0 - (theta1 + theta2 * ITmin * (Tmin / Tmax) ** theta3 *
                            np.log10(Tmin / 0.25)) * np.log10(Tmax / Tmin)
        delta = 1.0 + np.cos(-1.5 * np.log10(Tmax / Tmin))
        corr = (1.0 - np.cos(angle) + delta) / 3.0
        return min(corr, 1.0)

    def get_inter_eps(self, imts, num_events, rng):
        """
        :param imts: a list of M intensity measure types
        :param num_events: the number of events to consider (E)
        :param rng: random number generator
        :returns: a correlated matrix of epsilons of shape (M, E)

        NB: the user must specify the random seed first
        """
        corma = self._get_correlation_matrix(imts)
        return rng.multivariate_normal(
            np.zeros(len(imts)), corma, num_events).T  # E, M -> M, E

    def _get_correlation_matrix(self, imts):
        # cached on the periods
        periods = tuple(imt.period for imt in imts)
        try:
            return self.cache[periods]
        except KeyError:
            self.cache[periods] = corma = np.zeros((len(imts), len(imts)))
        for i, imi in enumerate(imts):
            for j, imj in enumerate(imts):
                corma[i, j] = self.get_correlation(imi, imj)
        return corma


class Bradley2012(CrossCorrelationBetween):
    """
    Implements the correlation model for total residuals
    between Peak Ground Velocity and Spectrum-Based
    Intensity Measures from Bradley, B. A. (2012).
    'Empirical correlations between peak ground velocity
    and spectrum-based intensity measures.'
    Earthquake Spectra, 28(1), 17–35.
    https://doi.org/10.1193/1.3675582
    """
    cache = {}  # periods -> correlation matrix

    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:
        """
        :returns: a scalar in the range 0..1
        """

        if from_imt == to_imt:
            return 1
        if from_imt.string != 'PGV' and to_imt.string != 'PGV':
            return 0

        if from_imt.string == 'PGV':
            T = to_imt.period
        else:
            T = from_imt.period

        if T < 0.01:
            return 0.733
        elif T < 0.1:
            a = 0.73
            b = 0.54
            c = 0.045
            d = 1.8
        elif T < 0.75:
            a = 0.54
            b = 0.81
            c = 0.28
            d = 1.5
        elif T < 2.5:
            a = 0.80
            b = 0.76
            c = 1.1
            d = 3.0
        else:
            a = 0.76
            b = 0.70
            c = 5.0
            d = 3.2

        return ((a + b) / 2 - (a - b) / 2 * np.tanh(d * np.log(T / c)))

    def get_inter_eps(self, imts, num_events, rng):
        """
        :param imts: a list of M intensity measure types
        :param num_events: the number of events to consider (E)
        :param rng: random number generator
        :returns: a correlated matrix of epsilons of shape (M, E)

        NB: the user must specify the random seed first
        """
        corma = self._get_correlation_matrix(imts)
        return rng.multivariate_normal(
            np.zeros(len(imts)), corma, num_events).T  # E, M -> M, E

    def _get_correlation_matrix(self, imts):
        # cached on the periods
        periods = tuple(imt.period for imt in imts)
        try:
            return self.cache[periods]
        except KeyError:
            self.cache[periods] = corma = np.zeros((len(imts), len(imts)))
        for i, imi in enumerate(imts):
            for j, imj in enumerate(imts):
                corma[i, j] = self.get_correlation(imi, imj)
        return corma


class NoCrossCorrelation(CrossCorrelationBetween):
    """
    Used when there is no cross correlation
    """
    def get_correlation(self, from_imt, to_imt):
        return from_imt == to_imt

    def get_inter_eps(self, imts, num_events, rng):
        """
        :param imts: a list of M intensity measure types
        :param num_events: the number of events to consider (E)
        :param rng: random number generator
        :returns: an uncorrelated matrix of epsilons of shape (M, E)

        NB: the user must specify the random seed first
        """
        return np.array([
            self.distribution.rvs(num_events, rng) for imt in imts])


class FullCrossCorrelation(CrossCorrelationBetween):
    """
    Used when there is full cross correlation, i.e. same epsilons for all IMTs
    """
    def get_correlation(self, from_imt, to_imt):
        return 1.

    def get_inter_eps(self, imts, num_events, rng):
        """
        :param imts: a list of M intensity measure types
        :param num_events: the number of events to consider (E)
        :param rng: random number generator
        :returns:
            a matrix of epsilons of shape (M, E) with the same epsilons
            for each IMT

        NB: the user must specify the random seed first
        """
        eps = self.distribution.rvs(num_events, rng)
        return np.array([eps for imt in imts])
