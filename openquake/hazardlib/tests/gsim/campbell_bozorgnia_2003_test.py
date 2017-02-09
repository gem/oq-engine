# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from openquake.hazardlib.gsim.campbell_bozorgnia_2003 import (
    CampbellBozorgnia2003NSHMP2007
)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated from subroutine getCamp2000 in hazFXv7.f fotran code
# availble from http://earthquake.usgs.gov/hazards/products/ak/2007/software/

class CampbellBozorgnia2003NSHMP2007TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2003NSHMP2007

    def test_mean_ss(self):
        self.check('CB03/CB03_MEAN_SS_NSHMP2007.csv',
                   max_discrep_percentage=0.2)

    def test_mean_normal(self):
        self.check('CB03/CB03_MEAN_NORMAL_NSHMP2007.csv',
                   max_discrep_percentage=0.2)

    def test_mean_thrust(self):
        self.check('CB03/CB03_MEAN_THRUST_NSHMP2007.csv',
                   max_discrep_percentage=0.4)

    def test_mean_reverse(self):
        self.check('CB03/CB03_MEAN_REVERSE_NSHMP2007.csv',
                   max_discrep_percentage=0.3)

    def test_mean_std_total(self):
        self.check('CB03/CB03_STD_TOTAL_NSHMP2007.csv',
                   max_discrep_percentage=0.1)
