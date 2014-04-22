#!/usr/bin/env/python

"""
Implements sets of classes for mapping components of the focal mechanism
"""
import csv
import datetime
from math import fabs, floor, sqrt, pi
import numpy as np
import gcmt_utils as utils
from hmtk.seismicity.catalogue import Catalogue


def cmp_mat(a, b):
    """
    Sorts two matrices returning a positive or zero value
    """
    c = 0
    for x,y in zip(a.flat, b.flat):
        c = cmp(abs(x),abs(y))
        if c != 0: return c
    return c


class GCMTHypocentre(object):
    """
    Simple representation of the hypocentre
    """
    def __init__(self):
        """
        """
        self.source = None
        self.date = None
        self.time = None
        self.longitude = None
        self.latitude = None
        self.depth = None
        self.m_b = None
        self.m_s = None
        self.location = None


class GCMTCentroid(object):
    """
    Representation of a GCMT centroid
    """
    def __init__(self, reference_date, reference_time):
        """
        :param reference_date:
            Date of hypocentre as instance of :class: datetime.datetime.date
        :param reference_time:
            Time of hypocentre as instance of :class: datetime.datetime.time

        """
        self.centroid_type = None
        self.source = None
        self.time = reference_time
        self.time_error = None
        self.date = reference_date
        self.longitude = None
        self.longitude_error = None
        self.latitude = None
        self.latitude_error = None
        self.depth = None
        self.depth_error = None
        self.depth_type = None
        self.centroid_id = None

    def _get_centroid_time(self, time_diff):
        """
        Calculates the time difference between the date-time classes
        """
        source_time = datetime.datetime.combine(self.date, self.time)
        second_diff = floor(fabs(time_diff))
        microsecond_diff = int(1000. * (time_diff - second_diff))
        if time_diff < 0.:
            source_time = source_time - datetime.timedelta(
                seconds=int(second_diff), microseconds=microsecond_diff)
        else:
            source_time = source_time + datetime.timedelta(
                seconds=int(second_diff), microseconds=microsecond_diff)
        self.time = source_time.time()
        self.date = source_time.date()


