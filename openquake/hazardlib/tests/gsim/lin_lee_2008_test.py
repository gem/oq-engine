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
from openquake.hazardlib.gsim.lin_lee_2008 import LinLee2008SInter
from openquake.hazardlib.gsim.lin_lee_2008 import LinLee2008SSlab

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# test data generated from OpenSHA implementation

class LinLee2008SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = LinLee2008SInter

    def test_mean(self):
        self.check('LL08/LL08SInter_MEAN.csv',
                    max_discrep_percentage=0.1)

    def test_total_std(self):
        self.check('LL08/LL08SInter_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)

class LinLee2008SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = LinLee2008SSlab

    def test_mean(self):
        self.check('LL08/LL08SSlab_MEAN.csv',
                    max_discrep_percentage=0.1)

    def test_total_std(self):
        self.check('LL08/LL08SSlab_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)
