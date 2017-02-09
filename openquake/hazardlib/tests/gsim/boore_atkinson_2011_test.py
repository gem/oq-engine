# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from openquake.hazardlib.gsim.boore_atkinson_2011 import (BooreAtkinson2011,
                                                          Atkinson2008prime)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class BooreAtkinson2011TestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreAtkinson2011

    # Test data created using the code available on the website of
    # D. Boore - http://daveboore.com/ (checked on 2014.01.08)
    # Code name: nga08_gm_tmr.for

    def test_mean_normal(self):
        self.check('BA11/BA11_MEDIAN.csv',
                   max_discrep_percentage=1.1)


class Atkinson2008primeTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Atkinson2008prime

    # Test data created using GMPE adjustment factor

    def test_mean_normal(self):
        self.check('BA11/A08_BA11_MEAN.csv',
                   max_discrep_percentage=1.1)
