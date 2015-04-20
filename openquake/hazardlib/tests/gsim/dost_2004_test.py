# The Hazard Library
# Copyright (C) 2015, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from openquake.hazardlib.gsim.dost_2004 import (DostEtAl2004,
                                                DostEtAl2004BommerAdaptation)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class DostEtAl2004TestCase(BaseGSIMTestCase):
    GSIM_CLASS = DostEtAl2004

    # Tables generated from current implementation - CIRCULAR TEST!

    def test_mean(self):
        self.check('DOST2004/DOST2004_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('DOST2004/DOST2004_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class DostEtAl2004BommerAdjustedTestCase(BaseGSIMTestCase):
    GSIM_CLASS = DostEtAl2004BommerAdaptation

    # Tables generated from current implementation - CIRCULAR TEST!

    def test_mean(self):
        self.check('DOST2004/DOST2004_ADJUSTED_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('DOST2004/DOST2004_ADJUSTED_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('DOST2004/DOST2004_ADJUSTED_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('DOST2004/DOST2004_ADJUSTED_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
