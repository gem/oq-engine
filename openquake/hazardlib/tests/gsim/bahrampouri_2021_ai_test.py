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

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.bahrampouri_2021 import BahrampouriEtAl2021Asc
from openquake.hazardlib.gsim.bahrampouri_2021 import BahrampouriEtAl2021SInter
from openquake.hazardlib.gsim.bahrampouri_2021 import BahrampouriEtAl2021SSlab

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1


class BahrampouriEtAl2021IAAscTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BahrampouriEtAl2021Asc
    MEAN_FILE = "BMG20/BMG20_AI_ASC_mean.csv"
    TOTAL_FILE = "BMG20/BMG20_AI_ASC_TOTAL.csv"
    INTRA_FILE = "BMG20/BMG20_AI_ASC_INTRA.csv"

    def test_all(self):
        self.check( self.MEAN_FILE, self.TOTAL_FILE,self.INTRA_FILE,  max_discrep_percentage=MEAN_DISCREP)

class BahrampouriEtAl2021IAInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BahrampouriEtAl2021SInter

    MEAN_FILE = "BMG20/BMG20_AI_SInter_mean.csv"
    TOTAL_FILE = "BMG20/BMG20_AI_SInter_TOTAL.csv"
    INTRA_FILE = "BMG20/BMG20_AI_SInter_INTRA.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.TOTAL_FILE, self.INTRA_FILE, max_discrep_percentage=MEAN_DISCREP)

class BahrampouriEtAl2021IATestSlabCase(BaseGSIMTestCase):
    GSIM_CLASS = BahrampouriEtAl2021SSlab

    MEAN_FILE = "BMG20/BMG20_AI_SSlab_mean.csv"
    TOTAL_FILE = "BMG20/BMG20_AI_SSlab_TOTAL.csv"
    INTRA_FILE = "BMG20/BMG20_AI_SSlab_INTRA.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.TOTAL_FILE,self.INTRA_FILE,
                   max_discrep_percentage=MEAN_DISCREP)
