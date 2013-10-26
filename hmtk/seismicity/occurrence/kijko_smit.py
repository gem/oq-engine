# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2013, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
# 
# The software Hazard Modeller's Toolkit (hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
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
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.


import numpy as np
from hmtk.seismicity.occurrence.base import (
    SeismicityOccurrence, OCCURRENCE_METHODS)
from hmtk.seismicity.occurrence.utils import input_checks, recurrence_table
from hmtk.seismicity.occurrence.aki_maximum_likelihood import AkiMaxLikelihood


@OCCURRENCE_METHODS.add(
    'calculate',
    reference_magnitude=0.0,
    magnitude_interval=0.1)
class KijkoSmit(SeismicityOccurrence):
    """
    Class to Implement the Kijko & Smit (2012) algorithm for estimation
    of a- and b-value
    """
    def calculate(self, catalogue, config, completeness=None):
        """
        Main function to calculate the a- and b-value
        """
        # Input checks
        cmag, ctime, ref_mag, dmag, config = input_checks(catalogue,
                                                          config,
                                                          completeness)
        ival = 0
        mag_eq_tolerance = 1E-5
        number_intervals = np.shape(ctime)[0]
        b_est = np.zeros(number_intervals, dtype=float)
        neq = np.zeros(number_intervals, dtype=float)
        nyr = np.zeros(number_intervals, dtype=float)

        for ival in range(0, number_intervals):
            id0 = np.abs(ctime - ctime[ival]) < mag_eq_tolerance
            m_c = np.min(cmag[id0])
            if ival == number_intervals - 1:
                id1 = np.logical_and(catalogue.data['year'] >= ctime[ival],
                    catalogue.data['magnitude'] >= (m_c - mag_eq_tolerance))
            else:
                id1 = np.logical_and(catalogue.data['year'] >= ctime[ival],
                                     catalogue.data['year'] < ctime[ival + 1])
                id1 = np.logical_and(id1,
                    catalogue.data['magnitude'] >= (m_c - mag_eq_tolerance))

#        while ival < number_intervals:
#            id0 = np.abs(ctime - ctime[ival]) < mag_eq_tolerance
#            m_c = np.min(cmag[id0])
#            # Find events later than cut-off year, and with magnitude
#            # greater than or equal to the corresponding completeness magnitude.
#            # m_c - mag_eq_tolerance is required to correct floating point
#            # differences.
#            id1 = np.logical_and(catalogue['year'] >= ctime[ival],
#                catalogue['magnitude'] >= (m_c - mag_eq_tolerance))
            nyr[ival] = np.float(np.max(catalogue.data['year'][id1]) -
                                 np.min(catalogue.data['year'][id1]) + 1)
            neq[ival] = np.sum(id1)
            # Get a- and b- value for the selected events
            temp_rec_table = recurrence_table(catalogue.data['magnitude'][id1],
                                              dmag,
                                              catalogue.data['year'][id1])

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

        if not config['reference_magnitude']:
            aval = np.log10(aval)
            sigma_a = np.log10(sigma_a) - aval
        else:
            sigma_a = sigma_a - aval
        return bval, sigma_b, aval, sigma_a

    def _harmonic_mean(self, parameters, neq):
        """
        Calculates the Harmonic mean of a vector of parameters
        """
        weight = neq.astype(float) / np.sum(neq)
        if np.shape(parameters)[0] != np.shape(weight)[0]:
            raise ValueError('Parameter vector not same shape as weights')
        else:
            average_value = np.zeros(np.shape(parameters)[0], dtype=float)
            id0 = np.logical_not(np.isnan(parameters))
            average_value = 1. / np.sum(weight[id0] / parameters[id0])
        return average_value

    def _calculate_a_value(self, bval, nvalue, nyr, cmag, ref_mag):
        """
        Calculates the rate of events >= ref_mag using the b-value estimator
        and Eq. 10 of Kijko & Smit
        """

        denominator = np.sum(nyr * np.exp(-bval * (cmag - ref_mag)))
        return nvalue / denominator
