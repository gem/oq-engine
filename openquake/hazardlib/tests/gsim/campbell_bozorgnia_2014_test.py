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
import numpy as np
import pytest
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.tests.gsim.mgmpe.dummy import new_ctx
from openquake.hazardlib.gsim.abrahamson_2014 import get_epistemic_sigma
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import (
    CampbellBozorgnia2014, coeffs_high, coeffs_low)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class CampbellBozorgnia2014TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2014
    MEAN_FILE = 'CB14/CB2014%s_MEAN.csv'
    STD_INTRA_FILE = 'CB14/CB2014%s_STD_INTRA.csv'
    STD_INTER_FILE = 'CB14/CB2014%s_STD_INTER.csv'
    STD_TOTAL_FILE = 'CB14/CB2014%s_STD_TOTAL.csv'


coeffs = {'': None, '_HIGHQ': coeffs_high, '_LOWQ': coeffs_low}
params = [(name, SJ) for name in ['', '_HIGHQ', '_LOWQ'] for SJ in [0, 1]]


@pytest.mark.parametrize('name, SJ', params)
def test_all(name, SJ):
    self = CampbellBozorgnia2014TestCase()
    tag = name + ('_JAPAN' if SJ else '')
    self.check(self.MEAN_FILE % tag,
               self.STD_INTRA_FILE % tag,
               self.STD_INTER_FILE % tag,
               self.STD_TOTAL_FILE % tag,
               max_discrep_percentage=0.1,
               coeffs=coeffs[name], SJ=SJ)


def test_sigma_mu_epsilon_shift_applied_once():
    # Check sigma_mu_epsilon shifts the median by eps * get_epistemic_sigma,
    # including at SA(T<0.25) where the PGA floor can overwrite the median
    # and the shift must be applied once, after the floor mask.
    epsilons = [0.0, 1.0, -1.28155, 2.5]
    gmms = [CampbellBozorgnia2014(sigma_mu_epsilon=e) for e in epsilons]
    imts = ['PGA', 'SA(0.05)', 'SA(0.1)', 'SA(0.2)', 'SA(1.0)']
    cmaker = simple_cmaker(gmms, imts, mags=['7.50'])
    ctx = new_ctx(cmaker, 3, mag=7.5)
    ctx.rrup = np.array([5., 20., 50.])
    ctx.vs30 = 760.
    ctx.z2pt5 = 1.
    mea, _, _, _ = cmaker.get_mean_stds([ctx])
    sigma_epi = get_epistemic_sigma(ctx)
    for g, eps in enumerate(epsilons):
        expected = np.broadcast_to(eps * sigma_epi, mea[0].shape)
        np.testing.assert_allclose(mea[g] - mea[0], expected, atol=1e-12)
