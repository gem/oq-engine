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
Test suite for the NZ NSHM 2022 modification of Abrahamson & Gulerce (2020) NGA Subduction GMPEs. 
"""

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.nz22.nz_nshm2022_abrahamson_gulerce_2020 import (
    NZNSHM2022_AbrahamsonGulerce2020SInter,
    NZNSHM2022_AbrahamsonGulerce2020SSlab,
)

# Interface - Global
class NZNSHM2022_AbrahamsonGulerce2020TestCase(BaseGSIMTestCase):

    FILES = [
        "nz22/ag2020/AG20_{}_GLO_GNS_MEAN.csv",
        "nz22/ag2020/AG20_{}_GLO_GNS_TOTAL_STDDEV.csv",
    ]
    REG = "GLO"
    ADJ = False
    SIGMA_MU_EPSILON = 0.0

    def test_all(self):
        for gcls, trt in zip([NZNSHM2022_AbrahamsonGulerce2020SInter, NZNSHM2022_AbrahamsonGulerce2020SSlab],
                             ['INTERFACE', 'SLAB']):
            self.GSIM_CLASS = gcls
            mean_file, std_file = [f.format(trt) for f in self.FILES]
            
            self.check(
                mean_file,
                max_discrep_percentage=0.1,
                region=self.REG, apply_usa_adjustment=self.ADJ,
                sigma_mu_epsilon=self.SIGMA_MU_EPSILON
            )
            
            self.check(
                std_file,
                max_discrep_percentage=0.1,
                region=self.REG, apply_usa_adjustment=self.ADJ,
                sigma_mu_epsilon=self.SIGMA_MU_EPSILON
            )