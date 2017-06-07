# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
from openquake.hazardlib.gsim.youngs_1997 import (
    YoungsEtAl1997SInter,
    YoungsEtAl1997SSlab,
    YoungsEtAl1997GSCSSlabBest,
    YoungsEtAl1997GSCSSlabUpperLimit,
    YoungsEtAl1997GSCSSlabLowerLimit,
    YoungsEtAl1997SInterNSHMP2008
)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated from OpenSHA implementation.
# for the GSC version, test data have been generated from the hazardlib
# implementation. Indipendent test data from original author are needed
# for more robust testing


class YoungsEtAl1997SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = YoungsEtAl1997SInter

    def test_mean(self):
        self.check('YOUNGS97/Y97SInter_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('YOUNGS97/Y97SInter_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class YoungsEtAl1997SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = YoungsEtAl1997SSlab

    def test_mean(self):
        self.check('YOUNGS97/Y97SSlab_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('YOUNGS97/Y97SSlab_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class YoungsEtAl1997GSCSSlabBestTestCase(BaseGSIMTestCase):
    GSIM_CLASS = YoungsEtAl1997GSCSSlabBest

    def test_mean(self):
        self.check('YOUNGS97/YoungsEtAl1997GSCSSlabBest_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('YOUNGS97/Y97SSlab_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class YoungsEtAl1997GSCSSlabUpperLimitTestCase(BaseGSIMTestCase):
    GSIM_CLASS = YoungsEtAl1997GSCSSlabUpperLimit

    def test_mean(self):
        self.check('YOUNGS97/YoungsEtAl1997GSCSSlabUpperLimit_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('YOUNGS97/Y97SSlab_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class YoungsEtAl1997GSCSSlabLowerLimitTestCase(BaseGSIMTestCase):
    GSIM_CLASS = YoungsEtAl1997GSCSSlabLowerLimit

    def test_mean(self):
        self.check('YOUNGS97/YoungsEtAl1997GSCSSlabLowerLimit_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('YOUNGS97/Y97SSlab_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class YoungsEtAl1997SInterNSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = YoungsEtAl1997SInterNSHMP2008

    def test_mean(self):
        self.check('YOUNGS97/Y97SInterNSHMP2008_MEAN.csv',
                   max_discrep_percentage=2.5)

    def test_std_total(self):
        self.check('YOUNGS97/Y97SInterNSHMP2008_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
