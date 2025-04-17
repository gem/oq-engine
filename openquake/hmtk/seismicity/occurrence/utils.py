# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

import numpy as np


def recurrence_table(mag, dmag, year, time_interval=None):
    """
    Table of recurrence statistics for each magnitude
    [Magnitude, Number of Observations, Cumulative Number
    of Observations >= M, Number of Observations
    (normalised to annual value), Cumulative Number of
    Observations (normalised to annual value)]
    Counts number and cumulative number of occurrences of
    each magnitude in catalogue

    :param numpy.ndarray mag:
        Catalog matrix magnitude column
    :param numpy.ndarray dmag:
        Magnitude interval
    :param numpy.ndarray year:
        Catalog matrix year column

    :returns numpy.ndarray recurrence table:
        Recurrence table
    """
    # Define magnitude vectors
    if time_interval is None:
        num_year = np.max(year) - np.min(year) + 1.0
    else:
        num_year = time_interval
    upper_m = np.max(np.ceil(10.0 * mag) / 10.0)
    lower_m = np.min(np.floor(10.0 * mag) / 10.0)
    mag_range = np.arange(lower_m, upper_m + (1.5 * dmag), dmag)
    mval = mag_range[:-1] + (dmag / 2.0)
    # Find number of earthquakes inside range
    number_obs = np.histogram(mag, mag_range)[0]
    number_rows = np.shape(number_obs)[0]
    # Cumulative number of events
    n_c = np.zeros((number_rows, 1))
    i = 0
    while i < number_rows:
        n_c[i] = np.sum(number_obs[i:], axis=0)
        i += 1
    # Normalise to Annual Rate
    number_obs_annual = number_obs / num_year
    n_c_annual = n_c / num_year
    rec_table = np.column_stack(
        [mval, number_obs, n_c, number_obs_annual, n_c_annual]
    )
    return rec_table


def input_checks(catalogue, config, completeness):
    """Performs a basic set of input checks on the data"""

    if isinstance(completeness, np.ndarray):
        # completeness table is a numpy array (i.e. [year, magnitude])
        if np.shape(completeness)[1] != 2:
            raise ValueError("Completeness Table incorrectly configured")
        else:
            cmag = completeness[:, 1]
            ctime = completeness[:, 0]
    elif isinstance(completeness, float):
        # Completeness corresponds to a single magnitude (i.e. applies to
        # the entire catalogue)
        cmag = np.array(completeness)
        ctime = np.array(np.min(catalogue.data["year"]))
    else:
        # Everything is valid - i.e. no completeness magnitude
        cmag = np.array(np.min(catalogue.data["magnitude"]))
        ctime = np.array(np.min(catalogue.data["year"]))

    # Set the config parameters if missing
    config = {} if config is None else config
    key = "reference_magnitude"
    if key not in config or config[key] is None:
        config["reference_magnitude"] = 0.0
    key = "magnitude_interval"
    if key not in config or config[key] is None:
        config["magnitude_interval"] = 0.1
    ref_mag = config["reference_magnitude"]
    dmag = config["magnitude_interval"]

    return cmag, ctime, ref_mag, dmag, config


def generate_trunc_gr_magnitudes(bval, mmin, mmax, nsamples):
    """
    Generate a random list of magnitudes distributed according to a
    truncated Gutenberg-Richter model

    :param float bval:
        b-value
    :param float mmin:
        Minimum Magnitude
    :param float mmax:
        Maximum Magnitude
    :param int nsamples:
        Number of samples

    :returns:
        Vector of generated magnitudes
    """
    sampler = np.random.uniform(0.0, 1.0, nsamples)
    beta = bval * np.log(10.0)
    return (-1.0 / beta) * (
        np.log(1.0 - sampler * (1 - np.exp(-beta * (mmax - mmin))))
    ) + mmin


