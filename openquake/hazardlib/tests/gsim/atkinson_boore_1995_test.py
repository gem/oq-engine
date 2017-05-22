# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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

from openquake.hazardlib.gsim.atkinson_boore_1995 import (
    AtkinsonBoore1995GSCBest,
    AtkinsonBoore1995GSCLowerLimit,
    AtkinsonBoore1995GSCUpperLimit
)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data provided by Geological Survey of Canada


class AtkinsonBoore1995GSCBestTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AtkinsonBoore1995GSCBest


    def test_mean(self):
        self.check('AB95/AB95GSCBest_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AB95/AB95GSCBest_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class AtkinsonBoore1995GSCLowerLimitTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AtkinsonBoore1995GSCLowerLimit


    def test_mean(self):
        self.check('AB95/AB95GSCLowerLimit_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AB95/AB95GSCLowerLimit_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class AtkinsonBoore1995GSCUpperLimitTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AtkinsonBoore1995GSCUpperLimit


    def test_mean(self):
        self.check('AB95/AB95GSCUpperLimit_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AB95/AB95GSCLowerLimit_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
