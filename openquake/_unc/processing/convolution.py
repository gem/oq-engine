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


def convolution(an01: Analysis, rlzgroups: dict, imt: str, atype: str,
                res: int=50):
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
def get_grp_ids(sset, uncs, an01, rlzgroups):
    """
    :param sset: set of sources
    :param uncs: uncertainty indices
    :param an01: Analysis instance
    :param rlzgroups: dictionary
    :returns: list of group indices, group weights
    """
    assert uncs[0] == 0  # starts with 0 always
    gweights = {srcid: 1 for srcid in sset}
    for unc in uncs:
        srcids = an01.dfs[unc].srcid.to_numpy()
        n = len(rlzgroups[unc, srcids[0]])
        if unc == 0:
            grp_ids = [(i,) for i in range(n)]
        else:
            grp_ids = [grpids + (i,) for grpids in grp_ids for i in range(n)]
        # Update the weight reduction factors for the sources not having this
        # branch set of correlated uncertainties
        srcids_not = sset - set(srcids)
        for srcid in srcids_not:
            gweights[srcid] *= n
    # number of grp_ids = prod(num_groups(unc) for unc in uncs)
    return grp_ids, gweights


def get_rlzs(an01, srcid, rlzgroups, grpids):
    # Get the indexes of the realizations for the current source
    # for the grpids in question
    rset = set()
    for unc, grpid in enumerate(grpids):
        # Check if the current source is in this group
        if srcid in an01.dfs[unc].srcid.to_numpy():
            idx = set(rlzgroups[unc, srcid][grpid])
            if not rset:  # first time
                rset = idx
            else:
                rset &= idx
    return sorted(rset)


def process(sset, uset, an01, rlzgroups, res, imt, atype):
    """
    Process correlated sources
    """ 
    # Uncertainty grp_ids; for instance, in test_02_performance 
    # grp_ids = [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)]
    # gweights = {'a': 2, 'c': 4, 'b': 1}
    grp_ids, gweights = get_grp_ids(sset, sorted(uset), an01, rlzgroups)

    histos = {}
    for grpids in grp_ids:
        # build a HistoGroup for each grpids, for instance grpids = (1, 3)
        for srcid in sorted(sset):
            rlzs = get_rlzs(an01, srcid, rlzgroups, grpids)
            # for instance rlzs = [3, 7, 11, 15, 19, 23]

            _imls, afes, weights = afes_matrix_from_dstore(
                an01.dstores[srcid], imt, atype, rlzs=rlzs)

            # Get histograms
            h = HistoGroup.new(afes, weights, res)

            # Updating results for the current set of correlated uncertainties
            if grpids not in histos:
                histos[grpids] = h
            else:
                histos[grpids] *= h
            histos[grpids].weight += weights.sum() / gweights[srcid]

    for grpids in grp_ids:
        histos[grpids].weight /= len(sset)  # fix weight

    # Taking the mixture MFD
    return mixture(list(histos.values()))
