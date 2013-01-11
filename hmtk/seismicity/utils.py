#!/usr/bin/env/python

'''Utility functions for seismicity calculations'''
from math import fabs
import numpy as np

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
