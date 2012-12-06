# -*- coding: utf-8 -*-

"""
"""

import unittest
import os
import numpy as np

from hmtk.seismicity.declusterer.dec_gardner_knopoff import GardnerKnopoffType1
from hmtk.seismicity.declusterer.distance_time_windows import GardnerKnopoffWindow
from hmtk.parsers.catalogue import CsvCatalogueParser

class GardnerKnopoffType1TestCase(unittest.TestCase):
    """ 
    Unit tests for the Gardner and Knopoff declustering algorithm class.
    """
    
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    
    def setUp(self):
        """
        Read the sample catalogue 
        """
        flnme = 'gardner_knopoff_test_catalogue.csv'
        filename = os.path.join(self.BASE_DATA_PATH, flnme)
        parser = CsvCatalogueParser(filename)
        self.cat = parser.read_file()
        
    def test_dec_gardner_knopoff(self):
        """
        Testing the Gardner and Knopoff algorithm 
        """
        config = {'time_distance_window' : GardnerKnopoffWindow(),
                  'fs_time_prop' : 1.0}
        # Instantiate the declusterer and process the sample catalogue 
        dec = GardnerKnopoffType1()
        _, flagvector = dec.decluster(self.cat, config)
        self.assertTrue(np.allclose(flagvector,self.cat.data['flag']))