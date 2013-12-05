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

from openquake.hazardlib.gsim.pezeshk_2011 import PezeshkEtAl2011
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class Pezeshk2011EtAlTestCase(BaseGSIMTestCase):
    GSIM_CLASS = PezeshkEtAl2011

    # Test data were obtained from a tool given by the authors
    # The data of the values of the mean PGA and SA are in g's.

    def test_mean(self):
        self.check('PEZE11/PZ11_MEAN.csv',
                    max_discrep_percentage=0.5)

    def test_std_total(self):
        self.check('PEZE11/PZ11_STD_TOTAL.csv',
                    max_discrep_percentage=0.5)
