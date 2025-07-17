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

import numpy as np
from openquake._unc.bins import get_bins_data, get_bins_from_params

# We use a PMF-matrix to store the results of a number of disaggregation
# results obtained from a set of realisations admitted by a logic tree for a
# single IMT.
#
# For the description of a PMF we use:
#    - A numpy vector (cardinality: L = number of IMLs)
#    - A numpy array (cardinality: L x |number of bins|) containing the annual
#      frequencies of exceeedance """


def get_afes_from_dstore(dstore, imt_idx: int, info: bool = False,
                         idxs: list=[]):
    """
    Pulls from the datastore the poes for a given IMT and convert them to afes
    (we assume the dstore contains only 1 site).

    :param dstore:
        Instance of :class:`openquake.commonlib.datastore.DataStore`
    :param imt_idx:
        Index specifying the intensity measure type of interest
    :param info:
        [optional] A boolean controlling the amont of information provided
    :param idxs:
        [optional] the indexes of the realisations to read
    :returns:
        A tuple with a list of the values in the three dimensions, an array
        with the annual frequencies of exceedance, one array with the
        weights of the realisations and an array with the shape of the
        disaggregation matrix.
    """

    # Indexes of the realisations
    if len(idxs) > 0:
        idxs = np.array(idxs, dtype=int)
    else:
        idxs = slice(None)

    # Read oq parameters
    oqp = dstore['oqparam']
    imtstr = list(oqp.imtls)[imt_idx]

    # Read the poes and convert them into frequencies. The Mag
    # matrix has the following dimensions:
    # |Site| x |IMTs| x |IMLs| x |Mag| x |Rlz|
    poes = dstore.getitem('disagg/Mag')[0, imt_idx, 0, :, idxs]
    shapes = poes.shape
    poes[poes > 0.99999] = 0.99999
    afes = -np.log(1.-poes) / oqp.investigation_time

    # Realization weights
    weights = dstore.getitem('weights')[idxs]

    # Central value for each bin
    binc = {}
    tmp = dstore.getitem('disagg-bins/Mag')[:]
    binc['mag'] = tmp[:-1] + np.diff(tmp) / 2

    if info:
        len_description = 30
        tmps = 'Investigation time'.ljust(len_description)
        print(f'{tmps:s}: {oqp.investigation_time:f}')
        tmps = 'IMT'.ljust(len_description)
        print(f'{tmps:s}: {imtstr:s}')
        tmps = 'Number of realizations'.ljust(len_description)
        print(f'{tmps:s}: {len(poes):d}')

    return binc, afes, weights, shapes


def get_histograms(afes_mtx: np.ndarray, weights: np.ndarray, res: int,
                   idxs: np.ndarray=None):
    """
    Computes the histograms of the AfE for each M-D-e combination

    :param afes_mtx:
        A 4D :class:`numpy.ndarray` instance with cardinality:
        |Mag| x |Dist| x |Eps| x |Rlz|
    :param weights:
        The weights for the realisations
    :param res:
        The number of samples per each power of 10
    :param idxs:
        Indexes of the realisations to consider
    :returns:
        A tuple with three lists. The first list contains the histograms for
        all the intensity measure levels. The second list contains the first
        integer (a multiple of 10) defining the lower edge of the first bin of
        the histogram. The second list contains integers defining the range
        covered by the histogram (i.e. number of powers of 10).
    """
    if idxs is not None:
        afes_mtx = afes_mtx[idxs, :]
        weights = weights[idxs]

    # Loop over each M-D-e combination
    ohis = []
    min_powers = []
    num_powers = []
    idx_empty = []
    for imag in range(afes_mtx.shape[0]):

        dat = np.array(afes_mtx[imag, :])

        # Filling the output list with a None for the combinations
        # without contributions
        if not np.any(dat > 1e-30):
            idx_empty.append(imag)
            ohis.append(None)
            min_powers.append(None)
            num_powers.append(None)
            continue

        # Computing bins
        min_power, num_pow = get_bins_data(dat)
        bins = get_bins_from_params(min_power, res, num_powers=num_pow)

        # Computing histogram
        his, _ = np.histogram(dat, bins, weights=weights)
        his = his / np.sum(his)

        # Checking
        assert len(his) == num_pow * res
        assert np.abs(np.sum(his) - 1.0) < 1e-8

        # Updating output
        ohis.append(his)
        min_powers.append(int(min_power))
        num_powers.append(int(num_pow))

    for imag in idx_empty:
        ohis[imag] = np.zeros((num_pow * res))
        min_powers[imag] = np.min(min_powers)
        num_powers[imag] = 0

    return ohis, min_powers, num_powers
