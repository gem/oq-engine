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
from nhlib.gsim.boore_atkinson_2008 import BooreAtkinson2008

from tests.gsim.utils import BaseGSIMTestCase


class BooreAtkinson2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreAtkinson2008

    # test data were generated using opensha implementation of GMPE
    # corrected for pga4nl calculation (using Mref = 5.0 instead of
    # Mref = 1.0) as described in caption to table 6 (pag 119) of
    # BA2008 paper

    def test_mean(self):
        self.check('BA08/BA08_MEAN.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_intra(self):
        self.check('BA08/BA08_STD_INTRA.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_inter(self):
        self.check('BA08/BA08_STD_INTER.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_total(self):
        self.check('BA08/BA08_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)