# The Hazard Library
# Copyright (C) 2013 GEM Foundation
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
from openquake.hazardlib.gsim.boore_1997 import (BooreEtAl1997,
    BooreEtAl1997Unspecified, BooreEtAl1997Arbitrary,
    BooreEtAl1997UnspecifiedArbitrary)


from tests.gsim.utils import BaseGSIMTestCase


class BooreEtAl1997TestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreEtAl1997
    
    # All test data were generated using the Matlab implementation of the
    # Boore et al (1997) GMPE, as provided by Jack Baker
    # http://www.stanford.edu/~bakerjw/GMPEs.html

    def test_mean_normal(self):
        self.check('BJF1997/BJF1997_MEAN.csv',
                    max_discrep_percentage=0.1)
                     
    def test_std_intra(self):
        self.check('BJF1997/BJF1997_INTRA.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_inter(self):
        self.check('BJF1997/BJF1997_INTER.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_total(self):
        self.check('BJF1997/BJF1997_TOTAL.csv',
                    max_discrep_percentage=0.1)


class BooreEtAl1997UnspecifiedTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreEtAl1997Unspecified
    
    def test_mean_normal(self):
        self.check('BJF1997/BJF1997_UNC_MEAN.csv',
                    max_discrep_percentage=0.1)
                     
    def test_std_intra(self):
        self.check('BJF1997/BJF1997_UNC_INTRA.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_inter(self):
        self.check('BJF1997/BJF1997_UNC_INTER.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_total(self):
        self.check('BJF1997/BJF1997_UNC_TOTAL.csv',
                    max_discrep_percentage=0.1)


class BooreEtAl1997ArbitraryTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreEtAl1997Arbitrary
    
    def test_mean_normal(self):
        self.check('BJF1997/BJF1997_Arb_MEAN.csv',
                    max_discrep_percentage=0.1)
                     
    def test_std_intra(self):
        self.check('BJF1997/BJF1997_Arb_INTRA.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_inter(self):
        self.check('BJF1997/BJF1997_Arb_INTER.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_total(self):
        self.check('BJF1997/BJF1997_Arb_TOTAL.csv',
                    max_discrep_percentage=0.1)


class BooreEtAl1997ArbitraryUnspecifiedTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreEtAl1997ArbitraryUnspecified
    
    def test_mean_normal(self):
        self.check('BJF1997/BJF1997_UNC_Arb_MEAN.csv',
                    max_discrep_percentage=0.1)
                     
    def test_std_intra(self):
        self.check('BJF1997/BJF1997_UNC_Arb_INTRA.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_inter(self):
        self.check('BJF1997/BJF1997_UNC_Arb_INTER.csv',
                    max_discrep_percentage=0.1)
                    
    def test_std_total(self):
        self.check('BJF1997/BJF1997_UNC_Arb_TOTAL.csv',
                    max_discrep_percentage=0.1)
