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

"""
Module :module:`openquake._unc.processing.sampling` contains code for sampling
the realizations from a set of outputs from the OQ Engine
"""

import logging
import numpy as np
from openquake._unc.analysis import Analysis


def sampling(ssets: list, bsets: list, an01: Analysis, root_path: str,
             grp_curves, nsam: int):
    """
    Propagates epistemic uncertainties by sampling. It accounts for the
    correlations between the source-specific logic trees.

    :param ssets:
        A list where each element contains the set of sources sharing
        correlated uncertainties
    :param bsets:
        A list with the id of the branch sets with correlated uncertainties
    :param an01:
        A :class:`openquake._unc.analysis.Analysis` instance
    :param root_path:
        Path where
    :param grp_curves:
    :param nsam:
        Total number of samples
    :returns:
        A tuple containing the intensity measure levels and a
        :class:`numpy.ndarray` instance with the annual frequencies of
        exceedance
    """

    msg = 'Computing sampling'
    logging.info(msg)

    # Create a dictionary with the datastores, one for each source
    sids = np.array(list(an01.dstores))
    dstores = an01.dstores

    # Create the mtx where we store results for all the IMTs. The shape
    # of this matrix - called afes - is: S x SRC x R x I x L
    # S - number of sites
    # SRC - number of sources
    # R - realizations
    # I - IMTs
    # L - IMLs
    shps = dstores[sids[0]].getitem('hcurves-rlzs')[:].shape
    afes = np.zeros((shps[0], len(an01.dstores), nsam, shps[2], shps[3]))
    weir = np.ones(nsam)

    # Process the sets of results. When a set contains a single source,
    # this means that the source does not have correlations with other sources.
    for i, _ in enumerate(ssets):
        sset = ssets[i]
        bset = bsets[i]

        # Info
        msg = f'Processing set {i} sources {sset} correlated bs {bset}'
        logging.info(msg)

        # When bset is not None, it contains sources with correlated
        # uncertainties. Firstly we create a dictionary with key the
        # 'bsid' and values a set of indexes of the sampled sets of
        # correlated uncertainties
        if bset is not None:

            # For each correlated branch-set we draw a number of indexes of the
            # realizations
            bset_sampled_indexes = {}
            for bsid in sorted(bset):

                # ID of the sources in this set with a given correlated
                # uncertainty
                bs_sids = list(an01.bsets[bsid]['data'])

                # Realisations for the first source
                rlzs, wei = an01.get_rpaths_weights(
                    dstores[bs_sids[0]], bs_sids[0])

                # These are the weights assigned to each group of correlated
                # results for this uncertainty
                weights_per_group = []
                for iii in grp_curves[bsid][bs_sids[0]]:
                    weights_per_group.append(sum(wei[iii]))
                weights_per_group = np.array(weights_per_group)

                # 'bset_sampled_indexes' contains the indexes of the sampled
                # set of correlated realisations
                tmp = np.array(list(range(len(weights_per_group))))
                weights_per_group = rounding(weights_per_group, 4)
                bset_sampled_indexes[bsid] = np.random.choice(
                    tmp, size=nsam, p=weights_per_group)

            # Sample hazard curves for each source in this set
            for srcid in sorted(sset):

                print(f'Source ID: {srcid}')
                msg = f"   Source: {srcid}"
                logging.info(msg)

                # This is a container for the indexes of the realizations. Each
                # element is a set of indexes of realizations for the source
                # in question
                iii = [None] * nsam

                # This is a counter for the branch set of correlated
                # uncertainties in a group
                i = 0

                # For each set of correlated results
                for bsid in bset:

                    # If the logic tree of the current source includes this
                    # correlation
                    if srcid in grp_curves[bsid]:

                        # For each sample
                        for sam in range(nsam):

                            # Get the sequence of indexes of the curves for the
                            # sampled set of correlated results
                            xx = bset_sampled_indexes[bsid][sam]
                            tmp = grp_curves[bsid][srcid][xx]
                            if i == 0:
                                iii[sam] = set(tmp)
                            else:
                                iii[sam] = iii[sam].intersection(set(tmp))

                        i += 1

                # Get realisations and weights for the source currently
                # investigated. `wei` contains the weights assigned to each one
                # of the realizations admitted by the logic tree of the current
                # source
                _, wei = an01.get_rpaths_weights(dstores[srcid], srcid)

                # Array where we store the indexes of the sampled realisations
                idx_rlzs = np.zeros((nsam), dtype=int)
                poes = dstores[srcid].getitem('hcurves-rlzs')[:]

                # Index of the current source
                kkk = np.where(sids == srcid)[0]

                # Process each sample for the current source
                for sam in range(nsam):

                    # These are the indexes from which we draw a sample
                    idxs = np.array(sorted(list(iii[sam])))

                    #if srcid == 'b':
                    #    breakpoint()

                    # Normalised weights
                    norm_wei = wei[idxs] / sum(wei[idxs])

                    # Pick the index of the hazard curve for the current sample
                    idx_rlzs[sam] = np.random.choice(idxs, p=norm_wei)

                    # Save the probabilities of exceedance for the current
                    # source and sample
                    afes[:, kkk, sam, :, :] = poes[:, idx_rlzs[sam]]

                    # Save the weight for this sample
                    weir[sam] *= wei[idx_rlzs[sam]]

        else:

            srcid = list(sset)[0]
            kkk = np.where(sids == srcid)[0]

            # Get realisations and weights for the source currently
            # investigated
            rlzs, wei = an01.get_rpaths_weights(dstores[srcid], srcid)

            # Sampling of results
            iii = np.arange(0, len(wei))
            idx_rlzs = np.random.choice(iii, size=nsam, p=wei)

            # Updating the afes matrix
            poes = dstores[srcid]['hcurves-rlzs'][:]
            afes[:, kkk, :, :, :] = poes[:, idx_rlzs]
            weir *= wei[idx_rlzs]

    # Converting the final matrix into annual frequencies of exceedance
    oqp = dstores[sids[0]]['oqparam']
    afes[afes > 0.99999] = 0.99999
    afes = - np.log(1. - afes) / oqp.investigation_time

    return oqp.hazard_imtls, afes


def rounding(weights_per_group, num):
    out = []
    for i in range(len(weights_per_group)-1):
        wei = weights_per_group[i]
        tmp = float(f"{wei:.{num}f}")
        out.append(tmp)
    out.append(1.0 - np.sum(out))
    return np.array(out)

