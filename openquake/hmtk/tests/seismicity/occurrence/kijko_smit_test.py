# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2018 GEM Foundation, G. Weatherill, M. Pagani,
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
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Unit tests for the Kijko and Smith (2012) algorithm which computes
seismicity occurrence parameters.
"""

import unittest
import numpy as np

from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.occurrence.kijko_smit import KijkoSmit


class KijkoSmitTest(unittest.TestCase):

    def setUp(self):
        """
        This generates a catalogue to be used for the regression.
        """
        # Generates a data set assuming b=1
        self.dmag = 0.1
        mext = np.arange(4.0, 7.01, 0.1)
        self.mval = mext[0:-1] + self.dmag / 2.0
        self.bval = 1.0
        numobs = np.flipud(np.diff(np.flipud(10.0**(-self.bval * mext + 7.0))))

        # Define completeness window
        numobs[0:6] *= 10
        numobs[6:13] *= 20
        numobs[13:22] *= 50
        numobs[22:] *= 100

        compl = np.array([[1900, 1950, 1980, 1990], [6.34, 5.44, 4.74, 3.0]])
        self.compl = np.flipud(compl.transpose())
        numobs = np.around(numobs)

        magnitude = np.zeros(int(np.sum(numobs)))
        year = np.zeros(int(np.sum(numobs))) * 1999

        lidx = 0
        for mag, nobs in zip(self.mval, numobs):
            uidx = int(lidx + nobs)
            magnitude[lidx:uidx] = mag + 0.01
            year_low = compl[0, np.min(np.nonzero(compl[1, :] < mag)[0])]
            year[lidx:uidx] = (year_low + np.random.rand(uidx - lidx) *
                               (2000 - year_low))
            lidx = uidx

        self.catalogue = Catalogue.make_from_dict(
            {'magnitude': magnitude, 'year': year})
        self.ks_ml = KijkoSmit()
        self.config = {'Average Type': 'Weighted'}

    def test_kijko_smit_maximum_likelihood(self):
        """
        Tests that the computed b value corresponds to the same value
        used to generate the test data set
        """
        bval, sigma_b, aval, sigma_a = self.ks_ml.calculate(
            self.catalogue, self.config, self.compl)
        print(bval, sigma_b)
        self.assertAlmostEqual(self.bval, bval, 1)

    def test_kijko_smit_set_reference_magnitude(self):
        completeness_table = np.array([[1900, 1.0]])
        catalogue = Catalogue.make_from_dict(
            {'magnitude': np.array([5.0, 6.0]),
             'year': np.array([2000, 2000])})
        config = {'reference_magnitude': 0.0}
        self.ks_ml.calculate(catalogue, config, completeness_table)
