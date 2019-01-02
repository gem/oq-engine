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
from openquake.hazardlib.gsim.pankow_pechmann_2004 import PankowPechmann2004
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data obtained from Table 2 of Pankow and Pechmann (2004)


class PankowPechmann2004TestCase(BaseGSIMTestCase):
    GSIM_CLASS = PankowPechmann2004

    # Test data were taken from Table 2 of Pankow & Pechmann (2004)
    # (some decimals are added manually, due to lack of precision).
    # No table has been provided for the standard deviation,
    # whose test is then still missing.

    def test_mean(self):
        self.check('PP2004/PP2004_MEAN.csv',
                   max_discrep_percentage=0.1)

