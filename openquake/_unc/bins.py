#
# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2025 GEM Foundation
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

SMALL = 1e-20


def get_bins_data(samples: np.ndarray):
    """
    Computes the lowest power of 10 and the number of powers of 10 needed to
    cover the values in the `samples` dataset.

    :param samples:
        A set of values for which we want to obtain the corresponding bins
    :returns:
        A tuple with two ints, the minimum power of 10 and the number of
        powers.
    """

    # If all the values are 0
    if np.all(np.abs(samples) < SMALL):
        return None, None

    # Fixing 0 values
    samples[samples < SMALL] = SMALL * 1.01

    # Find histogram params
    sam = samples[np.abs(samples) > SMALL]
    min_power = np.floor(np.log10(np.min(sam)))
    upv = np.ceil(np.log10(np.max(sam)))
    num_powers = upv - min_power

    return int(min_power), int(num_powers)


def get_bins_from_params(min_power: int, nsampl_per_power: int,
                         num_powers: int):
    """
    :param min_power:
        Lowest power i.e. 10^min_power corresponds to the left limit of the
        first bin of the histogram
    :param nsampl_per_power:
        The number of samples in each power
    :param num_powers:
        The range covered by the bins
    :returns:
        num_powers * nsampl_per_power + 1 bins
    """
    assert nsampl_per_power > 0
    assert num_powers > 0
    minp = int(min_power)
    nump = int(num_powers)
    res = int(nsampl_per_power)
    bins = np.logspace(minp, minp + nump,  nump*res + 1)
    return bins
