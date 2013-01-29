
import numpy as np
from hmtk.seismicity.occurrence.base import SeismicityOccurrence
from hmtk.seismicity.occurrence.utils import input_checks, recurrence_table
from hmtk.seismicity.occurrence.aki_maximum_likelihood import AkiMaxLikelihood

class KijkoSmit(SeismicityOccurrence):
    '''Class to Implement the Kijko & Smit (2012) algorithm for estimation
    of a- and b-value'''

    def calculate(self, catalogue, config, completeness=None):
        '''Main function to calculate the a- and b-value'''
        # Input checks
        cmag, ctime, ref_mag, dmag = input_checks(catalogue, config, 
                                                   completeness)
        ival = 0
        mag_eq_tolerance = 1E-5
        number_intervals = np.shape(ctime)[0]
        b_est = np.zeros(number_intervals, dtype=float)
        neq = np.zeros(number_intervals, dtype=float)
        nyr = np.zeros(number_intervals, dtype=float)
        while ival < number_intervals:
            id0 = np.abs(ctime - ctime[ival]) < mag_eq_tolerance
            m_c = np.min(cmag[id0])
            # Find events later than cut-off year, and with magnitude
            # greater than or equal to the corresponding completeness magnitude.
            # m_c - mag_eq_tolerance is required to correct floating point
            # differences.
            id1 = np.logical_and(catalogue['year'] >= ctime[ival],
                catalogue['magnitude'] >= (m_c - mag_eq_tolerance))
            nyr[ival] = np.float(np.max(catalogue['year'][id1]) -
                                 np.min(catalogue['year'][id1]) + 1)
            neq[ival] = np.sum(id1)
            # Get a- and b- value for the selected events
            temp_rec_table = recurrence_table(catalogue['magnitude'][id1], 
                                              dmag, 
                                              catalogue['year'][id1])

            aki_ml = AkiMaxLikelihood()
            b_est[ival]= aki_ml._aki_ml(temp_rec_table[:, 0], 
                                        temp_rec_table[:, 1], 
                                        dmag, m_c)[0]
            ival += 1

        total_neq = np.float(np.sum(neq))
        bval = self._harmonic_mean(b_est, neq)
        sigma_b = bval / np.sqrt(total_neq)
        aval = self._calculate_a_value(bval, total_neq, nyr, cmag, ref_mag)
        sigma_a = self._calculate_a_value(bval + sigma_b, total_neq, nyr, 
                                          cmag, ref_mag)

        if not 'reference_magnitude' in config:
            aval = np.log10(aval)
            sigma_a = np.log10(sigma_a) - aval
        else: 
            sigma_a = sigma_a - aval
        return bval, sigma_b, aval, sigma_a 
        
    def _harmonic_mean(self, parameters, neq):
        '''Harmonic mean'''
        weight = neq.astype(float) / np.sum(neq)
        if np.shape(parameters)[0] != np.shape(weight)[0]:
            raise ValueError('Parameter vector not same shape as weights')
        else:
            average_value = np.zeros(np.shape(parameters)[0], dtype=float)
            average_value = 1. / np.sum(weight / parameters)
        return average_value

    def _calculate_a_value(self, bval, nvalue, nyr, cmag, ref_mag):
        '''Calculates the rate of events >= ref_mag using the b-value estimator
        and Eq. 10 of Kijko & Smit'''

        denominator = np.sum(nyr * np.exp(-bval * (cmag - ref_mag)))
        return nvalue / denominator
