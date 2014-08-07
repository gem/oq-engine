# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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
from openquake.hazardlib.gsim.cauzzi_faccioli_2008 import CauzziFaccioli2008
from openquake.hazardlib.gsim.cauzzi_faccioli_2008 import CauzziFaccioli2008SWISS01
from openquake.hazardlib.gsim.cauzzi_faccioli_2008 import CauzziFaccioli2008SWISS04
from openquake.hazardlib.gsim.cauzzi_faccioli_2008 import CauzziFaccioli2008SWISS08
from openquake.hazardlib.gsim.cauzzi_faccioli_2008 import CauzziFaccioli2008SWISS01T
from openquake.hazardlib.gsim.cauzzi_faccioli_2008 import CauzziFaccioli2008SWISS04T
from openquake.hazardlib.gsim.cauzzi_faccioli_2008 import CauzziFaccioli2008SWISS08T
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.base import (SitesContext, RuptureContext, DistancesContext)
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.const import StdDev

import numpy

# Test data generated from OpenSHA implementation.

class CauzziFaccioli2008SWISS01TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CauzziFaccioli2008SWISS01

    def test_mean(self):
        self.check('CF08Swiss/CF08_MEAN_VsK_1.csv',
                   max_discrep_percentage=0.50)

    def test_std_total(self):
        self.check('CF08Swiss/CF08_STD_TOTAL_SigmaSS_TMR.csv',max_discrep_percentage=0.50)

class CauzziFaccioli2008SWISS04TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CauzziFaccioli2008SWISS04
#~ 
    def test_mean(self):
        self.check('CF08Swiss/CF08_MEAN_VsK_4.csv',
                   max_discrep_percentage=0.50)
#~ 
    def test_std_total(self):
        self.check('CF08Swiss/CF08_STD_TOTAL_SigmaSS_TMR.csv',max_discrep_percentage=0.50)
#~ 
class CauzziFaccioli2008SWISS08TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CauzziFaccioli2008SWISS08
#~ 
    def test_mean(self):
        self.check('CF08Swiss/CF08_MEAN_VsK_8.csv',
                   max_discrep_percentage=0.50)

    def test_std_total(self):
        self.check('CF08Swiss/CF08_STD_TOTAL_SigmaSS_TMR.csv',max_discrep_percentage=0.50)
#~ 
class CauzziFaccioli2008SWISS01TTestCase(BaseGSIMTestCase):
    GSIM_CLASS = CauzziFaccioli2008SWISS01T

    def test_mean(self):
        self.check('CF08Swiss/CF08_MEAN_VsK_1.csv',
                   max_discrep_percentage=0.50)

    def test_std_total(self):
        self.check('CF08Swiss/CF08_STD_TOTAL_SigmaSS_T.csv',max_discrep_percentage=0.50)

class CauzziFaccioli2008SWISS04TTestCase(BaseGSIMTestCase):
    GSIM_CLASS = CauzziFaccioli2008SWISS04T

    def test_mean(self):
        self.check('CF08Swiss/CF08_MEAN_VsK_4.csv',
                   max_discrep_percentage=0.80)
    def test_std_total(self):
        self.check('CF08Swiss/CF08_STD_TOTAL_SigmaSS_T.csv',max_discrep_percentage=0.50)
        
class CauzziFaccioli2008SWISS08TTestCase(BaseGSIMTestCase):
    GSIM_CLASS = CauzziFaccioli2008SWISS08T

    def test_mean(self):
        self.check('CF08Swiss/CF08_MEAN_VsK_8.csv',
                   max_discrep_percentage=0.50)
    def test_std_total(self):
        self.check('CF08Swiss/CF08_STD_TOTAL_SigmaSS_T.csv',max_discrep_percentage=0.50)
