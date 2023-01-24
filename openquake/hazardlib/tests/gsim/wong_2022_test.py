# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2023 GEM Foundation
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

from openquake.hazardlib.gsim.wong2022 import WongEtAl2022Shallow, WongEtAl2022Deep
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated from digitalization of figures. Tolerance is therefore large, 10%.
# to be updated with more accurate test tables. 


class Wong2022ShallowTestCase(BaseGSIMTestCase):
    GSIM_CLASS = WongEtAl2022Shallow

    def test_all(self):
        self.check('Wong2022/WONGShallow2022_MEAN.csv',
                   'Wong2022/WONGShallow2022_SIGMA.csv',
                   max_discrep_percentage=10,
                   std_discrep_percentage=1)

class Wong2022DeepTestCasePGA(BaseGSIMTestCase):
    GSIM_CLASS = WongEtAl2022Deep

    def test_all(self):
        self.check('Wong2022/WONGDeep2022_MEAN_PGA.csv',
                   'Wong2022/WONGDeep2022_SIGMA_PGA.csv',
                   max_discrep_percentage=10,
                   std_discrep_percentage=1)
        
class Wong2022DeepTestCaseSA02(BaseGSIMTestCase):
    GSIM_CLASS = WongEtAl2022Deep

    def test_all(self):
        self.check('Wong2022/WONGDeep2022_MEAN_SA02.csv',
                   'Wong2022/WONGDeep2022_SIGMA_SA02.csv',
                   max_discrep_percentage=10,
                   std_discrep_percentage=1)

class Wong2022DeepTestCaseSA1(BaseGSIMTestCase):
    GSIM_CLASS = WongEtAl2022Deep

    def test_all(self):
        self.check('Wong2022/WONGDeep2022_MEAN_SA1.csv',
                   'Wong2022/WONGDeep2022_SIGMA_SA1.csv',
                   max_discrep_percentage=10,
                   std_discrep_percentage=1)
