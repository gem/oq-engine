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
from openquake.hazardlib.gsim.si_midorikawa_1999 import SiMidorikawa1999Asc, \
    SiMidorikawa1999SInter, SiMidorikawa1999SSlab

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
# test data was generated using alternative implementation of GMPE.


class SiMidorikawa1999AscTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SiMidorikawa1999Asc

    def test_mean(self):
        self.check('SM99/SM99ASC_MEAN.csv', max_discrep_percentage=0.1)

    def test_total_stddev(self):
        self.check('SM99/SM99ASC_STD_TOTAL.csv', max_discrep_percentage=0.1)


class SiMidorikawa1999SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SiMidorikawa1999SInter

    def test_mean(self):
        self.check('SM99/SM99SInter_MEAN.csv', max_discrep_percentage=0.1)

    def test_total_stddev(self):
        self.check('SM99/SM99SInter_STD_TOTAL.csv', max_discrep_percentage=0.1)


class SiMidorikawa1999SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SiMidorikawa1999SSlab

    def test_mean(self):
        self.check('SM99/SM99SSlab_MEAN.csv', max_discrep_percentage=0.1)

    def test_total_stddev(self):
        self.check('SM99/SM99SSlab_STD_TOTAL.csv', max_discrep_percentage=0.1)
