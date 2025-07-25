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

import logging

from openquake._unc.analysis import Analysis
from openquake._unc.hazard_pmf import afes_matrix_from_dstore, mixture
from openquake._unc.convolution import HistoGroup


def convolution(ssets: list, usets: list, an01: Analysis,
                grp_curves: dict, imt: str, atype: str, res: int=50):
    """
    This processes the hazard curves and computes the final results

    :param ssets: sets of sources
    :param usets: sets of branchset IDs
    :param an01:
        An instance of :class:`openquake._unc.analysis.Analysis`
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
    logging.info('Computing convolution')

    # Process the sets of sources. When a set contains a single source,
    # this means that the source does not have correlations with other sources.
    for iset, (sset, uset) in enumerate(zip(ssets, usets)):
        logging.info(f'Processing sources {sset} correlated bs {uset}')

        # When uset is not None there are correlated sources
        if uset is not None:
            h = process_uset(sset, uset, an01, grp_curves, res, imt, atype)
        else:
            srcid = list(sset)[0]
            # Load the matrix containing the annual frequencies of exceedance.
            # afes is an array with shape I x L where I is the number of
            # intensity measure levels and L is the number of intensity measure
            # levels
            imls, afes, weights = afes_matrix_from_dstore(
                an01.dstores[srcid], imt, atype)

            # Convert the matrix into a list of histograms, one for each
            # intensity measure level considered
            h = HistoGroup.new(afes, weights, res)

        # Update the final distribution
        if iset == 0:
            acc = h
        else:
            acc *= h

    return acc


def _get_path_info(sset, uset, an01, grp_curves):
    """
    :param sset: set of sources
    :param uset: set of branchset IDs
    :param an01: Analysis instance
    :param grp_curves: dictionary
    """
    paths = []
    uset_list = []
    weight_redux = {srcid: 1 for srcid in sset}
    for uset_i, bsid in enumerate(uset):
        uset_list.append(bsid)
        srcids = an01.bsets[bsid]['srcid']
        if uset_i == 0:
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
        for srcid in srcids_not:
            weight_redux[srcid] *= len(grp_curves[bsid][srcids[0]])
    return paths, uset_list, weight_redux


def process_uset(sset, uset, an01, grp_curves, res, imt, atype):
    """
    Process a branchset

    :param uset:
    :param an01:
    :param grp_curves:
    :param res:
    :param imt:
        The intensity measure type of interest
    """
    # Compute the number of groups of correlated uncertainties
    num_paths = 1
    for uset_i, bsid in enumerate(uset):
        srcids = an01.bsets[bsid]['srcid']
        num_paths *= len(grp_curves[bsid][srcids[0]])

    # Paths
    paths, uset_list, weight_redux = _get_path_info(
        sset, uset, an01, grp_curves)

    ares = {}
    chk_idxs = {}
    chk_wei = {}
    for path in paths:

        # Get the indexes of the groups in each branch set
        group_idxs = [int(s) for s in path.split('_')]

        # For each source
        for srcid in sorted(sset):

            # For each group. Here we find the indexes 'rlz_idx' of the
            # realizations (i.e. the hazard curves) for the current source
            # obtained for the path in question.
            rlz_idx = set()
            for i, grp_i in enumerate(group_idxs):

                # Check if the current source is in this group
                bsid = uset_list[i]
                if srcid in an01.bsets[bsid]['srcid']:
                    tmp = set(grp_curves[bsid][srcid][grp_i])
                    if len(rlz_idx) == 0:
                        rlz_idx = tmp
                    else:
                        rlz_idx = rlz_idx.intersection(tmp)

            # Get hazard curves
            _, afes, weights = afes_matrix_from_dstore(
                an01.dstores[srcid], imt, atype, False, sorted(rlz_idx))

            # Get histogram
            h = HistoGroup.new(afes, weights, res)

            # Computing weight
            wei_sum = sum(weights) / weight_redux[srcid]

            # Checking the weights
            if srcid not in chk_idxs:
                chk_idxs[srcid] = rlz_idx
                chk_wei[srcid] = wei_sum
            else:
                chk_idxs[srcid] = chk_idxs[srcid].union(rlz_idx)
                chk_wei[srcid] += wei_sum

            # Updating results for the current set of correlated uncertainties
            if path not in ares:
                ares[path] = [h.pmfs, h.minpow, h.numpow, wei_sum]
            else:
                his_t, m_pow_t, n_pow_t, wei = ares[path]
                h *= HistoGroup(his_t, m_pow_t, n_pow_t)
                his, m_pow, n_pow = h.pmfs, h.minpow, h.numpow
                ares[path] = [his, m_pow, n_pow, wei + wei_sum]

    results = []
    for i, path in enumerate(paths):
        ares[path][3] /= len(sset)  # fix weight
        results.append(HistoGroup(*ares[path]))

    # Taking the mixture MFD
    return mixture(results)
