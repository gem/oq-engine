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
from openquake.hazardlib.gsim.atkinson_boore_1995 import AtkinsonBoore1995GSC
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AtkinsonBoore1995GSCTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AtkinsonBoore1995GSC

    # Test data generated from Excel implementation

    def test_mean(self):
        self.check('AB95/AB95GSC_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AB95/AB95GSC_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
