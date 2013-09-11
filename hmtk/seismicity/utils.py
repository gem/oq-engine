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

#!/usr/bin/env/python

'''Utility functions for seismicity calculations'''
import numpy as np
from math import fabs
from scipy.stats import truncnorm

MARKER_NORMAL = np.array([0, 31, 59, 90, 120, 151, 181,
                          212, 243, 273, 304, 334])

MARKER_LEAP = np.array([0, 31, 60, 91, 121, 152, 182, 
                        213, 244, 274, 305, 335])

SECONDS_PER_DAY = 86400.0

def decimal_year(year, month, day):
    """
    Allows to calculate the decimal year for a vector of dates 
    (TODO this is legacy code kept to maintain comparability with previous 
    declustering algorithms!)

    :param year: year column from catalogue matrix
    :type year: numpy.ndarray
    :param month: month column from catalogue matrix
    :type month: numpy.ndarray
    :param day: day column from catalogue matrix
    :type day: numpy.ndarray
    :returns: decimal year column
    :rtype: numpy.ndarray
    """
    marker = np.array([0., 31., 59., 90., 120., 151., 181.,
                                 212., 243., 273., 304., 334.])
    tmonth = (month - 1).astype(int)
    day_count = marker[tmonth] + day - 1.
    dec_year = year + (day_count / 365.)

    return dec_year

def leap_check(year):
    """
    Returns logical array indicating if year is a leap year
    """
    return np.logical_and((year % 4) == 0, 
                          np.logical_or((year % 100 != 0), (year % 400) == 0))

def decimal_time(year, month, day, hour, minute, second):
    """
    Returns the full time as a decimal value
    :param year:
        Year of events (integer numpy.ndarray)
    :param month:
        Month of events (integer numpy.ndarray)
    :param day:
        Days of event (integer numpy.ndarray)
    :param hour:
        Hour of event (integer numpy.ndarray)
    :param minute:
        Minute of event (integer numpy.ndarray)
    :param second:
        Second of event (float numpy.ndarray)
    :returns decimal_time:
        Decimal representation of the time (as numpy.ndarray)
    """
    tmonth = month - 1
    day_count = MARKER_NORMAL[tmonth] + day - 1
    id_leap = leap_check(year)
    leap_loc = np.where(id_leap)[0]
    day_count[leap_loc] = MARKER_LEAP[tmonth[leap_loc]] + day[leap_loc] - 1
    year_secs = (day_count.astype(float) * SECONDS_PER_DAY) +  second + \
        (60. * minute.astype(float)) + (3600. * hour.astype(float))
    decimal_time = year.astype(float) + (year_secs / (365. * 24. * 3600.))
    decimal_time[leap_loc] = year[leap_loc].astype(float) + \
        (year_secs[leap_loc] / (366. * 24. * 3600.))
    return decimal_time


def haversine(lon1, lat1, lon2, lat2, radians=False, earth_rad=6371.227):
    """
    Allows to calculate geographical distance
    using the haversine formula.

    :param lon1: longitude of the first set of locations
    :type lon1: numpy.ndarray
    :param lat1: latitude of the frist set of locations
    :type lat1: numpy.ndarray
    :param lon2: longitude of the second set of locations
    :type lon2: numpy.float64
    :param lat2: latitude of the second set of locations
    :type lat2: numpy.float64
    :keyword radians: states if locations are given in terms of radians
    :type radians: bool
    :keyword earth_rad: radius of the earth in km
    :type earth_rad: float
    :returns: geographical distance in km
    :rtype: numpy.ndarray
    """
    if radians == False:
        cfact = np.pi / 180.
        lon1 = cfact * lon1
        lat1 = cfact * lat1
        lon2 = cfact * lon2
        lat2 = cfact * lat2

    # Number of locations in each set of points
    if not np.shape(lon1):
        nlocs1 = 1
        lon1 = np.array([lon1])
        lat1 = np.array([lat1])
    else:
        nlocs1 = np.max(np.shape(lon1))
    if not np.shape(lon2):
        nlocs2 = 1
        lon2 = np.array([lon2])
        lat2 = np.array([lat2])
    else:
        nlocs2 = np.max(np.shape(lon2))
    # Pre-allocate array
    distance = np.zeros((nlocs1, nlocs2))
    i = 0
    while i < nlocs2:
        # Perform distance calculation
        dlat = lat1 - lat2[i]
        dlon = lon1 - lon2[i]
        aval = (np.sin(dlat / 2.) ** 2.) + (np.cos(lat1) * np.cos(lat2[i]) *
             (np.sin(dlon / 2.) ** 2.))
        distance[:, i] = (2. * earth_rad * np.arctan2(np.sqrt(aval),
                                                    np.sqrt(1 - aval))).T
        i += 1
    return distance


