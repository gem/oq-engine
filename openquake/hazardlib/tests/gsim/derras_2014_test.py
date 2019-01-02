# The Hazard Library
# Copyright (C) 2013-2018 GEM Foundation
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

from openquake.hazardlib.gsim.derras_2014 import DerrasEtAl2014
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Maximum discrepancy set to 0.1 %
MAX_DISC = 0.1


class DerrasEtAl2014TestCase(BaseGSIMTestCase):
    GSIM_CLASS = DerrasEtAl2014

    # Tables constructed from Excel implementation supplied as Electronic
    # supplement to the paper

    def test_mean(self):
        self.check('derras14/DERRAS14_MEAN.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_intra(self):
        self.check('derras14/DERRAS14_INTRA_EVENT_STDDEV.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_inter(self):
        self.check('derras14/DERRAS14_INTER_EVENT_STDDEV.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_total(self):
        self.check('derras14/DERRAS14_TOTAL_STDDEV.csv',
                   max_discrep_percentage=MAX_DISC)
