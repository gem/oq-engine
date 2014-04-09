# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2014, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli, L. E. Rodriguez-Abreu
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
# The software Hazard Modeller's Toolkit (hmtk) provided herein
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
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

import unittest
import os
import numpy as np

from hmtk.seismicity.gcmt_catalogue import GCMTCatalogue
from hmtk.parsers.catalogue.gcmt_ndk_parser import ParseNDKtoGCMT
#from hmtk.parsers.catalogue.csv_catalogue_parser import CsvGCMTCatalogueParser



class GCMTCatalogueParserTestCase(unittest.TestCase):
    """
    Unit tests for the GCMT Catalogue Parser Class
    """

    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'gcmt_data')

    def setUp(self):
        """
        Read a sample catalogue containing 2 events after instantiating
        the CsvCatalogueParser object.
        """
        filename = os.path.join(self.BASE_DATA_PATH, 'test_gcmt_catalogue.txt')
        parser = ParseNDKtoGCMT(filename)
        parserCent = ParseNDKtoGCMT(filename)
        self.cat = parser.read_file()
        self.catCent = parserCent.read_file(use_centroid='True')

    def test_read_catalogue(self):
        """
        Check that the some fields in the first row of the catalogue are read
        correctly
        """
        self.assertEqual(self.cat.data['eventID'][0], 0)
        self.assertEqual(self.cat.data['centroidID'][0], 'S199004281929A  ')
        self.assertEqual(self.cat.data['year'][0], 1990.)
        self.assertEqual(self.cat.data['month'][0], 04.)
        self.assertEqual(self.cat.data['day'][0], 28.)
        self.assertEqual(self.cat.data['hour'][0], 19.)
        self.assertEqual(self.cat.data['minute'][0], 30.)
        self.assertEqual(self.cat.data['second'][0], 0.)
        self.assertEqual(self.cat.data['longitude'][0], -72.9)
        self.assertEqual(self.cat.data['latitude'][0], 18.46)
        self.assertEqual(self.cat.data['depth'][0], 100.)
        self.assertEqual(self.cat.data['moment'][0], 3.256 * (10 ** 16))
        self.assertEqual(self.cat.data['strike1'][0], 104.)
        self.assertEqual(self.cat.data['dip1'][0], 44.)
        self.assertEqual(self.cat.data['rake1'][0], 96.)
        self.assertEqual(self.cat.data['strike2'][0], 276.)
        self.assertEqual(self.cat.data['dip2'][0], 46.)
        self.assertEqual(self.cat.data['rake2'][0], 84.)
        self.assertEqual(self.cat.data['eigenvalue_t'][0], 3.42 * (10 ** 16))
        self.assertEqual(self.cat.data['plunge_t'][0], 86.)
        self.assertEqual(self.cat.data['azimuth_t'][0], 112.)
        self.assertEqual(self.cat.data['eigenvalue_b'][0], -0.33 * (10 ** 16))
        self.assertEqual(self.cat.data['plunge_b'][0], 4.)
        self.assertEqual(self.cat.data['azimuth_b'][0], 280.)
        self.assertEqual(self.cat.data['eigenvalue_p'][0], -3.092 * (10 ** 16))
        self.assertEqual(self.cat.data['plunge_p'][0], 1.)
        self.assertEqual(self.cat.data['azimuth_p'][0], 10.)

    def test_read_catalogue_num_events(self):
        """
        Check that the number of earthquakes read form the catalogue is
        correct
        """
        self.assertEqual(self.cat.get_number_tensors(), 2)


    def test_select_use_centroid(self):
        """
        Check the data when chosing use_centroid=True is correct
        """
        self.assertEqual(self.catCent.data['hour'][0], 19.)
        self.assertEqual(self.catCent.data['minute'][0], 30.)
        self.assertEqual(self.catCent.data['second'][0], 3.)
        self.assertEqual(self.catCent.data['longitude'][0], -72.79)
        self.assertEqual(self.catCent.data['latitude'][0], 18.58)
        self.assertEqual(self.catCent.data['depth'][0], 12.0)

        
    def test_select_events_depth(self):
        """
        Check that the number of earthquakes after filtering by depth is
        correct
        """
        fdepth = np.logical_and(self.cat.data['depth'] >= 100.,
                               self.cat.data['depth'] <= 200.)                
        self.cat.select_catalogue_events(np.where(fdepth)[0])
        t1 = self.assertEqual(self.cat.get_number_tensors(), 1)
        t2 = self.assertEqual(self.cat.data['centroidID'][0],
                              'S199004281929A  ')
        self.assertEqual(t1, t2)


    def test_select_events_mag(self):
        """
        Check that the number of earthquakes after filtering by magnitude is
        correct
        """
        fmag = np.logical_and(self.cat.data['magnitude'] >= 5.,
                               self.cat.data['magnitude'] <= 8.)                
        self.cat.select_catalogue_events(np.where(fmag)[0])
        self.assertEqual(self.cat.get_number_tensors(), 1)
        t1 = self.assertEqual(self.cat.get_number_tensors(), 1)
        t2 = self.assertEqual(self.cat.data['centroidID'][0],
                              'C201001122153A  ')
        self.assertEqual(t1, t2)


    def test_without_specifying_years(self):
        """
        Tests that when the catalogue is parsed without specifying the start
        and end year that the start and end year come from the minimum and
        maximum in the catalogue
        """
        filename = os.path.join(self.BASE_DATA_PATH, 'test_gcmt_catalogue.txt')
        parser = ParseNDKtoGCMT(filename)
        self.cat = parser.read_file()
        self.assertEqual(self.cat.start_year, np.min(self.cat.data['year']))
        self.assertEqual(self.cat.end_year, np.max(self.cat.data['year']))

