# The Hazard Library
# Copyright (C) 2013-2026 GEM Foundation
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

from openquake.hazardlib.gsim.zafarani_2018 import (ZafaraniEtAl2018,
                                                   ZafaraniEtAl2018VHratio)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class ZaferaniEtAl2018TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZafaraniEtAl2018

    # Tables are created using an calculation excel file confirmed by the authors  

    def test_mean_ss(self):
        self.check('Za18/Za18_MEAN_SS_H.csv',
                   max_discrep_percentage=0.1)
        
    def test_mean_t(self):
        self.check('Za18/Za18_MEAN_T_H.csv',
                   max_discrep_percentage=0.1)
        
    def test_std_tot(self):
        self.check('Za18/Za18_STD_TOT_T_H.csv',
                   max_discrep_percentage=0.1)


class AmbraseysEtAl2005VHratioTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZafaraniEtAl2018VHratio

    # Tables are created using an calculation excel file confirmed by the authors  

    def test_mean_ss(self):
        self.check('Za18/Za18_MEAN_SS_V_H.csv',
                   max_discrep_percentage=0.1)
        
    def test_mean_t(self):
        self.check('Za18/Za18_MEAN_T_V_H.csv',
                   max_discrep_percentage=0.1)
        
    def test_std_tot(self):
        self.check('Za18/Za18_STD_TOT_SS_V_H.csv',
                   max_discrep_percentage=0.1)