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

from openquake.hazardlib.gsim.fukushima_tanaka_1990 import (
    FukushimaTanaka1990,
    FukushimaTanakaSite1990
)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


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
