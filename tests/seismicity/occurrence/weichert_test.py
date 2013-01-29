# -*- coding: utf-8 -*-

"""
Unit tests for the Weichert algorithm class which computes 
seismicity occurrence parameters.
"""

import unittest
import numpy as np

from hmtk.seismicity.occurrence.weichert import Weichert

class WeichertTestCase(unittest.TestCase):
    
    def setUp(self):
        """
        This generates a catalogue to be used for the regression.  
        """
        # Generates a data set assuming b=1
        self.dmag = 0.1
        mext = np.arange(4.0,7.01,0.1)
        self.mval = mext[0:-1] + self.dmag / 2.0
        self.bval = 1.0
        numobs = np.flipud(np.diff(np.flipud(10.0**(-self.bval*mext+7.0))))
        # Compute the number of observations in the different magnitude 
        # intervals (according to completeness) 
        numobs[0:6] *= 10
        numobs[6:13] *= 20
        numobs[13:22] *= 50
        numobs[22:] *= 100
        # Define completeness window
        compl = np.array([[1900, 1950, 1980, 1990], [6.34, 5.44, 4.74, 3.0]])
        self.compl = compl.transpose()
        # Compute the number of observations (i.e. earthquakes) in each 
        # magnitude bin
        numobs = np.around(numobs)
        magnitude = np.zeros( (np.sum(numobs)) )
        year = np.zeros( (np.sum(numobs)) ) * 1999 
        # Generate the catalogue
        lidx = 0
        for mag, nobs in zip(self.mval, numobs):
            uidx = int(lidx+nobs)
            magnitude[lidx:uidx] = mag + 0.01
            year_low = compl[0,np.min(np.nonzero(compl[1,:] < mag)[0])] 
            year[lidx:uidx] = (year_low + np.random.rand(uidx-lidx) * 
                    (2000-year_low))
            lidx = uidx 
        # Fix the parameters that later will be used for the testing 
        self.catalogue = {'magnitude' : magnitude, 'year' : year}
        self.wei = Weichert()
        self.config = {'Average Type' : 'Weighted'}
        
    def test_weichert(self):
        """
        Tests that the computed b value corresponds to the same value
        used to generate the test data set 
        """
        bval, sigma_b, aval, sigma_a = self.wei.calculate(self.catalogue, 
                self.config, self.compl)
        self.assertAlmostEqual(self.bval, bval, 1)
