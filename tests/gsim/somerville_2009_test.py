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
from openquake.hazardlib.gsim.somerville_2009 import \
    SomervilleEtAl2009YilgarnCraton, SomervilleEtAl2009NonCratonic

from tests.gsim.utils import BaseGSIMTestCase

import numpy

# Test data generated from EQRM implementation of Somerville 2009 GMPE.


class SomervilleEtAl2009YilgarnCratonTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SomervilleEtAl2009YilgarnCraton

    def test_mean(self):
        self.check('S09/SOMMERVILLE_YILGARN2009_MEAN.csv',
                   max_discrep_percentage=0.5)

    def test_std_total(self):
        self.check('S09/SOMMERVILLE_YILGARN2009_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class SomervilleEtAl2009NonCratonicTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SomervilleEtAl2009NonCratonic

    def test_mean(self):
        self.check('S09/SOMMERVILLE_Non_Cratonic2009_MEAN.csv',
                   max_discrep_percentage=0.4)