def generate_synthetic_magnitudes(aval, bval, mmin, mmax, nyears):
    """
    Generates a synthetic catalogue for a specified number of years, with
    magnitudes distributed according to a truncated Gutenberg-Richter
    distribution

    :param float aval:
        a-value
    :param float bval:
        b-value
    :param float mmin:
        Minimum Magnitude
    :param float mmax:
        Maximum Magnitude
    :param int nyears:
        Number of years
    :returns:
        Synthetic catalogue (dict) with year and magnitude attributes
    """
    nsamples = int(np.round(nyears * (10.0 ** (aval - bval * mmin)), 0))
    year = np.random.randint(0, nyears, nsamples)
    # Get magnitudes
    mags = generate_trunc_gr_magnitudes(bval, mmin, mmax, nsamples)
    return {"magnitude": mags, "year": np.sort(year)}


# def downsample_completeness_table(comp_table, sample_width=0.1, mmax=None):
#    """
#    Re-sample the completeness table to a specified sample_width
#    """
#    new_comp_table = []
#    for i in range(comp_table.shape[0] - 1):
#        mvals = np.arange(comp_table[i, 1],
#                          comp_table[i + 1, 1], d_m)  # FIXME: d_m is undefined!
#        new_comp_table.extend([[comp_table[i, 0], mval] for mval in mvals])
#    # If mmax > last magnitude in completeness table
#    if mmax and (mmax > comp_table[-1, 1]):
#        new_comp_table.extend(
#            [[comp_table[-1, 0], mval]
#             for mval in np.arange(comp_table[-1, 1], mmax + d_m, d_m)])
#    return np.array(new_comp_table)


def get_completeness_counts(catalogue, completeness, d_m, return_empty=False):
    """
    Returns the number of earthquakes in a set of magnitude bins of specified
    with, along with the corresponding completeness duration (in years) of the
    bin

    :param catalogue:
        Earthquake catalogue as instance of
        :class: openquake.hmtk.seisimicity.catalogue.Catalogue
    :param numpy.ndarray completeness:
        Completeness table [year, magnitude]
    :param float d_m:
        Bin size
    :returns:
        * cent_mag - array indicating center of magnitude bins
        * t_per - array indicating total duration (in years) of completeness
        * n_obs - number of events in completeness period
    """
    mmax_obs = np.max(catalogue.data["magnitude"])
    # thw line below was added by Nick Ackerley but it breaks the tests
    # catalogue.data["dtime"] = catalogue.get_decimal_time()
    if mmax_obs > np.max(completeness[:, 1]):
        cmag = np.hstack([completeness[:, 1], mmax_obs])
    else:
        cmag = completeness[:, 1]
    cyear = np.hstack([catalogue.end_year + 1, completeness[:, 0]])

    # When the magnitude value is on the bin edge numpy's histogram function
    # may assign randomly to one side or the other based on the floating
    # point value. As catalogues are rounded to the nearest 0.1 this occurs
    # frequently! So we offset the bin edge by a very tiny amount to ensure
    # that, for example, M = 4.099999999 is assigned to the bin M = 4.1 and
    # not 4.0
    master_bins = np.arange(np.min(cmag) - 1.0e-7, np.max(cmag) + d_m, d_m)
    count_rates = np.zeros(len(master_bins) - 1)
    count_years = np.zeros_like(count_rates)
    for i in range(len(cyear) - 1):
        time_idx = np.logical_and(
            catalogue.data["dtime"] < cyear[i],
            catalogue.data["dtime"] >= cyear[i + 1],
        )
        nyrs = cyear[i] - cyear[i + 1]
        sel_mags = catalogue.data["magnitude"][time_idx]
        m_idx = np.where(master_bins >= (cmag[i] - (d_m / 2.0)))[0]
        m_bins = master_bins[m_idx]
        count_rates[m_idx[:-1]] += np.histogram(sel_mags, bins=m_bins)[
            0
        ].astype(float)
        count_years[m_idx[:-1]] += float(nyrs)
    # Removes any zero rates greater than
    try:
        last_loc = np.where(count_rates > 0)[0][-1]
        n_obs = count_rates[: (last_loc + 1)]
        t_per = count_years[: (last_loc + 1)]
        cent_mag = (master_bins[:-1] + master_bins[1:]) / 2.0
        cent_mag = np.around(cent_mag[: (last_loc + 1)], 3)
    except IndexError as e:
        if return_empty:
            n_obs = np.array([]) # empty
            t_per = np.array([])
            cent_mag = np.array([])
        else:
            print(e)

    return cent_mag, t_per, n_obs
