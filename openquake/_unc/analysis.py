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

from openquake.calculators.base import dcache
from openquake._unc.dsg_mde import get_afes_from_dstore as afes_from

# Setting namespace
NS = "{http://openquake.org/xmlns/nrml/0.5}"

# Paths
PATH_CALC = "{0:s}calculations/{0:s}calc".format(NS)
PATH_UNC = "{0:s}uncertainties/".format(NS)
PATH_SRCIDS = "{:s}sourceIDs".format(NS)
PATH_BSIDS = "{:s}branchSetID".format(NS)
PATH_ORDINAL = "{:s}branchSetOrdinal".format(NS)


class Analysis:
    """
    Stores information and provides methods required to process the results
    computed from various sources.

    :param bsets:
        A dictionary with branchset ID as keys and a dictionary with various
        information as value. Dictionary content:
        - srcids: IDs of the sources
        - bsids: IDs of the branches in the original LTs
        - utype: Type of uncertainty
        - ordinal: Ordinal of the branchsets in their LTs
    :param corbs_per_src:
        A dictionary
    :param dstores:
        A dictionary with source IDs as keys and a string with the path to
        the datastore containing the results (i.e. hazard curves) as value.
    :param fname:
        The path to the analysis.xml file
    """
    def __init__(self, utypes: dict, bsets: dict, corbs_per_src: dict,
                 dstores: dict, fname: str, seed: int):

        # The branch sets for which we have correlated uncertainties
        self.utypes = utypes
        self.bsets = bsets

        # Correlated branchsets. These are two dictionaries with key the
        # branchset ID
        self.corbs_per_src = corbs_per_src

        # A dictionary with key the IDs of the sources. The value is a string
        # with the path to the datastore containing the results.
        self.dstores = dstores
        itimes = [dstore['oqparam'].investigation_time
                  for dstore in dstores.values()]
        self.itime, = np.unique(itimes)

        # Path to the folder containing the datastores
        self.fname = fname
        self.rng = np.random.default_rng(seed)  # used in sampling

    @classmethod
    def read(cls, fname: str, seed: int=10):
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
        root = ET.parse(fname).getroot()

        # Reading info about calculations per individual source
        dstores = {}  # i.e. {'a': 'job_a.ini', ...}
        srcids = set()
        for calc in root.findall(PATH_CALC):
            # Check duplicated IDs
            if calc.attrib['sourceID'] in srcids:
                msg = "Duplicated src ID in the definition of datastores"
                msg += f" Check: {calc.attrib['sourceID']}"
                raise ValueError(msg)

            # Read or compute the datastore
            ini = os.path.join(root_path, calc.attrib['ini'])
            dstores[calc.attrib['sourceID']] = dcache.get(ini)

            # Updating the set of src IDs
            srcids.add(calc.attrib['sourceID'])

        # Branch sets
        utypes = {}
        bsets = {}

        # Correlated branch sets per source
        corbs_per_src = {}

        # For each branchset in the .xml
        for bs in root.findall(PATH_UNC):

            bsid = bs.attrib['branchSetID']
            utype = bs.attrib['uncertaintyType'].encode()
            srcids = bs.findall(PATH_SRCIDS)[0].text.split(' ')
            bsids = bs.findall(PATH_BSIDS)[0].text.split(' ')

            # Here we should check that the uncertainties in the analysis .xml
            # file are the same used for the various sources
            ordinal = []
            for srcid in srcids:
                dstore = dstores[srcid]
                # List of unique uncertainty types
                us = dstore.getitem('full_lt/source_model_lt')['utype']
                us = list(collections.Counter(us))
                # Find the index of the uncertainty
                try:
                    idx = us.index(utype)
                except ValueError:  # for gmpeModel there ia a single bset
                    idx = 0
                ordinal.append(idx)

            utypes[bsid] = utype
            bsets[bsid] = {srcid: {'bsid': bsids[i], 'ordinal': ordinal[i]}
                           for i, srcid in enumerate(srcids)}

            # For each source ID we store the ordinal of the branchset
            # containing the uncertainty here considered. Note that the
            # ordinal can be either for the SSC or the GMC.
            for srcid, odn in zip(srcids, ordinal):
                corbs_per_src[srcid, odn] = bsid

        # Initializing the Analysis object
        self = cls(utypes, bsets, corbs_per_src, dstores, fname, seed)
        return self

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
            srcids = set(self.bsets[bsid])

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
        for src_id in self.dstores:
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

    def get_imtls(self):
        """
        Get the imtls
        """
        dstore = list(self.dstores.values())[0]
        return dstore['oqparam'].hazard_imtls

    def get_rpaths_weights(self, dstore, srcid):
        """
        :param dstore:
            A :class:`openquake.commonlib.datastore.DataStore` instance
        :param srcid:
            The ID of the source
        :returns:
            Realization paths and corresponding weights
        """
        weights = dstore['weights'][:]
        bpaths = dstore['full_lt'].rlzs['branch_path']
        return bpaths, weights

    def read_dstores(self, atype: str, imtstr: str):
        """
        Reads the information in the datastore for each realizations, the
        poes of the computed results (e.g. hazard curves) and, the weights
        assigned to the realizations.

        :param atype:
            The type of analysis to be performed
        :param imtstr:
            A string defining the intensity measure type

        :returns:
            Three dictionaries with the ID of the sources as keys:
                - 'rlzs' contains, for each source, the
                   paths describing the SSC and the GMC
                - 'poes' contains the hazard curves
                - 'weights' contains the weights of all the realizations
        """
        rlzs = {}
        poes = {}
        weights = {}

        # For each source we read information in the corresponding datastore
        for key, dstore in self.dstores.items():
            fname = dstore.filename
            msg = f"Source: {key} - File: {os.path.basename(fname)}"
            logging.info(msg)

            # Read data from datastore
            imti = list(dstore['oqparam'].imtls).index(imtstr)
            if atype == 'hcurves':
                # Read HC dataset. It has the following shape S x R x I x L
                # S - number of sites
                # R - realizations
                # I - IMTs
                # L - IMLs
                poes[key] = dstore['hcurves-rlzs'][:,:,imti,:]
            elif atype == 'mde':
                # Read disagg results. Matrix shape is 7D
                binc, poes[key], _, shapes = afes_from(
                    dstore, 'Mag_Dist_Eps', imti)
                if not hasattr(self, 'shapes'):
                    self.shapes = shapes
                    self.dsg_mag = dstore['disagg-bins/Mag'][:]
                    self.dsg_dst = dstore['disagg-bins/Dist'][:]
                    self.dsg_eps = dstore['disagg-bins/Eps'][:]
                else:
                    assert self.shapes[:-1] == shapes[:-1]
            elif atype == 'md':
                # Read disagg results. Matrix shape is 7D
                binc, poes[key], _, shapes = afes_from(dstore, 'Mag_Dist', imti)
                if not hasattr(self, 'shapes'):
                    self.shapes = shapes
                    self.dsg_mag = dstore['disagg-bins/Mag'][:]
                    self.dsg_dst = dstore['disagg-bins/Dist'][:]
                else:
                    assert self.shapes[:-1] == shapes[:-1]
            elif atype == 'm':
                # Read disagg results. Matrix shape is 7D
                binc, poes[key], _, shapes = afes_from(dstore, 'Mag', imti)
                if not hasattr(self, 'shapes'):
                    self.shapes = shapes
                    self.dsg_mag = dstore['disagg-bins/Mag'][:]
                else:
                    assert self.shapes[:-1] == shapes[:-1]

            # Read weights for all the realizations
            weights[key] = dstore['weights'][:]

            # Read realizations
            rlzs[key] = dstore['full_lt'].rlzs['branch_path']

        return rlzs, poes, weights

    def extract_afes_rlzs(self, mag_dst_rlz, weights):
        """
        Extract nonzero afes and indices from the array mag_dst_rlz,
        by averaging on the realization weights.
        """
        oute = []
        idxe = []
        cnt = 0
        Ma, D, R = mag_dst_rlz.shape
        for imag in range(Ma):
            for idst in range(D):
                poes = mag_dst_rlz[imag, idst, :]
                poes[poes > 0.99999] = 0.99999
                afes = -np.log(1. - poes) / self.itime
                afe = np.sum(afes * weights)
                if afe > 0:
                    oute.append(afe)
                    idxe.append(cnt)
                cnt += 1
        return oute, idxe


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
        for srcid in an01.bsets[bsid]:
            if verbose:
                logging.info(f"   Source: {srcid}")
                logging.debug(rlzs[srcid])

            patterns[bsid][srcid] = {}
            rpaths = rlzs[srcid]
            smpaths = [r[:-2] for r in rpaths]
            gspaths = [r[-1] for r in rpaths]
            nssc = len(smpaths[0])
            ssc = '..' + ''.join('.' for i in range(2, nssc))
            ngmc = len(gspaths[0])
            gmc = ''.join('.' for i in range(ngmc))
            # Create the general pattern. This will select everything
            pattern = '^' + ssc + '~' + gmc
            # Find the index in the pattern where we replace the '.' with the
            # ID of the branches that are correlated.
            ordinal = an01.bsets[bsid][srcid]['ordinal']

            # + 1 for the first element (that uses two letters)
            idx = ordinal + 1 + 1
            is_gmc = an01.utypes[bsid] == b'gmpeModel'
            if is_gmc:
                paths = gspaths
                idx += nssc
                ordinal = 0
            else:
                paths = [path[ordinal + 1] for path in smpaths]
            patt = [pattern[:idx] + path + pattern[idx+1:]
                    for path in np.unique(paths)]
            patterns[bsid][srcid] = patt
    """# in the analysis_test, `patterns` is the following dictionary:
    {'bs1': {'b': ['^...A.~.', '^...B.~.'],
             'c': ['^....A.~.', '^....B.~.']},
     'bs2': {'a': ['^...~A', '^...~B', '^...~C', '^...~D'],
             'b': ['^.....~A', '^.....~B', '^.....~C', '^.....~D']}}
    """
    return patterns


def get_hcurves_ids(rlzs, patterns, weights):
    """
    Given the realizations for each source as specified in the `rlzs`
    dictionary, the patterns describing the

    :param rlzs:
        A dictionary with keys the IDs of the sources. The values are lists
        of pairs (smpaths, gspaths) for each realisation.
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
            rpath = rlzs[srcid]
            ws = weights[srcid]

            # Loop over the patterns of all the realizations for a given source
            grp_hcurves[bsid][srcid] = []
            grp_weights[bsid][srcid] = []
            for p in patterns[bsid][srcid]:
                idxs = []
                wei = 0.0
                for i, rlz in enumerate(rpath):
                    if re.search(p, rlz):
                        idxs.append(i)
                        wei += ws[i]
                grp_hcurves[bsid][srcid].append(idxs)
                grp_weights[bsid][srcid].append(wei)
    return grp_hcurves, grp_weights
