# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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

from openquake.hazardlib.gsim.campbell_bozorgnia_2008 import (
    CampbellBozorgnia2008, CampbellBozorgnia2008Arbitrary)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data have been generated from the Fortran implementation provided by
# K. Campbell and Y. Bozorgnia, available as a supplement to the NGA documents
# at:
# http://peer.berkeley.edu/ngawest/nga_models.html

# As of September 2013 the CAV model has not been included in the test suite

class CampbellBozorgnia2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2008

    def test_mean_reverse_faulting(self):
        self.check('CB08/CB08_RV_MEAN.csv', max_discrep_percentage=0.1)

    def test_mean_normal_faulting(self):
        self.check('CB08/CB08_NM_MEAN.csv', max_discrep_percentage=0.1)
        
    def test_mean_strike_slip_faulting(self):
        self.check('CB08/CB08_SS_MEAN.csv', max_discrep_percentage=0.1)

    def test_std_inter_reverse(self):
        self.check('CB08/CB08_RV_STD_INTER.csv', max_discrep_percentage=0.1)
        
    def test_std_inter_normal(self):
        self.check('CB08/CB08_NM_STD_INTER.csv', max_discrep_percentage=0.1)
        
    def test_std_inter_strike_slip(self):
        self.check('CB08/CB08_SS_STD_INTER.csv', max_discrep_percentage=0.1)

    def test_std_intra_reverse(self):
        self.check('CB08/CB08_RV_STD_INTRA.csv', max_discrep_percentage=0.1)
    
    def test_std_intra_normal(self):
        self.check('CB08/CB08_NM_STD_INTRA.csv', max_discrep_percentage=0.1)
        
    def test_std_intra_strike_slip(self):
        self.check('CB08/CB08_SS_STD_INTRA.csv', max_discrep_percentage=0.1)

    def test_std_total_reverse(self):
        self.check('CB08/CB08_RV_STD_TOTAL.csv', max_discrep_percentage=0.1)
    
    def test_std_total_normal(self):
        self.check('CB08/CB08_NM_STD_TOTAL.csv', max_discrep_percentage=0.1)
    
    def test_std_total_strike_slip(self):
        self.check('CB08/CB08_SS_STD_TOTAL.csv', max_discrep_percentage=0.1)

class CampbellBozorgnia2008ArbitraryTestCase(BaseGSIMTestCase):
    # This second class tests the implementation for the Arbitrary horizontal
    # component of ground motion. As this inherits the original class and 
    # modifies only the calculation of the total sigma, only the total sigma
    # output is tested
    
    GSIM_CLASS = CampbellBozorgnia2008Arbitrary
    
    def test_std_total_reverse(self):
        self.check('CB08/CB08_RV_STD_TOTAL_ARBITRARY.csv',
                   max_discrep_percentage=0.1)
    
    def test_std_total_normal(self):
        self.check('CB08/CB08_NM_STD_TOTAL_ARBITRARY.csv',
                   max_discrep_percentage=0.1)
    
    def test_std_total_strike_slip(self):
        self.check('CB08/CB08_SS_STD_TOTAL_ARBITRARY.csv',
                   max_discrep_percentage=0.1)
