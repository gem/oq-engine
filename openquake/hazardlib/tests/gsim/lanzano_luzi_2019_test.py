# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
Implements the tests for the set of GMPE classes included within the GMPE
of Lanzano and Luzi (2019). Test tables were created by an excel spreadsheet
that calculates expected values provided by the original authors.
"""
from openquake.hazardlib.gsim.lanzano_luzi_2019 import (LanzanoLuzi2019shallow,
                                                        LanzanoLuzi2019deep,
                                                        LanzanoLuzi2019shallow_scaled,
                                                        LanzanoLuzi2019deep_scaled)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepancy percentages to be applied to all tests


class LanzanoLuzi2019shallowTestCase(BaseGSIMTestCase):
    """
    Tests the Lanzano and Luzi (2019) GMPE for the case of shallow events.
    """
    GSIM_CLASS = LanzanoLuzi2019shallow
    # File containing the results for the Mean
    MEAN_FILE = "LL19/LanzanoLuzi2019shallow_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "LL19/LanzanoLuzi2019shallow_STD_TOTAL.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=0.1)


class LanzanoLuzi2019deepTestCase(BaseGSIMTestCase):
    """
    Tests the Lanzano and Luzi (2019) GMPE for the case of deep events.
    """
    GSIM_CLASS = LanzanoLuzi2019deep
    MEAN_FILE = "LL19/LanzanoLuzi2019deep_MEAN.csv"
    STD_FILE = "LL19/LanzanoLuzi2019deep_STD_TOTAL.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=0.1)


class LanzanoLuzi2019shallow_scaledTestCase(BaseGSIMTestCase):
    """
    Tests the Lanzano and Luzi (2019) GMPE for the case of shallow events.
    """
    GSIM_CLASS = LanzanoLuzi2019shallow_scaled
    MEAN_FILE = "LL19/LanzanoLuzi2019shallow_scaled_MEAN.csv"

    def test_all(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=0.1)


class LanzanoLuzi2019deep_scaledTestCase(BaseGSIMTestCase):
    """
    Tests the Lanzano and Luzi (2019) GMPE for the case of deep events.
    """
    GSIM_CLASS = LanzanoLuzi2019deep_scaled
    MEAN_FILE = "LL19/LanzanoLuzi2019deep_scaled_MEAN.csv"

    def test_all(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=0.1)
