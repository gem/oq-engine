# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2022 GEM Foundation
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

# Test data have been generated from the Python implementation available from the authors


from openquake.hazardlib.gsim.stafford_2022 import Stafford2022
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

#test case
class Stafford2022TestCase(BaseGSIMTestCase):
    """
    Test the default model. Here only the mean values are tested.
    """

    GSIM_CLASS =  Stafford2022

    def test_central_mean(self):
        self.check('STAFFORD2022/STAFFORD_NZ_SS_MEAN_CENTRAL_v2.csv',
                   'STAFFORD2022/STAFFORD_NZ_REV_MEAN_CENTERAL_v2.csv',
                   'STAFFORD2022/STAFFORD_NZ_NM_MEAN_CENTRAL_v2.csv',
                   max_discrep_percentage=0.01, mu_branch = "Central", sigma_branch = "Central")
        
        
    def test_lower_mean(self):
        self.check('STAFFORD2022/STAFFORD_NZ_SS_MEAN_LOWER_v2_EPI_SCALED.csv',
                   'STAFFORD2022/STAFFORD_NZ_REV_MEAN_LOWER_v2_EPI_SCALED.csv',
                   'STAFFORD2022/STAFFORD_NZ_NM_MEAN_LOWER_v2_EPI_SCALED.csv',
                   max_discrep_percentage=0.01, mu_branch = "Lower", sigma_branch = "Central")

    def test_upper_mean(self):
        self.check('STAFFORD2022/STAFFORD_NZ_SS_MEAN_UPPER_v2_EPI_SCALED.csv',
                   'STAFFORD2022/STAFFORD_NZ_REV_MEAN_UPPER_v2_EPI_SCALED.csv',
                   'STAFFORD2022/STAFFORD_NZ_NM_MEAN_UPPER_v2_EPI_SCALED.csv',
                    max_discrep_percentage=0.01, mu_branch = "Upper", sigma_branch = "Central")

    def test_central_sigma(self):
        self.check('STAFFORD2022/STAFFORD_NZ_SS_SIGMA_CENTRAL_v2.csv',
                   'STAFFORD2022/STAFFORD_NZ_REV_SIGMA_CENTRAL_v2.csv',
                   'STAFFORD2022/STAFFORD_NZ_NM_SIGMA_CENTRAL_v2.csv',
                    max_discrep_percentage=0.01, mu_branch = "Central", sigma_branch = "Central")
        
    def test_lower_sigma(self):
        self.check('STAFFORD2022/STAFFORD_NZ_SS_SIGMA_LOWER_v2.csv',
                   'STAFFORD2022/STAFFORD_NZ_REV_SIGMA_LOWER_v2.csv',
                   'STAFFORD2022/STAFFORD_NZ_NM_SIGMA_LOWER_v2.csv',
                    max_discrep_percentage=0.01, mu_branch = "Central", sigma_branch = "Lower")
        
    def test_upper_sigma(self):
        self.check('STAFFORD2022/STAFFORD_NZ_SS_SIGMA_UPPER_v2.csv',
                   'STAFFORD2022/STAFFORD_NZ_REV_SIGMA_UPPER_v2.csv',
                   'STAFFORD2022/STAFFORD_NZ_NM_SIGMA_UPPER_v2.csv',
                    max_discrep_percentage=0.01, mu_branch = "Central", sigma_branch = "Upper")
