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


# This quantile convention interpolates between weighted CDF midpoints.
def weighted_percentile(data, weights, perc):
    """
    Given a vector of values and one of associated weights computes the
    requested percentile.
    Zero-weight entries are ignored and the CDF is accumulated in float64.

    :param data:
        Vector with data
    :param weights:
        A vector of weights (same cardinality of data)
    :param perc:
        Percentile in [0-1]!
    :returns:
        A float with the value for a given percentile
    """
    data = np.asarray(data, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if data.ndim != 1 or weights.shape != data.shape:
        raise ValueError('Data and weights must be matching vectors')
    if np.any(~np.isfinite(data)) or np.any(~np.isfinite(weights)):
        raise ValueError('Data and weights must be finite')
    if np.any(weights < 0) or not np.any(weights > 0):
        raise ValueError('Weights must be nonnegative with a positive sum')
    if (np.any(~np.isfinite(perc)) or
            np.any((np.asarray(perc) < 0) | (np.asarray(perc) > 1))):
        raise ValueError('Percentile must be in [0, 1]')
    # Zero-weight bins do not anchor the CDF or its endpoints.
    occupied = weights > 0
    data, weights = data[occupied], weights[occupied]
    ix = np.argsort(data)
    data, weights = data[ix], weights[ix]
    # Interpolate between weighted CDF midpoints, accumulated in float64.
    total = weights.sum(dtype=float)
    cdf = (np.cumsum(weights, dtype=float) - 0.5 * weights) / total
    return np.interp(perc, cdf, data)
