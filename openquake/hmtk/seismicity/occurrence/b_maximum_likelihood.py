# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-
"""
"""

import numpy as np
from openquake.hmtk.seismicity.occurrence.utils import input_checks, recurrence_table
from openquake.hmtk.seismicity.occurrence.base import (
    SeismicityOccurrence, OCCURRENCE_METHODS)
from openquake.hmtk.seismicity.occurrence.aki_maximum_likelihood import AkiMaxLikelihood


@OCCURRENCE_METHODS.add(
    'calculate', **{
        'completeness': True,
        'reference_magnitude': 0.0,
        'magnitude_interval': 0.1,
        'Average Type': ['Weighted', 'Harmonic']})
class BMaxLikelihood(SeismicityOccurrence):
    """ Implements maximum likelihood calculations taking into account time
    variation in completeness"
    """

    def calculate(self, catalogue, config, completeness=None):
        """ Calculates recurrence parameters a_value and b_value, and their
        respective uncertainties

        :param catalogue: Earthquake Catalogue
            An instance of :class:`openquake.hmtk.seismicity.catalogue`
        :param dict config:
            A configuration dictionary; the only parameter that can be
            defined in this case if the type of average to be applied
            in the calculation
        :param list or numpy.ndarray completeness:
            Completeness table
        """

        # Input checks
        cmag, ctime, ref_mag, dmag, config = input_checks(catalogue,
                                                          config,
                                                          completeness)

        # Check the configuration
        if not config['Average Type'] in ['Weighted','Harmonic']:
            raise ValueError('Average type not recognised in bMaxLiklihood!')
        return self._b_ml(catalogue, config, cmag, ctime, ref_mag, dmag)


    def _b_ml(self, catalogue, config, cmag, ctime, ref_mag, dmag):
        end_year = float(catalogue.end_year)
        catalogue = catalogue.data
        ival = 0
        mag_eq_tolerance = 1E-5
        aki_ml = AkiMaxLikelihood()

        while ival < np.shape(ctime)[0]:

            id0 = np.abs(ctime - ctime[ival]) < mag_eq_tolerance
            m_c = np.min(cmag[id0])

            print('--- ctime', ctime[ival], ' m_c', m_c)

            # Find events later than cut-off year, and with magnitude
            # greater than or equal to the corresponding completeness
            # magnitude. m_c - mag_eq_tolerance is required to correct
            # floating point differences.
            id1 = np.logical_and(
                catalogue['year'] >= ctime[ival],
                catalogue['magnitude'] >= (m_c - mag_eq_tolerance))
            # Get a- and b- value for the selected events
            temp_rec_table = recurrence_table(catalogue['magnitude'][id1],
                                              dmag,
                                              catalogue['year'][id1],
                                              end_year-ctime[ival]+1)

            bval, sigma_b = aki_ml._aki_ml(temp_rec_table[:, 0],
                                           temp_rec_table[:, 1], dmag, m_c)

            if ival == 0:
                gr_pars = np.array([np.hstack([bval, sigma_b])])
                neq = np.sum(id1)  # Number of events
            else:
                gr_pars = np.vstack([gr_pars, np.hstack([bval, sigma_b])])
                neq = np.hstack([neq, np.sum(id1)])
            ival = ival + np.sum(id0)

        # Get average GR parameters
        bval, sigma_b = self._average_parameters(
            gr_pars, neq, config['Average Type'])
        aval = self._calculate_a_value(bval,
                                       np.float(np.sum(neq)),
                                       cmag,
                                       ctime,
                                       catalogue['magnitude'],
                                       end_year,
                                       dmag)
        sigma_a = self._calculate_a_value(bval + sigma_b,
                                          np.float(np.sum(neq)),
                                          cmag,
                                          ctime,
                                          catalogue['magnitude'],
                                          end_year,
                                          dmag)
        if not config['reference_magnitude']:
            return bval,\
                   sigma_b,\
                   aval,\
                   sigma_a - aval
        else:
            rate = 10. ** (aval - bval * config['reference_magnitude'])
            sigma_rate =  10. ** (sigma_a - 
                bval * config['reference_magnitude']) - rate
            return bval,\
                   sigma_b,\
                   rate,\
                   sigma_rate

    def _average_parameters(self, gr_params, neq, average_type='Weighted'):
        """
        Calculates the average of a set of Gutenberg-Richter parameters
        depending on the average type

        :param numpy.ndarray gr_params:
            Gutenberg-Richter parameters [b, sigma_b, a, sigma_a]
        :param numpy.ndarray neq:

        """
        if np.shape(gr_params)[0] != neq.size:
            raise ValueError('Number of weights does not correspond'
                             ' to number of parameters')

        if 'Harmonic' in average_type:
            average_parameters = self._harmonic_mean(gr_params, neq)
        else:
            average_parameters = self._weighted_mean(gr_params, neq)
        bval = average_parameters[0]
        sigma_b = average_parameters[1]
        return bval, sigma_b

    def _calculate_a_value(self, bvalue, nvalue, cmag, cyear, magnitude,
        end_year, dmag):
        """
        Calculates the a-value using the method of Weichert (1980) and 
        McGuire (2004)
        """
        mmin = cmag[0]
        mmax = np.max(magnitude)
        if mmax > np.max(cmag):
            cmag = np.hstack([cmag, mmax + dmag])
        target_mag = (cmag[:-1] + cmag[1:]) / 2.
        nyear = end_year - cyear + 1.
        beta = bvalue * np.log(10.)
        rate_mmin = nvalue * np.sum(np.exp(-beta * target_mag)) /\
            np.sum(nyear * np.exp(-beta * target_mag))
        return np.log10(rate_mmin) + bvalue * mmin

    def _weighted_mean(self, parameters, neq):
        '''Simple weighted mean'''
        weight = neq.astype(float) / np.sum(neq)
        if np.shape(parameters)[0] != weight.size:
            raise ValueError('Parameter vector not same shape as weights')
        else:
            average_value = np.zeros(np.shape(parameters)[1], dtype=float)
            for iloc in range(0, np.shape(parameters)[1]):
                average_value[iloc] = np.sum(parameters[:, iloc] * weight)
        return average_value

    def _harmonic_mean(self, parameters, neq):
        '''Harmonic mean'''
        weight = neq.astype(float) / np.sum(neq)
        if np.shape(parameters)[0] != weight.size:
            raise ValueError('Parameter vector not same shape as weights')

        average_value = np.zeros(np.shape(parameters)[1], dtype=float)
        for iloc in range(0, np.shape(parameters)[1]):
            average_value[iloc] = 1. / np.sum(
                (weight * (1. / parameters[:, iloc])))
        return average_value
