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
"""
We use a hazard PMF to store the results of a number of a hazard curves
representing a set of realisations admitted by a logic tree for a single
IMT.

For the description of a PMF we use:
    - A numpy vector (cardinality: L = number of IMLs)
    - A numpy array (cardinality: L x |number of bins|) containing the annual
      frequencies of exceeedance
"""
import copy
import numpy as np
from typing import Tuple
from collections.abc import Sequence
from openquake._unc.bins import get_bins_data, get_bins_from_params
from openquake._unc.utils import get_rlzs, get_rlz_hcs

TOLERANCE = 1e-6


def get_m_from_2d(poes, shapes, idxs=None):
    cnt = 0
    counter = 0
    out = np.empty((shapes))
    for imag in range(shapes[0]):
        if cnt in idxs:
            out[imag] = poes[counter]
            counter += 1
        cnt += 1
    return out


def get_md_from_2d(poes, shapes, idxs=None):
    cnt = 0
    counter = 0
    out = np.empty((shapes))
    for imag in range(shapes[0]):
        for idst in range(shapes[1]):
            if cnt in idxs:
                out[imag, idst] = poes[counter]
                counter += 1
            cnt += 1
    return out


def get_mde_from_2d(poes, shapes, idxs=None):
    cnt = 0
    counter = 0
    out = np.empty((shapes))
    for imag in range(shapes[0]):
        for idst in range(shapes[1]):
            if cnt in idxs:
                out[imag, idst] = poes[counter]
                counter += 1
            cnt += 1
    return out


def get_2d_from_m(poes):
    """
    Reshape the array containing the results of a M disaggregation analysis.

    :param poes:
        The m disaggregation matrix for a given site, imt and iml. This is
        a 1d array.
    :returns:
        An array with the same information that can be used in the
        convolution
    """
    num_rlzs = poes.shape[-1]
    num_rows = int(poes.size/num_rlzs)
    out = np.zeros((num_rlzs, num_rows))
    cnt = 0
    for imag in range(poes.shape[0]):
        out[:, cnt] = poes[imag, :]
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
                            idxs: list=[]):
    """
    Pulls from the datastore the afes matrix for a given IMT (we assume the
    dstore contains only 1 site)

    :param dstore:
        The datastore containing the information
    :param imtstr:
        A string specifying the intensity measure type of interest
    :param info:
        A boolean controlling the amont of information provided
    :param idxs:
        [optional] the indexes of the realisations to read
    :returns:
        A triple with the intensity measure levels, the annual frequencies of
        exceedance and the weights of the realisations.
    """

    # Indexes of the realisations
    if len(idxs) > 0:
        idxs = np.array(idxs, dtype=int)
    else:
        idxs = slice(None)

    # Intensity measure levels
    oqp = dstore['oqparam']
    imls = oqp.hazard_imtls[imtstr]

    # Index of the selected IMT
    imt_idx = list(oqp.hazard_imtls).index(imtstr)

    # Poes
    if atype == 'hcurves':
        poes = dstore.getitem('hcurves-rlzs')[0, idxs, imt_idx, :]
    elif atype == 'mde':
        # Number of sites
        # Number of IMTs
        # Number of IMLs disaggregated
        # Number of magnitudes
        # Number of distances
        # Number of epsilons
        # Number of realisations
        poes = dstore.getitem('disagg-rlzs/Mag_Dist_Eps')[
            0, imt_idx, 0, :, :, :, idxs]
        poes = get_2d_from_mde(poes)
    elif atype == 'md':
        # The shape of the final `poes` is: R X A where R is the number of
        # realizations and A is the number of the annual frequencies of
        # exceedance
        poes = dstore.getitem('disagg-rlzs/Mag_Dist')[0, :, :, imt_idx, 0, idxs]
        poes = get_2d_from_md(poes)
        assert len(idxs) == poes.shape[0]
    elif atype == 'm':
        poes = dstore.getitem('disagg-rlzs/Mag')[0, :, imt_idx, 0, idxs]
        poes = get_2d_from_m(poes)
    else:
        raise ValueError(f'Unsupported atype: {atype}')

    poes[poes > 0.99999] = 0.99999
    afes = -np.log(1.-poes)/oqp.investigation_time

    # Weights
    weights = dstore.getitem('weights')[:]
    if atype in ['mde', 'md', 'm']:
        rmap = dstore.get('best_rlzs', None)[:][0]
        weights = weights[rmap][idxs]
    else:
        weights = weights[idxs]

    if info:
        len_description = 30
        tmps = 'Investigation time'.ljust(len_description)
        print('{:s}: {:f}'.format(tmps, oqp.investigation_time))
        tmps = 'IMT'.ljust(len_description)
        print('{:s}: {:s}'.format(tmps, imtstr))
        tmps = 'Number of realizations'.ljust(len_description)
        print('{:s}: {:d}'.format(tmps, len(poes)))

    return imls, afes, weights


