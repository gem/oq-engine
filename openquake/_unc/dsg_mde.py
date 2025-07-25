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

# We use a PMF-matrix to store the results of a number of disaggregation
# results obtained from a set of realisations admitted by a logic tree for a
# single IMT.
#
# For the description of a PMF we use:
#    - A numpy vector (cardinality: L = number of IMLs)
#    - A numpy array (cardinality: L x |number of bins|) containing the annual
#      frequencies of exceeedance """


def get_afes_from_dstore(dstore, name, imt_idx: int,
                         info: bool=False, idxs: list=[]):
    """
    Pulls from the datastore the poes for a given IMT and convert them to afes
    (we assume the dstore contains only 1 site).

    :param dstore:
        Instance of :class:`openquake.commonlib.datastore.DataStore`
    :param name:
        One of Mag, Mag_Dist, Mag_Dist_Eps
    :param imt_idx:
        Index of the intensity measure type of interest
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

    # Indexes of the realizations
    if len(idxs) > 0:
        idxs = np.array(idxs, dtype=int)
    else:
        idxs = slice(None)

    # Read oq parameters
    oqp = dstore['oqparam']
    imtstr = list(oqp.imtls)[imt_idx]

    # Read the poes and convert them into frequencies. The Mag_Dist_Eps
    # matrix has the following dimensions:
    # |Site| x |Mag| x |Dist| x |Eps| x |IMTs| x |IMLs| x |Rlz|

    if name == 'Mag_Dist_Eps': 
        poes = dstore['disagg-rlzs/Mag_Dist_Eps'][0, :, :, :, imt_idx, 0, idxs]
    elif name == 'Mag_Dist':
        poes = dstore['disagg-rlzs/Mag_Dist'][0, :, :, imt_idx, 0, idxs]
    elif name == 'Mag':
        poes = dstore['disagg-rlzs/Mag'][0, :, imt_idx, 0, idxs]
    else:
        raise NameError(name)
    shapes = poes.shape
    poes[poes > 0.99999] = 0.99999
    afes = -np.log(1.-poes) / oqp.investigation_time

    # Realization weights
    weights = dstore['weights'][idxs]

    # Central value for each bin
    binc = {}
    tmp = dstore.getitem('disagg-bins/Mag')[:]
    binc['mag'] = tmp[:-1] + np.diff(tmp) / 2
    tmp = dstore.getitem('disagg-bins/Dist')[:]
    binc['dst'] = tmp[:-1] + np.diff(tmp) / 2
    tmp = dstore.getitem('disagg-bins/Eps')[:]
    binc['eps'] = tmp[:-1] + np.diff(tmp) / 2

    if info:
        len_description = 30
        tmps = 'Investigation time'.ljust(len_description)
        print(f'{tmps:s}: {oqp.investigation_time:f}')
        tmps = 'IMT'.ljust(len_description)
        print(f'{tmps:s}: {imtstr:s}')
        tmps = 'Number of realizations'.ljust(len_description)
        print(f'{tmps:s}: {len(poes):d}')

    return binc, afes, weights, shapes
