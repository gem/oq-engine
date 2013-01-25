# -*- coding: utf-8 -*-

import numpy as np
from hmtk.seismicity.occurrence.base import SeismicityOccurrence
from hmtk.seismicity.occurrence.utils import recurrence_table

class AkiMaxLikelihood(SeismicityOccurrence):

    def calculate(self, catalogue, config=None, completeness=None):
        """ Calculation of b-value and its uncertainty for a given 
        catalogue, using the maximum likelihood method of Aki (1965), 
        with a correction for discrete bin width (Bender, 1983).

        :param catalogue:
            See :class:`hmtk.seismicity.occurrence.base.py' for further 
            explanation
        :param config:
            The configuration in this case do not contains specific 
            information
        :keyword float completeness: 
            Completeness magnitude

        :return bval:
            b-value of the Gutenberg-Richter relationship
        :rtype float:
        :return sigma_b:
        :rtype float:
        """
        rt = recurrence_table(catalogue['magnitude'])
        bval, sigma_b = self._aki_ml(rt[:,0], rt[:,1])
        return bval, sigma_b 

    def _aki_ml(self, mval, number_obs, dmag=0.1, m_c=0.0):
        """
        :param numpy.ndarray mval: 
            array of reference magnitudes (column 0 from recurrence 
            table)
        :param numpy.ndarray number_obs: 
            number of observations in magnitude bin (column 1 from 
            recurrence table)
        :keyword float dmag: 
            magnitude interval
        :keyword float m_c: 
            completeness magnitude
        :returns: 
            bvalue and sigma_b
        :rtype: float
        """
        # Exclude data below Mc
        id0 = mval >= m_c
        print id0
        mval = mval[id0]
        number_obs = number_obs[id0]
        # Get Number of events, minimum magnitude and mean magnitude
        neq = np.sum(number_obs)
        m_min = np.min(mval)
        m_ave = np.sum(mval * number_obs) / neq
        # Calculate b-value
        bval = np.log10(np.exp(1.0)) / (m_ave - m_min + (dmag / 2.))
        # Calculate sigma b from Bender estimator
        sigma_b = np.sum(number_obs * ((mval - m_ave) ** 2.0)) / (neq * (neq - 1))
        sigma_b = np.log(10.) * (bval ** 2.0) * np.sqrt(sigma_b)
        return bval, sigma_b
