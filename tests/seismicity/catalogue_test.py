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

# -*- coding: utf-8 -*-

"""

"""

import unittest
import numpy as np

from hmtk.seismicity.catalogue import Catalogue

class CatalogueTestCase(unittest.TestCase):
    """ 
    Unit tests for the Catalogue class
    """
    def setUp(self):
        self.data_array = np.array([
                               [1900, 5.00], # E 
                               [1910, 6.00], # E
                               [1920, 7.00], # I
                               [1930, 5.00], # E 
                               [1970, 5.50], # I
                               [1960, 5.01], # I 
                               [1960, 6.99], # I
                               ])
        self.mt_table = np.array([[1920, 7.0],
                                  [1940, 6.0],
                                  [1950, 5.5],
                                  [1960, 5.0],
                                ])
        
    def test_load_from_array(self):
        """
        Tests the creation of a catalogue from an array and a key list 
        """
        cat = Catalogue()
        cat.load_from_array(['year','magnitude'], self.data_array)
        self.assertTrue(np.allclose(cat.data['magnitude'],self.data_array[:,1]))
        self.assertTrue(np.allclose(cat.data['year'],self.data_array[:,0]))
        
    def test_load_to_array(self):
        """
        Tests the creation of a catalogue from an array and a key list 
        """
        cat = Catalogue()
        cat.load_from_array(['year','magnitude'], self.data_array)
        data = cat.load_to_array(['year','magnitude'])
        self.assertTrue(np.allclose(data,self.data_array))
    
    def test_catalogue_mt_filter(self):
        """
        Tests the catalogue magnitude-time filter
        """
        cat = Catalogue()
        cat.load_from_array(['year','magnitude'], self.data_array)
        cat.catalogue_mt_filter(self.mt_table)
        mag = np.array([7.0, 5.5, 5.01, 6.99])
        yea = np.array([1920, 1970, 1960, 1960])
        self.assertTrue(np.allclose(cat.data['magnitude'],mag))
        self.assertTrue(np.allclose(cat.data['year'],yea))
        