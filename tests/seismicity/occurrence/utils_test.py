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
        # Create the catalogue A
        self.catalogueA = {'year': test_data[:,3], 
                          'magnitude': test_data[:,17]}

        # Read initial dataset  
        filename = os.path.join(self.BASE_DATA_PATH, 
                                'recurrence_test_cat_B.csv')
        test_data = np.genfromtxt(filename, delimiter=',', skip_header=1)
        # Create the catalogue A
        self.catalogueB = {'year': test_data[:,3], 
                          'magnitude': test_data[:,17]}

        # Read the verification table A
        filename = os.path.join(self.BASE_DATA_PATH, 
                                'recurrence_table_test_A.csv')
        self.true_tableA = np.genfromtxt(filename, delimiter = ',')

        # Read the verification table A
        filename = os.path.join(self.BASE_DATA_PATH, 
                                'recurrence_table_test_B.csv')
        self.true_tableB = np.genfromtxt(filename, delimiter = ',')

    def test_recurrence_table_A(self):
        """
        Basic recurrence table test
        """
        magnitude_interval = 0.1
        self.assertTrue( np.allclose(self.true_tableA, 
            rec_utils.recurrence_table(self.catalogueA['magnitude'], 
                                       magnitude_interval,
                                       self.catalogueA['year'])) )

    def test_recurrence_table_B(self):
        """
        Basic recurrence table test
        """
        magnitude_interval = 0.1
        self.assertTrue( np.allclose(self.true_tableB, 
            rec_utils.recurrence_table(self.catalogueB['magnitude'], 
                                       magnitude_interval,
                                       self.catalogueB['year'])) )

    def test_input_checks_raise_error(self):
        fake_completeness_table = np.zeros((10,10))
        catalogue = {}
        config = {}
        self.assertRaises(ValueError, rec_utils.input_checks, catalogue, 
                config, fake_completeness_table)

    def test_input_checks_simple_input(self):
        completeness_table = [[1900, 2.0]]
        catalogue = {'magnitude': [5.0, 6.0], 'year': [2000, 2000]}
        config = {}
        rec_utils.input_checks(catalogue, config, completeness_table)

    def test_input_checks_use_a_float_for_completeness(self):
        fake_completeness_table = 0.0
        catalogue = {'year': [1900]}
        config = {}
        rec_utils.input_checks(catalogue, config, fake_completeness_table)

    def test_input_checks_use_reference_magnitude(self):
        fake_completeness_table = 0.0
        catalogue = {'year': [1900]}
        config = {'reference_magnitude' : 3.0}
        cmag, ctime, ref_mag, dmag = rec_utils.input_checks(catalogue, 
                config, fake_completeness_table)
        self.assertEqual(3.0, ref_mag)

    def test_input_checks_sets_magnitude_interval(self):
        fake_completeness_table = 0.0
        catalogue = {'year': [1900]}
        config = {'magnitude_interval' : 0.1}
        cmag, ctime, ref_mag, dmag = rec_utils.input_checks(catalogue, 
                config, fake_completeness_table)
        self.assertEqual(0.1, dmag)
