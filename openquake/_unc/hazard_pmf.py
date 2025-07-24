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
"""
We use a hazard PMF to store the results of a number of a hazard curves
representing a set of realisations admitted by a logic tree for a single
IMT.

For the description of a PMF we use:
    - A numpy vector (cardinality: L = number of IMLs)
    - A numpy array (cardinality: L x |number of bins|) containing the annual
      frequencies of exceeedance
"""

import numpy as np
from openquake._unc.bins import get_bins_data, get_bins_from_params
from openquake._unc.convolution import HistoGroup

TOLERANCE = 1e-6


def get_md_from_2d(poes, shapes, idxs):
    """
    Reshape the array containing the results of a MD disaggregation analysis.

    :param poes:
        The MD disaggregation matrix for a given site, imt and iml. This is
        a 1d array.
    :returns:
        An array with the same information that can be used in the
        convolution
    """
    cnt = 0
    counter = 0
    out = np.zeros(shapes)
    for imag in range(shapes[0]):
        for idst in range(shapes[1]):
            if cnt in idxs:
                out[imag, idst] = poes[counter]
                counter += 1
            cnt += 1
    return out


def get_2d_from_md(poes):
    """
    Reshape the array containing the results of a MD disaggregation analysis.

    :param poes:
        The mde disaggregation matrix for a gives site, imt and iml. This is
        a 3d array.
    :returns:
        A 2d array with the same information that can be used in the
        convolution
    """
    num_rlzs = poes.shape[-1]
    num_rows = int(poes.size/num_rlzs)
    out = np.zeros((num_rlzs, num_rows))
    cnt = 0
    for imag in range(poes.shape[0]):
        for idst in range(poes.shape[1]):
            out[:, cnt] = poes[imag, idst, :]
            cnt += 1
    return out


def get_2d_from_mde(poes):
    """
    Reshape the array containing the results of a MDe disaggregation analysis.

    :param poes:
        The mde disaggregation matrix for a gives site, imt and iml. This is
        a 4 array.
    :returns:
        A 2d array with the same information that can be used in the
        convolution
    """
    num_rlzs = poes.shape[-1]
    num_rows = int(poes.size/num_rlzs)
    out = np.zeros((num_rlzs, num_rows))
    cnt = 0
    for imag in range(poes.shape[0]):
        for idst in range(poes.shape[1]):
            for ieps in range(poes.shape[2]):
                out[:, cnt] = poes[imag, idst, ieps, :]
                cnt += 1
    return out


def afes_matrix_from_dstore(dstore, imtstr: str, atype: str, info: bool=False,
                            rlzs=slice(None)):
    """
    Pulls from the datastore the afes matrix for a given IMT (we assume the
    dstore contains only 1 site)

    :param dstore:
        The datastore containing the information
    :param imtstr:
        A string specifying the intensity measure type of interest
    :param info:
        A boolean controlling the amont of information provided
    :param rlzs:
        [optional] the indexes of the realisations to read
    :returns:
        A triple with the intensity measure levels, the annual frequencies of
        exceedance and the weights of the realisations.
    """
    # Intensity measure levels
    oqp = dstore['oqparam']
    imls = oqp.hazard_imtls[imtstr]

    # Index of the selected IMT
    imt_idx = list(oqp.hazard_imtls).index(imtstr)

    # Poes
    if atype == 'hcurves':
        poes = dstore['hcurves-rlzs'][0, rlzs, imt_idx, :]
    elif atype == 'mde':
        # Number of sites
        # Number of IMTs
        # Number of IMLs disaggregated
        # Number of magnitudes
        # Number of distances
        # Number of epsilons
        # Number of realisations
        poes = dstore['disagg-rlzs/Mag_Dist_Eps'][
            0, imt_idx, 0, :, :, :, rlzs]
        poes = get_2d_from_mde(poes)
    elif atype == 'md':
        # The shape of the final `poes` is: R X A where R is the number of
        # realizations and A is the number of the annual frequencies of
        # exceedance
        poes = dstore['disagg-rlzs/Mag_Dist'][0, :, :, imt_idx, 0, rlzs]
        poes = get_2d_from_md(poes)
        assert len(rlzs) == poes.shape[0]
    elif atype == 'm':
        poes = dstore['disagg-rlzs/Mag'][0, :, imt_idx, 0, rlzs].T
        # shape (R, Ma) i.e. (6, 17) in test_m_correlation
    else:
        raise ValueError(f'Unsupported atype: {atype}')

    poes[poes > 0.99999] = 0.99999
    afes = -np.log(1.-poes)/oqp.investigation_time

    # Weights
    weights = dstore.getitem('weights')[:]
    if atype in ['mde', 'md', 'm']:
        rmap = dstore['best_rlzs'][0]
        weights = weights[rmap][rlzs]
    else:
        weights = weights[rlzs]

    if info:
        len_description = 30
        tmps = 'Investigation time'.ljust(len_description)
        print('{:s}: {:f}'.format(tmps, oqp.investigation_time))
        tmps = 'IMT'.ljust(len_description)
        print('{:s}: {:s}'.format(tmps, imtstr))
        tmps = 'Number of realizations'.ljust(len_description)
        print('{:s}: {:d}'.format(tmps, len(poes)))

    return imls, afes, weights


