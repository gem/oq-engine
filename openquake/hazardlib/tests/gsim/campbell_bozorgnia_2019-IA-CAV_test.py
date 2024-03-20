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

from openquake.hazardlib.gsim.campbell_bozorgnia_2019_IA_CAV import (
    CampbellBozorgnia2019_IA_CAV,
)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class CampbellBozorgnia2014_IA_CAVTestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2019_IA_CAV
    MEAN_FILE = 'CB19/CB2019_MEAN.csv'


    def test_all(self):
        self.check(self.MEAN_FILE,
                   self.STD_INTRA_FILE,
                   self.STD_INTER_FILE,
                   self.STD_TOTAL_FILE,
                   max_discrep_percentage=0.1)



