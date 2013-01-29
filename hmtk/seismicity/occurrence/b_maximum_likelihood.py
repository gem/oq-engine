# -*- coding: utf-8 -*-
"""
"""

import numpy as np
from hmtk.seismicity.occurrence.utils import input_checks, recurrence_table
from hmtk.seismicity.occurrence.base import SeismicityOccurrence
from hmtk.seismicity.occurrence.aki_maximum_likelihood import AkiMaxLikelihood

class BMaxLikelihood(SeismicityOccurrence):
    """ Implements maximum likelihood calculations taking into account time
    variation in completeness"
    """
   
    def calculate(self, catalogue, config, completeness=None, end_year=None):
        """ Calculates recurrence parameters a_value and b_value, and their 
        respective uncertainties

        :param dict catalogue: Earthquake Catalogue 
            An instance of :class:`hmtk.seismicity.catalogue`
        :param dict config: 
            A configuration dictionary; the only parameter that can be 
            defined in this case if the type of average to be applied 
            in the calculation
        :param list or numpy.ndarray completeness: 
            Completeness table
        :param int end_year: 
            Catalogue termination year 
        """

        # Input checks
        cmag, ctime, ref_mag, dmag = input_checks(catalogue, config,
                                                    completeness)

        # Fix the end year
        if end_year is None:
            end_year = np.max(catalogue['year'])

        # Check the configuration
        if not config['Average Type'] in ['Weighted','Harmonic']:
            raise ValueError('Average type not recognised in bMaxLiklihood!')

        return self._b_ml(catalogue, config, cmag, ctime, ref_mag, 
                dmag, end_year)

    def _b_ml(self, catalogue, config, cmag, ctime, ref_mag, dmag, end_year):
        """
        """

        ival = 0
        mag_eq_tolerance = 1E-5
        aki_ml = AkiMaxLikelihood()

        while ival < np.shape(ctime)[0]:

            id0 = np.abs(ctime - ctime[ival]) < mag_eq_tolerance
            m_c = np.min(cmag[id0])

            print '--- ctime',ctime[ival],' m_c',m_c

            # Find events later than cut-off year, and with magnitude
            # greater than or equal to the corresponding completeness magnitude.
            # m_c - mag_eq_tolerance is required to correct floating point
            # differences.
            id1 = np.logical_and(catalogue['year'] >= ctime[ival],
                catalogue['magnitude'] >= (m_c - mag_eq_tolerance))
            nyr = np.float(np.max(catalogue['year'][id1])) - ctime[ival] + 1.
            # Get a- and b- value for the selected events
            temp_rec_table = recurrence_table(catalogue['magnitude'][id1], 
                                              dmag, 
                                              catalogue['year'][id1],
                                              end_year-ctime[ival]+1)
            
            bval, sigma_b = aki_ml._aki_ml(temp_rec_table[:, 0],
                                             temp_rec_table[:, 1], dmag, m_c)

            aval = np.log10(np.float(np.sum(id1)) / nyr) + bval * m_c
            sigma_a = np.abs(np.log10(np.float(np.sum(id1)) / nyr) +
                (bval + sigma_b) * ref_mag - aval)

            # Calculate reference rate
            rate = 10.0 ** (aval - bval * ref_mag)
            sigrate = 10.0 ** ((aval + sigma_a) - (bval * ref_mag) -
                np.log10(rate))
            if ival == 0:
                gr_pars = np.array([np.hstack([bval, sigma_b, rate, sigrate])])
                neq = np.sum(id1)  # Number of events
            else:
                gr_pars = np.vstack([gr_pars, np.hstack([bval, sigma_b, rate,
                                                         sigrate])])
                neq = np.hstack([neq, np.sum(id1)])
            ival = ival + np.sum(id0)

        # Get average GR parameters
        bval, sigma_b, aval, sigma_a = self._average_parameters(gr_pars, neq, 
                config['Average Type'])

        if not 'reference_magnitude' in config:
            d_aval = aval - sigma_a
            aval = np.log10(aval)
            sigma_a = aval - np.log10(d_aval)

        return bval, sigma_b, aval, sigma_a
    
    def _average_parameters(self, gr_params, neq, average_type='Weighted'):
        """Calculates the average of a set of Gutenberg-Richter parameters
        depending on the average type

        :param numpy.ndarray gr_params: 
            Gutenberg-Richter parameters [b, sigma_b, a, sigma_a]
        :param numpy.ndarray neq:
            
        """ 
        if np.shape(gr_params)[0] != np.shape(neq)[0]:
            raise ValueError('Number of weights does not correspond'
                             ' to number of parameters')
        
        #neq = neq.astype(float)
        if 'Harmonic' in average_type:
            average_parameters = self._harmonic_mean(gr_params, neq)
        else:
            average_parameters = self._weighted_mean(gr_params, neq)
        bval = average_parameters[0]
        sigma_b = average_parameters[1]
        aval = average_parameters[2]
        sigma_a = average_parameters[3]
        return bval, sigma_b, aval, sigma_a 
        

    def _weighted_mean(self, parameters, neq):
        '''Simple weighted mean'''
        weight = neq.astype(float) / np.sum(neq)
        if np.shape(parameters)[0] != np.shape(weight)[0]:
            raise ValueError('Parameter vector not same shape as weights')
        else:
            average_value = np.zeros(np.shape(parameters)[1], dtype=float)
            for iloc in range(0, np.shape(parameters)[1]):
                average_value[iloc] = np.sum(parameters[:, iloc] * weight)
        return average_value

    def _harmonic_mean(self, parameters, neq):
        '''Harmonic mean'''
        weight = neq.astype(float) / np.sum(neq)
        if np.shape(parameters)[0] != np.shape(weight)[0]:
                raise ValueError('Parameter vector not same shape as weights')
        else:
            average_value = np.zeros(np.shape(parameters)[1], dtype=float)
            for iloc in range(0, np.shape(parameters)[1]):
                average_value[iloc] = 1. / np.sum(
                    (weight * (1. / parameters[:, iloc])))
        return average_value
