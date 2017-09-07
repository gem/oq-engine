# The Hazard Library
# Copyright (C) 2015-2017 GEM Foundation
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

from openquake.hazardlib.gsim.atkinson_2015 import Atkinson2015
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class Atkinson2015TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Atkinson2015

    # Tables generated from current implementation - CIRCULAR TEST!

    def test_mean(self):
        self.check('ATKINSON2015/ATKINSON2015_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('ATKINSON2015/ATKINSON2015_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('ATKINSON2015/ATKINSON2015_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('ATKINSON2015/ATKINSON2015_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
