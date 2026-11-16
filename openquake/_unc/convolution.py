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
from openquake.baselib import hdf5
from openquake._unc.bins import get_bins_from_params, get_bins_data
from openquake._unc.utils import weighted_percentile

TOLERANCE = 1e-6

class HistoGroup:
    """
    Positive-rate histograms with separate probability masses at zero.
    A None histogram represents a pure-zero distribution. Normalization
    includes both the positive bins and their corresponding zero mass.
 
    :param pmfs: list of histogram arrays (can contain None) 
    :param minpow: list of minimum powers (can contain None)
    :param numpow: list of number of powers (can contain None)
    :param normalized: if True, each complete distribution must sum to one
    :param res: optional resolution, also retained for all-zero groups
    :param mean_rates: optional means from original realization rates
    :param zero_mass: masses at zero, using the same units as the PMFs;
        defaults to one for None histograms and zero for positive PMFs
    """
    @classmethod
    def new(cls, afesRL: np.ndarray, weights: np.ndarray, res: int,
            rlzs=slice(None)):
        """
        Build positive-rate PMFs and explicit probability masses at zero.

        :param afesRL: realization rates with shape (R, L)
        :param weights: nonnegative realization weights
        :param res: number of bins per power of ten
        :param rlzs: indexes of the realizations to consider
        :returns: a HistoGroup with L histograms and original mean rates
        """
        afesRL = np.asarray(afesRL[rlzs], dtype=float)
        weights = np.asarray(weights[rlzs], dtype=float)
        if afesRL.ndim != 2 or weights.shape != (len(afesRL),):
            raise ValueError('Rates and weights must have compatible shapes')
        if np.any(~np.isfinite(afesRL)) or np.any(afesRL < 0):
            raise ValueError('Rates must be finite and nonnegative')
        if np.any(~np.isfinite(weights)) or np.any(weights < 0):
            raise ValueError('Weights must be finite and nonnegative')
        if len(weights):
            total = weights.sum(dtype=float)
            if not np.isfinite(total) or total <= 0:
                raise ValueError('Weights must have a finite, positive sum')
            weights = weights / total
        mean_rates = np.sum(afesRL * weights[:, None], axis=0, dtype=float)

        # Loop over the rates computed for each intensity measure level.
        ohis, min_powers, num_powers, zero_mass = [], [], [], []
        for dat in afesRL.T:
            positive = (dat > 0) & (weights > 0)
            zero_mass.append(weights[dat == 0].sum() if len(dat) else 1.)
            if not np.any(positive):
                ohis.append(None)
                min_powers.append(None)
                num_powers.append(None)
                continue

            # Computing bins and accumulating directly into each bin avoids
            # subtracting nearly equal cumulative weights for rare branches.
            values = dat[positive]
            min_power, num_power = get_bins_data(values)
            bins = get_bins_from_params(min_power, res, num_power)
            ohis.append(_histogram(values, weights[positive], bins))
            min_powers.append(min_power)
            num_powers.append(num_power)

        return cls(ohis, min_powers, num_powers, res=res,
                   mean_rates=mean_rates, zero_mass=zero_mass)

    def __init__(self, pmfs, minpow, numpow, weight=0, normalized=True,
                 res=None, mean_rates=None, zero_mass=None):
        assert len(pmfs) == len(minpow) == len(numpow)
        pmfs = [None if pmf is None else np.asarray(pmf, dtype=float)
                for pmf in pmfs]
        self.idxs, = np.where([pmf is not None for pmf in pmfs])
        # all histograms must have the same resolution
        if len(self.idxs) and res is None:
            i = self.idxs[0]
            res = len(pmfs[i]) // int(numpow[i])
        self.res = res
        for i in self.idxs:
            assert len(pmfs[i]) / numpow[i] == self.res
        self.pmfs = pmfs
        self.minpow = minpow
        self.numpow = numpow
        self.normalized = normalized
        self.weight = weight
        if zero_mass is None:
            zero_mass = [1. if pmf is None else 0. for pmf in pmfs]
        self.zero_mass = np.asarray(zero_mass, dtype=float)
        if (self.zero_mass.shape != (len(pmfs),) or
                np.any(~np.isfinite(self.zero_mass)) or
                np.any(self.zero_mass < 0)):
            raise ValueError('Zero masses must be finite and nonnegative')
        if mean_rates is None and not len(self.idxs):
            mean_rates = np.zeros(len(pmfs))
        self.mean_rates = (None if mean_rates is None else
                           np.asarray(mean_rates, dtype=float))
        if (self.mean_rates is not None and
                self.mean_rates.shape != (len(pmfs),)):
            raise ValueError('Mean rates must have one value per histogram')
        for pmf, zero in zip(pmfs, self.zero_mass):
            if pmf is not None and (pmf.ndim != 1 or
                    np.any(~np.isfinite(pmf)) or np.any(pmf < 0)):
                raise ValueError('PMF masses must be finite and nonnegative')
            total = zero + (0. if pmf is None else pmf.sum(dtype=float))
            if normalized and abs(1. - total) > TOLERANCE:
                raise ValueError(f'Sum not equal to 1 {total:8.4e}')

    def __imul__(self, other):
        return self * other

    def __mul__(histo_a, histo_b):
        """Convolve distributions, including their masses at zero."""
        n = len(histo_a.pmfs)
        assert len(histo_b.pmfs) == n
        out1, out2, out3, zero_mass = [], [], [], []
        for i in range(n):
            h = conv(histo_a.pmfs[i], histo_a.minpow[i], histo_a.numpow[i],
                     histo_b.pmfs[i], histo_b.minpow[i], histo_b.numpow[i],
                     histo_a.zero_mass[i], histo_b.zero_mass[i])
            out1.append(h.pmfs[0])
            out2.append(h.minpow[0])
            out3.append(h.numpow[0])
            zero_mass.append(h.zero_mass[0])

        mean_rates = None
        if histo_a.mean_rates is not None and histo_b.mean_rates is not None:
            mean_rates = histo_a.mean_rates + histo_b.mean_rates
        # Infer resolution from positive bins; a pure zero has no bin scale.
        res = None if any(pmf is not None for pmf in out1) else (
            histo_a.res or histo_b.res)
        return HistoGroup(out1, out2, out3, histo_a.weight + histo_b.weight,
                          res=res, mean_rates=mean_rates, zero_mass=zero_mass)

    # tested in test_m_convolution
    def to_matrix(self):
        """
        Convert the hazard curves distribution into a matrix and afes
        """
        if not len(self.idxs):
            return np.empty((0, len(self.pmfs))), np.empty(0)
        minpow = np.array(self.minpow, dtype=float)
        nump = np.array(self.numpow, dtype=float)
        idx, = np.where(np.isfinite(nump))
        minp = minpow[idx].min()
        maxp = (minpow[idx] + nump[idx]).max()
        n = int(maxp - minp) * self.res
        mat = np.full((n, len(self.pmfs)), np.nan)
        for i in idx:
            i0 = int(minpow[i] - minp) * self.res
            i1 = i0 + int(nump[i]) * self.res
            mat[i0:i1, i] = self.pmfs[i]
        afes = 10**np.linspace(minp, maxp, n)
        return mat, afes

    def get_stats(self, result_types):
        """
        :param result_types:
            Example: with [-1, 0.50, 0.84] we return mean, median and 84th
            percentile for histograms that are not None. Means use original
            realization rates when available, otherwise bin midpoints.
            Percentiles include the point mass at zero and use bin midpoints
            for the positive part of the distribution.
        """
        out = []
        for i in self.idxs:
            his = self.pmfs[i]
            bins = get_bins_from_params(
                self.minpow[i], self.res, self.numpow[i])
            mids = bins[:-1] + np.diff(bins) / 2
            total = self.zero_mass[i] + his.sum(dtype=float)
            if total <= 0:
                raise ValueError('Histogram has no probability mass')
            tmp = []
            for rty in result_types:
                if rty == -1:  # mean
                    if self.mean_rates is None:
                        tmp.append(np.dot(mids, his) / total)
                    else:
                        tmp.append(self.mean_rates[i])
                else:
                    tmp.append(_percentile(mids, his, self.zero_mass[i], rty))
            out.append(tmp)
        return np.array(out).reshape(len(self.idxs), len(result_types))

    def save(self, fname):
        """
        Save to a .hdf5 file. Positive-rate bins are stored in histograms;
        zero_mass stores the separate point mass at zero for every column.
        """
        mat, afes = self.to_matrix()
        with hdf5.File(fname, "w") as fout:
            fout.create_dataset("histograms", data=mat)
            fout.create_dataset("mininum_power",
                                data=np.array(self.minpow, dtype=float))
            fout.create_dataset("number_of_powers",
                                data=np.array(self.numpow, dtype=float))
            fout.create_dataset("afes", data=afes)
            fout.create_dataset("zero_mass", data=self.zero_mass)
            if self.mean_rates is not None:
                fout.create_dataset("mean_rates", data=self.mean_rates)


