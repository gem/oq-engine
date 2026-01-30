# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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

import os
import numpy as np

from openquake.hazardlib.tests.gsim.mgmpe.dummy import new_ctx
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.hassani_atkinson_2018 import (
    HassaniAtkinson2018)


PATH_ADJ_FILE = os.path.join(os.path.dirname(__file__),'..', '..', 'gsim',
                             'ha18_gamma_cal',
                             'hassani_atkinson_2018_gamma_cal.txt')

# Ratio of gamma adjusted/non-adjusted
EXP_RATIOS = np.array([[[0.60353158, 0.40182653, 0.41112883],
                        [0.78351984, 0.65665098, 0.84048471],
                        [0.84070221, 0.72329061, 0.6569959 ]]])


class HassaniAtkinson2018Test(BaseGSIMTestCase):
    GSIM_CLASS = HassaniAtkinson2018

    def test_mean(self):
        # Verification tables created using the .xls spreadsheet provided as an
        # electronic supplement to the BSSA paper
        self.check('HA18/HA18_MEAN_K_0pt03s_Ds_20bar.csv',
                   max_discrep_percentage=0.1, kappa0=0.03, d_sigma=20)
        

class HassaniAtkinson2018TestGammaAdjustment(BaseGSIMTestCase):
    """
    Test the file-dependent anelastic attenuation (gamma) adjustment.
    """
    def test_gamma_adj(self):

        # Create GMMs
        gmm_ori = HassaniAtkinson2018(d_sigma=100, kappa0=0.02)
        gmm_adj = HassaniAtkinson2018(d_sigma=100, kappa0=0.02, gamma_fle=PATH_ADJ_FILE)

        # Make the ctxs
        imts = ["PGA", 'SA(1.0)', 'SA(2.0)']
        cmaker_ori = simple_cmaker([gmm_ori], imts) # Mags set to Mw 6 by default
        ctx_ori = new_ctx(cmaker_ori, 3)
        ctx_ori.rrup = np.array([50., 100., 150])
        ctx_ori.vs30 = np.array([800., 400., 200.])
        mean_ori, _, _, _ = cmaker_ori.get_mean_stds([ctx_ori])

        cmaker_adj = simple_cmaker([gmm_adj], imts) # Mags set to Mw 6 by default
        ctx_adj = new_ctx(cmaker_adj, 3)
        ctx_adj.rrup = np.array([50., 100., 150])
        ctx_adj.vs30 = np.array([800., 400., 200.])
        mean_adj, _, _, _ = cmaker_adj.get_mean_stds([ctx_adj])

        # Check ratio of adjusted/original is correct
        ratio = np.exp(mean_adj)/np.exp(mean_ori) 
        np.testing.assert_allclose(ratio, EXP_RATIOS, rtol=1e-6)