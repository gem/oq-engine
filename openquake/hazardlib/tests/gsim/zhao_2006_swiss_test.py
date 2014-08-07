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
from openquake.hazardlib.gsim.zhao_2006 import (ZhaoEtAl2006Asc,
                                                ZhaoEtAl2006SInter,
                                                ZhaoEtAl2006SSlab)
                                                
from openquake.hazardlib.gsim.zhao_2006  import (ZhaoEtAl2006AscSWISS05, 
                                                 ZhaoEtAl2006AscSWISS03,
                                                 ZhaoEtAl2006AscSWISS08,
                                                 ZhaoEtAl2006AscSWISS05T,
                                                 ZhaoEtAl2006AscSWISS03T,
                                                 ZhaoEtAl2006AscSWISS08T)
from openquake.hazardlib.gsim.base import (SitesContext, 
                                           RuptureContext, 
                                           DistancesContext)
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.const import StdDev

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

import numpy

# Test data generated from Fortran implementation
# provided by John Zhao
# For the case Vs30 > 1100, test data have been
# generated from Matlab implementation taken from:
# http://www.stanford.edu/~bakerjw/Epsilon/Zhao_2006.m
# (this because the original code provided by Zhao
# does not include this case, even if it is described
# in the original paper)


class ZhaoEtAl2006AscSWISS05TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006AscSWISS05

    def test_mean(self):
        self.check('ZHAO06Swiss/ZETAL06_MEAN_VsK-5.csv',
                   max_discrep_percentage=0.4)
    def test_std_total(self):
        self.check('ZHAO06Swiss/ZETAL06_STD_TOTAL_SigmaSS_TMR.csv',max_discrep_percentage=0.50)

class ZhaoEtAl2006AscSWISS03TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006AscSWISS03

    def test_mean(self):
        self.check('ZHAO06Swiss/ZETAL06_MEAN_VsK-3.csv',
                   max_discrep_percentage=0.4)
    def test_std_total(self):
        self.check('ZHAO06Swiss/ZETAL06_STD_TOTAL_SigmaSS_TMR.csv',max_discrep_percentage=0.50)  
                           
class ZhaoEtAl2006AscSWISS08TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006AscSWISS08

    def test_mean(self):
        self.check('ZHAO06Swiss/ZETAL06_MEAN_VsK-8.csv',
                   max_discrep_percentage=0.4)                   
    def test_std_total(self):
        self.check('ZHAO06Swiss/ZETAL06_STD_TOTAL_SigmaSS_TMR.csv',max_discrep_percentage=0.50)

class ZhaoEtAl2006AscSWISS08TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006AscSWISS08

    def test_mean(self):
        self.check('ZHAO06Swiss/ZETAL06_MEAN_VsK-8.csv',
                   max_discrep_percentage=0.4)                   
    def test_std_total(self):
        self.check('ZHAO06Swiss/ZETAL06_STD_TOTAL_SigmaSS_TMR.csv',max_discrep_percentage=0.50)

class ZhaoEtAl2006AscSWISS05TTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006AscSWISS05T

    def test_mean(self):
        self.check('ZHAO06Swiss/ZETAL06_MEAN_VsK-5.csv',
                   max_discrep_percentage=0.4)
    def test_std_total(self):
        self.check('ZHAO06Swiss/ZETAL06_STD_TOTAL_SigmaSS_T.csv',max_discrep_percentage=0.50)

class ZhaoEtAl2006AscSWISS03TTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006AscSWISS03T

    def test_mean(self):
        self.check('ZHAO06Swiss/ZETAL06_MEAN_VsK-3.csv',
                   max_discrep_percentage=0.4)
    def test_std_total(self):
        self.check('ZHAO06Swiss/ZETAL06_STD_TOTAL_SigmaSS_T.csv',max_discrep_percentage=0.50)  
                           
class ZhaoEtAl2006AscSWISS08TTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006AscSWISS08T

    def test_mean(self):
        self.check('ZHAO06Swiss/ZETAL06_MEAN_VsK-8.csv',
                   max_discrep_percentage=0.4)                   
    def test_std_total(self):
        self.check('ZHAO06Swiss/ZETAL06_STD_TOTAL_SigmaSS_T.csv',max_discrep_percentage=0.50)
