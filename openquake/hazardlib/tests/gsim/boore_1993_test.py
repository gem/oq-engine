# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
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
from openquake.hazardlib.gsim.boore_1993 import (
    BooreEtAl1993GSCBest,
    BooreEtAl1993GSCUpperLimit,
    BooreEtAl1993GSCLowerLimit,
)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data provided by Geological Survey of Canada


class BooreEtAl1993GSCBestTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreEtAl1993GSCBest

    def test_mean(self):
        self.check('B93GSC/B93GSCBest_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('B93GSC/B93GSCBest_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class BooreEtAl1993GSCUpperLimitTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreEtAl1993GSCUpperLimit

    def test_mean(self):
        self.check('B93GSC/B93GSCUpperLimit_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('B93GSC/B93GSCUpperLimit_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class BooreEtAl1993GSCLowerLimitTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreEtAl1993GSCLowerLimit

    def test_mean(self):
        self.check('B93GSC/B93GSCLowerLimit_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('B93GSC/B93GSCLowerLimit_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
