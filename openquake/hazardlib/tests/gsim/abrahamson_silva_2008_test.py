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
from openquake.hazardlib.gsim.abrahamson_silva_2008 import AbrahamsonSilva2008

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data have been generated from Fortran implementation
# of Dave Boore available at:
# http://www.daveboore.com/software_online.html
# Note that the Fortran implementation has been modified not
# to compute the 'Constant Displacement Model' term

class AbrahamsonSilva2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AbrahamsonSilva2008

    def test_mean(self):
        self.check('AS08/AS08_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('AS08/AS08_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('AS08/AS08_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AS08/AS08_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)

