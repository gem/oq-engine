# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
Test data generated using the Excel file published as supplementary material
with the Earthquake Spectra paper

# Take note of the following bug in the 'VRT Spectrum (PSA)' Sheet of
# the supplemental Excel file:
#   * Formula error in Column L, i.e. the formula for f_sed
#     (Basin Response Term) should refer to the Sj flag instead of the Sji flag
"""

from openquake.hazardlib.gsim.bozorgnia_campbell_2016 import (
    BozorgniaCampbell2016,
    BozorgniaCampbell2016HighQ,
    BozorgniaCampbell2016LowQ,
    BozorgniaCampbell2016AveQJapanSite,
    BozorgniaCampbell2016HighQJapanSite,
    BozorgniaCampbell2016LowQJapanSite)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class BozorgniaCampbell2016TestCase(BaseGSIMTestCase):
    GSIM_CLASS = BozorgniaCampbell2016
    MEAN_FILE = 'BC15/BC15_GLOBAL_MEAN.csv'
    STD_INTRA_FILE = 'BC15/BC15_GLOBAL_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15/BC15_GLOBAL_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15/BC15_GLOBAL_STD_TOTAL.csv'

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


class BozorgniaCampbell2016HighQTestCase(BozorgniaCampbell2016TestCase):
    GSIM_CLASS = BozorgniaCampbell2016HighQ
    MEAN_FILE = 'BC15/BC15_HIGHQ_MEAN.csv'
    STD_INTRA_FILE = 'BC15/BC15_HIGHQ_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15/BC15_HIGHQ_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15/BC15_HIGHQ_STD_TOTAL.csv'


class BozorgniaCampbell2016LowQTestCase(BozorgniaCampbell2016TestCase):
    GSIM_CLASS = BozorgniaCampbell2016LowQ
    MEAN_FILE = 'BC15/BC15_LOWQ_MEAN.csv'
    STD_INTRA_FILE = 'BC15/BC15_LOWQ_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15/BC15_LOWQ_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15/BC15_LOWQ_STD_TOTAL.csv'


class BozorgniaCampbell2016AveQJapanSiteTestCase(
        BozorgniaCampbell2016TestCase):
    GSIM_CLASS = BozorgniaCampbell2016AveQJapanSite
    MEAN_FILE = 'BC15/BC15_AVEQ_JPN_MEAN.csv'
    STD_INTRA_FILE = 'BC15/BC15_AVEQ_JPN_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15/BC15_AVEQ_JPN_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15/BC15_AVEQ_JPN_STD_TOTAL.csv'


class BozorgniaCampbell2016HighQJapanSiteTestCase(
        BozorgniaCampbell2016TestCase):
    GSIM_CLASS = BozorgniaCampbell2016HighQJapanSite
    MEAN_FILE = 'BC15/BC15_HIGHQ_JPN_MEAN.csv'
    STD_INTRA_FILE = 'BC15/BC15_HIGHQ_JPN_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15/BC15_HIGHQ_JPN_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15/BC15_HIGHQ_JPN_STD_TOTAL.csv'


class BozorgniaCampbell2016LowQJapanSiteTestCase(
        BozorgniaCampbell2016TestCase):
    GSIM_CLASS = BozorgniaCampbell2016LowQJapanSite
    MEAN_FILE = 'BC15/BC15_LOWQ_JPN_MEAN.csv'
    STD_INTRA_FILE = 'BC15/BC15_LOWQ_JPN_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15/BC15_LOWQ_JPN_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15/BC15_LOWQ_JPN_STD_TOTAL.csv'
