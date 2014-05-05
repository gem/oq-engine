# The Hazard Library
# Copyright (C) 2014 GEM Foundation
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
from openquake.hazardlib.gsim.garcia_2005 import (
    GarciaEtAl2005SSlab,
    GarciaEtAl2005SSlabVert,
)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class GarciaEtAl2005SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = GarciaEtAl2005SSlab

    # Test data generated from Fortran implementation
    # provided by Daniel Garcia

    def test_mean(self):
        self.check('GA05/GA05SSLab_MEAN.csv', max_discrep_percentage=0.2)

    def test_std_total(self):
        self.check('GA05/GA05SSLab_STD_TOTAL.csv', max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('GA05/GA05SSLab_STD_INTRA.csv', max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('GA05/GA05SSLab_STD_INTER.csv', max_discrep_percentage=0.1)


class GarciaEtAl2005SSlabVertTestCase(BaseGSIMTestCase):
    GSIM_CLASS = GarciaEtAl2005SSlabVert

    # Test data generated from Fortran implementation
    # provided by Daniel Garcia

    def test_mean(self):
        self.check('GA05/GA05SSLabV_MEAN.csv', max_discrep_percentage=0.2)

    def test_std_total(self):
        self.check('GA05/GA05SSLabV_STD_TOTAL.csv', max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('GA05/GA05SSLabV_STD_INTRA.csv', max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('GA05/GA05SSLabV_STD_INTER.csv', max_discrep_percentage=0.1)
