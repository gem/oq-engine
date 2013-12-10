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
from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class SadighEtAl1997TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SadighEtAl1997

    # test data was generated using opensha implementation of GMPE.

    def test_mean_rock(self):
        self.check('SADIGH97/SADIGH1997_ROCK_MEAN.csv',
                    max_discrep_percentage=0.4)

    def test_total_stddev_rock(self):
        self.check('SADIGH97/SADIGH1997_ROCK_STD_TOTAL.csv',
                   max_discrep_percentage=1e-10)

    def test_mean_soil(self):
        self.check('SADIGH97/SADIGH1997_SOIL_MEAN.csv',
                    max_discrep_percentage=0.5)

    def test_total_stddev_soil(self):
        self.check('SADIGH97/SADIGH1997_SOIL_STD_TOTAL.csv',
                   max_discrep_percentage=1e-10)
