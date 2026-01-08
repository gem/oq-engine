# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
Test data generated using the Excel file published as supplementary material
with the V/H Earthquake Spectra paper from the same authors:
https://journals.sagepub.com/doi/suppl/10.1193/100614eqs151m

# Take note of the following bug in the 'HOR Spectrum (PSA)' Sheet of
# the supplemental Excel file:
#   * Formula error in cell A62 and Column L, i.e. the formula for f_sed
#     (Basin Response Term) should refer to the Sj flag instead of the Sji flag
#   * A1100 should refer to Z2.5 (VS30=1100) in Cell B48, not constant in A48.
"""
import pytest
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import (
    CampbellBozorgnia2014, CampbellBozorgnia2019, coeffs_high, coeffs_low)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class CampbellBozorgnia2014TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2014
    MEAN_FILE = 'CB14/CB2014%s_MEAN.csv'
    STD_INTRA_FILE = 'CB14/CB2014%s_STD_INTRA.csv'
    STD_INTER_FILE = 'CB14/CB2014%s_STD_INTER.csv'
    STD_TOTAL_FILE = 'CB14/CB2014%s_STD_TOTAL.csv'


class CampbellBozorgnia2019TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2019
    MEAN_FILE = 'CB19/CB2019%s_MEAN.csv'
    STD_INTRA_FILE = 'CB19/CB2019%s_STD_INTRA.csv'
    STD_INTER_FILE = 'CB19/CB2019%s_STD_INTER.csv'
    STD_TOTAL_FILE = 'CB19/CB2019%s_STD_TOTAL.csv'


coeffs = {'': None, '_HIGHQ': coeffs_high, '_LOWQ': coeffs_low}
params = [(cls, name, SJ)
          for name in ['', '_HIGHQ', '_LOWQ'] for SJ in [0, 1]
          for cls in [CampbellBozorgnia2014TestCase, CampbellBozorgnia2019TestCase]]
@pytest.mark.parametrize('cls, name, SJ', params)
def test_all(cls, name, SJ):
    self = cls()
    tag = name + ('_JAPAN' if SJ else '')
    self.check(self.MEAN_FILE % tag,
               self.STD_INTRA_FILE % tag,
               self.STD_INTER_FILE % tag,
               self.STD_TOTAL_FILE % tag,
               max_discrep_percentage=0.1,
               coeffs=coeffs[name], SJ=SJ)
