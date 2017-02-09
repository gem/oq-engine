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

from openquake.hazardlib.gsim.abrahamson_silva_1997 import AbrahamsonSilva1997

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data have been generated from Fortran implementation
# (subroutine getAS in HazFXv.f code) available from
# http://earthquake.usgs.gov/hazards/products/ak/2007/software/

class AbrahamsonSilva1997TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AbrahamsonSilva1997

    def test_mean_ss(self):
        self.check('AS97/AS97_MEAN_SS.csv',
                   max_discrep_percentage=0.2)

    def test_mean_reverse(self):
        self.check('AS97/AS97_MEAN_REVERSE.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AS97/AS97_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
