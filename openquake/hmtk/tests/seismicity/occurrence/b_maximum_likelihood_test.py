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
Unit tests for the maximum likelihood algorithm class which computes
seismicity occurrence parameters.
"""

import unittest
import numpy as np

from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.occurrence.b_maximum_likelihood import BMaxLikelihood


class BMaxLikelihoodTestCase(unittest.TestCase):

    def setUp(self):
        """
        This generates a catalogue to be used for the regression.
        """
        # Generates a data set assuming b=1
        self.dmag = 0.1
        mext = np.arange(4.0, 7.01, 0.1)
        self.mval = mext[0:-1] + self.dmag / 2.0
        self.bval = 1.0
        numobs = np.flipud(np.diff(np.flipud(10.0**(-self.bval*mext+7.0))))

        # Define completeness window
        numobs[0:6] *= 10
        numobs[6:13] *= 20
        numobs[13:22] *= 50
        numobs[22:] *= 100

        compl = np.array([[1900, 1950, 1980, 1990], [6.34, 5.44, 4.74, 3.0]])
        print(compl)
        self.compl = compl.transpose()
        print('completeness')
        print(self.compl)
        print(self.compl.shape)

        numobs = np.around(numobs)
        print(numobs)

        magnitude = np.zeros(int(np.sum(numobs)))
        year = np.zeros(int(np.sum(numobs))) * 1999

        lidx = 0
        for mag, nobs in zip(self.mval, numobs):
            uidx = int(lidx+nobs)
            magnitude[lidx:uidx] = mag + 0.01
            year_low = compl[0, np.min(np.nonzero(compl[1, :] < mag)[0])]
            year[lidx:uidx] = (year_low + np.random.rand(uidx-lidx) *
                               (2000-year_low))
            print('%.2f %.0f %.0f' % (mag, np.min(year[lidx:uidx]),
                                      np.max(year[lidx:uidx])))
            lidx = uidx

        self.catalogue = Catalogue.make_from_dict(
            {'magnitude': magnitude, 'year': year})
        self.b_ml = BMaxLikelihood()
        self.config = {'Average Type': 'Weighted'}

    def test_b_maximum_likelihood(self):
        """
        Tests that the computed b value corresponds to the same value
        used to generate the test data set
        """
        bval, sigma_b, aval, sigma_a = self.b_ml.calculate(
            self.catalogue, self.config, self.compl)
        self.assertAlmostEqual(self.bval, bval, 1)

    def test_b_maximum_likelihood_raise_error(self):
        completeness_table = np.zeros((10, 2))
        catalogue = {'year': [1900]}
        config = {'Average Type' : ['fake']}
        self.assertRaises(ValueError, self.b_ml.calculate, catalogue,
                config, completeness_table)

    def test_b_maximum_likelihood_average_parameters_raise_error(self):
        num = 4
        gr_pars = np.zeros((10, num))
        neq = np.zeros((num))
        self.assertRaises(ValueError, self.b_ml._average_parameters,
                          gr_pars, neq)

    def test_b_maximum_likelihood_average_parameters_use_harmonic(self):
        num = 4
        gr_pars = np.ones((num, 10))
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
