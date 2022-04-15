# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2022, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import unittest
import numpy as np
from openquake.hazardlib.gsim_lt import GsimLogicTree

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'gsim_lt')
aac = np.testing.assert_allclose


class TestCaseSimple(unittest.TestCase):

    def setUp(self):
        self.lt = GsimLogicTree(os.path.join(DATA_PATH, 'gmcLT_simple.xml'))

    def test_get_weights(self):
        wei = self.lt.get_weights('Active Shallow Crust')
        expected = [0.3, 0.7]
        aac(wei, expected)


class TestCaseWithApproach(unittest.TestCase):

    def setUp(self):
        name = "gmcLT_with_approach.xml"
        self.lt = GsimLogicTree(os.path.join(DATA_PATH, name))

    def test_get_weights(self):
        app = 'multimodel'
        wei = self.lt.get_weights('Active Shallow Crust', approach=app)
        expected = [1.0]
        aac(wei, expected)

        app = 'backbone'
        wei = self.lt.get_weights('Active Shallow Crust', approach=app)
        expected = [0.1, 0.9]
        aac(wei, expected)
