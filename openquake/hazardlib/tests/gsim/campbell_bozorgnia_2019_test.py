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
Tests for the Campbell & Bozorgnia (2019) ground-motion model.

Expected results are for IA in m/s and CAV in g-sec.
"""
import pytest

from openquake.hazardlib.gsim.campbell_bozorgnia_2019 import (
    CampbellBozorgnia2019, coeffs_high, coeffs_low)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class CampbellBozorgnia2019TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2019
    MEAN_FILE = 'CB19/CB2019%s_MEAN.csv'
    STD_INTRA_FILE = 'CB19/CB2019%s_STD_INTRA.csv'
    STD_INTER_FILE = 'CB19/CB2019%s_STD_INTER.csv'
    STD_TOTAL_FILE = 'CB19/CB2019%s_STD_TOTAL.csv'


coeffs = {'': None, '_HIGHQ': coeffs_high, '_LOWQ': coeffs_low}
params = [(name, SJ) for name in ['', '_HIGHQ', '_LOWQ'] for SJ in [0, 1]]


@pytest.mark.parametrize('name, SJ', params)
def test_all(name, SJ):
    self = CampbellBozorgnia2019TestCase()
    tag = name + ('_JAPAN' if SJ else '')
    self.check(self.MEAN_FILE % tag,
               self.STD_INTRA_FILE % tag,
               self.STD_INTER_FILE % tag,
               self.STD_TOTAL_FILE % tag,
               max_discrep_percentage=0.1,
               coeffs=coeffs[name], SJ=SJ)