# The Hazard Library
# Copyright (C) 2013-2014, GEM Foundation
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
from openquake.hazardlib.gsim.fukushima_tanaka_1990 import (
    FukushimaTanaka1990,
    FukushimaTanakaSite1990
)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data provided by ????


class FukushimaTanaka1990TestCase(BaseGSIMTestCase):
    GSIM_CLASS = FukushimaTanaka1990

    def test_mean(self):
        self.check('FT1990/FT1990_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('FT1990/FT1990_STDTOTAL.csv',
                   max_discrep_percentage=0.1)


class FukushimaTanaka1990SiteTestCase(BaseGSIMTestCase):
    GSIM_CLASS = FukushimaTanakaSite1990

    def test_mean(self):
        self.check('FT1990/FT1990Site_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('FT1990/FT1990Site_STDTOTAL.csv',
                   max_discrep_percentage=0.1)
