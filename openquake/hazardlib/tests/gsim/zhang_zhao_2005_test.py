# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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

from openquake.hazardlib.gsim.zhang_zhao_2005 import (
    Zhang_Zhao2005SInter,
    Zhang_Zhao2005SSlab,
    Zhang_Zhao2005Crust)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase



class Zhang_Zhao2005_Sinter_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Zhang_Zhao2005SInter

    # Verification tables provided by P. R. Jadhav and D. Wijewickreme
    
    def test_mean(self):
        
        self.check('ZHANG05/Zhang2005SInter_MEAN.csv',
                   max_discrep_percentage=0.47)

    def test_std_total(self):
        self.check('ZHANG05/Zhang2005SInter_STDDEV.csv',
                   max_discrep_percentage=0.1)

class Zhang_Zhao2005_SSlab_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Zhang_Zhao2005SSlab

    # Verification tables provided by P. R. Jadhav and D. Wijewickreme
    
    def test_mean(self):
        
        self.check('ZHANG05/Zhang2005SSlab_MEAN.csv',
                   max_discrep_percentage=0.47)

    def test_std_total(self):
        self.check('ZHANG05/Zhang2005SSlab_STDDEV.csv',
                   max_discrep_percentage=0.1)  

class Zhang_Zhao2005_Crust_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Zhang_Zhao2005Crust

    # Verification tables provided by P. R. Jadhav and D. Wijewickreme
    
    def test_mean(self):
        
        self.check('ZHANG05/Zhang2005Crust_MEAN.csv',
                   max_discrep_percentage=0.47)

    def test_std_total(self):
        self.check('ZHANG05/Zhang2005Crust_STDDEV.csv',
                   max_discrep_percentage=0.1)                    