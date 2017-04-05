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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-

"""
Unit tests for the Aki maximum likelihood algorithm class which computes
seismicity occurrence parameters.
"""

import unittest
import numpy as np

from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.occurrence.aki_maximum_likelihood import AkiMaxLikelihood


class AkiMaximumLikelihoodTestCase(unittest.TestCase):

    def setUp(self):
        """
        This generates a minimum data-set to be used for the regression.
        """
        # Test A: Generates a data set assuming b=1 and N(m=4.0)=10.0 events
        self.dmag = 0.1
        mext = np.arange(4.0, 7.01, 0.1)
        self.mval = mext[0:-1] + self.dmag / 2.0
        self.bval = 1.0
        self.numobs = np.flipud(
            np.diff(np.flipud(10.0 ** (-self.bval * mext + 8.0))))
        # Test B: Generate a completely artificial catalogue using the
        # Gutenberg-Richter distribution defined above
        numobs = np.around(self.numobs)
        size = int(np.sum(self.numobs))
        magnitude = np.zeros(size)
        lidx = 0
        for mag, nobs in zip(self.mval, numobs):
            uidx = int(lidx+nobs)
            magnitude[lidx:uidx] = mag + 0.01
            lidx = uidx
        year = np.ones(size) * 1999
        self.catalogue = Catalogue.make_from_dict(
            {'magnitude': magnitude, 'year': year})
        # Create the seismicity occurrence calculator
        self.aki_ml = AkiMaxLikelihood()

    def test_aki_maximum_likelihood_A(self):
        """
        Tests that the computed b value corresponds to the same value
        used to generate the test data set
        """
        bval, sigma_b = self.aki_ml._aki_ml(self.mval, self.numobs)
        self.assertAlmostEqual(self.bval, bval, 2)

    def test_aki_maximum_likelihood_B(self):
        """
        Tests that the computed b value corresponds to the same value
        used to generate the test data set
        """
        bval, sigma_b = self.aki_ml.calculate(self.catalogue)
        self.assertAlmostEqual(self.bval, bval, 2)