class GCMTCatalogue(Catalogue):
    """
    Class to hold a catalogue of moment tensors
    """
    FLOAT_ATTRIBUTE_LIST = ['second', 'timeError', 'longitude', 'latitude',
                            'SemiMajor90', 'SemiMinor90', 'ErrorStrike',
                            'depth', 'depthError', 'magnitude',
                            'sigmaMagnitude', 'moment', 'strike1', 'rake1',
                            'dip1', 'strike2', 'rake2', 'dip2',
                            'eigenvalue_b', 'azimuth_b', 'plunge_b',
                            'eigenvalue_p', 'azimuth_p', 'plunge_p',
                            'eigenvalue_t', 'azimuth_t', 'plunge_t',
                            'f_clvd', 'e_rel']

    INT_ATTRIBUTE_LIST = ['eventID', 'year', 'month', 'day', 'hour', 'minute',
                          'flag']

    STRING_ATTRIBUTE_LIST = ['Agency', 'magnitudeType', 'comment',
                             'centroidID']

    TOTAL_ATTRIBUTE_LIST = list(
        (set(FLOAT_ATTRIBUTE_LIST).union(
                set(INT_ATTRIBUTE_LIST))).union(
                    set(STRING_ATTRIBUTE_LIST)))
        
    def __init__(self, start_year=None, end_year=None):
        """
        Instantiate catalogue class
        """
        super(GCMTCatalogue, self).__init__()

        self.gcmts = []
        self.number_gcmts = None
        self.start_year = start_year
        self.end_year = end_year

        for attribute in self.TOTAL_ATTRIBUTE_LIST:
            if attribute in self.FLOAT_ATTRIBUTE_LIST:
                self.data[attribute] = np.array([], dtype=float)
            elif attribute in self.INT_ATTRIBUTE_LIST:
                self.data[attribute] = np.array([], dtype=int)

    def get_number_tensors(self):
        """
        Returns number of CMTs
        """
        return len(self.gcmts)


    def select_catalogue_events(self, id0):
        '''
        Orders the events in the catalogue according to an indexing vector
        :param np.ndarray id0:
            Pointer array indicating the locations of selected events
        '''
        for key in self.data.keys():
            if isinstance(
                    self.data[key], np.ndarray) and len(self.data[key]) > 0:
                # Dictionary element is numpy array - use logical indexing
                self.data[key] = self.data[key][id0]
            elif isinstance(
                    self.data[key], list) and len(self.data[key]) > 0:
                # Dictionary element is list
                self.data[key] = [self.data[key][iloc] for iloc in id0]
            else:
                continue

        if len(self.gcmts) > 0:
            self.gcmts = [self.gcmts[iloc] for iloc in id0] 
            self.number_gcmts = self.get_number_tensors()

   
    def gcmt_to_simple_array(self, centroid_location=True):
        """
        Converts the GCMT catalogue to a simple array of 
        [ID, year, month, day, hour, minute, second, long., lat., depth, Mw,
        strike1, dip1, rake1, strike2, dip2, rake2, b-plunge, b-azimuth,
        b-eigenvalue, p-plunge, p-azimuth, p-eigenvalue, t-plunge, t-azimuth,
        t-eigenvalue, moment, f_clvd, erel]
        """
        catalogue = np.zeros([self.get_number_tensors(), 29], dtype=float) 
        for iloc, tensor in enumerate(self.gcmts):
            catalogue[iloc, 0] = iloc
            if centroid_location:
                catalogue[iloc, 1] = float(tensor.centroid.date.year)
                catalogue[iloc, 2] = float(tensor.centroid.date.month)
                catalogue[iloc, 3] = float(tensor.centroid.date.day)
                catalogue[iloc, 4] = float(tensor.centroid.time.hour)
                catalogue[iloc, 5] = float(tensor.centroid.time.minute)
                catalogue[iloc, 6] = np.round(
                    np.float(tensor.centroid.time.second) +
                    np.float(tensor.centroid.time.microsecond) / 1000000., 2)
                catalogue[iloc, 7] = tensor.centroid.longitude
                catalogue[iloc, 8] = tensor.centroid.latitude
                catalogue[iloc, 9] = tensor.centroid.depth
            else:
                catalogue[iloc, 1] = float(tensor.hypocentre.date.year)
                catalogue[iloc, 2] = float(tensor.hypocentre.date.month)
                catalogue[iloc, 3] = float(tensor.hypocentre.date.day)
                catalogue[iloc, 4] = float(tensor.hypocentre.time.hour)
                catalogue[iloc, 5] = float(tensor.hypocentre.time.minute)
                catalogue[iloc, 6] = np.round(
                    np.float(tensor.centroid.time.second) +
                    np.float(tensor.centroid.time.microsecond) / 1000000., 2)
                catalogue[iloc, 7] = tensor.hypocentre.longitude
                catalogue[iloc, 8] = tensor.hypocentre.latitude
                catalogue[iloc, 9] = tensor.hypocentre.depth
            catalogue[iloc, 10] = tensor.magnitude
            catalogue[iloc, 11] = tensor.moment
            catalogue[iloc, 12] = tensor.f_clvd
            catalogue[iloc, 13] = tensor.e_rel
            # Nodal planes
            catalogue[iloc, 14] = tensor.nodal_planes.nodal_plane_1['strike']
            catalogue[iloc, 15] = tensor.nodal_planes.nodal_plane_1['dip']
            catalogue[iloc, 16] = tensor.nodal_planes.nodal_plane_1['rake']
            catalogue[iloc, 17] = tensor.nodal_planes.nodal_plane_2['strike']
            catalogue[iloc, 18] = tensor.nodal_planes.nodal_plane_2['dip']
            catalogue[iloc, 19] = tensor.nodal_planes.nodal_plane_2['rake']
            # Principal axes
            catalogue[iloc, 20] = tensor.principal_axes.b_axis['eigenvalue'] 
            catalogue[iloc, 21] = tensor.principal_axes.b_axis['azimuth']
            catalogue[iloc, 22] = tensor.principal_axes.b_axis['plunge']
            catalogue[iloc, 23] = tensor.principal_axes.p_axis['eigenvalue']
            catalogue[iloc, 24] = tensor.principal_axes.p_axis['azimuth']
            catalogue[iloc, 25] = tensor.principal_axes.p_axis['plunge']
            catalogue[iloc, 26] = tensor.principal_axes.t_axis['eigenvalue']
            catalogue[iloc, 27] = tensor.principal_axes.t_axis['azimuth']
            catalogue[iloc, 28] = tensor.principal_axes.t_axis['plunge']
        return catalogue

