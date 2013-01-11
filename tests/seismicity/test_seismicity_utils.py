#/usr/bin/env/python

'''Tests set of seismicity utility functions including:
i) decimal_year
ii) decimal_time
iii) haversine
iv) greg2julian
v) piecewise_linear_scalar
'''

import unittest
import numpy as np
from hmtk.seismicity import utils

class TestSeismicityUtilities(unittest.TestCase):
    '''Class for testing seismicity utilities'''
    def setUp(self):
        '''Sets up the test class'''
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.second = None
        self.longitude = None
        self.latitude = None

    def test_leap_year_check(self):
        '''Tests the leap year check'''
        # 1900 - Not leap year
        # 1995 - Not leap year
        # 2000 - Leap year
        # 2012 - Leap year
        test_years = np.array([1900, 1995, 2000, 2012])
        leap_values = utils.leap_check(test_years)
        self.assertFalse(leap_values[0])
        self.assertFalse(leap_values[1])
        self.assertTrue(leap_values[2])
        self.assertTrue(leap_values[3])

    def test_decimal_year(self):
        '''Tests the function utils.decimal_year'''
        self.year = np.array([1990., 1995., 2000.])
        self.month = np.array([1., 6., 12.])
        self.day = np.array([1., 30., 31.])
        self.assertTrue(np.allclose(
            utils.decimal_year(self.year, self.month, self.day),
            np.array([1990., 1995.49315068, 2000.99726027])))
    
    def test_decimal_time(self):
        '''Tests the function utils.decimal_time'''
        self.year = np.array([1990, 1995, 2000])
        self.month = np.array([1, 6, 12])
        self.day = np.array([1, 30, 31])
        self.hour = np.array([0, 12, 23])
        self.minute = np.array([0, 30, 59])
        self.second = np.array([0.0, 30.0, 59.0])
        self.assertTrue(np.allclose(
            utils.decimal_time(self.year, self.month, self.day, self.hour, 
            self.minute, self.second),
            np.array([1990., 1995.49457858, 2000.99999997])))
    
    def test_haversine(self):
        '''Tests the function utils.haversine
        Distances tested against i) Matlab implementation of the haversine 
                                    formula
                                ii) Matlab "distance" function (also based on
                                    the haversine formula (assumes 
                                    Earth Radius = 6371.0 not 6371.227 as 
                                    assumed here!)
        '''
        # Simple test
        self.longitude = np.arange(30., 40., 1.)
        self.latitude = np.arange(30., 40., 1.)
        distance = utils.haversine(self.longitude, self.latitude, 35.0, 35.0)
        expected_distance = np.array([[727.09474718], 
                                      [580.39194024],
                                      [434.3102452],
                                      [288.87035021],
                                      [144.09319874], 
                                      [0.],
                                      [143.38776088],
                                      [286.04831311],
                                      [427.95959077],
                                      [569.09922383]])
        self.assertTrue(np.allclose(distance, expected_distance))
        
        # 2-D test
        self.longitude = np.array([30., 35., 40.])
        self.latitude = np.array([30., 35., 40.])
        distance = utils.haversine(self.longitude, self.latitude, 
                                    self.longitude, self.latitude)
        expected_distance = np.array([[ 0., 727.09474718, 1435.38402047],
                                      [727.09474718, 0., 709.44452948],
                                      [1435.38402047, 709.44452948, 0.]])
        self.assertTrue(np.allclose(distance, expected_distance))
        # Crossing International Dateline
        self.longitude = np.array([179.5, 180.0, -179.5])
        self.latitude = np.array([45., 45., 45.])
        distance = utils.haversine(self.longitude, self.latitude, 179.9, 45.)
        expected_distance = np.array([[31.45176332], 
                                      [7.86294832], 
                                      [47.1775851]])
        self.assertTrue(np.allclose(distance, expected_distance))
        
    def test_piecewise_linear_function(self):
        '''Test the piecewise linear calculator'''
        # Good parameter set - 2 segments
        params = [2.0, -1.0, 5.0, 0.0]
        values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
        expected = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 9.0, 8.0, 7.0, 6.0]
        for iloc, xval in enumerate(values):
            self.assertAlmostEqual(expected[iloc], 
                                   utils.piecewise_linear_scalar(params, xval))
        # Odd-number of values in parameters - raise value error
        params = [2.0, -1.0, 5.0, 0.0, 3.4]
        with self.assertRaises(ValueError):
            utils.piecewise_linear_scalar(params, 1.0)
        # Single segment test
        params1seg = [2.0, 0.0]
        self.assertAlmostEqual(2.0, 
                               utils.piecewise_linear_scalar(params1seg, 1.0))
        # 3- segment test
        params = np.array([2.0, -1.0, 3.0, 4.0, 8.0, 0.0])
        expected = [0.0, 2.0, 4.0, 6.0, 8.0, 7.0, 6.0, 5.0, 4.0, 7.0]
        for iloc, xval in enumerate(values):
            self.assertAlmostEqual(expected[iloc], 
                                   utils.piecewise_linear_scalar(params, xval))