#    def test_specifying_years(self):
#        """
#        Tests that when the catalogue is parsed with the specified start and
#        end years that this are recognised as attributes of the catalogue
#        """
#        filename = os.path.join(self.BASE_DATA_PATH, 'test_gcmt_catalogue.txt')
#        parser = CsvGCMTCatalogueParser(filename)
#        self.cat = parser.read_file(start_year=1000, end_year=1100)
#        self.assertEqual(self.cat.start_year, 1000)
#        self.assertEqual(self.cat.end_year, 1100)


#class TestCsvCatalogueWriter(unittest.TestCase):
#    '''
#    Tests the catalogue csv writer
#    '''
#    def setUp(self):
#        '''
#        '''
#        self.output_filename = os.path.join(os.path.dirname(__file__),
#                                            'TEST_GCMT_OUTPUT_CATALOGUE.csv')
#        print self.output_filename
#        self.catalogue = GCMTCatalogue()
#        self.catalogue.data['eventID'] = np.array([1, 2, 3, 4, 5])
#        self.catalogue.data['magnitude'] = np.array([5.6, 5.4, 4.8, 4.3, 5.])
#        self.catalogue.data['year'] = np.array([1960, 1965, 1970, 1980, 1990])
#        self.catalogue.data['ErrorStrike'] = np.array([np.nan, np.nan, np.nan,
#                                                       np.nan, np.nan])
#        self.magnitude_table =  np.array([[1990., 4.5], [1970., 5.5]])
#        self.flag = np.array([1, 1, 1, 1, 0], dtype=bool)
#
#
#    def check_catalogues_are_equal(self, cat1, cat2):
#        '''
#        Compares two catalogues
#        '''
#        np.testing.assert_array_equal(cat1.data['eventID'],
#                                      cat2.data['eventID'])
#        np.testing.assert_array_equal(cat1.data['year'],
#                                      cat2.data['year'])
#
#        np.testing.assert_array_almost_equal(cat1.data['magnitude'],
#                                             cat2.data['magnitude'])

#    def test_catalogue_writer_no_purging(self):
#        '''
#        Tests the writer without any purging
#        '''
#        # Write to file
#        writer = CsvCatalogueWriter(self.output_filename)
#        writer.write_file(self.catalogue)
#        parser = CsvCatalogueParser(self.output_filename)
#        cat2 = parser.read_file()
#        self.check_catalogues_are_equal(self.catalogue, cat2)

#    def test_catalogue_writer_only_flag_purging(self):
#        '''
#        Tests the writer only purging according to the flag
#        '''
#        # Write to file
#        writer = CsvCatalogueWriter(self.output_filename)
#        writer.write_file(self.catalogue, flag_vector=self.flag)
#        parser = CsvCatalogueParser(self.output_filename)
#        cat2 = parser.read_file()
#
#        expected_catalogue = Catalogue()
#        expected_catalogue.data['eventID'] = np.array([1, 2, 3, 4])
#        expected_catalogue.data['magnitude'] = np.array([5.6, 5.4, 4.8, 4.3])
#        expected_catalogue.data['year'] = np.array([1960, 1965, 1970, 1980])
#        expected_catalogue.data['ErrorStrike'] = np.array([np.nan, np.nan,
#                                                           np.nan, np.nan])
#        self.check_catalogues_are_equal(expected_catalogue, cat2)

#    def test_catalogue_writer_only_mag_table_purging(self):
#        '''
#        Tests the writer only purging according to the magnitude table
#        '''
#        # Write to file
#        writer = CsvCatalogueWriter(self.output_filename)
#        writer.write_file(self.catalogue, magnitude_table=self.magnitude_table)
#        parser = CsvCatalogueParser(self.output_filename)
#        cat2 = parser.read_file()
#
#        expected_catalogue = Catalogue()
#        expected_catalogue.data['eventID'] = np.array([1, 3, 5])
#        expected_catalogue.data['magnitude'] = np.array([5.6, 4.8, 5.0])
#        expected_catalogue.data['year'] = np.array([1960, 1970, 1990])
#        expected_catalogue.data['ErrorStrike'] =np.array([np.nan, np.nan,
#                                                          np.nan])
#        self.check_catalogues_are_equal(expected_catalogue, cat2)

#    def test_catalogue_writer_both_purging(self):
#        '''
#        Tests the writer only purging according to the magnitude table and
#        the flag vector
#        '''
#        # Write to file
#        writer = CsvCatalogueWriter(self.output_filename)
#        writer.write_file(self.catalogue,
#                          flag_vector=self.flag,
#                          magnitude_table=self.magnitude_table)
#        parser = CsvCatalogueParser(self.output_filename)
#        cat2 = parser.read_file()
#
#        expected_catalogue = Catalogue()
#        expected_catalogue.data['eventID'] =  np.array([1, 3])
#        expected_catalogue.data['magnitude'] = np.array([5.6, 4.8])
#        expected_catalogue.data['year'] = np.array([1960, 1970])
#        expected_catalogue.data['ErrorStrike'] = np.array([np.nan, np.nan])
#        self.check_catalogues_are_equal(expected_catalogue, cat2)


#    def tearDown(self):
#        '''
#        Remove the test file
#        '''
#        os.system('rm %s' % self.output_filename)
