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
Module `openquake._unc.analysis`
"""

import re
import os
import collections
import xml.etree.ElementTree as ET
import logging
import numpy as np

from openquake.commonlib import datastore
from openquake.calculators.base import dcache
from openquake._unc.dtypes.dsg_mde import get_afes_from_dstore as afes_ds_mde
from openquake._unc.dtypes.dsg_md import get_afes_from_dstore as afes_ds_md


# Setting namespace
NS = "{http://openquake.org/xmlns/nrml/0.5}"

# Paths
PATH_CALC = "{0:s}calculations/{0:s}calc".format(NS)
PATH_UNC = "{0:s}uncertainties/".format(NS)
PATH_SRC_IDS = "{:s}sourceIDs".format(NS)
PATH_BSIDS = "{:s}branchSetID".format(NS)
PATH_ORDINAL = "{:s}branchSetOrdinal".format(NS)


class Analysis:
    """
    Stores information and provides methods required to process the results
    computed from various sources.

    :param bsets:
        A dictionary with branchset ID as keys and a dictionary with various
        information as value. Dictionary content:
        - src_ids: IDs of the sources
        - bsids: IDs of the branches in the original LTs
        - utype: Type of uncertainty
        - logictree: Type of LT (ssc or gmc)
        - ordinal: Ordinal of the branchsets in their LTs
    :param corbs_per_src_ssc:
        A dictionary
    :param corbs_bs_id_ssc:
    :param calcs:
        A dictionary with source IDs as keys and a string with the path to
        the datastore containing the results (i.e. hazard curves) as value.
    :param root_path:
        The path to the folder
    """

    def __init__(self, bsets: dict, corbs_per_src: dict, corbs_bs_id: dict,
                 calcs: dict, root_path: str = None):

        # The branch sets for which we have correlated uncertainties
        self.bsets = bsets

        # Correlated branchsets. These are two dictionaries with key the
        # branchset ID
        self.corbs_per_src = corbs_per_src
        self.corbs_bs_id = corbs_bs_id

        # A dictionary with key the IDs of the sources. The value is a string
        # with the path to the datastore containing the results.
        self.calcs = calcs

        # Path to the folder containing the datastores
        self.root_path = root_path

    @classmethod
    def read(cls, fname: str):
        """
        This method loads the information about the analysis of results from
        an .xml file.

        :param fname:
            Name of the .xml file containing information on results of the
            calculations performed and the possible correlation of
            uncertainties between the LTs of individual sources
        """

        # TODO
        # Add the following checks:
        # - We have a datastore for each source correlated
        # - The datastores are all different
        # - The original correlated branch sets must have the same number of
        #   branches

        # Set the path to the folder with the .xml file
        root_path = os.path.dirname(fname)

        # Get .xml root
        tree = ET.parse(fname)
        root = tree.getroot()

        # Reading info about calculations per individual source
        calcs = {}  # i.e. {'a': './out_a/calc_8509.hdf5', ...}
        src_ids = set()
        for calc in root.findall(PATH_CALC):
            # Check duplicated IDs
            if calc.attrib['sourceID'] in src_ids:
                msg = "Duplicated src ID in the definition of datastores"
                msg += f" Check: {calc.attrib['sourceID']}"
                raise ValueError(msg)

            # Read or compute the datastore
            if 'datastore' in calc.attrib:
                dstore = os.path.join(root_path, calc.attrib['datastore'])
            else:
                ini = os.path.join(root_path, calc.attrib['ini'])
                dstore = dcache.get(ini).filename

            # Dictionary with the path to the .hdf5 file with the datastore
            calcs[calc.attrib['sourceID']] = dstore

            # Updating the set of src IDs
            src_ids.add(calc.attrib['sourceID'])

        # Reading info about correlated uncertainties i.e. branch sets
        bsets = {}

        # Correlated branch sets per source
        corbs_per_src = {}
        corbs_bs_id = {}

        # For each branchset in the .xml with the information about
        # correlation
        for bs in root.findall(PATH_UNC):

            bsid = bs.attrib['branchSetID']
            utype = bs.attrib['uncertaintyType'].encode()
            logictree = bs.attrib['logicTree']
            src_ids = bs.findall(PATH_SRC_IDS)[0].text.split(' ')
            bsids = bs.findall(PATH_BSIDS)[0].text.split(' ')

            # Here we should check that the uncertainties in the analysis .xml
            # file are the same used for the various sources
            ordinal = []
            for sid in src_ids:
                fname = calcs[sid]
                dstore = datastore.read(fname)
                tmp = dstore.getitem('full_lt/source_model_lt')['utype']

                # This creates a list of unique uncertainty types
                utypes = list(collections.Counter(tmp))

                # Find the index of the uncertainty
                if utype in utypes:
                    ordinal.append(utypes.index(utype))
                else:
                    # We assume that in the GMM logic tree we have only one
                    # branch
                    ordinal.append(0)

            # Values:
            # - IDs of the sources involved
            # - IDs of the branches in the original LTs
            # - Type of uncertainty
            # - Type of LT (ssc or gmc)
            # - Ordinal of the branchsets in their LTs
            bsets[bsid] = {'sid': src_ids, 'bsids': bsids, 'utype': utype,
                           'logictree': logictree, 'ordinal': ordinal}
            data = {}
            for i, sid in enumerate(src_ids):
                data[sid] = {'bsid': bsids[i], 'ordinal': ordinal[i]}
            bsets[bsid] = {'utype': utype, 'logictree': logictree,
                           'data': data}

            # For each source ID we store the ordinal of the branchset
            # containing the uncertainty here considered. Note that the
            # ordinal can be either for the SSC or the GMC.
            for sid, odn in zip(src_ids, ordinal):
                corbs_per_src[(sid, int(odn), logictree)] = bsid

        # Initializing the Analysis object
        return cls(bsets, corbs_per_src, corbs_bs_id, calcs, root_path)

    # this is not used
    def get_srcIDs_with_correlations(self):
        """
        Returns a set with the IDs of the sources with correlated uncertainties
        """
        out = set()
        for bsid in self.bsets:
            out |= self.bsets[bsid]['data']
        return out

    def get_sets(self):
        """
        :returns:
            A pair of lists of sets. In the first
            each set contains source IDs sharing some correlation.
            In the second each set contains the IDs of the branch sets with
            correlations (note that the branch set ID refers to the ones
            included in the .xml file used to instantiate the `Analysis`
            object).
        """
        ssets = []
        bsets = []
        # Process all the correlated branch sets
        for bsid in sorted(self.bsets):
            found = False
            srcids = set(self.bsets[bsid]['data'])

            # If true, this source is in the current branch set
            for i, sset in enumerate(ssets):
                if srcids & sset:
                    ssets[i] |= srcids
                    bsets[i] |= {bsid}
                    found = True
                    continue
            if not found:
                ssets.append(srcids)
                bsets.append({bsid})

        # Adding uncorrelated sources
        for src_id in self.calcs:
            found = False
            for sset in ssets:
                if src_id in sset:
                    found = True
                    continue
            if not found:
                ssets.append({src_id})
                bsets.append(None)

        # in analysis_test we have
        # ssets = [{'b', 'a', 'c'}, {'d'}]
        # bsets = [{'bs2', 'bs1'}, None]
        return ssets, bsets

    def get_dstores(self):
        """
        Get the datastores instances for the sources considered in the
        analysis, sorted by source id.
        """
        return {src_id: datastore.read(fname)
                for src_id, fname in sorted(self.calcs.items())}

    def get_imtls(self):
        """
        Get the imtls
        """
        dstore = list(self.get_dstores().values())[0]
        return dstore['oqparam'].hazard_imtls

    def get_bpaths_weights(self, dstore, srcid):
        """
        :param dstore:
            A :class:`openquake.commonlib.datastore.DataStore` instance
        :param srcid:
            The ID of the source
        :returns:
            Branch paths and corresponding weights
        """
        weights = dstore['weights'][:]
        bpaths = dstore['full_lt'].rlzs['branch_path']
        return bpaths, weights

    def read_dstores(self, root_path: str, atype: str, imtstr: str):
        """
        Reads the information in the datastore for each realizations, the
        poes of the computed results (e.g. hazard curves) and, the weights
        assigned to the realizations.

        :param root_path:
            Path to the folder containing the .xml file
        :param atype:
            The type of analysis to be perfomed
        :param imtstr:
            A string defining the intensity measure type

        :returns:
            Three dictionaries with the ID of the sources as keys:
                - 'rlzs' contains, for each source, the realization and the
                   paths describing the SSC and the GMC
                - 'poes' contains the hazard curves
                - 'weights' contains the weights of all the realizations
        """
        rlzs = {}
        poes = {}
        weights = {}

        # For each source we read information in the corresponding datastore
        for key in self.calcs:
            fname = self.calcs[key]
            msg = f"Source: {key} - File: {os.path.basename(fname)}"
            logging.info(msg)

            # Create the datastore
            dstore = datastore.read(fname)
            imti = list(dstore['oqparam'].imtls).index(imtstr)

            # Read data from datastore
            if atype == 'hcurves':
                # Read HC dataset. It has the following shape S x R x I x L
                # S - number of sites
                # R - realizations
                # I - IMTs
                # L - IMLs
                poes[key] = dstore['hcurves-rlzs'][:,:,imti,:]
            elif atype == 'mde':
                # Read disagg results. Matrix shape is 7D
                binc, poes[key], _, shapes = afes_ds_mde(dstore, imti)
                if not hasattr(self, 'shapes'):
                    self.shapes = shapes
                    self.dsg_mag = dstore['disagg-bins/Mag'][:]
                    self.dsg_dst = dstore['disagg-bins/Dist'][:]
                    self.dsg_eps = dstore['disagg-bins/Eps'][:]
                else:
                    assert self.shapes[:-1] == shapes[:-1]
            elif atype == 'md':
                # Read disagg results. Matrix shape is 7D
                binc, poes[key], _, shapes = afes_ds_md(dstore, imti)
                if not hasattr(self, 'shapes'):
                    self.shapes = shapes
                    self.dsg_mag = dstore['disagg-bins/Mag'][:]
                    self.dsg_dst = dstore['disagg-bins/Dist'][:]
                else:
                    assert self.shapes[:-1] == shapes[:-1]
            elif atype == 'm':
                # Read disagg results. Matrix shape is 7D
                binc, poes[key], _, shapes = afes_ds_md(dstore, imti)
                if not hasattr(self, 'shapes'):
                    self.shapes = shapes
                    self.dsg_mag = dstore['disagg-bins/Mag'][:]
                else:
                    assert self.shapes[:-1] == shapes[:-1]

            # Read weights for all the realizations
            weights[key] = dstore['weights'][:]

            # Read realizations
            rlz = []
            ssc = []
            gmc = []
            for k in dstore['full_lt'].rlzs['branch_path']:
                smpath, gspath = k.split('~')
                ssc.append(smpath)
                gmc.append(gspath)
                rlz.append(k)

            # This dictionary [where keys are the source IDs] contains two
            # arrays (with the indexes of the realizations for the SSC and
            # GMC) and one list with the paths of all the realizations
            rlzs[key] = [np.array(ssc), np.array(gmc), rlz]

        return rlzs, poes, weights


def get_patterns(rlzs: dict, an01: Analysis, verbose=False):
    """
    Computes the patterns needed to select realizations from a source-specific
    logic tree

    :param rlzs:
        A dictionary with information on all the realizations. The key is the
        source ID.
    :param an01:
        An instance of :class:`openquake._unc.analysis.Analysis`
    :param verbose:
        A boolean controlling the logging
    :returns:
        A dictionary with key the ID of the branch set with correlated
        uncertainties (IDs as defined in the `analysis.xml` input file) and
        with value a dictionary with key the IDs of the sources with correlated
        uncertainties and with values a list of patterns than can be used to
        select the realizations belonging to each set of correlated
        uncertainties.
    """
    patterns = {}
    for bsid in an01.bsets:

        if verbose:
            logging.info(f"Creating patterns for branch set {bsid}")

        # Processing the sources in the branchset bsid
        patterns[bsid] = {}
        for srcid in an01.bsets[bsid]['data']:
            if verbose:
                logging.info(f"   Source: {srcid}")
                logging.debug(rlzs[srcid])

            # Create the general pattern. This will select everything
            # e.g. '.+.+.+~.+'
            patterns[bsid][srcid] = {}
            smpaths, gspaths, _ = rlzs[srcid]
            nssc = len(smpaths[0])
            tmpssc = '..' + ''.join('.' for i in range(2, nssc))
            ngmc = len(gspaths[0])
            tmpgmc = ''.join('.' for i in range(ngmc))
            pattern = '^' + tmpssc + '~' + tmpgmc
            # Find the index in the pattern where we replace the '.' with the
            # ID of the branches that are correlated.
            ordinal = int(an01.bsets[bsid]['data'][srcid]['ordinal'])
            # + 1 for the initial ~
            # + 1 for the first element (that uses two letters)
            idx = ordinal + 1 + 1
            is_gmc = an01.bsets[bsid]['logictree'] == 'gmc'
            if is_gmc:
                paths = rlzs[srcid][1]
                idx += nssc
            else:
                paths = [bpath[ordinal + 1] for bpath in rlzs[srcid][0]]
            temp_patterns = []
            for key in np.unique(paths):
                tmp = pattern[:idx] + key + pattern[idx+1:]
                temp_patterns.append(tmp)
            patterns[bsid][srcid] = temp_patterns

    return patterns


def get_hcurves_ids(rlzs, patterns, weights):
    """
    Given the realizations for each source as specified in the `rlzs`
    dictionary, the patterns describing the

    :param rlzs:
        A dictionary with keys the IDs of the sources. The values are lists,
        each one with three elements: one containing the description of the
        paths for the SSC, one for the GMC and one with the overall path of
        each realisation.
    :param patterns:
        A dictionary with keys the IDs of the branch sets of correlated
        uncertainties. The value is a dictionary with key the source ID.
        The values are lists of strings. Each string is a regular expression
        (e.g.  ^.+A.+.+~.+') that can be used to select the subset of
        realizations involving the current source that are correlated.
    :param weights:
        A dictionary with keys the IDs of the sources and an array as value.
        These arrays contain the weights assigned to each realisation admitted
        by the logic tree for a single source.
    :returns:
        A tuple with two dictionaries.
    """

    # These are two dictionaries with key the branch set ID and value a
    # dictionary with key the source IDs
    grp_hcurves = {}
    grp_weights = {}
    for bsid in patterns:
        grp_hcurves[bsid] = {}
        grp_weights[bsid] = {}
        for srcid in patterns[bsid]:
            # Loop over the patterns of all the realizations for a given source
            grp_hcurves[bsid][srcid] = []
            grp_weights[bsid][srcid] = []
            for p in patterns[bsid][srcid]:
                tmp_idxs = []
                wei = 0.0
                for i, rlz in enumerate(rlzs[srcid][2]):
                    if re.search(p, rlz):
                        tmp_idxs.append(i)
                        wei += weights[srcid][i]
                grp_hcurves[bsid][srcid].append(tmp_idxs)
                grp_weights[bsid][srcid].append(wei)
    return grp_hcurves, grp_weights
