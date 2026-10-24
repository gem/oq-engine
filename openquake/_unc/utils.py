# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2025-2026 GEM Foundation
#
#                `.......      `....     `..`...     `..`... `......
#                `..    `..  `..    `..  `..`. `..   `..     `..
#                `..    `..`..        `..`..`.. `..  `..     `..
#                `.......  `..        `..`..`..  `.. `..     `..
#                `..       `..        `..`..`..   `. `..     `..
#                `..         `..     `.. `..`..    `. ..     `..
#                `..           `....     `..`..      `..     `..
#
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding: utf-8

import numpy as np


def probabilities_to_rates(poes, investigation_time):
    """
    Convert Poisson exceedance probabilities to annual exceedance rates.

    Inputs are promoted to float64 before evaluating ``-log1p(-p) / T``.
    Probabilities must be finite and in [0, 1); an exact one implies an
    infinite rate and is rejected instead of being silently capped.
    The input array is not modified and its shape is preserved.

    :param poes: scalar or array of exceedance probabilities
    :param investigation_time: finite, positive investigation time in years
    :returns: float64 rates
    :raises ValueError: for invalid probabilities or investigation time
    """
    message = 'Investigation time must be finite and positive'
    if np.ndim(investigation_time) != 0:
        raise ValueError(message)
    try:
        investigation_time = float(investigation_time)
    except (TypeError, ValueError):
        raise ValueError(message) from None
    if not np.isfinite(investigation_time) or investigation_time <= 0:
        raise ValueError('Investigation time must be finite and positive')
    poes = np.asarray(poes, dtype=np.float64)
    if np.any(~np.isfinite(poes)) or np.any((poes < 0) | (poes > 1)):
        raise ValueError('Probabilities must be finite and in [0, 1]')
    if np.any(poes == 1):
        raise ValueError('A probability of 1 implies an infinite rate')
    return -np.log1p(-poes) / investigation_time


# NB: this will be obsolete in numpy 2+
def weighted_percentile(data, weights, perc):
    """
    Given a vector of values and one of associated weights computes the
    requested percentile.

    :param data:
        Vector with data
    :param weights:
        A vector of weights (same cardinality of data)
    :param perc:
        Percentile in [0-1]!
    :returns:
        A float with the value for a given percentile
    """
    ix = np.argsort(data)
    data = data[ix]  # sort data
    weights = weights[ix]  # sort weights
    # 'like' a CDF function
    cdf = (np.cumsum(weights) - 0.5 * weights) / np.sum(weights)
    return np.interp(perc, cdf, data)
