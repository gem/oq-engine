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

import os
import logging
import numpy as np

from openquake._unc.analysis import Analysis
from openquake._unc.hazard_pmf import (
    afes_matrix_from_dstore, get_hazard_pmf, convolve, mixture)


def convolution(ssets: list, bsets: list, an01: Analysis, root_path: str,
                grp_curves: dict, imt: str, atype: str, res: int = 50):
    """
    This processes the hazard curves and computes the final results

    :param ssets:
    :param bsets:
    :param an01:
        An instance of :class:`openquake._unc.analysis.Analysis`
    :param root_path:
        Root path where to find the datastores of the files with the results of
        the source-specific analyses.
    :param grp_curves:
        A dictionary of dictionaries
    :param imt:
        A string specifying an intensity measure type
    :param atype:
        The type of data type to be analysed (e.g. hcurves, mde)
    :param res:
        An integer that defines the resolution of the histograms i.e. number of
        intervals for each log unit
    :returns:
        A triple containing the output histogram, and two arrays with the
        lowest power and the number of powers used to define the histogram
    """

    msg = 'Computing convolution'
    logging.info(msg)

    # Create a dictionary with the datastores, one for each source
    dstores = an01.dstores

    # Process the sets of logic trees. When a set contains a single source,
    # this means that the source does not have correlations with other sources.
    for iset in range(len(ssets)):

        sset = ssets[iset]
        bset = bsets[iset]

        # Info
        msg = f'Processing set {iset} sources {sset} correlated bs {bset}'
        logging.info(msg)

        # When bset is not None there are correlated sources
        if bset is not None:

            his, min_pow, num_pow = process_bset(
                sset, bset, an01, grp_curves, dstores, res, imt, atype)

        else:

            # Source ID
            sid = list(sset)[0]
            # Load the matrix containing the annual frequencies of exceedance.
            # afes is an array with shape I x L where I is the number of
            # intensity measure levels and L is the number of intensity measure
            # levels
            afds = afes_matrix_from_dstore
            imls, afes, weights = afds(dstores[sid], imt, atype=atype)

            # Convert the matrix into a list of histograms, one for each
            # intensity measure level considered
            his, min_pow, num_pow = get_hazard_pmf(
                afes, samples=res, weights=weights)

        # Update the final distribution
        if iset == 0:
            fhis, fmin_pow, fnum_pow = his, min_pow, num_pow
        else:
            fhis, fmin_pow, fnum_pow = convolve(
               fhis, his, fmin_pow, res, fnum_pow, min_pow, res, num_pow, res)

    #return fhis, np.array(fmin_pow, dtype=int), np.array(fnum_pow, dtype=int)
    assert len(fhis) == len(fmin_pow) == len(fnum_pow)
    return fhis, np.array(fmin_pow), np.array(fnum_pow)


def _get_path_info(sset, bset, an01, grp_curves):
    """
    :param sset:
    :param bset:
    :param an01:
    :param grp_curves:
    """
    paths = []
    bset_list = []
    weight_redux = {sid: 1 for sid in sset}
    for bset_i, bsid in enumerate(bset):
        bset_list.append(bsid)
        srcids = list(an01.bsets[bsid]['data'].keys())
        if bset_i == 0:
            for i in range(len(grp_curves[bsid][srcids[0]])):
                paths.append(f'{i}')
        else:
            tmp = []
            for path in paths:
                for i in range(len(grp_curves[bsid][srcids[0]])):
                    tmp.append(f'{path}_{i}')
            paths = tmp
        # Update the weight reduction factors for the sources not having this
        # branch set of correlated uncertainties
        srcids_not = sset - set(srcids)
        for sid in srcids_not:
            weight_redux[sid] *= len(grp_curves[bsid][srcids[0]])
    return paths, bset_list, weight_redux


def process_bset(sset, bset, an01, grp_curves, dstores, res, imt, atype):
    """
    Process a branchset

    :param bset:
    :param an01:
    :param grp_curves:
    :param dstores:
    :param res:
    :param imt:
        The intensity measure type of interest
    """

    # Compute the number of groups of correlated uncertainties
    num_paths = 1
    for bset_i, bsid in enumerate(bset):
        srcids = list(an01.bsets[bsid]['data'].keys())
        num_paths *= len(grp_curves[bsid][srcids[0]])

    # Paths
    paths, bset_list, weight_redux = _get_path_info(
        sset, bset, an01, grp_curves)

    ares = {}
    chk_idxs = {}
    chk_wei = {}
    for path in paths:

        # Get the indexes of the groups in each branch set
        group_idxs = [int(s) for s in path.split('_')]

        # For each source
        for sid in sorted(sset):

            # For each group. Here we find the indexes 'rlz_idx' of the
            # realizations (i.e. the hazard curves) for the current source
            # obtained for the path in question.
            rlz_idx = set()
            for i, grp_i in enumerate(group_idxs):

                # Check if the current source is in this group
                bsid = bset_list[i]
                if sid in list(an01.bsets[bsid]['data'].keys()):

                    tmp = set(grp_curves[bsid][sid][grp_i])
                    if len(rlz_idx) == 0:
                        rlz_idx = tmp
                    else:
                        rlz_idx = rlz_idx.intersection(tmp)

            # Get hazard curves
            iii = sorted(list(rlz_idx))
            _, afes, weights = afes_matrix_from_dstore(
                dstores[sid], imtstr=imt, info=False, idxs=iii, atype=atype)

            # Get histogram
            his, min_pow, num_pow = get_hazard_pmf(
                afes, samples=res, weights=weights)

            # Computing weight
            wei_sum = sum(weights) / weight_redux[sid]

            # Checking the weights
            if sid not in chk_idxs:
                chk_idxs[sid] = rlz_idx
                chk_wei[sid] = wei_sum
            else:
                chk_idxs[sid] = chk_idxs[sid].union(rlz_idx)
                chk_wei[sid] += wei_sum

            # Updating results for the current set of correlated uncertainties
            if path not in ares:
                ares[path] = [his, min_pow, num_pow, wei_sum]
            else:
                his_t = ares[path][0]
                m_pow_t = ares[path][1]
                n_pow_t = ares[path][2]
                wei = ares[path][3]
                his, m_pow, n_pow = convolve(
                        his_t, his,
                        m_pow_t, res, n_pow_t,
                        min_pow, res, num_pow, res)
                ares[path] = [his, m_pow, n_pow, wei+wei_sum]

    results = []
    twei = 0
    for i, path in enumerate(paths):
        ares[path][3] = ares[path][3] / len(sset)
        results.append(ares[path])
        twei += ares[path][3]

    # Taking the mixture MFD
    his, min_pow, num_pow = mixture(results, res)

    return his, min_pow, num_pow
