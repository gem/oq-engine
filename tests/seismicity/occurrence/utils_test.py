# -*- coding: utf-8 -*-  
    
import os
import unittest
import numpy as np

import hmtk.seismicity.occurrence.utils as rec_utils

class RecurrenceTableTestCase(unittest.TestCase):
    """ 
    Unit tests for .
    """
    
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')    
    
    def setUp(self):
        """
        """
        # Read initial dataset  
        filename = os.path.join(self.BASE_DATA_PATH, 
                                'completeness_test_cat.csv')
        test_data = np.genfromtxt(filename, delimiter=',', skip_header=1)
        # Create the catalogue
        self.catalogue = {'year': test_data[:,3], 
                          'magnitude': test_data[:,17]}
        # Read the verification table
        filename = os.path.join(self.BASE_DATA_PATH, 
                                'recurrence_table_test_1.csv')
        self.true_table = np.genfromtxt(filename, delimiter = ',')
    
    def test_recurrence_table(self):
        """
        Basic recurrence table test
        """
        magnitude_interval = 0.1
        self.assertTrue( np.allclose(self.true_table, 
            rec_utils.recurrence_table(self.catalogue['magnitude'], 
                                       magnitude_interval,
                                       self.catalogue['year'])) )