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
PATH_BSIDS = "{:s}branchSetID".format(NS)


class Analysis:
    """
    Stores information and provides methods required to process the results
    computed from various sources.

    :param utypes:
        A list of uncertainty types as listed in the analysis.xml file
    :param bsets:
        A list of dictionaries (one for each utype) with keys
        - srcid: IDs of the sources
        - bsid: IDs of the branches in the original LTs
        - ipath: Ipaths of the branchsets in their LTs
    :param dstores:
        A dictionary with source IDs as keys and a string with the path to
        the datastore containing the results (i.e. hazard curves) as value.
    :param fname:
        The path to the analysis.xml file
    """
    def __init__(self, utypes: dict, bsets: dict,
                 dstores: dict, fname: str, seed: int):

        # The branch sets for which we have correlated uncertainties
        self.utypes = utypes
        self.bsets = bsets

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
        utypes = []
        bsets = []

        # For each branchset in the .xml
        for bs in root.findall(PATH_UNC):
            utype = bs.attrib['uncertaintyType'].encode()
            srcids = bs.findall(PATH_SRCIDS)[0].text.split(' ')
            bsids = bs.findall(PATH_BSIDS)[0].text.split(' ')

            # Here we should check that the uncertainties in the analysis .xml
            # file are the same used for the various sources
            ipath = []
            for srcid in srcids:
                dstore = dstores[srcid]
                # List of unique uncertainty types
                smlt = dstore.getitem('full_lt/source_model_lt')[:]
                utype2ord = {u: i for i, u in enumerate(
                    collections.Counter(smlt['utype']))}
                # Find the ipath of the uncertainty branchset, 0 for gmpeModel
                ipath.append(utype2ord.get(utype, 0))

            utypes.append(utype)
            bsets.append({'srcid': srcids, 'bsid': bsids, 'ipath': ipath})

        # Initializing the Analysis object
        self = cls(utypes, bsets, dstores, fname, seed)
        return self

    def to_dframe(self):
        """
        Debug utility print the bsets as a DataFrame
        """
        dic = {'unc': [], 'bsid': [], 'srcid': [], 'ipath': []}
        for unc, d in enumerate(self.bsets):
            dic['unc'].extend([unc] * len(d['bsid']))
            dic['bsid'].extend(d['bsid'])
            dic['srcid'].extend(d['srcid'])
            dic['ipath'].extend(d['ipath'])
        return pd.DataFrame(dic).set_index('unc')


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
        for unc, dic in enumerate(self.bsets):
            srcids = set(dic['srcid'])
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
                usets.append(None)

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

    def get_rpaths_weights(self, srcid):
        """
        :param srcid:
            The ID of a source
        :returns:
            Realization paths and corresponding weights
        """
        dstore = self.dstores[srcid]
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
        for unc, dic in enumerate(self.bsets):
            if verbose:
                logging.info(f"Creating patterns for branch set {unc}")

            # Processing the sources in the branchset unc
            pat = {}
            patterns.append(pat)
            for srcid, ipath in zip(dic['srcid'], dic['ipath']):
                if verbose:
                    logging.info(f"   Source: {srcid}")
                    logging.debug(rlzs[srcid])

                pat[srcid] = {}
                rpaths = rlzs[srcid]
                smpaths = [r[:-2] for r in rpaths]
                gspaths = [r[-1] for r in rpaths]
                nssc = len(smpaths[0])
                ssc = '..' + ''.join('.' for i in range(2, nssc))
                ngmc = len(gspaths[0])
                gmc = ''.join('.' for i in range(ngmc))
                # Create the general pattern. This will select everything
                pattern = '^' + ssc + '~' + gmc
                # Find the index iwhere we replace the '.' with the
                # ID of the branches that are correlated
                # + 1 for the first element (that uses two letters)
                idx = ipath + 1 + 1
                is_gmc = self.utypes[unc] == b'gmpeModel'
                if is_gmc:
                    paths = gspaths
                    idx += nssc
                    ipath = 0
                else:
                    paths = [path[ipath + 1] for path in smpaths]
                patt = [pattern[:idx] + path + pattern[idx+1:]
                        for path in np.unique(paths)]
                pat[srcid] = patt
        """# in the analysis_test, `patterns` is the following list:
        [{'b': ['^...A.~.', '^...B.~.'],
          'c': ['^....A.~.', '^....B.~.']},
         {'a': ['^...~A', '^...~B', '^...~C', '^...~D'],
          'b': ['^.....~A', '^.....~B', '^.....~C', '^.....~D']}]
        """
        return patterns


def get_hcurves_ids(rlzs, patterns):
    """
    Given the realizations for each source as specified in the `rlzs`
    dictionary, the patterns describing the

    :param rlzs:
        A dictionary with keys the IDs of the sources. The values are lists
        of pairs (smpaths, gspaths) for each realisation.
    :param patterns:
        A list of ictionaries with key the source ID.
        The values are lists of strings. Each string is a regular expression
        (e.g.  ^.+A.+.+~.+') that can be used to select the subset of
        realizations involving the current source that are correlated.
    :returns:
        A list of dictionaries srcid -> idxs
    """
    grp_hcurves = []
    for pat in patterns:
        hcurves = {}
        for srcid in pat:
            rpath = rlzs[srcid]
            # Loop over the patterns of all the realizations for a given source
            hcurves[srcid] = []
            for p in pat[srcid]:
                idxs = []
                for i, rlz in enumerate(rpath):
                    if re.search(p, rlz):
                        idxs.append(i)
                hcurves[srcid].append(idxs)
        grp_hcurves.append(hcurves)
    return grp_hcurves
