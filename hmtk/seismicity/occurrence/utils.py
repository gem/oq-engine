# -*- coding: utf-8 -*-

"""
"""

import numpy as np

def recurrence_table(mag, dmag, year):
    """
    Table of recurrence statistics for each magnitude
    [Magnitude, Number of Observations, Cumulative Number
    of Observations >= M, Number of Observations
    (normalised to annual value), Cumulative Number of
    Observations (normalised to annual value)]
    Counts number and cumulative number of occurrences of
    each magnitude in catalogue

    :param mag: catalog matrix magnitude column
    :type mag: numpy.ndarray
    :param dmag: magnitude interval
    :type dmag: numpy.ndarray
    :param year: catalog matrix year column
    :type year: numpy.ndarray
    :returns: recurrence table
    :rtype: numpy.ndarray
    """
    # Define magnitude vectors
    num_year = np.max(year) - np.min(year) + 1.
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
        ctime = np.array(np.min(catalogue['year']))
    else:
        # Everything is valid - i.e. no completeness magnitude
        cmag = np.array(np.min(catalogue['magnitude']))
        ctime = np.array(np.min(catalogue['year']))
     
    # Set reference magnitude - if not in config then default to M = 0.
    if not config['reference_magnitude']:
        ref_mag = 0.0
    else:
        ref_mag = config['reference_magnitude']

    if not config['magnitude_interval']:
        dmag = 0.1
    else:
        dmag = config['magnitude_interval']
    
    return cmag, ctime, ref_mag, dmag
