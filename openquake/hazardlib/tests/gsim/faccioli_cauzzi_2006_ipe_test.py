# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Implements the tests for Bindi et al. (2011) GMPE for macroseismic intensity

Test data generated from source code provided by Philippe Roth
"""
from openquake.hazardlib.gsim.faccioli_cauzzi_2006 import FaccioliCauzzi2006
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class FaccioliCauzzi2006TestCase(BaseGSIMTestCase):
    GSIM_CLASS = FaccioliCauzzi2006
    # File containing the results for the Mean
    MEAN_FILE = "faccioli_cauzzi_2006/FaccioliCauzzi2006_mean.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "faccioli_cauzzi_2006/FaccioliCauzzi2006_stDev.csv"

    def test_all(self):
        self.check(self.MEAN_FILE,
                   self.STD_FILE,
                   max_discrep_percentage=MEAN_DISCREP,
                   std_discrep_percentage=STDDEV_DISCREP)
