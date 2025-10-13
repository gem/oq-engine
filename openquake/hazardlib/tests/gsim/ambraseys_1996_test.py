# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2023 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from openquake.hazardlib.gsim.ambraseys_1996 import AmbraseysEtAl1996
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data provided by INGV


class AmbraseysEtAl1996TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AmbraseysEtAl1996

    # Tables provided by INGV (Giovanni Lanzano- Vera D'Amico)
    MEAN_FILE = "AMB96/AMB96_MPS04_MEAN.csv"
    STD_FILE = "AMB96/AMB96_MPS04_STD_TOTAL.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=0.1)



