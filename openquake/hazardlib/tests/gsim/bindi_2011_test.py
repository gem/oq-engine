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

#
#
#
# Test tables elaboratated from data provided directly from the authors.
#

from openquake.hazardlib.gsim.bindi_2011 import BindiEtAl2011
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class BindiEtAl2011TestCase(BaseGSIMTestCase):
    GSIM_CLASS = BindiEtAl2011

    # Tables provided by original authors

    def test_mean(self):
        self.check('BINDI2011/BINDI2011_MEAN.csv',
                    max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('BINDI2011/BINDI2011_STD_INTER.csv',
                    max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('BINDI2011/BINDI2011_STD_INTRA.csv',
                    max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('BINDI2011/BINDI2011_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)
