# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2019 GEM Foundation, G. Weatherill, M. Pagani, D. Monelli
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein is released as
# a prototype implementation on behalf of scientists and engineers working
# within the GEM Foundation (Global Earthquake Model).
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
Module :class: openquake.hmtk.seismicity.max_magnitude.cumulative_moment.CumulativeMoment
implements cumulative moment estimator of maximum magnitude from instrumental
seismicity
'''
from math import fabs
import numpy as np
from openquake.hmtk.seismicity.max_magnitude.base import (
    BaseMaximumMagnitude, MAX_MAGNITUDE_METHODS)


@MAX_MAGNITUDE_METHODS.add("get_mmax", number_bootstraps=np.int)
class CumulativeMoment(BaseMaximumMagnitude):
    '''Class to implement the bootstrapped cumulative moment estimator of
    maximum magnitude. Adapted by G. Weatherill from the Cumulative Strain
    Energy approach originally suggested by Makropoulos & Burton (1983)'''

    def get_mmax(self, catalogue, config):
        '''
        Calculates Maximum magnitude and its uncertainty

        :param catalogue:
            Instance of openquake.hmtk.seismicity.catalogue.Catalogue class
            Earthquake calatalogue data as dictionary containing -
            * 'year' - Year of event
            * 'magnitude' - Magnitude of event
            * 'sigmaMagnitude' - Uncertainty on magnitude (optional)

        :param dict config:
            Configuration file for algorithm, containing thw following -
            * 'number_bootstraps' - Number of bootstraps for uncertainty

        :param int seed:
            Seed for random number generator (must be positive)

        :returns:
            * Maximum magnitude (float)
            * Uncertainty on maximum magnituse (float)
        '''

        # If no bootstraps no uncertainty on magnitudes then simply calculate
        # Mmax without uncertainty
        self.check_config(config)
        cond = config['number_bootstraps'] == 1 or\
            not isinstance(catalogue.data['sigmaMagnitude'], np.ndarray) or\
            len(catalogue.data['sigmaMagnitude']) == 0 or\
            np.all(np.isnan(catalogue.data['sigmaMagnitude']))

        if cond:
            return self.cumulative_moment(catalogue.data['year'],
                                          catalogue.data['magnitude']), 0.0

        neq = len(catalogue.data['magnitude'])
        mmax_samp = np.zeros(config['number_bootstraps'], dtype=float)

        # Sample magnitudes from catalogue and calculate MMax from sample
        for iloc in range(0, config['number_bootstraps']):
            mw_sample = catalogue.data['magnitude'] + \
                catalogue.data['sigmaMagnitude'] * np.random.normal(0., 1.,
                                                                    neq)
            mmax_samp[iloc] = self.cumulative_moment(catalogue.data['year'],
                                                     mw_sample)
        # Return mean and standard deviation of samples
        return np.mean(mmax_samp), np.std(mmax_samp, ddof=1)

    def check_config(self, config):
        '''
        Checks the configuration file for the number of bootstraps.
        Returns 1 if not found or invalid (i.e. < 0)
        '''
        nb = config['number_bootstraps'] or 0
        if nb < 1:
            config['number_bootstraps'] = 1
        return config

    def cumulative_moment(self, year, mag):
        '''Calculation of Mmax using aCumulative Moment approach, adapted from
        the cumulative strain energy method of Makropoulos & Burton (1983)

        :param year: Year of Earthquake
        :type year: numpy.ndarray
        :param mag: Magnitude of Earthquake
        :type mag: numpy.ndarray
        :keyword iplot: Include cumulative moment plot
        :type iplot: Boolean
        :return mmax: Returns Maximum Magnitude
        :rtype mmax: Float
        '''
        # Calculate seismic moment
        m_o = 10. ** (9.05 + 1.5 * mag)
        year_range = np.arange(np.min(year), np.max(year) + 1, 1)
        nyr = np.shape(year_range)[0]
        morate = np.zeros(nyr, dtype=float)
        # Get moment release per year
        for loc, tyr in enumerate(year_range):
            idx = np.abs(year - tyr) < 1E-5
            if np.sum(idx) > 0:
                # Some moment release in that year
                morate[loc] = np.sum(m_o[idx])
        ave_morate = np.sum(morate) / nyr

        # Average moment rate vector
        exp_morate = np.cumsum(ave_morate * np.ones(nyr))
        modiff = (np.abs(np.max(np.cumsum(morate) - exp_morate)) +
                  np.abs(np.min(np.cumsum(morate) - exp_morate)))
        # Return back to Mw
        if fabs(modiff) < 1E-20:
            return -np.inf
        mmax = (2. / 3.) * (np.log10(modiff) - 9.05)
        return mmax
