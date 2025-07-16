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

import re
import os
import numpy as np
import pandas as pd
from glob import glob
from openquake.baselib import hdf5
from openquake.commonlib.datastore import read
from openquake._unc.bins import get_bins_from_params


# TODO: read directly from the dstore
def read_hazard_curve_csv(filename):
    """
    Read a csv file containing hazard curves.
    :param str filename:
        Name of the .csv file containing the data
    :return:
        A tuple with the following information:
            - Longitudes
            - Latitudes
            - PoEs
            - dictionary of metadata
            - IMLs
    """
    aw = hdf5.read_csv(filename)
    imls = [float(col[:4]) for col in aw.dtype.names[3:]]
    poes = np.hstack([aw[col] for col in aw.dtype.names[3:]])
    return aw['lon'], aw['lat'], poes, vars(aw), imls


def get_mean(fhis, fmin_pow, fnum_pow, res):
    """
    Compute the weighted mean given an histogram

    :param fhis:
    :param fmin_pow:
    :param fnum_pow:
    :param res:
    :returns:
        A list
    """
    mean = []
    for his, mpow, npow in zip(fhis, fmin_pow, fnum_pow):
        bins = get_bins_from_params(mpow, res, npow)
        mids = bins[:-1] + np.diff(bins)/2
        mean.append(np.average(mids, weights=his))
    return mean


def weighted_percentile(data, weights, perc):
    """
    Given a vector of values and one of associated weights computes the
    requested percentile.

    :param data:
        Vector with data
    :param weights:
        A vector of weights (same cardinality of data)
    :param perc:
        Percentile in [0-1]!
    :returns:
        A float with the value for a given percentile
    """
    ix = np.argsort(data)
    data = data[ix]  # sort data
    weights = weights[ix]  # sort weights
    # 'like' a CDF function
    cdf = (np.cumsum(weights) - 0.5 * weights) / np.sum(weights)
    return np.interp(perc, cdf, data)


# TODO: use dstore, not folder
def get_rlzs(folder: str) -> pd.DataFrame:
    """
    Create a DataFrame with the list of realisations.
    """
    fmt = 'realizations_*.csv'
    fname = glob(os.path.join(folder, fmt))
    print('Found: {:s}'.format(fname[0]))
    m = re.match(".*_(\\d*)\\.csv$", fname[0])
    calc_id = m.group(1)
    return pd.read_csv(fname[0]), calc_id


# TODO: use dstore, not folder
def get_mean_hc(folder: str, imt: str):
    fmt = 'hazard_curve-mean-{:s}*.csv'
    fname = glob(os.path.join(folder, fmt.format(imt)))
    print('Found: {:s}'.format(fname[0]))
    return read_hazard_curve_csv(fname[0])


# TODO: use dstore, not folder
def get_quantile_hc(folder, imt, quantile):
    tmps = 'quantile_curve-{:s}-{:s}*.csv'.format(str(quantile), imt)
    fname = glob(os.path.join(folder, tmps))
    return read_hazard_curve_csv(fname[0])


# TODO: use dstore, not folder
def get_rlz_hcs(folder, imt):
    fmt = 'hazard_curve-rlz*-{:s}_*.csv'
    poes = []
    pattern = os.path.join(folder, fmt.format(imt))
    for i, fname in enumerate(sorted(glob(pattern))):
        if i == 0:
            m = re.match(".*_(\\d*)\\.csv$", fname)
            calc_id = m.group(1)
        lo, la, poe, hea, iml = read_hazard_curve_csv(fname)
        poes.append(poe)
    return lo, la, np.array(poes), hea, np.squeeze(iml), calc_id


# TODO: use dstore, not folder
def get_lt_info_from_datastore(folder, calc_id):
    fname = os.path.join(folder, "calc_{:s}.hdf5".format(calc_id))
    return _get_lt_info_from_datastore(fname)


def _get_lt_info_from_datastore(fname):
    dstore = read(fname)
    ssclt = dstore.read_df('full_lt/source_model_lt')
    gmclt = dstore.read_df('full_lt/gsim_lt')
    sm_data = dstore.read_df('full_lt/sm_data')
    return ssclt, gmclt, sm_data


def get_correlation(ssclts, gmclts, rlzs, comtx):

    for i, ra in rlzs[0].iterrows():
        for j, rb in rlzs[1].iterrows():
            m = re.search('\\d*\\~(\\d*)', ra.branch_path)
            rza = int(m.group(1))
            m = re.search('\\d*\\~(\\d*)', rb.branch_path)
            rzb = int(m.group(1))
            sera = gmclts[0].iloc[rza]
            serb = gmclts[0].iloc[rzb]
            if (sera.uncertainty == serb.uncertainty):
                comtx[i, j] = 1
                comtx[j, i] = 1

