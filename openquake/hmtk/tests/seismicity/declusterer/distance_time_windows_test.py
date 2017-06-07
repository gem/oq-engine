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

import unittest
import os
import numpy as np

from openquake.hmtk.seismicity.declusterer.distance_time_windows import (
    GardnerKnopoffWindow, GruenthalWindow, UhrhammerWindow)

class CsvCatalogueParserTestCase(unittest.TestCase):
    """ Unit tests for the csv Catalogue Parser Class"""
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

    def setUp(self):
        self.gardner_knopoff_window = GardnerKnopoffWindow()
        self.gruenthal_window = GruenthalWindow()
        self.uhrhammer_window = UhrhammerWindow()

    def test_gardner_knopoff_window(self):
        """
        Test the Gardner and Knopoff Distance-Time window
        """
        mag = np.array([5.0,6.6])
        sw_space, sw_time = self.gardner_knopoff_window.calc(mag)
        self.assertAlmostEqual(sw_space[0], 39.99447, places=5)
        self.assertAlmostEqual(sw_space[1], 63.10736, places=5)
        self.assertAlmostEqual(sw_time[0], 143.71430/364.75, places=5)
        self.assertAlmostEqual(sw_time[1], 891.45618/364.75, places=5)

    def test_gruenthal_window(self):
        """
        Test the Gruenthal Distance-Time window
        """
        mag = np.array([5.0,6.6])
        sw_space, sw_time = self.gruenthal_window.calc(mag)
        #self.assertAlmostEqual(sw_space[0], 39.99447, places=5)
        #self.assertAlmostEqual(sw_time[0], 143.71430/364.75, places=5)
        #self.assertAlmostEqual(sw_space[1], 63.10736, places=5)
        #self.assertAlmostEqual(sw_time[1], 891.45618/364.75, places=5)

    def test_uhrhammer_window(self):
        mag = np.array([5.0,6.6])
        sw_space, sw_time = self.uhrhammer_window.calc(mag)
        #self.assertAlmostEqual(sw_space[0], 39.99447, places=5)
        #self.assertAlmostEqual(sw_time[0], 143.71430/364.75, places=5)
        #self.assertAlmostEqual(sw_space[1], 63.10736, places=5)
        #self.assertAlmostEqual(sw_time[1], 891.45618/364.75, places=5)