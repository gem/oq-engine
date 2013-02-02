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

import unittest
import os

from hmtk.parsers.catalogue.csv_catalogue_parser import CsvCatalogueParser

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
        self.assertEqual(self.cat.data['eventID'][0], 54)
        self.assertEqual(self.cat.data['Agency'][0], 'sheec')
        self.assertEqual(self.cat.data['year'][0], 1011)
        
    def test_read_catalogue_num_events(self):
        """
        Check that the number of earthquakes read form the catalogue is 
        correct
        """
        self.assertEqual(self.cat.get_number_events(),8)