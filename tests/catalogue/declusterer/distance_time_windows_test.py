import unittest
import os
import numpy as np

from hmtk.catalogue.declusterer.distance_time_windows import (
    GardnerKnopoffWindow, GruenthalWindow, UhrhammerWindow)

class CsvCatalogueParserTestCase(unittest.TestCase):
    """ Unit tests for the csv Catalogue Parser Class"""
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    
    def setUp(self):
        self.gardner_knopoff_window = GardnerKnopoffWindow()
        self.gruenthal_window = GruenthalWindow()
        self.uhrhammer_window = UhrhammerWindow()

    def test_gardner_knopoff_window(self):
        """
        Test the Gardner and Knopoff Distance-Time window
        """
        mag = np.array([5.0,6.6])
        sw_space, sw_time = self.gardner_knopoff_window.calc(mag)
        self.assertAlmostEqual(sw_space[0], 39.99447, places=5)
        self.assertAlmostEqual(sw_space[1], 63.10736, places=5)
        self.assertAlmostEqual(sw_time[0], 143.71430/364.75, places=5)
        self.assertAlmostEqual(sw_time[1], 891.45618/364.75, places=5)
    
    def test_gruenthal_window(self):
        """
        Test the Gruenthal Distance-Time window
        """
        mag = np.array([5.0,6.6])
        sw_space, sw_time = self.gruenthal_window.calc(mag)
        #self.assertAlmostEqual(sw_space[0], 39.99447, places=5)
        #self.assertAlmostEqual(sw_time[0], 143.71430/364.75, places=5)
        #self.assertAlmostEqual(sw_space[1], 63.10736, places=5)
        #self.assertAlmostEqual(sw_time[1], 891.45618/364.75, places=5)
    
    def test_uhrhammer_window(self):
        mag = np.array([5.0,6.6])
        sw_space, sw_time = self.uhrhammer_window.calc(mag)
        #self.assertAlmostEqual(sw_space[0], 39.99447, places=5)
        #self.assertAlmostEqual(sw_time[0], 143.71430/364.75, places=5)
        #self.assertAlmostEqual(sw_space[1], 63.10736, places=5)
        #self.assertAlmostEqual(sw_time[1], 891.45618/364.75, places=5)