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

import unittest
import os
import numpy as np
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.parsers.catalogue.csv_catalogue_parser import (CsvCatalogueParser,
                                                         CsvCatalogueWriter)


class CsvCatalogueParserTestCase(unittest.TestCase):
    """
    Unit tests for the csv Catalogue Parser Class
    """

    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

    def setUp(self):
        """
        Read a sample catalogue containing 8 events after instantiating
        the CsvCatalogueParser object.
        """
        filename = os.path.join(self.BASE_DATA_PATH, 'test_catalogue.csv')
        parser = CsvCatalogueParser(filename)
        self.cat = parser.read_file()

    def test_read_catalogue(self):
        """
        Check that the some fields in the first row of the catalogue are read
        correctly
        """
        self.assertEqual(self.cat.data['eventID'][0], '54')
        self.assertEqual(self.cat.data['Agency'][0], 'sheec')
        self.assertEqual(self.cat.data['year'][0], 1011)

    def test_read_catalogue_num_events(self):
        """
        Check that the number of earthquakes read form the catalogue is
        correct
        """
        self.assertEqual(self.cat.get_number_events(), 8)

    def test_without_specifying_years(self):
        """
        Tests that when the catalogue is parsed without specifying the start
        and end year that the start and end year come from the minimum and
        maximum in the catalogue
        """
        filename = os.path.join(self.BASE_DATA_PATH, 'test_catalogue.csv')
        parser = CsvCatalogueParser(filename)
        self.cat = parser.read_file()
        self.assertEqual(self.cat.start_year, np.min(self.cat.data['year']))
        self.assertEqual(self.cat.end_year, np.max(self.cat.data['year']))

    def test_specifying_years(self):
        """
        Tests that when the catalogue is parsed with the specified start and
        end years that this are recognised as attributes of the catalogue
        """
        filename = os.path.join(self.BASE_DATA_PATH, 'test_catalogue.csv')
        parser = CsvCatalogueParser(filename)
        self.cat = parser.read_file(start_year=1000, end_year=1100)
        self.assertEqual(self.cat.start_year, 1000)
        self.assertEqual(self.cat.end_year, 1100)


class TestCsvCatalogueWriter(unittest.TestCase):
    '''
    Tests the catalogue csv writer
    '''
    def setUp(self):
        '''
        '''
        self.output_filename = os.path.join(os.path.dirname(__file__),
                                            'TEST_OUTPUT_CATALOGUE.csv')
        print(self.output_filename)
        self.catalogue = Catalogue()
        self.catalogue.data['eventID'] = ['1', '2', '3', '4', '5']
        self.catalogue.data['magnitude'] = np.array([5.6, 5.4, 4.8, 4.3, 5.])
        self.catalogue.data['year'] = np.array([1960, 1965, 1970, 1980, 1990])
        self.catalogue.data['ErrorStrike'] = np.array([np.nan, np.nan, np.nan,
                                                       np.nan, np.nan])
        self.magnitude_table = np.array([[1990., 4.5], [1970., 5.5]])
        self.flag = np.array([1, 1, 1, 1, 0], dtype=bool)

    def check_catalogues_are_equal(self, cat1, cat2):
        '''
        Compares two catalogues
        '''
        for key1, key2 in zip(cat1.data['eventID'], cat2.data['eventID']):
            print(key1, key2)
            assert key1 == key2
        # np.testing.assert_array_equal(cat1.data['eventID'],
        #                              cat2.data['eventID'])
        np.testing.assert_array_equal(cat1.data['year'],
                                      cat2.data['year'])

        np.testing.assert_array_almost_equal(cat1.data['magnitude'],
                                             cat2.data['magnitude'])

    def test_catalogue_writer_no_purging(self):
        '''
        Tests the writer without any purging
        '''
        # Write to file
        writer = CsvCatalogueWriter(self.output_filename)
        writer.write_file(self.catalogue)
        parser = CsvCatalogueParser(self.output_filename)
        cat2 = parser.read_file()
        self.check_catalogues_are_equal(self.catalogue, cat2)

    def test_catalogue_writer_only_flag_purging(self):
        '''
        Tests the writer only purging according to the flag
        '''
        # Write to file
        writer = CsvCatalogueWriter(self.output_filename)
        writer.write_file(self.catalogue, flag_vector=self.flag)
        parser = CsvCatalogueParser(self.output_filename)
        cat2 = parser.read_file()

        expected_catalogue = Catalogue()
        expected_catalogue.data['eventID'] = ['1', '2', '3', '4']
        expected_catalogue.data['magnitude'] = np.array([5.6, 5.4, 4.8, 4.3])
        expected_catalogue.data['year'] = np.array([1960, 1965, 1970, 1980])
        expected_catalogue.data['ErrorStrike'] = np.array([np.nan, np.nan,
                                                           np.nan, np.nan])
        self.check_catalogues_are_equal(expected_catalogue, cat2)

    def test_catalogue_writer_only_mag_table_purging(self):
        '''
        Tests the writer only purging according to the magnitude table
        '''
        # Write to file
        writer = CsvCatalogueWriter(self.output_filename)
        writer.write_file(self.catalogue, magnitude_table=self.magnitude_table)
        parser = CsvCatalogueParser(self.output_filename)
        cat2 = parser.read_file()

        expected_catalogue = Catalogue()
        expected_catalogue.data['eventID'] = ['1', '3', '5']
        expected_catalogue.data['magnitude'] = np.array([5.6, 4.8, 5.0])
        expected_catalogue.data['year'] = np.array([1960, 1970, 1990])
        expected_catalogue.data['ErrorStrike'] = np.array([np.nan, np.nan,
                                                          np.nan])
        self.check_catalogues_are_equal(expected_catalogue, cat2)

    def test_catalogue_writer_both_purging(self):
        '''
        Tests the writer only purging according to the magnitude table and
        the flag vector
        '''
        # Write to file
        writer = CsvCatalogueWriter(self.output_filename)
        writer.write_file(self.catalogue,
                          flag_vector=self.flag,
                          magnitude_table=self.magnitude_table)
        parser = CsvCatalogueParser(self.output_filename)
        cat2 = parser.read_file()

        expected_catalogue = Catalogue()
        expected_catalogue.data['eventID'] = ['1', '3']
        expected_catalogue.data['magnitude'] = np.array([5.6, 4.8])
        expected_catalogue.data['year'] = np.array([1960, 1970])
        expected_catalogue.data['ErrorStrike'] = np.array([np.nan, np.nan])
        self.check_catalogues_are_equal(expected_catalogue, cat2)

    def tearDown(self):
        '''
        Remove the test file
        '''
        os.system('rm %s' % self.output_filename)
