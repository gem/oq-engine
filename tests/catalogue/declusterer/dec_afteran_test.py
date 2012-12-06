# -*- coding: utf-8 -*-

"""
"""

import unittest
import os
import numpy as np

from hmtk.catalogue.declusterer.dec_afteran import Afteran
from hmtk.catalogue.declusterer.distance_time_windows import GardnerKnopoffWindow
from hmtk.parsers.catalogue import CsvCatalogueParser

class AfteranTestCase(unittest.TestCase):
    """ 
    Unit tests for the Afteran declustering algorithm class.
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
        Testing the Afteran algorithm 
        """
        config = {'time_distance_window' : GardnerKnopoffWindow(),
                  'fs_time_prop' : 1.0}
        # Instantiate the declusterer and process the sample catalogue 
        dec = Afteran()
        vcl, flagvector = dec.decluster(self.cat, config)
        print 'vcl:',vcl
        print 'flagvector:',flagvector, self.cat.data['flag']
        self.assertIs(np.allclose(flagvector,self.cat.data['flag']),True)