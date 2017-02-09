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

"""
Implements the comprehensive test suite for the Campbell & Bozorgnia (2014)
NGA-West2 GMPE
Tests generated using a modified form of the implementation from Yue Hua,
Stanford University. The original implementation can be found at this link:
http://web.stanford.edu/~bakerjw/GMPEs.html
"""

from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import (
    CampbellBozorgnia2014,
    CampbellBozorgnia2014HighQ,
    CampbellBozorgnia2014LowQ,
    CampbellBozorgnia2014JapanSite,
    CampbellBozorgnia2014HighQJapanSite,
    CampbellBozorgnia2014LowQJapanSite)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class CampbellBozorgnia2014TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2014
    MEAN_FILE = 'CB14/CB2014_MEAN.csv'
    STD_INTRA_FILE = 'CB14/CB2014_STD_INTRA.csv'
    STD_INTER_FILE = 'CB14/CB2014_STD_INTER.csv'
    STD_TOTAL_FILE = 'CB14/CB2014_STD_TOTAL.csv'

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check(self.STD_INTRA_FILE,
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check(self.STD_INTER_FILE,
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.STD_TOTAL_FILE,
                   max_discrep_percentage=0.1)


class CampbellBozorgnia2014HighQTestCase(CampbellBozorgnia2014TestCase):
    GSIM_CLASS = CampbellBozorgnia2014HighQ
    MEAN_FILE = 'CB14/CB2014_HIGHQ_MEAN.csv'
    STD_INTRA_FILE = 'CB14/CB2014_HIGHQ_STD_INTRA.csv'
    STD_INTER_FILE = 'CB14/CB2014_HIGHQ_STD_INTER.csv'
    STD_TOTAL_FILE = 'CB14/CB2014_HIGHQ_STD_TOTAL.csv'


class CampbellBozorgnia2014LowQTestCase(CampbellBozorgnia2014TestCase):
    GSIM_CLASS = CampbellBozorgnia2014LowQ
    MEAN_FILE = 'CB14/CB2014_LOWQ_MEAN.csv'
    STD_INTRA_FILE = 'CB14/CB2014_LOWQ_STD_INTRA.csv'
    STD_INTER_FILE = 'CB14/CB2014_LOWQ_STD_INTER.csv'
    STD_TOTAL_FILE = 'CB14/CB2014_LOWQ_STD_TOTAL.csv'


class CampbellBozorgnia2014JapanSiteTestCase(CampbellBozorgnia2014TestCase):
    GSIM_CLASS = CampbellBozorgnia2014JapanSite
    MEAN_FILE = 'CB14/CB2014_JAPAN_MEAN.csv'
    STD_INTRA_FILE = 'CB14/CB2014_JAPAN_STD_INTRA.csv'
    STD_INTER_FILE = 'CB14/CB2014_JAPAN_STD_INTER.csv'
    STD_TOTAL_FILE = 'CB14/CB2014_JAPAN_STD_TOTAL.csv'


class CampbellBozorgnia2014HighQJapanSiteTestCase(
        CampbellBozorgnia2014TestCase):
    GSIM_CLASS = CampbellBozorgnia2014HighQJapanSite
    MEAN_FILE = 'CB14/CB2014_HIGHQ_JAPAN_MEAN.csv'
    STD_INTRA_FILE = 'CB14/CB2014_HIGHQ_JAPAN_STD_INTRA.csv'
    STD_INTER_FILE = 'CB14/CB2014_HIGHQ_JAPAN_STD_INTER.csv'
    STD_TOTAL_FILE = 'CB14/CB2014_HIGHQ_JAPAN_STD_TOTAL.csv'


class CampbellBozorgnia2014LowQJapanSiteTestCase(
        CampbellBozorgnia2014TestCase):
    GSIM_CLASS = CampbellBozorgnia2014LowQJapanSite
    MEAN_FILE = 'CB14/CB2014_LOWQ_JAPAN_MEAN.csv'
    STD_INTRA_FILE = 'CB14/CB2014_LOWQ_JAPAN_STD_INTRA.csv'
    STD_INTER_FILE = 'CB14/CB2014_LOWQ_JAPAN_STD_INTER.csv'
    STD_TOTAL_FILE = 'CB14/CB2014_LOWQ_JAPAN_STD_TOTAL.csv'
