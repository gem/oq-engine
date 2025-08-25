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
from openquake.baselib import hdf5
from openquake._unc.bins import get_bins_from_params, get_bins_data
from openquake._unc.utils import weighted_percentile

TOLERANCE = 1e-6

class HistoGroup:
    """
    A container of histograms (some of them can be None).
 
    :param pmfs: list of histogram arrays (can contain None) 
    :param minpow: list of minimum powers (can contain None)
    :param numpow: list of number of powers (can contain None)
    :param normalized: if True, each histogram must be normalized
    """
    @classmethod
    def new(cls, afesRL: np.ndarray,  weights: np.ndarray, res: int,
            rlzs=slice(None)):
        """
        Computes the PMFs of the AfE for each intensity measure level

        :param afesRL:
            A 2D :class:`numpy.ndarray` instance of shape (R, L)
        :param weights:
            The weights for the realisations
        :param res:
            The number of samples per each power of 10
        :param rlzs:
            Indexes of the realisations to consider
        :returns:
            A HistoGroup instance with L histograms of R elements each
        """
        afesRL = afesRL[rlzs]
        weights = weights[rlzs]

        # Loop over each column of afesRL i.e. each set of afes computed for a
        # given intensity level
        ohis = []
        min_powers = []
        num_powers = []
        for lvl in range(afesRL.shape[1]):
            dat = afesRL[:, lvl]
            if not np.any(dat > 1e-20):
                ohis.append(None)
                min_powers.append(None)
                num_powers.append(None)
                continue

            # Computing bins
            min_power, num_power = get_bins_data(dat)
            bins = get_bins_from_params(min_power, res, num_power)

            # Computing histogram
            his, _ = np.histogram(dat, bins, weights=weights)
            his /= his.sum()  # with numpy 2 we could use normed = True

            # Updating output
            ohis.append(his)
            min_powers.append(min_power)
            num_powers.append(num_power)

        return cls(ohis, min_powers, num_powers)

    def __init__(self, pmfs, minpow, numpow, weight=0, normalized=True):
        assert len(pmfs) == len(minpow) == len(numpow)
        self.idxs, = np.where([pmf is not None for pmf in pmfs])
        # all histograms must have the same resolution
        i, *idx = self.idxs
        self.res = len(pmfs[i]) // int(numpow[i])
        for i in idx:
            assert len(pmfs[i]) / numpow[i] == self.res
        self.pmfs = pmfs
        self.minpow = minpow
        self.numpow = numpow
        self.normalized = normalized
        self.weight = weight
        for pmf, minp, nump in zip(pmfs, minpow, numpow):
            if normalized and pmf is not None and np.abs(
                    1.0 - np.sum(pmf)) > TOLERANCE:
                smm = np.sum(pmf)
                raise ValueError(f'Sum not equal to 1 {smm:8.4e}')

    def __imul__(self, other):
        return self * other

    def __mul__(histo_a, histo_b):
        """
        Implements the convolution product of histograms
        """
        n = len(histo_a.pmfs)
        assert len(histo_b.pmfs) == n

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
                h = conv(ha, mpa, npa, hb, mpb, npb)
                min_power_o, num_powers_o, pmfo = (
                    h.minpow[0], h.numpow[0], h.pmfs[0])

            out1.append(pmfo)
            out2.append(min_power_o)
            out3.append(num_powers_o)

        return HistoGroup(out1, out2, out3, histo_a.weight + histo_b.weight)

    # tested in test_m_convolution
    def to_matrix(self):
        """
        Convert the hazard curves distribution into a matrix and afes
        """
        minpow = np.array(self.minpow, dtype=int)
        nump = np.array(self.numpow, dtype=float)
        idx, = np.where(np.isfinite(nump))
        minp = minpow[idx].min()
        maxp = (minpow[idx] + nump[idx]).max()
        n = int(maxp - minp) * self.res
        mat = np.full((n, len(self.pmfs)), np.nan)
        for i in idx:
            i0 = (minpow[i] - minp) * self.res
            i1 = i0 + int(nump[i]) * self.res
            mat[i0:i1, i] = self.pmfs[i]
        afes = 10**np.linspace(minp, maxp, n)
        return mat, afes

    def get_stats(self, result_types):
        """
        :param result_types:
            Example: with [-1, 0.50, 0.84] we return mean, median and 84th
            percentile for the mid points of the underlying bins (not None)
        """
        out = []
        for i in self.idxs:
            his = self.pmfs[i]
            bins = get_bins_from_params(
                self.minpow[i], self.res, self.numpow[i])
            mids = bins[:-1] + np.diff(bins) / 2
            tmp = []
            for rty in result_types:
                if rty == -1:  # mean
                    tmp.append(np.average(mids, weights=his))
                else:
                    tmp.append(weighted_percentile(mids, weights=his, perc=rty))
            out.append(tmp)
        return np.array(out)

    def save(self, fname):
        """
        Save to a .hdf5 file
        """
        mat, afes = self.to_matrix()
        with hdf5.File(fname, "w") as fout:
            fout.create_dataset("histograms", data=mat)
            fout.create_dataset("mininum_power", data=np.array(self.minpow))
            fout.create_dataset("number_of_powers", data=np.array(self.numpow))
            fout.create_dataset("afes", data=afes)


def conv(pmfa, min_power_a, num_powers_a, pmfb, min_power_b, num_powers_b):
    """
    Computing the convolution of two histograms.

    :param pmfa: PMF of the first histogram
    :param min_power_a: minimim power of the first histogram
    :param num_powers_a: number of powers of the first histogram
    :param pmfb: PMF of the second histogram
    :param min_power_b: minimim power of the second histogram
    :param num_powers_b: number of powers of the second histogram
    :returns:
        :class:`HistoGroup` instance with a single histogram
    """
    # Checking input
    h = HistoGroup([pmfa, pmfb], [min_power_a, min_power_b],
                   [num_powers_a, num_powers_b])

    # Compute bin data and bins for output
    vmin = np.floor(np.log10(10**min_power_a + 10**min_power_b))
    vmax = np.ceil(np.log10(10**(min_power_a + num_powers_a) +
                            10**(min_power_b + num_powers_b)))
    min_power_o = int(vmin)
    num_powers_o = int(vmax - vmin)
    bins_o = get_bins_from_params(min_power_o, h.res, num_powers_o)

    # Compute mid points
    bins_a = get_bins_from_params(min_power_a, h.res, num_powers_a)
    bins_b = get_bins_from_params(min_power_b, h.res, num_powers_b)
    midsa = bins_a[:-1] + np.diff(bins_a) / 2
    midsb = bins_b[:-1] + np.diff(bins_b) / 2

    xvals = np.add.outer(midsa, midsb).flatten()
    yvals = np.outer(pmfa, pmfb).flatten()
    idxs = np.digitize(xvals, bins_o) - 1
    pmfo = np.zeros(len(bins_o) - 1)
    for i in np.unique(idxs):
        pmfo[i] = yvals[idxs == i].sum()

    return HistoGroup([pmfo], [min_power_o], [num_powers_o])
