# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from openquake.hazardlib.gsim.chiou_youngs_2008_swiss import (
    ChiouYoungs2008SWISS01,
    ChiouYoungs2008SWISS06,
    ChiouYoungs2008SWISS04)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class ChiouYoungs2008SWISS01TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2008SWISS01

    def test_std_total(self):
        self.check('CY08Swiss/cy_2008_phis_ss_embeded.csv',
                   max_discrep_percentage=2.00)

    def test_mean_hanging_wall_normal_slip(self):
        self.check('CY08Swiss/CY08_MEDIAN_MS_HW_NM_VsK-1.csv',
                   max_discrep_percentage=0.80)

    def test_mean_hanging_wall_reversed_slip(self):
        self.check('CY08Swiss/CY08_MEDIAN_MS_HW_RV_VsK-1.csv',
                   max_discrep_percentage=0.80)

    def test_mean_hanging_wall_strike_slip(self):
        self.check('CY08Swiss/CY08_MEDIAN_MS_HW_SS_VsK-1.csv',
                   max_discrep_percentage=0.80)


class ChiouYoungs2008SWISS06TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2008SWISS06

    def test_std_total(self):
        self.check('CY08Swiss/cy_2008_phis_ss_embeded.csv',
                   max_discrep_percentage=2.00)

    def test_mean_hanging_wall_normal_slip(self):
        self.check('CY08Swiss/CY08_MEDIAN_MS_HW_NM_VsK-6.csv',
                   max_discrep_percentage=0.80)

    def test_mean_hanging_wall_reversed_slip(self):
        self.check('CY08Swiss/CY08_MEDIAN_MS_HW_RV_VsK-6.csv',
                   max_discrep_percentage=0.80)

    def test_mean_hanging_wall_strike_slip(self):
        self.check('CY08Swiss/CY08_MEDIAN_MS_HW_SS_VsK-6.csv',
                   max_discrep_percentage=0.80)


class ChiouYoungs2008SWISS04TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2008SWISS04

    def test_std_total(self):
        self.check('CY08Swiss/cy_2008_phis_ss_embeded.csv',
                   max_discrep_percentage=2.00)

    def test_mean_hanging_wall_normal_slip(self):
        self.check('CY08Swiss/CY08_MEDIAN_MS_HW_NM_VsK-4.csv',
                   max_discrep_percentage=0.80)

    def test_mean_hanging_wall_reversed_slip(self):
        self.check('CY08Swiss/CY08_MEDIAN_MS_HW_RV_VsK-4.csv',
                   max_discrep_percentage=0.80)

    def test_mean_hanging_wall_strike_slip(self):
        self.check('CY08Swiss/CY08_MEDIAN_MS_HW_SS_VsK-4.csv',
                   max_discrep_percentage=0.80)