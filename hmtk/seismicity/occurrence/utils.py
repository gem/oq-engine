# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2013, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
# 
# The software Hazard Modeller's Toolkit (hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-

"""
"""

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
        num_year = np.max(year) - np.min(year) + 1.
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
    rec_table = np.column_stack([mval, number_obs, n_c, number_obs_annual,
                                 n_c_annual])
    return rec_table

def input_checks(catalogue, config, completeness):
    """ Performs a basic set of input checks on the data
    """

    if isinstance(completeness, np.ndarray):
        # completeness table is a numpy array (i.e. [year, magnitude])
        if np.shape(completeness)[1] != 2:
            raise ValueError('Completeness Table incorrectly configured')
        else:
            cmag = completeness[:, 1]
            ctime = completeness[:, 0]
    elif isinstance(completeness, float):
        # Completeness corresponds to a single magnitude (i.e. applies to
        # the entire catalogue)
        cmag = np.array(completeness)
        ctime = np.array(np.min(catalogue.data['year']))
    else:
        # Everything is valid - i.e. no completeness magnitude
        cmag = np.array(np.min(catalogue.data['magnitude']))
        ctime = np.array(np.min(catalogue.data['year']))

    # Set reference magnitude - if not in config then default to M = 0.
    if not config:
        # use default reference magnitude of 0.0 and magnitude interval of 0.1
        ref_mag = 0.0
        dmag = 0.1
    else:
        if (not 'reference_magnitude' in config.keys()) or \
            not config['reference_magnitude']:
            ref_mag = 0.0
        else:
            ref_mag = config['reference_magnitude']

        if (not 'magnitude_interval' in config.keys()) or \
            not config['magnitude_interval']:
            dmag = 0.1
        else:
            dmag = config['magnitude_interval']

#    if config is None or not 'reference_magnitude' in config:
#        ref_mag = 0.0
#    else:
#        ref_mag = config['reference_magnitude']
#
#    if config is None or not 'magnitude_interval' in config:
#        dmag = 0.1
#    else:
#        dmag = config['magnitude_interval']

    return cmag, ctime, ref_mag, dmag


def generate_trunc_gr_magnitudes(bval, mmin, mmax, nsamples):
    '''
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
    '''
    sampler = np.random.uniform(0., 1., nsamples)
    beta = bval * np.log(10.)
    return (-1. / beta) * (np.log(1. - sampler * (1 - np.exp(-beta * (mmax -
        mmin))))) + mmin

def generate_synthetic_magnitudes(aval, bval, mmin, mmax, nyears):
    '''
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
    '''
    nsamples = np.round(nyears * (10. ** (aval - bval * mmin)), 0)
    year = np.random.randint(0, nyears, nsamples)
    # Get magnitudes
    mags = generate_trunc_gr_magnitudes(bval, mmin, mmax, nsamples)
    return {'magnitude': mags, 'year': np.sort(year)}
