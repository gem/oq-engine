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

from openquake.hazardlib.gsim.sedaghati_pezeshk_2017 import (SedaghatiPezeshk2017)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

class SedaghatiPezeshk2017TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SedaghatiPezeshk2017
    MEAN_FILE = 'SEDAGHATI17/SEDAGHATI_PEZESHK_2017_MEAN.csv'
    STD_TOTAL_FILE = 'SEDAGHATI17/SEDAGHATI_PEZESHK_2017_TOTAL.csv'
    STD_INTER_FILE = 'SEDAGHATI17/SEDAGHATI_PEZESHK_2017_INTER.csv'
    STD_INTRA_FILE = 'SEDAGHATI17/SEDAGHATI_PEZESHK_2017_INTRA.csv'


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
