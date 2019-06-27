# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2019 GEM Foundation, G. Weatherill, M. Pagani, D. Monelli
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is free software: you can
# redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein is
# released as a prototype implementation on behalf of scientists and engineers
# working within the GEM Foundation (Global Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the hope that
# it will be useful to the scientific, engineering, disaster risk and software
# design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software developers,
# as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be directed to
# the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# The GEM Foundation, and the authors of the software, assume no liability for
# use of the software.

'''
Module :mod:`openquake.hmtk.seismicity.max_magnitude.kijko_sellevol_bayes`
implements the Kijko & Sellevol (1989) method for estimating maximum magnitude
from observed seismicity with uncertain b-value
'''

import numpy as np
from math import fabs
from scipy.integrate import quadrature
from openquake.hmtk.seismicity.max_magnitude.base import (
    BaseMaximumMagnitude, MAX_MAGNITUDE_METHODS,
    _get_observed_mmax, _get_magnitude_vector_properties)


def check_config(config, data):
    '''Check config file inputs

    :param dict config:
         Configuration settings for the function

    '''
    essential_keys = ['input_mmin', 'b-value', 'sigma-b']
    for key in essential_keys:
        if not key in config.keys():
            raise ValueError('For KijkoSellevolBayes the key %s needs to '
                             'be set in the configuation' % key)
    if 'tolerance' not in config.keys() or not config['tolerance']:
        config['tolerance'] = 1E-5

    if not config.get('maximum_iterations', False):
        config['maximum_iterations'] = 1000

    if config['input_mmin'] < np.min(data['magnitude']):
        config['input_mmin'] = np.min(data['magnitude'])

    if fabs(config['sigma-b'] < 1E-15):
        raise ValueError('Sigma-b must be greater than zero!')

    return config


@MAX_MAGNITUDE_METHODS.add(
    "get_mmax",
    **{"input_mmin": lambda cat: np.min(cat.data['magnitude']),
       "input_mmax": lambda cat: cat.data['magnitude'][
           np.argmax(cat.data['magnitude'])],
       "input_mmax_uncertainty": lambda cat: cat.get_observed_mmax_sigma(0.2),
       "b-value": np.float,
       "sigma-b": np.float,
       "maximum_iterations": 1000,
       "tolerance": 1E-5})
class KijkoSellevolBayes(BaseMaximumMagnitude):
    '''
    Class to implement Kijko & Sellevol Bayesian estimator of Mmax, with
    uncertain b-value
    '''

    def get_mmax(self, catalogue, config):
        '''Calculate maximum magnitude

        :returns: **mmax** Maximum magnitude and **mmax_sig** corresponding uncertainty
        :rtype: Float
        '''
        # Check configuration file
        config = check_config(config, catalogue.data)
        # Negative b-values will return nan - this simply skips the integral
        if config['b-value'] <= 0.0:
            return np.nan, np.nan

        obsmax, obsmaxsig = _get_observed_mmax(catalogue.data, config)

        beta = config['b-value'] * np.log(10.)
        sigbeta = config['sigma-b'] * np.log(10.)

        neq, mmin = _get_magnitude_vector_properties(catalogue.data, config)

        pval = beta / (sigbeta ** 2.)
        qval = (beta / sigbeta) ** 2.

        mmax = np.copy(obsmax)
        d_t = np.inf
        iterator = 0
        while d_t > config['tolerance']:
            rval = pval / (pval + mmax - mmin)
            ldelt = (1. / (1. - (rval ** qval))) ** neq
            delta = ldelt * quadrature(self._ksb_intfunc, mmin, mmax,
                                       args=(neq, mmin, pval, qval))[0]

            tmmax = obsmax + delta
            d_t = np.abs(tmmax - mmax)
            mmax = np.copy(tmmax)
            iterator += 1
            if iterator > config['maximum_iterations']:
                print('Kijko-Sellevol-Bayes estimator reached'
                      'maximum # of iterations')
                d_t = -np.inf

        return mmax.item(), np.sqrt(obsmaxsig ** 2. + delta ** 2.)

    def _ksb_intfunc(self, mval, neq, mmin, pval, qval):
        '''
        Integral function inside Kijko-Sellevol-Bayes estimator
        (part of Eq. 10 in Kijko, 2004 - section 3.2)

        :param float mval:
            Magnitude
        :param float neq:
            Number of Earthquakes
        :param float mmin:
            Minimum Magnitude
        :param float pval:
            p-value (see Kijko, 2004 - section 3.2)
        :param float qval:
            q-value (see Kijki, 2004 - section 3.2)
        :returns:
            Output of function integrand
        '''
        func1 = (1. - ((pval / (pval + mval - mmin)) ** qval)) ** neq
        return func1
