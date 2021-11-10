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
import numpy.matlib
from scipy import constants
from abc import ABC, abstractmethod
from openquake.hazardlib.imt import IMT


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


class BakerJayaram2008(CrossCorrelation):
    """
    Implements the correlation model of Baker and Jayaram published in 2008
    on Earthquake Spectra. This model works for GMRotI50.
    """
    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:

        from_per = from_imt.period
        to_per = to_imt.period

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


def get_correlation_mtx(corr_model: CrossCorrelation,
                        ref_imt: IMT, target_imts: list, num_sites):
    """
    :param corr_model:
        An instance of a correlation model
    :param ref_imt:
        An :class:`openquake.hazardlib.imt.IMT` instance
    :param target_imts:
        A list of the target imts of size M
    :param num_sites:
        The number of involved sites
    :returns:
        A matrix of shape [<number of IMTs>, <number of sites>]
    """
    corr = np.array([corr_model.get_correlation(ref_imt, imt)
                     for imt in target_imts])
    corr = np.matlib.repmat(np.squeeze(corr), num_sites, 1).T
    return corr


class GodaAtkinson2009(CrossCorrelation):
    """
    Implements the correlation model of Goda and Atkinson published in 2009
    https://pubs.geoscienceworld.org/ssa/bssa/article-abstract/99/5/3003/342221/Probabilistic-Characterization-of-Spatially
    """
    cache = {}  # periods -> correlation matrix

    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:
        # Goda and Atkinson (2009) correlation model, provided by Vitor

        if from_imt == to_imt:
            return 1

        T1 = from_imt.period or 0.05  # for PGA
        T2 = to_imt.period or 0.05  # for PGA

        Tmin = min(T1, T2)
        Tmax = max(T1, T2)
        ITmin = 1. if Tmin < 0.25 else 0.

        theta1 = 1.374
        theta2 = 5.586
        theta3 = 0.728

        angle = np.pi/2. - (theta1 + theta2 * ITmin * (Tmin / Tmax) ** theta3 *
                            np.log10(Tmin / 0.25)) * np.log10(Tmax / Tmin)
        delta = 1 + np.cos(-1.5 * np.log10(Tmin / Tmax))
        return (1. - np.cos(angle) + delta) / 3.

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

    def get_inter_eps(self, imts, num_events):
        """
        :param imts: a list of M intensity measure types
        :param num_events: the number of events to consider (E)
        :returns: a correlated matrix of epsilons of shape (M, E)

        NB: the user must specify the random seed first
        """
        corma = self._get_correlation_matrix(imts)
        return numpy.random.multivariate_normal(
            numpy.zeros(len(imts)), corma, num_events)