def afes_matrix_from_csv_files(fname: str, imtstr: str, info: bool = False,
                               idxs: list = []):
    """
    :param fname:
        The name of the folder containing the .csv files with prefix
        'hazard_curve-rlz' and the file with data on realizations
    :param imtstr:
        The string of the IMTs
    :param info:
        When true more info is prompted
    :param idxs:
        List of indexes with the realisations to be selected
    :returns:
        A tuple with a vector containing the imls values and a 2D vector with
        the set of afes for each IML. The cardinality of the second array is
        the number of realisations times the number of sites.
    """
    # The shape of poes: |realizations| x |number of imls| x |sites|
    _, _, poes, hea, imls, calc_id_a = get_rlz_hcs(fname, imtstr)

    # Indexes of the realisations
    if len(idxs) > 0:
        idxs = np.array(idxs, dtype=int)
    else:
        idxs = slice(None)

    poes = poes[idxs, :, :]

    # Information on the content of files
    if info:
        len_description = 30
        tmps = 'OQ version'.ljust(len_description)
        print('{:s}: {:s}'.format(tmps, hea['engine']))
        tmps = 'Investigation time'.ljust(len_description)
        print('{:s}: {:f}'.format(tmps, hea['investigation_time']))
        tmps = 'IMT'.ljust(len_description)
        print('{:s}: {:s}'.format(tmps, hea['imt']))
        tmps = 'Number of files'.ljust(len_description)
        print('{:s}: {:d}'.format(tmps, len(poes)))

    # Computing afes
    poes[poes > 0.99999] = 0.99999
    afes = -np.log(1.-poes)/hea['investigation_time']

    # Getting weights
    rlzs, calc_id = get_rlzs(fname)

    return imls, np.squeeze(afes), rlzs.weight.to_numpy()


def get_hazard_pmf(afes_mtx: np.ndarray, weights: np.ndarray = None,
                   samples: int = 30, idxs: np.ndarray = None):
    """
    :param afes_mtx:
        Annual frequency of exceedance matrix
    :param weights:
        Weights for the realisations included in the `afes_mtx`
    :param samples:
        The number of samples per each power of 10
    :param idxs:
        The indexes of the realizations to use
    """
    if idxs is not None:
        afes_mtx = afes_mtx[idxs, :]
        weights = weights[idxs]

    # Computing histograms
    his, min_powers, num_powers = get_histograms(afes_mtx, weights=weights,
                                                 res=samples)

    return his, min_powers, num_powers


def get_histograms(afes_mtx: np.ndarray,  weights: np.ndarray, res: int,
                   idxs: np.ndarray = None):
    """
    Computes the PMFs of the AfE for each intensity measure level

    :param afes_mtx:
        A 2D :class:`numpy.ndarray` instance
    :param weights:
        The weights for the realisations
    :param res:
        The number of samples per each power of 10
    :param idxs:
        Indexes of the realisations to consider
    :returns:
        A tuple with three lists. The first list contains the histograms
        for all the intensity measure levels. The second list contains the
        first integer (a multiple of 10) defining the lower edge of the first
        bin of the histogram. The second list contains integers defining the
        range covered by the histogram (i.e. number of powers of 10).
    """

    if idxs is not None:
        afes_mtx = afes_mtx[idxs, :]
        weights = weights[idxs]

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

    return ohis, min_powers, num_powers


def mixture(results: Sequence[list[list]],
            resolution: float) -> Tuple[list, list, list]:
    """
    Given a list of PMFs this computes for each IML a mixture distribution
    corresponding to a weighted sum of input PMFs.

    :param results:
        It's a list of lists. The number of elements is equal to the number of
        correlated groups. Each element contains the following:
        his_t, min_pow_t, num_pow_t, weight_t
    :param resolution:
        The number of points per power interval (i.e. the resolution used to
        represent the pmf)
    :returns:
        A triple with the pmfs, the min power and the range (num of powers).
    """
    num_imls = len(results[0][0])

    # The minimum power is IMT dependent
    minpow = np.empty((num_imls))
    minpow[:] = np.nan
    maxpow = np.empty((num_imls))
    maxpow[:] = np.nan
    for i, res in enumerate(results):

        tmp_minpow = np.array(res[1], dtype=float)
        tmp_numpow = np.array(res[2], dtype=float)
        idx = ~np.isnan(tmp_minpow)

        if i == 0:
            minpow[idx] = tmp_minpow[idx]
            maxpow[idx] = tmp_numpow[idx] + tmp_minpow[idx]
        else:
            minpow[idx] = np.minimum(minpow[idx], tmp_minpow[idx])
            maxpow[idx] = np.maximum(maxpow[idx], tmp_minpow[idx] +
                                     tmp_numpow[idx])

    idx = ~np.isnan(minpow)
    maxrange = copy.copy(minpow)
    maxrange[idx] = maxpow[idx] - minpow[idx]

    # Create output. For each IML we create the mixture PMF as a weighted sum
    # of the two original PMFs. In the case of disaggregation the number of
    # imls `num_imls` corresponds to the number of cells (i.e. the number of
    # M-R combinations)
    olst = []
    for i_iml in range(0, num_imls):

        tmp = None
        tot_wei = 0.0
        for j, res in enumerate(results):

            # Skipping this IML if the maxrange is nan
            if np.isnan(maxrange[i_iml]):
                break

            # Skipping this realization if the lower limit is None
            if res[1][i_iml] is None:
                continue

            # Initialize the array where we store the output distribution
            if j == 0:
                tmp = np.zeros((int(resolution*maxrange[i_iml])))

            # Find where to add the current PMF
            low = int(resolution*(res[1][i_iml]-minpow[i_iml]))
            upp = int(low + resolution*(res[2][i_iml]))

            # Sum the PMF
            idxs = np.arange(low, upp)
            tmp[idxs] += np.array(res[0][i_iml])*res[3]
            tot_wei += res[3]

        if tmp is not None:
            chk = np.sum(tmp)
            chk = np.sum(tmp)/tot_wei
            msg = f'Wrong PMF. Elements do not sum to 1 ({chk:8.6e})'
            assert np.all(np.abs(chk-1.0) < TOLERANCE), msg
            olst.append(tmp)
        else:
            olst.append(None)

    # Check output dimension
    minpow = [i if ~np.isnan(i) else None for i in minpow]
    maxrange = [i if ~np.isnan(i) else None for i in maxrange]
    assert len(olst) == len(minpow) == len(maxrange)

    return olst, minpow, maxrange
