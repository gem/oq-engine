# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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

import openquake.hazardlib.gsim.ita04 as ita04
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

MAX_DISC = 0.1


"""
class SabettaPugliese1996(BaseGSIMTestCase):
    GSIM_CLASS = ita04.AmbraseysEtAl1996Normal()
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_A04_J15_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MAX_DISC)
"""


class AmbraseysEtAl1996Test(BaseGSIMTestCase):
    GSIM_CLASS = ita04.AmbraseysEtAl1996Normal
    MEAN_FILE = "ITA04/AmbraseysEtAl1996Normal_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MAX_DISC)
