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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-

"""
"""

import unittest
import os
import numpy as np

from openquake.hmtk.seismicity.declusterer.dec_afteran import Afteran
from openquake.hmtk.seismicity.declusterer.distance_time_windows import GardnerKnopoffWindow
from openquake.hmtk.parsers.catalogue import CsvCatalogueParser

class AfteranTestCase(unittest.TestCase):
    """
    Unit tests for the Afteran declustering algorithm class.
    """

    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

    def setUp(self):
        """
        Read the sample catalogue
        """
        flnme = 'afteran_test_catalogue.csv'
        filename = os.path.join(self.BASE_DATA_PATH, flnme)
        parser = CsvCatalogueParser(filename)
        self.cat = parser.read_file()
        self.dec = Afteran()

    def test_dec_afteran(self):
        """
        Testing the Afteran algorithm
        """
        config = {
            'time_distance_window': GardnerKnopoffWindow(),
            'time_window': 60.}
        # Instantiate the declusterer and process the sample catalogue
        # self.dec = Afteran()
        print(dir(self.dec))
        vcl, flagvector = self.dec.decluster(self.cat, config)
        print('vcl:', vcl)
        print('flagvector:', flagvector, self.cat.data['flag'])
        self.assertTrue(np.allclose(flagvector, self.cat.data['flag']))

    def test_find_aftershocks(self):
        '''
        Tests the find aftershocks function
        '''
        # Test when aftershocks are in array
        year_dec = np.array([0.10, 0.20, 0.5, 0.60, 0.80, 1.2])
        vsel = np.array([3, 4, 5])
        expected_result = (np.array([False, False, False, True, True, False]),
                           True)
        model_result = self.dec._find_aftershocks(vsel, year_dec, 0.25, 2, 6)
        self.assertTrue(np.all(expected_result[0] == model_result[0]))
        self.assertTrue(model_result[1])

        # Test when no aftershocks are found - reduce window to < 0.1
        expected_result = (
            np.array([False, False, False, False, False, False]), False)
        model_result = self.dec._find_aftershocks(vsel, year_dec, 0.09, 2, 6)
        self.assertTrue(np.all(expected_result[0] == model_result[0]))
        self.assertFalse(model_result[1])

    def test_find_foreshocks(self):
        '''
        Tests the find_foreshocks function
        '''
        # Test when aftershocks are in array
        year_dec = np.array([0.10, 0.40, 0.5, 0.60, 0.80, 1.2])
        vsel = np.array([0, 1])
        expected_result = (
            np.array([False, True, False, False, False, False]), True)
        model_result = self.dec._find_foreshocks(vsel, year_dec, 0.25, 2, 6)
        self.assertTrue(np.all(expected_result[0] == model_result[0]))
        self.assertTrue(model_result[1])

        # Test when no aftershocks are found - reduce window to < 0.1
        expected_result = (
            np.array([False, False, False, False, False, False]), False)
        model_result = self.dec._find_foreshocks(vsel, year_dec, 0.09, 2, 6)
        self.assertTrue(np.all(expected_result[0] == model_result[0]))
        self.assertFalse(model_result[1])
