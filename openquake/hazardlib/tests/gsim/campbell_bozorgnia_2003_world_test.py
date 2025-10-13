# The Hazard Library
# Copyright (C) 2013-2023 GEM Foundation
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

from openquake.hazardlib.gsim.campbell_bozorgnia_2003_world import (CampbellBozorgnia2003,
                                                                    CampbellBozorgnia2003Vertical)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class CampbellBozorgnia2003TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2003

    # Tables created using EZ-FRISK and an excel calculation file

    def test_mean_r(self):
        self.check('CB03_W/CB03_MEAN_R_H.csv',
                   max_discrep_percentage=0.1)
        
    def test_mean_ss(self):
        self.check('CB03_W/CB03_MEAN_SS_H.csv',
                   max_discrep_percentage=0.1)
        
    def test_mean_t(self):
        self.check('CB03_W/CB03_MEAN_T_H.csv',
                   max_discrep_percentage=0.1)
    
    def test_std_tot(self):
        self.check('CB03_W/CB03_STD_TOT_H.csv',
                   max_discrep_percentage=0.1)


class CampbellBozorgnia2003VerticalTestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2003Vertical

    # Tables created using EZ-FRISK 

    def test_mean_r(self):
        self.check('CB03_W/CB03_MEAN_R_V.csv',
                   max_discrep_percentage=0.1)
        
    def test_mean_ss(self):
        self.check('CB03_W/CB03_MEAN_SS_V.csv',
                   max_discrep_percentage=0.1)
        
    def test_mean_t(self):
        self.check('CB03_W/CB03_MEAN_T_V.csv',
                   max_discrep_percentage=0.1)
    
    def test_std_tot(self):
        self.check('CB03_W/CB03_STD_TOT_V.csv',
                   max_discrep_percentage=0.1)
