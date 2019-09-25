# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2019 GEM Foundation, G. Weatherill, M. Pagani,
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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Prototype of a 'Catalogue' class
"""

import csv
import numpy as np
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.utils import spherical_to_cartesian
from openquake.hmtk.seismicity.utils import (decimal_time, bootstrap_histogram_1D,
                                             bootstrap_histogram_2D)


class Catalogue(object):
    """
    General Catalogue Class
    """

    FLOAT_ATTRIBUTE_LIST = [
        'second', 'timeError', 'longitude', 'latitude',
        'SemiMajor90', 'SemiMinor90', 'ErrorStrike', 'depth',
        'depthError', 'magnitude', 'sigmaMagnitude']

    INT_ATTRIBUTE_LIST = ['year', 'month', 'day', 'hour', 'minute',
                          'flag']

    STRING_ATTRIBUTE_LIST = ['eventID', 'Agency', 'magnitudeType', 'comment']

    TOTAL_ATTRIBUTE_LIST = list(
        (set(FLOAT_ATTRIBUTE_LIST).union(
            set(INT_ATTRIBUTE_LIST))).union(
                set(STRING_ATTRIBUTE_LIST)))

    SORTED_ATTRIBUTE_LIST = [
        'eventID', 'Agency', 'year', 'month', 'day', 'hour',
        'minute', 'second', 'timeError', 'longitude', 'latitude',
        'SemiMajor90', 'SemiMinor90', 'ErrorStrike',
        'depth', 'depthError', 'magnitude', 'sigmaMagnitude',
        'magnitudeType']

    def __init__(self):
        """
        Initialise the catalogue dictionary
        """
        self.data = {}
        self.end_year = None
        self.start_year = None

        self.processes = {'declustering': None,
                          'completeness': None,
                          'recurrence': None,
                          'Poisson Tests': None}

        for attribute in self.TOTAL_ATTRIBUTE_LIST:
            if attribute in self.FLOAT_ATTRIBUTE_LIST:
                self.data[attribute] = np.array([], dtype=float)
            elif attribute in self.INT_ATTRIBUTE_LIST:
                self.data[attribute] = np.array([], dtype=int)
            else:
                self.data[attribute] = []
        self.number_earthquakes = 0

    def get_number_events(self):
        return len(self.data['eventID'])

    def __len__(self):
        return self.get_number_events()
    
    def __str__(self):
        """
        Returns a shortened print of the catalogue
        """
        neq = self.get_number_events()
        if not neq:
            return "<Catalogue Object>No events"
        elif neq > 20:
            # Too many events to print, show 1st 10 and last 10
            row_set = ["<Catalogue Object>{:g} events".format(neq)]
            for i in range(10):
                row_set.append(self._get_row_str(i))
            row_set.append("...")
            for i in range(-10, 0, 1):
                row_set.append(self._get_row_str(i))
        else:
            # Show all events
            row_set = ["<Catalogue Object>{:g} events".format(neq)]
            for i in range(neq):
                row_set.append(self._get_row_str(i))
        return "\n".join(row_set)

    def _get_row_str(self, i):
        """
        Returns a string representation of the key information in a row
        """
        row_data = ["{:s}".format(self.data['eventID'][i]),
                    "{:g}".format(self.data['year'][i]),
                    "{:g}".format(self.data['month'][i]),
                    "{:g}".format(self.data['day'][i]),
                    "{:g}".format(self.data['hour'][i]),
                    "{:g}".format(self.data['minute'][i]),
                    "{:.1f}".format(self.data['second'][i]),
                    "{:.3f}".format(self.data['longitude'][i]),
                    "{:.3f}".format(self.data['latitude'][i]),
                    "{:.1f}".format(self.data['depth'][i]),
                    "{:.1f}".format(self.data['magnitude'][i])]
        return " ".join(row_data)

    def __getitem__(self, key):
        """
        If the key is provided as an int, return a data for that index,
        otherwise if it is a string then return the data column
        """
        if isinstance(key, int):
            # Gets the row specied
            row =[]
            for attr in self.SORTED_ATTRIBUTE_LIST:
                if len(self.data[attr]):
                    row.append(self.data[attr][key])
                else:
                    # For empty columns just append None
                    row.append(None)
            return row
        elif isinstance(key, str):
            return self.data[key]
        else:
            raise ValueError("__getitem__ requires integer or string")

    def __iter__(self):
        """
        Iteration yields for each event a list of data
        """
        for i in range(len(self)):
            row =[]
            for key in self.SORTED_ATTRIBUTE_LIST:
                if len(self.data[key]):
                    row.append(self.data[key][i])
                else:
                    # For empty columns just append None
                    row.append(None)
            yield row

    def add_event(self):
        raise NotImplementedError

    def write_catalogue(self, output_file, key_list=SORTED_ATTRIBUTE_LIST):
        """
        Writes the catalogue to file using HTMK format (CSV).

        :param output_file:
            Name of the output file
        :param key_list:
            Optional list of attribute keys to be exported
        """

        with open(output_file, 'w') as of:
            writer = csv.DictWriter(of, fieldnames=key_list)
            writer.writeheader()
            for i in range(self.get_number_events()):
                row_dict = {}
                for key in key_list:
                    if len(self.data[key]) > 0:
                        data = self.data[key][i]
                        if key in self.INT_ATTRIBUTE_LIST:
                            if np.isnan(data):
                                data = ''
                            else:
                                data = int(data)
                        if key in self.FLOAT_ATTRIBUTE_LIST:
                            if np.isnan(data):
                                data = ''
                            else:
                                data = float(data)
                    row_dict[key] = data
                writer.writerow(row_dict)

    def load_to_array(self, keys):
        """
        This loads the data contained in the catalogue into a numpy array. The
        method works only for float data

        :param keys:
            A list of keys to be uploaded into the array
        :type list:
        """
        # Preallocate the numpy array
        data = np.empty((len(self.data[keys[0]]), len(keys)))
        for i in range(0, len(self.data[keys[0]])):
            for j, key in enumerate(keys):
                data[i, j] = self.data[key][i]
        return data

    def load_from_array(self, keys, data_array):
        """
        This loads the data contained in an array into the catalogue object

        :param keys:
            A list of keys explaining the content of the columns in the array
        :type list:
        """

        if len(keys) != np.shape(data_array)[1]:
            raise ValueError('Key list does not match shape of array!')

        for i, key in enumerate(keys):
            if key in self.INT_ATTRIBUTE_LIST:
                self.data[key] = data_array[:, i].astype(int)
            else:
                self.data[key] = data_array[:, i]
            if key not in self.TOTAL_ATTRIBUTE_LIST:
                print('Key %s not a recognised catalogue attribute' % key)

        self.update_end_year()

    @classmethod
    def make_from_dict(cls, data):
        cat = cls()
        cat.data = data
        cat.update_end_year()
        return cat

    def update_end_year(self):
        """
        NOTE: To be called only when the catalogue is loaded (not when
        it is modified by declustering or completeness-based filtering)
        """
        self.end_year = np.max(self.data['year'])

    def update_start_year(self):
        """
        NOTE: To be called only when the catalogue is loaded (not when
        it is modified by declustering or completeness-based filtering)
        """
        self.start_year = np.min(self.data['year'])

    def catalogue_mt_filter(self, mt_table, flag=None):
        """
        Filter the catalogue using a magnitude-time table. The table has
        two columns and n-rows.

        :param nump.ndarray mt_table:
            Magnitude time table with n-rows where column 1 is year and column
            2 is magnitude

        """
        if flag is None:
            # No flag defined, therefore all events are initially valid
            flag = np.ones(self.get_number_events(), dtype=bool)

        for comp_val in mt_table:
            id0 = np.logical_and(self.data['year'].astype(float) < comp_val[0],
                                 self.data['magnitude'] < comp_val[1])
            print(id0)
            flag[id0] = False
        if not np.all(flag):
            self.purge_catalogue(flag)

    def get_bounding_box(self):
        """
        Returns the bounding box of the catalogue

        :returns: (West, East, South, North)
        """
        return (np.min(self.data["longitude"]),
                np.max(self.data["longitude"]),
                np.min(self.data["latitude"]),
                np.max(self.data["latitude"]))

    def get_observed_mmax_sigma(self, default=None):
        """
        :returns: the sigma for the maximum observed magnitude
        """
        if not isinstance(self.data['sigmaMagnitude'], np.ndarray):
            obsmaxsig = default
        else:
            obsmaxsig = self.data['sigmaMagnitude'][
                np.argmax(self.data['magnitude'])]
        return obsmaxsig

    def get_decimal_time(self):
        '''
        Returns the time of the catalogue as a decimal
        '''
        return decimal_time(self.data['year'],
                            self.data['month'],
                            self.data['day'],
                            self.data['hour'],
                            self.data['minute'],
                            self.data['second'])

    def hypocentres_as_mesh(self):
        '''
        Render the hypocentres to a nhlib.geo.mesh.Mesh object
        '''
        return Mesh(self.data['longitude'],
                    self.data['latitude'],
                    self.data['depth'])

    def hypocentres_to_cartesian(self):
        '''
        Render the hypocentres to a cartesian array
        '''
        return spherical_to_cartesian(self.data['longitude'],
                                      self.data['latitude'],
                                      self.data['depth'])

    def sort_catalogue_chronologically(self):
        '''
        Sorts the catalogue into chronological order
        '''
        dec_time = self.get_decimal_time()
        idx = np.argsort(dec_time)
        if np.all((idx[1:] - idx[:-1]) > 0.):
            # Catalogue was already in chronological order
            return
        self.select_catalogue_events(idx)

    def purge_catalogue(self, flag_vector):
        '''
        Purges present catalogue with invalid events defined by flag_vector

        :param numpy.ndarray flag_vector:
            Boolean vector showing if events are selected (True) or not (False)

        '''
        id0 = np.where(flag_vector)[0]
        self.select_catalogue_events(id0)
        self.get_number_events()

    def select_catalogue_events(self, id0):
        '''
        Orders the events in the catalogue according to an indexing vector.

        :param np.ndarray id0:
            Pointer array indicating the locations of selected events
        '''
        for key in self.data:
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

    def get_depth_distribution(self, depth_bins, normalisation=False,
                               bootstrap=None):
        '''
        Gets the depth distribution of the earthquake catalogue to return a
        single histogram. Depths may be normalised. If uncertainties are found
        in the catalogue the distrbution may be bootstrap sampled

        :param numpy.ndarray depth_bins:
             getBin edges for the depths

        :param bool normalisation:
            Choose to normalise the results such that the total contributions
            sum to 1.0 (True) or not (False)

        :param int bootstrap:
            Number of bootstrap samples

        :returns:
            Histogram of depth values

        '''
        if len(self.data['depth']) == 0:
            # If depth information is missing
            raise ValueError('Depths missing in catalogue')

        if len(self.data['depthError']) == 0:
            self.data['depthError'] = np.zeros(self.get_number_events(),
                                               dtype=float)

        return bootstrap_histogram_1D(self.data['depth'],
                                      depth_bins,
                                      self.data['depthError'],
                                      normalisation=normalisation,
                                      number_bootstraps=bootstrap,
                                      boundaries=(0., None))

    def get_depth_pmf(self, depth_bins, default_depth=5.0, bootstrap=None):
        """
        Returns the depth distribution of the catalogue as a probability mass
        function
        """
        if len(self.data['depth']) == 0:
            # If depth information is missing
            return PMF([(1.0, default_depth)])
        # Get the depth distribution
        depth_hist = self.get_depth_distribution(depth_bins,
                                                 normalisation=True,
                                                 bootstrap=bootstrap)
        # If the histogram does not sum to 1.0 then remove the difference
        # from the lowest bin
        depth_hist = np.around(depth_hist, 3)
        while depth_hist.sum() - 1.0:
            depth_hist[-1] -= depth_hist.sum() - 1.0
            depth_hist = np.around(depth_hist, 3)

        pmf_list = []
        for iloc, prob in enumerate(depth_hist):
            pmf_list.append((prob,
                             (depth_bins[iloc] + depth_bins[iloc + 1]) / 2.0))
        return PMF(pmf_list)

    def get_magnitude_depth_distribution(self, magnitude_bins, depth_bins,
                                         normalisation=False, bootstrap=None):
        '''
        Returns a 2-D magnitude-depth histogram for the catalogue

        :param numpy.ndarray magnitude_bins:
             Bin edges for the magnitudes

        :param numpy.ndarray depth_bins:
            Bin edges for the depths

        :param bool normalisation:
            Choose to normalise the results such that the total contributions
            sum to 1.0 (True) or not (False)

        :param int bootstrap:
            Number of bootstrap samples

        :returns:
            2D histogram of events in magnitude-depth bins
        '''
        if len(self.data['depth']) == 0:
            # If depth information is missing
            raise ValueError('Depths missing in catalogue')

        if len(self.data['depthError']) == 0:
            self.data['depthError'] = np.zeros(self.get_number_events(),
                                               dtype=float)

        if len(self.data['sigmaMagnitude']) == 0:
            self.data['sigmaMagnitude'] = np.zeros(self.get_number_events(),
                                                   dtype=float)

        return bootstrap_histogram_2D(self.data['magnitude'],
                                      self.data['depth'],
                                      magnitude_bins,
                                      depth_bins,
                                      boundaries=[(0., None), (None, None)],
                                      xsigma=self.data['sigmaMagnitude'],
                                      ysigma=self.data['depthError'],
                                      normalisation=normalisation,
                                      number_bootstraps=bootstrap)

    def get_magnitude_time_distribution(self, magnitude_bins, time_bins,
                                        normalisation=False, bootstrap=None):
        '''
        Returns a 2-D histogram indicating the number of earthquakes in a
        set of time-magnitude bins. Time is in decimal years!

        :param numpy.ndarray magnitude_bins:
             Bin edges for the magnitudes

        :param numpy.ndarray time_bins:
            Bin edges for the times

        :param bool normalisation:
            Choose to normalise the results such that the total contributions
            sum to 1.0 (True) or not (False)

        :param int bootstrap:
            Number of bootstrap samples

        :returns:
            2D histogram of events in magnitude-year bins
        '''
        return bootstrap_histogram_2D(
            self.get_decimal_time(),
            self.data['magnitude'],
            time_bins,
            magnitude_bins,
            xsigma=np.zeros(self.get_number_events()),
            ysigma=self.data['sigmaMagnitude'],
            normalisation=normalisation,
            number_bootstraps=bootstrap)

    def concatenate(self, catalogue):
        """
        This method attaches one catalogue to the current one

        :parameter catalogue:
            An instance of :class:`htmk.seismicity.catalogue.Catalogue`
        """

        atts = getattr(self, 'data')
        attn = getattr(catalogue, 'data')
        data = _merge_data(atts, attn)

        if data is not None:
            setattr(self, 'data', data)
            for attrib in vars(self):
                atts = getattr(self, attrib)
                attn = getattr(catalogue, attrib)
                if attrib is 'end_year':
                    setattr(self, attrib, max(atts, attn))
                elif attrib is 'start_year':
                    setattr(self, attrib, min(atts, attn))
                elif attrib is 'data':
                    pass
                elif attrib is 'number_earthquakes':
                    setattr(self, attrib, atts + attn)
                elif attrib is 'processes':
                    if atts != attn:
                        raise ValueError('The catalogues cannot be merged' +
                                         ' since the they have' +
                                         ' a different processing history')
                else:
                    raise ValueError('unknown attribute: %s' % attrib)
        self.sort_catalogue_chronologically()


def _merge_data(dat1, dat2):
    """
    Merge two data dictionaries containing catalogue data

    :parameter dictionary dat1:
        Catalogue data dictionary

    :parameter dictionary dat2:
        Catalogue data dictionary

    :returns:
        A catalogue data dictionary containing the information originally
        included in dat1 and dat2
    """

    cnt = 0
    for key in dat1:
        flg1 = len(dat1[key]) > 0
        flg2 = len(dat2[key]) > 0
        if flg1 != flg2:
            cnt += 1

    if cnt:
        raise Warning('Cannot merge catalogues with different' +
                      ' attributes')
        return None
    else:
        for key in dat1:
            if isinstance(dat1[key], np.ndarray):
                dat1[key] = np.concatenate((dat1[key], dat2[key]), axis=0)
            elif isinstance(dat1[key], list):
                dat1[key] += dat2[key]
            else:
                raise ValueError('Unknown type')
        return dat1