def conv(pmfa, min_power_a, num_powers_a, pmfb, min_power_b, num_powers_b,
         zero_a=None, zero_b=None):
    """
    Convolve positive-rate histograms and optional masses at zero.

    Inputs are normalized including their zero masses. None represents a
    pure zero distribution. The positive-positive, zero-positive and
    positive-zero combinations all contribute to the output positive PMF.

    :param pmfa: positive-bin masses of the first histogram, or None
    :param min_power_a: minimum power of ten for the first histogram
    :param num_powers_a: number of powers spanned by the first histogram
    :param pmfb: positive-bin masses of the second histogram, or None
    :param min_power_b: minimum power of ten for the second histogram
    :param num_powers_b: number of powers spanned by the second histogram
    :param zero_a: first zero mass; defaults to one for None, otherwise zero
    :param zero_b: second zero mass; defaults to one for None, otherwise zero
    :returns: a HistoGroup containing the sum distribution
    """
    za = (1. if pmfa is None else 0.) if zero_a is None else zero_a
    zb = (1. if pmfb is None else 0.) if zero_b is None else zero_b
    h = HistoGroup([pmfa, pmfb], [min_power_a, min_power_b],
                   [num_powers_a, num_powers_b], normalized=False,
                   zero_mass=[za, zb])
    values_a, weights_a = _support(h, 0)
    values_b, weights_b = _support(h, 1)
    xvals = np.add.outer(values_a, values_b).ravel()
    yvals = np.multiply.outer(weights_a, weights_b).ravel()
    zero_mass = yvals[xvals == 0].sum(dtype=float)
    positive = (xvals > 0) & (yvals > 0)
    if not np.any(positive):
        return HistoGroup([None], [None], [None], res=h.res,
                          zero_mass=[zero_mass])

    # Compute bins for the occupied positive support and accumulate masses.
    values = xvals[positive]
    minp, nump = get_bins_data(values)
    bins = get_bins_from_params(minp, h.res, nump)
    pmfo = _histogram(values, yvals[positive], bins)
    return HistoGroup([pmfo], [minp], [nump], zero_mass=[zero_mass])


