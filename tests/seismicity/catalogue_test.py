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
        