def greg2julian(year, month, day, hour, minute, second):
    """ 
    Function to convert a date from Gregorian to Julian format
    :param year:
        Year of events (integer numpy.ndarray)
    :param month:
        Month of events (integer numpy.ndarray)
    :param day:
        Days of event (integer numpy.ndarray)
    :param hour:
        Hour of event (integer numpy.ndarray)
    :param minute:
        Minute of event (integer numpy.ndarray)
    :param second:
        Second of event (float numpy.ndarray)
    :returns julian_time:
        Julian representation of the time (as float numpy.ndarray)
    """
    year = year.astype(float)
    month = month.astype(float)
    day = day.astype(float)
    
    timeut = hour.astype(float) + (minute.astype(float) / 60.0) + \
        (second / 3600.0)

    julian_time = (367.0 * year) - np.floor(7.0 * (year +
             np.floor((month + 9.0) / 12.0)) / 4.0) - np.floor(3.0 *
             (np.floor((year + (month - 9.0) / 7.0) / 100.0) + 1.0) /
             4.0) + np.floor((275.0 * month) / 9.0) + day +\
             1721028.5 + (timeut / 24.0)
    return julian_time


def piecewise_linear_scalar(params, xval):
    '''Piecewise linear function for a scalar variable xval (float).
    :param params:
        Piecewise linear parameters (numpy.ndarray) in the following form:
        [slope_i,... slope_n, turning_point_i, ..., turning_point_n, intercept]
        Length params === 2 * number_segments, e.g. 
        [slope_1, slope_2, slope_3, turning_point1, turning_point_2, intercept]
    :param xval:
        Value for evaluation of function (float)
    :returns: 
        Piecewise linear function evaluated at point xval (float)
    '''
    n_params = len(params)
    if fabs(float(n_params / 2) - float(n_params) / 2.) > 1E-7:
        raise ValueError(
            'Piecewise Function requires 2 * nsegments parameters')
    
    n_seg = n_params / 2
    
    if n_seg == 1:
        return params[1] + params[0] * xval
    
    gradients = params[0 : n_seg]
    turning_points = params[n_seg: -1]
    c_val = np.array([params[-1]])
    
    for iloc in range(1, n_seg):
        c_val = np.hstack([c_val, (c_val[iloc - 1] + gradients[iloc - 1] * 
            turning_points[iloc - 1]) - (gradients[iloc] *
            turning_points[iloc - 1])])
    
    if xval <= turning_points[0]:
        return gradients[0] * xval + c_val[0]
    elif xval > turning_points[-1]:
        return gradients[-1] * xval + c_val[-1]
    else:
        select = np.nonzero(turning_points <= xval)[0][-1] + 1
    return gradients[select] * xval + c_val[select]


def sample_truncated_gaussian_vector(data, uncertainties, bounds=None):
    '''
    Samples a Gaussian distribution subject to boundaries on the data
    :param numpy.ndarray data:
        Vector of N data values
    :param numpy.ndarray uncertainties:
        Vector of N data uncertainties
    :param int number_bootstraps:
        Number of bootstrap samples
    :param tuple bounds:
        (Lower, Upper) bound of data space
    '''
    nvals = len(data)
    if bounds:
        #if bounds[0] or (fabs(bounds[0]) < 1E-12):
        if bounds[0] is not None:
            lower_bound = (bounds[0] - data) / uncertainties
        else:
            lower_bound = -np.inf
        
        #if bounds[1] or (fabs(bounds[1]) < 1E-12):
        if bounds[1] is not None:
            upper_bound = (bounds[1] - data) / uncertainties
        else:
            upper_bound = np.inf
        sample = truncnorm.rvs(lower_bound, upper_bound, size=nvals)
    
    else:
        sample = np.random.normal(0., 1., nvals)
    return data + uncertainties * sample
        



