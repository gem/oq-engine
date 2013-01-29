
import numpy as np
from hmtk.seismicity.occurrence.base import SeismicityOccurrence
from hmtk.seismicity.occurrence.utils import input_checks

class Weichert(SeismicityOccurrence):
    '''Class to Implement Weichert Algorithm'''

    def calculate(self, catalogue, config, completeness=None):
        '''Calculates recurrence using the Weichert (1980) method'''
        # Input checks
        cmag, ctime, ref_mag, dmag = input_checks(catalogue, config,
                                                   completeness)
        # Apply Weichert preparation
        cent_mag, t_per, n_obs = self._weichert_prep(catalogue['year'],
                                                     catalogue['magnitude'],
                                                     ctime, cmag, dmag)

        # A few more Weichert checks
        key_list = config.keys()
        if (not 'bvalue' in key_list) or (not config['bvalue']):
            config['bvalue'] = 1.0
        if (not 'itstab' in key_list) or (not config['itstab']):
            config['itstab'] = 1E-5
        if (not 'maxiter' in key_list) or (not config['maxiter']):
            config['maxiter'] = 1000

        bval, sigma_b, rate, sigma_rate, aval, sigma_a = \
            self.weichert_algorithm(t_per, cent_mag, n_obs, ref_mag, 
            config['bvalue'], config['itstab'], config['maxiter'])

        if not 'reference_magnitude' in config:
            rate = np.log10(aval)
            sigma_rate = np.log10(sigma_a)

        return bval, sigma_b, rate, sigma_rate

    def _weichert_prep(self, year, magnitude, ctime, cmag, dmag, dtime=1.0):
        """
        Allows to prepare table input for Weichert algorithm

        :param year: catalog matrix year column
        :type year: numpy.ndarray
        :param magnitude: catalog matrix magnitude column
        :type magnitude: numpy.ndarray
        :param ctime: year of completeness for each period
        :type ctime: numpy.ndarray
        :param cmag: completeness magnitude for each period
        :type cmag: numpy.ndarray
        :param dmag: magnitude bin size (config file)
        :type dmag: positive float
        :param dtime: time bin size from config file)
        
        :type dtime: float
        :returns: central magnitude, tper length of observation period,
                  n_obs number of events in magnitude increment
        """

        # In the case that the user defines a single value for ctime or cmag
        # that is not an array
        if not(isinstance(ctime, np.ndarray)) and not(isinstance(ctime, list)):
            ctime = np.array([ctime])
        if not(isinstance(cmag, np.ndarray)) and not(isinstance(cmag, list)):
            cmag = np.array([cmag])
        valid_events = np.ones(np.shape(year)[0], dtype = bool)
        # Remove events from catalogue below completeness intervals
        mag_eq_tolerance = dmag / 1.E7
        time_tolerance = dtime / 1.E7

        for iloc, mag in enumerate(cmag):
            index0 = np.logical_and(magnitude < (mag - mag_eq_tolerance), 
                                    year < (ctime[iloc] - time_tolerance))
            valid_events[index0] = False
      
           
        year = year[valid_events]
        magnitude = magnitude[valid_events]
        for iloc, yr in enumerate(year):
            dum = np.hstack([iloc, yr, magnitude[iloc]])

        mag_range = np.arange(np.min(magnitude) - dmag / 2., 
                              np.max(magnitude) + (2.0 * dmag), dmag)
        time_range = np.arange(np.min(year) - dtime / 2.,
                               np.max(year) + (2.0 * dtime), 
                               dtime)
        
        # Histogram data
        fullcount1 = np.histogram2d(year, magnitude, 
                                    bins = [time_range, mag_range])[0]
        n_y = np.shape(fullcount1)[1] - 1
        cent_mag = ((mag_range[:-1] + mag_range[1:]) / 2.)[:-1]
        
        n_obs = np.sum(fullcount1, axis=0)[:-1]
        t_per = np.zeros(n_y)
        for iloc, mag in enumerate(cmag):
            index0 = cent_mag > (mag - (dmag / 2. - mag_eq_tolerance))
            t_per[index0] = np.max(year) - ctime[iloc] + 1

        #cut off magnitudes below the lowest magnitude of completeness
        valid_location = np.nonzero(t_per)[0][0]
        cent_mag = cent_mag[valid_location:]
        t_per = t_per[valid_location:]
        n_obs = n_obs[valid_location:]
        
        return cent_mag, t_per, n_obs

    def weichert_algorithm(self, tper, fmag, nobs, mrate=0.0, bval=1.0, 
                           itstab=1E-5, maxiter=1000):
        """
        Weichert algorithm

        :param tper: length of observation period corresponding to magnitude
        :type tper: numpy.ndarray (float)
        :param fmag: central magnitude
        :type fmag: numpy.ndarray (float)
        :param nobs: number of events in magnitude increment
        :type nobs: numpy.ndarray (int)
        :keyword mrate: reference magnitude
        :type mrate: float
        :keyword bval: initial value for b-value
        :type beta: float
        :keyword itstab: stabilisation tolerance
        :type itstab: float
        :keyword maxiter: Maximum number of iterations
        :type maxiter: Int
        :returns: b-value, sigma_b, a-value, sigma_a
        :rtype: float
        """
        beta = bval * np.log(10.)
        d_m = fmag[1] - fmag[0]
        itbreak = 0
        snm = np.sum(nobs * fmag)
        nkount = np.sum(nobs)
        iteration = 1
        while (itbreak != 1):
            beta_exp = np.exp(-beta * fmag)
            tjexp = tper * beta_exp
            tmexp = tjexp * fmag
            sumexp = np.sum(beta_exp)
            stmex = np.sum(tmexp)
            sumtex = np.sum(tjexp)
            stm2x = np.sum(fmag * tmexp)
            dldb = stmex / sumtex
            if np.isnan(stmex) or np.isnan(sumtex):
                raise ValueError('NaN occers in Weichert iteration')

            d2ldb2 = nkount * ((dldb ** 2.0) - (stm2x / sumtex))
            dldb = (dldb * nkount) - snm
            betl = np.copy(beta)
            beta = beta - (dldb / d2ldb2)
            sigbeta = np.sqrt(-1. / d2ldb2)

            if np.abs(beta - betl) <= itstab:
                # Iteration has reached convergence
                bval = beta / np.log(10.0)
                sigb = sigbeta / np.log(10.)
                fngtm0 = nkount * (sumexp / sumtex)
                fn0 = fngtm0 * np.exp((beta) * (fmag[0] - (d_m / 2.0)))
                stdfn0 = fn0 / np.sqrt(nkount)
                #if mrate == 0.:
                #    a_m = fn0
                #    siga_m = stdfn0
                #else:
                a_m = fngtm0 * np.exp((-beta) * (mrate -
                                                (fmag[0] - (d_m / 2.0))))
                siga_m = a_m / np.sqrt(nkount)
                itbreak = 1
            else:
                iteration += 1
                if iteration > maxiter:
                    raise RuntimeError('Maximum Number of Iterations reached')
                continue
        return bval, sigb, a_m, siga_m, fn0, stdfn0
