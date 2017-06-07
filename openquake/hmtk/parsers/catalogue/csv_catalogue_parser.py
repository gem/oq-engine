# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Module :mod:`openquake.hmtk.parsers.catalogue.csv_catalogue_parser`
implements :class:`CsvCatalogueParser`.
"""
import csv
import numpy as np
from copy import deepcopy
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.gcmt_catalogue import GCMTCatalogue
from openquake.hmtk.parsers.catalogue.base import (
    BaseCatalogueParser, BaseCatalogueWriter)


class CsvCatalogueParser(BaseCatalogueParser):
    """CSV Catalogue Parser Class
    """

    def read_file(self, start_year=None, end_year=None):
        """
        """
        filedata = open(self.input_file, 'rU')
        catalogue = self._setup_catalogue()
        # Reading the data file
        data = csv.DictReader(filedata)
        # Parsing the data content
        for irow, row in enumerate(data):
            if irow == 0:
                valid_key_list = self._header_check(
                    row.keys(),
                    catalogue.TOTAL_ATTRIBUTE_LIST)
            for key in valid_key_list:
                if key in catalogue.FLOAT_ATTRIBUTE_LIST:
                    catalogue.data[key] = self._float_check(
                        catalogue.data[key], row[key], irow, key)
                elif key in catalogue.INT_ATTRIBUTE_LIST:
                    catalogue.data[key] = self._int_check(
                        catalogue.data[key], row[key], irow, key)
                else:
                    catalogue.data[key].append(row[key])
        if start_year:
            catalogue.start_year = start_year
        else:
            catalogue.update_start_year()

        if end_year:
            catalogue.end_year = end_year
        else:
            catalogue.update_end_year()
        return catalogue

    def _setup_catalogue(self):
        """
        Returns a blank catalogue instance
        """
        return Catalogue()

    def _header_check(self, input_keys, catalogue_keys):
        valid_key_list = []
        for element in input_keys:
            if element in catalogue_keys:
                valid_key_list.append(element)
            else:
                print('Catalogue Attribute %s is not '
                      'a recognised catalogue key' % element)
        return valid_key_list

    def _float_check(self, attribute_array, value, irow, key):
        '''Checks if value is valid float, appends to array if valid, appends
        nan if not'''
        value = value.strip(' ')
        try:
            if value:
                attribute_array = np.hstack([attribute_array, float(value)])
            else:
                attribute_array = np.hstack([attribute_array, np.nan])
        except:
            print(irow, key)
            msg = 'Input file format error at line: %d' % (irow+2)
            msg += ' key: %s' % (key)
            raise ValueError(msg)
        return attribute_array

    def _int_check(self, attribute_array, value, irow, key):
        '''Checks if value is valid integer, appends to array if valid, appends
        nan if not'''
        value = value.strip(' ')
        try:
            if value:
                attribute_array = np.hstack([attribute_array, int(value)])
            else:
                attribute_array = np.hstack([attribute_array, np.nan])
        except:
            msg = 'Input file format error at line: %d' % (irow+2)
            msg += ' key: %s' % (key)
            raise ValueError(msg)
        return attribute_array


class GCMTCsvCatalogueParser(CsvCatalogueParser):
    """

    """
    def _setup_catalogue(self):
        """
        """
        return GCMTCatalogue()


class CsvCatalogueWriter(BaseCatalogueWriter):
    '''
    Writes catalogue to csv file
    '''
    # Because the catalogues TOTAL_ATTRIBUTE_LIST is randomly ordered,
    # the preferred output order is given as a list here
    OUTPUT_LIST = ['eventID', 'Agency', 'year', 'month', 'day', 'hour',
                   'minute', 'second', 'timeError', 'longitude',
                   'latitude', 'SemiMajor90', 'SemiMinor90', 'ErrorStrike',
                   'depth', 'depthError', 'magnitude', 'sigmaMagnitude',
                   'magnitudeType']

    def write_file(self, catalogue, flag_vector=None, magnitude_table=None):
        '''
        Writes the catalogue to file, purging events if necessary.

        :param catalogue:
            Earthquake catalogue as instance of :class:
            openquake.hmtk.seismicity.catalogue.Catalogue
        :param numpy.array flag_vector:
            Boolean vector specifying whether each event is valid (therefore
            written) or otherwise
        :param numpy.ndarray magnitude_table:
            Magnitude-time table specifying the year and magnitudes of
            completeness
        '''
        # First apply purging conditions
        output_catalogue = self.apply_purging(catalogue,
                                              flag_vector,
                                              magnitude_table)
        outfile = open(self.output_file, 'wt')
        writer = csv.DictWriter(outfile, fieldnames=self.OUTPUT_LIST)

        writer.writeheader()
        # Quick check to remove nan arrays
        for key in self.OUTPUT_LIST:
            cond = (isinstance(output_catalogue.data[key], np.ndarray)
                    and np.all(np.isnan(output_catalogue.data[key])))
            if cond:
                output_catalogue.data[key] = []
        # Write the catalogue
        for iloc in range(0, output_catalogue.get_number_events()):
            row_dict = {}
            for key in self.OUTPUT_LIST:
                if len(output_catalogue.data[key]) > 0:
                    row_dict[key] = output_catalogue.data[key][iloc]
                else:
                    row_dict[key] = ''
            writer.writerow(row_dict)
        outfile.close()

    def apply_purging(self, catalogue, flag_vector, magnitude_table):
        '''
        Apply all the various purging conditions, if specified.

        :param catalogue:
            Earthquake catalogue as instance of :class:`openquake.hmtk.seismicity.catalogue.Catalogue`
        :param numpy.array flag_vector:
            Boolean vector specifying whether each event is valid (therefore
            written) or otherwise
        :param numpy.ndarray magnitude_table:
            Magnitude-time table specifying the year and magnitudes of
            completeness
        '''
        output_catalogue = deepcopy(catalogue)
        if magnitude_table is not None:
            if flag_vector is not None:
                output_catalogue.catalogue_mt_filter(
                    magnitude_table, flag_vector)
                return output_catalogue
            else:
                output_catalogue.catalogue_mt_filter(
                    magnitude_table)
                return output_catalogue

        if flag_vector is not None:
            output_catalogue.purge_catalogue(flag_vector)
        return output_catalogue


class CsvGCMTCatalogueWriter(CsvCatalogueWriter):
    '''
    Writes GCMT catalogue to csv file
    '''
    OUTPUT_LIST = ['eventID', 'centroidID', 'Agency', 'year', 'month', 'day',
                   'hour', 'minute', 'second', 'timeError', 'longitude',
                   'latitude', 'depth', 'depthError', 'magnitude',
                   'sigmaMagnitude', 'magnitudeType', 'moment', 'SemiMajor90',
                   'SemiMinor90', 'ErrorStrike', 'strike1', 'rake1', 'dip1',
                   'strike2', 'rake2', 'dip2', 'f_clvd', 'e_rel',
                   'eigenvalue_b', 'azimuth_b', 'plunge_b',
                   'eigenvalue_p', 'azimuth_p', 'plunge_p',
                   'eigenvalue_t', 'azimuth_t', 'plunge_t']

    def write_file(self, catalogue, flag_vector=None, magnitude_table=None):
        '''
        Writes the catalogue to file, purging events if necessary.

        :param catalogue:
            Earthquake catalogue as instance of :class:
            openquake.hmtk.seismicity.catalogue.Catalogue
        :param numpy.array flag_vector:
            Boolean vector specifying whether each event is valid (therefore
            written) or otherwise
        :param numpy.ndarray magnitude_table:
            Magnitude-time table specifying the year and magnitudes of
            completeness
        '''
        # First apply purging conditions
        output_catalogue = self.apply_purging(catalogue,
                                              flag_vector,
                                              magnitude_table)
        outfile = open(self.output_file, 'wt')
        writer = csv.DictWriter(outfile, fieldnames=self.OUTPUT_LIST)

        writer.writeheader()
        # Quick check to remove nan arrays
        for key in self.OUTPUT_LIST:
            cond = (isinstance(output_catalogue.data[key], np.ndarray)
                    and np.all(np.isnan(output_catalogue.data[key])))
            if cond:
                output_catalogue.data[key] = []
        # Write the catalogue
        for iloc in range(0, output_catalogue.get_number_events()):
            row_dict = {}
            for key in self.OUTPUT_LIST:
                if len(output_catalogue.data[key]) > 0:
                    row_dict[key] = output_catalogue.data[key][iloc]
                else:
                    row_dict[key] = ''
            writer.writerow(row_dict)
        outfile.close()

    def apply_purging(self, catalogue, flag_vector, magnitude_table):
        '''
        Apply all the various purging conditions, if specified.

        :param catalogue:
            Earthquake catalogue as instance of :class:
            openquake.hmtk.seismicity.catalogue.Catalogue:
        :param numpy.array flag_vector:
            Boolean vector specifying whether each event is valid (therefore
            written) or otherwise
        :param numpy.ndarray magnitude_table:
            Magnitude-time table specifying the year and magnitudes of
            completeness
        '''
        output_catalogue = deepcopy(catalogue)
        if magnitude_table is not None:
            if flag_vector is not None:
                output_catalogue.catalogue_mt_filter(
                    magnitude_table, flag_vector)
                return output_catalogue
            else:
                output_catalogue.catalogue_mt_filter(
                    magnitude_table)
                return output_catalogue

        if flag_vector is not None:
            output_catalogue.purge_catalogue(flag_vector)
        return output_catalogue
