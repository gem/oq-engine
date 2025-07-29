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
import pathlib
import logging
import numpy as np
import configparser

from typing import Union
from openquake.baselib import sap
from openquake.baselib import hdf5
from openquake._unc.analysis import Analysis, rlz_groups
from openquake._unc.processing.sampling import sampling
from openquake._unc.processing.convolution import convolution


def prepare(fname: str, atype: str, imtstr: str=None):
    """
    Prepare the information needed for the analysis.

    :param fname:
        The name of the .xml containing the input information
    :param atype:
        The type of analysis. Admitted options are:
            - 'hcurves'
            - 'mde', 'md', 'm'
    :param imtstr:
        The string defining the IMT considered in this analysis
    :returns:
        A tuple with the following four elements:
            - ssets: A list of sets. Each set contains the IDs of sources
                belonging to it.
            - usets: A list of sets. Each set contains the IDs of correlated
                branchsets.
            - grp_curves: a dictionary of dictionaries. The keys at the first
                level are the IDs of the correlated branches. The keys at the
                second level are the IDs of the sources. The values are the
                indexes of the realisations.
            - an01: an instance of :class:`openquake._unc.analysis.Analysis`
    """

    # Set the random seed and create the `analysis` object
    an01 = Analysis.read(fname, seed=10)

    # Read the datastores specified in the input path
    rlzs, _, weights = an01.read_dstores(atype, imtstr)

    # Correlated branchsets. For test case 2, the correlation between 'a' and
    # 'b' is the GMM model while between 'b' and 'c' it's the seismogenic
    # thickness.

    # Get the patterns (with wildcards) that can be used to select the
    # correlated realizations.
    patterns = an01.get_patterns(rlzs)

    # dictionary (unc, srcid) -> groups of realizations
    groups = rlz_groups(rlzs, patterns)

    return groups, an01


def propagate(fname_config: Union[str, dict], calc_type: str='hazard_curves',
              **kwargs):
    """
    Given a configuration file, this code returns either a set of realizations
    representing the results (in case of an analysis based on sampling) or a
    the result of a convolution analysis.

    :param fname_config:
        The name of a .toml formatted file with the configuration settings or
        a dictionary with the content of a .toml configuration file.
    :param calc_type:
        The calculation type. Default is the calculation of 'hazard_curves'.
        The other supported option is 'disaggregation'.
    :returns:
        In case of an analysis based on convolution, it returns a tuple
        containing: 'fhis' a list of arrays with length equal to the number of
        IMTs (each array contains the results of the analysis i.e.  a discrete
        distribution of the IMLs), 'fmin_pow' a vector with size equal to the
        number of IMTs containing the minimum exponent used to represent the
        poes, 'fnum_pow' a vector with size equal to the number of IMTs
        containing the number of powers used to represent the histogram with
        the poes, 'an01' an instance of
        :class:`openquake._unc.analysis.Analysis`

        In case of an analysis based on sampling, it returns a tuple
        containing: 'imls' a dictionary with keys the names of the IMTs and
        values the imls, 'afes' a large matrix with the samples and, 'an01'
        an instance of :class:`openquake._unc.analysis.Analysis`.
    """
    fmt = "%(asctime)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt, datefmt='%H:%M:%S',)

    # Check calculation option
    calc_types = ['hazard_curves', 'disaggregation']
    msg = f'Calculation type {calc_type} not supported'
    assert calc_type in calc_types, msg

    # Configuration
    if isinstance(fname_config, str):
        conf_file_path = os.path.dirname(fname_config)
        conf = configparser.ConfigParser()
        conf.read(fname_config)
    elif isinstance(fname_config, dict):
        conf = fname_config
        conf_file_path = conf['analysis']['conf_file_path']
    else:
        raise ValueError('Unknown format for input')

    # Name of the .xml file with the information needed to perform the analysis
    fname = os.path.join(conf_file_path, conf['analysis']['input_file'])
    assert os.path.exists(fname), fname

    # Read the name of the output folder in the configuration
    folder_out = os.path.join(conf_file_path, conf['output']['output_folder'])

    # Override the path to the output folder, with the path provided in the
    # call to this function
    if kwargs.get('override_folder_out', None) is not None:
        folder_out = kwargs['override_folder_out']

    # create folder_out if needed
    pathlib.Path(folder_out).mkdir(parents=True, exist_ok=True)

    # Define the type of analysis
    analysis_type = conf['analysis']['type']
    assert analysis_type in ['convolution', 'sampling']
    atype = conf['analysis'].get('atype')
    assert atype in ['hcurves', 'mde', 'md', 'm']
    section_analysis = conf['analysis']
    res = section_analysis.get('resolution', None)
    nsam = section_analysis.get('number_of_samples', None)
    imt = section_analysis.get('imt')

    if res is not None:
        res = int(res)
    if nsam is not None:
        nsam = int(nsam)

    # Figure folder
    fig_folder = os.path.join(folder_out, "figs")
    pathlib.Path(fig_folder).mkdir(parents=True, exist_ok=True)

    # Preparing required info
    grps, an01 = prepare(fname, atype, imt)

    if analysis_type == 'convolution':
        # getting the frequency histograms
        # for the intensity levels considered
        logging.info("Running convolution")
        h = convolution(an01, grps, imt, atype, res)
        return h, an01

    elif analysis_type == 'sampling':
        logging.info("Running sampling")
        imls, afes = sampling(an01, grps, nsam)
        return imls, afes, an01

    raise ValueError(f'Calculation type {analysis_type} not supported')


def write_results_sampling(fname: str, imls: np.ndarray, afes: np.ndarray):
    """
    Save the results to a .hdf5 file

    :param fname:
        Name of the output .hdf5 file
    :param imls:
        Intentity measure levels
    :param afes:
        List of arrays with the results of the sampling procedure
    """
    with hdf5.File(fname, "w") as fout:
        group = fout.create_group("imls")
        for key in imls:
            group.create_dataset(key, data=imls[key])
        fout.create_dataset("afes", data=afes)


def main(fname_config: str):
    """
    Propagate epistemic uncertainties computed for individual sources. The
    input file is an .xml formatted file that specifies the position of the
    input and the possible correlations between uncertainties defined for
    individual sources.
    """
    propagate(fname_config)


DESCR = "File with configuration information"
main.fname_config = DESCR

if __name__ == '__main__':
    sap.run(main)
