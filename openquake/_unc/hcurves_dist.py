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

import numpy as np
from openquake._unc.bins import get_bins_from_params
from openquake._unc.utils import weighted_percentile


def to_matrix(his: list, minp: np.ndarray, nump: np.ndarray) -> np.ndarray:
    """
    Convert the hazard curves distribution into a matrix
    """
    nump = np.array(nump, dtype=float)
    idx = np.array(np.where(np.isfinite(nump)), dtype=int)[0]
    # Find the number of samples per power
    samples = int(len(his[idx[0]])/nump[idx[0]])
    # samples = int(len(his[0])/nump[0])
    maxp = np.empty_like(minp)

    maxp[idx] = minp[idx] + nump[idx]
    mrange = int(np.amax(maxp[idx]) - np.amin(minp[idx]))
    mtx = np.empty((mrange*samples, len(his))) * np.nan
    for i in idx:
        i0 = int((minp[i] - min(minp[idx])) * samples)
        i1 = int(i0 + nump[i] * samples)
        mtx[i0:i1, i] = his[i]
    afes = 10**np.linspace(np.amin(minp[idx]), np.amax(maxp[idx]),
                           mrange*samples)
    return mtx, afes


def get_stats(result_types, hiss, minp, nump):
    """
    :param result_types:
        A list with the values of the percentiles. For -1 we compute the mean.
        Example: with [-1, 0.50, 0.84] we return mean, median and 84th
        percentile
    :returns:
        A tuple with two :class:`numpy.ndarray` instances. The first one
        contains the requested results (one for each column) the second one
        includes the indexes of the original list provided with finite values.
    """
    out = []
    nump = np.array(nump, dtype=float)
    idx = np.array(np.where(np.isfinite(nump)), dtype=int)[0]
    res = int(len(hiss[idx[0]]) / nump[idx[0]])
    for i in idx:
        his = hiss[i]
        mpow = minp[i]
        npow = nump[i]
        bins = get_bins_from_params(mpow, res, npow)
        mids = bins[:-1] + np.diff(bins) / 2
        tmp = []
        for rty in result_types:
            if rty < 0:
                tmp.append(np.average(mids, weights=his))
            else:
                tmp.append(weighted_percentile(mids, weights=his, perc=rty))
        out.append(tmp)
    return np.array(out), idx
