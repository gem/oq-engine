# -*- coding: utf-8 -*-

"""
Unit tests for the maximum likelihood algorithm class which computes 
seismicity occurrence parameters.
"""

import unittest
import numpy as np

from hmtk.seismicity.occurrence.b_maximum_likelihood import BMaxLikelihood

class BMaxLikelihoodTestCase(unittest.TestCase):
    
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

        # Define completeness window
        numobs[0:6] *= 10
        numobs[6:13] *= 20
        numobs[13:22] *= 50
        numobs[22:] *= 100

        compl = np.array([[1900, 1950, 1980, 1990], [6.34, 5.44, 4.74, 3.0]])
        print compl
        self.compl = compl.transpose()
        print 'completeness'
        print self.compl
        print self.compl.shape
        
        #self.compl = compl
        
        numobs = np.around(numobs)
        print numobs

        magnitude = np.zeros( (np.sum(numobs)) )
        year = np.zeros( (np.sum(numobs)) ) * 1999 

        lidx = 0
        for mag, nobs in zip(self.mval, numobs):
            uidx = int(lidx+nobs)
            magnitude[lidx:uidx] = mag + 0.01
            year_low = compl[0,np.min(np.nonzero(compl[1,:] < mag)[0])] 
            year[lidx:uidx] = (year_low + np.random.rand(uidx-lidx) * 
                    (2000-year_low))
            print '%.2f %.0f %.0f' % (mag,np.min(year[lidx:uidx]), np.max(year[lidx:uidx]))
            lidx = uidx 

        self.catalogue = {'magnitude' : magnitude, 'year' : year}
        self.b_ml = BMaxLikelihood()
        self.config = {'Average Type' : 'Weighted'}
        
    def test_b_maximum_likelihood(self):
        """
        Tests that the computed b value corresponds to the same value
        used to generate the test data set 
        """
        bval, sigma_b, aval, sigma_a = self.b_ml.calculate(self.catalogue, 
                self.config, self.compl)
        self.assertAlmostEqual(self.bval, bval, 1)

    def test_b_maximum_likelihood_raise_error(self):
        completeness_table = np.zeros((10,2))
        catalogue = {'year': [1900]}
        config = {'Average Type' : ['fake']}
        self.assertRaises(ValueError, self.b_ml.calculate, catalogue, 
                config, completeness_table)

    def test_b_maximum_likelihood_average_parameters_raise_error(self):
        num = 4 
        gr_pars = np.zeros((10,num))
        neq = np.zeros((num))
        self.assertRaises(ValueError, self.b_ml._average_parameters, 
                gr_pars, neq)

    def test_b_maximum_likelihood_average_parameters_use_harmonic(self):
        num = 4 
        gr_pars = np.ones((num,10))
        neq = np.ones((num))
        self.b_ml._average_parameters(gr_pars, neq, average_type='Harmonic')

    def test_b_maximum_likelihood_weighted_mean_raise_error(self):
        num = 4 
        parameters = np.ones((num))
        neq = np.ones((num+1))
        self.assertRaises(ValueError, self.b_ml._weighted_mean, 
                parameters, neq)

    def test_b_maximum_likelihood_harmonic_mean_raise_error(self):
        num = 4 
        parameters = np.ones((num))
        neq = np.ones((num+1))
        self.assertRaises(ValueError, self.b_ml._harmonic_mean, 
                parameters, neq)
