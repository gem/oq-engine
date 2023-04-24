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

from openquake.hazardlib.gsim.somerville_2009 import \
    SomervilleEtAl2009YilgarnCraton, SomervilleEtAl2009NonCratonic, \
    SomervilleEtAl2009YilgarnCraton_SS14, SomervilleEtAl2009NonCratonic_SS14
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated from EQRM implementation of Somerville 2009 GMPE.


class SomervilleEtAl2009YilgarnCratonTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SomervilleEtAl2009YilgarnCraton

    def test_all(self):
        self.check('S09/SomervilleEtAl2009YilgarnCraton_MEAN.csv',
                   'S09/SomervilleEtAl2009YilgarnCraton_STD_TOTAL.csv',
                   max_discrep_percentage=0.5,
                   std_discrep_percentage=0.1)


class SomervilleEtAl2009NonCratonicTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SomervilleEtAl2009NonCratonic

    def test_all(self):
        self.check('S09/SomervilleEtAl2009NonCratonic_MEAN.csv',
                   'S09/SomervilleEtAl2009NonCratonic_STD_TOTAL.csv',
                   max_discrep_percentage=0.4,
                   std_discrep_percentage=0.1)
                   
                   
class SomervilleEtAl2009YilgarnCratonSS14TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SomervilleEtAl2009YilgarnCraton_SS14

    def test_all(self):
        self.check('S09/SomervilleEtAl2009YilgarnCraton_SS14_MEAN.csv',
                   'S09/SomervilleEtAl2009YilgarnCraton_SS14_STD_TOTAL.csv',
                   max_discrep_percentage=0.5,
                   std_discrep_percentage=0.1)


class SomervilleEtAl2009NonCratonicSS14TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SomervilleEtAl2009NonCratonic_SS14

    def test_all(self):
        self.check('S09/SomervilleEtAl2009NonCratonic_SS14_MEAN.csv',
                   'S09/SomervilleEtAl2009NonCratonic_SS14_STD_TOTAL.csv',
                   max_discrep_percentage=0.4,
                   std_discrep_percentage=0.1)

