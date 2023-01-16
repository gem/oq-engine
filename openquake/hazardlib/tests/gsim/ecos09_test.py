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
Implements the tests for ECOS (2009) GMPE for macroseismic intensity

Test data generated from source code provided by Philippe Roth
"""
from openquake.hazardlib.gsim.ecos_2009 import ECOS2009, ECOS2009Highest
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class ECOS2009TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ECOS2009
    # File containing the results for the Mean
    MEAN_FILE = "ecos_2009/ecos09_mean.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "ecos_2009/ecos09_stDev.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=MEAN_DISCREP,
                   std_discrep_percentage=STDDEV_DISCREP)


class ECOS2009HighestTestCase(ECOS2009TestCase):
    GSIM_CLASS = ECOS2009Highest
    # File containing the results for the Mean
    MEAN_FILE = "ecos_2009/ecos09_H_mean.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "ecos_2009/ecos09_H_stDev.csv"
