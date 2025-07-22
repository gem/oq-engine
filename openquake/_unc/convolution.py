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
from openquake._unc.bins import get_bins_data, get_bins_from_params

TOLERANCE = 1e-6

class Histograms:
    """
    An histogram for each IMT.
 
    :param pmfs: Probability Mass Functions with L values
    :param minpow: L minimum powers
    :param numpow: L number of powers
    :param res: resolution
    """
    def __init__(self, pmfs, minpow, numpow, res):
        assert res
        assert len(pmfs) == len(minpow) == len(numpow)
        self.pmfs = pmfs
        self.minpow = minpow
        self.numpow = numpow
        self.res = res
        for pmf, minp, nump in zip(pmfs, minpow, numpow):
            if pmf is None:  # may happen in the convolution
                continue
            num = res * nump
            if len(pmf) != num:
                msg = ('|pmf| {:d} ≠ (number of powers * resolution) '
                       '{:d}*{:d}={:d}').format(len(pmf), nump, res, num)
                raise ValueError(msg)
            elif np.abs(1.0 - np.sum(pmf)) > TOLERANCE:
                smm = np.sum(pmf)
                raise ValueError(
                    f'Sum of elements pmfa not equal to 1 {smm:8.4e}')

    def __mul__(histo_a, histo_b):
        """
        Implements the convolution product of histograms
        """
        n = len(histo_a.pmfs)
        assert len(histo_b.pmfs) == n
        rea = histo_a.res
        reb = histo_b.res
        res = min(rea, reb)

        out1 = []
        out2 = []
        out3 = []
        for i in range(n):

            ha = histo_a.pmfs[i]
            npa = histo_a.numpow[i]
            mpa = histo_a.minpow[i]

            hb = histo_b.pmfs[i]
            npb = histo_b.numpow[i]
            mpb = histo_b.minpow[i]

            if ha is None and hb is None:
                min_power_o, num_powers_o, pmfo = None, None, None
            elif ha is None:
                min_power_o, num_powers_o, pmfo = mpb, npb, hb
            elif hb is None:
                min_power_o, num_powers_o, pmfo = mpa, npa, ha
            else:
                h = conv(ha, mpa, rea, npa, hb, mpb, reb, npb, res)
                min_power_o, num_powers_o, pmfo = \
                    h.minpow[0], h.numpow[0], h.pmfs[0]

            out1.append(pmfo)
            out2.append(min_power_o)
            out3.append(num_powers_o)

        # one histogram for each IMT considered, plenty of None
        return Histograms(out1, out2, out3, res)


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
    res = res or min(res_a, res_b)
    Histograms([pmfa, pmfb], [min_power_a, min_power_b],
               [num_powers_a, num_powers_b], res)

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
    midsa = bins_a[:-1] + np.diff(bins_a) / 2
    midsb = bins_b[:-1] + np.diff(bins_b) / 2

    xvals = np.add.outer(midsa, midsb).flatten()
    yvals = np.outer(pmfa, pmfb).flatten()
    idxs = np.digitize(xvals, bins_o) - 1
    pmfo = np.zeros(len(bins_o) - 1)
    for i in np.unique(idxs):
        pmfo[i] = yvals[idxs == i].sum()

    return Histograms([pmfo], [min_power_o], [num_powers_o], res)