def _histogram(values, weights, bins):
    # Accumulate each bin directly in float64, including the rightmost edge.
    indexes = np.searchsorted(bins, values, side='right') - 1
    indexes = np.clip(indexes, 0, len(bins) - 2)
    return np.bincount(indexes, weights=np.asarray(weights, dtype=float),
                       minlength=len(bins) - 1)


def _support(histo, i):
    # Only occupied bins enter the outer product; zero has its own atom.
    pmf = histo.pmfs[i]
    total = histo.zero_mass[i] + (0. if pmf is None else pmf.sum(dtype=float))
    if total <= 0:
        raise ValueError('Histogram has no probability mass')
    values, weights = np.array([0.]), np.array([histo.zero_mass[i]])
    if pmf is not None:
        bins = get_bins_from_params(
            histo.minpow[i], histo.res, histo.numpow[i])
        mids = bins[:-1] + np.diff(bins) / 2
        occupied = pmf > 0
        values = np.concatenate([values, mids[occupied]])
        weights = np.concatenate([weights, pmf[occupied]])
    occupied = weights > 0
    return values[occupied], weights[occupied] / total


def _percentile(mids, pmf, zero_mass, perc):
    # Respect the CDF jump at zero, then use the positive conditional CDF.
    if not 0 <= perc <= 1:
        raise ValueError('Percentile must be in [0, 1]')
    positive_mass = pmf.sum(dtype=float)
    if perc == 1 and positive_mass > 0:
        return weighted_percentile(mids, pmf, 1.)
    total = zero_mass + positive_mass
    if zero_mass > 0 and perc * total <= zero_mass:
        return 0.
    quantile = np.clip((perc * total - zero_mass) / positive_mass, 0., 1.)
    return weighted_percentile(mids, pmf, quantile)
