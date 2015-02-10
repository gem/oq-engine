# The Hazard Library
# Copyright (C) 2012-2015, GEM Foundation
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
from openquake.hazardlib.gsim.abrahamson_2014 import AbrahamsonEtAl2014
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data have been generated from the Matlab implementation available as
# Annex 1 of Abrahamson et al. (2014)


class Abrahamson2014EtAlTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AbrahamsonEtAl2014

    def test_mean(self):
        self.check('ASK14/ASK14_MEAN.csv',
                   max_discrep_percentage=0.1)

    """
    def test_std_inter(self):
        self.check('AS08/AS08_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('AS08/AS08_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AS08/AS08_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
    """
