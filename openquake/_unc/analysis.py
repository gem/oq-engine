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
import pandas as pd

from openquake.calculators.base import dcache
from openquake._unc.dsg_mde import get_afes_from_dstore as afes_from

# Setting namespace
NS = "{http://openquake.org/xmlns/nrml/0.5}"

# Paths
PATH_CALC = "{0:s}calculations/{0:s}calc".format(NS)
PATH_UNC = "{0:s}uncertainties/".format(NS)
PATH_SRCIDS = "{:s}sourceIDs".format(NS)


def get_weights(smlt, utype):
    """
    Get the weights associated to the given uncertainty type
    """
    return smlt[smlt['utype'] == utype]['weight']


def check_consistent(utype, smlts):
    """
    Make sure all the SMLTs have consistent weights
    """
    ws = get_weights(smlts[0], utype)
    for smlt in smlts[1:]:
        weights = get_weights(smlt, utype)
        assert len(weights) == len(ws), (len(weights), len(ws))
        assert (weights == ws).all(), (weights, ws)


class Analysis:
    """
    Stores information and provides methods required to process the results
    computed from various sources.

    :param utypes:
        A list of uncertainty types as listed in the analysis.xml file
    :param dfs:
        A list of DataFrames (one for each utype) with keys
        - srcid: IDs of the sources
        - ipath: indices of the branchsets
    :param dstores:
        A dictionary with source IDs as keys and a string with the path to
        the datastore containing the results (i.e. hazard curves) as value.
    :param fname:
        The path to the analysis.xml file
    """
    def __init__(self, utypes: dict, dfs: dict,
                 dstores: dict, fname: str, seed: int):

        # The branch sets for which we have correlated uncertainties
        self.utypes = utypes
        self.dfs = dfs

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
        utypes = []
        dfs = []

        # For each branchset in the .xml
        for unc, bs in enumerate(root.findall(PATH_UNC)):
            utype = bs.attrib['uncertaintyType'].encode()
            srcids = bs.findall(PATH_SRCIDS)[0].text.split(' ')

            # Here we should check that the uncertainties in the analysis .xml
            # file are the same used for the various sources
            ipath = []
            smlts = []
            for srcid in srcids:
                dstore = dstores[srcid]
                # List of unique uncertainty types
                smlt = dstore.getitem('full_lt/source_model_lt')[:]
                smlts.append(smlt)
                utype2ord = {u: i for i, u in enumerate(
                    collections.Counter(smlt['utype']))}
                # Find the path index of the uncertainty branchset
                i = -1 if utype == b'gmpeModel' else utype2ord[utype]
                ipath.append(i)

            check_consistent(utype, smlts)
            utypes.append(utype)
            dfs.append(pd.DataFrame(dict(srcid=srcids, ipath=ipath)))

        # Initializing the Analysis object
        self = cls(utypes, dfs, dstores, fname, seed)
        return self

    def to_dframe(self):
        """
        Debug utility print the dfs as a DataFrame
        """
        for unc, df in enumerate(self.dfs):
            df['unc'] = unc
        return pd.concat(self.dfs).set_index('unc')

    # used in propagate_uncertainties
    def get_sets(self):
        """
        :returns:
            Two lists of sets. The first has source IDs sharing correlation.
            The second has indices to the correlated uncertainties defined in
            the analysis.xml file.
        """
        ssets = []
        usets = []
        # Process all the correlated branch sets
        for unc, df in enumerate(self.dfs):
            srcids = set(df['srcid'])
            for uset, sset in zip(usets, ssets):
                # if any source is in the current branch set
                if srcids & sset:
                    sset |= srcids
                    uset |= {unc}
                    break
            else:
                # at the first loop ssets and usets are empty
                ssets.append(srcids)
                usets.append({unc})

        # Adding uncorrelated sources
        for src_id in self.dstores:
            found = any(src_id in sset for sset in ssets)
            if not found:
                ssets.append({src_id})
                usets.append(set())

        # in analysis_test we have
        # ssets = [{'b', 'a', 'c'}, {'d'}]
        # usets = [{0, 1}, None]
        return ssets, usets

    def get_imtls(self):
        """
        Get the imtls
        """
        dstore = list(self.dstores.values())[0]
        return dstore['oqparam'].hazard_imtls

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

    def get_patterns(self, rlzs: dict, verbose=False):
        """
        Computes the patterns needed to select realizations from a
        source-specific logic tree

        :param rlzs:
            A dictionary with information on all the realizations.
            The key is the source ID.
        :param verbose:
            A boolean controlling the logging
        :returns:
            A list of dictionaries, one for each uncertainty in the
            `analysis.xml`, with key the IDs of the sources with
            correlated uncertainties and with values a list of patterns than
            can be used to select the realizations belonging to each set of
            correlated uncertainties.
        """
        patterns = []
        for unc, df in enumerate(self.dfs):
            if verbose:
                logging.info(f"Creating patterns for branch set {unc}")

            # Processing the sources in the branchset unc
            pat = {}
            patterns.append(pat)
            for srcid, ipath in zip(df['srcid'], df['ipath']):
                if verbose:
                    logging.info(f"   Source: {srcid}")
                    logging.debug(rlzs[srcid])

                pat[srcid] = {}
                rpaths = rlzs[srcid]
                n = len(rpaths[0])
                # Create the general pattern. This will select everything
                pattern = ''.join('.' for i in range(2, n)) + '~.'
                # Find the index iwhere we replace the '.' with the
                # ID of the branches that are correlated
                if ipath == -1:
                    ipath = n - 1
                chars = [path[ipath] for path in rpaths]
                patt = [pattern[:ipath] + char + pattern[ipath+1:]
                        for char in np.unique(chars)]
                pat[srcid] = patt
        """# in the analysis_test, `patterns` is the following list:
        unc=0: setLowerSeismDepthAbsolute: b c
        unc=1: gmpeModel: a b
        [{'b': ['..A.~.', '..B.~.'],
          'c': ['...A.~.', '...B.~.']},
         {'a': ['..~A', '..~B', '..~C', '..~D'],
          'b': ['....~A', '....~B', '....~C', '....~D']}]
        """
        return patterns


def rlz_groups(rlzs, patterns):
    """
    Given the realizations for each source and the patterns returned by
    get_patterns return a list of dictionaries srcid -> rlzids, one
    for each uncertainty.
    """
    hcurves = {}
    for unc, pat in enumerate(patterns):
        for srcid in pat:
            # Loop over the patterns of all the realizations for a given source
            hcurves[unc, srcid] = [
                [i for i, rlz in enumerate(rlzs[srcid]) if re.match(p, rlz)]
                for p in pat[srcid]]
    return hcurves
