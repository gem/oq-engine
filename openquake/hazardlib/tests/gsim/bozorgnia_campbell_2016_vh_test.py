# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
with the V/H Earthquake Spectra paper:
https://journals.sagepub.com/doi/suppl/10.1193/100614eqs151m

# Take note of the following bug in the 'HOR Spectrum (PSA)' Sheet of
# the supplemental Excel file:
#   * Formula error in Column L, i.e. the formula for f_sed
#     (Basin Response Term) should refer to the Sj flag instead of the Sji flag
#   * A1100 should refer to Z2.5 (VS30=1100) in Cell B48, not constant in A48.
"""

from openquake.hazardlib.gsim.bozorgnia_campbell_2016_vh import (
    BozorgniaCampbell2016VH,
    BozorgniaCampbell2016HighQVH,
    BozorgniaCampbell2016LowQVH,
    BozorgniaCampbell2016AveQJapanSiteVH,
    BozorgniaCampbell2016HighQJapanSiteVH,
    BozorgniaCampbell2016LowQJapanSiteVH)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class BozorgniaCampbell2016VHTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BozorgniaCampbell2016VH
    MEAN_FILE = 'BC15b/BC15b_GLOBAL_MEAN.csv'
    STD_INTRA_FILE = 'BC15b/BC15b_GLOBAL_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15b/BC15b_GLOBAL_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15b/BC15b_GLOBAL_STD_TOTAL.csv'

    def test_all(self):
        self.check(self.MEAN_FILE,
                   self.STD_INTRA_FILE,
                   self.STD_INTER_FILE,
                   self.STD_TOTAL_FILE,
                   max_discrep_percentage=0.1)


class BozorgniaCampbell2016HighQVHTestCase(BozorgniaCampbell2016VHTestCase):
    GSIM_CLASS = BozorgniaCampbell2016HighQVH
    MEAN_FILE = 'BC15b/BC15b_HIGHQ_MEAN.csv'
    STD_INTRA_FILE = 'BC15b/BC15b_HIGHQ_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15b/BC15b_HIGHQ_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15b/BC15b_HIGHQ_STD_TOTAL.csv'


class BozorgniaCampbell2016LowQVHTestCase(BozorgniaCampbell2016VHTestCase):
    GSIM_CLASS = BozorgniaCampbell2016LowQVH
    MEAN_FILE = 'BC15b/BC15b_LOWQ_MEAN.csv'
    STD_INTRA_FILE = 'BC15b/BC15b_LOWQ_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15b/BC15b_LOWQ_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15b/BC15b_LOWQ_STD_TOTAL.csv'


class BozorgniaCampbell2016AveQJapanSiteVHTestCase(
        BozorgniaCampbell2016VHTestCase):
    GSIM_CLASS = BozorgniaCampbell2016AveQJapanSiteVH
    MEAN_FILE = 'BC15b/BC15b_AVEQ_JPN_MEAN.csv'
    STD_INTRA_FILE = 'BC15b/BC15b_AVEQ_JPN_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15b/BC15b_AVEQ_JPN_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15b/BC15b_AVEQ_JPN_STD_TOTAL.csv'


class BozorgniaCampbell2016HighQJapanSiteVHTestCase(
        BozorgniaCampbell2016VHTestCase):
    GSIM_CLASS = BozorgniaCampbell2016HighQJapanSiteVH
    MEAN_FILE = 'BC15b/BC15b_HIGHQ_JPN_MEAN.csv'
    STD_INTRA_FILE = 'BC15b/BC15b_HIGHQ_JPN_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15b/BC15b_HIGHQ_JPN_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15b/BC15b_HIGHQ_JPN_STD_TOTAL.csv'


class BozorgniaCampbell2016LowQJapanSiteVHTestCase(
        BozorgniaCampbell2016VHTestCase):
    GSIM_CLASS = BozorgniaCampbell2016LowQJapanSiteVH
    MEAN_FILE = 'BC15b/BC15b_LOWQ_JPN_MEAN.csv'
    STD_INTRA_FILE = 'BC15b/BC15b_LOWQ_JPN_STD_INTRA.csv'
    STD_INTER_FILE = 'BC15b/BC15b_LOWQ_JPN_STD_INTER.csv'
    STD_TOTAL_FILE = 'BC15b/BC15b_LOWQ_JPN_STD_TOTAL.csv'
