# -*- coding: utf-8 -*-

import numpy as np

def aki_max_likelihood(mval, number_obs, dmag=0.1, m_c=0.0):
    """
    Calculation of b-value and its uncertainty for a given catalogue,
    using the maximum likelihood method of Aki (1965), with a correction
    for discrete bin width (Bender, 1983).

    :param mval: array of reference magnitudes
                 (column 0 from recurrence table)
    :type mval: numpy.ndarray
    :param number_obs: number of observations in magnitude bin
                       (column 1 from recurrence table)
    :type number_obs: numpy.ndarray
    :keyword dmag: magnitude interval
    :type dmag: positive float
    :keyword m_c: completeness magnitude
    :type m_c: float
    :returns: bvalue and sigma_b
    :rtype: float
    """
    # Exclude data below Mc
    id0 = mval >= m_c
    mval = mval[id0]
    number_obs = number_obs[id0]
    # Get Number of events, minimum magnitude and mean magnitude
    neq = np.sum(number_obs)
    m_min = np.min(mval)
    m_ave = np.sum(mval * number_obs) / neq
    # Calculate b-value
    bval = np.log10(np.exp(1.0)) / (m_ave - m_min + (dmag / 2.))
    # Calculate sigma b from Bender estimator
    sigma_b = np.sum(number_obs * ((mval - m_ave) ** 2.0)) / (neq * (neq - 1))
    sigma_b = np.log(10.) * (bval ** 2.0) * np.sqrt(sigma_b)
    return bval, sigma_b
