# nhlib: A New Hazard Library
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
from nhlib.gsim.zhao_2006 import ZhaoEtAl2006Asc, ZhaoEtAl2006SInter,\
    ZhaoEtAl2006SSlab

from tests.gsim.utils import BaseGSIMTestCase

# Test data generated from OpenSHA implementation
# (ZhaoEtAl_2006_AttenRel).

class ZhaoEtAl2006AscTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006Asc

    def test_mean(self):
        self.check('ZHAO06/Z06Asc_MEAN.csv',
                    max_discrep_percentage=0.4)
                    
    def test_std_intra(self):
        self.check('ZHAO06/Z06Asc_STD_INTRA.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_inter(self):
        self.check('ZHAO06/Z06Asc_STD_INTER.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_total(self):
        self.check('ZHAO06/Z06Asc_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)


class ZhaoEtAl2006SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006SInter

    def test_mean(self):
        self.check('ZHAO06/Z06SInter_MEAN.csv',
                    max_discrep_percentage=0.4)

    def test_std_intra(self):
        self.check('ZHAO06/Z06SInter_STD_INTRA.csv',
                    max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('ZHAO06/Z06SInter_STD_INTER.csv',
                    max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('ZHAO06/Z06SInter_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)


class ZhaoEtAl2006SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006SSlab

    def test_mean(self):
        self.check('ZHAO06/Z06SSlab_MEAN.csv',
                    max_discrep_percentage=0.4)

    def test_std_intra(self):
        self.check('ZHAO06/Z06SSlab_STD_INTRA.csv',
                    max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('ZHAO06/Z06SSlab_STD_INTER.csv',
                    max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('ZHAO06/Z06SSlab_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)