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
from openquake.baselib.performance import compile
from openquake._unc.bins import get_bins_data, get_bins_from_params

TOLERANCE = 1e-6


def get_pmf(vals: np.ndarray, wei: np.ndarray = None, res: int = 10,
            scaling: str = None):
    """
    Returns a probability mass funtion from a set of values plus the bins data.

    :param vals:
        An instance of :class:`numpy.ndarray` with the values to use for the
        calculation of the PMF
    :param wei:
        An instance of :class:`numpy.ndarray` with the same cardinality of
        `vals`
    :param res:
        Resolution (i.e. number of bins per logaritmic interval)
    :param scaling:
        The way in which the resolution scales per each order of magnitude.
    """
    # Compute weights is not provided
    wei = wei if wei is not None else np.ones_like(vals) * 1. / len(vals)

    # Compute bins data and bins
    min_power, num_powers = get_bins_data(vals)
    bins = get_bins_from_params(min_power, res, num_powers)

    # Compute the histogram
    his, _ = np.histogram(vals, bins=bins, weights=wei)
    assert len(his) == num_powers * res

    return min_power, num_powers, his


# TODO: do we need this to be done in numba? it looks like a no to me
# @compile("(f8[:],f8[:],f8[:],f8[:])")
def _get_vals(pmfa, pmfb, midsa, midsb):
    # Outputs
    yvals = np.zeros(len(pmfa) * len(pmfb))
    xvals = np.zeros_like(yvals)
    cnt = 0
    for i, a in enumerate(pmfa):
        for j, b in enumerate(pmfb):
            xvals[cnt] = midsa[i] + midsb[j]
            yvals[cnt] = a * b
            cnt += 1
    xvals = xvals[:cnt+1]
    yvals = yvals[:cnt+1]
    return xvals, yvals


# TODO: introduce a histogram object with 4 attributes
# ASK: I was expecting a call to scipy.signal.convolve?
def conv(pmfa, min_power_a, res_a, num_powers_a,
         pmfb, min_power_b, res_b, num_powers_b, res=None):
    """
    Computing the convolution of two histograms.

    :param pmfa: PMF of the first histogram
    :param min_power_a: minimim power of the first histogram
    :param res_a: resolution of the first histogram
    :param num_powers_a: number of powers of the first histogram
    :param pmfb: PMF of the second histogram
    :param min_power_b: minimim power of the second histogram
    :param res_b: resolution of the second histogram
    :param num_powers_b: number of powers of the second histogram
    :returns:
        min_power_o, res, num_powers_o, pmfo
    """
    # Checking input
    num = num_powers_a*res_a
    if len(pmfa) != num:
        fmt = '|pmfa| {:d} ≠ (number of powers * resolution) {:d}*{:d}={:d}'
        msg = fmt.format(len(pmfa), num_powers_a, res_a, num)
        raise ValueError(msg)

    # Checking input
    num = num_powers_b*res_b
    if len(pmfb) != num:
        fmt = '|pmfb| {:d} ≠ (number of powers * resolution) {:d}*{:d}={:d}'
        msg = fmt.format(len(pmfb), num_powers_b, res_b, int(num))
        raise ValueError(msg)

    # Checking input
    if np.abs(1.0 - np.sum(pmfa)) > TOLERANCE and len(pmfa):
        smm = np.sum(pmfa)
        raise ValueError(f'Sum of elements pmfa not equal to 1 {smm:8.4e}')
    if np.abs(1.0 - np.sum(pmfb)) > TOLERANCE and len(pmfb):
        smm = np.sum(pmfb)
        raise ValueError(f'Sum of elements pmfb not equal to 1 {smm:8.4e}')

    # Defining the resolution of output
    if res is None:
        res = np.amin([res_a, res_b])

    # Compute bin data and bins for output
    vmin = np.floor(np.log10(10**min_power_a + 10**min_power_b))
    vmax = np.ceil(np.log10(10**(min_power_a + num_powers_a) +
                            10**(min_power_b + num_powers_b)))
    min_power_o = int(vmin)
    num_powers_o = int(vmax - vmin)
    bins_o = get_bins_from_params(min_power_o, res, num_powers_o)

    # Compute mid points
    bins_a = get_bins_from_params(min_power_a, res_a, num_powers_a)
    bins_b = get_bins_from_params(min_power_b, res_b, num_powers_b)
    midsa = bins_a[:-1] + np.diff(bins_a)/2
    midsb = bins_b[:-1] + np.diff(bins_b)/2

    xvals, yvals = _get_vals(pmfa, pmfb, midsa, midsb)
    idxs = np.digitize(xvals, bins_o)
    idxs -= 1
    pmfo = np.zeros(len(bins_o) - 1, dtype=np.float64)
    for i in np.unique(idxs):
        pmfo[i] = np.sum(yvals[idxs == i])
        msg = "The sum of pmfo is {:f}".format(sum(pmfo))

    assert len(pmfo) == res * num_powers_o

    assert np.abs(1.0 - np.sum(pmfo)) < TOLERANCE

    return min_power_o, res, num_powers_o, pmfo
