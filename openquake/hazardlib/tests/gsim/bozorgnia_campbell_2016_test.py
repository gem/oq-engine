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
with the Earthquake Spectra paper

# Take note of the following bug in the 'VRT Spectrum (PSA)' Sheet of
# the supplemental Excel file:
#   * Formula error in Column L, i.e. the formula for f_sed
#     (Basin Response Term) should refer to the Sj flag instead of the Sji flag
"""
import itertools
from openquake.hazardlib.gsim.bozorgnia_campbell_2016 import (
    BozorgniaCampbell2016)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# expected files depending on sgn, SJ
MEAN_FILE = {(0, 0): 'BC15/BC15_GLOBAL_MEAN.csv',
             (0, 1): 'BC15/BC15_AVEQ_JPN_MEAN.csv',
             (1, 0): 'BC15/BC15_HIGHQ_MEAN.csv',
             (1, 1): 'BC15/BC15_HIGHQ_JPN_MEAN.csv',
             (-1, 0): 'BC15/BC15_LOWQ_MEAN.csv',
             (-1, 1): 'BC15/BC15_LOWQ_JPN_MEAN.csv'}
STD_INTRA_FILE = {(0, 0): 'BC15/BC15_GLOBAL_STD_INTRA.csv',
                  (0, 1): 'BC15/BC15_AVEQ_JPN_STD_INTRA.csv',
                  (1, 0): 'BC15/BC15_HIGHQ_STD_INTRA.csv',
                  (1, 1): 'BC15/BC15_HIGHQ_JPN_STD_INTRA.csv',
                  (-1, 0): 'BC15/BC15_LOWQ_STD_INTRA.csv',
                  (-1, 1): 'BC15/BC15_LOWQ_JPN_STD_INTRA.csv'}

STD_INTER_FILE = {(0, 0): 'BC15/BC15_GLOBAL_STD_INTER.csv',
                  (0, 1): 'BC15/BC15_AVEQ_JPN_STD_INTER.csv',
                  (1, 0): 'BC15/BC15_HIGHQ_STD_INTER.csv',
                  (1, 1): 'BC15/BC15_HIGHQ_JPN_STD_INTER.csv',
                  (-1, 0): 'BC15/BC15_LOWQ_STD_INTER.csv',
                  (-1, 1): 'BC15/BC15_LOWQ_JPN_STD_INTER.csv'}

STD_TOTAL_FILE = {(0, 0): 'BC15/BC15_GLOBAL_STD_TOTAL.csv',
                  (0, 1): 'BC15/BC15_AVEQ_JPN_STD_TOTAL.csv',
                  (1, 0): 'BC15/BC15_HIGHQ_STD_TOTAL.csv',
                  (1, 1): 'BC15/BC15_HIGHQ_JPN_STD_TOTAL.csv',
                  (-1, 0): 'BC15/BC15_LOWQ_STD_TOTAL.csv',
                  (-1, 1): 'BC15/BC15_LOWQ_JPN_STD_TOTAL.csv'}


class BozorgniaCampbell2016TestCase(BaseGSIMTestCase):
    GSIM_CLASS = BozorgniaCampbell2016

    def test_all(self):
        for sgn, SJ in itertools.product([-1, 0, 1], [0, 1]):
            self.check(MEAN_FILE[sgn, SJ],
                       STD_INTRA_FILE[sgn, SJ],
                       STD_INTER_FILE[sgn, SJ],
                       STD_TOTAL_FILE[sgn, SJ],
                       max_discrep_percentage=0.1, sgn=sgn, SJ=SJ)
