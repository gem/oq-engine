# -*- coding: utf-8 -*-

"""
Unit tests for the Aki maximum likelihood algorithm class which computes 
seismicity occurrence parameters.
"""

import unittest
import numpy as np

from hmtk.seismicity.occurrence.aki_maximum_likelihood import AkiMaxLikelihood

class AkiMaximumLikelihoodTestCase(unittest.TestCase):
    
    def setUp(self):
        """
        This generates a minimum data-set to be used for the regression.  
        """
        # Test A: Generates a data set assuming b=1 and N(m=4.0)=10.0 events
        self.dmag = 0.1
        mext = np.arange(4.0,7.01,0.1)
        self.mval = mext[0:-1] + self.dmag / 2.0
        self.bval = 1.0
        self.numobs = np.flipud(np.diff(np.flipud(10.0**(-self.bval*mext+8.0))))
        # Test B: Generate a completely artificial catalogue using the 
        # Gutenberg-Richter distribution defined above 
        numobs = np.around(self.numobs)
        magnitude = np.zeros( (np.sum(self.numobs)) )
        lidx = 0
        for mag, nobs in zip(self.mval, numobs):
            uidx = int(lidx+nobs)
            magnitude[lidx:uidx] = mag + 0.01 
            lidx = uidx 
        year = np.ones( (np.sum(numobs)) ) * 1999 
        self.catalogue = {'magnitude' : magnitude, 'year': year}
        # Create the seismicity occurrence calculator 
        self.aki_ml = AkiMaxLikelihood()

    def test_aki_maximum_likelihood_A(self):
        """
        Tests that the computed b value corresponds to the same value
        used to generate the test data set 
        """
        bval, sigma_b = self.aki_ml._aki_ml(self.mval, self.numobs)
        self.assertAlmostEqual(self.bval, bval, 2)

    def test_aki_maximum_likelihood_B(self):
        """
        Tests that the computed b value corresponds to the same value
        used to generate the test data set 
        """
        bval, sigma_b = self.aki_ml.calculate(self.catalogue)        
        self.assertAlmostEqual(self.bval, bval, 2)