def get_histograms(afes_mtx: np.ndarray,  weights: np.ndarray, res: int,
                   rlzs=slice(None)):
    """
    Computes the PMFs of the AfE for each intensity measure level

    :param afes_mtx:
        A 2D :class:`numpy.ndarray` instance
    :param weights:
        The weights for the realisations
    :param res:
        The number of samples per each power of 10
    :param rlzs:
        Indexes of the realisations to consider
    :returns:
        A tuple with three lists. The first list contains the histograms
        for all the intensity measure levels. The second list contains the
        first integer (a multiple of 10) defining the lower edge of the first
        bin of the histogram. The second list contains integers defining the
        range covered by the histogram (i.e. number of powers of 10).
    """
    afes_mtx = afes_mtx[rlzs, :]
    weights = weights[rlzs]

    # Loop over each column of afes_mtx i.e. each set of afes computed for a
    # given intensity level
    ohis = []
    min_powers = []
    num_powers = []
    for i in range(afes_mtx.shape[1]):
        dat = np.array(afes_mtx[:, i])
        if not np.any(dat > 1e-20):
            ohis.append(None)
            min_powers.append(None)
            num_powers.append(None)
            continue

        # Computing bins
        min_power, num_power = get_bins_data(dat)
        bins = get_bins_from_params(min_power, res, num_powers=num_power)

        # Computing histogram
        his, _ = np.histogram(dat, bins, weights=weights)
        his = his / np.sum(his)

        # Checking
        computed = np.sum(his)
        assert len(his) == num_power*res
        msg = f'Computed value {computed}'
        assert np.abs(computed - 1.0) < 1e-6, msg

        # Updating output
        ohis.append(his)
        min_powers.append(int(min_power))
        num_powers.append(int(num_power))

    return HistoGroup(ohis, min_powers, num_powers)


def mixture(results: list[HistoGroup]) -> HistoGroup:
    """
    Given a list of HistoGroup this computes a mixture distribution
    corresponding to a weighted sum of the inputs.

    :param results:
        It's a list of HistoGroup. The number of elements is equal to the
        number of correlated groups
    :returns:
        Not normalized HistoGroup
    """
    resolution = results[0].res  # all equal resolutions
    num_imls = len(results[0].pmfs)  # all equal lenghts

    # The minimum power is IMT dependent
    minpow = np.full(num_imls, np.nan)
    maxpow = np.full(num_imls, np.nan)
    for i, res in enumerate(results):

        minp = np.array(res.minpow, dtype=float)
        nump = np.array(res.numpow, dtype=float)
        ok = ~np.isnan(minp)

        if i == 0:
            minpow[ok] = minp[ok]
            maxpow[ok] = nump[ok] + minp[ok]
        else:
            minpow[ok] = np.minimum(minpow[ok], minp[ok])
            maxpow[ok] = np.maximum(maxpow[ok], minp[ok] + nump[ok])

    ok = ~np.isnan(minpow)
    maxrange = minpow.copy()
    maxrange[ok] = maxpow[ok] - minpow[ok]

    # Create output. For each IML we create the mixture PMF as a weighted sum
    # of the two original PMFs. In the case of disaggregation the number of
    # imls `num_imls` corresponds to the number of cells (i.e. the number of
    # M-R combinations)
    olst = [None] * num_imls
    for i_iml in np.where(ok)[0]:

        out = np.zeros(int(resolution * maxrange[i_iml]))
        tot_wei = 0.0
        for j, res in enumerate(results):

            # Skipping this IML if the maxrange is nan
            if np.isnan(maxrange[i_iml]):
                break

            # Skipping this realization if the lower limit is None
            if res.minpow[i_iml] is None:
                continue

            # Find where to add the current PMF
            low = int(resolution * (res.minpow[i_iml] - minpow[i_iml]))
            upp = int(low + resolution *  res.numpow[i_iml])

            # Sum the PMF
            out[low:upp] += res.pmfs[i_iml] * res.weight
            tot_wei += res.weight

        chk = np.sum(out) / tot_wei
        msg = f'Wrong PMF. Elements do not sum to 1 ({chk:8.6e})'
        assert np.all(np.abs(chk-1.0) < TOLERANCE), msg
        olst[i_iml] = out

    return HistoGroup(olst, minpow, maxrange, normalized=False)
