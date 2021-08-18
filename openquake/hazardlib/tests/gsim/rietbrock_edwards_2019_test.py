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
Implements the test cases for the Rietbrock and Edwards (2019) GMPE.
Test data created using the Fortran implementation provided by
Ben Edwards
"""

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.rietbrock_edwards_2019 import \
    RietbrockEdwards2019Mean, RietbrockEdwards2019Low, RietbrockEdwards2019Up

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.08


class RietbrockEdwards2019LowTestCase(BaseGSIMTestCase):
    GSIM_CLASS = RietbrockEdwards2019Low

    # File containing the mean data
    MEAN_FILE = "RIET2019/low.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=MEAN_DISCREP)


class RietbrockEdwards2019MeanTestCase(BaseGSIMTestCase):
    GSIM_CLASS = RietbrockEdwards2019Mean

    # File containing the mean data
    MEAN_FILE = "RIET2019/mean.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=MEAN_DISCREP)


class RietbrockEdwards2019UpTestCase(BaseGSIMTestCase):
    GSIM_CLASS = RietbrockEdwards2019Up

    # File containing the mean data
    MEAN_FILE = "RIET2019/up.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=MEAN_DISCREP)
