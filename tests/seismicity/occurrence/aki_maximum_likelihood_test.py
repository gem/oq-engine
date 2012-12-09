# -*- coding: utf-8 -*-

"""

"""

import os
import unittest
import numpy as np

from hmtk.seismicity.occurrence.utils import recurrence_table
from hmtk.seismicity.catalogue import Catalogue
from hmtk.seismicity.occurrence.aki_maximum_likelihood import aki_max_likelihood

class AkiMaximumLikelihoodTestCase(unittest.TestCase):
    """ 
    Unit tests for the Aki maximum likelihood algorithm class which computes 
    seismicity occurrence parameters.
    """
    
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    
    def setUp(self):
        """
        This generates a minimum data-set to be used for the regression.  
        """
        # Generates a data set assuming b=1 and N(m=4.0)=10.0 events
        self.dmag = 0.1
        mext = np.arange(4.0,7.01,0.1)
        self.mval = mext[0:-1] + self.dmag / 2.0
        self.bval = 1.0
        self.numobs = np.diff(10.0**(-self.bval*mext+5.0))
        
    def test_aki_maximum_likelihood(self):
        """
        Tests that the computed b value corresponds to the same value
        used to generate the test data set 
        """
        # Isn't the magnitude interval width implicitly defined by mval?
        bval, sigma_b = aki_max_likelihood(self.mval, self.numobs, 
                                                dmag=self.dmag, m_c=0.0)
        self.assertAlmostEqual(self.bval, bval, 2)