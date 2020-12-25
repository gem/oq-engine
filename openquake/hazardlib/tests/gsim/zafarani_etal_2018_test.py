# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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

from openquake.hazardlib.gsim.zafarani_etal_2018 import (ZafaraniEtAl2018)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

class ZafaraniEtAl2018TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZafaraniEtAl2018
    MEAN_FILE = 'ZAFARANI18/Zafarani_etal_2018_MEAN.csv'
    STD_TOTAL_FILE = 'ZAFARANI18/Zafarani_etal_2018_TOTAL.csv'
    STD_INTER_FILE = 'ZAFARANI18/Zafarani_etal_2018_INTER.csv'
    STD_INTRA_FILE = 'ZAFARANI18/Zafarani_etal_2018_INTRA.csv'


    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage = 0.1)
    def test_std_total(self):
        self.check(self.STD_TOTAL_FILE,
                   max_discrep_percentage = 0.1)

    def test_std_inter(self):
        self.check(self.STD_INTER_FILE,
                   max_discrep_percentage = 0.1)

    def test_std_intra(self):
        self.check(self.STD_INTRA_FILE,
                   max_discrep_percentage = 0.1)
