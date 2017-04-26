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

from openquake.hmtk.seismicity.gcmt_catalogue import GCMTCatalogue
from openquake.hmtk.parsers.catalogue.gcmt_ndk_parser import ParseNDKtoGCMT
#from openquake.hmtk.parsers.catalogue.csv_catalogue_parser import CsvGCMTCatalogueParser



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
        parser_cent = ParseNDKtoGCMT(filename)
        self.cat = parser.read_file()
        self.cat_cent = parser_cent.read_file(use_centroid='True')

    def test_read_catalogue(self):
        """
        Check that the some fields in the first row of the catalogue are read
        correctly
        """
        self.assertAlmostEqual(self.cat.data['eventID'][0], 0)
        self.assertAlmostEqual(self.cat.data['centroidID'][0], 'S199004281929A  ')
        self.assertAlmostEqual(self.cat.data['year'][0], 1990.)
        self.assertAlmostEqual(self.cat.data['month'][0], 04.)
        self.assertAlmostEqual(self.cat.data['day'][0], 28.)
        self.assertAlmostEqual(self.cat.data['hour'][0], 19.)
        self.assertAlmostEqual(self.cat.data['minute'][0], 30.)
        self.assertAlmostEqual(self.cat.data['second'][0], 0.)
        self.assertAlmostEqual(self.cat.data['longitude'][0], -72.9)
        self.assertAlmostEqual(self.cat.data['latitude'][0], 18.46)
        self.assertAlmostEqual(self.cat.data['depth'][0], 100.)
        self.assertAlmostEqual(self.cat.data['moment'][0], 3.256 * (10 ** 16))
        self.assertAlmostEqual(self.cat.data['strike1'][0], 104.)
        self.assertAlmostEqual(self.cat.data['dip1'][0], 44.)
        self.assertAlmostEqual(self.cat.data['rake1'][0], 96.)
        self.assertAlmostEqual(self.cat.data['strike2'][0], 276.)
        self.assertAlmostEqual(self.cat.data['dip2'][0], 46.)
        self.assertAlmostEqual(self.cat.data['rake2'][0], 84.)
        self.assertAlmostEqual(self.cat.data['eigenvalue_t'][0], 3.42 * (10 ** 16))
        self.assertAlmostEqual(self.cat.data['plunge_t'][0], 86.)
        self.assertAlmostEqual(self.cat.data['azimuth_t'][0], 112.)
        self.assertAlmostEqual(self.cat.data['eigenvalue_b'][0], -0.33 * (10 ** 16))
        self.assertAlmostEqual(self.cat.data['plunge_b'][0], 4.)
        self.assertAlmostEqual(self.cat.data['azimuth_b'][0], 280.)
        self.assertAlmostEqual(self.cat.data['eigenvalue_p'][0], -3.092 * (10 ** 16))
        self.assertAlmostEqual(self.cat.data['plunge_p'][0], 1.)
        self.assertAlmostEqual(self.cat.data['azimuth_p'][0], 10.)

    def test_read_catalogue_num_events(self):
        """
        Check that the number of earthquakes read form the catalogue is
        correct
        """
        self.assertAlmostEqual(self.cat.get_number_tensors(), 2)


    def test_select_use_centroid(self):
        """
        Check the data when chosing use_centroid=True is correct
        """
        self.assertAlmostEqual(self.cat_cent.data['hour'][0], 19.)
        self.assertAlmostEqual(self.cat_cent.data['minute'][0], 30.)
        self.assertAlmostEqual(self.cat_cent.data['second'][0], 3.)
        self.assertAlmostEqual(self.cat_cent.data['longitude'][0], -72.79)
        self.assertAlmostEqual(self.cat_cent.data['latitude'][0], 18.58)
        self.assertAlmostEqual(self.cat_cent.data['depth'][0], 12.0)

        
    def test_select_events_depth(self):
        """
        Check that the number of earthquakes after filtering by depth is
        correct
        """
        fdepth = np.logical_and(self.cat.data['depth'] >= 100.,
                               self.cat.data['depth'] <= 200.)                
        self.cat.select_catalogue_events(np.where(fdepth)[0])
        t1 = self.assertAlmostEqual(self.cat.get_number_tensors(), 1)
        t2 = self.assertAlmostEqual(self.cat.data['centroidID'][0],
                              'S199004281929A  ')
        self.assertAlmostEqual(t1, t2)


    def test_select_events_mag(self):
        """
        Check that the number of earthquakes after filtering by magnitude is
        correct
        """
        fmag = np.logical_and(self.cat.data['magnitude'] >= 5.,
                               self.cat.data['magnitude'] <= 8.)                
        self.cat.select_catalogue_events(np.where(fmag)[0])
        self.assertAlmostEqual(self.cat.get_number_tensors(), 1)
        t1 = self.assertAlmostEqual(self.cat.get_number_tensors(), 1)
        t2 = self.assertAlmostEqual(self.cat.data['centroidID'][0],
                              'C201001122153A  ')
        self.assertAlmostEqual(t1, t2)


    def test_without_specifying_years(self):
        """
        Tests that when the catalogue is parsed without specifying the start
        and end year that the start and end year come from the minimum and
        maximum in the catalogue
        """
        filename = os.path.join(self.BASE_DATA_PATH, 'test_gcmt_catalogue.txt')
        parser = ParseNDKtoGCMT(filename)
        self.cat = parser.read_file()
        self.assertAlmostEqual(self.cat.start_year, np.min(self.cat.data['year']))
        self.assertAlmostEqual(self.cat.end_year, np.max(self.cat.data['year']))
