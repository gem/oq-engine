# The Hazard Library
# Copyright (C) 2015-2023 GEM Foundation
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

from openquake.hazardlib.gsim.zalachoris_rathje_2019 import (
        ZalachorisRathje2019)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class ZalachorisRathje2019TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZalachorisRathje2019

    # Tables provided by original authors (George Zalachoris) - he used fewer
    # decimals in the coeffs of BSSA14

    def test_all(self):
        self.check('Zalachoris/Zalachoris_MEAN.csv',
                   'Zalachoris/Zalachoris_intra.csv',
                   'Zalachoris/Zalachoris_inter.csv',
                   'Zalachoris/Zalachoris_totalsigma.csv',
                   max_discrep_percentage=1.0,
                   std_discrep_percentage=0.2)
