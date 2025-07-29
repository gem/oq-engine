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


def convolution(an01: Analysis, rlzgroups: dict, imt: str, atype: str, res: int=50):
    """
    This processes the hazard curves and computes the final results

    :param an01:
        An instance of :class:`openquake._unc.analysis.Analysis`
    :param rlzgroups:
        A dictionary (unc, srcid) -> groups of realizations
    :param imt:
        A string specifying an intensity measure type
    :param atype:
        The type of data type to be analysed (e.g. hcurves, mde)
    :param res:
        An integer that defines the resolution of the histograms i.e. number of
        intervals for each log unit
    :returns:
        A HistoGroup containing the convolution histogram
    """
    logging.info('Computing convolution')

    # Source sets and associated correlated uncertainties
    ssets, usets = an01.get_sets()

    # Process the sets of sources. When a set contains a single source,
    # this means that the source does not have correlations with other sources.
    for iset, (sset, uset) in enumerate(zip(ssets, usets)):
        logging.info(f'Processing sources {sset} correlated bs {uset}')

        # When uset is not empty there are correlated sources
        if uset:
            h = process(sset, uset, an01, rlzgroups, res, imt, atype)
        else:
            srcid, = sset
            # Load the matrix containing the annual frequencies of exceedance.
            # afes is an array with shape M x L where M is the number of
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


# tested in test_02_performance 
def _get_path_info(sset, uncs, an01, rlzgroups):
    """
    :param sset: set of sources
    :param uncs: uncertainty indices
    :param an01: Analysis instance
    :param rlzgroups: dictionary
    """
    assert uncs[0] == 0  # starts with 0 always
    weight_redux = {srcid: 1 for srcid in sset}
    for unc in uncs:
        srcids = an01.bsets[unc]['srcid']
        n = len(rlzgroups[unc, srcids[0]])
        if unc == 0:
            paths = [(i,) for i in range(n)]
        else:
            paths = [path + (i,) for path in paths for i in range(n)]
        # Update the weight reduction factors for the sources not having this
        # branch set of correlated uncertainties
        srcids_not = sset - set(srcids)
        for srcid in srcids_not:
            weight_redux[srcid] *= n
    return paths, weight_redux


def process(sset, uset, an01, rlzgroups, res, imt, atype):
    """
    Process correlated sources
    """ 
    # Compute the number of groups of correlated uncertainties
    num_paths = 1
    for unc in uset:
        srcids = an01.bsets[unc]['srcid']
        num_paths *= len(rlzgroups[unc, srcids[0]])

    # Paths
    paths, weight_redux = _get_path_info(sset, sorted(uset), an01, rlzgroups)

    histos = {}
    for path in paths:

        # For each source
        for srcid in sorted(sset):

            # For each group. Here we find the indexes 'rlz_idx' of the
            # realizations for the current source for the path in question.
            rlz_idx = set()
            for unc, grp_i in enumerate(path):

                # Check if the current source is in this group
                if srcid in an01.bsets[unc]['srcid']:
                    idx = set(rlzgroups[unc, srcid][grp_i])
                    if not rlz_idx:  # first time
                        rlz_idx = idx
                    else:
                        rlz_idx &= idx

            # Get hazard curves
            _, afes, weights = afes_matrix_from_dstore(
                an01.dstores[srcid], imt, atype, False, sorted(rlz_idx))

            # Get histograms
            h = HistoGroup.new(afes, weights, res)

            # Updating results for the current set of correlated uncertainties
            if path not in histos:
                histos[path] = h
            else:
                histos[path] *= h
            histos[path].weight += weights.sum() / weight_redux[srcid]

    for path in paths:
        histos[path].weight /= len(sset)  # fix weight

    # Taking the mixture MFD
    return mixture(list(histos.values()))
