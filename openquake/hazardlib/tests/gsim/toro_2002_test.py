# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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

from openquake.hazardlib.gsim.toro_2002 import ToroEtAl2002, ToroEtAl2002SHARE

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

import numpy

# Test data generated from OpenSHA implementation.

class ToroEtAl2002TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ToroEtAl2002

    def test_mean(self):
        self.check('TORO02/T02_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('TORO02/T02_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)

class ToroEtAl2002SHARETestCase(BaseGSIMTestCase):
    GSIM_CLASS = ToroEtAl2002SHARE

    def test_mean(self):
        self.check('TORO02/T02SHARE_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('TORO02/T02SHARE_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