def bootstrap_histogram_1D(values, intervals, uncertainties=None, 
        normalisation=False, number_bootstraps=None, boundaries=None):
    '''
    Bootstrap samples a set of vectors
    :param numpy.ndarray values:
        The data values
    :param numpy.ndarray intervals:
        The bin edges
    :param numpy.ndarray uncertainties:
        The standard deviations of each observation
    :param bool normalisation:
        If True then returns the histogram as a density function
    :param int number_bootstraps:
        Number of bootstraps
    :param tuple boundaries:
        (Lower, Upper) bounds on the data

    :param returns:
        1-D histogram of data

    '''
    if not number_bootstraps or np.all(np.fabs(uncertainties < 1E-12)):
        # No bootstraps or all uncertaintes are zero - return ordinary 
        # histogram
        output = np.histogram(values, intervals)[0]
        if normalisation:
            output = output.astype(float) / float(np.sum(output))
        else:
            output = output.astype(float)
        return output
    else:
        temp_hist = np.zeros([len(intervals) - 1, number_bootstraps], 
                             dtype=float)
        for iloc in range(0, number_bootstraps):
            sample = sample_truncated_gaussian_vector(values,
                                                      uncertainties,
                                                      boundaries)
            output = np.histogram(sample, intervals)[0]
            temp_hist[:, iloc] = output
        output = np.sum(temp_hist, axis=1)
        if normalisation:
            output = output.astype(float) / float(np.sum(output))
        else:
            output = output.astype(float) / float(number_bootstraps)
        return output

def bootstrap_histogram_2D(xvalues, yvalues, xbins, ybins, 
        boundaries=[None, None], xsigma=None, ysigma=None, 
        normalisation=False, number_bootstraps=None):
    '''
    Calculates a 2D histogram of data, allowing for normalisation and 
    bootstrap sampling
    :param numpy.ndarray xvalues:
        Data values of the first variable

    :param numpy.ndarray yvalues:
        Data values of the second variable

    :param numpy.ndarray xbins:
        Bin edges for the first variable

    :param numpy.ndarray ybins:
        Bin edges for the second variable

    :param list boundaries:
        List of (Lower, Upper) tuples corresponding to the bounds of the 
        two data sets

    :param numpy.ndarray xsigma:
        Error values (standard deviatons) on first variable

    :param numpy.ndarray ysigma:
        Error values (standard deviatons) on second variable

    :param bool normalisation:
        If True then returns the histogram as a density function
    
    :param int number_bootstraps:
        Number of bootstraps

    :param returns:
        2-D histogram of data
    '''
    if (xsigma is None and ysigma is None) or not number_bootstraps:
        # No sampling - return simple 2-D histrogram
        output = np.histogram2d(xvalues, yvalues, bins=[xbins, ybins])[0]
        if normalisation:
            output = output.astype(float) / float(np.sum(output))
        return output

    else:
        if xsigma is None:
            xsigma = np.zeros(len(xvalues), dtype=float)
        if ysigma is None:
            ysigma = np.zeros(len(yvalues), dtype=float)
        temp_hist = np.zeros(
            [len(xbins) - 1, len(ybins) - 1, number_bootstraps],
            dtype=float)
        for iloc in range(0, number_bootstraps):
            xsample = sample_truncated_gaussian_vector(xvalues, xsigma,
                                                       boundaries[0])
            ysample = sample_truncated_gaussian_vector(yvalues, ysigma,
                                                       boundaries[0])

            temp_hist[:, :, iloc] = np.histogram2d(xsample, 
                                                   ysample, 
                                                   bins=[xbins, ybins])[0]
        if normalisation:
            output = np.sum(temp_hist, axis=2)
            output = output / np.sum(output)
        else:
            output = np.sum(temp_hist, axis=2) / float(number_bootstraps)
        return output






