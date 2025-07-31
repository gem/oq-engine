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

"""
Module :module:`openquake._unc.processing.sampling` contains code for sampling
the realizations from a set of outputs from the OQ Engine
"""

import logging
import numpy as np
from openquake._unc.analysis import Analysis


# tested in test_01_performance
def sampling(an01: Analysis, rlzgroups, nsam: int):
    """
    Propagates epistemic uncertainties by sampling. It accounts for the
    correlations between the source-specific logic trees.

    :param an01:
        A :class:`openquake._unc.analysis.Analysis` instance
    :param rlzgroups:
        Dictionary unc, srcid -> groups of indices
    :param nsam:
        Total number of samples
    :returns:
        A tuple containing the intensity measure levels and a
        :class:`numpy.ndarray` instance with the annual frequencies of
        exceedance
    """
    logging.info('Computing sampling')

    # Source sets and associated correlated uncertainties
    ssets, usets = an01.get_sets()

    # Create a dictionary with the datastores, one for each source
    dstores = an01.dstores
    srcids = np.array(list(dstores))

    # Create the mtx where we store results for all the IMTs. The shape
    # of this array - called afes - is: N x SRC x R x M x L
    # NB: the afes array can easily run out of memory with large nsam
    shp = dstores[srcids[0]]['hcurves-rlzs'].shape
    afes = np.zeros((shp[0], len(an01.dstores), nsam, shp[2], shp[3]))
    weir = np.ones(nsam)

    # Process the sets of results. When a set contains a single source,
    # this means that the source does not have correlations with other sources.
    for sset, uset in zip(ssets, usets):
        logging.info(f'Processing sources {sset} correlated with {uset}')

        if uset:
            # For each correlated branchset we draw a number of realizations
            sampled_indexes = {}
            for unc in sorted(uset):  # ordered fixed for reproducibility

                # ID of the first source with a given correlated uncertainty
                srcid = an01.dfs[unc].srcid.to_numpy()[0]
                wei = an01.dstores[srcid]['weights'][:]

                # These are the weights assigned to each group
                weights_per_group = [
                    wei[grp].sum() for grp in rlzgroups[unc, srcid]]
                weights = rounding(weights_per_group, 2)

                # 'sampled_indexes' contains the indexes of the sampled
                # set of correlated realisations
                sampled_indexes[unc] = an01.rng.choice(
                    len(weights), nsam, p=weights)

            sample_set(an01, sset, uset, nsam, rlzgroups, sampled_indexes,
                       afes, weir)
        else:
            # sset contains a single uncorrelated source
            srcid, = sset
            isrc, = np.where(srcids == srcid)

            # for instance [0.25, 0.25, 0.25, 0.25]
            wei = an01.dstores[srcid]['weights'][:]

            # Sampling
            # for instance [3, 3, 0, ..., 2, 3, 3] with 1E5 elements
            idx_rlzs = an01.rng.choice(len(wei), size=nsam, p=wei)

            # Updating the afes matrix
            poes = dstores[srcid]['hcurves-rlzs'][:]
            afes[:, isrc, :, :, :] = poes[:, idx_rlzs]
            weir *= wei[idx_rlzs]

    # Converting the final matrix into annual frequencies of exceedance
    oqp = dstores[srcids[0]]['oqparam']
    afes[afes > 0.99999] = 0.99999
    afes = - np.log(1. - afes) / oqp.investigation_time

    return oqp.hazard_imtls, afes


def sample_set(an01, sset, uset, nsam, rlzgroups, sampled_indexes, afes, weir):

    # Sample hazard curves for each source in this set
    srcids = np.array(list(an01.dstores))
    for srcid in sorted(sset):
        logging.info(f"   Source: {srcid}")

        # This is a container for the indexes of the realizations. Each
        # element is a set of indexes of realizations for the source
        # in question
        ridx = [None] * nsam

        # For each set of correlated results
        for unc in uset:
            try:
                grps = rlzgroups[unc, srcid]
            except KeyError:
                continue
            # If the logic tree of the current source includes this correlation
            for sam in range(nsam):
                # Get the sequence of indexes of the curves for the
                # sampled set of correlated results
                idx = sampled_indexes[unc][sam]
                rlzids = set(grps[idx])
                if ridx[sam] is None:
                    ridx[sam] = rlzids
                else:
                    ridx[sam] &= rlzids

        # Get realisations and weights for the source currently
        # investigated. `wei` contains the weights assigned to each one
        # of the realizations admitted by the logic tree of the current
        # source
        wei = an01.dstores[srcid]['weights'][:]
        poes = an01.dstores[srcid]['hcurves-rlzs'][:]

        # Index of the current source
        isrc, = np.where(srcids == srcid)

        # Process each sample for the current source
        for sam in range(nsam):

            # These are the indexes from which we draw a sample, for instance
            # [0, 4, 8, 12, 16, 20]
            idxs = sorted(ridx[sam])

            # Normalised weights, for instance
            # [0.166, 0.166, 0.166, 0.166, 0.166, 0.170]
            norm_wei = wei[idxs] / wei[idxs].sum()

            # Pick the realization index for the current sample
            # for instance [0, 4, 8, 12, 16, 20] => 20
            idx = an01.rng.choice(idxs, p=norm_wei)

            # Save the probabilities of exceedance for the current source
            afes[:, isrc, sam, :, :] = poes[:, idx]

            # Save the weight for this sample
            weir[sam] *= wei[idx]


def rounding(weights, digits):
    """
    >>> rounding([.123, .234, .51, .133], 2)
    array([0.12, 0.23, 0.51, 0.14])
    """
    out = np.round(weights, digits)
    out[-1] = 1. - out[:-1].sum()
    return out

